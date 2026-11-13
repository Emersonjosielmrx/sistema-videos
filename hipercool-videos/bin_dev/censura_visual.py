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
LIMIAR_DUVIDA = float(os.environ.get("CENSURA_LIMIAR_DUVIDA", "0.45"))
LIMIAR_NSFW = float(os.environ.get("CENSURA_LIMIAR_NSFW", "1.15"))
# Acima dessa fração do painel coberta por caixas, o mosaico local vira o painel todo -> fosco.
MAX_FRAC_LOCAL = float(os.environ.get("CENSURA_MAX_FRAC_LOCAL", "0.80"))

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
def _parse_caixas(resp, W, H):
    """Lê box_2d mesmo com JSON truncado (o Gemini às vezes não fecha a lista)."""
    caixas = []
    for m in re.finditer(r'"box_2d"\s*:\s*\[\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\]', resp or ""):
        y0, x0, y1, x1 = (int(v) for v in m.groups())
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
    return _parse_caixas(resp, W, H)


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


def censurar_fosco(img_in, img_out):
    """Exodia fosco da V8 (aprovado pela usuária): fundo negativo/pixelado/cinza/branco +
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


def censurar_imagem(img_in, img_out, score, tipo=None, texto_nsfw=None):
    """Gera img_out censurada. Retorna (nivel, detalhe): nivel in intacto|local|fosco|branco.
    texto_nsfw: a narração também indica +18? Desempata quando o Sightengine dá score forte e a
    visão do Gemini diz que não é explícito (o Sightengine erra bastante em manhwa)."""
    if tipo == "branco" and censurar_branco(img_in, img_out):
        return "branco", ""
    if score is None or score < LIMIAR_DUVIDA:
        return "intacto", ""
    caixas = localizar_regioes(img_in)
    if caixas:
        frac = censurar_localizado(img_in, img_out, caixas)
        if frac <= MAX_FRAC_LOCAL:
            return "local", f"{len(caixas)} região(ões), {frac:.0%} do painel"
        censurar_fosco(img_in, img_out)
        return "fosco", f"regiões cobriam {frac:.0%} do painel"
    if caixas == [] and (score < LIMIAR_NSFW or texto_nsfw is False):
        return "intacto", "visão julgou não explícito"
    censurar_fosco(img_in, img_out)
    return "fosco", "sem localização" if caixas is None else "score forte, narração +18 e sem região"
