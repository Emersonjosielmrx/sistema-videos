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
    with _TRAVA_EST:
        try:
            return json.loads(ESTADO.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return {"postados": [], "reprovados": []}


def _eh_nota_titulo(titulo):
    return not titulo or not isinstance(titulo, str) or titulo.lstrip().startswith("(")


def _gravar_estado(est):
    """03/11: grava JUNTANDO com o que está no arquivo. Em 02/11 duas rodadas rodaram juntas e a que terminou depois
    gravou a lista que tinha lido de manhã por cima: o post do yKfgs no Fio da Meada sumiu e ele voltou pra fila (quase
    saiu em 3 canais — regra: vídeo único por canal). Postado/reprovado/corte que existir no arquivo nunca se perde."""
    with _TRAVA_EST:
        _gravar_estado_trancado(est)


def _gravar_estado_trancado(est):
    disco = _estado()

    # 1. Postados:
    # Incidente 3: Título que começa com "(" é NOTA provisória: perde para um título de verdade
    # do arquivo para o mesmo url. Título de verdade novo (da rodada) continua valendo.
    # Conserto 03/11: postado que existe no arquivo nunca se perde, e não duplica (mesmo nome+url).
    titulos_reais_disco = {
        p.get("url"): p.get("titulo")
        for p in disco.get("postados", [])
        if isinstance(p, dict) and p.get("url") and not _eh_nota_titulo(p.get("titulo"))
    }

    postados_est = []
    vistos = set()
    for p in est.get("postados", []):
        if isinstance(p, dict):
            url = p.get("url")
            if url in titulos_reais_disco and _eh_nota_titulo(p.get("titulo")):
                p["titulo"] = titulos_reais_disco[url]
            chave = (p.get("nome"), url)
            if chave not in vistos:
                postados_est.append(p)
                vistos.add(chave)
        else:
            postados_est.append(p)

    for p in disco.get("postados", []):
        if isinstance(p, dict):
            chave = (p.get("nome"), p.get("url"))
            if chave not in vistos:
                postados_est.append(p)
                vistos.add(chave)
        else:
            postados_est.append(p)

    est["postados"] = postados_est

    # 2. Reprovados:
    # Incidente 1: ficha com SEM_PALAVRAO.txt está liberada e nunca pode ficar em "reprovados".
    # Conserto 03/11: reprovado que existe no arquivo nunca se perde.
    reprovados_unidos = set(est.get("reprovados", [])) | set(disco.get("reprovados", []))
    est["reprovados"] = sorted(
        nome for nome in reprovados_unidos
        if not (FICHAS / str(nome) / "SEM_PALAVRAO.txt").exists()
    )

    # 3. Cortes postados:
    # Conserto 03/11: corte que existe no arquivo nunca se perde.
    est["cortes_postados"] = sorted(set(est.get("cortes_postados", [])) | set(disco.get("cortes_postados", [])))

    # 4. Presos e Presos a Soltar:
    # Incidente 2: preso marcado por qualquer rodada não pode sumir.
    # Incidente 4: ao gravar, cada nome de presos_soltar (da rodada ou do arquivo) sai de "presos"
    # SÓ se lá o status for "enviando" (preso com "erro" nunca é solto por aqui).
    # "presos_soltar" não fica gravado no arquivo depois de aplicado.
    presos_disco = dict(disco.get("presos") or {})
    presos_est = dict(est.get("presos") or {})

    presos = {}
    todos_nomes = set(presos_disco.keys()) | set(presos_est.keys())
    for nome in todos_nomes:
        info_disco = presos_disco.get(nome)
        info_est = presos_est.get(nome)
        if info_disco is not None and info_est is not None:
            info = {}
            if isinstance(info_disco, dict):
                info.update(info_disco)
            else:
                info["status"] = info_disco
            if isinstance(info_est, dict):
                info.update(info_est)
            else:
                info["status"] = info_est
            status_disco = info_disco.get("status") if isinstance(info_disco, dict) else info_disco
            status_est = info_est.get("status") if isinstance(info_est, dict) else info_est
            if status_disco == "erro" or status_est == "erro":
                info["status"] = "erro"
            presos[nome] = info
        elif info_est is not None:
            presos[nome] = dict(info_est) if isinstance(info_est, dict) else {"status": info_est}
        else:
            presos[nome] = dict(info_disco) if isinstance(info_disco, dict) else {"status": info_disco}

    soltar = set(est.pop("presos_soltar", None) or []) | set(disco.get("presos_soltar") or [])
    for nome in soltar:
        info = presos.get(nome)
        status = info.get("status") if isinstance(info, dict) else info
        if status == "enviando":
            del presos[nome]

    if presos or "presos" in est or "presos" in disco:
        est["presos"] = presos

    ESTADO.write_text(json.dumps(est, ensure_ascii=False, indent=1), encoding="utf-8")
