"""06/11 dona: "se até a hora de postar não tiver aprovado uma capa nas exigências, posta com as rejeitadas de roupa
mesmo" + "inclusive poste nas que estão sem capas". Para os longos JÁ POSTADOS (colab\\capas_depois.json) que ficaram
sem a B/C: usa a reprovada_auto da letra que foi recusada SÓ por roupa/letras (rechecada: nunca nudez/menor/sangue),
monta como capa_b/capa_c e sobe o teste A/B (A + B/C) pelo Studio. Canal sem A/B = fica a A que já está.
    python capas_toleradas_ja_postados.py          -> só monta (para conferir)
    python capas_toleradas_ja_postados.py --subir  -> monta e sobe
"""
import json
import re
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parent / "bin"))
sys.path.insert(0, str(AQUI))
import capa_ia_anime as c  # noqa: E402
import capas_depois as cd  # noqa: E402

SUBIR = "--subir" in sys.argv
EST = AQUI / "capas_toleradas_ja_postados.json"


def candidata(rep, letra):
    for f in sorted(rep.glob(f"{letra}_*.jpg")):
        motivos = set(f.stem.split("_")[3:])
        if motivos and motivos <= {"letras", "vestidas"}:
            return f
    return None


def main():
    est = json.loads(EST.read_text(encoding="utf-8")) if EST.exists() else {}
    for item in cd.ler():
        vid, pasta, p = item["vid"], Path(item["pasta"]), item["params"]
        if est.get(vid, {}).get("subiu"):
            continue
        rep, capa = pasta / "reprovadas_auto", pasta / "capa.jpg"
        if not rep.exists() or not capa.exists():
            continue
        novas = []
        for letra in "bc":
            out = pasta / f"capa_{letra}.jpg"
            if out.exists():
                novas.append(out)
                continue
            f = candidata(rep, letra.upper())
            if not f:
                continue
            chk = c._checar(str(f))
            if not c._so_roupa_ou_letras(chk):
                print(vid, letra, "rechecada: não tolerável", chk)
                continue
            texto, cena = p.get("texto", ""), p.get("cena", "")
            if letra == "b":
                txt, estilo, fala = (c._etiqueta(texto, cena) if texto else ""), "etiqueta", ""
            else:
                txt, estilo = (c._papel(texto, cena) if texto else ""), "rotulos"
                fala = c.FALAS_DELA[0] if texto else ""
            c._compor(str(f), txt, out, c.QUADRO["16:9"], estilo=estilo, rostos=chk, fala=fala)
            out.with_suffix(".capa.json").write_text(json.dumps(
                {"pose": "tolerada_ja_postado", "tolerada": True, "variante_ab": letra, "origem": str(f),
                 "texto": txt, "checagem": chk}, ensure_ascii=False, indent=1), encoding="utf-8")
            print(vid, letra, "montada", out)
            novas.append(out)
        if not novas:
            continue
        est[vid] = {"capas": [str(x) for x in novas], "subiu": False}
        if SUBIR:
            res = cd._studio(item["canal"], vid, "--ab", ",".join(str(x) for x in [capa] + novas[:2]))
            ok = bool(re.search(r'"teste_ab": "(ok|ja)', res))
            est[vid].update(subiu=ok, res=res[:200])
            print(vid, "Studio:", res[:160])
        EST.write_text(json.dumps(est, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
