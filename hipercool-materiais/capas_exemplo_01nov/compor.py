# Texto das capas-exemplo 01/11: rótulos amarelos com seta (Porão) — papel dele + fala dela, pela checagem da visão.
import json
import sys
from pathlib import Path

sys.path.insert(0, r"D:\recapd-ambientes\producao\bin")
import capa_ia_anime as c  # noqa: E402

BASE = Path(r"D:\hipercool-materiais\capas_exemplo_01nov")
TEXTOS = {
    "pjOoN03xa0k": ("IMPERADOR GÊNIO", "VEM, BONITÃO!"),
    "VgQUQTmYLeQ": ("FAZENDA NÍVEL 100", "SÓ MEU!"),
    "ssMbrCz0fhE": ("FERREIRO RANK SSS", "VOCÊ É MEU!"),
    "bSwsF_ISmrM": ("FAZENDA NA DUNGEON", "ME ESCOLHE!"),
}
for img in sorted((BASE / "brutas").glob("*.png")):
    vid = img.stem.rsplit("_", 1)[0]
    if vid not in TEXTOS or (len(sys.argv) > 1 and img.stem not in sys.argv[1:]):
        continue
    chk = c._checar(img)
    papel, fala = TEXTOS[vid]
    out = BASE / f"{img.stem}.jpg"
    c._compor(img, papel, out, c.QUADRO["16:9"], estilo="rotulos", mascote=None, rostos=chk, fala=fala)
    print(img.stem, "reprovada" if c._reprovada(chk) else "ok", json.dumps(chk, ensure_ascii=False)[:300], flush=True)
