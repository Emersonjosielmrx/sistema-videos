# -*- coding: utf-8 -*-
# COMUM — fonte única: D:\hipercool-materiais\comum\placar_titulos.py. Mudou esta cópia? python D:\hipercool-materiais\bin\recursos.py subir placar_titulos.py --de <projeto>
"""placar_titulos.py — UM aprendizado de estilo de título pra todos os projetos de vídeo.

Antes (até 20/10) hipercool seo.py, recapd e historias seo_generator.py tinham cada um seu titulos_estilos.json — e
os três estavam ZERADOS: cada um aprendia sozinho com pouca amostra e quase ninguém registrava resultado. Agora:
- escolher(estilos): Thompson sobre o placar GERAL (busca / provocacao / curiosidade valem pra todos);
- registrar(estilo, venceu, projeto, idioma, video_id): conta 1 vez por vídeo; guarda também por projeto e idioma
  (pra o dono ver se um estilo só ganha numa língua/num tipo de canal).
Quem registra: hipercool metricas.py (CTR contra a mediana dos completos do canal) e o placar comum de 48 h
(notificar_telegram.medir_48h: views em 48 h contra a mediana do canal, pra todo vídeo com estilo_titulo na ficha).
"""
import json
import random
from pathlib import Path

STATS = Path(r"D:\postador-de-videos\_analise\titulos_estilos.json")
MAX_MEDIDOS = 3000


def ler():
    try:
        return json.loads(STATS.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def escolher(estilos):
    """Thompson: Beta(vitórias+1, derrotas+1) por estilo no placar geral; sem dados = rodízio aleatório."""
    s = ler().get("estilos", {})
    return max(estilos, key=lambda e: random.betavariate(
        s.get(e, {}).get("vitorias", 0) + 1, s.get(e, {}).get("testes", 0) - s.get(e, {}).get("vitorias", 0) + 1))


def registrar(estilo, venceu, projeto="", idioma="", video_id=""):
    """True se contou; False se sem estilo ou se esse vídeo já foi contado."""
    if not estilo:
        return False
    s = ler()
    medidos = s.setdefault("medidos", {})
    if video_id and video_id in medidos:
        return False
    grupos = [s.setdefault("estilos", {})]
    if projeto:
        grupos.append(s.setdefault("por_projeto", {}).setdefault(projeto, {}))
    if idioma:
        grupos.append(s.setdefault("por_idioma", {}).setdefault(idioma, {}))
    for g in grupos:
        d = g.setdefault(estilo, {"testes": 0, "vitorias": 0})
        d["testes"] += 1
        d["vitorias"] += float(venceu or 0)  # 23/10: empate com a mediana = 0,5 (era derrota)
    if video_id:
        medidos[video_id] = {"estilo": estilo, "venceu": bool(venceu), "projeto": projeto}
        for k in list(medidos)[:-MAX_MEDIDOS]:
            del medidos[k]
    s["_leia"] = ("Placar ÚNICO dos estilos de título (todos os projetos). Gerado por placar_titulos.py (COMUM); "
                  "não editar à mão.")
    return _salvar(STATS, s)


def _salvar(arq, s):
    try:  # PC2/desktop recebem o bin/ por cópia e não têm a pasta do postador: lá não registra
        arq.parent.mkdir(parents=True, exist_ok=True)
        tmp = arq.with_suffix(".tmp")
        tmp.write_text(json.dumps(s, ensure_ascii=False, indent=1), encoding="utf-8")
        tmp.replace(arq)
    except OSError:
        return False
    return True


# ─── placares de outras escolhas (21/10): fonte do parceiro, pose da capa — mesmo mecanismo do título ────────────
def _arq(placar):
    return STATS.parent / f"placar_{placar}.json"


def registrar_item(placar, grupo, item, venceu, video_id=""):
    """Ex.: registrar_item("fontes", "parceiro", "kaijinre", True, vid). 1 contagem por vídeo. True se contou."""
    if not item:
        return False
    try:
        s = json.loads(_arq(placar).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        s = {}
    medidos = s.setdefault("medidos", {})
    if video_id and video_id in medidos:
        return False
    d = s.setdefault("grupos", {}).setdefault(grupo, {}).setdefault(item, {"testes": 0, "vitorias": 0})
    d["testes"] += 1
    d["vitorias"] += float(venceu or 0)  # 23/10: empate com a mediana = 0,5 (era derrota)
    if video_id:
        medidos[video_id] = 1
        for k in list(medidos)[:-MAX_MEDIDOS]:
            del medidos[k]
    return _salvar(_arq(placar), s)


def taxas(placar, grupo):
    """{item: (testes, vitorias)} do grupo; {} sem dados."""
    try:
        g = json.loads(_arq(placar).read_text(encoding="utf-8")).get("grupos", {}).get(grupo, {})
    except (OSError, ValueError):
        return {}
    return {k: (v.get("testes", 0), v.get("vitorias", 0)) for k, v in g.items()}
