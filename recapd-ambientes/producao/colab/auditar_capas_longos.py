r"""auditar_capas_longos.py — confere a capa A que está no AR de cada longo já postado contra o critério das capas
(13/11, dona: "várias capas não batem com a A nem com a B nem com a C; procure quais são e troque").

Critério (capa_longo_v2): protagonista à vista + mulheres de biquíni (nunca roupa) + sem letras/logo + sem tela
dividida + clara + desenho (não foto) + todos adultos. Usa a MESMA checagem de visão das capas (capa_ia_anime._checar)
na capa.jpg da pasta do vídeo — não abre canal nem Studio. Reprovada = volta pra fila do capas_depois (refazer, guarda a
velha) com o motivo; a troca no YouTube vai pela rotina normal (dona autorizou trocar em 13/11).
Obra com elenco menor (MENORES) nunca recebe capa sensual. AUDITAR_CAPAS=0 desliga.

    python auditar_capas_longos.py            # só lista
    python auditar_capas_longos.py --fazer    # põe as reprovadas na fila de refazer
"""
import json
import os
import shutil
import sys
from datetime import datetime
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parent / "bin"))
FILA = AQUI / "capas_depois.json"
MENORES = {"asv0DQxVhVw", "q5Sv63C0THA"}
RES = AQUI / "auditoria_capas.json"


def motivos(c):
    if c is None:
        return ["checagem indisponível"]
    m = []
    if not c.get("ele"):
        m.append("sem protagonista")
    if not c.get("ela"):
        m.append("sem mulher")
    if c.get("vestidas"):
        m.append("mulher vestida")
    for k, txt in (("letras", "letras/logo"), ("dividida", "tela dividida"), ("escura", "escura"), ("foto", "foto real"),
                   ("sangue", "sangue"), ("exposto", "nudez")):
        if c.get(k):
            m.append(txt)
    if c.get("adultos") is False:
        m.append("parece menor")
    return m


def main(fazer):
    if os.environ.get("AUDITAR_CAPAS", "1") == "0":
        return
    import capa_ia_anime as cia
    fila = json.loads(FILA.read_text(encoding="utf-8"))
    feitos = {}
    try:
        feitos = json.loads(RES.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        pass
    reprovadas = []
    for it in fila:
        if it.get("estado") != "feito":
            continue
        vid, pasta = it["vid"], Path(it["pasta"])
        capa = pasta / "capa.jpg"
        if not capa.exists() or vid in MENORES:
            continue
        chave = f"{vid}:{int(capa.stat().st_mtime)}"
        if chave in feitos:  # já auditada (mesma capa): não gasta visão de novo
            m = feitos[chave]
        else:
            m = motivos(cia._checar(str(capa)))
            feitos[chave] = m
            RES.write_text(json.dumps(feitos, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"{vid} {it.get('canal', '')[:22]:22} {'OK' if not m else 'REPROVADA: ' + ', '.join(m)}", flush=True)
        if m and m != ["checagem indisponível"]:
            reprovadas.append((it, m))
    print(f"\n{len(reprovadas)} capa(s) fora do critério")
    if not fazer or not reprovadas:
        return
    fila = json.loads(FILA.read_text(encoding="utf-8"))
    tag = datetime.now().strftime("%m%d")
    for it, m in reprovadas:
        pasta = Path(it["pasta"])
        for f in ("capa.jpg", "capa.capa.json"):
            if (pasta / f).exists():
                shutil.move(str(pasta / f), str(pasta / f"{f}.auditoria_{tag}"))
        for x in fila:
            if x["vid"] == it["vid"]:
                x.update(estado="pendente", tentativas=0, refazer=f"auditoria_{tag}: {', '.join(m)}")
    FILA.write_text(json.dumps(fila, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{len(reprovadas)} na fila pra refazer (a capa velha ficou como .auditoria_{tag})")


if __name__ == "__main__":
    main("--fazer" in sys.argv)
