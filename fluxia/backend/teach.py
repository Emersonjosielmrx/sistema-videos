"""Ensinar o agente: o administrador escreve o que quer mudar e a IA traduz em regras ou em troca de campos."""

import json
import re
from datetime import datetime

from .agent import ask_agent, SMART_MODEL
from .db import get_db
from .flow_config import normalize, TEACHABLE_FIELDS, DEFAULTS

TEACH_SYSTEM = """Você ajusta a configuração de um agente de atendimento de WhatsApp a pedido do administrador da plataforma.

Responda SOMENTE com um objeto JSON, sem texto antes ou depois, neste formato:
{"add_rules": ["regra nova"], "remove_rules": [número da regra], "set": {"campo": valor}, "reply": "mensagem curta para o administrador"}

Como decidir:
- Mudança de comportamento, tom, o que dizer ou não dizer, como reagir a situações: use add_rules. Escreva cada regra como uma instrução clara e completa para o agente, em português.
- Pedido para esquecer/apagar/desfazer uma regra existente: use remove_rules com os números da lista de regras atuais.
- Troca de um dado (link, endereço, horário, chave Pix, mensagens fixas, o que fazer com áudio etc.): use set, só com os campos permitidos abaixo e só quando o administrador pedir.
- Se for uma pergunta, um pedido ambíguo ou algo que não dá para fazer com estes recursos, não mude nada (listas e set vazios) e explique em reply.
- reply: uma ou duas frases dizendo exatamente o que mudou, em português informal.

Campos permitidos em set:
{fields}"""


async def save_version(flow_id: int, config: dict, source: str, note: str = ""):
    db = await get_db()
    try:
        await db.execute(
            "INSERT INTO flow_versions (flow_id, config, source, note) VALUES (?, ?, ?, ?)",
            (flow_id, json.dumps(config, ensure_ascii=False), source, note[:500]),
        )
        await db.commit()
    finally:
        await db.close()


async def write_config(flow_id: int, config: dict, source: str, note: str = "") -> dict:
    cfg = normalize(config)
    db = await get_db()
    try:
        # Fluxo criado antes do histórico: guarda o estado atual para o "desfazer" ter para onde voltar.
        has_versions = await db.execute_fetchall("SELECT 1 FROM flow_versions WHERE flow_id = ? LIMIT 1", (flow_id,))
        if not has_versions:
            old = await db.execute_fetchall("SELECT config FROM flows WHERE id = ?", (flow_id,))
            if old:
                await db.execute(
                    "INSERT INTO flow_versions (flow_id, config, source, note) VALUES (?, ?, 'original', 'versão antes do histórico')",
                    (flow_id, json.dumps(normalize(json.loads(old[0]["config"] or "{}")), ensure_ascii=False)),
                )
        await db.execute("UPDATE flows SET config = ? WHERE id = ?", (json.dumps(cfg, ensure_ascii=False), flow_id))
        await db.commit()
    finally:
        await db.close()
    await save_version(flow_id, cfg, source, note)
    return cfg


async def undo_last(flow_id: int) -> tuple[bool, str]:
    """Volta para a versão anterior à última alteração."""
    db = await get_db()
    try:
        rows = await db.execute_fetchall(
            "SELECT id, config, source, note FROM flow_versions WHERE flow_id = ? ORDER BY id DESC LIMIT 2", (flow_id,)
        )
    finally:
        await db.close()
    if len(rows) < 2:
        return False, "Não tem alteração anterior para desfazer."
    previous = json.loads(rows[1]["config"])
    await write_config(flow_id, previous, "desfazer", f"desfez: {rows[0]['note'] or rows[0]['source']}")
    return True, f"Desfeito: {rows[0]['note'] or rows[0]['source']}"


def _parse_json(text: str) -> dict:
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if not m:
        raise ValueError("a IA não devolveu JSON")
    return json.loads(m.group(0))


def _coerce(field: str, value):
    default = DEFAULTS[field]
    if isinstance(default, bool):
        return value if isinstance(value, bool) else str(value).strip().lower() in ("true", "1", "sim")
    if isinstance(default, int):
        return int(value)
    return str(value).strip()


async def teach(flow: dict, instruction: str, source: str) -> dict:
    cfg = flow["config"]
    rules = "\n".join(f"{i}. {r['text']}" for i, r in enumerate(cfg["learned_rules"], 1)) or "(nenhuma)"
    current = {k: cfg[k] for k in TEACHABLE_FIELDS}
    fields = "\n".join(f"- {k}: {desc}" for k, desc in TEACHABLE_FIELDS.items())
    user = (
        f"PROMPT ATUAL DO AGENTE:\n{cfg['prompt']}\n\n"
        f"REGRAS ATUAIS:\n{rules}\n\n"
        f"VALORES ATUAIS DOS CAMPOS:\n{json.dumps(current, ensure_ascii=False, indent=1)}\n\n"
        f"PEDIDO DO ADMINISTRADOR:\n{instruction}"
    )
    raw = await ask_agent(TEACH_SYSTEM.replace("{fields}", fields), [{"role": "user", "content": user}],
                          model=SMART_MODEL, max_tokens=1200, timeout=90)
    plan = _parse_json(raw)

    new_cfg = json.loads(json.dumps(cfg))
    changes: list[str] = []
    remove = sorted({int(n) for n in plan.get("remove_rules") or [] if str(n).isdigit()}, reverse=True)
    for n in remove:
        if 1 <= n <= len(new_cfg["learned_rules"]):
            removed = new_cfg["learned_rules"].pop(n - 1)
            changes.append(f"regra removida: {removed['text']}")
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    for text in plan.get("add_rules") or []:
        text = str(text).strip()
        if text:
            new_cfg["learned_rules"].append({"text": text[:600], "created_at": now, "source": source})
            changes.append(f"regra nova: {text}")
    for field, value in (plan.get("set") or {}).items():
        if field not in TEACHABLE_FIELDS:
            continue
        try:
            value = _coerce(field, value)
        except (TypeError, ValueError):
            continue
        if new_cfg.get(field) != value:
            new_cfg[field] = value
            changes.append(f"{field} = {value}")

    reply = str(plan.get("reply") or "").strip()
    if changes:
        await write_config(flow["id"], new_cfg, source, instruction)
        flow["config"] = normalize(new_cfg)
    return {"changed": bool(changes), "changes": changes, "reply": reply or ("Feito." if changes else "Não mudei nada.")}


async def remove_rule(flow: dict, number: int, source: str) -> str:
    rules = flow["config"]["learned_rules"]
    if not 1 <= number <= len(rules):
        return f"Não existe a regra {number}. Mande *regras* para ver a lista."
    new_cfg = json.loads(json.dumps(flow["config"]))
    removed = new_cfg["learned_rules"].pop(number - 1)
    await write_config(flow["id"], new_cfg, source, f"apagou regra {number}")
    flow["config"] = normalize(new_cfg)
    return f"Regra {number} apagada: {removed['text']}"
