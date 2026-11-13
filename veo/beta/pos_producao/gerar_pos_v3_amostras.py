# -*- coding: utf-8 -*-
"""gerar_pos_v3_amostras.py — gera 3 videos de AMOSTRA com b-roll do Pexels.

Pega 3 videos pos_v2 recentes, volta pros crus (ja_feitos), e re-monta com
com_pexels_broll=True. Saida em pos_producao/amostras_v3/ pra a dona avaliar.
"""
import sys
from pathlib import Path

_BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(_BASE))

import centralizar_publicar as cp
from centralizar_publicar import log

_OUT_DIR = _BASE / "amostras_v3"
_OUT_DIR.mkdir(parents=True, exist_ok=True)


def _encontrar_cru(stem):
    """Tenta achar o cru (ja_feitos) ou pos_v2 como fallback."""
    cru = cp.ja_feitos_path(stem)
    if cru.exists() and cru.stat().st_size > 50_000:
        return cru
    # fallback: usa o pos_v2 como base (nao ideal mas funciona)
    pos = cp.pos_v2_out_path(stem)
    if pos.exists() and pos.stat().st_size > 50_000:
        return pos
    return None


def gerar():
    # pega 3 ultimos pos_v2
    pos_dir = cp.DIR_POS_V2
    mp4s = sorted([f for f in pos_dir.glob("*.mp4")],
                  key=lambda x: x.stat().st_mtime)[-3:]

    log("=" * 60)
    log(f"GERANDO 3 AMOSTRAS POS V3 (com Pexels b-roll)")
    log(f"saida: {_OUT_DIR}")
    log("=" * 60)

    from montar_final import montar
    from worker_noite import _escolher_metadados

    for idx, pos_v2 in enumerate(mp4s, 1):
        stem = pos_v2.stem
        log(f"\n[{idx}/3] stem={stem}")

        # acha o cru
        cru = _encontrar_cru(stem)
        if not cru:
            log(f"  ! cru nao encontrado, pulando")
            continue
        log(f"  cru: {cru.name}")

        # metadados (infere do stem)
        canal, tema, fala = _escolher_metadados(stem)

        # monta v3 (com b-roll)
        out = _OUT_DIR / f"v3_{idx}_{stem}.mp4"
        try:
            meta = montar(
                str(cru), str(out), canal, tema, fala,
                voz="auto", formato_cta="slide",
                com_vo3_propaganda=True,
                com_pexels_broll=True  # <<< ATIVA B-ROLL
            )
            ok = meta.get("ok") if isinstance(meta, dict) else bool(meta)
            if ok:
                tam_mb = out.stat().st_size / (1024*1024)
                broll_count = meta.get("efeitos", {}).get("broll_count", 0)
                log(f"  OK v3 ({tam_mb:.1f}MB) brolls={broll_count}")
            else:
                log(f"  FALHOU montagem v3")
        except Exception as e:
            log(f"  ERRO: {str(e)[:100]}")

    log("=" * 60)
    log(f"CONCLUIDO: amostras em {_OUT_DIR}")
    log("=" * 60)


if __name__ == "__main__":
    gerar()
