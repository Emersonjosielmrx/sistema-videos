# -*- coding: utf-8 -*-
"""reorganizar_e_completo.py — reorganiza pos_final e gera versão COMPLETA.

Fase 1: Move _LIMPO pra pos_final/limpo/, apaga _VO3 e _ESTATICA avulsos
Fase 2: Gera _COMPLETO (VO3 + estática juntas) em pos_final/completo/

Resultado final:
  pos_final/limpo/     → vídeos limpos sem propaganda
  pos_final/completo/  → vídeos com VO3 clip + card CTA estática juntos
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


def fase1_reorganizar():
    """Move LIMPO pra subpasta, apaga VO3 e ESTATICA avulsos."""
    base = cp.DIR_POS_FINAL
    dir_limpo = base / "limpo"
    dir_limpo.mkdir(exist_ok=True)

    movidos = 0
    apagados = 0

    for f in sorted(base.glob("*_LIMPO.mp4")):
        dest = dir_limpo / f.name
        if not dest.exists():
            shutil.move(str(f), str(dest))
            movidos += 1
        else:
            f.unlink()
            apagados += 1

    log(f"FASE 1a: {movidos} LIMPO movidos pra limpo/, {apagados} duplicados removidos")

    apagados_vo3 = 0
    apagados_est = 0
    for f in sorted(base.glob("*_VO3.mp4")):
        f.unlink()
        apagados_vo3 += 1
    for f in sorted(base.glob("*_ESTATICA.mp4")):
        f.unlink()
        apagados_est += 1

    # apagar sidecars .pos.json tambem
    for f in base.glob("*.pos.json"):
        f.unlink()

    log(f"FASE 1b: {apagados_vo3} VO3 + {apagados_est} ESTATICA apagados")
    log(f"Espaco liberado estimado: ~{(apagados_vo3 * 4.5 + apagados_est * 3.7):.0f} MB")


def fase2_gerar_completos():
    """Gera versão COMPLETA (VO3 + estática juntas) pra cada vídeo cru."""
    from montar_final import montar

    dir_completo = cp.DIR_POS_FINAL / "completo"
    dir_completo.mkdir(exist_ok=True)

    todos = sorted(cp.DIR_INICIAIS.glob("*.mp4"))
    pendentes = []
    for v in todos:
        if v.stat().st_size < 50_000:
            continue
        out = dir_completo / f"{v.stem}_COMPLETO.mp4"
        if out.exists() and out.stat().st_size > 50_000:
            continue
        pendentes.append(v)

    log(f"FASE 2: {len(pendentes)} COMPLETOS pendentes de {len(todos)} crus")
    log(f"Saida: {dir_completo}")
    log("=" * 60)

    inicio = time.time()
    processados = 0
    erros = 0

    for v in pendentes:
        elapsed = time.time() - inicio
        stem = v.stem
        canal, tema, fala = _escolher_metadados(stem)
        out = dir_completo / f"{stem}_COMPLETO.mp4"

        log(f"[{processados+1}/{len(pendentes)}] {v.name}  canal={canal}  ({elapsed:.0f}s)")

        try:
            t0 = time.time()
            meta = montar(
                str(v), str(out), canal, tema, fala,
                voz="auto", formato_cta="slide",
                com_propaganda=True,
                com_vo3_propaganda=True,
            )
            dt = time.time() - t0
            ok = meta.get("ok") if isinstance(meta, dict) else bool(meta)
            if ok:
                sz = out.stat().st_size // 1024
                log(f"    COMPLETO: OK ({sz}KB, {dt:.0f}s)")
                processados += 1
            else:
                log(f"    COMPLETO: FALHOU")
                erros += 1
        except Exception as e:
            log(f"    COMPLETO: ERRO {str(e)[:80]}")
            erros += 1

        if processados % 50 == 0 and processados > 0:
            elapsed = time.time() - inicio
            rate = processados / (elapsed / 60)
            restam = len(pendentes) - processados
            eta_min = restam / rate if rate > 0 else 0
            log(f"--- RITMO: {processados}/{len(pendentes)} ({erros} erros) {rate:.1f}/min  ETA ~{eta_min:.0f}min ---")

    elapsed = time.time() - inicio
    log("=" * 60)
    log(f"FASE 2 FINALIZADA: {processados} COMPLETOS OK, {erros} erros em {elapsed/60:.1f}min ({elapsed/3600:.1f}h)")
    if processados > 0:
        log(f"Ritmo medio: {processados/(elapsed/60):.1f}/min")


def main():
    log("=" * 60)
    log("REORGANIZAR + GERAR COMPLETOS")
    log("=" * 60)

    log("\n>>> FASE 1: Reorganizar (mover LIMPO, apagar VO3/ESTATICA avulsos)")
    fase1_reorganizar()

    log(f"\n>>> FASE 2: Gerar COMPLETOS (VO3 + estatica juntas)")
    fase2_gerar_completos()

    log("\n>>> RESULTADO FINAL:")
    dir_limpo = cp.DIR_POS_FINAL / "limpo"
    dir_completo = cp.DIR_POS_FINAL / "completo"
    n_limpo = len(list(dir_limpo.glob("*.mp4"))) if dir_limpo.exists() else 0
    n_completo = len(list(dir_completo.glob("*.mp4"))) if dir_completo.exists() else 0
    log(f"  pos_final/limpo/    = {n_limpo} videos")
    log(f"  pos_final/completo/ = {n_completo} videos")
    log("PRONTO!")


if __name__ == "__main__":
    main()
