#!/usr/bin/env python3
# COMUM — fonte única: D:\hipercool-materiais\comum\master_loudness.py. Mudou esta cópia? python D:\hipercool-materiais\bin\recursos.py subir master_loudness.py --de <projeto>
"""master_loudness.py — STANDALONE, NÃO integrado ao pipeline.

Aplica um loudnorm FINAL (two-pass) no MIX já pronto de um vídeo, pra trazer o
master pro alvo de entrega do YouTube (~-14/-16 LUFS) sem mexer no pipeline nem
re-renderizar o vídeo. Vídeo é copiado (stream copy); só o áudio é re-encodado.

Motivo: medição em 2026-06-30 mostrou o cap01 OFICIAL a -25.7 LUFS integrado —
~11 dB abaixo do padrão. O YouTube só ABAIXA o que está alto, nunca sobe o que
está baixo, então o vídeo sai com volume fraco pro espectador.

Uso:
  python bin/master_loudness.py INPUT.mp4 [OUTPUT.mp4] [--lufs -16] [--tp -1.5]

Sem OUTPUT, grava em _testes/MASTER_LOUDNESS_<lufs>_<nome>.mp4 pra aprovação A/B.
Two-pass: 1ª passada mede (loudnorm print_format=json), 2ª aplica com measured_*.
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path


def ffprobe_lufs(path):
    """Mede o LUFS integrado atual (informativo)."""
    # 30/10 (Fable): -vn/-sn — medir o áudio não precisa decodificar o vídeo (num longo de 95 min a medição levava 9 min)
    r = subprocess.run(
        ["ffmpeg", "-i", str(path), "-vn", "-sn", "-af",
         "loudnorm=print_format=summary", "-f", "null", "-"],
        capture_output=True, text=True,
    )
    out = {}
    for line in r.stderr.splitlines():
        if "Input Integrated:" in line:
            out["I"] = line.split(":")[1].strip()
        elif "Input True Peak:" in line:
            out["TP"] = line.split(":")[1].strip()
        elif "Input LRA:" in line:
            out["LRA"] = line.split(":")[1].strip()
    return out


def measure_pass(path, target_lufs, target_tp, lra=11):
    """1ª passada: loudnorm em modo medição, devolve os measured_* em JSON."""
    af = (f"loudnorm=I={target_lufs}:TP={target_tp}:LRA={lra}:"
          f"print_format=json")
    r = subprocess.run(
        ["ffmpeg", "-i", str(path), "-vn", "-sn", "-af", af, "-f", "null", "-"],  # 30/10: só o áudio (ver ffprobe_lufs)
        capture_output=True, text=True,
    )
    # O JSON é impresso nas últimas linhas do stderr.
    lines = r.stderr.splitlines()
    start = next((i for i, l in enumerate(lines) if l.strip().startswith("{")), None)
    if start is None:
        raise RuntimeError("loudnorm não emitiu JSON (1ª passada). stderr:\n"
                           + "\n".join(lines[-15:]))
    blob = "\n".join(lines[start:])
    # corta após o fechamento do objeto
    blob = blob[: blob.rindex("}") + 1]
    return json.loads(blob)


def apply_pass(path, out_path, target_lufs, target_tp, m, lra=11):
    """2ª passada: aplica loudnorm linear com os valores medidos. Vídeo = copy."""
    af = (
        f"loudnorm=I={target_lufs}:TP={target_tp}:LRA={lra}:"
        f"measured_I={m['input_i']}:measured_TP={m['input_tp']}:"
        f"measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:"
        f"offset={m['target_offset']}:linear=true:print_format=summary"
    )
    cmd = [
        "ffmpeg", "-y", "-i", str(path),
        "-af", af,
        "-c:v", "copy",
        "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2",
        str(out_path),
    ]
    subprocess.run(cmd, check=True, capture_output=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input")
    ap.add_argument("output", nargs="?", default=None)
    ap.add_argument("--lufs", type=float, default=-16.0,
                    help="alvo de loudness integrado (YouTube ~-14; seguro -16)")
    ap.add_argument("--tp", type=float, default=-1.5,
                    help="true peak máximo (dBTP)")
    ap.add_argument("--lra", type=float, default=11.0)
    args = ap.parse_args()

    inp = Path(args.input)
    if not inp.exists():
        print(f"ERRO: não existe: {inp}", file=sys.stderr)
        sys.exit(1)

    if args.output:
        out = Path(args.output)
    else:
        testes = inp.parent.parent.parent  # heurística; cai em _testes do projeto
        # mais robusto: usa _testes na raiz do projeto se achar
        root = Path(__file__).resolve().parent.parent
        tdir = root / "_testes"
        tdir.mkdir(exist_ok=True)
        out = tdir / f"MASTER_LOUDNESS_{int(args.lufs)}_{inp.stem}.mp4"

    print(f"== ANTES ==", flush=True)
    before = ffprobe_lufs(inp)
    print("  ", before, flush=True)

    print(f"== medindo (1ª passada, alvo {args.lufs} LUFS) ==", flush=True)
    m = measure_pass(inp, args.lufs, args.tp, args.lra)
    print(f"   measured_I={m['input_i']} TP={m['input_tp']} LRA={m['input_lra']}",
          flush=True)

    print(f"== aplicando (2ª passada) → {out.name} ==", flush=True)
    apply_pass(inp, out, args.lufs, args.tp, m, args.lra)

    print(f"== DEPOIS ==", flush=True)
    after = ffprobe_lufs(out)
    print("  ", after, flush=True)
    print(f"\nOK: {out}", flush=True)
    print("Compare A/B de ouvido. Se aprovar, integrar como passada final do mix "
          "em add_dynamic_music / add_background_music.", flush=True)


if __name__ == "__main__":
    main()
