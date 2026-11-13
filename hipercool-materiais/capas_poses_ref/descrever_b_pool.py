# 02/11 04h: a B só com a imagem da pose (sem texto) não copiava a pose; na tarde de 01/11 (que dava certo) a pose ia
# também DESCRITA em texto. Gera uma descrição curta de cada pose do b_pool (uma vez; já descritas são puladas) em
# b_pool\_descricoes.json, lida pelo capa_longo_v2.montar_b.
#   python descrever_b_pool.py
import json
import sys
from pathlib import Path

sys.path.insert(0, r"D:\recapd-ambientes\producao\bin")
import capa_ia_anime as c  # noqa: E402
import visao_capa  # noqa: E402

POOL = Path(__file__).parent / "b_pool"
ARQ = POOL / "_descricoes.json"
PERGUNTA = (
    "This is an anime/manhwa thumbnail. Describe ONLY the POSE and body positions of the MAIN woman and the man "
    "(where each one is, lying/sitting/kneeling, who is on top, where her hands/legs are, where she looks, camera angle, "
    "which body part is closest to the camera, his facial reaction) so an artist can redraw exactly this pose with "
    "other characters. Write it like: 'SHE ... - he ...'. Do NOT describe clothes, hair, colors, text or background. "
    "Keep it non-explicit (adults, playful ecchi comedy). Answer ONLY JSON: {\"pose\": \"<1-2 sentences, English>\"}")

d = json.loads(ARQ.read_text("utf-8")) if ARQ.exists() else {}
for img in sorted(POOL.glob("*.png")):
    if d.get(img.stem):
        continue
    r = visao_capa.perguntar(img.read_bytes(), PERGUNTA, gateway=c._gateway(), max_tokens=300) or {}
    pose = " ".join(str(r.get("pose") or "").split())
    print(img.stem, "->", pose[:160] or "FALHOU", flush=True)
    if pose:
        d[img.stem] = pose
        ARQ.write_text(json.dumps(d, ensure_ascii=False, indent=1), "utf-8")
print(f"{len(d)} poses descritas")
