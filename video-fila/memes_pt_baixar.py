# -*- coding: utf-8 -*-
"""Memes BR curtos (pt ou sem fala) para os vídeos + corta os longos que a dona deixou no Desktop.
1 download por vez (ytdlp_vez), pausa entre eles, para na hora se o YouTube barrar o IP."""
import json, os, re, subprocess, sys, time
from pathlib import Path

sys.path.insert(0, r"D:\hipercool-materiais\comum")
import ytdlp_vez  # noqa: E402

FF = r"D:\hipercool-materiais\bin\ffmpeg.exe"
FP = r"D:\hipercool-materiais\bin\ffprobe.exe"
DESK = Path(r"C:\Users\Haylla\Desktop")
SAIDA = DESK / "memes_pt"
CORTES = DESK / "memes_novos_2023" / "cortes_curtos"
MAX_S = 12  # meme curto (cortes dos longos)
MAX_DL = 20  # download: o filtro corta o que sobra

BUSCAS = [
    "que isso meu filho calma meme", "ai que delicia cara meme", "ta pegando fogo bicho meme",
    "e o que galera meme faustao", "olha a faca meme", "cala boca galvao meme",
    "eu vou ficar louco meme", "acabou de acontecer meme som", "nossa senhora meme som",
    "ele gosta meme", "oloco meu meme faustao", "ihhh ala meme", "tururu meme som",
    "que papelao meme", "nao foi dessa vez meme", "brasil sil sil meme",
    "ratinho efeito sonoro meme", "risada do ratinho", "xaropinho meme", "ui ui ui meme",
    "pare de me ligar meme", "e isso ai meme", "deu ruim meme som", "vish meme som",
    "efeito sonoro suspense brasileiro meme", "som de grilo silencio constrangedor",
    "som de plateia rindo meme", "som de aplausos curto meme", "dramatic chipmunk som",
    "som de tapa meme", "som de batida dramatica meme", "efeito sonoro de erro meme br",
    "sei la meme", "tchau querida meme", "ta de brincadeira meme",
]

# 23/11 2ª leva: refazer os que vieram errados + memes BR novos (numerados a partir de 101)
BUSCAS2 = [
    "ai que delicia cara meme original #shorts", "e o que galera faustao meme #shorts", "xaropinho rapaz meme #shorts",
    "eu vou ficar louco meme brasileiro #shorts", "ui ui ui meme brasileiro #shorts", "cala boca galvao #shorts",
    "tchau querida meme #shorts", "nossa senhora meme #shorts", "ihhh ala meme #shorts", "pare de me ligar meme",
    "que deselegante meme", "nao tankei meme", "calma calabreso meme", "receba meme", "eita giovana meme",
    "ai papai meme", "tome meme", "senta la claudia meme", "pode isso arnaldo meme", "ta bom chega meme",
    "e verdade esse bilhete meme", "uepa meme", "ixi meme som", "faz o L meme", "mas que porra e essa meme",
    "acabou a palhacada meme", "olha so quem chegou meme", "nao e possivel meme", "ai meu deus meme",
    "que ota meme", "tchau tchau meme", "meu deus do ceu meme", "socorro meme", "ta tranquilo ta favoravel meme",
    "e o pix nada meme", "nao me compare meme", "cade o respeito meme", "foi de base meme",
    "som de buzina meme", "som de suspense curto", "som de boom dramatico", "som de vidro quebrando meme",
    "som de explosao curta meme", "som de pulo desenho", "som de escorregao desenho", "som de passarinho cantando",
    "som de sino ding", "som de cronometro tic tac", "som de vitoria curto", "som de derrota game over curto",
]


def dur(p):
    try:
        return float(subprocess.run([FP, "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(p)],
                                    capture_output=True, text=True, timeout=60).stdout.strip())
    except Exception:  # noqa: BLE001
        return 0.0


def nome(s):
    return re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_")[:40]


def baixar(lista=None, inicio=1):
    SAIDA.mkdir(exist_ok=True)
    feito = {p.stem.split("__")[0] for p in SAIDA.rglob("*.mp4")}
    try:
        import memes_pt_filtro as filtro
    except Exception as e:  # noqa: BLE001
        filtro = None; print("filtro indisponível:", e, flush=True)
    for i, q in enumerate(lista or BUSCAS, inicio):
        base = f"{i:02d}_{nome(q)}"
        if base in feito:
            continue
        while ytdlp_vez.pausado():
            print(f"pausa do yt-dlp: {ytdlp_vez.pausado()/60:.0f} min", flush=True)
            time.sleep(60)
        cmd = ["yt-dlp", f"ytsearch8:{q}", "--match-filter", f"duration<={MAX_DL}", "--max-downloads", "1",
               "-f", "bv*[height<=1080]+ba/b", "--merge-output-format", "mp4",
               "--ffmpeg-location", str(Path(FF).parent), "--no-playlist", "--no-warnings",
               "-o", str(SAIDA / f"{base}__%(title).40s.%(ext)s")]
        with ytdlp_vez.vez("memes pt: download"):
            r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
        txt = (r.stdout or "") + (r.stderr or "")
        if ytdlp_vez.bloqueio(txt):
            ytdlp_vez.pausar("memes_pt: " + txt[-150:])
            print("YouTube barrou: parei.", flush=True)
            return
        novos = list(SAIDA.glob(base + "__*.mp4"))
        res = ""
        if novos and filtro and os.environ.get('MEMES_FILTRO_NO_DOWNLOAD') == '1':
            try:
                res = filtro.filtrar(novos[0], {})
            except Exception as e:  # noqa: BLE001
                res = f"filtro erro: {e}"
        print(f"{'OK ' if novos else '-- '}{q}  {res}", flush=True)
        time.sleep(25)


def cortar():
    """Longos (> MAX_S) que ficaram no Desktop viram pedaços: corta nos silêncios (cada meme da compilação);
    sem silêncio, pedaços de 5 s. .part incompleto entra só se o ffprobe lê."""
    CORTES.mkdir(exist_ok=True)
    for p in sorted((DESK / "memes_novos_2023").iterdir()):
        if not p.is_file() or p.suffix == ".txt" or p.stat().st_size == 0:
            continue
        d = dur(p)
        if d <= MAX_S or d > 1200:  # >20 min = .part corrompido (duração falsa)
            continue
        base = nome(re.sub(r"^meme_\d+_", "", p.name.replace(".part", "").replace(".mp4", "")))
        if any(CORTES.glob(base + "_*.mp4")):
            continue
        r = subprocess.run(stdin=subprocess.DEVNULL, timeout=120, args=[FF, "-nostdin", "-hide_banner", "-i", str(p), "-af", "silencedetect=n=-35dB:d=0.35", "-f", "null", "-"],
                           capture_output=True, text=True, encoding="utf-8", errors="replace")
        ini = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", r.stderr)]
        fim = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", r.stderr)]
        pontos = sorted({0.0, *ini, *fim, d})
        trechos, a = [], 0.0
        for b in pontos[1:]:
            if b - a >= 1.2:
                trechos.append((a, b))
            a = b
        # trecho comprido demais (música/gameplay) vira pedaços de 5 s
        final = []
        for a, b in trechos:
            while b - a > MAX_S:
                final.append((a, a + 5)); a += 5
            if b - a >= 1.2:
                final.append((a, b))
        final = final[:40]
        for k, (a, b) in enumerate(final, 1):
            subprocess.run(stdin=subprocess.DEVNULL, timeout=120, args=[FF, "-nostdin", "-hide_banner", "-loglevel", "error", "-y", "-ss", f"{a:.2f}", "-i", str(p),
                            "-t", f"{b - a:.2f}", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
                            "-c:a", "aac", "-b:a", "160k", str(CORTES / f"{base}_{k:02d}.mp4")])
        print(f"cortado {p.name}: {len(final)} pedaços", flush=True)


if __name__ == "__main__":
    if "cortar" in sys.argv[1:] or len(sys.argv) == 1:
        cortar()
    if "baixar" in sys.argv[1:] or len(sys.argv) == 1:
        baixar()
    if "baixar2" in sys.argv[1:]:
        baixar(BUSCAS2, 101)
    print("FIM", flush=True)
