# -*- coding: utf-8 -*-
"""censura_visual.py — censura +18 na IMAGEM do painel, só nas PARTES explícitas.

Base: V8 de produção (D:\\recapd-ambientes\\producao, validada em 2026-07-02/03).
Melhoria (2026-10-13): em vez de borrar o painel inteiro, localiza as regiões explícitas
(Gemini, box_2d) e aplica mosaico SÓ nelas. Rosto, balão, fundo e a legenda (queimada
depois, por cima) continuam visíveis.

  DETECÇÃO (quais painéis):  Sightengine nudity-2.0 (score ponderado, cache md5)
                             -> fallback NudeNet local (fraco em manhwa).
  LOCALIZAÇÃO (onde):        Gemini visão devolve caixas (cache md5). NudeNet não serve:
                             em arte de manhwa ele não acha quase nada.
  APLICAÇÃO (censurar_imagem):
    score < LIMIAR_DUVIDA            -> intacto
    caixas achadas                   -> "local": mosaico só nas caixas (balões preservados)
    caixas cobrem quase tudo / Gemini falhou / score forte sem caixa
                                     -> "fosco": exodia fosco da V8 (fundo borrado, balões nítidos)
    Gemini diz "nada explícito" e score só de dúvida -> intacto
    tipo="branco" (mancha branca + vizinho +18) -> censura especial branca (V8)
"""
import hashlib
import json
import os
import re
import shutil
import subprocess
import time
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
CACHE_DIR = PROJECT_DIR / "workspace" / "censura_cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

# Chaves Sightengine: lê todas as cópias existentes (cada projeto guardou as suas).
KEY_FILES = [
    PROJECT_DIR / "secrets" / "sightengine.json",
    Path(r"D:\postador-de-videos\secrets\sightengine.json"),
    Path(r"D:\recapd-ambientes\producao\secrets\sightengine.json"),
]

# Score ponderado (sexual_activity*2 + sexual_display*1.5 + erotica*1.2). Calibrado na V8.
# 16/10 (noite): baixado de 0,45 pra 0,25. O dono assistiu o cap 4 e achou aos 3m25 um quadro que
# ele mesmo classificou como passível de banimento — close de roupa íntima. Aquele painel (o 040)
# tinha score 0,433 e passou DIRETO por 0,017 de diferença; a análise do vídeo pronto também não
# pegou. Roupa íntima em close não é "nudez" pro detector, mas é conteúdo sexual pro YouTube.
# Custo medido em 545 painéis de 5 capítulos: de 0,45 pra 0,25 entram 25 painéis a mais (5 por
# capítulo) na conferência — barato perto de perder o canal.
LIMIAR_DUVIDA = float(os.environ.get("CENSURA_LIMIAR_DUVIDA", "0.25"))
LIMIAR_NSFW = float(os.environ.get("CENSURA_LIMIAR_NSFW", "1.15"))
# Acima dessa fração do painel coberta por caixas, o mosaico local vira o painel todo -> fosco.
# ORDEM DO DONO (16/10): MOSAICO PRIMEIRO, fosco só quando não tiver jeito. Cheguei a baixar isto
# pra 0,40 por achar o mosaico grande feio (55 painéis em 9 capítulos virariam fosco) — desfeito:
# estética não decide isso. Quem manda o painel pro fosco é a prova de que o mosaico não resolveu:
# cobertura menor que MIN_FRAC_LOCAL com nudez forte, a conferência da imagem já censurada, e a
# lista de painéis reprovados pela análise do vídeo pronto.
MAX_FRAC_LOCAL = float(os.environ.get("CENSURA_MAX_FRAC_LOCAL", "0.80"))
# ABAIXO dessa fração, com score de nudez forte, o mosaico local não cobre nada que importe
# (o modelo marca 1 mamilo e o resto do corpo nu fica nítido) -> fosco. Em painel só de dúvida
# (score < LIMIAR_NSFW) o mosaico pequeno continua valendo: ali a parte explícita é pequena mesmo.
MIN_FRAC_LOCAL = float(os.environ.get("CENSURA_MIN_FRAC_LOCAL", "0.03"))
# Score ALTO é cena sexual inteira, não um pedaço a cobrir: aí o mosaico precisa cobrir bem mais do
# painel, senão o resto do quadro conta a mesma história em volta das caixas. Medido no cap 3 em
# 16/10: com score 1,73 e mosaico de 21% a análise do vídeo pronto reprovou 3 quadros do painel 100.
# Pelos números do capítulo, estes dois valores pegam os 4 painéis de score alto e mosaico pequeno
# (1,73/21%, 1,67/24%, 1,39/10%, 1,38/16%) e deixam em paz os de score baixo (0,84/63%, 0,78/20%).
SCORE_CENA_INTEIRA = float(os.environ.get("CENSURA_SCORE_CENA_INTEIRA", "1.30"))
FRAC_EXIGIDA_SCORE_ALTO = float(os.environ.get("CENSURA_FRAC_SCORE_ALTO", "0.35"))

PROMPT_REGIOES = (
    "Você é um moderador de conteúdo preparando a versão censurada de um painel de manhwa "
    "(personagens adultos) para o YouTube.\n"
    "1) Decida se o painel é EXPLÍCITO: genitália, mamilos ou nádegas DESCOBERTOS; calcinha/cueca à "
    "mostra em contexto sexual (ex.: por baixo da saia); mão tocando seio, virilha ou nádegas de forma "
    "sexual; fluidos corporais. NÃO é explícito: corpo coberto por roupa, decote com roupa, beijo, "
    "abraço, rosto corado, personagem vestida em pose comum.\n"
    "2) Se for explícito, liste SÓ as regiões a borrar (essas partes e as mãos tocando nelas). NÃO "
    "inclua rostos, balões de fala, texto, cabelo, roupa comum nem o fundo.\n"
    'Responda só JSON: {"explicito":true|false,"regioes":[{"rotulo":"...","box_2d":[ymin,xmin,ymax,xmax]}]} '
    "com coordenadas normalizadas 0-1000 (regioes vazia se não for explícito)."
)
REGIOES_VER = "regioes2"  # muda quando o prompt muda -> não reusa resposta do prompt antigo

# SILHUETA BRANCA (dono 19/10): a própria obra "censura" o pênis pintando-o de BRANCO/luz, liso e sem traços — mas o
# contorno continua com o formato do órgão. O Sightengine/NudeNet não veem pele ali, a localização acima não marcava,
# e o fosco/mosaico por cima de uma mancha branca grande mantém a silhueta (caps 8, 9 e 14: o dono achou nos quadros).
# Pergunta própria só sobre essa forma; a caixa dela tem o branco APAGADO (inpaint) antes de qualquer censura e
# sempre leva mosaico. Testado 19/10: achou nos 5 painéis com a forma (cap08 047/074, cap09 030/059, cap14 003) e não
# marcou nada em 3 painéis com faixa de luz/brilho que um filtro só geométrico confundia.
PROMPT_SILHUETA = (
    "Você é um moderador de conteúdo preparando a versão censurada de um painel de manhwa (personagens adultos) "
    "para o YouTube. Alguns autores escondem a genitália masculina pintando-a como uma FORMA BRANCA ou de luz, lisa, "
    "sem traços dentro — mas o contorno dessa forma continua com o formato do órgão (alongado, ponta arredondada). "
    "Marque SÓ formas assim. NÃO marque balões de fala, texto, céu, parede, luz de janela, faixas finas de brilho, "
    "roupa branca nem gotas pequenas.\n"
    'Responda só JSON: {"tem":true|false,"regioes":[{"box_2d":[ymin,xmin,ymax,xmax]}]} '
    "com coordenadas normalizadas 0-1000 (regioes vazia se não tiver)."
)
SILHUETA_VER = "silhueta1"
BRANCO_MIN = 225        # pixel "branco da silhueta" (os 3 canais)
BRANCO_FRAC_MIN = 0.05  # caixa com menos branco que isso: nada pra apagar (só leva o mosaico)

_keys = None
_nudenet = None


def _ffmpeg():
    return shutil.which("ffmpeg") or "ffmpeg"


def _md5(img_path):
    return hashlib.md5(Path(img_path).read_bytes()).hexdigest()


# ─── Chaves Sightengine ──────────────────────────────────────────────────────
KEY_STATUS = CACHE_DIR / "_chaves_esgotadas.json"  # api_user -> dia em que esgotou (só deste projeto)


def _load_keys():
    """Chaves de todos os KEY_FILES, sem repetir api_user. Só lê esses arquivos (são de
    outros projetos); o status 'exhausted' antigo deles é ignorado — vale o KEY_STATUS."""
    global _keys
    if _keys is None:
        _keys, vistos = [], set()
        for f in KEY_FILES:
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
            except Exception:
                continue
            for k in data.get("keys", []):
                if k.get("api_user") and k["api_user"] not in vistos:
                    vistos.add(k["api_user"])
                    _keys.append(k)
    return _keys


def _esgotadas():
    try:
        return json.loads(KEY_STATUS.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _pick_key():
    """Primeira chave que não esgotou HOJE (o limite diário do plano grátis zera; se for o
    mensal, ela falha de novo e é remarcada no dia)."""
    hoje, esg = time.strftime("%Y-%m-%d"), _esgotadas()
    for k in _load_keys():
        if esg.get(k["api_user"]) != hoje:
            return k
    return None


def _mark_exhausted(key):
    esg = _esgotadas()
    esg[key["api_user"]] = time.strftime("%Y-%m-%d")
    KEY_STATUS.write_text(json.dumps(esg, indent=2), encoding="utf-8")


# ─── Detecção (quais painéis) ────────────────────────────────────────────────
def _score_ponderado(nud):
    """Só sinais de nudez real. NÃO reintroduza 'suggestive' nem '1-none': foram a causa
    dos falsos positivos de 2026-07-02 (personagem vestida tarjada). Ver V8."""
    return (nud.get("sexual_activity", 0) * 2.0
            + nud.get("sexual_display", 0) * 1.5
            + nud.get("erotica", 0) * 1.2)


def _get_nudenet():
    global _nudenet
    if _nudenet is None:
        try:
            from nudenet import NudeDetector
            _nudenet = NudeDetector()
        except Exception:
            _nudenet = False
    return _nudenet


def _score_nudenet(img_path):
    det = _get_nudenet()
    if not det:
        return 0.0
    try:
        res = det.detect(str(img_path))
    except Exception:
        return 0.0
    s = 0.0
    for d in res:
        cls = d.get("class", "")
        if "EXPOSED" not in cls:
            continue
        conf = float(d.get("score", 0) or 0)
        s += (1.5 if "GENITALIA" in cls else 1.2 if ("BREAST" in cls or "BUTTOCKS" in cls) else 0.7) * conf
    return s


def detectar_score(img_path):
    """(score, origem). origem: 'sightengine' | 'nudenet' | None (nada disponível).
    Cache guarda o dict cru do Sightengine e recalcula o score na leitura (zero custo)."""
    h = _md5(img_path)
    cache_f = CACHE_DIR / f"{h}.json"
    if cache_f.exists():
        try:
            d = json.loads(cache_f.read_text(encoding="utf-8"))
            return _score_ponderado(d.get("nudity", {})), "sightengine"
        except Exception:
            pass
    key = _pick_key()
    if key:
        try:
            import requests
            with open(img_path, "rb") as fh:
                r = requests.post("https://api.sightengine.com/1.0/check.json",
                                  files={"media": fh},
                                  data={"models": "nudity-2.0", "api_user": key["api_user"],
                                        "api_secret": key["api_secret"]},
                                  timeout=30)
            d = r.json()
            if d.get("status") == "success":
                nud = d.get("nudity", {})
                cache_f.write_text(json.dumps({"score": _score_ponderado(nud), "nudity": nud},
                                              ensure_ascii=False), encoding="utf-8")
                return _score_ponderado(nud), "sightengine"
            err = str(d.get("error", "")).lower()
            if "usage" in err or "limit" in err or "quota" in err or r.status_code == 429:
                _mark_exhausted(key)
        except Exception:
            pass
    if _get_nudenet():
        return _score_nudenet(img_path), "nudenet"
    return None, None


def mancha_branca_frac(img_path):
    """3ª camada (V8): parte explícita apagada em branco pelo autor -> detectores não pegam.
    Fração da maior mancha branca grande, sem texto e longe da borda."""
    import cv2
    import numpy as np
    im = cv2.imread(str(img_path))
    if im is None:
        return 0.0
    h, w = im.shape[:2]
    gray = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
    _, wht = cv2.threshold(gray, 240, 255, cv2.THRESH_BINARY)
    wht = cv2.morphologyEx(wht, cv2.MORPH_OPEN, np.ones((7, 7), np.uint8))
    n, _lab, st, _ct = cv2.connectedComponentsWithStats(wht, 8)
    best = 0.0
    for i in range(1, n):
        x, y, ww, hh, area = st[i]
        frac = area / (w * h)
        if frac < 0.05 or frac > 0.40:
            continue
        if (gray[y:y + hh, x:x + ww] < 60).mean() > 0.015:
            continue
        if x <= 2 or y <= 2 or x + ww >= w - 2 or y + hh >= h - 2:
            continue
        best = max(best, frac)
    return best


# ─── Localização (onde) ──────────────────────────────────────────────────────
_QUAD = re.compile(r"\[\s*(\d+(?:\.\d+)?)\s*,\s*(\d+(?:\.\d+)?)\s*,\s*(\d+(?:\.\d+)?)\s*,\s*(\d+(?:\.\d+)?)\s*\]")


def _parse_caixas(resp, W, H):
    """Lê box_2d mesmo com JSON truncado (o Gemini às vezes não fecha a lista). Aceita os três formatos que o
    modelo devolve: [y,x,y,x]; o aninhado [[y,x,y,x]] (sem ler esse o cap 10 panel_027 saía INTACTO com
    "explicito":true — nudez frontal na versão postada); e várias caixas no mesmo campo [[...],[...]] (cap 3
    panel_020 original: só a 1ª era lida e o 2º mamilo ficava de fora)."""
    caixas = []
    for bloco in re.finditer(r'"box_2d"\s*:\s*([\[\]\d\s,.]+)', resp or ""):
        for m in _QUAD.finditer(bloco.group(1)):
            y0, x0, y1, x1 = (int(float(v)) for v in m.groups())
            if y1 <= y0 or x1 <= x0:
                continue
            caixas.append([int(x0 * W / 1000), int(y0 * H / 1000), int(x1 * W / 1000), int(y1 * H / 1000)])
    return caixas


def localizar_regioes(img_path):
    """Caixas [x0,y0,x1,y1] em pixels das partes explícitas.
    [] = o modelo julgou que NÃO é explícito; None = não consegui perguntar."""
    from PIL import Image
    h = _md5(img_path)
    cache_f = CACHE_DIR / f"{h}.{REGIOES_VER}.json"
    W, H = Image.open(img_path).size
    resp = None
    if cache_f.exists():
        try:
            resp = json.loads(cache_f.read_text(encoding="utf-8"))["resp"]
        except Exception:
            resp = None
    if resp is None:
        # 1º Gemini do proxy do Claude Code (rápido, caixas mais precisas, não gasta a cota das chaves);
        # 2º chaves diretas do gemini_llm.
        try:
            import claude_client
            resp = claude_client.gemini(PROMPT_REGIOES, [Path(img_path).read_bytes()],
                                        max_tokens=1024, temperature=0.2)
        except Exception:
            resp = None
        if not resp or "explicito" not in resp:
            try:
                import gemini_llm
                resp = gemini_llm.describe_image(Path(img_path).read_bytes(), PROMPT_REGIOES,
                                                 temperature=0.2, max_tokens=1024)
            except Exception:
                resp = None
        if not resp or "explicito" not in resp:
            return None
        cache_f.write_text(json.dumps({"resp": resp}, ensure_ascii=False), encoding="utf-8")
    if re.search(r'"explicito"\s*:\s*false', resp):
        return []
    # Explícito: se nenhuma caixa saiu legível (formato novo, JSON cortado, lista vazia), devolve
    # None = "não consegui localizar" -> fosco. NUNCA [] aqui: [] quer dizer "não é explícito" e
    # deixaria o painel intacto justamente quando o modelo disse que ele É explícito.
    return _parse_caixas(resp, W, H) or None


def localizar_silhuetas(img_path):
    """Caixas [x0,y0,x1,y1] (pixels) de silhueta branca fálica (ver PROMPT_SILHUETA). [] = não tem ou não consegui
    perguntar (sem resposta não grava cache: tenta de novo no próximo render; a análise do vídeo pronto pega depois)."""
    from PIL import Image
    cache_f = CACHE_DIR / f"{_md5(img_path)}.{SILHUETA_VER}.json"
    W, H = Image.open(img_path).size
    resp = None
    if cache_f.exists():
        try:
            resp = json.loads(cache_f.read_text(encoding="utf-8"))["resp"]
        except Exception:
            resp = None
    for tentativa in range(3 if resp is None else 0):  # proxy caiu (503/timeout em 19/10) -> chaves diretas -> de novo
        try:
            import claude_client
            resp = claude_client.gemini(PROMPT_SILHUETA, [Path(img_path).read_bytes()], max_tokens=600,
                                        temperature=0.1)
        except Exception:
            resp = None
        if not resp or '"tem"' not in resp:
            try:
                import gemini_llm
                resp = gemini_llm.describe_image(Path(img_path).read_bytes(), PROMPT_SILHUETA, temperature=0.1,
                                                 max_tokens=600)
            except Exception:
                resp = None
        if resp and '"tem"' in resp:
            cache_f.write_text(json.dumps({"resp": resp}, ensure_ascii=False), encoding="utf-8")
            break
        resp = None
        time.sleep(10 * (tentativa + 1))
    if resp is None:
        return []
    if re.search(r'"tem"\s*:\s*false', resp):
        return []
    caixas = _parse_caixas(resp, W, H)
    m = re.search(r'"regioes"\s*:\s*(\[.*)', resp, re.S)
    if not caixas and m:  # 19/10 (cap08 panel_074): veio "regioes":[[y0,x0,y1,x1]] sem o rótulo box_2d
        for q in _QUAD.finditer(m.group(1)):
            y0, x0, y1, x1 = (int(float(v)) for v in q.groups())
            if y1 > y0 and x1 > x0:
                caixas.append([int(x0 * W / 1000), int(y0 * H / 1000), int(x1 * W / 1000), int(y1 * H / 1000)])
    return caixas


def apagar_silhuetas(img_in, img_out, caixas):
    """Apaga o branco das silhuetas (inpaint com as cores de volta) dentro das caixas, sem tocar nos balões.
    Mosaico por cima de branco puro continua mostrando o contorno — por isso some primeiro. Devolve quantas apagou."""
    import cv2
    import numpy as np
    bgr = cv2.imread(str(img_in))
    H, W = bgr.shape[:2]
    baloes = _mascara_baloes(bgr)
    n = 0
    for x0, y0, x1, y1 in caixas:
        mx, my = int((x1 - x0) * 0.15), int((y1 - y0) * 0.15)
        x0, y0, x1, y1 = max(0, x0 - mx), max(0, y0 - my), min(W, x1 + mx), min(H, y1 + my)
        roi = bgr[y0:y1, x0:x1]
        branco = (np.all(roi >= BRANCO_MIN, axis=2) & (baloes[y0:y1, x0:x1] == 0)).astype(np.uint8) * 255
        if branco.mean() / 255 < BRANCO_FRAC_MIN:
            continue
        branco = cv2.dilate(branco, np.ones((15, 15), np.uint8))
        bgr[y0:y1, x0:x1] = cv2.inpaint(roi, branco, 9, cv2.INPAINT_TELEA)
        n += 1
    cv2.imwrite(str(img_out), bgr, [cv2.IMWRITE_JPEG_QUALITY, 92])
    return n


# ─── Aplicação na imagem ─────────────────────────────────────────────────────
def _mascara_baloes(bgr):
    """Balões de fala: mancha branca fechada (não encosta na borda), não enorme, e por dentro só
    branco + texto preto. O fundo branco da página (encosta na borda, tem personagem dentro) e
    fluido/brilho (sem texto) NÃO entram — senão a parte explícita escaparia da censura."""
    import cv2
    import numpy as np
    H, W = bgr.shape[:2]
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    # sem morfologia aqui: fechar buracos "atravessa" o contorno fino do balão e o funde com o
    # fundo da página (que encosta na borda e é descartado) -> balão ficava com mosaico
    _, wht = cv2.threshold(gray, 235, 255, cv2.THRESH_BINARY)
    n, lab, st, _ct = cv2.connectedComponentsWithStats(wht, 4)
    mask = np.zeros((H, W), np.uint8)
    contorno = np.ones((max(3, W // 90) | 1,) * 2, np.uint8)
    for i in range(1, n):
        x, y, ww, hh, area = st[i]
        if area < 0.004 * W * H or x <= 1 or y <= 1 or x + ww >= W - 1 or y + hh >= H - 1:
            continue
        comp = (lab == i).astype(np.uint8) * 255
        cnts, _ = cv2.findContours(comp, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cheio = np.zeros((H, W), np.uint8)
        cv2.drawContours(cheio, cnts, -1, 255, -1)  # fecha os buracos das letras
        dentro = gray[cheio > 0]
        if dentro.size > 0.30 * W * H:
            continue
        escuro = (dentro < 80).mean()
        meio = ((dentro >= 80) & (dentro <= 235)).mean()
        if escuro < 0.01 or meio > 0.12:  # sem texto, ou tem arte colorida dentro
            continue
        mask |= cv2.dilate(cheio, contorno)  # inclui o contorno preto do balão
    return mask


# Enquadrar numa parte limpa só vale se sobrar painel de verdade: abaixo disto o recorte vira um
# detalhe sem contexto e é melhor o mosaico. Medido no cache de regiões: 73% dos painéis com +18
# têm 70% ou mais da área limpa, então a maioria passa com folga.
MIN_LADO_RECORTE = float(os.environ.get("CENSURA_MIN_LADO_RECORTE", "0.45"))


def recorte_limpo(img_path, caixas, margem=0.02):
    """(x, y, w, h) do maior pedaço do painel que NÃO toca nenhuma região +18, ou None.

    Trabalha em faixas: corta por cima, por baixo, pela esquerda ou pela direita das caixas, e fica
    com a faixa de maior área. É simples de propósito — faixa é o que a câmera do 2.5D sabe
    enquadrar, e recorte em L ficaria com a cena explícita na borda.

    `caixas` vem de localizar_regioes (já em pixels). Devolve None quando o que sobra é estreito
    demais (MIN_LADO_RECORTE do lado original)."""
    import cv2
    img = cv2.imread(str(img_path))
    if img is None or not caixas:
        return None
    H, W = img.shape[:2]
    mx, my = int(W * margem), int(H * margem)
    x0 = max(0, min(c[0] for c in caixas) - mx)
    y0 = max(0, min(c[1] for c in caixas) - my)
    x1 = min(W, max(c[2] for c in caixas) + mx)
    y1 = min(H, max(c[3] for c in caixas) + my)

    faixas = [
        ("acima",   (0, 0, W, y0)),
        ("abaixo",  (0, y1, W, H - y1)),
        ("esquerda", (0, 0, x0, H)),
        ("direita", (x1, 0, W - x1, H)),
    ]
    melhor, area_melhor = None, 0
    for _nome, (x, y, w, h) in faixas:
        if w < W * MIN_LADO_RECORTE or h < H * MIN_LADO_RECORTE:
            continue
        if w * h > area_melhor:
            melhor, area_melhor = (x, y, w, h), w * h
    return melhor


def _baloes_cortados(img_path, recorte):
    """True se o recorte cortaria um balão de fala pela metade (o público perderia a fala)."""
    try:
        import fx_parallax
        # baloes() devolve {"frac": ..., "caixas": [...]}, não a lista direto
        caixas = (fx_parallax.baloes(img_path) or {}).get("caixas") or []
    except Exception:  # noqa: BLE001 — sem detector de balão, não barra o recorte
        return False
    x, y, w, h = recorte
    for bx0, by0, bx1, by1 in caixas:
        dentro_x = bx0 >= x and bx1 <= x + w
        dentro_y = by0 >= y and by1 <= y + h
        fora = bx1 <= x or bx0 >= x + w or by1 <= y or by0 >= y + h
        if not (fora or (dentro_x and dentro_y)):
            return True      # encosta na borda: ficaria cortado
    return False


def censurar_recortando(img_in, img_out, caixas):
    """Grava o painel ENQUADRADO numa parte limpa. True se deu; False pra cair no mosaico."""
    import cv2
    rec = recorte_limpo(img_in, caixas)
    if not rec or _baloes_cortados(img_in, rec):
        return False
    img = cv2.imread(str(img_in))
    if img is None:
        return False
    x, y, w, h = rec
    cv2.imwrite(str(img_out), img[y:y + h, x:x + w])
    return True


def censurar_localizado(img_in, img_out, caixas):
    """Mosaico só dentro das caixas (bordas suaves). Retorna fração do painel coberta."""
    import cv2
    import numpy as np
    bgr = cv2.imread(str(img_in))
    H, W = bgr.shape[:2]
    mask = np.zeros((H, W), np.uint8)
    # folga generosa: a caixa do Gemini costuma vir justa e deixar virilha/fluido ao lado à mostra
    pad = int(W * 0.03)
    for x0, y0, x1, y1 in caixas:
        ex, ey = int((x1 - x0) * 0.22) + pad, int((y1 - y0) * 0.22) + pad
        # caixa minúscula (mamilo marcado sozinho num painel grande): 22% dela não cobre nada.
        # Piso de 6% da largura, só nesse caso, pra virar uma mancha de verdade.
        if (x1 - x0) * (y1 - y0) < 0.02 * W * H:
            ex, ey = max(ex, int(W * 0.06)), max(ey, int(W * 0.06))
        cv2.rectangle(mask, (max(0, x0 - ex), max(0, y0 - ey)),
                      (min(W - 1, x1 + ex), min(H - 1, y1 + ey)), 255, -1)
    mask[_mascara_baloes(bgr) > 0] = 0
    frac = float((mask > 0).mean())
    bloco = max(12, W // 24)
    peq = cv2.resize(bgr, (max(1, W // bloco), max(1, H // bloco)), interpolation=cv2.INTER_AREA)
    mosaico = cv2.resize(peq, (W, H), interpolation=cv2.INTER_NEAREST)
    mosaico = cv2.GaussianBlur(mosaico, (0, 0), bloco * 0.25)
    k = max(3, (W // 40) | 1)
    m = cv2.GaussianBlur(mask, (k, k), 0).astype(np.float32)[..., None] / 255.0
    res = (bgr.astype(np.float32) * (1 - m) + mosaico.astype(np.float32) * m).astype(np.uint8)
    cv2.imwrite(str(img_out), res, [cv2.IMWRITE_JPEG_QUALITY, 92])
    return frac


# Versionamento das censuras: config/censuras.json diz qual receita está em uso e guarda o que já
# foi aprovado e o que já foi vetado. Ideia do dono em 16/10: "tem que ter uma espécie de
# versionamento de censuras, assim não ficamos dando voltas".
_CENSURAS = None


def _receita(chave, padrao=None):
    """Parâmetros da receita em uso para a chave pedida ('com_localizacao', 'fosco_medio',
    'fosco_forte'...). Se a chave não estiver em 'em_uso', procura uma receita com esse nome."""
    global _CENSURAS
    if _CENSURAS is None:
        try:
            _CENSURAS = json.loads((PROJECT_DIR / "config" / "censuras.json").read_text(encoding="utf-8"))
        except (OSError, ValueError):
            _CENSURAS = {}
    nome = (_CENSURAS.get("em_uso") or {}).get(chave, chave)
    rec = (_CENSURAS.get("receitas") or {}).get(nome) or {}
    return rec.get("parametros") or (padrao or {})


def _mascara_nitida(orig):
    """Máscara do que volta NÍTIDO por cima da censura: balões com texto + branco que encosta na
    borda do painel (margem da página). Mancha branca solta no meio NÃO volta."""
    import cv2
    gray = cv2.cvtColor(orig, cv2.COLOR_BGR2GRAY)
    _, wht = cv2.threshold(gray, 240, 255, cv2.THRESH_BINARY)
    n, lab, st, _ct = cv2.connectedComponentsWithStats(wht, 8)
    H, W = gray.shape
    keep = _mascara_baloes(orig)
    for i in range(1, n):
        x, y, ww, hh, _a = st[i]
        if x <= 1 or y <= 1 or x + ww >= W - 1 or y + hh >= H - 1:
            keep[lab == i] = 255
    return keep


def censurar_fosco(img_in, img_out):
    """Mosaico COLORIDO do painel inteiro, com um borrão por cima; balões nítidos recolocados.
    Receita `fosco_painel_v1` (config/censuras.json). NÍVEL ÚNICO.

    Só entra em painel que a localização não cobriu — ou porque não veio caixa nenhuma, ou porque
    as caixas comprovadamente não deram conta. Quando há localização utilizável, quem manda é o
    mosaico localizado, que é o que o dono aprovou ("as que você usa mosaico localizado estão
    ótimas").

    Entrou no lugar do "Exodia fosco" (negativo + pixelão + cinza + véu branco + borrão 251), que o
    dono aposentou em 16/10: *"a ideia é só não usar o blur total como tem usado"*. Medido no mesmo
    dia no painel 100 do cap 3: o negativo não mudava nada no resultado final, só o borrão
    trabalhava, e o painel virava mancha.

    Vetado, não propor de novo (está tudo em config/censuras.json): cinza ("nada de cinza"), tarja
    preta, bloco grande com interpolação dura ("o moço ficou parecendo um peixe") — por isso a
    ampliação é INTER_LINEAR e não INTER_NEAREST — e um segundo nível mais forte (blocos 90 /
    borrão 95), que o dono viu em 16/10 e recusou: *"o N3 certeza é quase blur total, não dá pra
    manter só no anterior?"*."""
    import cv2
    import numpy as np
    orig = cv2.imread(str(img_in))
    if orig is None:
        return
    H, W = orig.shape[:2]
    r = _receita("fosco_painel", {"blocos": 55, "blur_kernel": 45})
    blocos = int(r.get("blocos", 55))
    k = int(r.get("blur_kernel", 45))
    peq = cv2.resize(orig, (max(3, W // blocos), max(3, H // blocos)), interpolation=cv2.INTER_AREA)
    px = cv2.resize(peq, (W, H), interpolation=cv2.INTER_LINEAR)
    if k >= 3:
        px = cv2.GaussianBlur(px, (k | 1, k | 1), 0)
    m = cv2.GaussianBlur(_mascara_nitida(orig), (15, 15), 0).astype(np.float32)[..., None] / 255.0
    res = (orig.astype(np.float32) * m + px.astype(np.float32) * (1 - m)).astype(np.uint8)
    cv2.imwrite(str(img_out), res, [cv2.IMWRITE_JPEG_QUALITY, 92])


def censurar_fosco_exodia(img_in, img_out):
    """APOSENTADA em 16/10 — mantida só para comparar (ver config/censuras.json).

    Exodia fosco da V8: fundo negativo/pixelado/cinza/branco +
    GaussianBlur forte, balões da arte original recolocados nítidos por cima."""
    import cv2
    import numpy as np
    fc = ("[0:v]split=2[bg][fg];"
          "[bg]negate,scale=iw/25:-1,scale=iw*25:-1:flags=neighbor,hue=s=0,"
          "noise=alls=60:allf=t+u:all_seed=42,drawbox=x=0:y=0:w=iw:h=ih:color=white@0.7:t=fill[bgt];"
          "[fg]lumakey=threshold=0.85:tolerance=0.20:softness=0.10[bal];[bgt][bal]overlay")
    tmp_ex = str(img_out) + ".ex.jpg"
    subprocess.run([_ffmpeg(), "-y", "-i", str(img_in), "-filter_complex", fc, "-q:v", "2", tmp_ex],
                   check=True, capture_output=True, timeout=60)
    orig = cv2.imread(str(img_in))
    ex = cv2.resize(cv2.imread(tmp_ex), (orig.shape[1], orig.shape[0]))
    Path(tmp_ex).unlink(missing_ok=True)
    fosco = cv2.GaussianBlur(ex, (251, 251), 0)
    # nítido por cima: balões com texto + branco da página (encosta na borda). Mancha branca
    # no meio do painel (fluido/brilho) NÃO volta nítida.
    gray = cv2.cvtColor(orig, cv2.COLOR_BGR2GRAY)
    _, wht = cv2.threshold(gray, 240, 255, cv2.THRESH_BINARY)
    n, lab, st, _ct = cv2.connectedComponentsWithStats(wht, 8)
    H, W = gray.shape
    keep = _mascara_baloes(orig)
    for i in range(1, n):
        x, y, ww, hh, _a = st[i]
        if x <= 1 or y <= 1 or x + ww >= W - 1 or y + hh >= H - 1:
            keep[lab == i] = 255
    m = cv2.GaussianBlur(keep, (15, 15), 0).astype(np.float32)[..., None] / 255.0
    res = (orig.astype(np.float32) * m + fosco.astype(np.float32) * (1 - m)).astype(np.uint8)
    cv2.imwrite(str(img_out), res, [cv2.IMWRITE_JPEG_QUALITY, 92])


def censurar_branco(img_in, img_out):
    """Censura especial (V8, variante B2 aprovada): mancha branca genital -> inpaint + escurece."""
    import cv2
    import numpy as np
    im = cv2.imread(str(img_in))
    H, W = im.shape[:2]
    gray = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
    _, wht = cv2.threshold(gray, 240, 255, cv2.THRESH_BINARY)
    wht = cv2.morphologyEx(wht, cv2.MORPH_OPEN, np.ones((7, 7), np.uint8))
    n, lab, st, _ct = cv2.connectedComponentsWithStats(wht, 8)
    mask = np.zeros((H, W), np.uint8)
    for i in range(1, n):
        x, y, ww, hh, area = st[i]
        if not 0.05 <= area / (W * H) <= 0.40:
            continue
        if (gray[y:y + hh, x:x + ww] < 60).mean() > 0.015:
            continue
        if x <= 2 or y <= 2 or x + ww >= W - 2 or y + hh >= H - 2:
            continue
        mask[lab == i] = 255
    if not mask.any():
        return False
    mask = cv2.dilate(mask, np.ones((9, 9), np.uint8), iterations=2)
    m3 = cv2.merge([mask, mask, mask]) / 255.0
    b = cv2.inpaint(im, mask, 9, cv2.INPAINT_NS)
    out = (b * (1 - m3) + (b * 0.55) * m3).astype(np.uint8)
    cv2.imwrite(str(img_out), out, [cv2.IMWRITE_JPEG_QUALITY, 92])
    return True


# ─── reforço depois da advertência do YouTube (16/10) ────────────────────────
# O canal pt levou advertência ("Nudez e conteúdo sexual") por painéis que saíram sem censura ou com mosaico no
# lugar errado. Três reforços, todos com a MESMA pergunta da análise do vídeo pronto (revisao_video.exposto:
# "tem mamilo/genitália/nádegas à mostra, sem mosaico ou com mosaico fraco?"):
#   1. reforcar_scores: painel que o Sightengine deixou abaixo da dúvida mas a visão vê parte exposta entra na
#      censura (cap 3 panel_048: corpo inteiro nu, score 0,16, nunca era olhado);
#   2. conferência do mosaico: a imagem JÁ censurada é perguntada de novo; se ainda aparece, vira fosco (cap 3
#      panel_054 original: o Gemini pôs as caixas longe dos mamilos, score 0,69, saía "local" com tudo à mostra);
#   3. segunda opinião quando a localização diz "não explícito" e a pergunta diz que tem parte exposta: fosco.
# E a lista de painéis FORÇADOS: o que a análise do vídeo pronto reprovou sai em fosco na próxima renderização.
FORCADOS = CACHE_DIR / "_forcar_fosco.json"  # md5 do painel -> {"painel", "motivo", "em"}


def _forcados():
    try:
        return json.loads(FORCADOS.read_text(encoding="utf-8"))
    except Exception:
        return {}


def forcar_fosco(img_path, motivo=""):
    """Marca o painel pra sair em fosco em toda renderização daqui pra frente (pt, línguas, 16:9)."""
    d = _forcados()
    d[_md5(img_path)] = {"painel": str(img_path), "motivo": motivo, "em": time.strftime("%Y-%m-%d %H:%M")}
    FORCADOS.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")


def forcado(img_path):
    return _md5(img_path) in _forcados()


def _visao_exposto(img_path):
    """True só se a visão afirma parte exposta. Sem resposta = False aqui: quem barra no escuro é a análise do
    vídeo pronto (que reprova "incompleto")."""
    try:
        import revisao_video
        return revisao_video.exposto(img_path) is True
    except Exception:
        return False


def reforcar_scores(paineis, scores):
    """Scores com o reforço 1 e os forçados: painel abaixo de LIMIAR_DUVIDA que a visão vê exposto sobe pra
    LIMIAR_DUVIDA (entra na censura; a localização e a conferência decidem como cobrir); forçado sobe pra
    LIMIAR_NSFW. Devolve (scores novos, índices que subiram)."""
    novos, subiram = list(scores), []
    baixos = [k for k, s in enumerate(scores) if (s or 0.0) < LIMIAR_DUVIDA]
    try:
        import revisao_video
        vis = revisao_video.expostos([paineis[k] for k in baixos])
    except Exception:
        vis = {}
    for k in baixos:
        if vis.get(paineis[k]) is True:
            novos[k] = LIMIAR_DUVIDA
            subiram.append(k)
    for k, p in enumerate(paineis):
        if forcado(p) and (novos[k] or 0.0) < LIMIAR_NSFW:
            novos[k] = LIMIAR_NSFW
            if k not in subiram:
                subiram.append(k)
    return novos, sorted(subiram)


def censurar_imagem(img_in, img_out, score, tipo=None, texto_nsfw=None):
    """Gera img_out censurada. Retorna (nivel, detalhe): nivel in intacto|local|fosco|branco.
    texto_nsfw: a narração também indica +18? Desempata quando o Sightengine dá score forte e a
    visão do Gemini diz que não é explícito (o Sightengine erra bastante em manhwa).
    Painel com risco passa antes pela SILHUETA BRANCA (19/10): o branco dela é apagado e qualquer caminho (local,
    fosco, forçado, branco) trabalha sobre a imagem já sem a silhueta; a área dela sai sempre com mosaico."""
    forcar = forcado(img_in)  # pelo md5 do painel ORIGINAL (a imagem sem silhueta tem outro md5)
    risco = forcar or tipo == "branco" or (score is not None and score >= LIMIAR_DUVIDA)
    sil = localizar_silhuetas(img_in) if risco else []
    if not sil:
        return _censurar(img_in, img_out, score, tipo, texto_nsfw, forcar)
    base = Path(str(img_out) + ".sem_silhueta.jpg")
    try:
        apagadas = apagar_silhuetas(img_in, base, sil)
        nivel, det = _censurar(base, img_out, score, tipo, texto_nsfw, forcar)
        if nivel in ("intacto", "local", "recorte"):
            censurar_localizado(base if nivel == "intacto" else img_out, img_out, sil)
            nivel = "local" if nivel == "intacto" else nivel
        return nivel, (f"{det}; " if det else "") + f"silhueta branca: {len(sil)} caixa(s), {apagadas} apagada(s)"
    finally:
        base.unlink(missing_ok=True)


def _censurar(img_in, img_out, score, tipo, texto_nsfw, forcar):
    if forcar:
        censurar_fosco(img_in, img_out)
        return "fosco", "forçado: a análise do vídeo pronto achou nudez neste painel"
    if tipo == "branco" and censurar_branco(img_in, img_out):
        return "branco", ""
    if score is None or score < LIMIAR_DUVIDA:
        return "intacto", ""
    caixas = localizar_regioes(img_in)
    if caixas:
        # 1ª escolha: não mostrar, em vez de cobrir. Se sobra painel limpo que não corta balão, a
        # câmera enquadra ali e a arte aparece inteira — ideia do dono em 16/10, melhor que borrão.
        # DESLIGADO por padrão (CENSURA_RECORTE=1 liga). Testado em 16/10 nos painéis 086, 066 e
        # 007 do cap 3: o recorte saiu COM nudez visível nos três. A ideia é boa, mas depende de a
        # localização marcar TODAS as áreas +18, e ela marca só a que o modelo aponta — o resto do
        # corpo nu fica fora das caixas e entra no recorte. Só religar depois que a detecção
        # cobrir o corpo inteiro, e conferindo painel a painel na imagem.
        if os.environ.get("CENSURA_RECORTE", "0") == "1" and censurar_recortando(img_in, img_out, caixas):
            return "recorte", "enquadrado na parte limpa do painel"
        frac = censurar_localizado(img_in, img_out, caixas)
        if frac > MAX_FRAC_LOCAL:
            censurar_fosco(img_in, img_out)
            return "fosco", f"regiões cobriam {frac:.0%} do painel"
        if frac < MIN_FRAC_LOCAL and score >= LIMIAR_NSFW:
            # nudez forte com mosaico quase invisível: o modelo marcou só um pedaço
            censurar_fosco(img_in, img_out)
            return "fosco", f"mosaico cobria só {frac:.1%} com score {score:.2f}"
        if score >= SCORE_CENA_INTEIRA and frac < FRAC_EXIGIDA_SCORE_ALTO:
            # Score muito alto é cena sexual inteira, não "um pedaço a cobrir": tapar 2 ou 3 caixas
            # deixa o resto do quadro contando a mesma história. Medido no cap 3 em 16/10: o painel
            # 100 (score 1,73, 3 caixas, 21% do painel) passou como mosaico e a análise do vídeo
            # pronto reprovou o capítulo em 3 quadros dele — pernas e posição à mostra em volta do
            # mosaico. Mesmo caso nos painéis de score 1,67/24%, 1,39/10% e 1,38/16%.
            # Continua valendo a ordem da dona (mosaico primeiro): isto só pega score alto E
            # cobertura pequena, ou seja, quando o mosaico comprovadamente não dá conta.
            censurar_fosco(img_in, img_out)
            return "fosco", f"cena inteira: score {score:.2f} com mosaico de só {frac:.0%}"
        if _visao_exposto(img_out):  # reforço 2: o mosaico ficou no lugar errado ou fraco
            censurar_fosco(img_in, img_out)
            return "fosco", f"conferência: ainda aparecia com o mosaico de {frac:.0%}"
        return "local", f"{len(caixas)} região(ões), {frac:.0%} do painel"
    if caixas == [] and (score < LIMIAR_NSFW or texto_nsfw is False):
        if _visao_exposto(img_in):  # reforço 3: a localização liberou, a pergunta direta não
            censurar_fosco(img_in, img_out)
            return "fosco", "localização disse não explícito, conferência viu parte exposta"
        return "intacto", "visão julgou não explícito"
    censurar_fosco(img_in, img_out)
    return "fosco", "sem localização" if caixas is None else "score forte, narração +18 e sem região"
