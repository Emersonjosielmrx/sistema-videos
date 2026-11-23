# -*- coding: utf-8 -*-
"""Memes BR curtos (pt ou sem fala) para os vídeos + corta os longos que a dona deixou no Desktop.
1 download por vez (ytdlp_vez), pausa entre eles, para na hora se o YouTube barrar o IP."""
import json, re, subprocess, sys, time
from pathlib import Path

sys.path.insert(0, r"D:\hipercool-materiais\comum")
import ytdlp_vez  # noqa: E402

FF = r"D:\hipercool-materiais\bin\ffmpeg.exe"
FP = r"D:\hipercool-materiais\bin\ffprobe.exe"
DESK = Path(r"C:\Users\Haylla\Desktop")
SAIDA = DESK / "memes_pt"
CORTES = DESK / "memes_novos_2023" / "cortes_curtos"
MAX_S = 12  # meme curto

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


def dur(p):
    try:
        return float(subprocess.run([FP, "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(p)],
                                    capture_output=True, text=True, timeout=60).stdout.strip())
    except Exception:  # noqa: BLE001
        return 0.0


def nome(s):
    return re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_")[:40]


def baixar():
    SAIDA.mkdir(exist_ok=True)
    feito = {p.stem.split("__")[0] for p in SAIDA.glob("*.mp4")}
    for i, q in enumerate(BUSCAS, 1):
        base = f"{i:02d}_{nome(q)}"
        if base in feito:
            continue
        while ytdlp_vez.pausado():
            print(f"pausa do yt-dlp: {ytdlp_vez.pausado()/60:.0f} min", flush=True)
            time.sleep(60)
        cmd = ["yt-dlp", f"ytsearch5:{q}", "--match-filter", f"duration<={MAX_S}", "--max-downloads", "1",
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
        ok = any(SAIDA.glob(base + "__*.mp4"))
        print(f"{'OK ' if ok else '-- '}{q}", flush=True)
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
        r = subprocess.run([FF, "-nostdin", "-hide_banner", "-i", str(p), "-af", "silencedetect=n=-35dB:d=0.35", "-f", "null", "-"],
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
            subprocess.run([FF, "-nostdin", "-hide_banner", "-loglevel", "error", "-y", "-ss", f"{a:.2f}", "-i", str(p),
                            "-t", f"{b - a:.2f}", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
                            "-c:a", "aac", "-b:a", "160k", str(CORTES / f"{base}_{k:02d}.mp4")])
        print(f"cortado {p.name}: {len(final)} pedaços", flush=True)


if __name__ == "__main__":
    if "cortar" in sys.argv[1:] or len(sys.argv) == 1:
        cortar()
    if "baixar" in sys.argv[1:] or len(sys.argv) == 1:
        baixar()
    print("FIM", flush=True)
