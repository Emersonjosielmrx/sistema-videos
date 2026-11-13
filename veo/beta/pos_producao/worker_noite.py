# -*- coding: utf-8 -*-
"""worker_noite.py — processa a pos-producao de cada video VEO novo, sem parar.

Roda em loop ate o PC desligar. Fontes que ele observa:
  (1) D:\\veo\\beta\\videos\\cron_shorts\\*.mp4  -> acabou de sair do Veo
  (2) D:\\hipercool-materiais\\_postados\\vo3\\*.mp4  -> ja foi postado no YouTube
      (tambem processa: versao pos e' a que a galera tem orgulho)

Para cada novo MP4:
  - se ja existe a versao pos em hieprcoll-materiais/veo/pos/<stem>.mp4 -> skip
  - chama montar_final.montar() e grava no diretorio central
  - move a fonte pra hieprcoll-materiais/veo/ja_feitos/<stem>.mp4
  - loga tudo

Tambem roda em paralelo um health-check de 30min: se a OmniRoute destravar
o Gemini (resolver o 429/402), limpa os caches do circuit-breaker e os
cards antigos pra re-tentar em alta qualidade.

Uso:
    python worker_noite.py                  (loop infinito)
    python worker_noite.py --once           (1 passada e sai, p/ teste)
    python worker_noite.py --max N          (so processa N videos e sai)
"""
import argparse
import json
import os
import shutil
import sys
import time
from pathlib import Path

# Adiciona pos_producao ao path
_BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(_BASE))
sys.path.insert(0, str(_BASE.parent))
import sem_janela  # noqa: F401,E402  (filhos sem janela na tela - dono, 15/10; item BX-02)

import centralizar_publicar as cp  # noqa: E402
from centralizar_publicar import log  # noqa: E402

_FONTES_OBSERVADAS = [
    cp.ORIGEM_CRON_VEO,
    cp.ORIGEM_POSTADOS,
]

_HEALTH_ARQ = cp.DIR_LOGS / "omniroute_health.json"
_HEALTH_INTERVALO_S = 30 * 60   # 30 min, conforme pedido
_WORKER_INTERVALO_S = 30        # checa novos a cada 30s

# cache do gerador (formula de cada video: prompt/foto/cenario/score/cta)
_CACHE_GERADOR = Path(r"D:\veo\beta\logs\video_cache.json")
_cache_idx = None  # stem -> item do cache (lazy)


def _idx_cache():
    """Indexa o cache do gerador por STEM do video (do campo video_path).
    Lazy + cacheado em processo. Vazio se o arquivo nao existir."""
    global _cache_idx
    if _cache_idx is None:
        _cache_idx = {}
        try:
            dados = json.loads(_CACHE_GERADOR.read_text(encoding="utf-8"))
            for it in dados:
                vp = it.get("video_path") or ""
                st = Path(vp).stem
                if st:
                    _cache_idx[st] = it
        except Exception:
            _cache_idx = {}
    return _cache_idx


def _gravar_sidecar(video_in: Path, out_mp4: Path, meta: dict, dt: float):
    """Grava <stem>.pos.json ao lado do mp4 pos com rastreabilidade completa:
    o que a POS aplicou (efeitos/produto/voz) + a FORMULA da geracao
    (prompt/foto/cenario/score) puxada do cache do gerador. Torna o video
    replicavel e os erros/acertos auditaveis."""
    stem = video_in.stem
    ger = _idx_cache().get(stem, {})
    doc = {
        "stem": stem,
        "gerado_em": ger.get("ts"),
        "processado_em": time.strftime("%Y-%m-%d %H:%M:%S"),
        "duracao_pos_s": round(dt, 1),
        "arquivo_pos": out_mp4.name,
        # --- GERACAO (como o video base nasceu) ---
        "geracao": {
            "canal": ger.get("canal") or meta.get("canal"),
            "tema": ger.get("tema") or meta.get("tema"),
            "fala": ger.get("fala") or meta.get("fala"),
            "cenario": ger.get("cenario"),
            "prompt_final": ger.get("prompt_final"),
            "foto": ger.get("foto"),
            "score": ger.get("score"),
            "iteracoes": ger.get("iteracoes"),
            "fonte": ger.get("fonte"),
            "cta_gerador": ger.get("cta"),
            "hook_family": ger.get("hook_family"),
        },
        # --- POS-PRODUCAO (o que aplicamos por cima) ---
        "pos": {
            "efeitos": meta.get("efeitos"),
            "propaganda": meta.get("propaganda"),
            "voz": meta.get("voz"),
            "formato_cta": meta.get("formato_cta"),
            "avisos": meta.get("avisos"),
        },
    }
    side = out_mp4.with_suffix(".pos.json")
    side.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")


def _ja_processado(stem: str) -> bool:
    """True se ja existe AMBAS variantes (limpo + completo) pra esse stem."""
    for var in _VARIANTES:
        out = cp.DIR_POS_FINAL / var["subpasta"] / f"{stem}{var['sufixo']}.mp4"
        if not out.exists() or out.stat().st_size < 50_000:
            return False
    return True


def _escolher_metadados(stem: str):
    """Infere canal/tema/fala a partir do stem (slug -> nome humano)."""
    # O nome do stem segue padrao: "<slug>_<YYYYMMDD>_<HHMMSS>".
    # Sem acesso a um LLM aqui (rapido), inferimos a partir do slug.
    slug = stem.rsplit("_", 2)[0] if "_" in stem else stem
    # mapeamento simples; o resto cai no default do roteamento
    mapa = {
        "alienigenas": ("Alienigenas", "ETs em Situacoes Engracadas",
                        "ETs roubam nosso wifi de madrugada e nem pagam a conta"),
        "dicas_financeir": ("Dicas Financeiras", "Educacao Financeira",
                            "O banco esconde esse erro que destroi seu salario todo mes"),
        "curiosidades_ia": ("Curiosidades IA", "Fatos Rapidos Chocantes",
                            "Voce nao vai acreditar no que a IA descobriu ontem"),
        "agenda_ia": ("Agenda IA", "Produtividade com IA",
                      "Sua agenda lota sozinha enquanto voce dorme"),
        "cerebro_digital": ("Cerebro Digital", "Tecnologia e IA",
                            "Seu cerebro nao e tao unico quanto voce pensa"),
        "segredos_do_oce": ("Segredos do Oceano", "Mundo Animal",
                            "Tem um monstro la embaixo que a ciencia nao explica"),
        "e_se...": ("E Se...", "Curiosidades Hipoteticas",
                    "E se a gravidade sumisse por 5 segundos?"),
        "super_slow_ia": ("Super Slow IA", "Videos Satisfatorios",
                         "Veja coisas absurdas em camera superlenta"),
        "corpo_humano": ("Corpo Humano", "Ciencia do Corpo",
                         "Seu corpo faz isso agora e voce nem sabe"),
        "robos_desastrad": ("Robos Desastrados", "Videos Engracados com IA",
                            "Robo tenta ajudar e quebra a casa inteira"),
        "stand-up_ia": ("Stand Up IA", "Humor com IA",
                        "Ia comediante tenta fazer piada e falha bonito"),
        "aulas_ia": ("Aulas IA", "Educacao com IA",
                     "Professor IA explica tudo em 2 minutos"),
        "motivacao_ia": ("Motivacao IA", "Frases Motivacionais",
                         "Voce ja tentou mais do que 90% das pessoas"),
        "noticias_de_ia": ("Noticias de IA", "Tech News",
                          "Ia nova lancada ontem muda tudo"),
        "cassetadas_ia": ("Cassetadas IA", "Videos Engracados com IA",
                         "Ia tenta limpar a casa e arruma uma bagunca maior"),
    }
    if slug in mapa:
        return mapa[slug]
    # default: usa o slug como canal
    canal = slug.replace("_", " ").title()
    return canal, canal, f"Descubra o que voce nao sabia sobre {canal}"


# 2 variantes por video cru: LIMPO (subpasta limpo/) e COMPLETO (subpasta completo/)
_VARIANTES = [
    {"sufixo": "_LIMPO",    "subpasta": "limpo",    "com_propaganda": False, "com_vo3_propaganda": False},
    {"sufixo": "_COMPLETO", "subpasta": "completo", "com_propaganda": True,  "com_vo3_propaganda": True},
]


def _processar_um(video_in: Path) -> bool:
    """Roda a pos de 1 video gerando 2 variantes (limpo + completo).
    True se pelo menos 1 variante gerou."""
    stem = video_in.stem
    if _ja_processado(stem):
        return False

    canal, tema, fala = _escolher_metadados(stem)
    from montar_final import montar

    log(f"  -> pos 2-variantes: {video_in.name}  canal={canal}")
    ok_count = 0

    for var in _VARIANTES:
        sufixo = var["sufixo"]
        subpasta = var["subpasta"]
        var_stem = f"{stem}{sufixo}"
        dir_out = cp.DIR_POS_FINAL / subpasta
        dir_out.mkdir(exist_ok=True)
        out = dir_out / f"{var_stem}.mp4"
        if out.exists() and out.stat().st_size > 50_000:
            log(f"     {sufixo}: ja existe, skip")
            ok_count += 1
            continue

        try:
            t0 = time.time()
            meta = montar(
                str(video_in), str(out), canal, tema, fala,
                voz="auto", formato_cta="slide",
                com_propaganda=var["com_propaganda"],
                com_vo3_propaganda=var["com_vo3_propaganda"],
            )
            dt = time.time() - t0
            ok = meta.get("ok") if isinstance(meta, dict) else bool(meta)
            if ok:
                log(f"     {sufixo}: OK ({out.stat().st_size // 1024}KB, {dt:.1f}s)")
                ok_count += 1
                try:
                    _gravar_sidecar(video_in, out, meta if isinstance(meta, dict) else {}, dt)
                except Exception as e:
                    log(f"     {sufixo} sidecar: {str(e)[:60]}")
            else:
                log(f"     {sufixo}: FALHOU")
        except Exception as e:
            log(f"     {sufixo}: ERRO {str(e)[:80]}")

    if ok_count == 0:
        return False

    log(f"  -> {ok_count}/2 variantes OK pra {stem}")

    try:
        origem = video_in.resolve().parent
        eh_postados = origem == cp.ORIGEM_POSTADOS.resolve()
        if eh_postados:
            log(f"     -> origem _postados/vo3: fonte PRESERVADA (nao move)")
        else:
            dest = cp.ja_feitos_path(stem)
            shutil.move(str(video_in), str(dest))
            log(f"     -> movido pra ja_feitos/{dest.name}")
    except Exception as e:
        log(f"  AVISO move fonte: {e}")
    return True


_proxima_health = 0.0  # epoch do proximo health-check (setado no main)


def _talvez_health():
    """Roda o health-check de imagem se ja deu o intervalo de 30 min.
    Chamado ENTRE videos pra nao ficar preso atras da fila gigante."""
    global _proxima_health
    if _proxima_health and time.time() >= _proxima_health:
        log("[health] rodada de 30 min - testando OmniRoute...")
        _health_imagem_forcado()
        _proxima_health = time.time() + _HEALTH_INTERVALO_S


def _processar_fila(limite: int | None) -> int:
    """Varre as fontes, processa o que tem. Retorna qtd processada."""
    processados = 0
    for fonte in _FONTES_OBSERVADAS:
        if not fonte.exists():
            continue
        for v in sorted(fonte.glob("*.mp4")):
            if v.stat().st_size < 50_000:
                continue   # tiny/corrompido
            _talvez_health()   # health entre videos (nao espera esvaziar fila)
            if _processar_um(v):
                processados += 1
                if limite and processados >= limite:
                    return processados
    return processados


def _health_imagem_forcado():
    """Tenta uma chamada leve ao gateway; se Gemini responde, marca ok."""
    try:
        # primeira: limpa o circuit breaker do omniroute_image (variavel global)
        import omniroute_image as oi
        oi._exhausted = False
        oi._exhausted_at = 0.0

        # teste HONESTO: premium_only pula o Pollinations, entao so retorna
        # True se Gemini/FLUX responderam de verdade (a imagem de alta qualidade).
        from pathlib import Path
        tmp = cp.DIR_LOGS / "_healthcheck.png"
        ok = oi._generate(
            "Vertical 1080x1920 simple gradient background, "
            "deep purple, no text, no logos",
            tmp, premium_only=True)
        fonte = getattr(oi, "_ultima_fonte", None)
        if ok and tmp.exists() and tmp.stat().st_size > 5000:
            log(f"  [health] PREMIUM DISPONIVEL agora (fonte={fonte}) <<< re-tentando alta qualidade")
            _HEALTH_ARQ.write_text(json.dumps({
                "ts": time.time(), "ok": True, "fonte": fonte,
                "tam": tmp.stat().st_size,
            }), encoding="utf-8")
            tmp.unlink(missing_ok=True)
            return True
        log("  [health] premium ainda bloqueado (segue no Pollinations)")
        _HEALTH_ARQ.write_text(json.dumps({
            "ts": time.time(), "ok": False, "fonte": fonte,
        }), encoding="utf-8")
        return False
    except Exception as e:
        log(f"  [health] erro: {e}")
        return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--once", action="store_true", help="1 passada e sai")
    ap.add_argument("--max", type=int, default=0, help="max videos (0 = sem limite)")
    ap.add_argument("--intervalo", type=int, default=_WORKER_INTERVALO_S,
                    help=f"segundos entre checagens (default {_WORKER_INTERVALO_S})")
    ap.add_argument("--health-em", type=int, default=0,
                    help="roda health check de imagem na inicializacao")
    args = ap.parse_args()

    cp.garantir_layout()
    log("=" * 60)
    log(f"worker_noite iniciando  once={args.once} max={args.max}")
    log(f"fontes observadas:")
    for f in _FONTES_OBSERVADAS:
        log(f"  {f}  (existe={f.exists()})")
    log(f"saida pos em: {cp.DIR_POS_FINAL}")
    log("=" * 60)

    global _proxima_health
    if args.health_em > 0:
        _health_imagem_forcado()
    # agenda o proximo health; _processar_fila dispara ENTRE videos
    _proxima_health = time.time() + _HEALTH_INTERVALO_S

    while True:
        n = _processar_fila(args.max if args.max else None)
        if args.once:
            log(f"passada unica: {n} processados")
            return
        if args.max and n >= args.max:
            log(f"atingiu max={args.max}: {n} processados, saindo")
            return
        _talvez_health()  # tambem checa quando a fila esvazia
        time.sleep(args.intervalo)


if __name__ == "__main__":
    main()