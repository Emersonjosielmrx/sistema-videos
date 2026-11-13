"""teste_delogo_no_tempo.py — a cobertura "delogo" da legenda do parceiro acompanha cada legenda (largura/altura do
trecho, e nada quando não há legenda), em vez de uma faixa única da largura da tela. Sem IA, sem rede.
A 2ª parte gera um vídeo de mentira com ffmpeg + PIL (pula sozinha se faltar um dos dois).

    python teste_delogo_no_tempo.py
"""
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import numpy as np  # noqa: E402
import parceiro_marca as pm  # noqa: E402

W, H, FPS = 720, 1280, 15
# (início s, fim s, texto) da "legenda deles" no vídeo de mentira; entre 7,5 e 9 s não há legenda
LEGENDAS = [(1.0, 3.0, "OI"), (4.0, 7.5, "ELE NUNCA MAIS VOLTOU"), (9.0, 11.0, "E AGORA")]
Y_LEG = 0.62


def test_trechos_puro():
    f = pm.DELOGO_FPS
    am = [None] * 60
    for i in range(5, 15):
        am[i] = (0.45, 0.55, 0.60, 0.64)            # palavra curta, 1 s a 3 s
    for i in range(20, 37):
        am[i] = (0.08, 0.92, 0.60, 0.64)            # frase larga
    am[28] = None                                   # buraco de 1 amostra: não quebra o trecho
    for i in range(45, 55):
        am[i] = (0.30, 0.70, 0.60, 0.69)            # 2 linhas (mais alta)
    tr = pm._trechos_delogo(am, W, H, fps=f)
    assert len(tr) == 3, tr
    curto, largo, duas = tr
    assert curto["w"] < 0.15 * W and largo["w"] > 0.8 * W and 0.38 * W < duas["w"] < 0.45 * W, tr
    assert duas["h"] > curto["h"] and all(t["h"] <= pm.DELOGO_MAX_H * H for t in tr)
    assert abs(curto["t0"] - 4 / f) < 0.01 and abs(curto["t1"] - 16 / f) < 0.01, curto     # 1 amostra de folga
    assert all(a["t1"] <= b["t0"] for a, b in zip(tr, tr[1:])), tr                         # sem sobreposição
    assert all(t["x"] >= 2 and t["x"] + t["w"] <= W - 3 for t in tr)
    filtro = pm._filtro_delogo(tr)
    assert filtro.count("delogo=") == 3 and "enable='between(t," in filtro


def test_trechos_bordas():
    assert pm._trechos_delogo([], W, H) == [] and pm._trechos_delogo([None] * 20, W, H) == []
    alta = [(0.2, 0.8, 0.40, 0.70)] * 10                       # 30% da altura: viraria listras -> sem delogo
    assert pm._trechos_delogo(alta, W, H) == []
    muitos = []
    for k in range(200):                                       # 200 legendas de 1 amostra: junta até o teto
        muitos += [(0.1 + 0.3 * (k % 2), 0.5 + 0.3 * (k % 2), 0.6, 0.64), None, None]
    tr = pm._trechos_delogo(muitos, W, H)
    assert 0 < len(tr) <= pm.DELOGO_MAX_TRECHOS, len(tr)
    assert all(a["t1"] <= b["t0"] for a, b in zip(tr, tr[1:]))


def _video_de_mentira(pasta):
    from PIL import Image, ImageDraw, ImageFont
    fonte = next((p for p in ("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", r"C:\Windows\Fonts\arialbd.ttf",
                              "/System/Library/Fonts/Supplemental/Arial Bold.ttf") if Path(p).exists()), None)
    if not fonte:
        return None
    ft = ImageFont.truetype(fonte, 40)
    rnd = np.random.RandomState(1)
    # fundo com TEXTURA (é nele que o delogo largo vira listras): faixas + ruído, tons médios
    base = (90 + 40 * np.sin(np.arange(W) / 9.0)[None, :, None] + rnd.randint(0, 50, (H, W, 3))).clip(0, 255).astype(np.uint8)
    saida = pasta / "fonte.mp4"
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r",
                          str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "ultrafast", "-crf", "12", "-pix_fmt",
                          "yuv420p", str(saida)], stdin=subprocess.PIPE)
    for n in range(12 * FPS):
        t = n / FPS
        img = Image.fromarray(base)
        for a, b, txt in LEGENDAS:
            if a <= t < b:
                ImageDraw.Draw(img).text((W // 2, int(Y_LEG * H)), txt, font=ft, fill=(255, 255, 255), anchor="mm",
                                         stroke_width=4, stroke_fill=(0, 0, 0))
        p.stdin.write(img.tobytes())
    p.stdin.close()
    p.wait()
    return saida


def _quadro(video, t, filtro=None):
    vf = ["-vf", filtro] if filtro else []
    r = subprocess.run(["ffmpeg", "-v", "error", "-i", str(video), *vf, "-ss", f"{t:.2f}", "-frames:v", "1", "-f",
                        "rawvideo", "-pix_fmt", "gray", "-"], capture_output=True)
    assert len(r.stdout) >= W * H, r.stderr[-300:]
    return np.frombuffer(r.stdout[:W * H], np.uint8).reshape(H, W).astype(np.int16)


def test_video_de_mentira():
    if not shutil.which("ffmpeg"):
        print("      (sem ffmpeg: parte do vídeo pulada)")
        return
    try:
        import PIL  # noqa: F401
    except ImportError:
        print("      (sem PIL: parte do vídeo pulada)")
        return
    pasta = Path(tempfile.mkdtemp())
    try:
        video = _video_de_mentira(pasta)
        if video is None:
            print("      (sem fonte de letra: parte do vídeo pulada)")
            return
        faixa_px = [int((Y_LEG - 0.025) * H), int((Y_LEG + 0.025) * H)]
        am = pm._extensoes_no_tempo(video, W, H, [Y_LEG - 0.05, Y_LEG + 0.05])
        assert abs(len(am) - 12 * pm.DELOGO_FPS) <= 2, len(am)
        f = pm.DELOGO_FPS
        assert am[int(2.0 * f)] and am[int(5.5 * f)] and am[int(10.0 * f)]                # legenda na tela
        assert am[int(0.4 * f)] is None and am[int(8.3 * f)] is None                      # sem legenda
        larg = lambda a: a[1] - a[0]
        assert larg(am[int(2.0 * f)]) < 0.2 < 0.7 < larg(am[int(5.5 * f)]), (am[int(2.0 * f)], am[int(5.5 * f)])
        filtro = pm.delogo_no_tempo(video, W, H, faixa_px)
        assert filtro and filtro.count("delogo=") == 3, filtro
        # o ffmpeg aceita a cadeia e ela faz o que promete:
        antes, depois = _quadro(video, 8.3), _quadro(video, 8.3, filtro)
        assert np.abs(antes - depois).max() <= 2, "sem legenda na tela o quadro tem de sair intacto"
        antes, depois = _quadro(video, 2.0), _quadro(video, 2.0, filtro)
        y = int(Y_LEG * H)
        dif = np.abs(antes - depois)[y - 20:y + 20]
        assert dif[:, W // 2 - 25:W // 2 + 25].mean() > 20, "a palavra curta tem de ser apagada"
        assert dif[:, :W // 2 - 90].max() <= 2 and dif[:, W // 2 + 90:].max() <= 2, \
            "fora da palavra curta a imagem não pode ser mexida (antes a faixa pegava a largura toda)"
        antes, depois = _quadro(video, 5.5), _quadro(video, 5.5, filtro)
        dif = np.abs(antes - depois)[y - 20:y + 20]
        assert dif[:, 80:W - 80].mean() > 10, "a frase larga tem de ser apagada inteira"
        # com a medida de largura dos pixels (leg_x) o que está fora dela não entra
        assert pm.delogo_no_tempo(video, W, H, faixa_px, leg_x=[0.96, 0.99]) is None
    finally:
        shutil.rmtree(pasta, ignore_errors=True)


if __name__ == "__main__":
    falhas = 0
    for nome, fn in sorted(globals().items()):
        if nome.startswith("test_"):
            try:
                fn()
                print(f"ok    {nome}")
            except AssertionError as err:
                falhas += 1
                print(f"FALHA {nome}: {err!r}"[:800])
    print("tudo certo" if not falhas else f"{falhas} teste(s) falharam")
    sys.exit(1 if falhas else 0)
