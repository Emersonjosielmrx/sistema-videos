import asyncio
import json
import time
import traceback
from collections import OrderedDict

from . import admin_chat
from .db import get_db, record_event
from .engine import (
    Incoming, Run, HermesSender, SENT_IDS, process, flow_for_connection, load_flow,
    get_conversation, save_conversation, set_pause, set_ai_off, utc_in, log_execution,
)

IGNORED_TYPES = {"sticker", "reaction", "poll", "event", "unknown"}

_seen: OrderedDict[str, None] = OrderedDict()
_locks: dict[str, asyncio.Lock] = {}
_pending: dict[str, list] = {}
_timers: dict[str, asyncio.Task] = {}
_tasks: set[asyncio.Task] = set()
_owner_last: dict[str, float] = {}  # quando a loja mandou a última mensagem em cada conversa


def _already_seen(key: str) -> bool:
    # O Hermes reenvia webhooks que falharam; a mesma mensagem não pode gerar duas respostas.
    if key in _seen:
        return True
    _seen[key] = None
    if len(_seen) > 5000:
        _seen.popitem(last=False)
    return False


def _spawn(coro):
    task = asyncio.create_task(coro)
    _tasks.add(task)
    task.add_done_callback(_tasks.discard)
    return task


def schedule(connection: dict, payload: dict):
    _spawn(_handle(connection, payload))


def lock_for(flow_id: int, phone: str) -> asyncio.Lock:
    return _locks.setdefault(f"{flow_id}:{phone}", asyncio.Lock())


async def enqueue(flow: dict, conn: dict, phone: str, jid: str, push_name: str, mode: str, item: Incoming):
    """Junta mensagens seguidas do mesmo cliente e responde uma vez só, depois de alguns segundos sem mensagem nova."""
    key = f"{flow['id']}:{phone}"
    _pending.setdefault(key, []).append(item)
    old = _timers.get(key)
    if old and not old.done():
        old.cancel()
    delay = 0 if item.type == "vote" else flow["config"]["buffer_seconds"]
    _timers[key] = _spawn(_fire(key, delay, flow["id"], conn, phone, jid, push_name, mode))


async def _fire(key: str, delay: float, flow_id: int, conn: dict, phone: str, jid: str, push_name: str, mode: str):
    try:
        await asyncio.sleep(delay)
    except asyncio.CancelledError:
        return
    if _timers.get(key) is asyncio.current_task():
        del _timers[key]
    async with lock_for(flow_id, phone):
        items = _pending.pop(key, [])
        if not items:
            return
        flow = await load_flow(flow_id)
        if not flow:
            return
        run = Run(flow=flow, conn=conn, phone=phone, jid=jid, push_name=push_name,
                  sender=HermesSender(conn, jid), mode=mode)
        trigger = {"node": "trigger", "status": "ok",
                   "info": ("Simulação do administrador" if mode == "sim" else "Mensagem recebida no WhatsApp")
                   + (f" de {push_name}" if push_name and mode != "sim" else "")}
        try:
            await process(run, items, [trigger])
        except Exception as e:
            traceback.print_exc()
            await record_event("mensagem", f"fluxo {flow_id}, conversa {phone}: {type(e).__name__}: {str(e)[:300]}", flow_id)
            await log_execution(flow_id, conn["id"], "in", phone, items[-1].type,
                                "\n".join(i.text for i in items), "", "error",
                                {"steps": run.steps + [{"node": "send", "status": "error", "info": str(e)[:200]}],
                                 "mode": mode, "error": str(e)[:500]})


async def _handle(conn: dict, payload: dict):
    try:
        event = payload.get("event")
        data = payload.get("data") or {}
        if event == "poll_vote":
            await _handle_vote(conn, data)
        elif event == "message":
            await _handle_message(conn, data)
    except Exception as e:
        traceback.print_exc()
        await record_event("webhook", f"conexão {conn['id']}, evento {payload.get('event')}: {type(e).__name__}: {str(e)[:300]}")


async def _handle_message(conn: dict, data: dict):
    chat = data.get("chat") or ""
    if not chat or data.get("isGroup") or chat.endswith(("@g.us", "@broadcast", "@newsletter")):
        return
    msg_id = data.get("id") or ""
    msg_type = data.get("type") or "text"
    if data.get("fromMe"):
        # Ao conectar chegam eventos internos (tipo "unknown") marcados como fromMe: não é a loja respondendo.
        real = msg_type not in IGNORED_TYPES and (msg_type != "text" or (data.get("text") or "").strip())
        if real and msg_id not in SENT_IDS:
            await _owner_replied(conn, chat, data)
        return
    if msg_type in IGNORED_TYPES:
        return
    reply = data.get("buttonReply") or {}
    choice = reply.get("id") or reply.get("text")
    if reply.get("messageId") and choice and await _choice(conn, reply["messageId"], choice, chat, f"btn:{conn['id']}:{msg_id}"):
        return
    text = (data.get("text") or "").strip()
    if msg_type == "text" and not text:
        return
    if msg_id and _already_seen(f"{conn['id']}:{msg_id}"):
        return

    item = Incoming(id=msg_id, type=msg_type, text=text, raw=data.get("raw"), arrived_at=time.time())
    push_name = data.get("pushName") or ""
    flow = await flow_for_connection(conn["id"])
    if await admin_chat.is_admin(conn, chat):
        await admin_chat.AdminChat(conn, flow, chat, enqueue).handle(item, push_name)
        return
    if not flow:
        return
    phone = chat.split("@")[0].split(":")[0]
    await enqueue(flow, conn, phone, chat, push_name, "live", item)


async def _handle_vote(conn: dict, data: dict):
    names = data.get("selectedNames") or []
    poll_id = data.get("pollMessageId") or ""
    if not names or not poll_id:
        return
    await _choice(conn, poll_id, names[0], data.get("chat") or "",
                  f"vote:{conn['id']}:{poll_id}:{data.get('voter')}:{data.get('timestamp')}")


async def _choice(conn: dict, poll_id: str, choice: str, chat: str, seen_key: str) -> bool:
    """Escolha numa enquete, botão ou lista que o FluxIA mandou. False = a mensagem com as opções não é nossa."""
    db = await get_db()
    try:
        rows = await db.execute_fetchall("SELECT * FROM polls WHERE message_id = ?", (poll_id,))
    finally:
        await db.close()
    if not rows:
        return False
    if _already_seen(seen_key):
        return True
    poll = dict(rows[0])
    flow = await load_flow(poll["flow_id"])
    if not flow or flow["connection_id"] != conn["id"] or not chat:
        return True
    if poll["kind"] == "admin":
        await admin_chat.AdminChat(conn, flow, chat, enqueue).vote(choice)
        return True
    mode = "sim" if poll["phone"].startswith("sim:") else "live"
    await enqueue(flow, conn, poll["phone"], chat, "", mode, Incoming(id=poll_id, type="vote", vote=choice))
    return True


async def _owner_replied(conn: dict, chat: str, data: dict):
    """A loja respondeu à mão pelo celular: a IA fica quieta nessa conversa por um tempo."""
    flow = await flow_for_connection(conn["id"])
    if not flow:
        return
    cfg = flow["config"]
    phone = chat.split("@")[0].split(":")[0]
    # 02/11: o número admin também conversa de verdade com o dono da linha (Emerson ↔ Luiz). Ele é atendido como
    # cliente na conversa "sim:"; antes a resposta do dono era ignorada aqui e o bot seguia respondendo o admin.
    if await admin_chat.is_admin(conn, chat):
        phone = f"sim:{phone}"
    text = (data.get("text") or "").strip() or f"[{data.get('type') or 'mensagem'}]"
    sent_at = (data.get("timestamp") or time.time() * 1000) / 1000
    key = f"{flow['id']}:{phone}"
    previous = _owner_last.get(key)
    _owner_last[key] = sent_at
    async with lock_for(flow["id"], phone):
        conv = await get_conversation(flow["id"], phone, chat)
        conv["history"].append({"role": "assistant", "content": f"[Resposta da equipe da loja]: {text}"})
        await save_conversation(conv)
        if cfg["owner_off_two_messages"] and previous is not None and 0 <= sent_at - previous < 60:
            await set_ai_off(flow["id"], phone)
            info = "A loja mandou 2 mensagens seguidas em menos de 1 min: IA desligada para este contato"
            await record_event("contato", f"fluxo {flow['id']}, conversa {phone} ({conv.get('customer_name') or 'sem nome'}): {info}", flow["id"], level="OK")
        elif cfg["pause_on_owner_reply"] and cfg["pause_minutes"] > 0:
            await set_pause(flow["id"], phone, chat, utc_in(cfg["pause_minutes"]))
            info = f"A loja respondeu à mão: IA pausada por {cfg['pause_minutes']} min nesta conversa"
        else:
            info = "A loja respondeu à mão (pausa automática desligada)"
    await log_execution(flow["id"], conn["id"], "owner", phone, data.get("type") or "text", text[:500], "", "skip",
                        {"steps": [{"node": "filter", "status": "stop", "info": info}], "mode": "live"})
