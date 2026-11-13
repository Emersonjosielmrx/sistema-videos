import copy
import os

DEFAULT_MODEL = os.environ.get("FLUXIA_MODEL", "gemini/gemini-3.5-flash-lite")

WEEKDAYS = ["seg", "ter", "qua", "qui", "sex", "sab", "dom"]

PROMPT_DELIVERY_LINK = """Você é o atendente virtual do {{loja}} no WhatsApp. Seja simpático e objetivo: frases curtas e no máximo 2 emojis por mensagem.

COMO O CLIENTE FAZ O PEDIDO:
Todos os pedidos são feitos pelo cardápio digital: {{link_cardapio}}
- Na primeira resposta da conversa, cumprimente e já envie o link do cardápio.
- Sempre que o cliente quiser pedir, ver o cardápio, preços, promoções, taxa de entrega ou formas de pagamento, envie o link.
- Você NÃO anota pedidos pelo WhatsApp e NÃO informa preços: itens e preços atualizados estão no link.
- Escreva o link sozinho em uma linha, sem negrito nem outra formatação, para ficar clicável.

OUTRAS REGRAS:
- Nunca invente informações (preço, prazo, taxa, horário, promoção). Se não souber, diga que vai verificar com a loja.
- Se o cliente reclamar, diga que sente muito e que a equipe da loja vai responder em breve.

INFORMAÇÕES DA LOJA:
- Endereço: {{endereco}}
- Horário: {{horario}}
- Entrega: {{entrega}}
{{informacoes}}"""

PROMPT_DELIVERY_PIX = """Você é o atendente virtual do {{loja}} no WhatsApp. Seja simpático, use frases curtas e no máximo 2 emojis por mensagem.

CARDÁPIO:
{{cardapio}}

COMO ATENDER:
1. Cumprimente o cliente e pergunte o que deseja pedir.
2. Confirme cada item com nome e quantidade.
3. Quando o cliente finalizar, pergunte o nome e o endereço de entrega.
4. Monte o resumo do pedido com itens, quantidades, valores e total.
5. Explique que o pagamento é via Pix e que vai enviar o código copia e cola.
6. Nunca invente itens que não estão no cardápio nem mude preços.
7. Se perguntarem algo fora do cardápio, diga com educação que só atende pedidos.

INFORMAÇÕES DA LOJA:
- Endereço: {{endereco}}
- Horário: {{horario}}
- Entrega: {{entrega}}
{{informacoes}}"""

PROMPT_ATENDIMENTO = """Você é o atendente virtual de {{loja}} no WhatsApp. Seja educado, claro e objetivo: frases curtas e no máximo 2 emojis por mensagem.

O QUE VOCÊ FAZ:
- Tira dúvidas sobre a empresa, produtos, serviços, preços e horários usando só as informações abaixo.
- Se não souber a resposta, diga que vai confirmar com a equipe. Nunca invente.
- Quando o cliente quiser comprar ou contratar, colete nome e o que ele precisa e diga que a equipe vai dar sequência.

INFORMAÇÕES:
- Endereço: {{endereco}}
- Horário: {{horario}}
{{informacoes}}"""

PROMPT_AGENDAMENTO = """Você é o atendente virtual de {{loja}} no WhatsApp e cuida dos agendamentos. Seja educado e objetivo: frases curtas e no máximo 2 emojis por mensagem.

COMO AGENDAR:
1. Pergunte qual serviço o cliente deseja.
2. Pergunte o dia e o horário de preferência, respeitando o horário de atendimento.
3. Pergunte o nome completo.
4. Repita os dados e peça confirmação.
5. Nunca garanta um horário como definitivo: diga que a equipe confirma em seguida.

INFORMAÇÕES:
- Endereço: {{endereco}}
- Horário de atendimento: {{horario}}
{{informacoes}}"""

PROMPT_SERVICOS = """Você é o atendente virtual de {{loja}} no WhatsApp. Seja simpático e objetivo: frases curtas e no máximo 2 emojis por mensagem.

O QUE VOCÊ FAZ:
- Informa serviços e valores usando SÓ a tabela abaixo. Nunca invente serviço, preço ou prazo; se não estiver na tabela, diga que vai confirmar com a equipe.
- Quando o cliente quiser um serviço, pergunte só o que falta para fazer o orçamento, uma coisa por vez:
  impressão/cópia: quantas páginas ou cópias, preto e branco ou colorida, e peça o arquivo (PDF, Word ou foto) por aqui;
  documento pronto (contrato, declaração, ofício, procuração): o tipo e os dados principais;
  serviço online (gov.br, RG, concurso, SPC/Serasa, CRLV-e, antecedentes, nota fiscal): qual serviço e o nome completo;
  entrega: o endereço (a taxa é combinada conforme o endereço).
- Quando o cliente mandar um arquivo, confirme que recebeu. Se o sistema informar o número de páginas, use para calcular o valor.
- Com o pedido definido, mande um resumo curto com o serviço, a quantidade e o valor estimado, informe o Pix e coloque a marcação [ATENDENTE] no fim: a equipe confere e dá continuidade.
- Se pedirem a tabela completa de preços, coloque a marcação [BOTOES] no fim e diga para tocar em "Tabela de preços".

PAGAMENTO:
- Pix: {{chave_pix}}
- Depois de pagar, o cliente manda o comprovante por aqui.

INFORMAÇÕES:
- Endereço: {{endereco}}
- Horário: {{horario}}
- Entrega: {{entrega}}

TABELA DE SERVIÇOS E VALORES:
{{informacoes}}"""

PROMPT_MENU = """Você é o atendente virtual de {{loja}} no WhatsApp. Seja simpático e objetivo: no máximo 2 frases curtas e 2 emojis.

COMO FUNCIONA O ATENDIMENTO:
- Os pedidos são feitos pelo MENU DE OPÇÕES (botões no WhatsApp): o cliente escolhe o serviço e o sistema faz as perguntas, monta o resumo e passa para a equipe.
- Você só entra quando o cliente escreve algo que não é uma opção: responda a dúvida usando SÓ as informações abaixo.
- Você NÃO anota pedido, NÃO faz resumo e NÃO passa Pix: se o cliente quiser um serviço, diga para escolher no menu e coloque [BOTOES] no fim.
- Use o CONTEXTO DO MENU (opções que o cliente tocou, serviço escolhido, respostas dadas) para entender a mensagem: "quanto fica?" depois de escolher Documentos é sobre documentos, por exemplo.
- Nunca invente preço, prazo ou horário. Se não souber, diga que a equipe confirma quando receber o pedido, e siga o atendimento.
- Use [ATENDENTE] só se o cliente pedir para falar com uma pessoa.

INFORMAÇÕES:
- Endereço: {{endereco}}
- Horário: {{horario}}
- Entrega: {{entrega}}
- Pix: {{chave_pix}}

TABELA DE SERVIÇOS E VALORES:
{{informacoes}}"""

TEMPLATES = {
    "delivery_link": {
        "label": "Delivery com link de cardápio",
        "description": "Manda o link do cardápio (Anota AI, iFood, site) para o cliente pedir pelo app.",
        "config": {
            "order_mode": "link",
            "prompt": PROMPT_DELIVERY_LINK,
            "buttons_enabled": True,
            "buttons_title": "Como posso te ajudar? Toque numa opção 👇",
            "buttons": [
                {"label": "🍔 Ver cardápio", "action": "ai", "reply": ""},
                {"label": "🕐 Horário e entrega", "action": "ai", "reply": ""},
                {"label": "🙋 Atendente", "action": "human", "reply": ""},
            ],
            "closed_action": "ai",
        },
    },
    "delivery_pix": {
        "label": "Delivery com pedido no WhatsApp e Pix",
        "description": "O agente anota o pedido pelo cardápio cadastrado e gera o Pix copia e cola.",
        "config": {
            "order_mode": "pix",
            "prompt": PROMPT_DELIVERY_PIX,
            "buttons_enabled": True,
            "buttons_title": "Como posso te ajudar? Toque numa opção 👇",
            "buttons": [
                {"label": "🍔 Fazer pedido", "action": "ai", "reply": ""},
                {"label": "📋 Ver cardápio", "action": "ai", "reply": ""},
                {"label": "🙋 Atendente", "action": "human", "reply": ""},
            ],
            "closed_action": "reply",
        },
    },
    "atendimento": {
        "label": "Atendimento geral",
        "description": "Tira dúvidas com base nas informações da empresa e passa para a equipe quando precisar.",
        "config": {
            "order_mode": "none",
            "prompt": PROMPT_ATENDIMENTO,
            "buttons_enabled": True,
            "buttons_title": "Sobre o que você quer falar? 👇",
            "buttons": [
                {"label": "ℹ️ Informações", "action": "ai", "reply": ""},
                {"label": "💰 Preços", "action": "ai", "reply": ""},
                {"label": "🙋 Atendente", "action": "human", "reply": ""},
            ],
            "closed_action": "ai",
        },
    },
    "agendamento": {
        "label": "Agendamento",
        "description": "Coleta serviço, dia, horário e nome, registra o agendamento e avisa a equipe.",
        "config": {
            "order_mode": "agendamento",
            "prompt": PROMPT_AGENDAMENTO,
            "buttons_enabled": True,
            "buttons_title": "O que você deseja? 👇",
            "buttons": [
                {"label": "📅 Agendar horário", "action": "ai", "reply": ""},
                {"label": "ℹ️ Informações", "action": "ai", "reply": ""},
                {"label": "🙋 Atendente", "action": "human", "reply": ""},
            ],
            "closed_action": "ai",
        },
    },
    "servicos": {
        "label": "Serviços com tabela de preços",
        "description": "Cyber, gráfica, assistência: informa valores da tabela, recebe arquivos para imprimir e passa o pedido para a equipe.",
        "config": {
            "order_mode": "none",
            "prompt": PROMPT_SERVICOS,
            "buttons_enabled": True,
            "buttons_title": "Como posso te ajudar? Toque numa opção 👇",
            "buttons": [
                {"label": "🖨️ Impressão/cópia", "action": "ai", "reply": ""},
                {"label": "📄 Documentos/online", "action": "ai", "reply": ""},
                {"label": "💰 Tabela de preços", "action": "reply", "reply": "Confira nossos serviços e valores 👇\n\n{{informacoes}}"},
                {"label": "🙋 Atendente", "action": "human", "reply": ""},
            ],
            "image_action": "vision",
            "document_action": "file",
            "closed_action": "ai",
        },
    },
    "servicos_menu": {
        "label": "Menu de opções (botões) + IA",
        "description": "Como os bots antigos: menu, submenu e perguntas de cada serviço com botões do WhatsApp; a IA só responde o que não for opção.",
        "config": {
            "order_mode": "none",
            "prompt": PROMPT_MENU,
            "menu_enabled": True,
            "button_style": "botoes",
            "buttons_enabled": False,
            "image_action": "vision",
            "document_action": "file",
            "closed_action": "ai",
        },
    },
}

# Fluxos antigos guardavam o tipo "delivery"; viram o modelo certo conforme a config.
LEGACY_TYPES = {"delivery": "delivery_link", "general": "atendimento", "scheduling": "agendamento"}

DEFAULTS = {
    # Negócio
    "store_name": "",
    "store_city": "",
    "store_address": "",
    "store_hours": "",
    "delivery_info": "",
    "business_info": "",
    # Pedido
    "order_mode": "link",
    "menu_url": "",
    "pix_key": "",
    # Agente
    "prompt": PROMPT_DELIVERY_LINK,
    "learned_rules": [],
    "model": DEFAULT_MODEL,
    "history_limit": 20,
    # Boas-vindas e botões (enquete do WhatsApp)
    "greeting_text": "",
    "buttons_enabled": False,
    "buttons_title": "Como posso te ajudar? Toque numa opção 👇",
    "buttons": [],
    # Como as opções aparecem: enquete, ou botões clicáveis do WhatsApp em blocos de 3 (precisa do Hermes v0.15.0+)
    "button_style": "enquete",
    # Menu de enquetes com perguntas por serviço (menu_flow.py); vazio = menu padrão da papelaria
    "menu_enabled": False,
    "menu": {},
    # Tipo de mensagem
    "audio_action": "transcribe",
    "audio_reply": "Oi! Não consigo ouvir áudio por aqui. Pode me mandar por escrito? 🙏",
    "image_action": "vision",
    "image_reply": "Recebi sua imagem! 👍",
    "document_action": "receipt",
    "document_reply": "Recebi seu arquivo! 👍",
    "other_action": "ai",
    "other_reply": "",
    # Horário de funcionamento
    "hours_enabled": False,
    "timezone": "America/Belem",
    "hours": {d: "" for d in WEEKDAYS},
    "closed_action": "ai",
    "closed_message": "Oi! No momento estamos fechados. 😴 Nosso horário: {{horario}}. Assim que abrirmos a gente te responde!",
    # Dono assumindo a conversa
    # 01/11 (dono): cada resposta da loja à mão pausa a IA 24 h naquela conversa (renova a cada resposta);
    # nada de desligar o contato para sempre. Com 60-120 min a IA voltava e respondia conversa pessoal do dono.
    "pause_on_owner_reply": True,
    "pause_minutes": 1440,
    "owner_off_two_messages": False,
    # Agrupar mensagens seguidas
    "buffer_seconds": 6,
    # Envio
    "reply_length": "curta",
    "typing": True,
    "split_messages": True,
    # Avisos para o dono
    "notify_phone": "",
    # Admins só deste fluxo (além dos admins gerais das Configurações): ensinam e simulam pelo WhatsApp
    "admin_phones": "",
    "notify_handoff": True,
    "notify_receipt": True,
    "notify_order": True,
}

ACTIONS_AUDIO = {"transcribe", "reply", "ai", "ignore"}
ACTIONS_IMAGE = {"vision", "receipt", "reply", "ignore"}
ACTIONS_DOCUMENT = {"receipt", "file", "reply", "ignore"}
ACTIONS_OTHER = {"ai", "reply", "ignore"}
ORDER_MODES = {"link", "pix", "none", "agendamento"}
BUTTON_ACTIONS = {"ai", "reply", "human"}
BUTTON_STYLES = {"enquete", "botoes"}
REPLY_LENGTHS = {
    "curta": "Seja MUITO breve: no máximo 2 frases curtas por resposta (umas 150 letras, sem contar o link). "
             "Não cumprimente de novo se já cumprimentou nesta conversa. Não termine com \"qualquer dúvida é só chamar\" "
             "nem frases de enfeite. Uma mensagem só, sem parágrafos extras.",
    "media": "Seja breve: no máximo 3 ou 4 frases curtas por resposta. Não repita o cumprimento.",
    "livre": "",
}

# Campos que o administrador pode trocar por mensagem no WhatsApp (e descrição para a IA que interpreta o pedido).
TEACHABLE_FIELDS = {
    "store_name": "nome da loja/empresa",
    "store_city": "cidade",
    "store_address": "endereço",
    "store_hours": "horário de funcionamento escrito para o cliente (ex.: 'todos os dias das 18h às 23h30')",
    "delivery_info": "informações de entrega (taxa, área, tempo)",
    "business_info": "informações extras da empresa: serviços, preços, perguntas frequentes",
    "menu_url": "link do cardápio digital",
    "pix_key": "chave Pix",
    "greeting_text": "mensagem fixa de boas-vindas enviada na primeira mensagem do cliente (vazio = a IA cumprimenta)",
    "buttons_enabled": "true/false: mandar botões (enquete) na primeira mensagem",
    "buttons_title": "título da enquete de botões",
    "audio_action": "o que fazer com áudio: transcribe (transcrever e responder), reply (resposta fixa), ai (a IA responde sem ouvir), ignore",
    "audio_reply": "resposta fixa para áudio",
    "image_action": "o que fazer com imagem: vision (a IA olha a imagem), receipt (tratar como comprovante), reply (resposta fixa), ignore",
    "image_reply": "resposta fixa para imagem",
    "document_action": "o que fazer com PDF/documento: receipt (comprovante), file (arquivo do cliente para o serviço, a IA sabe o nome e as páginas), reply (resposta fixa), ignore",
    "document_reply": "resposta fixa para documento",
    "closed_action": "fora do horário: reply (manda a mensagem de fechado) ou ai (a IA responde sabendo que está fechado)",
    "closed_message": "mensagem enviada fora do horário",
    "pause_minutes": "minutos que a IA fica pausada numa conversa depois que o dono responde à mão",
    "buffer_seconds": "segundos esperando o cliente terminar de digitar antes de responder",
    "split_messages": "true/false: dividir respostas longas em várias mensagens",
    "reply_length": "tamanho das respostas: curta (até 2 frases), media (3 a 4 frases) ou livre",
    "notify_phone": "número que recebe avisos (pedido, comprovante, cliente pedindo atendente)",
}


def flow_template_key(flow_type: str) -> str:
    return LEGACY_TYPES.get(flow_type, flow_type if flow_type in TEMPLATES else "delivery_link")


def new_config(template: str, overrides: dict | None = None) -> dict:
    cfg = copy.deepcopy(DEFAULTS)
    cfg.update(copy.deepcopy(TEMPLATES[template]["config"]))
    cfg.update(overrides or {})
    return normalize(cfg)


def normalize(raw: dict) -> dict:
    """Completa campos ausentes com o padrão e corrige tipos (config vinda do painel, do WhatsApp ou de versão antiga)."""
    cfg = copy.deepcopy(DEFAULTS)
    for k, v in (raw or {}).items():
        if k in DEFAULTS:
            cfg[k] = v
    # versão 1 guardava store_hours e o prompt era fixo no código
    for k in ("store_name", "store_city", "store_address", "store_hours", "delivery_info", "business_info",
              "menu_url", "pix_key", "prompt", "model", "greeting_text", "buttons_title", "audio_reply",
              "image_reply", "document_reply", "other_reply", "timezone", "closed_message", "notify_phone", "admin_phones"):
        cfg[k] = str(cfg[k] or "").strip() if k != "prompt" else str(cfg[k] or "")
    if not cfg["prompt"].strip():
        cfg["prompt"] = DEFAULTS["prompt"]
    if not cfg["model"]:
        cfg["model"] = DEFAULT_MODEL
    if not cfg["timezone"]:
        cfg["timezone"] = DEFAULTS["timezone"]
    cfg["menu"] = cfg["menu"] if isinstance(cfg["menu"], dict) else {}
    for k in ("menu_enabled", "buttons_enabled", "hours_enabled", "pause_on_owner_reply", "owner_off_two_messages", "typing", "split_messages",
              "notify_handoff", "notify_receipt", "notify_order"):
        cfg[k] = _to_bool(cfg[k])
    cfg["history_limit"] = _clamp_int(cfg["history_limit"], 4, 60, DEFAULTS["history_limit"])
    cfg["pause_minutes"] = _clamp_int(cfg["pause_minutes"], 0, 1440, DEFAULTS["pause_minutes"])
    cfg["buffer_seconds"] = _clamp_int(cfg["buffer_seconds"], 0, 60, DEFAULTS["buffer_seconds"])
    cfg["order_mode"] = cfg["order_mode"] if cfg["order_mode"] in ORDER_MODES else "link"
    cfg["audio_action"] = cfg["audio_action"] if cfg["audio_action"] in ACTIONS_AUDIO else "transcribe"
    cfg["image_action"] = cfg["image_action"] if cfg["image_action"] in ACTIONS_IMAGE else "vision"
    cfg["document_action"] = cfg["document_action"] if cfg["document_action"] in ACTIONS_DOCUMENT else "receipt"
    cfg["other_action"] = cfg["other_action"] if cfg["other_action"] in ACTIONS_OTHER else "ai"
    cfg["closed_action"] = cfg["closed_action"] if cfg["closed_action"] in ("ai", "reply") else "ai"
    cfg["reply_length"] = cfg["reply_length"] if cfg["reply_length"] in REPLY_LENGTHS else "curta"
    cfg["button_style"] = cfg["button_style"] if cfg["button_style"] in BUTTON_STYLES else "enquete"
    hours = cfg["hours"] if isinstance(cfg["hours"], dict) else {}
    cfg["hours"] = {d: str(hours.get(d) or "").strip() for d in WEEKDAYS}
    buttons = []
    for b in cfg["buttons"] if isinstance(cfg["buttons"], list) else []:
        if not isinstance(b, dict) or not str(b.get("label") or "").strip():
            continue
        action = b.get("action") if b.get("action") in BUTTON_ACTIONS else "ai"
        buttons.append({"label": str(b["label"]).strip()[:100], "action": action, "reply": str(b.get("reply") or "").strip()})
    cfg["buttons"] = buttons[:12]
    rules = []
    for r in cfg["learned_rules"] if isinstance(cfg["learned_rules"], list) else []:
        text = (r.get("text") if isinstance(r, dict) else str(r or "")).strip()
        if text:
            rules.append({
                "text": text[:600],
                "created_at": (r.get("created_at") if isinstance(r, dict) else "") or "",
                "source": (r.get("source") if isinstance(r, dict) else "") or "painel",
            })
    cfg["learned_rules"] = rules[:60]
    return cfg


def _to_bool(v) -> bool:
    if isinstance(v, str):
        return v.strip().lower() in ("1", "true", "sim", "yes", "on")
    return bool(v)


def _clamp_int(v, lo: int, hi: int, default: int) -> int:
    try:
        return max(lo, min(hi, int(v)))
    except (TypeError, ValueError):
        return default


def hours_summary(cfg: dict) -> str:
    names = {"seg": "seg", "ter": "ter", "qua": "qua", "qui": "qui", "sex": "sex", "sab": "sáb", "dom": "dom"}
    parts = [f"{names[d]} {cfg['hours'][d]}" for d in WEEKDAYS if cfg["hours"].get(d)]
    return ", ".join(parts)


def render_placeholders(text: str, cfg: dict, menu_text: str = "") -> str:
    values = {
        "loja": cfg["store_name"] or "nossa loja",
        "cidade": cfg["store_city"] or "não informado",
        "endereco": cfg["store_address"] or "não informado",
        "horario": cfg["store_hours"] or hours_summary(cfg) or "não informado",
        "entrega": cfg["delivery_info"] or "não informado",
        "link_cardapio": cfg["menu_url"] or "(link do cardápio não configurado)",
        "chave_pix": cfg["pix_key"] or "(chave Pix não configurada)",
        "cardapio": menu_text or "(cardápio vazio)",
        "informacoes": cfg["business_info"],
    }
    for k, v in values.items():
        text = text.replace("{{" + k + "}}", v)
    return text.strip()
