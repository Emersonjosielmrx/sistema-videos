#!/usr/bin/env python3
"""Confere se alguma fala do manhwa ficou de fora dos roteiros já guardados, e corrige.

Por que existe (dono, 16/10/2026): "Muitas falas estão sendo puladas e isso afeta o entendimento do
manhwa. Pra quem assiste só o vídeo está bem aceitável, mas se ler a história vê as lacunas
inteiras." A partir de hoje `narration.gerar_recap` já confere ao gerar; este script é pro que já
está guardado em `workspace/narration_cache/`, que não seria refeito.

    python conferir_falas.py                 -> só relata (não muda nada)
    python conferir_falas.py --corrigir      -> reescreve as locuções que deixaram fala de fora
    python conferir_falas.py --obra the-inheritor --corrigir

O que ele NÃO pega: fala que a LEITURA dos painéis nem transcreveu — essa só volta refazendo a
visão, que é o que `HIPER_NARRACAO_V=v2` força (veja hp_paineis.arquivo_narracao).
"""
import argparse
import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import narration  # noqa: E402
from hp_common import PROJECT_DIR, log  # noqa: E402

CACHE = PROJECT_DIR / "workspace" / "narration_cache"


def conferir(arquivo, corrigir=False):
    """(painéis com fala de fora, falas, quantas foram reescritas)."""
    try:
        d = json.loads(Path(arquivo).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    loc, desc = d.get("locucoes") or [], d.get("descriptions") or []
    if not loc or not desc:
        return None

    perdidas = narration.falas_perdidas(loc, desc)
    n_falas = sum(len(f) for _i, f in perdidas)
    if not perdidas or not corrigir:
        return len(perdidas), n_falas, 0

    # backup antes de mexer: roteiro é caro de refazer
    bak = Path(str(arquivo) + ".antes_conferencia")
    if not bak.exists():
        shutil.copy2(arquivo, bak)

    ng = "F"
    npapel = "narradora"
    n = narration._completar_falas_perdidas(loc, desc, npapel, ng)
    if n:
        d["locucoes"] = loc
        d["_conferencia_falas"] = {"paineis": len(perdidas), "falas": n_falas, "reescritos": n}
        Path(arquivo).write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    return len(perdidas), n_falas, n


def main():
    ap = argparse.ArgumentParser(description="Confere falas que ficaram de fora dos roteiros")
    ap.add_argument("--obra", help="só os capítulos desta obra (pelo nome do arquivo)")
    ap.add_argument("--corrigir", action="store_true", help="reescreve (sem isto, só relata)")
    a = ap.parse_args()

    arquivos = sorted(p for p in CACHE.glob("*panels.json")
                      if (not a.obra or a.obra in p.name)
                      and not any(x in p.name for x in ("_en.", "_fr.", "_es.", "_hi.", "_id.",
                                                        "_it.", "_ru.", "_th.", "_vi.")))
    if not arquivos:
        log("nenhum roteiro encontrado")
        return

    tot_p = tot_f = tot_n = 0
    for p in arquivos:
        r = conferir(p, a.corrigir)
        if not r:
            continue
        np_, nf, nn = r
        tot_p += np_
        tot_f += nf
        tot_n += nn
        if np_:
            log(f"{p.name[:52]:52} {np_:3} painéis, {nf:3} falas de fora"
                + (f", {nn} reescritos" if a.corrigir else ""))
    log(f"TOTAL: {tot_p} painéis com fala de fora, {tot_f} falas"
        + (f", {tot_n} locuções reescritas" if a.corrigir else " (rode com --corrigir pra consertar)"))


if __name__ == "__main__":
    main()
