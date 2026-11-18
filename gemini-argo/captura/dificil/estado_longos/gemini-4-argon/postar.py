"""Trecho de colab/postar_longos.py (postagem dos longos). Várias rodadas podem rodar ao mesmo tempo (tarefa do
Windows a cada hora + execução manual); cada uma lê o estado no começo, trabalha horas e grava no fim."""
import json
import threading
from pathlib import Path

BASE = Path(__file__).parent
ESTADO = BASE / "longos_postados.json"
FICHAS = BASE / "fichas"  # uma pasta por longo (ficha); o bipar_palavrao.py cria FICHAS/<nome>/SEM_PALAVRAO.txt
_TRAVA_EST = threading.RLock()


def _estado():
    try:
        return json.loads(ESTADO.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {"postados": [], "reprovados": []}


def _gravar_estado(est):
    """03/11: grava JUNTANDO com o que está no arquivo. Em 02/11 duas rodadas rodaram juntas e a que terminou depois
    gravou a lista que tinha lido de manhã por cima: o post do yKfgs no Fio da Meada sumiu e ele voltou pra fila (quase
    saiu em 3 canais — regra: vídeo único por canal). Postado/reprovado/corte que existir no arquivo nunca se perde."""
    with _TRAVA_EST:
        _gravar_estado_trancado(est)


def _eh_nota_titulo(titulo):
    return not titulo or not isinstance(titulo, str) or titulo.lstrip().startswith("(")


def _gravar_estado_trancado(est):
    disco = _estado()

    titulos_reais_disco = {
        p.get("url"): p.get("titulo")
        for p in disco.get("postados", [])
        if p.get("url") and not _eh_nota_titulo(p.get("titulo"))
    }
    postados_est = []
    for p in est.get("postados", []):
        url = p.get("url")
        if url in titulos_reais_disco and _eh_nota_titulo(p.get("titulo")):
            p = {**p, "titulo": titulos_reais_disco[url]}
        postados_est.append(p)

    vistos = {(p.get("nome"), p.get("url")) for p in postados_est}
    est["postados"] = postados_est + [
        p for p in disco.get("postados", [])
        if (p.get("nome"), p.get("url")) not in vistos
    ]

    reprovados_unidos = set(est.get("reprovados", [])) | set(disco.get("reprovados", []))
    est["reprovados"] = sorted(
        nome for nome in reprovados_unidos
        if not (FICHAS / nome / "SEM_PALAVRAO.txt").exists()
    )

    est["cortes_postados"] = sorted(set(est.get("cortes_postados", [])) | set(disco.get("cortes_postados", [])))

    presos_disco = dict(disco.get("presos") or {})
    presos_est = dict(est.get("presos") or {})
    presos = {**presos_disco, **presos_est}

    soltar = set(est.pop("presos_soltar", None) or []) | set(disco.get("presos_soltar") or [])
    for nome in soltar:
        info = presos.get(nome)
        if isinstance(info, dict) and info.get("status") == "enviando":
            del presos[nome]

    if presos or "presos" in est or "presos" in disco:
        est["presos"] = presos

    ESTADO.write_text(json.dumps(est, ensure_ascii=False, indent=1), encoding="utf-8")
