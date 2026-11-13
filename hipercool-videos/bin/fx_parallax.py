# -*- coding: utf-8 -*-
"""fx_parallax.py — personagem RECORTADO do painel + movimento 2.5D (parallax). Sem API.

Recorte: modelo local isnet-anime (ONNX, CPU, ~2-3 s/painel), máscara em cache por md5.
Camadas (canvas W x H):
  1. fundo: o próprio painel cobrindo a tela, bem borrado e escuro (aparece nas faixas);
  2. painel inteiro encaixado na largura, com o pan vertical preso aos balões (_trilho_baloes), com o lugar do
     personagem preenchido (inpaint) pra não aparecer "fantasma" quando ele se mexe;
  3. personagem recortado com sombra e contorno de luz, aproximando mais rápido e
     deslizando ao contrário do painel -> profundidade.
Closes (sem recorte): rosto achado pelo YOLOv8 de rosto de anime (ONNX local, cache por md5) ->
punch-in no rosto pra REAÇÃO; coisa pequena achada pelo recorte (sem rosto) -> close no OBJETO.
O movimento é gerado em OpenCV e codificado no Quick Sync (GPU Intel) quando dá; depois
passa pelo MESMO comando do build_clip (cor, vinheta, overlay, luma, transição, SFX).
Qualquer falha cai no build_clip normal: o pipeline nunca quebra por causa disto.

Ligar/desligar: HIPER_PARALLAX=0 desliga. HIPER_PARALLAX_CHANCE (padrão 0.6).

Cache (workspace/cache/clips_2p5d): o vídeo do movimento (a parte cara, numpy quadro a quadro) fica guardado
por imagem+modo+painel; outro render do mesmo painel (as outras línguas) reaproveita esticando/encolhendo pra
duração da fala nova (RETIME) e só refaz o passe barato (cor/vinheta/overlay/transição/SFX/voz). Nas outras
línguas o espelho está DESLIGADO (ESPELHO_CHANCE = 0): ele invertia onomatopeia, letreiro de loja e
balão que o detector de balão não pega. HIPER_CACHE_2P5D=0 desliga; HIPER_CACHE_2P5D_GB = tamanho máximo (apaga os mais velhos).
"""
import hashlib
import math
import os
import subprocess
from pathlib import Path

from fx_assets import W, H, FPS
from fx_clips import (CLIP_CRF, apply_effects_to_cmd, build_clip, _append_overlay,
                      _append_luma_transition)
from hp_common import PROJECT_DIR, log

try:  # COMUM (dona 02/11): DepthFlow no modo profundidade; sem a lib/GPU segue o render antigo
    import realce_visual
except Exception:  # noqa: BLE001
    realce_visual = None

MODELO = Path(os.environ.get("HIPER_SEG_MODELO", r"D:\hipercool-materiais\models\isnet-anime.onnx"))
MODELO_ROSTO = Path(os.environ.get("HIPER_ROSTO_MODELO", r"D:\hipercool-materiais\models\anime_face_yolov8s.onnx"))
MASK_DIR = PROJECT_DIR / "workspace" / "cache" / "mascaras"
FRAC_MIN, FRAC_MAX = 0.10, 0.72   # personagem precisa ocupar uma parte razoável do painel
RATIO_MAX = 3.0                   # painel mais alto que isso continua no pan vertical normal
CHANCE = float(os.environ.get("HIPER_PARALLAX_CHANCE", "0.75"))
LIGADO = os.environ.get("HIPER_PARALLAX", "1") != "0"
ROSTO_CONF = 0.5
ROSTO_FRAC = (0.08, 0.65)         # largura do rosto / largura do painel pra valer um close
ROSTO_GRANDE = 0.40               # daqui pra cima o rosto já enche o painel: close nos OLHOS, zoom menor
ZOOM_MAX = 3.0                    # px da tela por px do painel no close (mais que isso borra)
CACHE_DIR = PROJECT_DIR / "workspace" / "cache" / "clips_2p5d"
RETIME = (0.75, 1.4)              # fator de duração aceito ao reaproveitar (mais que isso o movimento destoa)
# Espelho DESLIGADO (16/10): a única trava era tem_balao(), que só enxerga balão branco inteiro.
# Medido no cap 1 do The Inheritor: dos 11 painéis que sairiam espelhados em inglês, 9 têm texto na tela
# — onomatopeia coreana (p015, p019, p050, p074), texto em pt "NÃO FOI NADA MAIS" (p046), página de
# créditos (p108) e balão colado na borda que o detector não pega (p001, p012, p105). Texto ao contrário
# na tela é pior do que todas as línguas terem o mesmo movimento. Religar só com detector de texto
# fora de balão (e de painel com dois quadros lado a lado, que inverte a ordem de leitura).
ESPELHO_CHANCE = 0.0              # fração dos painéis sem balão que sai espelhada em cada outra língua
CACHE_STATS = {"reaproveitado": 0, "novo": 0, "espelhado": 0}

_sess = None
_cache_podado = False
_sess_rosto = None
_qsv_ok = None
_sess_depth = None

MODELO_DEPTH = Path(os.environ.get("HIPER_DEPTH_MODELO",
                                    r"D:\hipercool-materiais\models\depth-anything-v2-small\model.onnx"))
DEPTH_CACHE = PROJECT_DIR / "workspace" / "cache" / "profundidade"


def _sessao():
    global _sess
    if _sess is None:
        import onnxruntime as ort
        _sess = ort.InferenceSession(str(MODELO), providers=["CPUExecutionProvider"])
    return _sess


def mascara(img_path):
    """Máscara 0..255 (uint8) do personagem, do tamanho do painel. Cache por md5."""
    import cv2
    import numpy as np
    from PIL import Image
    h = hashlib.md5(Path(img_path).read_bytes()).hexdigest()
    cache = MASK_DIR / f"{h}.png"
    if cache.exists():
        return cv2.imread(str(cache), cv2.IMREAD_GRAYSCALE)
    im = Image.open(img_path).convert("RGB")
    a = np.asarray(im.resize((1024, 1024), Image.LANCZOS), dtype=np.float32)
    a = a / max(1.0, float(a.max())) - np.array([0.485, 0.456, 0.406], np.float32)
    s = _sessao()
    pred = s.run(None, {s.get_inputs()[0].name: a.transpose(2, 0, 1)[None].astype(np.float32)})[0][0, 0]
    pred = (pred - pred.min()) / max(1e-6, float(pred.max() - pred.min()))
    m = (cv2.resize(pred, im.size, interpolation=cv2.INTER_LINEAR) * 255).astype(np.uint8)
    MASK_DIR.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(cache), m)
    return m


def rostos(img_path):
    """[(x, y, w, h, conf)] dos rostos (YOLOv8 de rosto de anime/manhwa, ONNX na CPU, ~0,5 s/painel,
    sem API). Cache por md5. [] se o modelo não existir."""
    import json
    import cv2
    import numpy as np
    global _sess_rosto
    h5 = hashlib.md5(Path(img_path).read_bytes()).hexdigest()
    cache = MASK_DIR / f"{h5}.rostos.json"
    if cache.exists():
        return [tuple(r) for r in json.loads(cache.read_text())]
    if not MODELO_ROSTO.exists():
        return []
    if _sess_rosto is None:
        import onnxruntime as ort
        _sess_rosto = ort.InferenceSession(str(MODELO_ROSTO), providers=["CPUExecutionProvider"])
    img = cv2.imread(str(img_path))
    h, w = img.shape[:2]
    s = 640 / max(h, w)
    nw, nh = int(round(w * s)), int(round(h * s))
    pad = np.full((640, 640, 3), 114, np.uint8)
    pad[:nh, :nw] = cv2.resize(img, (nw, nh))
    x = pad[:, :, ::-1].astype(np.float32).transpose(2, 0, 1)[None] / 255.0
    out = _sess_rosto.run(None, {_sess_rosto.get_inputs()[0].name: x})[0][0].T  # (N, 5): cx cy w h conf
    out = out[out[:, 4] >= 0.3]
    caixas = [[float((cx - bw / 2) / s), float((cy - bh / 2) / s), float(bw / s), float(bh / s)]
              for cx, cy, bw, bh, _ in out]
    idx = cv2.dnn.NMSBoxes(caixas, out[:, 4].tolist(), 0.3, 0.5) if caixas else []
    res = [(*[round(v, 1) for v in caixas[i]], round(float(out[i, 4]), 3)) for i in np.array(idx).flatten()]
    MASK_DIR.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps(res))
    return res


def rosto_principal(img_path):
    """(x, y, w, h) do maior rosto que vale um close (confiança >= 0,5 e não ocupando já o painel
    todo), ou None. O teto era 40% da largura e barrava justamente o painel de REAÇÃO (rosto grande):
    no cap 10 só 5 dos 37 painéis com rosto passavam e o capítulo terminou com 1 close (o cap 1 teve 10).
    De 0,65 pra cima é rosto que já cobre o painel inteiro — aí não há close a dar."""
    try:
        from PIL import Image
        pw = Image.open(img_path).size[0]
        ok = [r for r in rostos(img_path) if r[4] >= ROSTO_CONF and ROSTO_FRAC[0] <= r[2] / pw <= ROSTO_FRAC[1]]
    except Exception:  # noqa: BLE001
        return None
    return tuple(max(ok, key=lambda r: r[2])[:4]) if ok else None


def objeto_principal(img_path):
    """(x, y, w, h) de uma coisa pequena em destaque (o recorte achou só 1-10% do painel e nenhum
    rosto): celular, carta, mão com objeto... None se não houver."""
    import cv2
    import numpy as np
    try:
        if not MODELO.exists() or rostos(img_path):
            return None
        m = (mascara(img_path) > 127).astype(np.uint8)
        frac = float(m.mean())
        if not 0.012 <= frac < 0.10:
            return None
        n, _lab, st, _c = cv2.connectedComponentsWithStats(m, 8)
        if n < 2:
            return None
        k = int(np.argmax(st[1:, cv2.CC_STAT_AREA])) + 1
        x, y, w, h, area = (int(v) for v in st[k])
        ph, pw = m.shape
        if area < 0.6 * m.sum() or w < 0.08 * pw:
            return None
        return x, y, w, h
    except Exception:  # noqa: BLE001
        return None


def baloes(img_path):
    """{"frac": fração do painel coberta por balão de fala, "caixas": [[x, y, w, h]]}. Cache por md5."""
    import json
    import cv2
    import numpy as np
    h5 = hashlib.md5(Path(img_path).read_bytes()).hexdigest()
    cache = MASK_DIR / f"{h5}.baloes.json"
    if cache.exists():
        return json.loads(cache.read_text())
    try:
        from censura_visual import _mascara_baloes
        m = (_mascara_baloes(cv2.imread(str(img_path))) > 0).astype(np.uint8)
    except Exception:  # noqa: BLE001
        return {"frac": 0.0, "caixas": []}
    n, _lab, st, _c = cv2.connectedComponentsWithStats(m, 8)
    res = {"frac": round(float(m.mean()), 4), "caixas": [[int(v) for v in st[k][:4]] for k in range(1, n)]}
    MASK_DIR.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps(res))
    return res


def tem_balao(img_path):
    return bool(baloes(img_path)["caixas"])


def espera_leitura(img_path, texto, duration):
    """Segundos com o painel inteiro antes do close. Com balão: tempo de ler (~15 letras/s, mín. 1,2 s,
    no máx. 60% do clip), senão o close tampa o balão. Sem balão: o pulo rápido de sempre."""
    if not tem_balao(img_path):
        return min(0.45, 0.18 * duration)
    return min(0.6 * duration, max(1.2, len(texto or "") / 15.0))


def brilho_principal(img_path):
    """(x, y, w, h) da maior mancha colorida e muito clara (poder, energia, fogo, magia): 1-20% do
    painel. Balão é branco (sem cor) e fica de fora; toda a faixa de tom de pele (rosa, vermelho e
    laranja não saturados ao extremo) também — a arte desenha pele rosada. None se não houver."""
    import cv2
    import numpy as np
    try:
        hsv = cv2.cvtColor(cv2.imread(str(img_path)), cv2.COLOR_BGR2HSV)
        hh, ss, vv = hsv[..., 0], hsv[..., 1], hsv[..., 2]
        pele = ((hh <= 25) | (hh >= 150)) & (ss < 210)
        m = ((vv >= 210) & (ss >= 140) & ~pele).astype(np.uint8)  # cor viva: céu/cabelo azulado não entra
        m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))
        n, _lab, st, _c = cv2.connectedComponentsWithStats(m, 8)
        if n < 2:
            return None
        k = int(np.argmax(st[1:, cv2.CC_STAT_AREA])) + 1
        x, y, w, h, area = (int(v) for v in st[k])
        ph, pw = m.shape
        if not 0.01 <= area / (pw * ph) <= 0.20 or w < 0.08 * pw:
            return None
        return x, y, w, h
    except Exception:  # noqa: BLE001
        return None


def _render_close(img_path, caixa, out_mp4, duration, panel_idx, alvo_frac=0.55, t_pulo=None, olhos=False):
    """Close (punch-in): começa no painel inteiro e, depois de t_pulo s (tempo de ler o balão), a câmera
    'pula' até a caixa (rosto/objeto/poder) com flash leve e segue aproximando devagar. Sem recorte.
    olhos=True (modo close, rosto): rosto que já é grande vira close nos OLHOS em vez de punch-in no meio
    da cara."""
    import cv2
    import numpy as np
    bgr = cv2.imread(str(img_path))
    ph, pw = bgr.shape[:2]
    bx, by, bw, bh = caixa
    cx, cy = bx + bw / 2, by + bh / 2
    s0 = W / pw
    s1 = min(ZOOM_MAX, max(s0 * 1.3, alvo_frac * W / max(bw, bh * W / H * 0.8)))
    if olhos and bw >= ROSTO_GRANDE * pw:
        # painel de reação: a cara já ocupa meio painel. Mirar o meio dela com o punch-in de sempre
        # (1,3x no mínimo) corta testa e queixo; então mira o terço de cima (os olhos) e empurra pouco.
        cy = by + bh * 0.36
        s1 = min(s1, s0 * 1.18)
    sc = max(W / pw, H / ph)
    cover = cv2.resize(bgr, (int(pw * sc) + 2, int(ph * sc) + 2))
    oy_c, ox_c = (cover.shape[0] - H) // 2, (cover.shape[1] - W) // 2
    tela = cv2.convertScaleAbs(cv2.GaussianBlur(cover[oy_c:oy_c + H, ox_c:ox_c + W], (0, 0), 22), alpha=0.42)
    frames = max(2, int(round(duration * FPS)))
    if t_pulo is None:
        t_pulo = min(0.45, 0.18 * duration)
    d_pulo = 0.28

    def origem(s, ancora_y):
        """Canto do painel na tela pra escala s, com o ponto (cx, cy) indo pra (W/2, ancora_y);
        sem mostrar fora do painel onde ele cobre a tela."""
        ox, oy = W / 2 - cx * s, ancora_y - cy * s
        ox = min(0.0, max(W - pw * s, ox)) if pw * s >= W else (W - pw * s) / 2
        oy = min(0.0, max(H - ph * s, oy)) if ph * s >= H else (H - ph * s) / 2
        return ox, oy

    enc = (["-c:v", "h264_qsv", "-global_quality", "16", "-preset", "medium"] if _qsv()
           else ["-c:v", "libx264", "-preset", "veryfast", "-crf", "14"])
    proc = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "bgr24",
                             "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", *enc, "-pix_fmt", "nv12"
                             if _qsv() else "yuv420p", str(out_mp4)], stdin=subprocess.PIPE)
    branco = np.full((H, W, 3), 255, np.uint8)
    try:
        for f in range(frames):
            t = f / FPS
            if t < t_pulo:
                s, k = s0 * (1.0 + 0.02 * t / max(t_pulo, 1e-3)), 0.0
            else:
                k = min(1.0, (t - t_pulo) / d_pulo)
                k = 1 - (1 - k) ** 3  # sai rápido e freia (ease-out)
                resto = max(1e-3, duration - t_pulo - d_pulo)
                s = s0 * 1.02 + (s1 - s0 * 1.02) * k
                s *= 1.0 + 0.05 * max(0.0, (t - t_pulo - d_pulo) / resto)
            ox, oy = origem(s, H * (0.5 - 0.08 * k))
            frame = tela.copy()
            M = np.float32([[s, 0, ox], [0, s, oy]])
            painel = cv2.warpAffine(bgr, M, (W, H), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_CONSTANT)
            xa, ya = max(0, int(round(ox))), max(0, int(round(oy)))
            xb, yb = min(W, int(round(ox + pw * s))), min(H, int(round(oy + ph * s)))
            frame[ya:yb, xa:xb] = painel[ya:yb, xa:xb]
            flash = max(0.0, 1 - (t - t_pulo) / 0.12) * 0.35 if t >= t_pulo else 0.0
            if flash > 0:
                frame = cv2.addWeighted(frame, 1 - flash, branco, flash, 0)
            proc.stdin.write(frame.tobytes())
    finally:
        proc.stdin.close()
        proc.wait(timeout=300)
    return proc.returncode == 0 and Path(out_mp4).exists()


def _varios_quadros(img_path):
    """Painel com faixa branca horizontal no MEIO (dois quadros empilhados): o personagem
    atravessaria a divisória ao se mexer, então fica fora do efeito."""
    import cv2
    import numpy as np
    g = cv2.imread(str(img_path), cv2.IMREAD_GRAYSCALE)
    h = g.shape[0]
    linha_branca = (g >= 240).mean(axis=1) >= 0.97
    arte = ~linha_branca
    for y in np.flatnonzero(np.diff(linha_branca.astype(np.int8)) == 1):  # começo de faixa branca
        fim = y + 1
        while fim < h and linha_branca[fim]:
            fim += 1
        if fim - y >= 6 and arte[:y].sum() > 0.12 * h and arte[fim:].sum() > 0.12 * h:
            return True
    return False


def elegivel(img_path):
    """(True, fração) se o painel tem personagem destacável e proporção que cabe no canvas."""
    if not (LIGADO and MODELO.exists()):
        return False, 0.0
    try:
        from PIL import Image
        pw, ph = Image.open(img_path).size
        if ph / pw > RATIO_MAX or _varios_quadros(img_path):
            return False, 0.0
        frac = float((mascara(img_path) > 127).mean())
    except Exception:  # noqa: BLE001
        return False, 0.0
    return FRAC_MIN <= frac <= FRAC_MAX, frac


def pode_andar(img_path):
    """Personagem de corpo inteiro / meio corpo SOLTO na cena (não cortado na borda de baixo nem
    ocupando a largura toda) — só esse pode 'andar'. Busto colado na borda vira parallax."""
    import numpy as np
    try:
        m = mascara(img_path) > 127
        ys, xs = np.nonzero(m)
        if len(xs) < 50 or m[-3:].mean() > 0.02:
            return False
        ph, pw = m.shape
        larg = (np.percentile(xs, 98) - np.percentile(xs, 2)) / pw
        alt = (np.percentile(ys, 98) - np.percentile(ys, 2)) / ph
        return larg <= 0.55 and alt <= 0.85
    except Exception:  # noqa: BLE001
        return False


def _qsv():
    """O Quick Sync (GPU Intel) funciona nesta máquina? Testa uma vez."""
    global _qsv_ok
    if _qsv_ok is None:
        r = subprocess.run(["ffmpeg", "-v", "error", "-f", "lavfi", "-i", "color=black:s=64x64:d=0.2",
                            "-c:v", "h264_qsv", "-f", "null", "-"], capture_output=True, timeout=30)
        _qsv_ok = r.returncode == 0
    return _qsv_ok


def _duracao_audio(audio_path):
    try:
        r = subprocess.run(["ffprobe", "-v", "quiet", "-show_entries", "format=duration", "-of", "csv=p=0",
                            str(audio_path)], capture_output=True, text=True, timeout=10)
        return float(r.stdout.strip())
    except Exception:  # noqa: BLE001
        return 4.0


def _linhas_velocidade(cx, cy, n=90):
    """Alfa (float32, 2W x 2H) de linhas radiais de mangá centradas em (cx, cy) do canvas."""
    import cv2
    import numpy as np
    rng = np.random.default_rng(int(cx * 7 + cy))
    a = np.zeros((2 * H, 2 * W), np.float32)
    c = np.array([W, H], np.float32)  # centro no meio da folha 2x
    for ang in rng.uniform(0, 2 * np.pi, n):
        larg = rng.uniform(0.004, 0.02)
        r0 = rng.uniform(0.18, 0.32) * H
        p = [c + r0 * np.array([np.cos(ang), np.sin(ang)]),
             c + 2 * H * np.array([np.cos(ang - larg), np.sin(ang - larg)]),
             c + 2 * H * np.array([np.cos(ang + larg), np.sin(ang + larg)])]
        cv2.fillConvexPoly(a, np.int32(p), float(rng.uniform(0.5, 1.0)))
    return cv2.GaussianBlur(a, (0, 0), 1.5), (W - cx, H - cy)


def alvo_personagem(m):
    """Ponto (x, y) no painel pra câmera mirar: centro horizontal do personagem, na altura do
    rosto/tronco (terço de cima da caixa do recorte). None se não houver recorte."""
    import numpy as np
    ys, xs = np.nonzero(m > 127)
    if len(xs) < 50:
        return None
    y0, y1 = np.percentile(ys, 3), np.percentile(ys, 97)
    return float(np.median(xs)), float(y0 + (y1 - y0) * 0.3)


def _sessao_depth():
    global _sess_depth
    if _sess_depth is None:
        if not MODELO_DEPTH.exists():
            return None
        import onnxruntime as ort
        _sess_depth = ort.InferenceSession(str(MODELO_DEPTH), providers=["CPUExecutionProvider"])
    return _sess_depth


def profundidade(img_path):
    """Mapa de profundidade 0..1 (float32) do painel. Cache por md5 em PNG 16-bit."""
    import cv2
    import numpy as np
    h = hashlib.md5(Path(img_path).read_bytes()).hexdigest()
    DEPTH_CACHE.mkdir(parents=True, exist_ok=True)
    cache = DEPTH_CACHE / f"{h}.png"
    if cache.exists():
        d16 = cv2.imread(str(cache), cv2.IMREAD_UNCHANGED)
        return d16.astype(np.float32) / 65535.0
    sess = _sessao_depth()
    if sess is None:
        return None
    from PIL import Image
    im = Image.open(img_path).convert("RGB")
    inp = np.array(im.resize((518, 518))).transpose(2, 0, 1).astype(np.float32) / 255.0
    inp = np.expand_dims(inp, 0)
    out = sess.run(None, {sess.get_inputs()[0].name: inp})[0][0]
    if out.ndim == 3:
        out = out[0]
    dmin, dmax = out.min(), out.max()
    if dmax - dmin > 1e-6:
        out = (out - dmin) / (dmax - dmin)
    else:
        out = np.zeros_like(out)
    depth = cv2.resize(out.astype(np.float32), (im.width, im.height))
    cv2.imwrite(str(cache), (depth * 65535).astype(np.uint16))
    return depth


def profundidade_vale(img_path):
    """Painel serve pro efeito de profundidade? Precisa ser pelo menos tão alto quanto a tela (senão o
    render esticaria) e não ser quase todo balão. O limiar p95-p5 quase nunca barra: o mapa já vem 0..1."""
    import numpy as np
    from PIL import Image
    with Image.open(img_path) as im:
        if im.height * W < im.width * H:
            return False
    if baloes(img_path)["frac"] > 0.35:
        return False
    d = profundidade(img_path)
    if d is None:
        return False
    p5, p95 = np.percentile(d, 5), np.percentile(d, 95)
    return (p95 - p5) > 0.25


DEPTHFLOW_JANELA = 1.25  # painel até 25% mais alto que a tela: a janela fixa ainda pega quase tudo


def _render_depthflow(bgr_resized, depth_resized, caixas, s0, hp, yc_ini, yc_fim, out_mp4, duration, panel_idx):
    """DepthFlow (dona 02/11; REALCE_PARALLAX=0 desliga): câmera 3D de verdade sobre o mapa de profundidade, com
    os balões presos no plano que não mexe. Só quando uma janela fixa W x H pega todos os balões, porque o
    DepthFlow não faz o pan vertical preso aos balões. False = segue o render antigo."""
    import tempfile
    import cv2
    if realce_visual is None or hp > H * DEPTHFLOW_JANELA:
        return False
    y0 = int(min(max((yc_ini + yc_fim) / 2 - H / 2, 0), max(0, hp - H)))
    parados = []
    for x, y, w, h in caixas:
        bx, by, bw, bh = x * s0, y * s0 - y0, w * s0, h * s0
        if by < 0 or by + bh > H:  # balão fora da janela: o pan antigo é que mostra ele
            return False
        parados.append((bx, by, bw, bh))
    with tempfile.TemporaryDirectory(prefix="df_") as td:
        png = Path(td) / "janela.png"
        cv2.imwrite(str(png), bgr_resized[y0:y0 + H, :W])
        return realce_visual.parallax(png, out_mp4, duration, W, H, fps=FPS, semente=panel_idx,
                                      profundidade=depth_resized[y0:y0 + H, :W], parados=parados)


def _render_profundidade(img_path, out_mp4, duration, panel_idx):
    """Render 2.5D por mapa de profundidade: objetos perto aproximam/deslizam mais que longe.
    Balões ficam parados (profundidade zerada com borda suave) pro texto não entortar."""
    import cv2
    import numpy as np
    bgr = cv2.imread(str(img_path))
    ph, pw = bgr.shape[:2]
    depth = profundidade(img_path)
    if depth is None:
        return False
    frames = int(round(duration * FPS))
    s0 = W / pw
    hp = int(round(ph * s0))
    if frames < 2 or hp < H:
        return False
    rng = np.random.default_rng(panel_idx)
    direcao = rng.choice([-1, 1])
    fases = rng.uniform(0, 2 * math.pi, 2)
    bgr_resized = cv2.resize(bgr, (W, hp))
    # mesmo pan preso aos balões dos outros modos (aqui a câmera não dá zoom: zmax = 1)
    yc_ini, yc_fim = _trilho_baloes(baloes(img_path)["caixas"], hp, s0, 1.0)
    if _render_depthflow(bgr_resized, cv2.resize(depth, (W, hp)), baloes(img_path)["caixas"], s0, hp,
                         yc_ini, yc_fim, out_mp4, duration, panel_idx):
        return True
    livre = np.ones((hp, W), np.float32)
    for x, y, w, h in baloes(img_path)["caixas"]:
        livre[max(0, int(y * s0) - 12):int((y + h) * s0) + 12, max(0, int(x * s0) - 12):int((x + w) * s0) + 12] = 0
    depth_resized = (cv2.GaussianBlur(cv2.resize(depth, (W, hp)), (0, 0), 4)
                     * cv2.GaussianBlur(livre, (0, 0), 10)).astype(np.float32)
    enc = ["-c:v", "h264_qsv", "-global_quality", "22"] if _qsv() else \
          ["-c:v", "libx264", "-preset", "fast", "-crf", "22"]
    proc = subprocess.Popen(["ffmpeg", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24",
                             "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", *enc, "-pix_fmt", "nv12"
                             if _qsv() else "yuv420p", str(out_mp4)], stdin=subprocess.PIPE)
    ys, xs = np.mgrid[:H, :W].astype(np.float32)
    for f in range(frames):
        t = f / max(frames - 1, 1)
        e = t * t * (3 - 2 * t)
        y_off = 0
        if hp > H:
            y_off = int(min(max(yc_ini + (yc_fim - yc_ini) * e - H / 2, 0), hp - H))
        crop = bgr_resized[y_off:y_off + H, :W]
        d_crop = depth_resized[y_off:y_off + H, :W]
        dx = direcao * d_crop * 18 * e + 3 * np.sin(2 * np.pi * 0.4 * t + fases[0]) * d_crop
        dy = d_crop * 8 * e + 2 * np.cos(2 * np.pi * 0.3 * t + fases[1]) * d_crop
        zoom = 1.0 + 0.04 * d_crop * e
        map_x = ((xs - W / 2) / zoom + W / 2 - dx).astype(np.float32)
        map_y = ((ys - H / 2) / zoom + H / 2 - dy).astype(np.float32)
        frame = cv2.remap(crop, map_x, map_y, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT_101)
        proc.stdin.write(frame.tobytes())
    proc.stdin.close()
    proc.wait(timeout=60)
    return proc.returncode == 0


# zoom máximo da camada do PAINEL em cada modo (é o que decide quanto da altura ainda cabe na tela)
ZOOM_PAINEL = {"foco": 1.22, "andar": 1.09, "impacto": 1.02}


def _trilho_baloes(caixas, hp, s0, zmax):
    """(centro inicial, centro final) da janela vertical — em px do painel já na escala da tela — pro
    painel mais alto que a tela. Antes era um pan cego do topo ao rodapé e, com o zoom, as bordas ainda
    eram comidas: no cap 10 o balão do painel 1 (1078-1720 de 1764 px) ficava cortado embaixo do começo
    ao fim do clip, e no painel 27 o balão '...' saía por cima. Aqui o trajeto fica PRESO ao trecho que
    deixa os balões inteiros (o maior manda; balão que brigar com ele é ignorado)."""
    hv = H / max(zmax, 1.0)          # altura do painel que ainda cabe na tela no pico do zoom
    if hv >= hp:                     # painel inteiro na tela até o fim do zoom: nada a corrigir
        return hp / 2.0, hp / 2.0
    ini, fim = (H / 2.0, hp - H / 2.0) if hp > H else (hp / 2.0, hp / 2.0)  # trajeto de sempre
    lo, hi = hv / 2.0, hp - hv / 2.0   # tudo que a câmera pode mirar sem a borda do painel aparecer
    for x, y, w, h in sorted(caixas, key=lambda c: -c[2] * c[3]):
        a, b = (y + h) * s0 - hv / 2.0, y * s0 + hv / 2.0   # centros que deixam ESTE balão inteiro
        if a > b or max(lo, a) > min(hi, b):   # balão mais alto que a tela, ou briga com um maior
            continue
        lo, hi = max(lo, a), min(hi, b)
    return min(max(ini, lo), hi), min(max(fim, lo), hi)


def _render_camadas(img_path, mask_src, out_mp4, duration, panel_idx, modo="parallax", com_balao=False):
    """Gera o vídeo do movimento (sem áudio) em out_mp4. modo:
    parallax  personagem e painel em velocidades diferentes;
    andar     personagem atravessa a cena com passo (sobe/desce), fundo vai pro outro lado;
    foco      câmera aproxima e vai até o personagem (uma camada só, sem recorte visível);
    impacto   personagem salta pra frente + linhas de velocidade + fundo escurece + tremor que some;
    tensao    parallax com tremor leve e contínuo.
    Nos modos com recorte o painel de trás fica levemente desfocado (profundidade de campo, e
    esconde o preenchimento do buraco), com os balões de fala NÍTIDOS por cima."""
    import cv2
    import numpy as np
    bgr = cv2.imread(str(img_path))
    ph, pw = bgr.shape[:2]
    m = mascara(mask_src)
    if m.shape[:2] != (ph, pw):
        m = cv2.resize(m, (pw, ph))
    alpha = cv2.GaussianBlur((m > 110).astype(np.float32), (0, 0), 1.2)
    if modo == "foco":
        alpha[:] = 0  # sem camada da frente: o painel inteiro anda até o personagem
    alvo = alvo_personagem(m)
    # sombra e contorno calculados UMA vez no espaço do painel; por quadro só desloca (warp)
    sombra_src = np.roll(cv2.GaussianBlur(alpha, (0, 0), 9), 12, axis=0) * 0.38
    contorno_src = np.clip(cv2.dilate(alpha, np.ones((7, 7), np.uint8)) - alpha, 0, 1) * 0.30

    if modo == "foco":
        fundo_p = bgr.copy()
    else:
        # painel sem o personagem (inpaint em 1/2 resolução, só na região do personagem)
        buraco = cv2.dilate((m > 60).astype(np.uint8) * 255, np.ones((15, 15), np.uint8))
        peq = cv2.inpaint(cv2.resize(bgr, (pw // 2, ph // 2)), cv2.resize(buraco, (pw // 2, ph // 2)),
                          6, cv2.INPAINT_TELEA)
        fundo_p = bgr.copy()
        sel = buraco > 0
        fundo_p[sel] = cv2.resize(peq, (pw, ph))[sel]
        # profundidade de campo: fundo levemente desfocado (o personagem "descola" do painel)
        fundo_p = cv2.GaussianBlur(fundo_p, (0, 0), 2.2 if modo == "andar" else 1.6)
        # painel mais escuro que o personagem (no impacto bem mais, pra ele "saltar")
        fundo_p = cv2.convertScaleAbs(fundo_p, alpha=0.62 if modo == "impacto" else 0.86)
        try:  # balões continuam nítidos e claros (texto legível)
            from censura_visual import _mascara_baloes
            bal = _mascara_baloes(bgr) > 0
            fundo_p[bal] = bgr[bal]
        except Exception:  # noqa: BLE001
            pass

    # fundo de tela: painel cobrindo o canvas, borrado e escuro
    sc = max(W / pw, H / ph)
    cover = cv2.resize(bgr, (int(pw * sc) + 2, int(ph * sc) + 2))
    cy, cx = (cover.shape[0] - H) // 2, (cover.shape[1] - W) // 2
    tela = cv2.convertScaleAbs(cv2.GaussianBlur(cover[cy:cy + H, cx:cx + W], (0, 0), 22), alpha=0.42)

    s0 = W / pw
    hp = ph * s0
    yc_ini, yc_fim = _trilho_baloes(baloes(mask_src)["caixas"], hp, s0, ZOOM_PAINEL.get(modo, 1.06))
    sinal = 1 if panel_idx % 2 == 0 else -1  # alterna o lado do deslize entre painéis
    preto = np.zeros((H, W, 3), np.uint8)
    branco = np.full((H, W, 3), 255, np.uint8)
    frames = max(2, int(round(duration * FPS)))

    enc = (["-c:v", "h264_qsv", "-global_quality", "16", "-preset", "medium"] if _qsv()
           else ["-c:v", "libx264", "-preset", "veryfast", "-crf", "14"])
    proc = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "bgr24",
                             "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", *enc, "-pix_fmt", "nv12"
                             if _qsv() else "yuv420p", str(out_mp4)], stdin=subprocess.PIPE)
    linhas = None
    if modo == "impacto" and alvo:
        y_ini = H / 2 - yc_ini          # onde o topo do painel fica na tela no começo do clip
        linhas, (lx, ly) = _linhas_velocidade(W / 2 - pw * s0 / 2 + alvo[0] * s0, y_ini + alvo[1] * s0)
    rng = np.random.default_rng(panel_idx)
    fases = rng.uniform(0, 6.28, 2)
    # passo do "andar": só sobe/desce se o personagem não estiver cortado na borda de baixo
    # (senão o corte reto do tronco apareceria flutuando)
    passo = 0.0 if (m[-3:] > 127).mean() > 0.02 else 0.011 * H
    n_passos = max(2, round(duration * 1.7))
    try:
        for f in range(frames):
            t = f / (frames - 1)
            e = t * t * (3 - 2 * t)  # suaviza início/fim
            dy_p = 0.0
            if modo == "foco" and alvo:
                # câmera aproxima e anda até o personagem (rosto/tronco vai pro centro)
                z_p = z_f = 1.0 + 0.22 * e
                dx_p = (pw / 2 - alvo[0]) * s0 * z_p * 0.75 * e
                dy_p = (ph / 2 - alvo[1]) * s0 * z_p * 0.75 * e if hp <= H else 0.0
                dx_f, dy_f = dx_p, dy_p
            elif modo == "impacto":
                # personagem salta pra frente nos primeiros ~0,22 s e continua crescendo devagar
                pulo = 1 - (1 - min(1.0, t / 0.22)) ** 3
                z_p, z_f = 1.0 + 0.02 * e, 1.0 + 0.16 * pulo + 0.03 * t
                dx_p, dx_f, dy_f = 0.0, 0.0, -0.01 * H * pulo
            elif modo == "andar":
                # velocidade constante (passo não acelera); personagem um pouco à frente do painel;
                # painel já começa com zoom pra o deslize não mostrar a borda
                z_p, z_f = 1.06 + 0.03 * t, 1.07 + 0.03 * t
                dx_p, dx_f = -sinal * 0.02 * W * (2 * t - 1), sinal * 0.07 * W * (2 * t - 1)
                dy_f = -abs(np.sin(np.pi * n_passos * t)) * passo
            else:
                # câmera do painel: zoom leve + deslize; personagem: zoom bem maior + deslize contrário
                # tensão: zoom mais forte (1.22) que o parallax normal (1.17)
                z_fg = 0.22 if modo == "tensao" else 0.17
                z_p, z_f = 1.0 + 0.06 * e, 1.0 + z_fg * e
                dx_p, dx_f = -sinal * 0.03 * W * e, sinal * 0.045 * W * e
                dy_f = -0.02 * H * e
            # respiração: o recorte "vive" (escala ~1% num ciclo de ~3 s), em vez de figura colada parada
            if modo != "foco":
                z_f *= 1.0 + 0.009 * np.sin(2 * np.pi * (f / FPS) / 3.1 + fases[0])
            # impacto: tranco curto (0.12 s) que some; tensão: balanço lento ±4 px a 0.5 Hz (sem vibração)
            if modo == "impacto":
                amp = (5 * max(0.0, 1 - f / FPS / 0.3)) if com_balao else 8 * max(0.0, 1 - t / 0.12)
                jx = amp * np.sin(f * 2.3 + fases[0])
                jy = amp * np.cos(f * 1.9 + fases[1])
            elif modo == "tensao":
                jx = 4.0 * np.sin(2 * np.pi * 0.5 * t + fases[0])
                jy = 2.5 * np.cos(2 * np.pi * 0.35 * t + fases[1])
            else:
                jx, jy = 0.0, 0.0
            # ponto do painel que fica no meio da tela (pan vertical preso aos balões), travado a cada
            # quadro pra borda do painel não entrar na tela com o zoom daquele momento
            y_cam = yc_ini + (yc_fim - yc_ini) * e
            meia = H / (2 * z_p)   # painel alto: [meia, hp-meia] = sem borda na tela; painel baixo
            lo_f, hi_f = min(meia, hp - meia), max(meia, hp - meia)   # (invertido): painel todo na tela
            y_cam = min(max(y_cam, lo_f), hi_f)

            def matriz(z, dx, dy):
                s = s0 * z
                ox = W / 2 - (pw * s) / 2 + dx + jx
                oy = H / 2 - y_cam * z + dy + jy
                return np.float32([[s, 0, ox], [0, s, oy]])

            Mp, Mf = matriz(z_p, dx_p, dy_p), matriz(z_f, dx_f, dy_f)
            borda = dict(borderMode=cv2.BORDER_CONSTANT, borderValue=0)
            # painel por cima da tela (retângulo exato, sem warp da máscara)
            frame = tela.copy()
            painel = cv2.warpAffine(fundo_p, Mp, (W, H), flags=cv2.INTER_LINEAR, **borda)
            s = s0 * z_p
            x0, y0 = int(round(Mp[0, 2])), int(round(Mp[1, 2]))
            x1, y1 = int(round(x0 + pw * s)), int(round(y0 + ph * s))
            xa, ya, xb, yb = max(0, x0), max(0, y0), min(W, x1), min(H, y1)
            frame[ya:yb, xa:xb] = painel[ya:yb, xa:xb]
            if linhas is not None:  # linhas de velocidade girando devagar, atrás do personagem
                R = cv2.getRotationMatrix2D((W, H), 4.0 * t, 1.0)
                R[0, 2] -= lx
                R[1, 2] -= ly
                a = cv2.warpAffine(linhas, R, (W, H)) * (0.42 * (1 - 0.5 * t))
                frame = cv2.blendLinear(branco, frame, a, 1.0 - a)
            # sombra, contorno de luz e personagem (blendLinear = mistura em C, rápida)
            for camada, src in ((preto, sombra_src), (branco, contorno_src)):
                a = cv2.warpAffine(src, Mf, (W, H), **borda)
                frame = cv2.blendLinear(camada, frame, a, 1.0 - a)
            a_f = cv2.warpAffine(alpha, Mf, (W, H), **borda)
            fg = cv2.warpAffine(bgr, Mf, (W, H), flags=cv2.INTER_LINEAR, **borda)
            frame = cv2.blendLinear(fg, frame, a_f, 1.0 - a_f)
            proc.stdin.write(frame.tobytes())
    finally:
        proc.stdin.close()
        proc.wait(timeout=300)
    return proc.returncode == 0 and Path(out_mp4).exists()


def build_teaser(paineis, out_path, sfx_file=None, seg=0.6):
    """Abertura de ~3 s: montagem rápida dos painéis dados (cortes de `seg` s com flash branco e zoom
    mirando o personagem) + riser. Mesmo formato dos clips de fala (libx264, 30 fps, aac 24k mono):
    formato de áudio diferente quebra o concat com -c copy (vídeo em hindi saiu com o áudio torto)."""
    import cv2
    import numpy as np
    dur = seg * len(paineis)
    n_seg = int(round(seg * FPS))
    cmd = ["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}",
           "-r", str(FPS), "-i", "-"]
    if sfx_file and Path(sfx_file).exists():
        cmd += ["-i", str(sfx_file), "-filter_complex",
                f"[1:a]aformat=sample_rates=24000:channel_layouts=mono,atrim=0:{dur:.2f},"
                f"apad=whole_dur={dur:.2f},volume=0.7,afade=t=out:st={dur - 0.4:.2f}:d=0.4[a]",
                "-map", "0:v", "-map", "[a]"]
    else:
        cmd += ["-f", "lavfi", "-t", f"{dur:.2f}", "-i", "anullsrc=r=24000:cl=mono", "-map", "0:v", "-map", "1:a"]
    cmd += ["-c:v", "libx264", "-preset", "fast", "-crf", CLIP_CRF, "-g", "30", "-c:a", "aac", "-b:a", "192k",
            "-pix_fmt", "yuv420p", "-t", f"{dur:.2f}", str(out_path)]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    try:
        for p in paineis:
            bgr = cv2.imread(str(p))
            ph, pw = bgr.shape[:2]
            alvo = alvo_personagem(mascara(p)) or (pw / 2, ph / 2)
            for f in range(n_seg):
                t = f / max(1, n_seg - 1)
                s = max(W / pw, H / ph) * (1.06 + 0.10 * t)
                ox = min(0.0, max(W - pw * s, W / 2 - alvo[0] * s))
                oy = min(0.0, max(H - ph * s, H * 0.42 - alvo[1] * s))
                fr = cv2.warpAffine(bgr, np.float32([[s, 0, ox], [0, s, oy]]), (W, H))
                if f < 3:  # flash branco no corte
                    fr = cv2.addWeighted(fr, f / 3, np.full_like(fr, 255), 1 - f / 3, 0)
                proc.stdin.write(fr.tobytes())
    finally:
        proc.stdin.close()
        proc.wait(timeout=120)
    return proc.returncode == 0 and Path(out_path).exists()


def escolher_teaser(panel_files, excluir, n=5):
    """Até n painéis da 2ª metade do capítulo com personagem destacável (e fora de `excluir`: +18,
    propaganda), os mais bonitos, em ordem cronológica. [] se houver menos de 3."""
    from fx_acabamento import _nota_painel, _rosto_unico
    import censura_visual

    def sugestivo(p):  # abertura é o 1º segundo do vídeo: nada nem perto de +18 (score do cache)
        s, _ = censura_visual.detectar_score(p)
        return s is not None and s >= 0.25

    metade = len(panel_files) // 2
    cands = [p for k, p in enumerate(panel_files)
             if k >= metade and k not in excluir and elegivel(p)[0] and not sugestivo(p)]
    com_rosto = [p for p in cands if _rosto_unico(p)]  # rosto expressivo prende mais que corpo/cenário
    pool = com_rosto if len(com_rosto) >= 3 else cands
    melhores = sorted(pool, key=_nota_painel, reverse=True)[:n]
    return sorted(melhores, key=panel_files.index) if len(melhores) >= 3 else []


def _cache_ligado():
    return os.environ.get("HIPER_CACHE_2P5D", "1") != "0"


MODOS = ("parallax", "andar", "foco", "impacto", "tensao", "close", "objeto", "poder")


def _chave_cache(img_path, origem, modo, panel_idx):
    h = hashlib.sha1()
    for p in (img_path, origem):
        h.update(Path(p).read_bytes())
    # v2 (16/10): o enquadramento mudou — o trilho agora prende o balão dentro da tela e o zoom
    # ancora no meio da tela. Clip guardado com o v1 tem o balão cortado, então não serve mais.
    h.update(f"|{modo}|{panel_idx}|{W}x{H}@{FPS}|v2".encode())
    return h.hexdigest()[:24]


def cache_ligado():
    return _cache_ligado()


def modos_guardados(img_path, panel_idx):
    """Modos deste painel que já têm o movimento no cache (pra outra língua reaproveitar em vez de sortear)."""
    return [m for m in MODOS if any(CACHE_DIR.glob(f"{_chave_cache(img_path, img_path, m, panel_idx)}__*.mp4"))]


def _do_cache(chave, duration):
    """(arquivo, fator) da versão guardada com a duração mais próxima que ainda dá pra esticar/encolher."""
    melhor = None
    for f in CACHE_DIR.glob(f"{chave}__*.mp4"):
        try:
            fator = duration / (int(f.stem.rsplit("__", 1)[1]) / 1000)
        except (ValueError, ZeroDivisionError):
            continue
        if RETIME[0] <= fator <= RETIME[1] and (melhor is None or abs(math.log(fator)) < abs(math.log(melhor[1]))):
            melhor = (f, fator)
    return melhor


def _podar_cache():
    """Uma vez por processo: passou do limite, apaga os menos usados (mtime é renovado a cada uso)."""
    global _cache_podado
    if _cache_podado:
        return
    _cache_podado = True
    limite = float(os.environ.get("HIPER_CACHE_2P5D_GB", "15")) * 1e9
    arqs = sorted(CACHE_DIR.glob("*.mp4"), key=lambda f: f.stat().st_mtime)
    total = sum(f.stat().st_size for f in arqs)
    for f in arqs:
        if total <= limite:
            break
        total -= f.stat().st_size
        f.unlink(missing_ok=True)


def _espelhar(variante, panel_idx, origem):
    if not variante:
        return False
    sorte = int(hashlib.md5(f"{variante}|{panel_idx}".encode()).hexdigest()[:8], 16) / 0xFFFFFFFF
    return sorte < ESPELHO_CHANCE and not tem_balao(origem)


def build_clip_parallax(img_path, audio_path, out_path, panel_idx, effects_mgr, duration=None,
                        transition_type=None, sfx_file=None, overlay_video=None,
                        luma_transition=None, mascara_de=None, modo="parallax", texto=""):
    """Mesma assinatura do build_clip (+ mascara_de: painel original de onde vem o recorte/rosto/balões,
    pra versão censurada mexer igual; modo: parallax|andar|foco|impacto|tensao|close|objeto|poder;
    texto: a fala, pro tempo de leitura antes do close). Duração = a do áudio.
    effects_mgr.variante (língua do render, None no pt) liga o espelho por língua."""
    kw = dict(transition_type=transition_type, sfx_file=sfx_file,
              overlay_video=overlay_video, luma_transition=luma_transition)
    if duration is None:
        duration = _duracao_audio(audio_path)
    duration = max(duration, 1.5)
    camadas = Path(str(out_path)[:-4] + "_2p5d.mp4")
    origem = mascara_de or img_path
    achado = None
    try:
        fonte, fator = camadas, 1.0
        chave = _chave_cache(img_path, origem, modo, panel_idx) if _cache_ligado() else None
        achado = _do_cache(chave, duration) if chave else None
        if achado:
            fonte, fator = achado
            os.utime(fonte)
            CACHE_STATS["reaproveitado"] += 1
        elif modo in ("close", "objeto", "poder"):
            achar = {"close": rosto_principal, "objeto": objeto_principal, "poder": brilho_principal}[modo]
            caixa = achar(origem)
            if not caixa or not _render_close(img_path, caixa, camadas, duration, panel_idx,
                                              alvo_frac=0.55 if modo == "close" else 0.62,
                                              t_pulo=espera_leitura(origem, texto, duration),
                                              olhos=modo == "close"):
                raise RuntimeError(f"{modo} sem alvo")
        elif modo == "profundidade":
            if not _render_profundidade(img_path, camadas, duration, panel_idx):
                raise RuntimeError("render profundidade falhou")
        elif not _render_camadas(img_path, origem, camadas, duration, panel_idx, modo=modo,
                                 com_balao=tem_balao(origem)):
            raise RuntimeError("render das camadas falhou")
        if chave and not achado:
            CACHE_DIR.mkdir(parents=True, exist_ok=True)
            _podar_cache()
            fonte = CACHE_DIR / f"{chave}__{int(round(duration * 1000))}.mp4"
            os.replace(camadas, fonte)
            CACHE_STATS["novo"] += 1
        pre = [f"setpts={fator:.5f}*PTS", f"fps={FPS}"] if abs(fator - 1.0) > 0.005 else []
        if _espelhar(getattr(effects_mgr, "variante", None), panel_idx, origem):
            pre.append("hflip")
            CACHE_STATS["espelhado"] += 1
        color = effects_mgr.pick_color()
        color_filter = color["filter"] if isinstance(color, dict) else color
        vignette = effects_mgr.pick_vignette()
        vignette_filter = vignette if isinstance(vignette, str) else (
            vignette["filter"] if isinstance(vignette, dict) else None)
        chain = pre + [color_filter] + ([vignette_filter] if vignette_filter else []) + ["format=yuv420p"]
        filter_complex = f"[0:v]{','.join(chain)}[v]"
        filter_complex, overlay_input = _append_overlay(filter_complex, overlay_video)
        luma_idx = 2 + (1 if overlay_input else 0)
        filter_complex, luma_input = _append_luma_transition(filter_complex, luma_transition, luma_idx, duration)
        cmd = ["ffmpeg", "-y", "-i", str(fonte), "-i", str(audio_path), *overlay_input, *luma_input,
               "-filter_complex", filter_complex, "-map", "[v]", "-map", "1:a",
               "-c:v", "libx264", "-preset", "fast", "-crf", CLIP_CRF, "-g", "30",
               "-c:a", "aac", "-b:a", "192k", "-pix_fmt", "yuv420p", "-t", f"{duration:.2f}", str(out_path)]
        cmd = apply_effects_to_cmd(cmd, transition_type, sfx_file, duration)
        subprocess.run(cmd, check=True, capture_output=True, timeout=180)
        return True
    except Exception as e:  # noqa: BLE001
        log(f"  [!] parallax falhou no painel {panel_idx} ({str(e)[:120]}) -> clip normal")
        if achado:  # versão guardada estragada: não reaproveitar de novo
            achado[0].unlink(missing_ok=True)
        return build_clip(img_path, audio_path, out_path, panel_idx, effects_mgr, duration=duration, **kw)
    finally:
        try:
            camadas.unlink(missing_ok=True)
        except PermissionError:
            pass
