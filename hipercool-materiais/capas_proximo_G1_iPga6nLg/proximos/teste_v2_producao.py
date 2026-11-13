# Teste ponta a ponta das capas v2 na produção (capa_ia_anime + capa_longo_v2): python teste_v2_producao.py <id> [ficha]
import sys
from pathlib import Path

sys.path.insert(0, r"D:\recapd-ambientes\producao\bin")
import capa_ia_anime as c  # noqa: E402
import capa_longo_v2 as v2  # noqa: E402

vid = sys.argv[1]
url = f"https://youtu.be/{vid}"
ref = c._capa_do_parceiro(url)
f = c._ficha_v2(ref, "", "16:9")
print("FICHA:", f)
if "ficha" in sys.argv:
    print("\nPROMPT A:", v2.montar(f, "A", url)[:1500])
    raise SystemExit
saida = Path(__file__).parent / "teste_v2" / vid / "capa.jpg"
saida.parent.mkdir(parents=True, exist_ok=True)
print("A:", c.capa_melhorada(url, str(saida), texto="X", cena=""))
print("B/C:", c.capas_ab(url, str(saida), texto="X", cena=""))
