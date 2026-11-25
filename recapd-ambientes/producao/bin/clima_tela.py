"""23/11 dona: "a barra de tempo de baixo pode melhorar muito — trocar de cor e formato conforme o que está sendo
narrado; o mesmo vale pra tarja e pra cor da legenda karaokê (quando não é MIX), e tamanhos diferentes junto com as
cores dependendo da palavra; você escolhe o gatilho".

Gatilho escolhido: o CLIMA do trecho (janela de ~20 s da narração), medido pelas palavras faladas:
  luta      soco/golpe/espada/ataque/sangue...        vermelho/laranja, barra "fogo", palavra forte 135%
  tensao    medo/perigo/sombra/ameaça/silêncio...     roxo escuro, barra "sombra" (pulsa devagar)
  romance   beijo/amor/coração/linda/vestido...       rosa, barra "coração" (ponta em coração)
  comedia   kkk/mentira/zoando/risada/hein...         amarelo vivo, barra "pulo" (ponta quica)
  dinheiro  bilion/milion/dinheiro/empresa/CEO...     verde/dourado, barra "moeda"
  sistema   sistema/nível/janela/status/missão...     ciano, barra "digital" (blocos)
  triste    chorou/morreu/sozinho/lágrima...          azul, barra "chuva" (fina, sem faíscas)
  normal    o resto                                    cor da cena (a de antes), barra sorteada
A palavra do karaokê ganha cor e tamanho pelo tipo dela: palavra do clima (ex.: "soco" numa luta) = cor do clima e
maior; número/dinheiro = verde e maior; nome próprio = cor do clima 115%; resto = amarelo de sempre.
CLIMA_TELA=0 desliga tudo (volta ao de antes)."""
import os
import re

LIGADO = os.environ.get("CLIMA_TELA", "1") != "0"
JANELA_S = 20.0

# (palavras, cor brilho &H00BBGGRR, núcleo, faísca, formato da barra, cor da palavra no karaokê RGB)
CLIMAS = {
    "luta": (r"soc[oa]|golpe|espad|ataq|sangu|lut[ao]|briga|chut|porrad|explod|destru|derrot|mat(ou|a|ar)\b|"
             r"arma|tiro|ferid|esmag|batalh|guerra|poder\b|aura",
             "&H000040FF", "&H0080D8FF", "&H0030A0FF", "fogo", (255, 90, 40)),
    "tensao": (r"medo|perig|sombr|amea[çc]|sil[êe]ncio|escur|assust|tens[ãa]o|susp|arrepi|cuidado|armadilh|segredo|"
               r"desconfi|estranh|trem(ia|eu)",
               "&H00A02870", "&H00FFB0E0", "&H00C060A0", "sombra", (180, 110, 255)),
    "romance": (r"beij|amor|apaixon|cora[çc][ãa]o|linda|lind[oa]|vestido|casament|noiv|namor|abra[çc]|olhar|"
                r"corou|vermelh[ao] de vergonha|charm|encant",
                "&H00A050FF", "&H00E0C0FF", "&H00C080FF", "coracao", (255, 110, 190)),
    "comedia": (r"\bkk+|mentir|zoand|brincadeir|risad|rindo|piada|hein\b|engra[çc]|vergonha alheia|kkk|rapaz|"
                r"molecada|galera",
                "&H0000D8FF", "&H00B0FFFF", "&H0040FFFF", "pulo", (255, 220, 30)),
    "dinheiro": (r"bilion|milion|milh[õo]es|bilh[õo]es|dinheir|empres|\bceo\b|herdeir|fortuna|rico|luxo|contrat|"
                 r"a[çc][õo]es|leil[ãa]o|reais|d[óo]lar",
                 "&H0040C850", "&H00B0FFD0", "&H0040D8FF", "moeda", (70, 230, 110)),
    "sistema": (r"sistema|n[íi]vel|janela|status|miss[ãa]o|habilidad|recompens|level|xp\b|classe|atributo|"
                r"notifica",
                "&H00FFD000", "&H00FFF8C0", "&H00FFFF60", "digital", (40, 220, 255)),
    "triste": (r"chor|morreu|morte|sozinh|l[áa]grim|triste|perdeu|luto|saudade|abandon|despedi|funeral",
               "&H00C08030", "&H00FFE0B0", "&H00FFC080", "chuva", (110, 160, 255)),
}
_RX = {k: re.compile(r"(?i)(" + v[0] + r")") for k, v in CLIMAS.items()}
_NUM = re.compile(r"(?i)^(\d[\d.,]*|r\$\S*|\$\S*|mil|milh\w+|bilh\w+|bilion\w*|milion\w*|dobro|triplo)$")

_TRECHOS = []  # [(ini, fim, clima)] do vídeo atual (o fx_subtitles preenche; barra e tarja leem)


def classificar(texto):
    melhor, n = "normal", 0
    for k, rx in _RX.items():
        c = len(rx.findall(texto or ""))
        if c > n:
            melhor, n = k, c
    return melhor if n >= int(__import__("os").environ.get("CLIMA_MIN_HITS", "1")) else "normal"  # 24/11: 2 -> 1


def montar(todas):
    """todas = [(início, fim, palavra)] do vídeo inteiro -> trechos de ~20 s com clima (vizinhos iguais se juntam)."""
    _TRECHOS.clear()
    if not LIGADO or not todas:
        return _TRECHOS
    fim_v = max(f for _i, f, _w in todas)
    t = 0.0
    while t < fim_v:
        t1 = t + JANELA_S
        txt = " ".join(w for i, _f, w in todas if t <= i < t1)
        c = classificar(txt)
        if _TRECHOS and _TRECHOS[-1][2] == c:
            _TRECHOS[-1] = (_TRECHOS[-1][0], t1, c)
        else:
            _TRECHOS.append((t, t1, c))
        t = t1
    return _TRECHOS


def clima_em(t):
    for a, b, c in _TRECHOS:
        if a <= t < b:
            return c
    return "normal"


def clima_dominante(a, b):
    """clima que mais tempo ocupa entre a e b (o capítulo inteiro)."""
    tot = {}
    for x, y, c in _TRECHOS:
        o = min(b, y) - max(a, x)
        if o > 0:
            tot[c] = tot.get(c, 0) + o
    return max(tot, key=tot.get) if tot else "normal"


def cor_barra(clima):
    v = CLIMAS.get(clima)
    return (v[1], v[2], v[3], v[4]) if v else None


# 24/11 dona ("não vi a legenda colorida"): no longo real só 3,8% das palavras coloriam (metade do vídeo é "normal").
# Agora: qualquer palavra de clima (de QUALQUER clima, não só o do trecho) pinta na cor dela; no trecho "normal" as palavras
# fortes ganham o tom quente do canal; nomes e números sempre destacam. CLIMA_CORES_FORTE=0 volta ao de antes.
_FORTE_NORMAL = (255, 150, 40)
_EMOCAO = __import__("re").compile(r"(?i)^(nunca|jamais|tudo|nada|todo|toda|ninguém|absurd\w*|incr[íi]vel|imposs[íi]vel|"
                                   r"chocad\w*|furios\w*|humilh\w*|vingan[çc]a|traiu|trai[çc][ãa]o|segredo|verdade|"
                                   r"mentira|perigo|desesper\w*|lend[áa]ri\w*|poderos\w*|gigante|enorme|maluc\w*|doid\w*)$")


def palavra(w, t, padrao_rgb):
    """(cor RGB, escala %) da palavra ativa do karaokê."""
    if not LIGADO:
        return padrao_rgb, 100
    c = clima_em(t)
    lw = (w or "").strip(".,!?;:…\"'").lower()
    forte = __import__("os").environ.get("CLIMA_CORES_FORTE", "1") != "0"
    if _NUM.match(lw):
        return (70, 230, 110), 125
    if c != "normal" and _RX[c].search(lw):
        return CLIMAS[c][5], 135
    if forte:
        for k, rx in _RX.items():  # palavra de clima fora do trecho dela também pinta (soco numa cena "normal")
            if len(lw) >= 4 and rx.search(lw):
                return CLIMAS[k][5], 125
    if (w or "")[:1].isupper() and len(lw) > 3:
        return (CLIMAS[c][5] if c != "normal" else (_FORTE_NORMAL if forte else padrao_rgb)), 115
    if forte and _EMOCAO.match(lw):
        return (CLIMAS[c][5] if c != "normal" else _FORTE_NORMAL), 125
    if c != "normal" and len(lw) >= (6 if forte else 7):
        return CLIMAS[c][5], 108
    return padrao_rgb, 100


def bgr_ass(rgb):
    return "&H%02X%02X%02X&" % (rgb[2], rgb[1], rgb[0])
