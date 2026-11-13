# -*- coding: utf-8 -*-
"""limpar_e_processar_novos.py — Limpeza das 4 pastas + processamento dos 112 novos.

Fase 1: Apaga duplicados na raiz de pos_final (315 mp4 sem sufixo)
Fase 2: Limpa pos_producao/tmp/ (6.5GB de temp ffmpeg)
Fase 3: Copia 112 novos do cron_shorts pra veo_videos_iniciais
Fase 4: Gera LIMPO + COMPLETO dos 112 novos
"""
import os
import sys
import shutil
import time
from pathlib import Path

_BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(_BASE))
os.environ.setdefault("PYTHONUTF8", "1")

import centralizar_publicar as cp
from centralizar_publicar import log

DIR_CRON_SHORTS = Path(r"D:\veo\beta\videos_pos\cron_shorts")
DIR_TMP = _BASE / "tmp"


def _escolher_metadados(stem: str):
    slug = stem.rsplit("_", 2)[0] if "_" in stem else stem
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
        "dicas_fitness": ("Dicas Fitness", "Saude e Fitness",
                         "Esse exercicio queima 3x mais que corrida"),
        "fatos_bizarros": ("Fatos Bizarros", "Curiosidades Bizarras",
                          "Isso aconteceu de verdade e ninguem acreditou"),
        "danca_e_musica": ("Danca E Musica", "Danca e Musica",
                           "Esse passo de danca ta viralizando no mundo todo"),
        "tech_news": ("Tech News", "Tecnologia",
                      "Lancamento bombástico que ninguem esperava"),
        "vendas_com_ia": ("Vendas com IA", "Marketing Digital",
                         "Ia vende mais que vendedor experiente"),
        "dicas_de_negoci": ("Dicas de Negocio", "Empreendedorismo",
                            "Esse hack fez uma loja faturar 10x mais"),
        "produtividade": ("Produtividade", "Produtividade",
                          "Pare de perder tempo com isso agora"),
        "fofos_e_absurdo": ("Fofos e Absurdos", "Fofura e Humor",
                            "Esse bichinho fez a coisa mais fofa do mundo"),
        "alucinaai": ("Alucinaai", "Alucinacoes IA",
                      "A IA sonhou isso e ninguem acreditou"),
    }
    if slug in mapa:
        return mapa[slug]
    canal = slug.replace("_", " ").title()
    return canal, canal, f"Descubra o que voce nao sabia sobre {canal}"


_VARIANTES = [
    {"sufixo": "_LIMPO",    "subpasta": "limpo",    "com_propaganda": False, "com_vo3_propaganda": False},
    {"sufixo": "_COMPLETO", "subpasta": "completo", "com_propaganda": True,  "com_vo3_propaganda": True},
]


def fase1_apagar_duplicados_raiz():
    """Apaga mp4 sem sufixo na raiz de pos_final (são duplicados dos que já estão em limpo/)."""
    base = cp.DIR_POS_FINAL
    apagados = 0
    bytes_liberados = 0

    for f in sorted(base.glob("*.mp4")):
        if f.parent != base:
            continue
        nome = f.name
        if "_LIMPO" in nome or "_COMPLETO" in nome or "_VO3" in nome or "_ESTATICA" in nome:
            continue
        sz = f.stat().st_size
        f.unlink()
        apagados += 1
        bytes_liberados += sz

    log(f"FASE 1: {apagados} duplicados apagados da raiz ({bytes_liberados / 1024**2:.0f} MB)")

    for f in base.glob("*.pos.json"):
        f.unlink()

    return apagados


def fase2_limpar_tmp():
    """Limpa pos_producao/tmp/ (temp ffmpeg)."""
    if not DIR_TMP.exists():
        log("FASE 2: tmp/ nao existe, skip")
        return 0

    bytes_liberados = 0
    apagados = 0

    for f in DIR_TMP.iterdir():
        if f.is_file():
            bytes_liberados += f.stat().st_size
            f.unlink()
            apagados += 1

    log(f"FASE 2: {apagados} arquivos temp apagados ({bytes_liberados / 1024**3:.1f} GB)")
    return apagados


def fase3_copiar_novos_cron_shorts():
    """Copia mp4 do cron_shorts que não existem em veo_videos_iniciais."""
    if not DIR_CRON_SHORTS.exists():
        log("FASE 3: cron_shorts nao existe, skip")
        return []

    novos = []
    for f in sorted(DIR_CRON_SHORTS.glob("*.mp4")):
        if f.stat().st_size < 50_000:
            continue
        dest = cp.DIR_INICIAIS / f.name
        if not dest.exists():
            shutil.copy2(str(f), str(dest))
            novos.append(dest)

    log(f"FASE 3: {len(novos)} novos copiados de cron_shorts -> veo_videos_iniciais")
    return novos


def fase4_gerar_variantes(videos: list[Path]):
    """Gera LIMPO + COMPLETO pra cada vídeo novo."""
    from montar_final import montar

    dir_limpo = cp.DIR_POS_FINAL / "limpo"
    dir_completo = cp.DIR_POS_FINAL / "completo"
    dir_limpo.mkdir(exist_ok=True)
    dir_completo.mkdir(exist_ok=True)

    pendentes = []
    for v in videos:
        todas_ok = True
        for var in _VARIANTES:
            out = cp.DIR_POS_FINAL / var["subpasta"] / f"{v.stem}{var['sufixo']}.mp4"
            if not out.exists() or out.stat().st_size < 50_000:
                todas_ok = False
                break
        if not todas_ok:
            pendentes.append(v)

    log(f"FASE 4: {len(pendentes)} pendentes de {len(videos)} novos")
    log("=" * 60)

    inicio = time.time()
    processados = 0
    erros = 0

    for v in pendentes:
        elapsed = time.time() - inicio
        stem = v.stem
        canal, tema, fala = _escolher_metadados(stem)
        log(f"[{processados+1}/{len(pendentes)}] {v.name}  canal={canal}  ({elapsed:.0f}s)")

        ok_count = 0
        for var in _VARIANTES:
            sufixo = var["sufixo"]
            dir_out = cp.DIR_POS_FINAL / var["subpasta"]
            out = dir_out / f"{stem}{sufixo}.mp4"
            if out.exists() and out.stat().st_size > 50_000:
                ok_count += 1
                continue

            try:
                t0 = time.time()
                meta = montar(
                    str(v), str(out), canal, tema, fala,
                    voz="auto", formato_cta="slide",
                    com_propaganda=var["com_propaganda"],
                    com_vo3_propaganda=var["com_vo3_propaganda"],
                )
                dt = time.time() - t0
                ok = meta.get("ok") if isinstance(meta, dict) else bool(meta)
                if ok:
                    sz = out.stat().st_size // 1024
                    log(f"    {sufixo}: OK ({sz}KB, {dt:.0f}s)")
                    ok_count += 1
                else:
                    log(f"    {sufixo}: FALHOU")
                    erros += 1
            except Exception as e:
                log(f"    {sufixo}: ERRO {str(e)[:80]}")
                erros += 1

        if ok_count > 0:
            processados += 1

        if processados % 20 == 0 and processados > 0:
            elapsed = time.time() - inicio
            rate = processados / (elapsed / 60) if elapsed > 0 else 0
            restam = len(pendentes) - processados
            eta_min = restam / rate if rate > 0 else 0
            log(f"--- RITMO: {processados}/{len(pendentes)} ({erros} erros) {rate:.1f}/min  ETA ~{eta_min:.0f}min ---")

    elapsed = time.time() - inicio
    log("=" * 60)
    log(f"FASE 4 FINALIZADA: {processados} OK, {erros} erros em {elapsed/60:.1f}min")


def main():
    log("=" * 60)
    log("LIMPEZA DAS 4 PASTAS + PROCESSAR NOVOS")
    log("=" * 60)

    log("\n>>> FASE 1: Apagar duplicados sem sufixo na raiz de pos_final")
    fase1_apagar_duplicados_raiz()

    log("\n>>> FASE 2: Limpar pos_producao/tmp/")
    fase2_limpar_tmp()

    log("\n>>> FASE 3: Copiar novos do cron_shorts pra veo_videos_iniciais")
    novos = fase3_copiar_novos_cron_shorts()

    if novos:
        log(f"\n>>> FASE 4: Gerar LIMPO + COMPLETO dos {len(novos)} novos")
        fase4_gerar_variantes(novos)
    else:
        log("\n>>> FASE 4: Nenhum novo pra processar")

    log("\n>>> RESULTADO FINAL:")
    n_limpo = len(list((cp.DIR_POS_FINAL / "limpo").glob("*.mp4")))
    n_completo = len(list((cp.DIR_POS_FINAL / "completo").glob("*.mp4")))
    n_iniciais = len(list(cp.DIR_INICIAIS.glob("*.mp4")))
    log(f"  veo_videos_iniciais = {n_iniciais} videos")
    log(f"  pos_final/limpo/    = {n_limpo} videos")
    log(f"  pos_final/completo/ = {n_completo} videos")
    log("PRONTO!")


if __name__ == "__main__":
    main()
