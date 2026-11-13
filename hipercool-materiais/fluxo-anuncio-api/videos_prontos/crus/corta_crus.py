# Corta os vídeos crus do AG JORNALISMO (YouTube, Creative Commons CC BY): tira os ~11 s do começo (onde aparece o
# nome da pessoa na tela) e fecha em até ~88 s, sempre numa pausa da fala. Sem recodificar a imagem? Não: recodifica
# (corte exato) em 1080p, áudio AAC, +faststart para a prévia tocar no navegador.
import re, subprocess
from pathlib import Path

AQUI = Path(__file__).parent
FF = r"D:\hipercool-materiais\bin\ffmpeg.exe"
SEM_JANELA = 0x08000000
VIDEOS = {"yt_HwmTKbcPSNI.mp4": "cru_luciana.mp4", "yt_cqJrF6vg9zo.mp4": "cru_caue.mp4", "yt_STjbJrpRNv4.mp4": "cru_alderon.mp4"}
for orig, novo in VIDEOS.items():
    for limite in (-35, -30, -26, -22):   # sala com barulho: sobe o limite até achar as pausas da fala
        r = subprocess.run([FF, "-hide_banner", "-i", str(AQUI / orig), "-vn", "-af", f"silencedetect=n={limite}dB:d=0.3", "-f", "null", "-"],
                           capture_output=True, text=True, encoding="utf-8", errors="replace", creationflags=SEM_JANELA)
        pausas = [(float(a), float(b)) for a, b in zip(re.findall(r"silence_start: ([\d.]+)", r.stderr), re.findall(r"silence_end: ([\d.]+)", r.stderr))]
        if len(pausas) >= 10:
            break
    ini = next((b - 0.15 for a, b in pausas if b >= 11.5), 12.0)
    fim = max([a + 0.25 for a, b in pausas if ini + 40 < a < ini + 88] or [ini + 85])
    subprocess.run([FF, "-v", "error", "-y", "-ss", f"{ini:.2f}", "-to", f"{fim:.2f}", "-i", str(AQUI / orig), "-c:v", "libx264", "-preset", "medium",
                    "-crf", "18", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", str(AQUI / novo)],
                   check=True, creationflags=SEM_JANELA)
    print(novo, f"de {ini:.2f} a {fim:.2f} s = {fim - ini:.1f} s", len(pausas), "pausas")
