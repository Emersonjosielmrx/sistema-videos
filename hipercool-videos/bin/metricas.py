# -*- coding: utf-8 -*-
"""metricas.py — MEDE o que rende e alimenta os rodízios (pendente antigo do dono: "testar todas e medir qual tem
as melhores respostas"; títulos "temos que fazer um estudo disso também").

Lê no YouTube Studio, PELO NAVEGADOR (youtube_studio_extras --metricas; nunca API do Google), as métricas dos vídeos
LONGOS postados há 2+ dias (completo de capítulo e compilado 16:9; Shorts não): impressões, CTR, visualizações,
duração média e retenção aos 30 s. Guarda em workspace/metricas.json e decide, com 7+ dias de dados:
  - compilado com fala de voz humana (intro_voz / intro_meio no estado da postagem): retenção aos 30 s acima da
    mediana dos compilados medidos = vitória da fala (intros_voz.registrar_resultado);
  - completo com estilo de título (estilo_titulo): CTR acima da mediana dos completos do mesmo canal, com
    impressões suficientes = vitória do estilo (seo.registrar_resultado).
Teste A/B de capa: o canal pt está com recursos avançados negados até 14/11/2026 (ver docs/PEDIDOS...), então não
há vencedora pra ler ainda.
Roda 1x por dia dentro da postagem (fila.postagem). Manual: python bin/metricas.py [--agora] [--so-decidir]
"""
import json
import statistics
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from hp_common import PROJECT_DIR, log  # noqa: E402

DADOS = PROJECT_DIR / "workspace" / "metricas.json"
ESTADOS = PROJECT_DIR / "workspace" / "postagens"
POSTADOR = Path(r"D:\postador-de-videos\bin")
TIPOS = ("completo", "longo")  # Shorts têm outra métrica (deslizou x assistiu): fora por enquanto
IDADE_MIN_H = 48
IDADE_MAX_D = 21
RELER_H = 72          # relê a cada 3 dias enquanto o vídeo for novo
DECIDIR_COM_D = 7     # decide com pelo menos 7 dias de dados
POR_RODADA = 6        # vídeos lidos por rodada (cada um abre o Chrome do canal)
INTERVALO_H = 20      # 1 rodada por dia
MIN_IMPRESSOES = 100
MIN_AMOSTRA = 3       # precisa de 3+ vídeos medidos pra ter mediana


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


def _videos():
    """[(id, canal, chave, item)] dos vídeos longos postados (com url) em todos os estados de postagem."""
    out = []
    for f in ESTADOS.glob("*.json"):
        if f.name.startswith("_"):
            continue
        canal_arq = f.stem.split("__")[-1] if "__" in f.stem else None
        for chave, it in _ler(f, {}).items():
            if chave not in TIPOS or not isinstance(it, dict) or not it.get("url") or not it.get("em"):
                continue
            vid = it["url"].rstrip("/").split("/")[-1].split("=")[-1]
            out.append((vid, it.get("canal") or canal_arq, chave, it))
    return out


def coletar(max_videos=POR_RODADA):
    """Lê no Studio os vídeos que estão na idade de medir. Devolve quantos leu."""
    sys.path.insert(0, str(POSTADOR))
    import youtube_studio_extras as yx
    dados, agora, feitos = _ler(DADOS, {}), datetime.now(), 0
    for vid, canal, chave, it in sorted(_videos(), key=lambda x: x[3]["em"]):
        if feitos >= max_videos:
            break
        idade_h = (agora - datetime.fromisoformat(it["em"])).total_seconds() / 3600
        d = dados.get(vid, {})
        if idade_h < IDADE_MIN_H or idade_h > IDADE_MAX_D * 24 or not canal:
            continue
        if d.get("lido_em") and (agora - datetime.fromisoformat(d["lido_em"])).total_seconds() / 3600 < RELER_H:
            continue
        r = yx.rodar(canal, video=vid, metricas=True, timeout=900)
        m = r.get("metricas")
        feitos += 1
        if not isinstance(m, dict):
            log(f"  métricas {vid}: não leu ({str(r)[:160]})")
            dados[vid] = {**d, "erro": str(r)[:200], "lido_em": agora.isoformat(timespec="minutes")}
        else:
            dados[vid] = {**d, **m, "lido_em": agora.isoformat(timespec="minutes"), "idade_h": round(idade_h),
                          "chave": chave, "canal": canal, "estilo": it.get("estilo_titulo"),
                          "intro_voz": it.get("intro_voz"), "intro_meio": it.get("intro_meio")}
            dados[vid].pop("erro", None)
            log(f"  métricas {vid} ({chave}): views {m.get('views')} | impressões {m.get('impressoes')} | "
                f"CTR {m.get('ctr')} | retenção 30 s {m.get('ret30')}")
        _gravar(DADOS, dados)
    return feitos


def decidir():
    """Transforma as métricas lidas em vitória/derrota de fala de abertura e de estilo de título (uma vez por vídeo)."""
    dados = _ler(DADOS, {})
    videos = {v: d for v, d in dados.items() if isinstance(d, dict) and not v.startswith("_")}
    maduros = lambda d: d.get("idade_h", 0) >= DECIDIR_COM_D * 24  # noqa: E731
    n = 0
    comps = {v: d for v, d in videos.items() if d.get("chave") == "longo" and d.get("ret30") is not None}
    if len(comps) >= MIN_AMOSTRA:
        import intros_voz
        med = statistics.median(d["ret30"] for d in comps.values())
        for d in comps.values():
            if d.get("decidido_intro") or not maduros(d):
                continue
            for k in ("intro_voz", "intro_meio"):
                if d.get(k):
                    intros_voz.registrar_resultado(d[k], d["ret30"] > med)
                    n += 1
            d["decidido_intro"] = f"ret30 {d['ret30']} x mediana {med}"
    por_canal = {}
    for d in videos.values():
        if d.get("chave") == "completo" and d.get("ctr") is not None and (d.get("impressoes") or 0) >= MIN_IMPRESSOES:
            por_canal.setdefault(d.get("canal"), []).append(d)
    for lst in por_canal.values():
        if len(lst) < MIN_AMOSTRA:
            continue
        import seo
        med = statistics.median(d["ctr"] for d in lst)
        for d in lst:
            if d.get("decidido_titulo") or not d.get("estilo") or not maduros(d):
                continue
            seo.registrar_resultado(d["estilo"], d["ctr"] > med)
            d["decidido_titulo"] = f"ctr {d['ctr']} x mediana {med}"
            n += 1
    _gravar(DADOS, dados)
    return n


def rodar(forcar=False):
    """1 rodada por dia: lê o que estiver na idade e decide o que já tem dados."""
    dados = _ler(DADOS, {})
    ult = dados.get("_ultima_rodada")
    if not forcar and ult and (datetime.now() - datetime.fromisoformat(ult)).total_seconds() / 3600 < INTERVALO_H:
        return
    lidos = coletar()
    dados = _ler(DADOS, {})
    dados["_ultima_rodada"] = datetime.now().isoformat(timespec="minutes")
    _gravar(DADOS, dados)
    n = decidir()
    log(f"  métricas: {lidos} vídeo(s) lido(s) no Studio, {n} resultado(s) registrado(s) nos rodízios")


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="mede o que rende (Studio pelo navegador) e alimenta os rodízios")
    ap.add_argument("--agora", action="store_true", help="roda mesmo se já rodou hoje")
    ap.add_argument("--so-decidir", action="store_true", help="não abre o navegador, só decide com o que já leu")
    a = ap.parse_args()
    if a.so_decidir:
        print(decidir(), "resultado(s) registrado(s)")
    else:
        rodar(forcar=a.agora)
