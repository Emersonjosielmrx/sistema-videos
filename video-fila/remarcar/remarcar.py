"""remarcar.py — troca a @ de canal REMOVIDO gravada no Short de parceiro pela @ de um canal VIVO (dona 19/11: "temos
muitos vídeos sobrando e poucos canais"; 526 Shorts prontos ficaram presos em 13 canais removidos 17-18/11).

Por que não o trocar_marca.py: o molde da @ antiga casava em outro lugar (15 de 40 amostras) e a @ velha continuava
aparecendo. Aqui a área é medida direto: o texto da @ é cinza-claro e fica numa faixa estreita; em 24 quadros espalhados
pego os pixels cinza-claros na faixa onde a @ antiga mora (procurada pelo OCR do Tesseract quando há, senão a faixa
16%-40% da altura, abaixo do card do parceiro) e a união vira uma caixa FIXA, com margem. O vídeo inteiro sai em 1
passada do ffmpeg (crop+gblur+overlay da PNG da @ nova, no estilo parceiro_marca._nossa_marca). Áudio copiado.

    python remarcar.py ENTRADA.mp4 SAIDA.mp4 "@novo-handle" --antigo "@esportenoturno" [--prova prova.png]

Sai com código 2 (sem gravar) se não achar a @ antiga com confiança — nunca posta vídeo com as duas @.
"""
import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

import cv2
import numpy as np

class pm:  # noqa: N801 — cópia de parceiro_marca._nossa_marca (roda também no STI, Linux, sem o recapd)
    FONTE = next((f for f in (os.environ.get("REMARCAR_FONTE", ""), r"C:\Windows\Fonts\timesbd.ttf",
                              str(Path(__file__).with_name("timesbd.ttf"))) if f and Path(f).exists()), "")

    @staticmethod
    def _nossa_marca(handle, altura_px):
        """RGBA da nossa marca: serifada em negrito, branca semitransparente, sombra leve (igual parceiro_marca)."""
        from PIL import Image, ImageDraw, ImageFont
        fonte = ImageFont.truetype(pm.FONTE, max(12, int(altura_px * 0.8)))
        l, t, r, b = ImageDraw.Draw(Image.new("RGBA", (4, 4))).textbbox((0, 0), handle, font=fonte, stroke_width=2)
        img = Image.new("RGBA", (r - l + 8, b - t + 8), (0, 0, 0, 0))
        ImageDraw.Draw(img).text((4 - l, 4 - t), handle, font=fonte, fill=(255, 255, 255, 150),
                                 stroke_width=2, stroke_fill=(0, 0, 0, 70))
        return cv2.cvtColor(np.array(img), cv2.COLOR_RGBA2BGRA)


def quadros(video, n=24):
    cap = cv2.VideoCapture(str(video))
    N = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 1
    out = []
    for k in range(n):
        cap.set(cv2.CAP_PROP_POS_FRAMES, int(N * (k + 0.5) / n))
        ok, f = cap.read()
        if ok:
            out.append(f)
    W, H = int(cap.get(3)), int(cap.get(4))
    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    cap.release()
    return out, W, H, fps


def _linha_do_texto(fr, y0, y1):
    """(ya, yb) da linha onde está a @: maior concentração de pixels cinza-claros (texto) dentro da faixa."""
    reg = fr[y0:y1].astype(int)
    g = reg.mean(axis=2)
    sat = reg.max(axis=2) - reg.min(axis=2)  # a @ é cinza (sem cor); o subtítulo do card é amarelo
    m = ((g > 120) & (g < 225) & (sat < 28)).astype(np.uint8)
    # tira traços longos (bordas do card): linha com cinza em > 70% da largura não é texto
    prof = m.sum(axis=1)
    prof[prof > 0.7 * m.shape[1]] = 0
    return m, prof


def medir(qs, W, H, faixa=(0.16, 0.40)):
    """Caixa fixa (x0,y0,x1,y1) que contém a @ antiga em todos os quadros, ou None."""
    y0f, y1f = int(faixa[0] * H), int(faixa[1] * H)
    caixas = []
    for fr in qs:
        m, prof = _linha_do_texto(fr, y0f, y1f)
        if prof.max() < 8:
            continue
        # a @ é a faixa de ~20-60 px de altura com texto, logo abaixo do card; pega o bloco de linhas com texto
        linhas = np.nonzero(prof > max(8, 0.25 * prof.max()))[0]
        if not len(linhas):
            continue
        # agrupa linhas contíguas e escolhe o bloco de altura de texto (12-70 px) mais "cheio"
        blocos, ini = [], linhas[0]
        for a_, b_ in zip(linhas, linhas[1:]):
            if b_ - a_ > 3:
                blocos.append((ini, a_))
                ini = b_
        blocos.append((ini, linhas[-1]))
        blocos = [(a_, b_) for a_, b_ in blocos if 12 <= b_ - a_ <= 70]
        if not blocos:
            continue
        a_, b_ = max(blocos, key=lambda ab: prof[ab[0]:ab[1] + 1].sum())
        cols = np.nonzero(m[a_:b_ + 1].sum(axis=0) > 0)[0]
        if len(cols) < 20:
            continue
        caixas.append((cols.min(), y0f + a_, cols.max(), y0f + b_))
    if len(caixas) < len(qs) * 0.5:
        return None, caixas
    arr = np.array(caixas)
    # descarta o que fugiu da mediana (cena com texto claro no fundo)
    cy = np.median((arr[:, 1] + arr[:, 3]) / 2)
    h = np.median(arr[:, 3] - arr[:, 1])
    bons = arr[abs((arr[:, 1] + arr[:, 3]) / 2 - cy) < h]
    if len(bons) < len(qs) * 0.5:
        return None, caixas
    x0, y0 = int(np.percentile(bons[:, 0], 5)), int(bons[:, 1].min())
    x1, y1 = int(np.percentile(bons[:, 2], 95)), int(bons[:, 3].max())
    mx, my = int(1.2 * h), int(0.6 * h)  # 19/11: com 0.6/0.35 sobrava a ponta do "@" e a base das letras
    medir.bruta = (x0, y0, x1, y1)
    return (max(0, x0 - mx), max(0, y0 - my), min(W, x1 + mx), min(H, y1 + my)), caixas


def medir_molde(qs, W, H, antigo):
    """19/11 (2º método, o principal quando se sabe a @ antiga): a @ do parceiro_marca é branca a 59% de opacidade e
    PARADA; no mínimo por pixel ao longo dos quadros ela continua clara (>= ~150) e o fundo que se mexe escurece. Casa o
    desenho exato da @ antiga (mesma fonte, várias escalas) nessa imagem. Devolve (caixa com margem, nota) ou (None, nota)."""
    g = np.stack([cv2.cvtColor(f, cv2.COLOR_BGR2GRAY) for f in qs])
    base = np.partition(g, 2, axis=0)[2]  # 3º menor (~10º percentil de 24): aguenta 1-2 quadros de corte/flash
    del g
    # top-hat: só o que é mais claro que a vizinhança (letra fina clara); some com fundo liso claro/escuro
    base = cv2.morphologyEx(base, cv2.MORPH_TOPHAT, cv2.getStructuringElement(cv2.MORPH_RECT, (15, 15)))
    base = base.astype(np.float32)
    v, cx = _casar(base, W, H, antigo)
    # isca: o mesmo handle ao contrário (mesmas letras, mesma largura) — o certo tem que ganhar com folga,
    # senão o "casamento" é só uma faixa clara qualquer no meio da tela
    isca, _ = _casar(base, W, H, "@" + antigo.lstrip("@")[::-1])
    nota = round(float(v), 3)
    medir_molde.isca = round(float(isca), 3)
    if cx is None or v < float(os.environ.get("REMARCAR_NOTA_MIN", "0.40")) or v - isca < 0.05:
        return None, nota
    X0, Y0, X1, Y1 = cx
    h = Y1 - Y0
    mx, my = int(0.6 * h), int(0.45 * h)
    medir.bruta = cx
    return (max(0, X0 - mx), max(0, Y0 - my), min(W, X1 + mx), min(H, Y1 + my)), nota


def _casar(base, W, H, antigo):
    melhor = (-1, None)
    for alt in range(int(H * 0.020), int(H * 0.050) + 1, 1):
        m = pm._nossa_marca(antigo, alt)
        a = (m[:, :, 3] > 100).astype(np.float32)
        ys, xs = np.nonzero(a.any(axis=1))[0], np.nonzero(a.any(axis=0))[0]
        a = a[ys[0]:ys[-1] + 1, xs[0]:xs[-1] + 1]
        th, tw = a.shape
        if tw >= W * 0.95:
            continue
        # só a coluna central (a @ é centralizada) e a altura 10%-75%
        x0 = max(0, int(W / 2 - tw / 2 - 0.08 * W))
        x1 = min(W, int(W / 2 + tw / 2 + 0.08 * W))
        y0, y1 = int(0.10 * H), int(0.75 * H)
        r = cv2.matchTemplate(base[y0:y1, x0:x1], a, cv2.TM_CCOEFF_NORMED)
        _, v, _, p = cv2.minMaxLoc(r)
        if v > melhor[0]:
            melhor = (v, (x0 + p[0], y0 + p[1], x0 + p[0] + tw, y0 + p[1] + th))
    return melhor


def confere(bruta, W, antigo):
    """A @ antiga foi posta por parceiro_marca: CENTRALIZADA (W/2) e na fonte _nossa_marca. Confere centro e largura
    (a do texto medido x a do @antigo desenhado na mesma altura). Devolve motivo de recusa ou ''."""
    x0, y0, x1, y1 = bruta
    cx = (x0 + x1) / 2
    if abs(cx - W / 2) > 0.08 * W:
        return f"caixa fora do centro (cx={cx:.0f}, W/2={W / 2:.0f})"
    if antigo and __import__("os").environ.get("REMARCAR_CONFERE_PROPORCAO") == "1":
        # 19/11: DESLIGADO — a altura medida pega só o miolo das letras e a razão dá 1,4-1,8 até no handle certo.
        # proporção largura/altura da tinta (não depende do tamanho da fonte)
        m = pm._nossa_marca(antigo, 60)
        a = m[:, :, 3] > 100
        ys, xs = np.nonzero(a.any(axis=1))[0], np.nonzero(a.any(axis=0))[0]
        esperado = (xs[-1] - xs[0]) / max(1, ys[-1] - ys[0])
        medido = (x1 - x0) / max(1, y1 - y0)
        r = medido / esperado
        if not 0.75 <= r <= 1.3:
            return f"proporção não bate com {antigo} (medida {medido:.2f}, esperada {esperado:.2f}, razão {r:.2f})"
    return ""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("entrada")
    ap.add_argument("saida")
    ap.add_argument("handle")
    ap.add_argument("--antigo", default="")
    ap.add_argument("--faixa", default="0.16,0.40")
    ap.add_argument("--prova", help="grava PNG antes|depois de 3 quadros")
    ap.add_argument("--so-medir", action="store_true", help="só mede e confere a caixa (sem ffmpeg)")
    ap.add_argument("--plano", action="store_true", help="grava a PNG da @ nova e imprime o filtro (sem ffmpeg)")
    a = ap.parse_args()
    qs, W, H, fps = quadros(a.entrada)
    caixa, todas, nota = None, [], None
    if a.antigo and os.environ.get("REMARCAR_MOLDE", "1") != "0":
        caixa, nota = medir_molde(qs, W, H, a.antigo)
        todas = [1] * len(qs) if caixa else []
    if not caixa:
        caixa, todas = medir(qs, W, H, tuple(float(x) for x in a.faixa.split(",")))
    if not caixa and a.faixa == "0.16,0.40":  # a @ pode ter ido pra 0.64 (MARCA_YS do parceiro_marca)
        caixa, todas = medir(qs, W, H, (0.58, 0.70))
    if not caixa:
        print(json.dumps({"ok": False, "motivo": f"@ antiga não achada com confiança ({len(todas)}/{len(qs)})"}))
        sys.exit(2)
    ruim = confere(medir.bruta, W, a.antigo)
    if ruim:
        print(json.dumps({"ok": False, "motivo": ruim, "caixa": caixa}))
        sys.exit(2)
    if a.so_medir:
        print(json.dumps({"ok": True, "caixa": caixa, "nota_molde": nota, "isca": getattr(medir_molde, "isca", None),
                          "so_medir": True}))
        return
    x0, y0, x1, y1 = caixa
    alt = max(22, int((y1 - y0) * 0.80))
    marca = pm._nossa_marca(a.handle, alt)
    png = Path(a.saida).with_suffix(".marca.png")
    cv2.imwrite(str(png), marca)
    mx = int((x0 + x1) / 2 - marca.shape[1] / 2)
    my = int((y0 + y1) / 2 - marca.shape[0] / 2)
    # some com a @ velha: reduz a caixa a 12x3 px (só a cor média do fundo, sem letra) e estica de volta, suavizado.
    # O gblur sozinho deixava o fantasma da @ antiga legível em fundo escuro (prova 19/11).
    w_, h_ = x1 - x0, y1 - y0
    fc = (f"[0:v]crop={w_}:{h_}:{x0}:{y0},scale=12:3:flags=area,scale={w_}:{h_}:flags=bicubic,gblur=sigma=4[b];"
          f"[0:v][b]overlay={x0}:{y0}[v1];"
          f"[v1][1:v]overlay={mx}:{my}[v]")
    if a.plano:  # o render roda em outra máquina (redistribuir.py): devolve o filtro e deixa a PNG
        print(json.dumps({"ok": True, "caixa": caixa, "fc": fc, "png": str(png)}))
        return
    ffm = os.environ.get("REMARCAR_FFMPEG", "ffmpeg")
    r = subprocess.run([ffm, "-v", "error", "-y", "-i", a.entrada, "-i", str(png), "-filter_complex", fc,
                        "-map", "[v]", "-map", "0:a?", "-c:v", "libx264", "-crf", "19", "-preset", "veryfast",
                        "-pix_fmt", "yuv420p", "-c:a", "copy", "-movflags", "+faststart", a.saida],
                       capture_output=True, text=True)
    png.unlink(missing_ok=True)
    if r.returncode != 0:
        print(json.dumps({"ok": False, "motivo": "ffmpeg: " + r.stderr[-300:]}))
        sys.exit(1)
    if a.prova:
        cap_a, cap_b = cv2.VideoCapture(a.entrada), cv2.VideoCapture(a.saida)
        N = int(cap_a.get(cv2.CAP_PROP_FRAME_COUNT)) or 1
        linhas = []
        ya, yb = max(0, y0 - 120), min(H, y1 + 60)
        for k in (0.15, 0.5, 0.85):
            for cp in (cap_a, cap_b):
                cp.set(cv2.CAP_PROP_POS_FRAMES, int(N * k))
            _, fa = cap_a.read()
            _, fb = cap_b.read()
            linhas.append(np.hstack([fa[ya:yb], fb[ya:yb]]))
        cv2.imwrite(a.prova, np.vstack(linhas))
    print(json.dumps({"ok": True, "caixa": caixa, "amostras": len(todas), "saida": a.saida}))


if __name__ == "__main__":
    main()
