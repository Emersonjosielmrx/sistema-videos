import asyncio
import json
import os
import secrets
import sys
import time
import traceback
from contextlib import asynccontextmanager
from pathlib import Path

import httpx
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.db import get_db, init_db, get_setting, set_setting, snapshot, record_event
from backend.auth import hash_password, verify_password, create_token, decode_token
from backend.hermes import HermesClient, HermesError
from backend.webhook import schedule as schedule_webhook
from backend.engine import (
    CollectSender, Incoming, Run, process, load_flow, get_menu_categories, reset_conversation, UPLOAD_DIR, AI_OFF,
)
from backend.flow_config import TEMPLATES, DEFAULTS, new_config, normalize, flow_template_key
from backend.teach import teach, write_config, undo_last
from backend.admin_chat import DEFAULT_ADMIN_PHONES


UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
DIST_DIR = Path(os.environ.get("FLUXIA_DIST", str(Path(__file__).parent.parent / "frontend" / "dist")))
PUBLIC_URL = os.environ.get("FLUXIA_PUBLIC_URL", "http://localhost:8100").rstrip("/")
DEFAULT_HERMES_URL = "https://hermescall.opus-sem-limites.com.br"
CLIENT_FIELDS = ("hours_enabled", "hours", "store_hours", "closed_action", "closed_message", "notify_phone")


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    db = await get_db()
    try:
        rows = await db.execute_fetchall("SELECT id FROM accounts WHERE role = 'admin' LIMIT 1")
        if not rows:
            await db.execute(
                "INSERT INTO accounts (email, password_hash, name, role) VALUES (?, ?, ?, 'admin')",
                (
                    os.environ.get("FLUXIA_ADMIN_EMAIL", "admin@fluxia.local").strip().lower(),
                    hash_password(os.environ.get("FLUXIA_ADMIN_PASSWORD", "admin123")),
                    "Admin",
                ),
            )
            await db.commit()
    finally:
        await db.close()
    task = asyncio.create_task(backup_loop())
    yield
    task.cancel()


async def backup_loop():
    while True:
        try:
            await asyncio.to_thread(snapshot)
        except Exception:
            traceback.print_exc()
        await asyncio.sleep(3600)


app = FastAPI(title="FluxIA", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Auth ---

async def get_current_account(request: Request) -> dict:
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        raise HTTPException(401, "Token ausente")
    payload = decode_token(auth[7:])
    if not payload:
        raise HTTPException(401, "Token inválido")
    db = await get_db()
    try:
        rows = await db.execute_fetchall("SELECT id, email, role FROM accounts WHERE id = ?", (int(payload["sub"]),))
    finally:
        await db.close()
    if not rows:
        raise HTTPException(401, "Conta removida")
    return dict(rows[0])


async def require_admin(account=Depends(get_current_account)) -> dict:
    if account["role"] != "admin":
        raise HTTPException(403, "Acesso negado")
    return account


class LoginBody(BaseModel):
    email: str
    password: str


_login_failures: dict[str, list[float]] = {}


def _too_many(key: str, limit: int) -> bool:
    now = time.monotonic()
    recent = [t for t in _login_failures.get(key, []) if now - t < 900]
    _login_failures[key] = recent
    return len(recent) >= limit


@app.post("/api/auth/login")
async def login(body: LoginBody, request: Request):
    email = body.email.strip().lower()
    ip = (request.headers.get("x-forwarded-for") or (request.client.host if request.client else "")).split(",")[0].strip()
    if _too_many(f"ip:{ip}", 20) or _too_many(f"email:{email}", 8):
        raise HTTPException(429, "Muitas tentativas. Espere 15 minutos e tente de novo.")
    db = await get_db()
    try:
        rows = await db.execute_fetchall("SELECT * FROM accounts WHERE email = ?", (email,))
    finally:
        await db.close()
    if not rows or not verify_password(body.password, rows[0]["password_hash"]):
        now = time.monotonic()
        _login_failures.setdefault(f"ip:{ip}", []).append(now)
        _login_failures.setdefault(f"email:{email}", []).append(now)
        raise HTTPException(401, "Email ou senha inválidos")
    acc = rows[0]
    token = create_token(acc["id"], acc["email"], acc["role"])
    return {"token": token, "account": {"id": acc["id"], "email": acc["email"], "name": acc["name"], "role": acc["role"]}}


@app.get("/api/auth/me")
async def me(account=Depends(get_current_account)):
    db = await get_db()
    try:
        rows = await db.execute_fetchall("SELECT id, email, name, role, created_at FROM accounts WHERE id = ?", (account["id"],))
        return dict(rows[0])
    finally:
        await db.close()


class PasswordBody(BaseModel):
    current: str
    new: str


@app.post("/api/auth/password")
async def change_password(body: PasswordBody, account=Depends(get_current_account)):
    if len(body.new) < 6:
        raise HTTPException(400, "A nova senha precisa ter pelo menos 6 caracteres")
    db = await get_db()
    try:
        rows = await db.execute_fetchall("SELECT password_hash FROM accounts WHERE id = ?", (account["id"],))
        if not verify_password(body.current, rows[0]["password_hash"]):
            raise HTTPException(400, "Senha atual incorreta")
        await db.execute("UPDATE accounts SET password_hash = ? WHERE id = ?", (hash_password(body.new), account["id"]))
        await db.commit()
        return {"ok": True}
    finally:
        await db.close()


# --- Hermes (WhatsApp) ---

async def hermes_config() -> tuple[str, str]:
    url = await get_setting("hermes_url", DEFAULT_HERMES_URL)
    key = await get_setting("hermes_api_key", "")
    return url, key


async def register_connection(account_id: int, session_id: str, hermes_url: str, api_key: str, label: str) -> int:
    token = secrets.token_urlsafe(24)
    await HermesClient(hermes_url, api_key).set_webhook(session_id, f"{PUBLIC_URL}/api/webhook/hermes/{token}")
    db = await get_db()
    try:
        cursor = await db.execute(
            """INSERT INTO whatsapp_connections (account_id, session_id, hermes_url, api_key, webhook_token, label)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (account_id, session_id, hermes_url, api_key, token, label),
        )
        await db.commit()
        return cursor.lastrowid
    finally:
        await db.close()


async def connection_by_id(conn_id: int | None) -> dict | None:
    if not conn_id:
        return None
    db = await get_db()
    try:
        rows = await db.execute_fetchall("SELECT * FROM whatsapp_connections WHERE id = ? AND active = 1", (conn_id,))
        return dict(rows[0]) if rows else None
    finally:
        await db.close()


async def whatsapp_status(conn: dict | None) -> dict:
    if not conn:
        return {"status": "disconnected", "phone": ""}
    try:
        info = await HermesClient(conn["hermes_url"], conn["api_key"]).get_session_info(conn["session_id"])
    except Exception:
        return {"status": "unknown", "phone": ""}
    if not info or not info.get("paired"):
        return {"status": "disconnected", "phone": ""}
    phone = (info.get("jid") or "").split("@")[0].split(":")[0]
    return {"status": "connected" if info.get("connected") else "offline", "phone": phone}


@app.post("/api/webhook/hermes/{token}")
async def hermes_webhook(token: str, request: Request):
    db = await get_db()
    try:
        rows = await db.execute_fetchall(
            "SELECT * FROM whatsapp_connections WHERE webhook_token = ? AND active = 1", (token,)
        )
    finally:
        await db.close()
    if not rows:
        raise HTTPException(404)
    try:
        payload = await request.json()
    except ValueError:
        raise HTTPException(400, "JSON inválido")
    conn = dict(rows[0])
    if payload.get("session") and payload["session"] != conn["session_id"]:
        raise HTTPException(400, "Sessão não confere")
    schedule_webhook(conn, payload)
    return {"ok": True}


# --- Configurações (admin) ---

class SettingsBody(BaseModel):
    hermes_url: str = ""
    hermes_api_key: str = ""
    admin_phones: str | None = None
    admin_lids: str | None = None


@app.get("/api/settings")
async def read_settings(account=Depends(require_admin)):
    url, key = await hermes_config()
    return {
        "hermes_url": url,
        "hermes_api_key_set": bool(key),
        "public_url": PUBLIC_URL,
        "admin_phones": await get_setting("admin_phones", DEFAULT_ADMIN_PHONES),
        "admin_lids": await get_setting("admin_lids", ""),
    }


@app.put("/api/settings")
async def save_settings(body: SettingsBody, account=Depends(require_admin)):
    if body.admin_lids is not None:
        lids = ["".join(ch for ch in p if ch.isdigit()) for p in body.admin_lids.replace(";", ",").split(",")]
        await set_setting("admin_lids", ",".join(x for x in lids if x))
    if body.admin_phones is not None:
        phones = [p for p in body.admin_phones.replace(";", ",").split(",") if "".join(ch for ch in p if ch.isdigit())]
        await set_setting("admin_phones", ",".join("".join(ch for ch in p if ch.isdigit()) for p in phones))
    if body.admin_phones is not None or body.admin_lids is not None:
        if not body.hermes_api_key.strip() and not body.hermes_url.strip():
            return {"ok": True, "hermes_agent_enabled": None}
    cur_url, cur_key = await hermes_config()
    url = (body.hermes_url.strip() or cur_url).rstrip("/")
    key = body.hermes_api_key.strip() or cur_key
    if not key:
        raise HTTPException(400, "Informe a chave de API do Hermes")
    try:
        hermes_settings = await HermesClient(url, key).get_settings()
    except HermesError as e:
        raise HTTPException(400, "Chave recusada pelo Hermes" if e.status in (401, 403) else f"Hermes respondeu {e.status}")
    except httpx.HTTPError:
        raise HTTPException(502, "Não consegui falar com o Hermes nessa URL")
    await set_setting("hermes_url", url)
    await set_setting("hermes_api_key", key)
    agent = hermes_settings.get("agent_chat") or {}
    return {"ok": True, "hermes_agent_enabled": bool(agent.get("enabled"))}


# --- Conexões de WhatsApp (admin) ---

class ConnectionBody(BaseModel):
    session_id: str
    hermes_url: str = ""
    api_key: str = ""
    label: str = ""


@app.get("/api/connections")
async def list_connections(account=Depends(require_admin)):
    db = await get_db()
    try:
        rows = await db.execute_fetchall(
            """SELECT id, session_id, label, hermes_url, active, created_at
               FROM whatsapp_connections WHERE account_id = ? AND active = 1""",
            (account["id"],),
        )
        return [dict(r) for r in rows]
    finally:
        await db.close()


@app.post("/api/connections")
async def create_connection(body: ConnectionBody, account=Depends(require_admin)):
    default_url, default_key = await hermes_config()
    try:
        conn_id = await register_connection(
            account["id"], body.session_id.strip(), body.hermes_url.strip() or default_url,
            body.api_key.strip() or default_key, body.label,
        )
    except HermesError as e:
        raise HTTPException(400, f"Hermes recusou: {e.detail}")
    except httpx.HTTPError:
        raise HTTPException(502, "Não consegui falar com o Hermes")
    return {"id": conn_id, "session_id": body.session_id}


@app.delete("/api/connections/{conn_id}")
async def delete_connection(conn_id: int, account=Depends(require_admin)):
    db = await get_db()
    try:
        await db.execute(
            "UPDATE whatsapp_connections SET active = 0 WHERE id = ? AND account_id = ?", (conn_id, account["id"])
        )
        await db.commit()
        return {"ok": True}
    finally:
        await db.close()


@app.get("/api/connections/{conn_id}/status")
async def connection_status(conn_id: int, account=Depends(require_admin)):
    db = await get_db()
    try:
        rows = await db.execute_fetchall(
            "SELECT * FROM whatsapp_connections WHERE id = ? AND account_id = ?", (conn_id, account["id"])
        )
    finally:
        await db.close()
    if not rows:
        raise HTTPException(404)
    return await whatsapp_status(dict(rows[0]))


# --- Fluxos (admin) ---

async def own_flow(flow_id: int, account: dict) -> dict:
    flow = await load_flow(flow_id)
    if not flow or flow["account_id"] != account["id"]:
        raise HTTPException(404, "Fluxo não encontrado")
    return flow


def flow_out(flow: dict) -> dict:
    out = dict(flow)
    out["template"] = flow_template_key(flow["type"])
    out["active"] = bool(flow["active"])
    return out


@app.get("/api/templates")
async def list_templates(account=Depends(require_admin)):
    return [{"key": k, "label": t["label"], "description": t["description"], "order_mode": t["config"]["order_mode"]}
            for k, t in TEMPLATES.items()]


@app.get("/api/flows")
async def list_flows(account=Depends(require_admin)):
    db = await get_db()
    try:
        rows = await db.execute_fetchall(
            "SELECT id FROM flows WHERE account_id = ? ORDER BY created_at DESC", (account["id"],)
        )
    finally:
        await db.close()
    return [flow_out(await load_flow(r["id"])) for r in rows]


@app.get("/api/flows/{flow_id}")
async def get_flow(flow_id: int, account=Depends(require_admin)):
    flow = await own_flow(flow_id, account)
    out = flow_out(flow)
    out["whatsapp"] = await whatsapp_status(await connection_by_id(flow["connection_id"]))
    return out


class FlowCreateBody(BaseModel):
    name: str
    template: str = "delivery_link"
    connection_id: int | None = None
    fields: dict = {}


@app.post("/api/flows")
async def create_flow(body: FlowCreateBody, account=Depends(require_admin)):
    if body.template not in TEMPLATES:
        raise HTTPException(400, "Modelo de fluxo inválido")
    name = body.name.strip()
    if not name:
        raise HTTPException(400, "Dê um nome ao fluxo")
    fields = {k: v for k, v in body.fields.items() if k in DEFAULTS}
    fields.setdefault("store_name", name)
    cfg = new_config(body.template, fields)
    db = await get_db()
    try:
        cursor = await db.execute(
            "INSERT INTO flows (account_id, connection_id, name, type, config) VALUES (?, ?, ?, ?, ?)",
            (account["id"], body.connection_id, name, body.template, json.dumps(cfg, ensure_ascii=False)),
        )
        await db.commit()
        flow_id = cursor.lastrowid
    finally:
        await db.close()
    await write_config(flow_id, cfg, "criacao", f"criado a partir do modelo {TEMPLATES[body.template]['label']}")
    return {"id": flow_id, "name": name}


class FlowUpdateBody(BaseModel):
    name: str | None = None
    connection_id: int | None = None
    config: dict | None = None
    note: str = ""


@app.put("/api/flows/{flow_id}")
async def update_flow(flow_id: int, body: FlowUpdateBody, account=Depends(require_admin)):
    flow = await own_flow(flow_id, account)
    db = await get_db()
    try:
        if body.name is not None and body.name.strip():
            await db.execute("UPDATE flows SET name = ? WHERE id = ?", (body.name.strip(), flow_id))
        if "connection_id" in body.model_fields_set:
            await db.execute("UPDATE flows SET connection_id = ? WHERE id = ?", (body.connection_id, flow_id))
        await db.commit()
    finally:
        await db.close()
    cfg = flow["config"]
    if body.config is not None:
        new_cfg = normalize({**flow["config"], **body.config})
        if new_cfg != flow["config"]:
            cfg = await write_config(flow_id, new_cfg, "painel", body.note or "editado no painel")
    return {"ok": True, "config": cfg}


@app.put("/api/flows/{flow_id}/toggle")
async def toggle_flow(flow_id: int, account=Depends(require_admin)):
    await own_flow(flow_id, account)
    db = await get_db()
    try:
        await db.execute("UPDATE flows SET active = CASE WHEN active = 1 THEN 0 ELSE 1 END WHERE id = ?", (flow_id,))
        await db.commit()
        return {"ok": True}
    finally:
        await db.close()


@app.delete("/api/flows/{flow_id}")
async def delete_flow(flow_id: int, account=Depends(require_admin)):
    await own_flow(flow_id, account)
    db = await get_db()
    try:
        for table in ("executions", "conversations", "menu_items", "orders", "client_flows", "flow_versions", "files", "polls"):
            await db.execute(f"DELETE FROM {table} WHERE flow_id = ?", (flow_id,))
        await db.execute("DELETE FROM flows WHERE id = ?", (flow_id,))
        await db.commit()
        return {"ok": True}
    finally:
        await db.close()


class TeachBody(BaseModel):
    instruction: str


@app.post("/api/flows/{flow_id}/teach")
async def teach_flow(flow_id: int, body: TeachBody, account=Depends(require_admin)):
    flow = await own_flow(flow_id, account)
    if not body.instruction.strip():
        raise HTTPException(400, "Escreva o que quer mudar")
    try:
        result = await teach(flow, body.instruction.strip(), "painel")
    except Exception as e:
        raise HTTPException(502, f"Não consegui aplicar agora: {str(e)[:200]}")
    result["config"] = flow["config"]
    return result


@app.get("/api/flows/{flow_id}/versions")
async def list_versions(flow_id: int, account=Depends(require_admin)):
    await own_flow(flow_id, account)
    db = await get_db()
    try:
        rows = await db.execute_fetchall(
            "SELECT id, source, note, created_at FROM flow_versions WHERE flow_id = ? ORDER BY id DESC LIMIT 50", (flow_id,)
        )
        return [dict(r) for r in rows]
    finally:
        await db.close()


@app.post("/api/flows/{flow_id}/versions/{version_id}/restore")
async def restore_version(flow_id: int, version_id: int, account=Depends(require_admin)):
    await own_flow(flow_id, account)
    db = await get_db()
    try:
        rows = await db.execute_fetchall(
            "SELECT config, created_at FROM flow_versions WHERE id = ? AND flow_id = ?", (version_id, flow_id)
        )
    finally:
        await db.close()
    if not rows:
        raise HTTPException(404)
    cfg = await write_config(flow_id, json.loads(rows[0]["config"]), "restaurado", f"voltou para a versão de {rows[0]['created_at']}")
    return {"ok": True, "config": cfg}


@app.post("/api/flows/{flow_id}/undo")
async def undo_flow(flow_id: int, account=Depends(require_admin)):
    await own_flow(flow_id, account)
    ok, msg = await undo_last(flow_id)
    if not ok:
        raise HTTPException(400, msg)
    return {"ok": True, "message": msg}


# --- Teste pelo painel ---

class TestMessageBody(BaseModel):
    flow_id: int
    message: str = ""
    vote: str = ""
    msg_type: str = "text"


def _test_phone(account: dict) -> str:
    return f"teste:{account['id']}"


@app.post("/api/test/message")
async def test_message(body: TestMessageBody, account=Depends(require_admin)):
    flow = await own_flow(body.flow_id, account)
    sender = CollectSender()
    run = Run(flow=flow, conn=None, phone=_test_phone(account), jid="", push_name="", sender=sender, mode="test")
    if body.vote:
        item = Incoming(type="vote", vote=body.vote)
    else:
        if not body.message.strip():
            raise HTTPException(400, "Escreva uma mensagem")
        item = Incoming(type=body.msg_type if body.msg_type in ("text", "audio", "image", "document") else "text",
                        text=body.message.strip())
    trigger = {"node": "trigger", "status": "ok", "info": "Teste pelo painel"}
    result = await process(run, [item], [trigger])
    return {"messages": sender.out, "steps": result["steps"], "execution_id": result["execution_id"], "status": result["status"]}


@app.post("/api/test/reset/{flow_id}")
async def test_reset(flow_id: int, account=Depends(require_admin)):
    await own_flow(flow_id, account)
    await reset_conversation(flow_id, _test_phone(account))
    return {"ok": True}


# --- Cardápio ---

class MenuItemBody(BaseModel):
    category: str = ""
    name: str
    description: str = ""
    price: float
    available: bool = True


async def own_menu_item(item_id: int, account: dict) -> dict:
    db = await get_db()
    try:
        rows = await db.execute_fetchall(
            "SELECT m.* FROM menu_items m JOIN flows f ON m.flow_id = f.id WHERE m.id = ? AND f.account_id = ?",
            (item_id, account["id"]),
        )
    finally:
        await db.close()
    if not rows:
        raise HTTPException(404)
    return dict(rows[0])


@app.get("/api/flows/{flow_id}/menu")
async def list_menu(flow_id: int, account=Depends(require_admin)):
    await own_flow(flow_id, account)
    return await get_menu_categories(flow_id)


@app.post("/api/flows/{flow_id}/menu")
async def add_menu_item(flow_id: int, body: MenuItemBody, account=Depends(require_admin)):
    await own_flow(flow_id, account)
    db = await get_db()
    try:
        cursor = await db.execute(
            "INSERT INTO menu_items (flow_id, category, name, description, price, available) VALUES (?, ?, ?, ?, ?, ?)",
            (flow_id, body.category, body.name, body.description, body.price, 1 if body.available else 0),
        )
        await db.commit()
        return {"id": cursor.lastrowid}
    finally:
        await db.close()


@app.put("/api/menu/{item_id}")
async def update_menu_item(item_id: int, body: MenuItemBody, account=Depends(require_admin)):
    await own_menu_item(item_id, account)
    db = await get_db()
    try:
        await db.execute(
            "UPDATE menu_items SET category = ?, name = ?, description = ?, price = ?, available = ? WHERE id = ?",
            (body.category, body.name, body.description, body.price, 1 if body.available else 0, item_id),
        )
        await db.commit()
        return {"ok": True}
    finally:
        await db.close()


@app.delete("/api/menu/{item_id}")
async def delete_menu_item(item_id: int, account=Depends(require_admin)):
    await own_menu_item(item_id, account)
    db = await get_db()
    try:
        await db.execute("DELETE FROM menu_items WHERE id = ?", (item_id,))
        await db.commit()
        return {"ok": True}
    finally:
        await db.close()


# --- Pedidos e agendamentos ---

@app.get("/api/flows/{flow_id}/orders")
async def list_orders(flow_id: int, account=Depends(require_admin)):
    await own_flow(flow_id, account)
    db = await get_db()
    try:
        rows = await db.execute_fetchall(
            "SELECT * FROM orders WHERE flow_id = ? ORDER BY created_at DESC LIMIT 100", (flow_id,)
        )
        return [dict(r) for r in rows]
    finally:
        await db.close()


class OrderStatusBody(BaseModel):
    status: str


@app.put("/api/orders/{order_id}/status")
async def update_order_status(order_id: int, body: OrderStatusBody, account=Depends(require_admin)):
    if body.status not in ("pending", "paid", "preparing", "delivering", "done", "confirmed", "cancelled"):
        raise HTTPException(400, "Status inválido")
    db = await get_db()
    try:
        rows = await db.execute_fetchall(
            "SELECT o.id FROM orders o JOIN flows f ON o.flow_id = f.id WHERE o.id = ? AND f.account_id = ?",
            (order_id, account["id"]),
        )
        if not rows:
            raise HTTPException(404)
        await db.execute("UPDATE orders SET status = ?, updated_at = datetime('now') WHERE id = ?", (body.status, order_id))
        await db.commit()
        return {"ok": True}
    finally:
        await db.close()


# --- Execuções ---

def execution_out(row) -> dict:
    d = dict(row)
    try:
        d["metadata"] = json.loads(d.get("metadata") or "{}")
    except ValueError:
        d["metadata"] = {}
    return d


@app.get("/api/executions")
async def list_executions(
    flow_id: int | None = None,
    phone: str | None = None,
    status: str | None = None,
    limit: int = 50,
    offset: int = 0,
    account=Depends(require_admin),
):
    conditions = ["f.account_id = ?"]
    params: list = [account["id"]]
    if flow_id:
        conditions.append("e.flow_id = ?")
        params.append(flow_id)
    if phone:
        conditions.append("e.phone LIKE ?")
        params.append(f"%{phone}%")
    if status:
        conditions.append("e.status = ?")
        params.append(status)
    where = " AND ".join(conditions)
    db = await get_db()
    try:
        rows = await db.execute_fetchall(
            f"""SELECT e.*, f.name as flow_name FROM executions e JOIN flows f ON e.flow_id = f.id
                WHERE {where} ORDER BY e.id DESC LIMIT ? OFFSET ?""",
            params + [min(limit, 200), offset],
        )
        count = await db.execute_fetchall(
            f"SELECT COUNT(*) as total FROM executions e JOIN flows f ON e.flow_id = f.id WHERE {where}", params
        )
        return {"items": [execution_out(r) for r in rows], "total": count[0]["total"]}
    finally:
        await db.close()


@app.get("/api/executions/{execution_id}")
async def get_execution(execution_id: int, account=Depends(require_admin)):
    db = await get_db()
    try:
        rows = await db.execute_fetchall(
            """SELECT e.*, f.name as flow_name FROM executions e JOIN flows f ON e.flow_id = f.id
               WHERE e.id = ? AND f.account_id = ?""",
            (execution_id, account["id"]),
        )
    finally:
        await db.close()
    if not rows:
        raise HTTPException(404)
    return execution_out(rows[0])


# --- Conversas ---

def conversation_out(row) -> dict:
    d = dict(row)
    d["history"] = json.loads(d["history"]) if d["history"] else []
    return d


@app.get("/api/flows/{flow_id}/conversations")
async def list_conversations(flow_id: int, account=Depends(require_admin)):
    await own_flow(flow_id, account)
    db = await get_db()
    try:
        rows = await db.execute_fetchall(
            "SELECT * FROM conversations WHERE flow_id = ? ORDER BY updated_at DESC LIMIT 100", (flow_id,)
        )
        return [conversation_out(r) for r in rows]
    finally:
        await db.close()


@app.delete("/api/flows/{flow_id}/conversations/{conv_id}")
async def delete_conversation(flow_id: int, conv_id: int, account=Depends(require_admin)):
    await own_flow(flow_id, account)
    db = await get_db()
    try:
        await db.execute("DELETE FROM conversations WHERE id = ? AND flow_id = ?", (conv_id, flow_id))
        await db.commit()
        return {"ok": True}
    finally:
        await db.close()


@app.post("/api/flows/{flow_id}/conversations/{conv_id}/resume")
async def resume_conversation(flow_id: int, conv_id: int, account=Depends(require_admin)):
    await own_flow(flow_id, account)
    await _resume(flow_id, conv_id)
    return {"ok": True}


async def _resume(flow_id: int, conv_id: int):
    await _set_ai(flow_id, conv_id, True)


class AIToggleBody(BaseModel):
    on: bool


async def _set_ai(flow_id: int, conv_id: int, on: bool):
    db = await get_db()
    try:
        await db.execute("UPDATE conversations SET paused_until = ? WHERE id = ? AND flow_id = ?",
                         ("" if on else AI_OFF, conv_id, flow_id))
        await db.commit()
    finally:
        await db.close()


@app.post("/api/flows/{flow_id}/conversations/{conv_id}/ai")
async def admin_conversation_ai(flow_id: int, conv_id: int, body: AIToggleBody, account=Depends(require_admin)):
    await own_flow(flow_id, account)
    await _set_ai(flow_id, conv_id, body.on)
    return {"ok": True}


# --- Arquivos recebidos (comprovantes) ---

async def _list_files(flow_id: int, kind: str | None) -> list[dict]:
    db = await get_db()
    try:
        if kind:
            rows = await db.execute_fetchall(
                "SELECT id, phone, kind, mimetype, caption, created_at FROM files WHERE flow_id = ? AND kind = ? ORDER BY id DESC LIMIT 100",
                (flow_id, kind),
            )
        else:
            rows = await db.execute_fetchall(
                "SELECT id, phone, kind, mimetype, caption, created_at FROM files WHERE flow_id = ? ORDER BY id DESC LIMIT 100",
                (flow_id,),
            )
        return [dict(r) for r in rows]
    finally:
        await db.close()


async def _file_response(file_id: int, flow_ids: list[int]) -> FileResponse:
    db = await get_db()
    try:
        rows = await db.execute_fetchall("SELECT * FROM files WHERE id = ?", (file_id,))
    finally:
        await db.close()
    if not rows or rows[0]["flow_id"] not in flow_ids:
        raise HTTPException(404)
    path = Path(rows[0]["path"]).resolve()
    if UPLOAD_DIR.resolve() not in path.parents or not path.is_file():
        raise HTTPException(404)
    return FileResponse(path, media_type=rows[0]["mimetype"] or None)


@app.get("/api/flows/{flow_id}/files")
async def list_flow_files(flow_id: int, kind: str | None = None, account=Depends(require_admin)):
    await own_flow(flow_id, account)
    return await _list_files(flow_id, kind)


@app.get("/api/files/{file_id}")
async def get_file(file_id: int, account=Depends(require_admin)):
    db = await get_db()
    try:
        rows = await db.execute_fetchall("SELECT id FROM flows WHERE account_id = ?", (account["id"],))
    finally:
        await db.close()
    return await _file_response(file_id, [r["id"] for r in rows])


# --- Painel inicial ---

@app.get("/api/dashboard")
async def dashboard(account=Depends(require_admin)):
    db = await get_db()
    try:
        one = lambda sql: db.execute_fetchall(sql, (account["id"],))
        flows = await one("SELECT COUNT(*) as total FROM flows WHERE account_id = ? AND active = 1")
        connections = await one("SELECT COUNT(*) as total FROM whatsapp_connections WHERE account_id = ? AND active = 1")
        today = await one(
            """SELECT COUNT(*) as total, SUM(e.status = 'error') as errors FROM executions e JOIN flows f ON e.flow_id = f.id
               WHERE f.account_id = ? AND e.created_at >= date('now') AND e.direction = 'in'"""
        )
        pending = await one(
            """SELECT COUNT(*) as total FROM orders o JOIN flows f ON o.flow_id = f.id
               WHERE f.account_id = ? AND o.status = 'pending'"""
        )
        paused = await one(
            """SELECT COUNT(*) as total FROM conversations c JOIN flows f ON c.flow_id = f.id
               WHERE f.account_id = ? AND c.paused_until > datetime('now')"""
        )
        return {
            "flows": flows[0]["total"],
            "connections": connections[0]["total"],
            "today_executions": today[0]["total"],
            "today_errors": today[0]["errors"] or 0,
            "pending_orders": pending[0]["total"],
            "paused_conversations": paused[0]["total"],
        }
    finally:
        await db.close()


@app.get("/api/events")
async def list_events(limit: int = 30, account=Depends(require_admin)):
    db = await get_db()
    try:
        rows = await db.execute_fetchall("SELECT * FROM events ORDER BY id DESC LIMIT ?", (min(limit, 200),))
        return [dict(r) for r in rows]
    finally:
        await db.close()


# --- Admin: clientes ---

class ClientBody(BaseModel):
    email: str
    password: str
    name: str = ""


class ClientUpdateBody(BaseModel):
    email: str | None = None
    name: str | None = None
    password: str | None = None


class ClientFlowBody(BaseModel):
    flow_id: int


@app.get("/api/clients")
async def list_clients(account=Depends(require_admin)):
    db = await get_db()
    try:
        rows = await db.execute_fetchall("SELECT id, email, name, created_at FROM accounts WHERE role = 'client' ORDER BY id")
        result = []
        for r in rows:
            d = dict(r)
            flows = await db.execute_fetchall(
                """SELECT f.id, f.name, f.type FROM client_flows cf JOIN flows f ON cf.flow_id = f.id
                   WHERE cf.account_id = ?""",
                (r["id"],),
            )
            d["flows"] = [dict(f) for f in flows]
            result.append(d)
        return result
    finally:
        await db.close()


@app.post("/api/clients")
async def create_client(body: ClientBody, account=Depends(require_admin)):
    email = body.email.strip().lower()
    if len(body.password) < 6:
        raise HTTPException(400, "A senha precisa ter pelo menos 6 caracteres")
    db = await get_db()
    try:
        if await db.execute_fetchall("SELECT id FROM accounts WHERE email = ?", (email,)):
            raise HTTPException(400, "Email já cadastrado")
        cursor = await db.execute(
            "INSERT INTO accounts (email, password_hash, name, role) VALUES (?, ?, ?, 'client')",
            (email, hash_password(body.password), body.name),
        )
        await db.commit()
        return {"id": cursor.lastrowid, "email": email}
    finally:
        await db.close()


@app.put("/api/clients/{client_id}")
async def update_client(client_id: int, body: ClientUpdateBody, account=Depends(require_admin)):
    db = await get_db()
    try:
        if not await db.execute_fetchall("SELECT id FROM accounts WHERE id = ? AND role = 'client'", (client_id,)):
            raise HTTPException(404)
        if body.email is not None and body.email.strip():
            email = body.email.strip().lower()
            if await db.execute_fetchall("SELECT id FROM accounts WHERE email = ? AND id != ?", (email, client_id)):
                raise HTTPException(400, "Email já cadastrado")
            await db.execute("UPDATE accounts SET email = ? WHERE id = ?", (email, client_id))
        if body.name is not None:
            await db.execute("UPDATE accounts SET name = ? WHERE id = ?", (body.name.strip(), client_id))
        if body.password:
            if len(body.password) < 6:
                raise HTTPException(400, "A senha precisa ter pelo menos 6 caracteres")
            await db.execute("UPDATE accounts SET password_hash = ? WHERE id = ?", (hash_password(body.password), client_id))
        await db.commit()
        return {"ok": True}
    finally:
        await db.close()


@app.post("/api/clients/{client_id}/flows")
async def link_client_flow(client_id: int, body: ClientFlowBody, account=Depends(require_admin)):
    await own_flow(body.flow_id, account)
    db = await get_db()
    try:
        await db.execute("INSERT OR IGNORE INTO client_flows (account_id, flow_id) VALUES (?, ?)", (client_id, body.flow_id))
        await db.commit()
        return {"ok": True}
    finally:
        await db.close()


@app.delete("/api/clients/{client_id}/flows/{flow_id}")
async def unlink_client_flow(client_id: int, flow_id: int, account=Depends(require_admin)):
    db = await get_db()
    try:
        await db.execute("DELETE FROM client_flows WHERE account_id = ? AND flow_id = ?", (client_id, flow_id))
        await db.commit()
        return {"ok": True}
    finally:
        await db.close()


@app.delete("/api/clients/{client_id}")
async def delete_client(client_id: int, account=Depends(require_admin)):
    db = await get_db()
    try:
        await db.execute("DELETE FROM client_flows WHERE account_id = ?", (client_id,))
        await db.execute("DELETE FROM accounts WHERE id = ? AND role = 'client'", (client_id,))
        await db.commit()
        return {"ok": True}
    finally:
        await db.close()


# --- Área do cliente: conecta o WhatsApp, liga/desliga, horário, avisos, comprovantes ---

async def client_flow(account_id: int, flow_id: int) -> dict:
    db = await get_db()
    try:
        rows = await db.execute_fetchall(
            "SELECT 1 FROM client_flows WHERE account_id = ? AND flow_id = ?", (account_id, flow_id)
        )
    finally:
        await db.close()
    flow = await load_flow(flow_id) if rows else None
    if not flow:
        raise HTTPException(404, "Não encontrado")
    return flow


async def client_flow_ids(account_id: int) -> list[int]:
    db = await get_db()
    try:
        rows = await db.execute_fetchall("SELECT flow_id FROM client_flows WHERE account_id = ?", (account_id,))
        return [r["flow_id"] for r in rows]
    finally:
        await db.close()


class PairBody(BaseModel):
    phone: str


async def ensure_session(flow: dict) -> dict:
    """Devolve a conexão do fluxo com uma linha que existe no Hermes, criando ou recriando se preciso."""
    conn = await connection_by_id(flow["connection_id"])
    if conn:
        client = HermesClient(conn["hermes_url"], conn["api_key"])
        if await client.get_session_info(conn["session_id"]):
            return conn
        # O Hermes apaga as linhas ainda não pareadas quando reinicia: cria outra com o mesmo webhook.
        session_id = await client.create_session(f"FluxIA - {flow['name']}")
        await client.set_webhook(session_id, f"{PUBLIC_URL}/api/webhook/hermes/{conn['webhook_token']}")
        db = await get_db()
        try:
            await db.execute("UPDATE whatsapp_connections SET session_id = ? WHERE id = ?", (session_id, conn["id"]))
            await db.commit()
        finally:
            await db.close()
        await record_event("pareamento", f"a linha {conn['session_id']} não existe mais no Hermes; criada a {session_id}", flow["id"], level="AVISO")
        return await connection_by_id(conn["id"])
    hermes_url, api_key = await hermes_config()
    if not api_key:
        raise HTTPException(503, "A plataforma ainda não foi configurada. Fale com o suporte.")
    session_id = await HermesClient(hermes_url, api_key).create_session(f"FluxIA - {flow['name']}")
    conn_id = await register_connection(flow["account_id"], session_id, hermes_url, api_key, flow["name"])
    db = await get_db()
    try:
        await db.execute("UPDATE flows SET connection_id = ? WHERE id = ?", (conn_id, flow["id"]))
        await db.commit()
    finally:
        await db.close()
    return await connection_by_id(conn_id)


@app.get("/api/client/flows")
async def client_list_flows(account=Depends(get_current_account)):
    result = []
    for flow_id in sorted(await client_flow_ids(account["id"])):
        flow = await load_flow(flow_id)
        if not flow:
            continue
        db = await get_db()
        try:
            stats = await db.execute_fetchall(
                """SELECT COUNT(*) AS n, COUNT(DISTINCT phone) AS clients FROM executions
                   WHERE flow_id = ? AND direction = 'in' AND created_at >= date('now')
                   AND phone NOT LIKE 'sim:%' AND phone NOT LIKE 'teste:%'""",
                (flow_id,),
            )
            receipts = await db.execute_fetchall(
                "SELECT COUNT(*) AS n FROM files WHERE flow_id = ? AND kind = 'comprovante' AND created_at >= date('now')",
                (flow_id,),
            )
        finally:
            await db.close()
        result.append({
            "id": flow["id"],
            "name": flow["name"],
            "active": bool(flow["active"]),
            "whatsapp": await whatsapp_status(await connection_by_id(flow["connection_id"])),
            "settings": {k: flow["config"][k] for k in CLIENT_FIELDS},
            "today": {"messages": stats[0]["n"], "clients": stats[0]["clients"], "receipts": receipts[0]["n"]},
        })
    return result


@app.post("/api/client/flows/{flow_id}/pair")
async def client_pair(flow_id: int, body: PairBody, account=Depends(get_current_account)):
    flow = await client_flow(account["id"], flow_id)
    phone = "".join(ch for ch in body.phone if ch.isdigit())
    if len(phone) in (10, 11):
        phone = "55" + phone
    if len(phone) < 12:
        raise HTTPException(400, "Informe o número com DDD")
    step = "preparar a linha no Hermes"
    try:
        conn = await ensure_session(flow)
        step = "pedir o código"
        code = await HermesClient(conn["hermes_url"], conn["api_key"]).pair_code(conn["session_id"], phone)
    except HermesError as e:
        await record_event("pareamento", f"fluxo {flow_id} ({flow['name']}), número {phone}, ao {step}: Hermes {e.status} {e.detail}", flow_id)
        if "already paired" in e.detail:
            raise HTTPException(409, "Este WhatsApp já está conectado.")
        low = e.detail.lower()
        if "rate" in low or "429" in low or "too many" in low:
            raise HTTPException(429, "O WhatsApp limitou as tentativas de conexão deste número. Espere uns 10 minutos ou use \"Conectar com QR code\".")
        if "bad-request" in low:
            raise HTTPException(400, "O WhatsApp não aceitou este número para conexão por código (comum em números do Pará sem o 9 no cadastro). Use \"Conectar com QR code\".")
        raise HTTPException(502, f"Não foi possível gerar o código. Tente \"Conectar com QR code\". (Motivo: {e.detail[:160]})")
    except httpx.HTTPError as e:
        await record_event("pareamento", f"fluxo {flow_id}, número {phone}, ao {step}: sem resposta do Hermes ({type(e).__name__}: {e})", flow_id)
        raise HTTPException(502, "Serviço do WhatsApp indisponível. Tente de novo em instantes.")
    await record_event("pareamento", f"fluxo {flow_id}, número {phone}: código gerado, esperando a loja digitar", flow_id, level="OK")
    return {"code": code}


@app.post("/api/client/flows/{flow_id}/qr")
async def client_qr(flow_id: int, account=Depends(get_current_account)):
    flow = await client_flow(account["id"], flow_id)
    step = "preparar a linha no Hermes"
    try:
        conn = await ensure_session(flow)
        step = "gerar o QR"
        qr = await HermesClient(conn["hermes_url"], conn["api_key"]).start_qr(conn["session_id"])
    except HermesError as e:
        if "already paired" in e.detail:
            raise HTTPException(409, "Este WhatsApp já está conectado.")
        await record_event("pareamento", f"fluxo {flow_id}, QR, ao {step}: Hermes {e.status} {e.detail}", flow_id)
        raise HTTPException(502, f"Não foi possível gerar o QR agora. Tente de novo. (Motivo: {e.detail[:160]})")
    except httpx.HTTPError as e:
        await record_event("pareamento", f"fluxo {flow_id}, QR, ao {step}: sem resposta do Hermes ({type(e).__name__}: {e})", flow_id)
        raise HTTPException(502, "Serviço do WhatsApp indisponível. Tente de novo em instantes.")
    return {"qr": qr}


@app.post("/api/client/flows/{flow_id}/disconnect")
async def client_disconnect(flow_id: int, account=Depends(get_current_account)):
    flow = await client_flow(account["id"], flow_id)
    conn = await connection_by_id(flow["connection_id"])
    if conn:
        try:
            await HermesClient(conn["hermes_url"], conn["api_key"]).logout(conn["session_id"])
        except HermesError:
            pass
        except httpx.HTTPError:
            raise HTTPException(502, "Serviço do WhatsApp indisponível. Tente de novo em instantes.")
    return {"ok": True}


@app.put("/api/client/flows/{flow_id}/toggle")
async def client_toggle(flow_id: int, account=Depends(get_current_account)):
    await client_flow(account["id"], flow_id)
    db = await get_db()
    try:
        await db.execute("UPDATE flows SET active = CASE WHEN active = 1 THEN 0 ELSE 1 END WHERE id = ?", (flow_id,))
        await db.commit()
        return {"ok": True}
    finally:
        await db.close()


@app.put("/api/client/flows/{flow_id}/settings")
async def client_settings(flow_id: int, request: Request, account=Depends(get_current_account)):
    flow = await client_flow(account["id"], flow_id)
    body = await request.json()
    changes = {k: v for k, v in (body or {}).items() if k in CLIENT_FIELDS}
    if not changes:
        raise HTTPException(400, "Nada para salvar")
    cfg = await write_config(flow_id, {**flow["config"], **changes}, "cliente", "opções alteradas pela loja")
    return {"ok": True, "settings": {k: cfg[k] for k in CLIENT_FIELDS}}


@app.get("/api/client/flows/{flow_id}/files")
async def client_files(flow_id: int, kind: str | None = "comprovante", account=Depends(get_current_account)):
    await client_flow(account["id"], flow_id)
    return await _list_files(flow_id, kind)


@app.get("/api/client/files/{file_id}")
async def client_file(file_id: int, account=Depends(get_current_account)):
    return await _file_response(file_id, await client_flow_ids(account["id"]))


@app.get("/api/client/flows/{flow_id}/paused")
async def client_paused(flow_id: int, account=Depends(get_current_account)):
    await client_flow(account["id"], flow_id)
    db = await get_db()
    try:
        rows = await db.execute_fetchall(
            """SELECT id, phone, customer_name, paused_until FROM conversations
               WHERE flow_id = ? AND paused_until > datetime('now') AND phone NOT LIKE 'sim:%' AND phone NOT LIKE 'teste:%'
               ORDER BY paused_until DESC""",
            (flow_id,),
        )
        return [dict(r) for r in rows]
    finally:
        await db.close()


@app.post("/api/client/flows/{flow_id}/conversations/{conv_id}/resume")
async def client_resume(flow_id: int, conv_id: int, account=Depends(get_current_account)):
    await client_flow(account["id"], flow_id)
    await _resume(flow_id, conv_id)
    return {"ok": True}


@app.get("/api/client/flows/{flow_id}/contacts")
async def client_contacts(flow_id: int, q: str = "", account=Depends(get_current_account)):
    await client_flow(account["id"], flow_id)
    like = f"%{q.strip()}%"
    db = await get_db()
    try:
        rows = await db.execute_fetchall(
            """SELECT id, phone, customer_name, paused_until, updated_at, history FROM conversations
               WHERE flow_id = ? AND phone NOT LIKE 'sim:%' AND phone NOT LIKE 'teste:%'
               AND (? = '%%' OR customer_name LIKE ? OR phone LIKE ?)
               ORDER BY updated_at DESC LIMIT 40""",
            (flow_id, like, like, like),
        )
    finally:
        await db.close()
    out = []
    for r in rows:
        history = json.loads(r["history"] or "[]")
        last = next((h["content"] for h in reversed(history) if h.get("role") == "user"), "")
        out.append({
            "id": r["id"], "phone": r["phone"], "customer_name": r["customer_name"], "updated_at": r["updated_at"],
            "paused_until": r["paused_until"], "ai_off": r["paused_until"] >= AI_OFF, "last": last[:120],
        })
    return out


@app.post("/api/client/flows/{flow_id}/conversations/{conv_id}/ai")
async def client_conversation_ai(flow_id: int, conv_id: int, body: AIToggleBody, account=Depends(get_current_account)):
    await client_flow(account["id"], flow_id)
    await _set_ai(flow_id, conv_id, body.on)
    return {"ok": True}


# --- Painel (frontend compilado) ---

if DIST_DIR.is_dir():
    app.mount("/assets", StaticFiles(directory=DIST_DIR / "assets"), name="assets")

    @app.get("/{path:path}", include_in_schema=False)
    async def spa(path: str):
        if path.startswith("api/"):
            raise HTTPException(404)
        candidate = (DIST_DIR / path).resolve()
        if path and candidate.is_file() and DIST_DIR.resolve() in candidate.parents:
            return FileResponse(candidate)
        return FileResponse(DIST_DIR / "index.html")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8100, reload=True)
