# Patch aditivo 2 na oficina: rota interna /videos/api/fotos_b64 (fotos em base64 → entrada/<id>.jpg, 48 h),
# para mandar ao "Vídeo de Anúncio" fotos que estão guardadas num banco (vitrine de imóveis).
import sys
from pathlib import Path

f = Path("/opt/video-oficina/app.py")
t = f.read_text(encoding="utf-8")
if "fotos_b64" in t:
    print("já aplicado"); sys.exit(0)
rota = '''

@app.post("/videos/api/fotos_b64")
async def fotos_b64(req: Request):
    """{"fotos": ["<base64>", ...]} (até 20) → {"ids": ["0a1b2c3d4e5f.jpg", ...]} na pasta de entrada (48 h)."""
    b = await req.json()
    lista = (b.get("fotos") or [])[:20]
    if not lista:
        raise HTTPException(400, "mande pelo menos 1 foto")

    def grava():
        ids = []
        for s in lista:
            img = ImageOps.exif_transpose(Image.open(io.BytesIO(base64.b64decode(str(s).split(",")[-1])))).convert("RGB")
            img.thumbnail((2560, 2560))
            nome = uuid.uuid4().hex[:12] + ".jpg"
            img.save(DADOS / "entrada" / nome, quality=90)
            ids.append(nome)
        return {"ids": ids}

    try:
        return await asyncio.to_thread(grava)
    except Exception as e:
        raise HTTPException(400, f"foto inválida: {str(e)[:120]}")
'''
marco = '\n\n# ═════════════ cortes automáticos'
assert t.count(marco) == 1
f.write_text(t.replace(marco, rota + marco), encoding="utf-8")
print("ok")
