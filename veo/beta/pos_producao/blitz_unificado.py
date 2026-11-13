# -*- coding: utf-8 -*-
"""blitz_unificado.py — gera LIMPO + COMPLETO de TODOS os pendentes.
Limpa tmp/ a cada video pra nao estourar disco.
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

_VARIANTES = [
    {"sufixo": "_LIMPO",    "subpasta": "limpo",    "com_propaganda": False, "com_vo3_propaganda": False},
    {"sufixo": "_COMPLETO", "subpasta": "completo", "com_propaganda": True,  "com_vo3_propaganda": True},
]

TMP = _BASE / "tmp"
DISCO_MIN_MB = 500


def espaco_livre_mb():
    return shutil.disk_usage("D:/").free // (1024 * 1024)


def limpar_tmp():
    if TMP.exists():
        for f in TMP.iterdir():
            if f.is_file():
                try:
                    f.unlink()
                except Exception:
                    pass


def escolher_meta(stem):
    slug = stem.rsplit("_", 2)[0] if "_" in stem else stem
    mapa = {
        "alienigenas": ("Alienigenas", "ETs em Situacoes Engracadas", "ETs roubam nosso wifi"),
        "dicas_financeir": ("Dicas Financeiras", "Educacao Financeira", "O banco esconde esse erro"),
        "curiosidades_ia": ("Curiosidades IA", "Fatos Rapidos Chocantes", "Voce nao vai acreditar"),
        "agenda_ia": ("Agenda IA", "Produtividade com IA", "Sua agenda lota sozinha"),
        "cerebro_digital": ("Cerebro Digital", "Tecnologia e IA", "Seu cerebro nao e tao unico"),
        "segredos_do_oce": ("Segredos do Oceano", "Mundo Animal", "Tem um monstro la embaixo"),
        "e_se...": ("E Se...", "Curiosidades Hipoteticas", "E se a gravidade sumisse?"),
        "super_slow_ia": ("Super Slow IA", "Videos Satisfatorios", "Coisas absurdas em superlenta"),
        "corpo_humano": ("Corpo Humano", "Ciencia do Corpo", "Seu corpo faz isso e voce nem sabe"),
        "robos_desastrad": ("Robos Desastrados", "Videos Engracados com IA", "Robo tenta ajudar e quebra tudo"),
        "stand-up_ia": ("Stand Up IA", "Humor com IA", "Ia comediante falha bonito"),
        "aulas_ia": ("Aulas IA", "Educacao com IA", "Professor IA explica em 2 min"),
        "motivacao_ia": ("Motivacao IA", "Frases Motivacionais", "Voce ja tentou mais que 90%"),
        "noticias_de_ia": ("Noticias de IA", "Tech News", "Ia nova lancada ontem muda tudo"),
        "cassetadas_ia": ("Cassetadas IA", "Videos Engracados", "Ia tenta limpar e faz bagunca"),
        "dicas_fitness": ("Dicas Fitness", "Saude e Fitness", "Queima 3x mais que corrida"),
        "fatos_bizarros": ("Fatos Bizarros", "Curiosidades Bizarras", "Aconteceu de verdade"),
        "danca_e_musica": ("Danca E Musica", "Danca e Musica", "Passo viralizando no mundo"),
        "tech_news": ("Tech News", "Tecnologia", "Lancamento bombastico"),
        "vendas_com_ia": ("Vendas com IA", "Marketing Digital", "Ia vende mais que vendedor"),
        "dicas_de_negoci": ("Dicas de Negocio", "Empreendedorismo", "Hack loja 10x mais"),
        "produtividade": ("Produtividade", "Produtividade", "Pare de perder tempo"),
        "fofos_e_absurdo": ("Fofos e Absurdos", "Fofura e Humor", "Bichinho mais fofo do mundo"),
        "alucinaai": ("Alucinaai", "Alucinacoes IA", "A IA sonhou e ninguem acreditou"),
        "curiosidad": ("Curiosidades", "Curiosidades", "Fato que ninguem contou"),
    }
    if slug in mapa:
        return mapa[slug]
    canal = slug.replace("_", " ").title()
    return canal, canal, f"Descubra o que voce nao sabia sobre {canal}"


def main():
    from montar_final import montar

    dir_limpo = cp.DIR_POS_FINAL / "limpo"
    dir_completo = cp.DIR_POS_FINAL / "completo"
    dir_limpo.mkdir(exist_ok=True)
    dir_completo.mkdir(exist_ok=True)

    pendentes = []
    for v in sorted(cp.DIR_INICIAIS.glob("*.mp4")):
        if v.stat().st_size < 50_000:
            continue
        stem = v.stem
        tem_limpo = (dir_limpo / f"{stem}_LIMPO.mp4").exists() and (dir_limpo / f"{stem}_LIMPO.mp4").stat().st_size > 50_000
        tem_completo = (dir_completo / f"{stem}_COMPLETO.mp4").exists() and (dir_completo / f"{stem}_COMPLETO.mp4").stat().st_size > 50_000
        if not tem_limpo or not tem_completo:
            pendentes.append((v, tem_limpo, tem_completo))

    log(f"BLITZ UNIFICADO: {len(pendentes)} pendentes de {len(list(cp.DIR_INICIAIS.glob('*.mp4')))} iniciais")
    log(f"  sem LIMPO: {sum(1 for _, l, _ in pendentes if not l)}")
    log(f"  sem COMPLETO: {sum(1 for _, _, c in pendentes if not c)}")
    log(f"Disco livre: {espaco_livre_mb()} MB")
    log("=" * 60)

    inicio = time.time()
    ok_total = 0
    erros = 0
    disco_pausa = 0

    for i, (v, tem_l, tem_c) in enumerate(pendentes):
        if i % 20 == 0:
            mb = espaco_livre_mb()
            if mb < DISCO_MIN_MB:
                limpar_tmp()
                mb = espaco_livre_mb()
                if mb < DISCO_MIN_MB:
                    log(f"DISCO CRITICO: {mb} MB livre, PARANDO")
                    break
                else:
                    disco_pausa += 1
                    log(f"  [disco] tmp limpo, agora {mb} MB livre")

        elapsed = time.time() - inicio
        stem = v.stem
        canal, tema, fala = escolher_meta(stem)

        vars_needed = []
        if not tem_l:
            vars_needed.append("LIMPO")
        if not tem_c:
            vars_needed.append("COMPLETO")

        log(f"[{i+1}/{len(pendentes)}] {v.name}  falta={' + '.join(vars_needed)}  ({elapsed:.0f}s)")

        for var in _VARIANTES:
            sufixo = var["sufixo"]
            out = cp.DIR_POS_FINAL / var["subpasta"] / f"{stem}{sufixo}.mp4"
            if out.exists() and out.stat().st_size > 50_000:
                continue
            try:
                t0 = time.time()
                meta = montar(str(v), str(out), canal, tema, fala,
                              voz="auto", formato_cta="slide",
                              com_propaganda=var["com_propaganda"],
                              com_vo3_propaganda=var["com_vo3_propaganda"])
                dt = time.time() - t0
                ok = meta.get("ok") if isinstance(meta, dict) else bool(meta)
                if ok:
                    log(f"    {sufixo}: OK ({out.stat().st_size // 1024}KB, {dt:.0f}s)")
                    ok_total += 1
                else:
                    log(f"    {sufixo}: FALHOU")
                    erros += 1
            except Exception as e:
                log(f"    {sufixo}: ERRO {str(e)[:80]}")
                erros += 1
            limpar_tmp()

        if (i + 1) % 50 == 0:
            elapsed = time.time() - inicio
            mb = espaco_livre_mb()
            rate = (i + 1) / (elapsed / 60) if elapsed > 0 else 0
            restam = len(pendentes) - (i + 1)
            eta = restam / rate if rate > 0 else 0
            log(f"--- RITMO: {i+1}/{len(pendentes)} ({ok_total} OK, {erros} erros) {rate:.1f}/min ETA ~{eta:.0f}min disco={mb}MB ---")

    elapsed = time.time() - inicio
    log("=" * 60)
    log(f"BLITZ UNIFICADO FINALIZADO: {ok_total} variantes OK, {erros} erros em {elapsed/60:.1f}min ({elapsed/3600:.1f}h)")
    log(f"Limpezas de disco: {disco_pausa}")
    n_limpo = len(list(dir_limpo.glob("*.mp4")))
    n_completo = len(list(dir_completo.glob("*.mp4")))
    log(f"TOTAIS: {n_limpo} LIMPOs, {n_completo} COMPLETOs")


if __name__ == "__main__":
    main()
