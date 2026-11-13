# Baixa só o 1º minuto e meio do vídeo do parceiro (SNhb31ZuuFA) pra tirar o rosto da bruxa principal (dona 01/11)
import subprocess, sys
sys.path.insert(0, r"D:\recapd-ambientes\producao\bin")
import ytdlp_vez
if ytdlp_vez.pausado():
    sys.exit(f"yt-dlp pausado por {ytdlp_vez.pausado():.0f}s")
with ytdlp_vez.vez("capas: download inicio SNhb31ZuuFA"):
    r = subprocess.run([sys.executable, "-m", "yt_dlp", "-f", "bv*[height<=720][ext=mp4]/b[height<=720]",
                        "--download-sections", "*0-90", "-o", r"D:\hipercool-materiais\capas_exemplo_01nov\quadros\inicio.%(ext)s",
                        "https://www.youtube.com/watch?v=SNhb31ZuuFA"], capture_output=True, text=True)
    print(r.stdout[-1500:], r.stderr[-1500:])
    ytdlp_vez.bloqueio(r.stderr) if hasattr(ytdlp_vez, "bloqueio") else None
