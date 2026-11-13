"""Foley contextual: o SOM DO QUE ACONTECE NA CENA (campainha, porta, soco, beijo...), disparado pelas palavras do VIDEO
REAGIDO (narrador do recap: "ele bate na porta" -> batida). Copiado de D:\\hipercool-videos\\bin\\fx_foley.py (18/10).

Diferente dos gatilhos de mr/triggers.py (palavra do CRIADOR -> som de meme). Aqui nao da para atrasar a fala (o audio do
video reagido vem misturado com o mic), entao o foley toca JUNTO, baixo e cortado em FOLEY_DUR_S com fade.
Liga/desliga: config overlays.foley.
"""
import re
from pathlib import Path
from .common import log

FOLEY_DUR_S = 2.3     # hipercool: gap 0.8 s + 1.5 s de fala
GAIN_DB = -10.0       # mesmo nivel dos gatilhos de palavra
COOLDOWN_S = 8.0
MAX_POR_PARTE = 3

# (situacao, arquivo relativo a paths.assets, [keywords]) - ordem importa: mais especifico primeiro.
FOLEY_MAP = [
    ("campainha", "sfx_memes/Campainha Ding Dong - Efeitos sonoros Nerzinho.mp3",
        ["ding dong", "ding-dong", "campainha", "interfone", "toca a campainha",
         "toca o interfone", "som da campainha"]),
    ("bate_porta", "sfx_memes/Batendo na Porta - Efeitos sonoros Nerzinho.mp3",
        ["bate na porta", "bateu na porta", "batida na porta", "batidas na porta", "bate à porta",
         "batem na porta", "bateram na porta", "knock"]),
    ("porta_abre", "sfx_memes/Minecraft Porta abrindo - Efeitos sonoros Nerzinho.mp3",
        ["porta se abre", "abre a porta", "abriu a porta", "abre uma porta",
         "porta desliza", "destranca", "porta abrindo"]),
    ("porta_fecha", "sfx_foley/door_close.wav",
        ["fecha a porta", "porta se fecha", "porta fechando", "bateu a porta",
         "porta bate"]),
    ("clack", "sfx_foley/door_close.wav",
        ["clack", "fechadura", "tranca", "destrava"]),
    ("passos", "sfx_memes/Minecraft som de passos - Efeitos sonoros Nerzinho.mp3",
        ["step step", "passos", "ponta dos pés", "caminha pelo corredor",
         "pés caminham", "anda pelo corredor", "step"]),
    ("telefone", "sfx_foley/phone_ring.wav",
        ["celular toca", "telefone toca", "ligação", "atende o telefone",
         "smartphone toca", "chamada"]),
    ("notificacao", "sfx_foley/notification.wav",
        ["notificação", "mensagem chega", "beep", "bipe"]),
    ("beijo", "sfx_foley/kiss_smooch.wav",
        ["beijo", "smooch", "beijando", "lábios", "selinho"]),
    # 18/10, testado na narracao do recap 3tMxBPYp6WE: "tapa" solto pegava "tapa os ouvidos" (verbo tapar), "comemora"
    # dava plateia pra 1 pessoa, "rajada de relampagos" dava vento e "espada" solta tocava em qualquer mencao
    ("soco", "sfx/punch.wav",
        ["soco", "golpe", "bateu", "dá um tapa", "deu um tapa", "leva um tapa", "levou um tapa", "punch", "murro",
         "golpe na cabeça", "leva um golpe"]),
    ("vidro", "sfx_foley/glass_break.wav",
        ["quebra o vidro", "vidro quebr", "estilha", "shatter", "vidro estilha",
         "copo quebr"]),
    ("tiro", "sfx_foley/gunshot.wav",
        ["tiro", "atira", "dispara a arma", "gunshot", "disparo"]),
    ("espada", "sfx_foley/sword_slash.wav",
        ["empunha a espada", "saca a espada", "sacou a espada", "desembainha", "brande a espada", "crava a espada",
         "cravou a espada", "enterrou a espada", "lâmina corta", "golpe de espada", "sword"]),
    ("coracao", "sfx_foley/heartbeat.wav",
        ["coração dispar", "coração bate", "palpita", "disparou", "batendo forte",
         "coração acelera", "heartbeat"]),
    ("comer", "sfx_foley/eating_crunch.wav",
        ["mastiga", "comendo", "crunch", "morde", "macarrão"]),
    ("beber", "sfx_foley/drinking_gulp.wav",
        ["bebe", "gole", "gulp", "tomando", "bebida", "brinde"]),
    ("chuva", "sfx_foley/rain_loop.wav",
        ["chuva", "chovendo", "tempestade de chuva", "rain"]),
    ("chuveiro", "sfx_foley/rain_loop.wav",
        ["chuveiro", "banho", "água caindo", "tomar banho"]),
    ("mar", "sfx_foley/ocean_waves.wav",
        ["ondas", "mar", "praia", "oceano", "ocean"]),
    ("grito", "sfx_foley/crowd_gasp.wav",
        ["multidão grita", "todos ofegam", "plateia", "gasp coletivo"]),
    ("aplauso", "sfx_foley/crowd_cheer.wav",
        ["aplauso", "aplaudem", "clap clap", "torcida"]),
    ("trovao", "sfx_foley/thunder.wav",
        ["trovão", "relâmpago", "raio cai", "thunder"]),
    ("vento", "sfx_foley/wind_blow.wav",
        ["vento forte", "vendaval", "rajada de vento", "wind"]),
    ("manha", "sfx_foley/birds_morning.wav",
        ["amanhece", "sol nasce", "de manhã", "pássaros cantam", "manhã ensolarada"]),
]


def _foley_path(cfg, rel):
    p = Path(cfg["paths"]["assets"]) / rel
    try:  # alguns assets baixados ficaram como XML de erro de ~111 B
        if not p.exists() or p.stat().st_size < 1000:
            return None
        with open(p, "rb") as fh:
            if fh.read(1) == b"<":
                return None
    except OSError:
        return None
    return p


def _tok(w):
    return re.sub(r"^[^\wà-ú]+|[^\wà-ú]+$", "", (w.get("w") or "").lower())


def plan_foley(cfg, content_words, timeline, duration):
    """content_words: palavras do video reagido (timeline ORIGINAL). Devolve sfx no timeline cortado."""
    toks = [_tok(w) for w in content_words]
    sfx, last_t, ultimo = [], -99.0, None
    for i, w in enumerate(content_words):
        if len(sfx) >= MAX_POR_PARTE:
            break
        if not toks[i] or not timeline.inside(w["s"]):
            continue
        t = timeline.map(w["s"])
        if t - last_t < COOLDOWN_S or t >= duration - 1.0:
            continue
        janela = " ".join(toks[i:i + 5])
        for situacao, rel, kws in FOLEY_MAP:
            # frase: comeca nesta palavra (aceita radical: "vidro quebr"); palavra solta: igual
            if not any(janela.startswith(kw) if " " in kw or "-" in kw else toks[i] == kw for kw in kws):
                continue
            if situacao == ultimo:  # mesmo som seguido: deixa respirar
                continue
            p = _foley_path(cfg, rel)
            if not p:
                continue
            sfx.append({"t": t, "file": p, "gain_db": GAIN_DB, "dur": FOLEY_DUR_S, "trigger": f"foley:{situacao}"})
            last_t, ultimo = t, situacao
            break
    if sfx:
        log(f"foley: {len(sfx)} ({', '.join(s['trigger'][6:] for s in sfx)})")
    return sfx
