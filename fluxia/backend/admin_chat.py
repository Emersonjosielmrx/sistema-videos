"""Modo administrador pelo WhatsApp: o número do admin conversa com o agente para ensinar, simular um cliente e reiniciar."""

import json
import re
import time
import unicodedata

from .db import get_db, get_setting
from .engine import Incoming, reset_conversation, remember_sent
from .hermes import HermesClient
from .media import find_media, download, transcribe
from .teach import teach, undo_last, remove_rule

DEFAULT_ADMIN_PHONES = "5591984698653"
GREETINGS = {"oi", "ola", "menu", "ajuda", "admin", "help", "comandos", "bom dia", "boa tarde", "boa noite", "inicio"}
ADMIN_BUTTONS = {
    "🧪 Simular cliente": "simular",
    "🔄 Reiniciar simulação": "reiniciar",
    "📋 Ver regras": "regras",
    "↩️ Desfazer última mudança": "desfazer",
    "⏯️ Ligar/desligar atendimento": "alternar",
    "📊 Status de hoje": "status",
}
ADMIN_IDLE_MINUTES = 15
_lid_cache: dict[int, tuple[float, set[str], set[str]]] = {}


def digits(s: str) -> str:
    return "".join(ch for ch in s or "" if ch.isdigit())


def phone_variants(phone: str) -> set[str]:
    """Números do Brasil podem existir no WhatsApp com ou sem o 9º dígito."""
    p = digits(phone)
    if len(p) in (10, 11):  # só DDD + número: é do Brasil
        p = "55" + p
    out = {p}
    if p.startswith("55") and len(p) == 13 and p[4] == "9":
        out.add(p[:4] + p[5:])
    if p.startswith("55") and len(p) == 12:
        out.add(p[:4] + "9" + p[4:])
    return out


async def _flow_admin_phones(conn_id: int) -> str:
    """Admins só desta linha (campo admin_phones do fluxo): ex. o dono da Globo manda só no fluxo da Globo."""
    db = await get_db()
    try:
        rows = await db.execute_fetchall("SELECT config FROM flows WHERE connection_id = ?", (conn_id,))
    finally:
        await db.close()
    out = []
    for r in rows:
        try:
            out.append(str(json.loads(r["config"] or "{}").get("admin_phones") or ""))
        except ValueError:
            pass
    return ",".join(out)


async def admin_phones(conn: dict | None = None) -> set[str]:
    raw = await get_setting("admin_phones", DEFAULT_ADMIN_PHONES)
    parts = re.split(r"[,;\s]+", raw)
    if conn:
        # no fluxo o número vem como a loja digitou ("91 98246-9729"): separa só por vírgula/linha
        parts += re.split(r"[,;\n]+", await _flow_admin_phones(conn["id"]))
    phones: set[str] = set()
    for p in parts:
        if digits(p):
            phones |= phone_variants(p)
    return phones


async def _admin_lids(conn: dict, phones: set[str]) -> set[str]:
    cached = _lid_cache.get(conn["id"])
    if cached and cached[2] != phones:
        cached = None  # lista de admins mudou: pergunta os LIDs de novo
    if cached and time.monotonic() - cached[0] < (21600 if cached[1] else 300):
        return cached[1]
    lids: set[str] = set()
    client = HermesClient(conn["hermes_url"], conn["api_key"])
    for p in phones:
        try:
            info = await client.contact_info(conn["session_id"], p)
            if info.get("lid"):
                lids.add(info["lid"].split("@")[0].split(":")[0])
        except Exception:
            pass
    _lid_cache[conn["id"]] = (time.monotonic(), lids, phones)
    return lids


async def is_admin(conn: dict, chat: str) -> bool:
    user, _, server = chat.partition("@")
    user = user.split(":")[0]
    phones = await admin_phones(conn)
    if server == "s.whatsapp.net":
        return user in phones
    if server == "lid":
        # O LID é fixo por conta de WhatsApp; o Hermes nem sempre devolve, então também vale a lista salva.
        known = {digits(x) for x in re.split(r"[,;\s]+", await get_setting("admin_lids", "")) if digits(x)}
        # a lista de admins do fluxo também aceita o LID direto (o Hermes pode não devolver o LID: limite do WhatsApp)
        return user in known or user in phones or user in await _admin_lids(conn, phones)
    return False


def normalize_text(text: str) -> str:
    t = unicodedata.normalize("NFKD", text.lower()).encode("ascii", "ignore").decode()
    return re.sub(r"\s+", " ", re.sub(r"[^\w\s]", " ", t)).strip()


async def get_mode(conn_id: int, phone: str) -> str:
    db = await get_db()
    try:
        rows = await db.execute_fetchall(
            "SELECT mode, updated_at < datetime('now', ?) AS idle FROM admin_state WHERE connection_id = ? AND phone = ?",
            (f"-{ADMIN_IDLE_MINUTES} minutes", conn_id, phone))
    finally:
        await db.close()
    # O admin é atendido como cliente; o modo administrador só vale depois de "admin" e cai sozinho quando fica parado.
    if not rows or (rows[0]["mode"] == "admin" and rows[0]["idle"]):
        return "sim"
    return rows[0]["mode"]


async def set_mode(conn_id: int, phone: str, mode: str):
    db = await get_db()
    try:
        await db.execute(
            """INSERT INTO admin_state (connection_id, phone, mode) VALUES (?, ?, ?)
               ON CONFLICT(connection_id, phone) DO UPDATE SET mode = excluded.mode, updated_at = datetime('now')""",
            (conn_id, phone, mode),
        )
        await db.commit()
    finally:
        await db.close()


class AdminChat:
    def __init__(self, conn: dict, flow: dict | None, chat: str, enqueue):
        self.conn = conn
        self.flow = flow
        self.chat = chat
        self.phone = chat.split("@")[0].split(":")[0]
        self.sim_phone = f"sim:{self.phone}"
        self.client = HermesClient(conn["hermes_url"], conn["api_key"])
        self.enqueue = enqueue

    async def say(self, text: str):
        resp = await self.client.send_text(self.conn["session_id"], self.chat, text)
        remember_sent(resp.get("id", ""))

    async def menu(self):
        name = self.flow["name"] if self.flow else "?"
        state = "ligado ✅" if self.flow and self.flow["active"] else "desligado ⏸️"
        await self.say(
            f"🛠️ *Modo administrador* — fluxo *{name}* (atendimento {state})\n\n"
            "Para ensinar, é só escrever o que quer mudar. Exemplos:\n"
            "• _quando perguntarem se tem entrega grátis, diga que não_\n"
            "• _o link do cardápio agora é https://..._\n"
            "• _seja mais formal_\n\n"
            f"*sair* = voltar a ser atendido como cliente (sai sozinho depois de {ADMIN_IDLE_MINUTES} min parado).\n"
            "Comandos: *simular*, *reiniciar*, *regras*, *apagar regra 2*, *desfazer*, *ligar*, *desligar*, *status*, *prompt*."
        )
        resp = await self.client.send_poll(self.conn["session_id"], self.chat, "O que você quer fazer?", list(ADMIN_BUTTONS))
        remember_sent(resp.get("id", ""))
        if resp.get("id") and self.flow:
            db = await get_db()
            try:
                await db.execute(
                    "INSERT OR REPLACE INTO polls (message_id, flow_id, phone, kind) VALUES (?, ?, ?, 'admin')",
                    (resp["id"], self.flow["id"], self.phone),
                )
                await db.commit()
            finally:
                await db.close()

    async def handle(self, item: Incoming, push_name: str):
        if not self.flow:
            await self.say("Este número ainda não tem fluxo configurado no FluxIA.")
            return
        mode = await get_mode(self.conn["id"], self.phone)
        cmd = normalize_text(item.text) if item.type == "text" else ""

        if mode == "sim":
            if cmd in ("admin", "modo admin", "administrador"):
                await set_mode(self.conn["id"], self.phone, "admin")
                await self.menu()
                return
            if cmd in ("reiniciar", "recomecar", "resetar"):
                await reset_conversation(self.flow["id"], self.sim_phone)
                await self.say("🔄 Conversa de simulação reiniciada. Mande a primeira mensagem como se fosse um cliente novo.")
                return
            await self.enqueue(self.flow, self.conn, self.sim_phone, self.chat, push_name, "sim", item)
            return

        if item.type == "audio":
            text = await self._transcribe(item)
            if not text:
                await self.say("Não consegui entender o áudio. Pode escrever?")
                return
            item = Incoming(id=item.id, type="text", text=text)
            cmd = normalize_text(text)
        elif item.type != "text":
            await self.say("No modo administrador eu entendo texto e áudio. Para testar imagens, mande *sair* primeiro.")
            return
        if cmd in ("sair", "sair do admin", "cliente"):
            await set_mode(self.conn["id"], self.phone, "sim")
            await reset_conversation(self.flow["id"], self.sim_phone)
            await self.say("✅ Saiu do modo administrador. Agora você é atendido como um cliente novo. Para voltar: *admin*.")
            return
        await set_mode(self.conn["id"], self.phone, "admin")  # renova o prazo do modo administrador
        await self.command(cmd, item.text)

    async def _transcribe(self, item: Incoming) -> str:
        found = find_media(item.raw)
        if not found:
            return ""
        try:
            kind, node = found
            return await transcribe(await download(kind, node), node.get("mimetype", "audio/ogg"))
        except Exception:
            return ""

    async def command(self, cmd: str, original: str):
        flow = self.flow
        if cmd in GREETINGS:
            await self.menu()
        elif cmd in ("simular", "simular cliente", "teste", "testar"):
            await set_mode(self.conn["id"], self.phone, "sim")
            await reset_conversation(flow["id"], self.sim_phone)
            await self.say(
                "🧪 *Simulação ligada.* A partir de agora eu respondo como se você fosse um cliente novo "
                "(boas-vindas, botões, áudio, imagem, tudo igual).\n\n"
                "Mande *reiniciar* para começar de novo e *sair* para voltar ao modo administrador."
            )
        elif cmd in ("reiniciar", "recomecar", "resetar"):
            await reset_conversation(flow["id"], self.sim_phone)
            await self.say("🔄 Conversa de simulação reiniciada.")
        elif (m := re.fullmatch(r"(?:reiniciar|resetar|liberar) ([\d ]{10,20})", cmd)) and 10 <= len(digits(m.group(1))) <= 13:
            target = digits(m.group(1))
            for p in phone_variants(target if target.startswith("55") else "55" + target):
                await reset_conversation(flow["id"], p)
            await self.say(f"🔄 Conversa com {target} reiniciada e liberada para a IA.")
        elif cmd in ("regras", "ver regras", "listar regras"):
            rules = flow["config"]["learned_rules"]
            if not rules:
                await self.say("Ainda não tem regras ensinadas. É só escrever o que quer mudar.")
            else:
                lines = "\n".join(f"*{i}.* {r['text']}" for i, r in enumerate(rules, 1))
                await self.say(f"📋 *Regras ensinadas* ({len(rules)}):\n\n{lines}\n\nPara apagar: *apagar regra 2*")
        elif m := re.fullmatch(r"(?:apagar|remover|excluir|tirar) (?:a )?regra (\d+)", cmd):
            await self.say(await remove_rule(flow, int(m.group(1)), "whatsapp"))
        elif cmd in ("desfazer", "voltar", "desfaz"):
            ok, msg = await undo_last(flow["id"])
            await self.say(("↩️ " if ok else "") + msg)
        elif cmd in ("ligar", "ativar", "desligar", "pausar", "alternar"):
            active = {"ligar": 1, "ativar": 1, "desligar": 0, "pausar": 0}.get(cmd, 0 if flow["active"] else 1)
            db = await get_db()
            try:
                await db.execute("UPDATE flows SET active = ? WHERE id = ?", (active, flow["id"]))
                await db.commit()
            finally:
                await db.close()
            flow["active"] = active
            await self.say("✅ Atendimento automático *ligado*." if active else "⏸️ Atendimento automático *desligado*. Os clientes não recebem resposta até você ligar de novo.")
        elif cmd in ("status", "resumo", "status de hoje"):
            await self.say(await self.status())
        elif cmd == "prompt":
            text = flow["config"]["prompt"]
            await self.say(f"📝 *Prompt atual:*\n\n{text[:3500]}")
        else:
            try:
                result = await teach(flow, original, "whatsapp")
            except Exception as e:
                await self.say(f"Não consegui aplicar agora ({str(e)[:120]}). Tenta de novo em instantes.")
                return
            text = result["reply"]
            if result["changed"]:
                text += "\n\n" + "\n".join(f"• {c}" for c in result["changes"][:8])
                text += "\n\nMande *simular* para testar ou *desfazer* para voltar atrás."
            await self.say(text)

    async def status(self) -> str:
        flow = self.flow
        db = await get_db()
        try:
            today = await db.execute_fetchall(
                """SELECT COUNT(*) AS n, SUM(status = 'error') AS errors, COUNT(DISTINCT phone) AS clients
                   FROM executions WHERE flow_id = ? AND created_at >= date('now') AND phone NOT LIKE 'sim:%' AND phone NOT LIKE 'teste%'""",
                (flow["id"],),
            )
            paused = await db.execute_fetchall(
                "SELECT COUNT(*) AS n FROM conversations WHERE flow_id = ? AND paused_until > datetime('now')", (flow["id"],)
            )
        finally:
            await db.close()
        t = today[0]
        return (
            f"📊 *{flow['name']}* — hoje\n"
            f"• Atendimento: {'ligado ✅' if flow['active'] else 'desligado ⏸️'}\n"
            f"• Mensagens atendidas: {t['n'] or 0} de {t['clients'] or 0} cliente(s)\n"
            f"• Erros: {t['errors'] or 0}\n"
            f"• Conversas com a loja atendendo (IA pausada): {paused[0]['n']}\n"
            f"• Regras ensinadas: {len(flow['config']['learned_rules'])}"
        )

    async def vote(self, label: str):
        cmd = ADMIN_BUTTONS.get(label)
        if cmd:
            await self.command(cmd, cmd)
