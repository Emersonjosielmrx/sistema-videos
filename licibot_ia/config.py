"""
LiciBot-IA · config.py
Configuração, padrões de palavras-chave (regex sem acento), CNAEs do MEI e parâmetros financeiros.
Tudo que muda entre máquinas fica no .env; o resto é regra de negócio e fica aqui.
"""

import os
import re
import unicodedata
from pathlib import Path

from dotenv import load_dotenv

BASE = Path(__file__).resolve().parent
load_dotenv(BASE / ".env")

# O PNCP fala em horário de Brasília e a VPS 157 está em Europe/Berlin: fixa o fuso do processo para que
# datetime.now() e o datetime('now','localtime') do SQLite comparem com os prazos do PNCP sem erro de horas.
os.environ["TZ"] = os.getenv("FUSO", "America/Sao_Paulo")
if hasattr(__import__("time"), "tzset"):
    __import__("time").tzset()


# Ajustes feitos no painel de controle (ajustes.json) valem por cima do .env.
AJUSTES_ARQ = BASE / "ajustes.json"
try:
    import json as _json
    AJUSTES: dict = _json.loads(AJUSTES_ARQ.read_text(encoding="utf-8"))
except (OSError, ValueError):
    AJUSTES = {}


def _v(nome: str, padrao) -> str:
    return str(AJUSTES[nome]) if nome in AJUSTES else os.getenv(nome, str(padrao))


def _f(nome: str, padrao: float) -> float:
    return float(_v(nome, padrao))


def _i(nome: str, padrao: int) -> int:
    return int(float(_v(nome, padrao)))


# ── LLM (OmniRoute da VPS 157, formato Anthropic /v1/messages) ──────────────
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "http://localhost:20128")
LLM_API_KEY = os.getenv("LLM_API_KEY", "")
LLM_MODEL = "cadeia-gratis"                             # 12/11: só modelos grátis (ver ai_analyzer.MODELOS_GRATIS)
LLM_EFFORT = _v("LLM_EFFORT", "medium")                  # low | medium | high | xhigh | max
LLM_PROMPT = _v("LLM_PROMPT", "v2")                      # v1 = original; v2 = regras de julgamento explícitas
LLM_PARALELO = _i("LLM_PARALELO", 3)                     # análises simultâneas
LLM_TIMEOUT = _f("LLM_TIMEOUT", 300)
IA_MAX_POR_VARREDURA = _i("IA_MAX_POR_VARREDURA", 120)    # teto de análises por varredura (0 = sem teto)
LLM_MAX_TENTATIVAS = _i("LLM_MAX_TENTATIVAS", 3)        # depois disso o edital fica "sem análise" (não avisa)
TEXTO_MAX_CHARS = _i("TEXTO_MAX_CHARS", 120_000)         # texto dos documentos guardado no banco
IA_TEXTO_MAX_CHARS = _i("IA_TEXTO_MAX_CHARS", 60_000)    # quanto desse texto vai ao modelo (custo: ~1 token / 3,5 car.)
MODO_TOKENS_ARQ = os.getenv("MODO_TOKENS_ARQ", "/opt/omniroute/modo_tokens.json")  # "esgotado" = adia a IA

# ── Notificações ─────────────────────────────────────────────────────────────
# Tudo de aviso fica em AJUSTES["AVISOS"] (o painel grava). Lido de novo a cada uso: o painel é um processo
# que fica no ar e não pode depender do valor do momento em que subiu.
GAVETA_TIPO = {"produtos_faceis": "produto", "servicos_ia": "servico", "solar": "obra"}
UFS_VIZINHAS = {"GO": ["GO", "DF", "MG", "MS", "MT", "BA", "TO"]}
AVISOS_PADRAO = {
    "tg_token": "", "tg_chat": "",
    "oportunidade": True,          # oportunidade nova que passa nos filtros abaixo
    "lembrete_prazo": True,        # "vou participar" que fecha em menos de 24 h
    "erro": True,                  # varredura quebrou
    "sem_credito": True,           # IA adiada por falta de crédito do Opus (no máximo 1 a cada 12 h)
    "resumo_diario": True, "hora_resumo": 8,
    "silencio_de": 22, "silencio_ate": 7,       # sem aviso nesse intervalo (fica para depois)
    "carteiras": ["MEI", "CPF", "AMIGO_SOLAR"],
    "tipos": ["produto", "servico", "obra"],
    "ufs": [],                     # vazio = todo o Brasil
    "liquido_min": 0,              # R$ que sobra no bolso, no mínimo
    "invest_min": 0,               # R$ de custo para entregar (compra da mercadoria, ferramentas), de...
    "invest_max": 0,               # ...até (0 = sem limite)
    "valor_min": 0,                # valor estimado da licitação, de...
    "valor_max": 0,                # ...até (0 = sem limite)
}


def ajustes_atuais() -> dict:
    try:
        return _json.loads(AJUSTES_ARQ.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def avisos() -> dict:
    a = ajustes_atuais()
    cfg = {**AVISOS_PADRAO, **(a.get("AVISOS") or {})}
    cfg["tg_token"] = cfg["tg_token"] or os.getenv("TELEGRAM_BOT_TOKEN", "")
    cfg["tg_chat"] = cfg["tg_chat"] or os.getenv("TELEGRAM_CHAT_ID", "")
    cfg["nota_min"] = float(a.get("NOTIFICAR_SCORE_MIN", os.getenv("NOTIFICAR_SCORE_MIN", 50)))
    cfg["max_por_aviso"] = int(float(a.get("NOTIFICAR_MAX", os.getenv("NOTIFICAR_MAX", 10))))
    return cfg


WEBHOOK_URL = os.getenv("WEBHOOK_URL", "")
TELEGRAM_BOT_TOKEN = avisos()["tg_token"]
TELEGRAM_CHAT_ID = avisos()["tg_chat"]
NOTIFICAR_SCORE_MIN = _i("NOTIFICAR_SCORE_MIN", 50)      # só avisa oportunidade com nota final >= isso
NOTIFICAR_MAX = _i("NOTIFICAR_MAX", 10)                  # máximo de itens por aviso

# ── Onde estamos ─────────────────────────────────────────────────────────────
NOSSA_UF = os.getenv("NOSSA_UF", "GO")
NOSSA_CIDADE = os.getenv("NOSSA_CIDADE", "Itumbiara")

# ── Varredura do PNCP ────────────────────────────────────────────────────────
PNCP_CONSULTA = "https://pncp.gov.br/api/consulta/v1"
PNCP_API = "https://pncp.gov.br/pncp-api/v1"
PNCP_PARALELO = _i("PNCP_PARALELO", 3)                   # fios; o ritmo é controlado por PNCP_DELAY (global)
PNCP_DELAY = _f("PNCP_DELAY", 0.5)                       # intervalo mínimo entre requisições (todos os fios)
TAMANHO_PAGINA = 50                                      # a API recusa > 50 e < 10
DIAS_A_FRENTE = _i("DIAS_A_FRENTE", 60)                  # dataFinal = hoje + isso (prazo de encerramento)
HORAS_MINIMAS_PREPARO = _i("HORAS_MINIMAS_PREPARO", 24)  # ignora o que fecha antes disso
# 4 = Concorrência eletrônica, 6 = Pregão eletrônico, 8 = Dispensa, 12 = Credenciamento.
# Presenciais (5, 7, 13) ficam de fora: exigem ir à sessão.
MODALIDADES = [int(x) for x in os.getenv("MODALIDADES", "8,6,12,4").split(",") if x.strip()]
ARQUIVO_MAX_MB = _i("ARQUIVO_MAX_MB", 40)
DOCS_POR_EDITAL = _i("DOCS_POR_EDITAL", 4)
DOCS_ATE_VALOR = _f("DOCS_ATE_VALOR", 300_000)              # acima disso (exceto solar) só itens, sem documentos
OCR_MAX_PAGINAS = _i("OCR_MAX_PAGINAS", 15)                 # PDF escaneado: OCR (tesseract por) até X páginas
DIAS_COLETA_RESULTADO = _i("DIAS_COLETA_RESULTADO", 10)  # coleta o preço vencedor X dias após fechar

DB_PATH = os.getenv("DB_PATH", str(BASE / "licibot.db"))
LOG_PATH = os.getenv("LOG_PATH", str(BASE / "licibot.log"))


# ═════════════════════════════════════════════════════════════════════════════
# ESTÁGIO 1 — regex sobre o texto SEM ACENTO e minúsculo (ver normalizar()).
# Cada padrão usa limite de palavra; termos genéricos ("video", "site", "monitor")
# só entram compostos, porque sozinhos puxavam decoração de natal, piscina etc.
# ═════════════════════════════════════════════════════════════════════════════

def normalizar(texto: str) -> str:
    t = unicodedata.normalize("NFKD", texto or "")
    t = "".join(c for c in t if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", t.lower()).strip()


_SERVICOS_IA = [
    r"degrava\w*",
    r"transcri\w+ (de |das |dos |em )?(audio|video|sess|reuni|grava|atas?\b|depoiment|audienc|entrevist|fala)",
    r"taquigraf\w*", r"estenotip\w*",
    r"atas? (das|de|da) (sess|reuni|audienc)",
    r"edicao (de )?(videos?|audio|imagens?)", r"editor(a)? de video",
    r"produc(ao|oes) (de )?(videos?|audiovisu\w*|conteudos?|podcasts?)",
    r"legendag\w*", r"closed caption", r"audiodescri\w*",
    r"locuc(ao|oes)", r"locutor", r"dublag\w*",
    r"spots? (publicitari\w*|de radio|para radio|institucion\w*)", r"jingles?", r"vinhetas?", r"podcasts?",
    r"diagramac\w*", r"editorac\w*", r"cartilhas?", r"e-?books?", r"revisao (ortografica|textual|gramatical)",
    r"traduc(ao|oes)",
    r"digitaliza\w* (de |do |da |dos |das )?(document|acervo|process|arquiv|prontuar|livro|jornal)",
    r"\bocr\b", r"indexa\w* (de )?(document|acervo|arquiv)", r"gestao eletronica de documentos",
    r"inteligencia artificial", r"\bia generativa", r"chat ?bots?", r"assistente virtual", r"agente virtual",
    r"desenvolvimento (de |do )?(sistemas?|softwares?|aplicativos?|apps?|portal|sites?|plataforma)",
    r"(criacao|manutencao|reformulacao) (de |do )?(sites?|portal|pagina|website)",
    r"automac(ao|oes) de processos", r"automacao robotica",   # "RPA" no PNCP é quase sempre drone
    r"(curso|treinamento|capacitac\w+|oficina)s? (de |em |sobre )(informatica|inteligencia artificial|tecnologia|excel|ferramentas digitais)",
    r"marketing digital", r"gestao de (redes sociais|midias sociais|conteudo)",
    r"criacao de (artes|pecas) (graficas|digitais|publicitarias)",
]

_PRODUTOS_FACEIS = [
    r"\bssds?\b", r"memorias? ram", r"hds? externos?", r"discos? rigidos?",
    r"nobreaks?", r"no-breaks?", r"estabilizador(es)?",
    r"monitor(es)? (de video|led|lcd|de computador|\d)",
    r"webcams?", r"cameras? web", r"microfones?", r"headsets?", r"fones? de ouvido",
    r"caixas? (de som|acusticas?|amplificadas?)", r"mesa de som",
    r"fragmentadora\w*", r"projetor(es)? (multimidia|de imagem)", r"datashow",
    r"impressoras?", r"multifuncion\w*", r"toners?", r"cartuchos?",
    r"notebooks?", r"computador(es)? (desktop|portateis?|pessoais?|tipo)", r"microcomputador\w*", r"all.in.one",
    r"chromebooks?", r"tablets?",
    r"\bswitch(es)? (de rede|gerenciave\w*|\d)", r"roteador(es)?", r"access points?", r"pen ?drives?",
    r"(equipamentos?|materia\w*|suprimentos?|insumos?|perifericos?|acessorios?|produtos?) (de |para )?informatica",
    r"refletor(es)? (solar\w*|de led|led)", r"luminarias? solar\w*",
]

_SOLAR = [
    r"fotovolta\w+", r"usinas? solar\w*", r"energia solar", r"placas? solar\w*", r"paine(l|is) solar\w*",
    r"modulos? solar\w*", r"gerac\w+ distribuida", r"microgera\w+", r"minigera\w+",
    r"inversor(es)? (solar\w*|fotovolt\w*|on.grid|hibrido)", r"eficiencia energetica", r"subestac\w+",
]

# Descarte imediato (só no objeto da compra). Serve para matar colisões com os padrões acima.
_NEGATIVOS = [
    r"protetor solar", r"filtro solar", r"bronzead\w*", r"aquecimento solar", r"aquecedor\w* solar",
    r"medicament\w*", r"farmac\w*", r"hospitalar\w*", r"cirurg\w*", r"odontolog\w*", r"protese\w*", r"ortese\w*",
    r"multiparametr\w*", r"servicos medicos", r"plantao medico", r"enfermag\w*", r"exames? laboratori\w*",
    r"dependentes quimicos", r"comunidade terapeutica",
    r"merenda", r"generos alimenticios", r"alimentacao escolar", r"refeic\w+", r"lanches?", r"coffee break",
    r"buffet", r"panetones?", r"cestas? basicas?",
    r"combustive\w*", r"gasolina", r"diesel", r"lubrificante\w*", r"pneus?", r"pecas automotivas",
    r"computador de bordo", r"ambulancia\w*",
    r"asfalt\w*", r"paviment\w*", r"recape\w*", r"terraplen\w*", r"cascalho", r"demolic\w*",
    r"reforma (de|da|do|e) ", r"construcao (de|da|do) ", r"obras? de engenharia civil",
    r"grama\b", r"adubo", r"fertiliz\w*", r"sementes?",
    r"material de limpeza", r"material de higiene", r"gas liquefeito", r"\bglp\b",
    r"decorac\w+ (de )?natal\w*", r"natalin\w*", r"ornamentac\w*",
    r"funerari\w*", r"translado", r"veterinari\w*", r"castrac\w*",
    r"seguro (patrimonial|predial|automotivo|veicular|de vida)", r"inspecao predial",
    r"materia\w* esportiv\w*", r"fardamento", r"uniformes?",
    r"locacao de (palco|estrutura|tendas?|banheiros?)", r"\bshows?\b", r"iluminacao cenica",
    r"transporte (escolar|de passageiros)", r"postos? de trabalho", r"cessao de mao de obra",
    # 11/11: medidos contra 491 análises do Opus — cortam 28 descartes e nenhum aprovado
    r"sabonete", r"polipropileno", r"refil de filtro", r"\blibras\b", r"interpretacao", r"interprete\b",
    r"subscric\w+", r"web ?tv", r"cobertura (fotografica|de eventos|jornalistica)", r"transmiss\w+ ao vivo",
    r"som e iluminacao", r"aeronave", r"servicos graficos", r"impressao grafica", r"\bscm\b",
    r"acesso a internet", r"banda larga", r"radiografi", r"raio.?x", r"camera(s)? ocr", r"leitura de placas",
    r"exposicao itinerante", r"carro de som", r"locacao (de )?(multifuncion|copiadora|tablet|notebook|computador)",
]


def _compilar(padroes: list[str]) -> list[re.Pattern]:
    return [re.compile(r"(?<![a-z0-9])" + p) for p in padroes]


GAVETAS: list[tuple[str, list[re.Pattern]]] = [
    ("solar", _compilar(_SOLAR)),
    ("servicos_ia", _compilar(_SERVICOS_IA)),
    ("produtos_faceis", _compilar(_PRODUTOS_FACEIS)),
]
NEGATIVOS = _compilar(_NEGATIVOS)


# ═════════════════════════════════════════════════════════════════════════════
# CNAEs do MEI (ocupações do Anexo XI da Resolução CGSN 140/2018).
# Desenvolvimento de software, web design, consultoria e suporte em TI NÃO são
# permitidos ao MEI -> vão para a carteira CPF. Conferir a lista no Portal do
# Empreendedor antes de abrir/alterar o MEI.
# ═════════════════════════════════════════════════════════════════════════════
CNAES_MEI: dict[str, str] = {
    "8219-9/99": "Digitador / preparação de documentos (degravação, transcrição, digitalização)",
    "8219-9/01": "Fotocopiador (digitalização de documentos)",
    "5912-0/99": "Editor de vídeo independente",
    "9001-9/99": "Locutor de mensagens fonadas e ao vivo",
    "1821-1/00": "Diagramador / serviços de pré-impressão",
    "8599-6/03": "Instrutor de informática (treinamento em informática)",
    "9511-8/00": "Técnico de manutenção de computador",
    "4751-2/01": "Comércio de equipamentos e suprimentos de informática",
    "4753-9/00": "Comércio de eletrodomésticos e equipamentos de áudio e vídeo",
    "4321-5/00": "Eletricista em residências e estabelecimentos comerciais",
    "7319-0/02": "Promoção de vendas",
}

# ═════════════════════════════════════════════════════════════════════════════
# Finanças
# ═════════════════════════════════════════════════════════════════════════════
TETO_MEI_ANUAL = _f("TETO_MEI_ANUAL", 81_000.00)
MEI_FATURADO_ANO = _f("MEI_FATURADO_ANO", 0.0)           # quanto o MEI já faturou no ano (atualize no .env)
MEI_DAS_MENSAL = _f("MEI_DAS_MENSAL", 80.0)
COMISSAO_AMIGO_SOLAR = _f("COMISSAO_AMIGO_SOLAR", 0.10)   # nossa parte nos contratos do parceiro
DESCONTO_PADRAO = {"servicos_ia": 0.25, "produtos_faceis": 0.20, "solar": 0.15}  # até o histórico ter dados

# IN SEGES/ME 116/2021: a pessoa física soma 20% (contribuição patronal) à proposta só para comparar;
# se vencer, o órgão tira esses 20% e recolhe ao INSS.
CPF_ENCARGO_COMPARACAO = 0.20
INSS_ALIQUOTA_PF = 0.11
INSS_TETO = _f("INSS_TETO", 8_475.55)                    # teto do salário de contribuição (confirmar o de 2026)
# IRRF mensal 2026 (Receita Federal): (limite superior, alíquota, parcela a deduzir)
IRRF_TABELA = [
    (2_428.80, 0.0, 0.0),
    (2_826.65, 0.075, 182.16),
    (3_751.05, 0.15, 394.16),
    (4_664.68, 0.225, 675.49),
    (float("inf"), 0.275, 908.73),
]
# Lei 15.270/2025: imposto zerado até R$ 5.000; entre 5.000,01 e 7.350 redutor = 978,62 - 0,133145 x renda
IRRF_ISENTO_ATE = 5_000.00
IRRF_REDUTOR_ATE = 7_350.00

# ── Bom pagador (poderId / esferaId do PNCP; "N" = não se aplica) ───────────
PESO_PODER = {"L": 1.0, "J": 0.95, "E": 0.6, "N": 0.5}
PESO_ESFERA = {"F": 1.0, "E": 0.7, "D": 0.7, "M": 0.5, "N": 0.5}
