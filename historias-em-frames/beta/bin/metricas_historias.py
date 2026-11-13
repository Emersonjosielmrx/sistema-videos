# -*- coding: utf-8 -*-
"""metricas_historias.py — mede no YouTube Studio o que as histórias postadas renderam e alimenta o rodízio de capas.

Adaptado de D:\\hipercool-videos\\bin\\metricas.py. Fonte: os postar.json que a rede do manhwa-react arquiva depois de
subir (D:\\hipercool-materiais\\_postados\\historias\\<gênero>\\<pasta>\\postar.json, campo "postado": video_id, canal_id,
canal_slug, publish_at, thumb). Lê pelo navegador (youtube_studio_extras --metricas; nunca API do Google) as
métricas dos vídeos publicados há 2 a 21 dias e guarda em workspace/metricas.json.

Decide com 7+ dias. As histórias são Shorts: a métrica é VIEWS, contra a mediana das histórias do mesmo canal.
  - CAPA: a capa que subiu (postado.thumb == "navegador") é a variante 1 do capa.capa.json; views acima da mediana =
    vitória da pose (capa_ia_historias.registrar_resultado).
  - TÍTULO: fica de fora. A rede reescreve o título de toda história por canal (medido em 18/10 nos 11 postados),
    então o estilo do seo_generator não é o que foi ao ar.

Roda 1x por dia (o auto_producer chama antes de cada vídeo; a trava de 20 h é aqui dentro).
Manual: python bin/metricas_historias.py [--agora] [--so-decidir]
"""
import json
import statistics
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from hp_common import PROJECT_DIR, log  # noqa: E402

DADOS = PROJECT_DIR / "workspace" / "metricas.json"
POSTADOS = Path(r"D:\hipercool-materiais\_postados\historias")
POSTADOR = Path(r"D:\postador-de-videos\bin")
IDADE_MIN_H = 48
IDADE_MAX_D = 21
RELER_H = 72          # relê a cada 3 dias enquanto o vídeo for novo
DECIDIR_COM_D = 7
POR_RODADA = 6        # cada vídeo abre o Chrome do canal
INTERVALO_H = 20
MIN_AMOSTRA = 3       # vídeos maduros do mesmo canal pra ter mediana


def _ler(p, padrao):
    try:
        return json.loads(Path(p).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return padrao


def _gravar(p, d):
    Path(p).parent.mkdir(parents=True, exist_ok=True)
    tmp = Path(p).with_suffix(".tmp")
    tmp.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    tmp.replace(p)


def _quando(s):
    try:
        d = datetime.fromisoformat(str(s).replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None
    return d if d.tzinfo else d.astimezone()


def _pose_da_capa(pasta, d):
    """Pose da capa que subiu junto com o vídeo, ou None."""
    if (d.get("postado") or {}).get("thumb") != "navegador" or not d.get("thumb"):
        return None
    cj = _ler(pasta / Path(d["thumb"]).with_suffix(".capa.json"), {})
    vs = cj.get("variantes") or []
    return vs[0].get("pose") if vs else None


def _videos():
    out = []
    for pj in POSTADOS.glob("*/*/postar.json"):
        d = _ler(pj, {})
        p = d.get("postado") or {}
        quando = _quando(p.get("publish_at") or p.get("postado_em"))
        if p.get("video_id") and p.get("canal_id") and quando:
            out.append({"vid": p["video_id"], "canal_id": p["canal_id"], "canal": p.get("canal_slug") or p["canal_id"],
                        "quando": quando, "genero": d.get("genero"), "pose": _pose_da_capa(pj.parent, d)})
    return out


def coletar(max_videos=POR_RODADA):
    """Lê no Studio os vídeos que estão na idade de medir. Devolve quantos leu."""
    sys.path.insert(0, str(POSTADOR))
    import youtube_studio_extras as yx
    dados, agora, feitos = _ler(DADOS, {}), datetime.now(timezone.utc), 0
    for v in sorted(_videos(), key=lambda x: x["quando"]):
        if feitos >= max_videos:
            break
        idade_h = (agora - v["quando"]).total_seconds() / 3600
        d = dados.get(v["vid"], {})
        lido = _quando(d.get("lido_em"))
        if idade_h < IDADE_MIN_H or idade_h > IDADE_MAX_D * 24:
            continue
        if lido and (agora - lido).total_seconds() / 3600 < RELER_H:
            continue
        r = yx.rodar(v["canal_id"], video=v["vid"], metricas=True, timeout=900)
        m = r.get("metricas")
        feitos += 1
        base = {**d, "lido_em": agora.isoformat(timespec="minutes"), "idade_h": round(idade_h),
                "canal": v["canal"], "genero": v["genero"], "pose": v["pose"]}
        if isinstance(m, dict) and "aviso" not in m:
            dados[v["vid"]] = {**base, **m}
            dados[v["vid"]].pop("erro", None)
            log(f"  métricas {v['vid']} ({v['canal']}): views {m.get('views')} | continuaram {m.get('continuaram')}")
        else:
            dados[v["vid"]] = {**base, "erro": str(m or r)[:200]}
            log(f"  métricas {v['vid']}: não leu ({str(m or r)[:160]})")
        _gravar(DADOS, dados)
    return feitos


def decidir():
    """Views contra a mediana do canal -> vitória/derrota da pose da capa (uma vez por vídeo)."""
    dados = _ler(DADOS, {})
    por_canal = {}
    for d in dados.values():
        if isinstance(d, dict) and d.get("views") is not None and d.get("idade_h", 0) >= DECIDIR_COM_D * 24:
            por_canal.setdefault(d.get("canal"), []).append(d)
    n = 0
    for lst in por_canal.values():
        if len(lst) < MIN_AMOSTRA:
            continue
        med = statistics.median(d["views"] for d in lst)
        for d in lst:
            if d.get("decidido_capa") or not d.get("pose"):
                continue
            import capa_ia_historias
            capa_ia_historias.registrar_resultado(d["pose"], d["views"] > med)
            d["decidido_capa"] = f"views {d['views']} x mediana {med}"
            n += 1
    _gravar(DADOS, dados)
    return n


def rodar(forcar=False):
    """1 rodada por dia: lê o que estiver na idade e decide o que já tem dados."""
    dados = _ler(DADOS, {})
    ult = _quando(dados.get("_ultima_rodada"))
    if not forcar and ult and (datetime.now(timezone.utc) - ult).total_seconds() / 3600 < INTERVALO_H:
        log("  métricas: já rodou nas últimas 20 h")
        return
    lidos = coletar()
    dados = _ler(DADOS, {})
    dados["_ultima_rodada"] = datetime.now(timezone.utc).isoformat(timespec="minutes")
    _gravar(DADOS, dados)
    n = decidir()
    log(f"  métricas: {lidos} vídeo(s) lido(s) no Studio, {n} resultado(s) de capa registrado(s)")


if __name__ == "__main__":
    import argparse
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description="mede as histórias postadas (Studio pelo navegador) e alimenta as capas")
    ap.add_argument("--agora", action="store_true", help="roda mesmo se já rodou hoje")
    ap.add_argument("--so-decidir", action="store_true", help="não abre o navegador, só decide com o que já leu")
    a = ap.parse_args()
    if a.so_decidir:
        print(decidir(), "resultado(s) registrado(s)")
    else:
        rodar(forcar=a.agora)
