#!/usr/bin/env python3
# COMUM — fonte única: D:\hipercool-materiais\comum\styled_transitions.py. Mudou esta cópia? python D:\hipercool-materiais\bin\recursos.py subir styled_transitions.py --de <projeto>
"""styled_transitions.py — STANDALONE (NAO integrado ao pipeline de producao).

Insere uma transicao ESTILIZADA visivel no corte entre dois clipes, usando os
MP4 de transicao (workspace/assets/overlays/transitions/) que sao LUZ sobre
FUNDO PRETO -> compostos com blend=screen (NAO overlay, que cobriria a cena).

POR QUE STANDALONE E ATRAS DE FLAG:
- A regra #4 do CLAUDE.md desaconselha overlay blend=screen no pipeline principal.
  Aqui e um experimento isolado p/ a usuaria APROVAR visualmente antes de integrar.
- NAO toca no audio (o erro historico dos 69% mudos veio de mexer audio pair-by-pair).
  O audio do clip base passa intacto (-c:a copy / amix opcional).

Tecnica (sem desincronizar):
  Para o corte A->B, pega os ultimos T s de A e os primeiros T s de B, e durante
  essa janela soma o brilho do MP4 de transicao via blend=screen. O video ganha
  o "lambido de luz" no corte; o audio segue o do clip (concatenacao normal).

Uso (demo de 1 corte):
  python bin/styled_transitions.py --a clipA.mp4 --b clipB.mp4 --out corte.mp4 \
      --transition transition_5.mp4 --dur 0.8
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path

PROJ = Path(__file__).resolve().parent.parent
TRANS_DIR = PROJ / "workspace" / "assets" / "overlays" / "transitions"


def log(m):
    print(f"[styled] {m}", file=sys.stderr)


def probe(path, stream="v:0", entry="duration"):
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", stream,
         "-show_entries", f"stream={entry}", "-of",
         "default=noprint_wrappers=1:nokey=1", str(path)],
        capture_output=True, text=True)
    out = r.stdout.strip().splitlines()
    return out[0] if out else ""


def res_of(path):
    w = probe(path, entry="width")
    h = probe(path, entry="height")
    return int(w), int(h)


def make_boundary(clip_a, clip_b, out, trans_mp4, dur=0.8):
    """Concatena A+B com a transicao de luz (blend=screen) sobreposta na juncao.

    A janela de transicao cobre os ultimos dur/2 de A e os primeiros dur/2 de B.
    Mantem o audio simples (concat dos dois). Sem xfade no audio = sem drift.
    """
    bw, bh = res_of(clip_a)
    da = float(probe(clip_a) or 0)

    # filtro:
    #  - escala MP4 de transicao p/ resolucao da base
    #  - concat de A e B no video base [base]
    #  - posiciona a transicao no tempo do corte (da - dur/2) e soma com screen
    half = dur / 2.0
    t_start = max(0.0, da - half)
    fc = (
        f"[0:v]scale={bw}:{bh}:flags=lanczos,setsar=1,fps=30[a];"
        f"[1:v]scale={bw}:{bh}:flags=lanczos,setsar=1,fps=30[b];"
        f"[a][b]concat=n=2:v=1:a=0[base];"
        f"[2:v]scale={bw}:{bh}:flags=lanczos,setsar=1,fps=30,"
        f"tpad=start_duration={t_start}:start_mode=clone,"
        f"trim=0:{da+half},setpts=PTS-STARTPTS[tr];"
        f"[base][tr]blend=all_mode=screen:all_opacity=0.9[v]"
    )
    # audio: concat simples dos dois clips (sem xfade -> sem drift de audio)
    fc_full = fc + ";[0:a][1:a]concat=n=2:v=0:a=1[aout]"
    cmd = [
        "ffmpeg", "-y",
        "-i", str(clip_a), "-i", str(clip_b), "-i", str(trans_mp4),
        "-filter_complex", fc_full,
        "-map", "[v]", "-map", "[aout]",
        "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k",
        str(out),
    ]
    log(f"corte A->B com {Path(trans_mp4).name} (screen, dur={dur}s) @ t={t_start:.2f}")
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        log("ERRO ffmpeg:\n" + r.stderr[-1500:])
        return False
    return Path(out).exists()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--a", required=True)
    ap.add_argument("--b", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--transition", default="transition_5.mp4")
    ap.add_argument("--dur", type=float, default=0.8)
    args = ap.parse_args()
    tr = TRANS_DIR / args.transition
    if not tr.exists():
        log(f"transicao nao encontrada: {tr}")
        sys.exit(1)
    ok = make_boundary(Path(args.a), Path(args.b), Path(args.out), tr, args.dur)
    sys.exit(0 if ok else 2)


if __name__ == "__main__":
    main()
