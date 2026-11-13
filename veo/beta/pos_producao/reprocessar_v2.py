# -*- coding: utf-8 -*-
"""reprocessar_v2.py — reprocessa TODOS os videos ja feitos com a receita
COMPLETA (v2), gravando numa pasta separada (veo/pos_v2) sem tocar na v1.

Receita v2 por video:
  CRIATIVO (Veo, ja com foto-protagonista da geracao)
    -> [transicao] CLIPE-PROPAGANDA vo3 do PRODUTO (pool, rotacionado; a "do
       meio" nao muda toda vez — reusa o pool, exatamente como a dona pediu)
    -> [transicao] CARD estatico (fundo IA + voz acentuada + WhatsApp/link)

- NAO regera clipe vo3 (usa o pool pronto) -> rapido (~25s/video, CPU).
- Card usa omniroute (Pollinations enquanto Gemini premium nao volta).
- Grava sidecar <stem>.pos.json (rastreabilidade).
- Idempotente: se ja existe em pos_v2 e nao --forcar, pula.

Uso:
    python reprocessar_v2.py                 (todos de ja_feitos)
    python reprocessar_v2.py --limite 5      (so os 5 primeiros — teste)
    python reprocessar_v2.py --forcar        (regera mesmo se ja existe)
"""
import argparse
import sys
import time
from pathlib import Path

_BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(_BASE))

import centralizar_publicar as cp
from centralizar_publicar import log
from worker_noite import _escolher_metadados, _gravar_sidecar


def _ja_v2(stem: str) -> bool:
    p = cp.pos_v2_out_path(stem)
    return p.exists() and p.stat().st_size > 50_000


def reprocessar(limite=0, forcar=False):
    cp.garantir_layout()
    fontes = sorted(cp.DIR_FEITOS.glob("*.mp4"))
    log("=" * 60)
    log(f"reprocessar_v2: {len(fontes)} videos em ja_feitos -> pos_v2")
    log(f"forcar={forcar} limite={limite or 'todos'}")
    log("=" * 60)

    from montar_final import montar
    feitos = pulados = falhas = 0
    for i, src in enumerate(fontes, 1):
        stem = src.stem
        if not forcar and _ja_v2(stem):
            pulados += 1
            continue
        canal, tema, fala = _escolher_metadados(stem)
        out = cp.pos_v2_out_path(stem)
        t0 = time.time()
        try:
            meta = montar(str(src), str(out), canal, tema, fala,
                          voz="auto", formato_cta="slide",
                          com_vo3_propaganda=True)
            dt = time.time() - t0
            ok = meta.get("ok") if isinstance(meta, dict) else bool(meta)
            if ok:
                feitos += 1
                vo3 = meta["efeitos"].get("vo3_propaganda")
                prod = meta["propaganda"].get("produto_nome")
                log(f"[{i}/{len(fontes)}] OK {stem} ({dt:.0f}s) "
                    f"vo3={vo3 or '-'} card={prod}")
                try:
                    _gravar_sidecar(src, out, meta if isinstance(meta, dict) else {}, dt)
                except Exception as e:
                    log(f"    aviso sidecar: {str(e)[:60]}")
            else:
                falhas += 1
                log(f"[{i}/{len(fontes)}] FALHOU {stem}")
        except Exception as e:
            falhas += 1
            log(f"[{i}/{len(fontes)}] ERRO {stem}: {str(e)[:80]}")
        if limite and feitos >= limite:
            log(f"limite {limite} atingido, parando")
            break

    log("=" * 60)
    log(f"CONCLUIDO v2: feitos={feitos} pulados={pulados} falhas={falhas}")
    log(f"saida: {cp.DIR_POS_V2}")
    log("=" * 60)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--limite", type=int, default=0)
    ap.add_argument("--forcar", action="store_true")
    a = ap.parse_args()
    reprocessar(limite=a.limite, forcar=a.forcar)
