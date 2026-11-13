"""Atendimento por menu de opções (botões/lista ou enquete, como os bots antigos de opções numeradas): menu → submenu → perguntas do
serviço uma a uma → resumo para confirmar → Pix e atendente. A IA só entra quando a pessoa escreve algo que não é
uma opção nem a resposta de uma pergunta."""

import json
import re
import unicodedata

GREETINGS = {"oi", "ola", "olá", "oii", "oie", "menu", "inicio", "início", "bom dia", "boa tarde", "boa noite",
             "opa", "eae", "e ai", "hello", "voltar", "opcoes", "opções"}
CANCEL_WORDS = {"cancelar", "cancela", "sair"}
YES = {"sim", "s", "confirmo", "confirmar", "ok", "isso", "certo", "pode", "correto"}
CONFIRM = "✅ Confirmar"
FIX = "✏️ Corrigir"
CANCEL = "❌ Cancelar"
BACK = "⬅️ Voltar ao menu"


def _norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9 ]", "", s.lower()).strip()


def _is_greeting(text: str) -> bool:
    n = _norm(text)
    return bool(n) and (n in {_norm(g) for g in GREETINGS} or (len(n.split()) <= 3 and n.split()[0] in {"oi", "ola", "bom", "boa", "opa"}))


QUESTION_WORDS = {"quanto", "quantos", "quando", "qual", "quais", "como", "onde", "voces", "vcs", "vc", "tem", "pode",
                  "aceita", "aceitam", "demora", "faz", "fazem", "abre", "abrem", "precisa", "e"}


def _is_question(text: str) -> bool:
    """Dúvida digitada no meio do formulário (vai para a IA em vez de virar resposta)."""
    words = _norm(text).split()
    return "?" in text or bool(words and words[0] in QUESTION_WORDS and len(words) > 2)


def _match(text: str, options: list[str]) -> str | None:
    """Opção escolhida pelo texto: igual ao rótulo (sem emoji/acento), ou o número da posição."""
    n = _norm(text)
    if n.isdigit() and 1 <= int(n) <= len(options):
        return options[int(n) - 1]
    for o in options:
        if _norm(o) == n or (len(n) >= 4 and _norm(o).startswith(n)):
            return o
    return None


# --- Menu da papelaria (preços do bot antigo da cyber) ---

# Rótulos de até 20 letras: assim as perguntas de até 3 opções saem como botões do WhatsApp (mais que isso vira lista).
MOTOBOY = "🛵 Entrega motoboy"
PDF_WPP = "📲 PDF no WhatsApp"
ENTREGA = [
    {"key": "entrega", "label": "Receber", "q": "Como prefere receber?\n🛵 Motoboy: taxa a combinar",
     "options": ["🏪 Retirar na loja", MOTOBOY]},
    {"key": "endereco", "label": "Endereço", "q": "Qual o endereço de entrega? 📍", "if": ["entrega", MOTOBOY]},
]
RECEBER_DOC = [
    {"key": "entrega", "label": "Receber", "q": "Como prefere receber o documento?\n📲 PDF no WhatsApp: + R$ 1,00\n🛵 Motoboy: taxa a combinar",
     "options": [PDF_WPP, "🏪 Buscar na loja", MOTOBOY]},
    {"key": "endereco", "label": "Endereço", "q": "Qual o endereço de entrega? 📍", "if": ["entrega", MOTOBOY]},
]
ARQUIVO = {"key": "arquivo", "label": "Arquivo", "q": "Me mande o arquivo por aqui (PDF, Word ou foto) 📎", "type": "file"}
COPIAS = {"key": "copias", "label": "Cópias", "q": "Quantas cópias de cada página?", "type": "number"}
PESSOA = [{"key": "nome", "q": "Qual o seu nome completo?"}, {"key": "cpf", "q": "Qual o seu CPF?"}]


def _svc(label, price, questions, unit=None):
    return {"label": label, "price": price, "questions": questions, **({"unit": unit} if unit else {})}


PAPELARIA_MENU = {
    "welcome": "Olá! 👋 Bem-vindo à *{{loja}}*!\nComo posso te ajudar hoje?",
    "menus": {
        # Rótulos de até 20 letras para caberem no botão do WhatsApp (o nome completo do serviço vai no resumo).
        "inicio": {"title": "Escolha uma opção 👇", "options": [
            {"label": "🖨️ Impressão/cópia", "goto": "impressao"},
            {"label": "📄 Documentos", "goto": "documentos"},
            {"label": "🏛️ Serviços online", "goto": "online"},
            {"label": "⌨️ Digitação/edição", "goto": "digitacao"},
            {"label": "📎 Acabamento", "goto": "acabamento"},
            {"label": "💻 Formatar PC", "service": "formatacao"},
            {"label": "💰 Tabela de preços", "action": "table"},
            {"label": "🙋 Atendente", "action": "human"},
        ]},
        "impressao": {"title": "Você escolheu IMPRESSÃO E CÓPIAS. Qual serviço?", "options": [
            {"label": "Preto e branco", "service": "pb"},
            {"label": "Colorida", "service": "colorida"},
            {"label": "Fotos", "service": "fotos"},
            {"label": "Papel fotográfico", "service": "fotografico"},
            {"label": "Cópia", "service": "copia"},
            {"label": "Scanner", "service": "scanner"},
            {"label": "Boleto", "service": "boleto"},
            {"label": BACK, "goto": "inicio"},
        ]},
        "documentos": {"title": "Você escolheu DOCUMENTOS PRONTOS. Qual documento?", "options": [
            {"label": "Contrato de aluguel", "service": "aluguel"},
            {"label": "Compra e venda", "service": "compra_venda"},
            {"label": "Declaração", "service": "declaracao"},
            {"label": "Ofício", "service": "oficio"},
            {"label": "Procuração", "service": "procuracao"},
            {"label": BACK, "goto": "inicio"},
        ]},
        "online": {"title": "Você escolheu SERVIÇOS ONLINE. Qual serviço?", "options": [
            {"label": "Senha Gov.br", "service": "govbr"},
            {"label": "2ª via do RG", "service": "rg"},
            {"label": "Concurso", "service": "concurso"},
            {"label": "SPC/Serasa CPF", "service": "spc_cpf"},
            {"label": "SPC/Serasa CNPJ", "service": "spc_cnpj"},
            {"label": "CRLV-e", "service": "crlv"},
            {"label": "Antecedentes", "service": "antecedentes"},
            {"label": "Nota fiscal", "service": "nota"},
            {"label": BACK, "goto": "inicio"},
        ]},
        "digitacao": {"title": "Você escolheu DIGITAÇÃO E EDIÇÃO. Qual serviço?", "options": [
            {"label": "Digitação de texto", "service": "digitacao"},
            {"label": "Formatação ABNT", "service": "abnt"},
            {"label": "Currículo / Word", "service": "curriculo"},
            {"label": "Atualizar PDF", "service": "pdf"},
            {"label": "Converter arquivo", "service": "conversao"},
            {"label": "Pesquisa escolar", "service": "pesquisa"},
            {"label": BACK, "goto": "inicio"},
        ]},
        "acabamento": {"title": "Você escolheu ACABAMENTO E MATERIAIS. Qual item?", "options": [
            {"label": "Encadernação", "service": "encadernacao"},
            {"label": "Plastificação 8x11", "service": "plast_8x11"},
            {"label": "Plastificação A4", "service": "plast_a4"},
            {"label": "Pasta", "service": "pasta"},
            {"label": "Envelope", "service": "envelope"},
            {"label": BACK, "goto": "inicio"},
        ]},
    },
    "services": {
        "pb": _svc("Impressão preto e branco", "R$ 2,00 por folha A4", [ARQUIVO, COPIAS, *ENTREGA], unit=2.0),
        "colorida": _svc("Impressão colorida", "R$ 3,00 por folha A4", [ARQUIVO, COPIAS, *ENTREGA], unit=3.0),
        "fotos": _svc("Impressão de fotos", "R$ 2,50 por foto", [
            {"key": "arquivo", "q": "Me mande as fotos por aqui 📸", "type": "file"},
            {"key": "copias", "q": "Quantas cópias de cada foto?", "type": "number"}, *ENTREGA], unit=2.5),
        "fotografico": _svc("Impressão em papel fotográfico", "R$ 5,00", [ARQUIVO, COPIAS, *ENTREGA], unit=5.0),
        "copia": _svc("Cópia", "R$ 0,50 por cópia", [{"key": "copias", "q": "Quantas cópias?", "type": "number"}], unit=0.5),
        "scanner": _svc("Scanner de documento", "R$ 1,00", [{"key": "qtd", "q": "Quantas páginas vai escanear?"},
            {"key": "envio", "q": "Como quer receber?\n📲 PDF no WhatsApp: + R$ 1,00", "options": [PDF_WPP, "📧 Por e-mail"]}]),
        "boleto": _svc("Impressão de boleto", "R$ 3,00", [{"key": "arquivo", "q": "Me mande o boleto (PDF ou foto) 📎", "type": "file"}]),
        "aluguel": _svc("Contrato de aluguel", "R$ 7,00", [
            {"key": "locador", "q": "1. Nome completo do locador (dono)?"},
            {"key": "locatario", "q": "2. Nome completo do locatário (inquilino)?"},
            {"key": "valor", "q": "3. Valor mensal do aluguel?"},
            {"key": "imovel", "q": "4. Endereço completo do imóvel?"},
            {"key": "prazo", "q": "5. Prazo do contrato (ex.: 12 meses, a partir de 01/11)?"}, *RECEBER_DOC]),
        "compra_venda": _svc("Contrato de compra e venda de imóvel", "R$ 7,00", [
            {"key": "vendedor", "q": "1. Nome completo e CPF do vendedor?"},
            {"key": "comprador", "q": "2. Nome completo e CPF do comprador?"},
            {"key": "imovel", "q": "3. Endereço e descrição do imóvel?"},
            {"key": "valor", "q": "4. Valor e forma de pagamento da venda?"}, *RECEBER_DOC]),
        "declaracao": _svc("Declaração", "R$ 7,00", [
            {"key": "tipo", "q": "1. Qual tipo de declaração (residência, renda, união estável...)?"},
            {"key": "nome", "q": "2. Nome completo e CPF de quem declara?"},
            {"key": "texto", "q": "3. O que precisa constar na declaração?"}, *RECEBER_DOC]),
        "oficio": _svc("Ofício", "R$ 7,00", [
            {"key": "destino", "q": "1. Para quem é o ofício (pessoa/órgão)?"},
            {"key": "assunto", "q": "2. Qual o assunto?"},
            {"key": "remetente", "q": "3. Quem assina (nome e cargo)?"}, *RECEBER_DOC]),
        "procuracao": _svc("Procuração", "R$ 7,00", [
            {"key": "outorgante", "q": "1. Nome completo e CPF do outorgante (quem dá a procuração)?"},
            {"key": "outorgado", "q": "2. Nome completo e CPF do outorgado (quem recebe)?"},
            {"key": "finalidade", "q": "3. Para que é a procuração?"}, *RECEBER_DOC]),
        "govbr": _svc("Recuperação de senha Gov.br", "R$ 15,00", [*PESSOA, {"key": "obs", "q": "O que está acontecendo com a conta?"}]),
        "rg": _svc("Agendamento de 2ª via do RG", "R$ 15,00", [*PESSOA, {"key": "obs", "q": "Tem preferência de dia ou local?"}]),
        "concurso": _svc("Inscrição de concurso", "R$ 20,00", [*PESSOA, {"key": "concurso", "q": "Qual concurso e cargo?"}]),
        "spc_cpf": _svc("Consulta SPC/Serasa (CPF)", "R$ 20,00", PESSOA),
        "spc_cnpj": _svc("Consulta SPC/Serasa (CNPJ)", "R$ 25,00", [{"key": "cnpj", "q": "Qual o CNPJ?"}, {"key": "nome", "q": "Nome da empresa?"}]),
        "crlv": _svc("CRLV-e", "R$ 15,00", [{"key": "placa", "q": "Placa do veículo?"}, {"key": "renavam", "q": "Número do Renavam?"},
                                         {"key": "cpf", "q": "CPF ou CNPJ do dono do veículo?"}]),
        "antecedentes": _svc("Antecedentes criminais", "R$ 7,00", [*PESSOA, {"key": "mae", "q": "Nome completo da mãe?"},
                                                               {"key": "nascimento", "q": "Data de nascimento?"}]),
        "nota": _svc("Nota fiscal da Prefeitura de Castanhal", "R$ 10,00", [
            {"key": "prestador", "q": "Nome/CPF ou CNPJ de quem emite?"}, {"key": "tomador", "q": "Nome/CPF ou CNPJ do cliente da nota?"},
            {"key": "servico", "q": "Qual serviço e o valor da nota?"}]),
        "digitacao": _svc("Digitação de texto", "R$ 15,00 por folha", [
            {"key": "arquivo", "q": "Me mande o texto a digitar (foto ou arquivo) 📎", "type": "file"},
            {"key": "prazo", "q": "Para quando precisa?"}, *RECEBER_DOC]),
        "abnt": _svc("Formatação nas normas ABNT", "R$ 50,00", [ARQUIVO, {"key": "prazo", "q": "Para quando precisa?"}, *RECEBER_DOC]),
        "curriculo": _svc("Edição de currículo ou arquivo Word", "R$ 7,00", [
            {"key": "arquivo", "q": "Me mande o arquivo atual (se tiver) 📎", "type": "file"},
            {"key": "mudancas", "q": "O que precisa mudar ou incluir?"}, *RECEBER_DOC]),
        "pdf": _svc("Atualização de arquivo PDF", "R$ 10,00", [ARQUIVO, {"key": "mudancas", "q": "O que precisa mudar?"}, *RECEBER_DOC]),
        "conversao": _svc("Ajuste ou conversão de arquivo", "R$ 10,00", [ARQUIVO, {"key": "formato", "q": "Para qual formato (Word, PDF, JPEG...) ou o que ajustar?"}]),
        "pesquisa": _svc("Pesquisa escolar", "R$ 15,00", [{"key": "tema", "q": "Qual o tema da pesquisa?"},
                                                        {"key": "serie", "q": "Série/ano e quantas páginas?"}, *RECEBER_DOC]),
        "encadernacao": _svc("Encadernação (até 100 folhas)", "R$ 10,00", [{"key": "qtd", "q": "Quantas folhas tem o material?"}, ARQUIVO]),
        "plast_8x11": _svc("Plastificação de documento 8x11", "R$ 5,00 cada", [{"key": "copias", "q": "Quantos documentos?", "type": "number"}], unit=5.0),
        "plast_a4": _svc("Plastificação A4", "R$ 10,00 cada", [{"key": "copias", "q": "Quantas folhas?", "type": "number"}], unit=10.0),
        "pasta": _svc("Pasta de documentos", "R$ 3,50 cada", [{"key": "copias", "q": "Quantas pastas?", "type": "number"}], unit=3.5),
        "envelope": _svc("Envelope", "R$ 1,00 cada", [{"key": "copias", "q": "Quantos envelopes?", "type": "number"}], unit=1.0),
        "formatacao": _svc("Formatação de notebook/computador (sem backup)", "R$ 100,00", [
            {"key": "aparelho", "q": "Qual o aparelho (marca/modelo)?"}, {"key": "problema", "q": "O que está acontecendo?"}]),
    },
}


# --- Motor ---

def _menu(cfg: dict) -> dict:
    m = cfg.get("menu") or {}
    return m if m.get("menus") else PAPELARIA_MENU


def _find_option(menu: dict, label: str) -> dict | None:
    for node in menu["menus"].values():
        for o in node["options"]:
            if o["label"] == label:
                return o
    return None


def _state(conv: dict) -> tuple[str, dict]:
    raw = conv.get("state") or ""
    kind, _, rest = raw.partition(":")
    if kind in ("form", "confirm"):
        try:
            return kind, json.loads(rest)
        except ValueError:
            return "", {}
    return kind, {"menu": rest} if kind == "menu" else {}


def _set(conv: dict, kind: str, data: dict | str = ""):
    conv["state"] = f"{kind}:{json.dumps(data, ensure_ascii=False) if isinstance(data, dict) else data}"


async def menu_recent(run, minutes: int = 10) -> bool:
    """Já mandou uma enquete de menu para esta pessoa há pouco (continua clicável, não precisa repetir)."""
    from .db import get_db
    db = await get_db()
    try:
        rows = await db.execute_fetchall(
            "SELECT 1 FROM polls WHERE flow_id = ? AND phone = ? AND kind = 'menu' AND created_at > datetime('now', ?)",
            (run.flow["id"], run.phone, f"-{minutes} minutes"))
    finally:
        await db.close()
    return bool(rows)


async def send_main_menu(run, conv, welcome: bool = True):
    from .flow_config import render_placeholders
    menu = _menu(run.cfg)
    if welcome and menu.get("welcome"):
        await _say(run, conv, render_placeholders(menu["welcome"], run.cfg))
    await _show(run, conv, "inicio")


async def _say(run, conv, text: str):
    from .engine import send_texts
    await send_texts(run, [text])
    conv["history"].append({"role": "assistant", "content": text})


async def _poll(run, conv, title: str, options: list[str]):
    from .db import get_db
    msg_ids = [i for i in await run.sender.poll(title, options[:12], run.cfg["button_style"] == "botoes") if i]
    run.sent.append(f"[opções] {title}: " + " | ".join(options))
    conv["history"].append({"role": "assistant", "content": f"{title}\n" + "\n".join(f"- {o}" for o in options)})
    if msg_ids:
        db = await get_db()
        try:
            await db.executemany("INSERT OR REPLACE INTO polls (message_id, flow_id, phone, kind) VALUES (?, ?, ?, 'menu')",
                                 [(i, run.flow["id"], run.phone) for i in msg_ids])
            await db.commit()
        finally:
            await db.close()


async def _show(run, conv, menu_id: str):
    node = _menu(run.cfg)["menus"].get(menu_id) or _menu(run.cfg)["menus"]["inicio"]
    await _poll(run, conv, node["title"], [o["label"] for o in node["options"]])
    _set(conv, "menu", menu_id)
    run.step("buttons", "ok", f"Menu \"{menu_id}\" enviado")


def _questions(svc: dict, answers: dict) -> list[dict]:
    out = []
    for q in svc["questions"]:
        cond = q.get("if")
        if cond and answers.get(cond[0]) != cond[1]:
            continue
        out.append(q)
    return out


async def _ask(run, conv, form: dict):
    svc = _menu(run.cfg)["services"][form["svc"]]
    qs = _questions(svc, form["a"])
    pending = [q for q in qs if q["key"] not in form["a"]]
    if not pending:
        return await _summary(run, conv, form)
    q = pending[0]
    if q.get("options"):
        await _poll(run, conv, q["q"], q["options"])
    else:
        await _say(run, conv, q["q"])
    _set(conv, "form", form)


def _estimate(svc: dict, form: dict) -> str:
    unit = svc.get("unit")
    copies = re.sub(r"\D", "", str(form["a"].get("copias", "")))
    if not unit or not copies:
        return ""
    pages = form.get("pages") or 1
    total = unit * pages * int(copies)
    detail = f"{pages} pág. x {copies} cópia(s)" if form.get("pages") else f"{copies} x"
    return f"*Valor estimado:* {detail} = R$ " + f"{total:.2f}".replace(".", ",")


def _summary_text(run, form: dict) -> str:
    svc = _menu(run.cfg)["services"][form["svc"]]
    lines = [f"*Serviço:* {svc['label']} ({svc['price']})"]
    for q in _questions(svc, form["a"]):
        label = q.get("label") or re.sub(r"^\d+\.\s*", "", q["q"]).rstrip("?📎📸📍 ").strip()
        lines.append(f"• {label}: {form['a'].get(q['key'], '')}")
    est = _estimate(svc, form)
    if est:
        lines.append(est)
    return "\n".join(lines)


async def _summary(run, conv, form: dict):
    await _say(run, conv, "Confira os dados:\n\n" + _summary_text(run, form))
    await _poll(run, conv, "Está tudo certo?", [CONFIRM, FIX, CANCEL])
    _set(conv, "confirm", form)
    run.step("actions", "ok", "Resumo enviado para o cliente confirmar")


async def _confirmed(run, conv, form: dict):
    from .engine import _handoff, notify_owner, _client_label
    from .flow_config import render_placeholders
    summary = _summary_text(run, form)
    done_text = _menu(run.cfg).get("done_text")  # menu sem Pix (ex.: orçamento de energia solar)
    if done_text:
        await _say(run, conv, render_placeholders(done_text, run.cfg))
    else:
        pix = render_placeholders("{{chave_pix}}", run.cfg)
        await _say(run, conv, "Pedido anotado! ✅\n\n"
                   f"💳 Pagamento via Pix: {pix}\nDepois de pagar, mande o comprovante por aqui.\n\n"
                   "Um atendente já vai dar continuidade ao seu atendimento. 😊")
    _set(conv, "done")
    run.step("actions", "ok", f"Pedido confirmado: {_menu(run.cfg)['services'][form['svc']]['label']}")
    if run.cfg["notify_order"]:
        await notify_owner(run, f"🛒 Pedido de {_client_label(run, conv)}:\n{summary}", "pedido")
    await _handoff(run, conv)


async def _save_files(run, items) -> tuple[list[str], int]:
    from .engine import find_media, download, save_file, pdf_pages
    names, pages = [], 0
    for item in items:
        if not item.raw:
            names.append(item.type)
            continue
        found = find_media(item.raw)
        if not found:
            continue
        kind, node = found
        name = node.get("fileName") or ("foto" if item.type == "image" else "arquivo")
        n = int(node.get("pageCount") or 0)
        try:
            data = await download(kind, node)
            run.files.append(await save_file(run.flow["id"], run.phone, item.type, data, node.get("mimetype", ""), item.text, name))
            if not n and "pdf" in (node.get("mimetype", "") + name).lower():
                n = pdf_pages(data) or 0
        except Exception as e:
            run.step("media", "error", f"Arquivo não baixado ({str(e)[:80]})")
        pages += n if n else (1 if item.type == "image" else 0)
        names.append(name + (f" ({n} pág.)" if n else ""))
    return names, pages


async def handle(run, conv: dict, items: list, first_contact: bool) -> bool:
    """True = o menu respondeu; False = segue para a IA (a mensagem não fica no histórico, a IA registra)."""
    text = "\n".join(i.text for i in items if i.type == "text" and i.text).strip()
    vote = next((i.vote for i in reversed(items) if i.type == "vote"), "")
    size = len(conv["history"])
    conv["history"].append({"role": "user", "content": text or (f"[botão] {vote}" if vote else "[arquivo]")})
    handled = await _handle(run, conv, items, first_contact, text, vote)
    if not handled:
        del conv["history"][size:]
    return handled


async def _handle(run, conv: dict, items: list, first_contact: bool, text: str, vote: str) -> bool:
    menu = _menu(run.cfg)
    kind, data = _state(conv)
    files = [i for i in items if i.type in ("image", "document")]

    async def choose(opt: dict) -> bool:
        if opt.get("goto"):
            await _show(run, conv, opt["goto"])
        elif opt.get("service") in menu["services"]:
            svc = menu["services"][opt["service"]]
            await _say(run, conv, f"Ótima escolha! *{svc['label']}*: {svc['price']}.\nPreciso de algumas informações:")
            await _ask(run, conv, {"svc": opt["service"], "a": {}})
        elif opt.get("action") == "table":
            from .flow_config import render_placeholders
            # Sem reenviar o menu: a enquete anterior continua clicável no WhatsApp.
            await _say(run, conv, render_placeholders(menu.get("table_text") or (
                "Confira nossos serviços e valores 👇\n\n{{informacoes}}\n\n"
                "Para pedir, toque numa opção do menu acima ou digite *menu*."), run.cfg))
        elif opt.get("action") == "human":
            from .engine import HANDOFF_REPLY, _handoff
            await _say(run, conv, HANDOFF_REPLY)
            _set(conv, "done")
            await _handoff(run, conv)
        else:
            return False
        run.step("media", "ok", f"Opção \"{opt['label']}\"")
        return True

    # Palavras que sempre voltam ao começo
    if text and not vote and (_is_greeting(text) or _norm(text) in CANCEL_WORDS) and not (kind == "form" and len(_norm(text)) > 12):
        await send_main_menu(run, conv, welcome=first_contact or _is_greeting(text))
        return True

    if kind == "confirm":
        answer = vote or (_match(text, [CONFIRM, FIX, CANCEL]) if text else None) or (CONFIRM if _norm(text) in YES else None)
        if answer == CONFIRM:
            await _confirmed(run, conv, data)
            return True
        if answer == FIX:
            await _say(run, conv, "Sem problema, vamos de novo. ✏️")
            await _ask(run, conv, {"svc": data["svc"], "a": {}})
            return True
        if answer == CANCEL:
            await _say(run, conv, "Pedido cancelado.")
            await _show(run, conv, "inicio")
            return True

    if kind == "form" and data.get("svc") in menu["services"]:
        svc = menu["services"][data["svc"]]
        pending = [q for q in _questions(svc, data["a"]) if q["key"] not in data["a"]]
        q = pending[0] if pending else None
        if q:
            answer = None
            if q.get("options"):
                answer = (vote if vote in q["options"] else None) or (_match(text, q["options"]) if text else None)
                if not answer and text and not vote and not _is_question(text):
                    answer = text
            elif q.get("type") == "file":
                if files:
                    names, pages = await _save_files(run, files)
                    data["pages"] = data.get("pages", 0) + pages
                    answer = ", ".join(names) or "arquivo recebido"
                elif text and _norm(text) in {"nao tenho", "nao", "depois", "levo na loja", "vou levar"}:
                    answer = "vai levar na loja"
            elif q.get("type") == "number":
                if text and re.search(r"\d", text):
                    answer = text
            elif text and not _is_question(text):
                answer = text
            if answer:
                data["a"][q["key"]] = answer
                run.step("media", "ok", f"Resposta: {q['key']}")
                await _ask(run, conv, data)
                return True
            if not vote and text:
                return False  # dúvida no meio do formulário: a IA responde e a pergunta continua pendente

    if vote:
        opt = _find_option(menu, vote)
        if opt:
            return await choose(opt)
        return False

    if kind == "menu" and text:
        node = menu["menus"].get(data.get("menu")) or menu["menus"]["inicio"]
        label = _match(text, [o["label"] for o in node["options"]])
        if label:
            return await choose(next(o for o in node["options"] if o["label"] == label))

    if first_contact and (not text or len(text.split()) <= 3):
        await send_main_menu(run, conv)
        return True
    return False


HUMAN_WORDS = ("atendente", "pessoa", "humano", "falar com alguem", "falar com voce", "dono", "jhonatas", "consultor", "vendedor")


def after_ai(conv: dict, cfg: dict, reply: str, client_text: str) -> str:
    """No meio do menu a IA não encerra o atendimento por conta própria e sempre devolve a pergunta pendente."""
    if "[ATENDENTE]" in reply and not any(w in _norm(client_text) for w in HUMAN_WORDS):
        reply = reply.replace("[ATENDENTE]", "").strip()
    kind, data = _state(conv)
    svc = _menu(cfg)["services"].get(data.get("svc")) if kind == "form" else None
    if svc:
        pending = [q for q in _questions(svc, data.get("a", {})) if q["key"] not in data.get("a", {})]
        if pending and _norm(pending[0]["q"])[:25] not in _norm(reply):
            reply = reply.rstrip() + "\n\n" + pending[0]["q"]
    return reply


def ai_note(conv: dict, cfg: dict) -> str:
    """O que o cliente já escolheu no menu, para a IA entender a mensagem fora do roteiro."""
    menu = _menu(cfg)
    kind, data = _state(conv)
    chosen = [h["content"][8:].strip() for h in conv["history"]
              if h.get("role") == "user" and isinstance(h.get("content"), str) and h["content"].startswith("[botão]")]
    lines = []
    if chosen:
        lines.append("Opções que o cliente tocou no menu, em ordem: " + " → ".join(chosen[-8:]) + ".")
    if kind == "menu":
        node = menu["menus"].get(data.get("menu"))
        if node:
            lines.append(f"Ele está vendo o menu \"{node['title']}\" com as opções: " + ", ".join(o["label"] for o in node["options"]) + ". "
                         "Se a mensagem tiver relação com essas opções, responda pensando nelas.")
    elif kind in ("form", "confirm"):
        svc = menu["services"].get(data.get("svc"))
        if svc:
            answers = "; ".join(f"{k}: {v}" for k, v in data.get("a", {}).items()) or "nenhuma ainda"
            lines.append(f"Ele escolheu o serviço *{svc['label']}* ({svc['price']}). Respostas já dadas: {answers}.")
            pending = [q for q in _questions(svc, data.get("a", {})) if q["key"] not in data.get("a", {})]
            if kind == "form" and pending:
                lines.append(f"Falta responder: \"{pending[0]['q']}\". Responda a dúvida em 1 ou 2 frases e repita essa pergunta no fim.")
            elif kind == "confirm":
                lines.append("Ele está na confirmação do pedido: tire a dúvida e peça para tocar em Confirmar, Corrigir ou Cancelar.")
    elif kind == "done":
        lines.append("O pedido dele já foi passado para a equipe.")
    return "\nCONTEXTO DO MENU: " + " ".join(lines) if lines else ""
