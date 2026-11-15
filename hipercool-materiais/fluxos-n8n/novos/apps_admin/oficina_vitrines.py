# Patch aditivo na oficina (/opt/video-oficina/app.py): pasta "vitrines" que NÃO expira (vídeos dos imóveis)
# e rota interna /videos/api/guardar_video (copia o vídeo pronto do job para vitrines/<pasta>/).
import re, sys
from pathlib import Path

f = Path("/opt/video-oficina/app.py")
t = f.read_text(encoding="utf-8")
if "guardar_video" in t:
    print("já aplicado"); sys.exit(0)

velho = '"estudos": 24 * 400}'
assert t.count(velho) == 1, "GUARDAR_HORAS mudou"
t = t.replace(velho, '"estudos": 24 * 400, "vitrines": 24 * 365 * 20}')

velho = '"cursos", "spots", "estudos"):\n        raise HTTPException(404)'
assert t.count(velho) == 1, "rota arquivo mudou"
t = t.replace(velho, '"cursos", "spots", "estudos", "vitrines"):\n        raise HTTPException(404)')

rota = '''

@app.post("/videos/api/guardar_video")
async def guardar_video(req: Request):
    """Copia o vídeo pronto de um job (saida/<job>.mp4, _musica e capa) para vitrines/<pasta>/, que não expira."""
    b = await req.json()
    job, pasta = b.get("job", ""), b.get("pasta", "")
    if not seguro(job) or not seguro(pasta):
        raise HTTPException(400, "job ou pasta inválida")
    destino = DADOS / "vitrines" / pasta

    def copia():
        destino.mkdir(parents=True, exist_ok=True)
        out = {}
        for nome, origem in (("video.mp4", f"{job}.mp4"), ("video_musica.mp4", f"{job}_musica.mp4"), ("capa.jpg", f"{job}.jpg")):
            if (DADOS / "saida" / origem).exists():
                shutil.copy2(DADOS / "saida" / origem, destino / nome)
                out[nome.split(".")[0]] = f"vitrines/{pasta}/{nome}"
        return out

    out = await asyncio.to_thread(copia)
    if "video" not in out:
        raise HTTPException(404, "vídeo do job não encontrado")
    return out
'''
marco = '\n\n# ═════════════ cortes automáticos'
assert t.count(marco) == 1, "marco mudou"
t = t.replace(marco, rota + marco)
f.write_text(t, encoding="utf-8")
print("ok")
