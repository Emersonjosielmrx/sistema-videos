"""censura_visual.py — censura +18 por VISÃO (não keyword), na IMAGEM do painel.

Arquitetura HÍBRIDA (decidida com a usuária 2026-06-30):
- DETECTOR: Sightengine API (nudity-2.0) — score confiável, acerta arte de manhwa.
  Roteador de chaves (free tier 2000/mês, 500/dia por conta) + cache por md5.
- LOCALIZADOR: NudeNet local (grátis, dá bounding box) — usado p/ censura cirúrgica
  QUANDO acha box. É fraco em manhwa, então é só reforço.
- 3 NÍVEIS por score (ideia da usuária — manchar mesmo em dúvida p/ enganar algoritmo YT):
    score < LIMIAR_DUVIDA      -> imagem intacta (normal)
    LIMIAR_DUVIDA..LIMIAR_NSFW -> shift de cor/blur LEVE (engana detector YT, não destrói)
    score >= LIMIAR_NSFW       -> mosaico FORTE (box do NudeNet se houver, senão zona preventiva)

Fallback total: API/modelo falhou -> retorna None/original, pipeline não quebra.
Cache: workspace/censura_cache/<md5>.json (score) — nunca re-chama Sightengine à toa.
"""
import json
import os
import shutil
import hashlib
import subprocess
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent


def _ffmpeg():
    """Resolve o binário ffmpeg de forma robusta: PATH → WinGet (glob) → fallback 'ffmpeg'."""
    f = shutil.which("ffmpeg")
    if f:
        return f
    import glob as _g
    for pat in (str(Path(os.environ.get("LOCALAPPDATA", "")) / "Microsoft/WinGet/**/ffmpeg.exe"),
                "C:/Users/*/AppData/Local/Microsoft/WinGet/**/ffmpeg.exe"):
        hits = _g.glob(pat, recursive=True)
        if hits:
            return hits[0]
    return "ffmpeg"


def _ffprobe():
    f = shutil.which("ffprobe")
    if f:
        return f
    import glob as _g
    for pat in (str(Path(os.environ.get("LOCALAPPDATA", "")) / "Microsoft/WinGet/**/ffprobe.exe"),
                "C:/Users/*/AppData/Local/Microsoft/WinGet/**/ffprobe.exe"):
        hits = _g.glob(pat, recursive=True)
        if hits:
            return hits[0]
    return "ffprobe"
SECRETS = PROJECT_DIR / "secrets" / "sightengine.json"
CACHE_DIR = PROJECT_DIR / "workspace" / "censura_cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

# Limiares de score ponderado (activity*2 + display*1.2 + suggestive*0.8). Calibráveis por env.
LIMIAR_DUVIDA = float(os.environ.get("CENSURA_LIMIAR_DUVIDA", "0.45"))
LIMIAR_NSFW = float(os.environ.get("CENSURA_LIMIAR_NSFW", "1.15"))

_keys_data = None
_nudenet = None


# ─── Roteador de chaves Sightengine ──────────────────────────────────────────
def _load_keys():
    global _keys_data
    if _keys_data is None:
        try:
            _keys_data = json.loads(SECRETS.read_text(encoding="utf-8"))
        except Exception:
            _keys_data = {"keys": []}
    return _keys_data


def _pick_key():
    """Retorna a 1a chave 'available'. Roteia quando uma esgota (HTTP 429/quota)."""
    for k in _load_keys().get("keys", []):
        if k.get("status") == "available":
            return k
    return None


def _mark_exhausted(key):
    import time
    key["status"] = "exhausted"
    key["used_at"] = time.strftime("%Y-%m-%d")
    try:
        SECRETS.write_text(json.dumps(_keys_data, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass


# ─── Detecção via Sightengine (com cache por md5) ────────────────────────────
def _score_ponderado(nud):
    """Score composto de nudez EXPLÍCITA (0..~2). Só os sinais que indicam
    nudez real: sexual_activity, sexual_display e erotica.
    IMPORTANTE: NÃO usa 'suggestive' nem '1 - none'. Causa raiz da queixa da
    usuária (2026-07-02): 'suggestive' do Sightengine dispara com QUALQUER
    personagem feminina vestida/atraente em manhwa (violão, notebook, amiga),
    e ele também DERRUBA o 'none', então tanto o termo suggestive quanto o
    '1 - none' inflavam o score e tarjavam cenas sem nudez nenhuma.
    'erotica' já pega o nu ESTÁTICO (peito/nu à mostra sem ato), que era o
    motivo original de usar 1-none — então não perdemos esse caso.
    ⚠️ NÃO reintroduza 'suggestive' nem '1-none' aqui sem manual override."""
    return (nud.get("sexual_activity", 0) * 2.0
            + nud.get("sexual_display", 0) * 1.5
            + nud.get("erotica", 0) * 1.2)


def detectar_score(img_path):
    """Retorna (score, nudity_dict) via Sightengine, cacheado por md5. None se indisponível."""
    try:
        img_bytes = Path(img_path).read_bytes()
    except Exception:
        return None
    h = hashlib.md5(img_bytes).hexdigest()
    cache_f = CACHE_DIR / f"{h}.json"
    if cache_f.exists():
        try:
            d = json.loads(cache_f.read_text(encoding="utf-8"))
            nud = d.get("nudity", {})
            score = _score_ponderado(nud) if nud else d.get("score", 0.0)
            return score, nud
        except Exception:
            pass
    key = _pick_key()
    if not key:
        return None
    try:
        import requests
    except Exception:
        return None
    try:
        r = requests.post(
            "https://api.sightengine.com/1.0/check.json",
            files={"media": open(img_path, "rb")},
            data={"models": "nudity-2.0",
                  "api_user": key["api_user"], "api_secret": key["api_secret"]},
            timeout=30)
        d = r.json()
        if d.get("status") != "success":
            err = str(d.get("error", "")).lower()
            if "usage" in err or "limit" in err or "quota" in err or r.status_code == 429:
                _mark_exhausted(key)
            return None
        nud = d.get("nudity", {})
        score = _score_ponderado(nud)
        cache_f.write_text(json.dumps({"score": score, "nudity": nud}, ensure_ascii=False), encoding="utf-8")
        return score, nud
    except Exception:
        return None


# ─── Localizador de região via NudeNet (grátis, box) ─────────────────────────
def _get_nudenet():
    global _nudenet
    if _nudenet is None:
        try:
            from nudenet import NudeDetector
            _nudenet = NudeDetector()
        except Exception:
            _nudenet = False
    return _nudenet


def detectar_boxes(img_path):
    """Retorna lista de boxes [x,y,w,h] de partes expostas (NudeNet). [] se nada/indisponível."""
    det = _get_nudenet()
    if not det:
        return []
    try:
        res = det.detect(str(img_path))
    except Exception:
        return []
    boxes = []
    for d in res:
        cls = d.get("class", "")
        if "EXPOSED" in cls or "GENITALIA" in cls or "BREAST" in cls or "BUTTOCKS" in cls:
            b = d.get("box")
            if b and len(b) == 4:
                boxes.append([int(b[0]), int(b[1]), int(b[2]), int(b[3])])  # x,y,w,h
    return boxes


def detectar_rostos(img_path):
    """Detecta rostos via OpenCV haar cascade + NudeNet FACE. Usado p/ censura localizada
    (negativo/névoa) só no rosto — como na referência 4.jpg da usuária. [] se nada."""
    boxes = []
    # NudeNet FACE (pega rostos de anime/manhwa bem)
    det = _get_nudenet()
    if det:
        try:
            for d in det.detect(str(img_path)):
                if "FACE" in d.get("class", ""):
                    b = d.get("box")
                    if b and len(b) == 4:
                        boxes.append([int(b[0]), int(b[1]), int(b[2]), int(b[3])])
        except Exception:
            pass
    # OpenCV haar como reforço
    try:
        import cv2
        img = cv2.imread(str(img_path))
        if img is not None:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            casc = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
            faces = casc.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=4, minSize=(40, 40))
            for (x, y, w, h) in faces:
                boxes.append([int(x), int(y), int(w), int(h)])
    except Exception:
        pass
    return boxes


def _negativo_pele(img_in, img_out, white=0.18):
    try:
        import cv2, numpy as np
    except Exception:
        return False
    bgr = cv2.imread(str(img_in))
    if bgr is None:
        return False
    H, W = bgr.shape[:2]
    ycrcb = cv2.cvtColor(bgr, cv2.COLOR_BGR2YCrCb)
    m = cv2.inRange(ycrcb, np.array([0, 133, 77], np.uint8), np.array([255, 180, 127], np.uint8))
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    m2 = cv2.inRange(hsv, np.array([0, 20, 70], np.uint8), np.array([25, 255, 255], np.uint8))
    m = cv2.bitwise_or(m, m2)
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((7, 7), np.uint8))
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))

    if os.environ.get("NEG_PROTECT_FACE", "1").strip() not in ("0", "false", "no"):
        try:
            for (fx, fy, fw, fh) in (detectar_rostos(img_in) or []):
                ex = int(fw * 0.35); up = int(fh * 1.2); down = int(fh * 0.15)
                x0 = max(0, fx - ex); x1 = min(W, fx + fw + ex)
                y0 = max(0, fy - up);  y1 = min(H, fy + fh + down)
                m[y0:y1, x0:x1] = 0
        except Exception:
            pass

    m = (cv2.GaussianBlur(m, (9, 9), 0).astype(np.float32) / 255.0)
    m3 = cv2.merge([m, m, m])
    neg = (255 - bgr).astype(np.float32)
    mean_lum = float(cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY).mean())
    fog_val = int(max(60, min(235, mean_lum * 0.55 + 90)))
    fog_color = np.full_like(bgr, fog_val)
    fog = cv2.addWeighted(bgr, 1 - white, fog_color, white, 0).astype(np.float32)
    res = fog * (1 - m3) + neg * m3
    return bool(cv2.imwrite(str(img_out), res.astype(np.uint8)))


def _expand(box, W, H, pct=0.30):
    x, y, w, h = box
    mw, mh = w * pct, h * pct
    nx = max(0, int(x - mw)); ny = max(0, int(y - mh))
    nw = int(w + mw * 2); nh = int(h + mh * 2)
    if nx + nw > W: nw = W - nx
    if ny + nh > H: nh = H - ny
    return [nx, ny, nw, nh]


# ─── Aplicação na IMAGEM (3 níveis) ──────────────────────────────────────────
def _img_dims(img_path):
    try:
        r = subprocess.run([_ffprobe(), "-v", "quiet", "-select_streams", "v:0",
                            "-show_entries", "stream=width,height", "-of", "csv=p=0", str(img_path)],
                           capture_output=True, text=True, timeout=10)
        w, h = r.stdout.strip().split(",")[:2]
        return int(w), int(h)
    except Exception:
        return 1000, 1500


def censurar_imagem(img_in, img_out, score, boxes=None, modo="hibrido"):
    """Gera img_out censurada conforme nível do score. Retorna nível aplicado."""
    W, H = _img_dims(img_in)
    boxes = boxes or []
    nivel = "intacto"
    if score >= LIMIAR_NSFW:
        nivel = "forte"
    elif score >= LIMIAR_DUVIDA:
        nivel = "leve"
    if modo == "forte_sempre" and score >= LIMIAR_DUVIDA:
        nivel = "forte"
    if modo == "leve_sempre" and score >= LIMIAR_DUVIDA:
        nivel = "leve"

    if nivel == "intacto":
        return "intacto"

    if nivel == "leve":
        # NÍVEL 1: EXODIA FOSCO
        # Igual a imagem da direita da usuária.
        # Fundo é FFmpeg modificado + OpenCV GaussianBlur. Balões ficam limpos por cima.
        import cv2, numpy as np
        vf_exodia = ("FC::"
                     "[0:v]split=2[bg][fg];"
                     "[bg]negate,scale=iw/25:-1,scale=iw*25:-1:flags=neighbor,hue=s=0,noise=alls=60:allf=t+u,"
                     "drawbox=x=0:y=0:w=iw:h=ih:color=white@0.7:t=fill[bg_tratado];"
                     "[fg]lumakey=threshold=0.85:tolerance=0.20:softness=0.10[baloes];"
                     "[bg_tratado][baloes]overlay")

        tmp_ex = str(img_out) + ".ex.jpg"
        cmd = [_ffmpeg(), "-y", "-i", str(img_in), "-filter_complex", vf_exodia[4:], "-q:v", "2", tmp_ex]
        subprocess.run(cmd, check=True, capture_output=True, timeout=60)

        if Path(tmp_ex).exists():
            img_orig = cv2.imread(str(img_in))
            img_ex = cv2.imread(tmp_ex)
            if img_orig is not None and img_ex is not None:
                img_ex = cv2.resize(img_ex, (img_orig.shape[1], img_orig.shape[0]))

                # Embaça o exodia puro
                exodia_fosco = cv2.GaussianBlur(img_ex, (251, 251), 0)

                # Extrai máscara dos balões na arte ORIGINAL
                gray = cv2.cvtColor(img_orig, cv2.COLOR_BGR2GRAY)
                _, mask_white = cv2.threshold(gray, 240, 255, cv2.THRESH_BINARY)
                kernel = np.ones((15, 15), np.uint8)
                mask_balao = cv2.dilate(mask_white, kernel, iterations=2)
                mask_balao = cv2.erode(mask_balao, kernel, iterations=1)
                mask_balao = cv2.GaussianBlur(mask_balao, (15, 15), 0)
                mask_3c = mask_balao.astype(float) / 255.0
                mask_3c = np.stack([mask_3c]*3, axis=-1)

                # Fundo = Exodia Fosco, Frente = Balões limpos originais
                res = (img_orig * mask_3c + exodia_fosco * (1 - mask_3c)).astype(np.uint8)
                ok = cv2.imwrite(str(img_out), res)
            try: Path(tmp_ex).unlink(missing_ok=True)
            except: pass
            return nivel if ok else None
        return None
    else:  # forte
        _modo = os.environ.get("CENSURA_MODO", "cor").strip().lower()
        _alias = {"nivel1": "tarja", "1": "tarja", "nivel2": "cor", "2": "cor",
                  "nivel3": "sutil", "3": "sutil", "lumakey": "sutil"}
        modo_forte = _alias.get(_modo, _modo)
        bx, by, bw, bh = int(W*0.12), int(H*0.12), int(W*0.76), int(H*0.74)

        # NÍVEL 2: BLUR EXTREMO TOTAL (Até os balões das palavras)
        # Imagem da esquerda da usuária. Apaga absolutamente tudo.
        import cv2
        bgr = cv2.imread(str(img_in))
        if bgr is not None:
            # Borrão absurdamente alto que derrete tudo sem máscara de texto
            fosco = cv2.GaussianBlur(bgr, (251, 251), 0)
            ok = cv2.imwrite(str(img_out), fosco)
            return nivel if ok else None
        return None
        


    try:
        # Se vf não foi declarada (porque caiu no nível 2 e não passou por nada anterior), ignora o block.
        # No nível 2 já retornamos 'nivel' ali em cima, logo só cai aqui se for intacto ou alguma falha.
        if 'vf' in locals():
            if isinstance(vf, str) and vf.startswith("FC::"):
                cmd = [_ffmpeg(), "-y", "-i", str(img_in), "-filter_complex", vf[4:], "-q:v", "2", str(img_out)]
            else:
                cmd = [_ffmpeg(), "-y", "-i", str(img_in), "-vf", vf, "-q:v", "2", str(img_out)]
            subprocess.run(cmd, check=True, capture_output=True, timeout=60)
            return nivel if Path(img_out).exists() else None
    except Exception:
        return None
    return None


def processar_painel(img_in, img_out, modo="hibrido", force_detect=False):
    
    det = detectar_score(img_in)
    if det is None:
        return None
    score, _nud = det
    
    if score < LIMIAR_DUVIDA and not force_detect:
        return {"nivel": "intacto", "score": score}
    boxes = detectar_boxes(img_in) if score >= LIMIAR_NSFW else []
    nivel = censurar_imagem(img_in, img_out, score, boxes, modo=modo)
    if nivel in (None, "intacto"):
        return {"nivel": nivel or "falha", "score": score}
    return {"nivel": nivel, "score": score, "boxes": len(boxes)}
