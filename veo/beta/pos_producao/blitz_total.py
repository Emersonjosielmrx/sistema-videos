# -*- coding: utf-8 -*-
"""blitz_total.py — processa TODOS os crus do veo_videos_iniciais ate zerar.
Igual ao blitz_1h.py mas sem limite de tempo.
"""
import os
import sys
import time
from pathlib import Path

_BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(_BASE))
os.environ.setdefault("PYTHONUTF8", "1")

import centralizar_publicar as cp
from centralizar_publicar import log

_VARIANTES = [
    {"sufixo": "_COMPLETO", "com_propaganda": True, "com_vo3_propaganda": True},
]


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


def _precisa_processar(stem: str) -> bool:
    for var in _VARIANTES:
        out = cp.DIR_POS_FINAL / f"{stem}{var['sufixo']}.mp4"
        if not out.exists() or out.stat().st_size < 50_000:
            return True
    return False


def main():
    from montar_final import montar

    inicio = time.time()
    todos = sorted(cp.DIR_INICIAIS.glob("*.mp4"))
    pendentes = [v for v in todos if v.stat().st_size > 50_000 and _precisa_processar(v.stem)]

    log(f"BLITZ TOTAL: {len(pendentes)} pendentes de {len(todos)} crus")
    log(f"Saida: {cp.DIR_POS_FINAL}")
    log("=" * 60)

    processados = 0
    variantes_ok = 0
    erros = 0

    for v in pendentes:
        elapsed = time.time() - inicio
        stem = v.stem
        canal, tema, fala = _escolher_metadados(stem)
        log(f"[{processados+1}] {v.name}  canal={canal}  ({elapsed:.0f}s)")

        ok_este = 0
        for var in _VARIANTES:
            sufixo = var["sufixo"]
            var_stem = f"{stem}{sufixo}"
            out = cp.DIR_POS_FINAL / f"{var_stem}.mp4"
            if out.exists() and out.stat().st_size > 50_000:
                ok_este += 1
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
                    ok_este += 1
                    variantes_ok += 1
                else:
                    log(f"    {sufixo}: FALHOU")
                    erros += 1
            except Exception as e:
                log(f"    {sufixo}: ERRO {str(e)[:80]}")
                erros += 1

        if ok_este > 0:
            processados += 1

        if processados % 50 == 0 and processados > 0:
            elapsed = time.time() - inicio
            rate = processados / (elapsed / 60)
            restam = len(pendentes) - processados
            eta_min = restam / rate if rate > 0 else 0
            log(f"--- RITMO: {processados}/{len(pendentes)} videos ({variantes_ok} variantes OK, {erros} erros) em {elapsed/60:.1f}min = {rate:.1f}/min  ETA ~{eta_min:.0f}min ---")

    elapsed = time.time() - inicio
    log("=" * 60)
    log(f"BLITZ TOTAL FINALIZADA: {processados} videos, {variantes_ok} variantes OK, {erros} erros em {elapsed/60:.1f}min ({elapsed/3600:.1f}h)")
    if processados > 0:
        log(f"Ritmo medio: {processados/(elapsed/60):.1f} videos/min, {variantes_ok/(elapsed/60):.1f} variantes/min")


if __name__ == "__main__":
    main()
