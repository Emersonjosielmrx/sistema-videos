"""marca_site.py — tira a marca d'água do SITE de tradução (scan) do vídeo-fonte antes do render (dona 26/10: "nas marcas
d'água, remover que seria o melhor; se não, identificar e colocar uma nossa em cima com tarja branca").

A marca do scan (ex.: COLAMANHUA.com, AcloudMerge.com) vem DENTRO do painel e anda com ele — não é fixa na tela, então
o detector de marca fixa do parceiro_marca não pega. Aqui: OCR (RapidOCR) num quadro a cada PASSO s, só o texto com
cara de site (SITE), a mesma caixa em quadros seguidos vira um intervalo; ffmpeg numa passada:
  - caixa pequena  -> delogo (reconstrói o fundo com os pixels da borda: a marca some);
  - caixa grande   -> tarja branca com a NOSSA marca (MARCA_TEXTO) — apagar um bloco grande borra demais.

    python marca_site.py limpar <fonte.mp4> <saida.mp4>   # sem marca achada = copia a fonte (rc 0)
    python marca_site.py ver <fonte.mp4>                  # só lista o que achou
"""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

PASSO = float(os.environ.get("MARCA_SITE_PASSO", "2"))
ESCALA = 0.5          # OCR em meia resolução (marca de scan é legível assim e o OCR fica ~4x mais rápido)
GRANDE = 0.035        # caixa acima disto da área do quadro = tarja em vez de apagar
MARCA_TEXTO = os.environ.get("MARCA_TEXTO", "INOVARE")
FONTE = next((str(p) for p in (Path(r"C:\Windows\Fonts\arialbd.ttf"),
                                Path(os.environ.get("RAIZ_WIN", "/kaggle/working/raiz")) / "C/Windows/Fonts/arialbd.ttf",
                                Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf")) if p.exists()),
             "arialbd.ttf")
SITE = re.compile(r"\.(com|net|org|co|io|xyz|me|top|site|cc|tv|gg|to)\b|www\.|manhua|manhwa|manga|scan|toon|comic|"
                  r"merge|asura|reaper|flame|luminous|webtoon|novel|read\w*\.|\bcom\b", re.I)


def _dims(video):
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                        "stream=width,height:format=duration", "-of", "json", str(video)], capture_output=True, text=True)
    d = json.loads(r.stdout)
    return int(d["streams"][0]["width"]), int(d["streams"][0]["height"]), float(d["format"]["duration"])


FINO = 0.25           # perto de uma marca achada, 4 quadros/s: o painel ROLA e a marca anda junto (26/10: 72 px em 0,5 s)


def _ler(ocr, video, ini, fim, passo, tmp, prefixo):
    """OCR dos quadros de [ini, fim) a cada `passo` s -> [(t, x0, y0, x1, y1, texto, passo)]."""
    for q in Path(tmp).glob(f"{prefixo}*.jpg"):
        q.unlink()
    cmd = ["ffmpeg", "-v", "error", "-ss", f"{ini:.2f}", "-i", str(video)]
    if fim is not None:
        cmd += ["-t", f"{fim - ini:.2f}"]
    subprocess.run(cmd + ["-vf", f"fps=1/{passo},scale=iw*{ESCALA}:-2", "-q:v", "3", f"{tmp}/{prefixo}%06d.jpg"],
                   check=True)
    out = []
    for q in sorted(Path(tmp).glob(f"{prefixo}*.jpg")):
        t = ini + (int(q.stem[len(prefixo):]) - 1) * passo
        res, _ = ocr(str(q))
        for caixa, texto, conf in res or []:
            if float(conf) < 0.5 or not SITE.search(texto.replace(" ", "")):
                continue
            xs = [p[0] / ESCALA for p in caixa]
            ys = [p[1] / ESCALA for p in caixa]
            out.append((t, min(xs), min(ys), max(xs), max(ys), texto, passo))
    return out


def detectar(video):
    """[(t, x0, y0, x1, y1, texto, passo)] em pixels da fonte: passada rápida a cada PASSO s e, em volta de cada
    marca achada, de novo a cada FINO s (segue a rolagem do painel)."""
    from rapidocr_onnxruntime import RapidOCR
    W, H, dur = _dims(video)
    ocr = RapidOCR()
    with tempfile.TemporaryDirectory() as tmp:
        grosso = _ler(ocr, video, 0.0, None, PASSO, tmp, "g")
        janelas = []
        for t in sorted({a[0] for a in grosso}):  # janelas [t-PASSO, t+PASSO] juntando as que se encostam
            a, b = max(0.0, t - PASSO), min(dur, t + PASSO)
            if janelas and a <= janelas[-1][1]:
                janelas[-1][1] = b
            else:
                janelas.append([a, b])
        fino = []
        for a, b in janelas:
            fino += _ler(ocr, video, a, b, FINO, tmp, "f")
    return (fino or grosso), (W, H, dur)


def _iou(a, b):
    ix = max(0, min(a[2], b[2]) - max(a[0], b[0]))
    iy = max(0, min(a[3], b[3]) - max(a[1], b[1]))
    inter = ix * iy
    return inter / ((a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - inter + 1e-6)


def intervalos(achados):
    """Junta a mesma caixa em quadros seguidos: [{a, b, caixa, texto}] (caixa = união, com folga)."""
    grupos = []
    for t, x0, y0, x1, y1, txt, passo in sorted(achados):
        cx = (x0, y0, x1, y1)
        for g in grupos:
            # só junta a MESMA posição (painel parado); andou = caixa nova naquele instante
            if t - g["b"] <= passo * 1.5 and _iou(g["caixa"], cx) > 0.6:
                g["b"] = t
                g["caixa"] = (min(g["caixa"][0], x0), min(g["caixa"][1], y0), max(g["caixa"][2], x1), max(g["caixa"][3], y1))
                break
        else:
            grupos.append({"a": t, "b": t, "caixa": cx, "texto": txt, "passo": passo})
    return grupos


def _filtro(grupos, W, H):
    """Linhas do filtergraph. Caixas que se tocam no mesmo tempo viram uma só (o texto do site vem em 2-3 linhas)."""
    partes = []
    folga = max(6, int(H * 0.008))
    for g in grupos:
        x0, y0, x1, y1 = g["caixa"]
        x0, y0 = max(1, int(x0) - folga), max(1, int(y0) - folga)
        x1, y1 = min(W - 2, int(x1) + folga), min(H - 2, int(y1) + folga)
        w, h = x1 - x0, y1 - y0
        if w < 4 or h < 4:
            continue
        a, b = max(0.0, g["a"] - g["passo"] / 2), g["b"] + g["passo"] / 2
        quando = f"enable='between(t,{a:.2f},{b:.2f})'"
        if w * h / (W * H) <= GRANDE:
            partes.append(f"delogo=x={x0}:y={y0}:w={w}:h={h}:{quando}")
        else:
            fs = max(14, int(h * 0.55))
            fonte = FONTE.replace("\\", "/").replace(":", "\\:")
            partes.append(f"drawbox=x={x0}:y={y0}:w={w}:h={h}:color=white@0.95:t=fill:{quando}")
            partes.append(f"drawtext=fontfile='{fonte}':text='{MARCA_TEXTO}':fontsize={fs}:fontcolor=black:"
                          f"x={x0}+({w}-text_w)/2:y={y0}+({h}-text_h)/2:{quando}")
    return partes


def _mascara_letras(img, x0, y0, x1, y1):
    """Só os TRAÇOS da marca dentro da caixa: pixel que foge da mediana local (letra sobre o desenho)."""
    import cv2
    import numpy as np
    roi = img[y0:y1, x0:x1]
    fundo = cv2.medianBlur(roi, 21)
    dif = cv2.absdiff(roi, fundo).max(axis=2)
    m = (dif > 22).astype(np.uint8) * 255
    return cv2.dilate(m, np.ones((3, 3), np.uint8), iterations=2)


def _inpaint(video, saida, grupos, W, H):
    """26/10: o delogo deixava listras borradas; aqui o OpenCV repinta só as letras (inpaint TELEA) nos quadros em que
    a marca aparece. Caixa GRANDE = tarja branca + nossa marca. Quadros sem marca passam direto."""
    import cv2
    import numpy as np
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=r_frame_rate",
                        "-of", "csv=p=0", str(video)], capture_output=True, text=True)
    n, d = (r.stdout.strip() or "30/1").split("/")
    fps = float(n) / float(d or 1)
    folga = max(4, int(H * 0.006))
    caixas = []
    for g in grupos:
        x0, y0, x1, y1 = g["caixa"]
        x0, y0 = max(0, int(x0) - folga), max(0, int(y0) - folga)
        x1, y1 = min(W, int(x1) + folga), min(H, int(y1) + folga)
        if x1 - x0 >= 4 and y1 - y0 >= 4:
            caixas.append((max(0.0, g["a"] - g["passo"] / 2), g["b"] + g["passo"] / 2, x0, y0, x1, y1))
    dec = subprocess.Popen(["ffmpeg", "-v", "error", "-i", str(video), "-f", "rawvideo", "-pix_fmt", "bgr24", "-"],
                           stdout=subprocess.PIPE)
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}",
                            "-r", f"{fps}", "-i", "-", "-i", str(video), "-map", "0:v", "-map", "1:a?", "-c:v", "libx264",
                            "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p", "-c:a", "copy", str(saida)],
                           stdin=subprocess.PIPE)
    tam, i, mexidos = W * H * 3, 0, 0
    while True:
        buf = dec.stdout.read(tam)
        if len(buf) < tam:
            break
        t = i / fps
        ativas = [c for c in caixas if c[0] <= t <= c[1]]
        if ativas:
            img = np.frombuffer(buf, np.uint8).reshape(H, W, 3).copy()
            for _, _, x0, y0, x1, y1 in ativas:
                if (x1 - x0) * (y1 - y0) / (W * H) > GRANDE:
                    cv2.rectangle(img, (x0, y0), (x1, y1), (255, 255, 255), -1)
                    esc = max(0.5, (y1 - y0) / 45)
                    (tw, th), _ = cv2.getTextSize(MARCA_TEXTO, cv2.FONT_HERSHEY_DUPLEX, esc, 2)
                    cv2.putText(img, MARCA_TEXTO, (x0 + (x1 - x0 - tw) // 2, y0 + (y1 - y0 + th) // 2),
                                cv2.FONT_HERSHEY_DUPLEX, esc, (0, 0, 0), 2, cv2.LINE_AA)
                else:
                    m = _mascara_letras(img, x0, y0, x1, y1)
                    img[y0:y1, x0:x1] = cv2.inpaint(img[y0:y1, x0:x1], m, 4, cv2.INPAINT_TELEA)
            buf = img.tobytes()
            mexidos += 1
        enc.stdin.write(buf)
        i += 1
    enc.stdin.close()
    dec.wait()
    enc.wait()
    print(f"[marca_site] {mexidos} de {i} quadros limpos", flush=True)
    return enc.returncode == 0 and Path(saida).exists()


def limpar(video, saida):
    achados, (W, H, _) = detectar(video)
    grupos = intervalos(achados)
    print(f"[marca_site] {len(achados)} detecção(ões) -> {len(grupos)} marca(s) no tempo", flush=True)
    if not grupos:
        shutil.copy2(video, saida)
        return 0
    if os.environ.get("MARCA_SITE_METODO", "inpaint") == "inpaint":
        try:
            if _inpaint(video, saida, grupos, W, H):
                return 0
        except Exception as e:  # noqa: BLE001 — limpeza é acabamento: falhou = cai no delogo
            print(f"[marca_site] inpaint falhou ({type(e).__name__}: {e}) — tentando delogo", flush=True)
    partes = _filtro(grupos, W, H)
    if not partes:
        shutil.copy2(video, saida)
        return 0
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8") as f:
        f.write(",\n".join(partes))  # filtro em arquivo: centenas de caixas estouram a linha de comando
        script = f.name
    try:
        r = subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(video), "-filter_script:v", script,
                            "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-c:a", "copy", str(saida)],
                           capture_output=True, text=True)
    finally:
        os.unlink(script)
    if r.returncode != 0 or not Path(saida).exists():
        print(f"[marca_site] ffmpeg falhou — segue a fonte sem limpar: {r.stderr[-400:]}", flush=True)
        shutil.copy2(video, saida)
    return 0


if __name__ == "__main__":
    if len(sys.argv) == 4 and sys.argv[1] == "limpar":
        sys.exit(limpar(sys.argv[2], sys.argv[3]))
    if len(sys.argv) == 3 and sys.argv[1] == "ver":
        ach, dims = detectar(sys.argv[2])
        for g in intervalos(ach):
            print(f"{g['a']:7.1f}-{g['b']:7.1f}s  {[int(v) for v in g['caixa']]}  {g['texto']}")
        sys.exit(0)
    print(__doc__)
    sys.exit(1)
