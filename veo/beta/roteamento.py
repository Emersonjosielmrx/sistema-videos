# -*- coding: utf-8 -*-
"""roteamento.py — quem decide o canal de um video do Veo.

RESPOSTA CURTA: nao e este arquivo. E a rede do manhwa-react.

Ate 15/10/2026 este modulo tinha um mapa persona -> handle do YouTube, com 19
handles. Em 16/10 a auditoria conferiu um por um: 18 estavam SUSPENSOS desde
04/09/2026 e o unico vivo (animescomia) esta reservado a rede. O sorteio ainda
usava hash() do Python, que muda a cada processo, entao o mesmo video podia ser
roteado para canais diferentes em execucoes diferentes — e um "or True" deixava
o caminho de "nao sei o canal" inalcancavel.

Hoje quem escolhe o canal e o "diretor da rede" (D:\\manhwa-react\\mr\\rede.py):
ele le o tema e a fala do video, da uma nota de encaixe para cada canal ATIVO de
D:\\postador-de-videos\\config\\rede_canais.json, poe 1 video por canal por dia e
garante que o mesmo video nunca saia em dois canais. Por isso a funcao abaixo
devolve lista vazia: lista vazia = "decida voce", e e exatamente o que queremos.

Ver docs\\PLANO_MELHORIAS_VEO.md, item AB-06.
"""
import hashlib
import json
from pathlib import Path

_REDE_CANAIS = Path(r"D:\postador-de-videos\config\rede_canais.json")

# Compatibilidade: D:\postador-de-videos\bin\agendar_vo3.py (tarefa AgendadorVO3,
# 05:00) faz "return R._DIRETO, R._POOL_HUMOR". Os nomes continuam existindo, mas
# VAZIOS: sem eles o import quebraria a tarefa, e com os handles antigos ela
# rotearia para canais suspensos. Vazio = nenhum canal = nada sobe por ali, que e
# o que vale ate a dona autorizar desligar essa tarefa (item AB-01 do plano).
_DIRETO = {}
_POOL_HUMOR = []


def canais_ativos() -> list:
    """Slugs dos canais ATIVOS da rede, lidos do mapa do postador.

    So para consulta/diagnostico — o roteamento de verdade e da rede."""
    try:
        dados = json.loads(_REDE_CANAIS.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    canais = dados.get("canais") or dados
    if isinstance(canais, dict):
        canais = list(canais.values())
    return sorted(
        str(c.get("slug") or "")
        for c in canais
        if isinstance(c, dict) and str(c.get("status", "")).lower() == "ativo" and c.get("slug")
    )


def escolha_estavel(opcoes: list, chave: str) -> str | None:
    """Escolhe sempre a mesma opcao para a mesma chave (md5, nunca hash()).

    hash() de string e randomizado por processo: a mesma chave daria canais
    diferentes a cada execucao. Regra da dona: md5.
    """
    if not opcoes:
        return None
    n = int(hashlib.md5((chave or "x").encode("utf-8")).hexdigest(), 16)
    return opcoes[n % len(opcoes)]


def canal_para_persona(persona=None, stem=None) -> list:
    """Sempre []. O canal e decidido pelo diretor da rede (mr/rede.py).

    Mantida com a assinatura antiga porque publicar.py ainda chama.
    """
    return []


def todos_canais_reais() -> list:
    """Compatibilidade com quem importava a versao antiga. Hoje: os ativos da rede."""
    return canais_ativos()


if __name__ == "__main__":
    print("roteamento: o canal e decidido pela rede do manhwa-react (mr/rede.py).")
    print("canal_para_persona(...) ->", canal_para_persona("Alienigenas", stem="vid123"))
    ativos = canais_ativos()
    print(f"canais ativos no mapa da rede ({len(ativos)}):", ", ".join(ativos) or "(nenhum)")
