# -*- coding: utf-8 -*-
"""render_worker.py — Executado remotamente via PC2 daemon (/exec).

Roda no PC2 (REVISION-PC) via:
    curl http://100.125.7.77:8771/exec \
      -d '{"cmd": "python <caminho>/render_worker.py <args>", "cwd": "C:/tmp"}'

Recebe como argumento o caminho de trabalho (SMB) onde estão os inputs e outputs.
O script processa 1 clip por invocação, lendo parâmetros do argv.

Exemplo de chamada:
    python D:/historias-em-frames/bin/render_worker.py \
        --scene 0 --effect parallax_push_in \
        --input //HAYLLA-PC/d$/historias-em-frames/workspace/temp/_clip_00.png \
        --audio //HAYLLA-PC/d$/historias-em-frames/workspace/temp/_clip_00.wav \
        --output //HAYLLA-PC/d$/historias-em-frames/workspace/temp/_clip_00_out.mp4 \
        --dur 7.5 --ffmpeg_threads 2
"""
import os
import sys
import time
import shutil
import argparse
import subprocess
from pathlib import Path

TIMEOUT_CLIP_S = 120


def log(msg):
    ts = time.strftime("%H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)


def run_cmd(cmd, timeout=TIMEOUT_CLIP_S):
    """Executa cmd via subprocess, retorna (returncode, stdout, stderr)."""
    log(f"  CMD: {cmd[:120]}")
    try:
        r = subprocess.run(
            cmd, shell=True, capture_output=True,
            timeout=timeout, text=True
        )
        return r.returncode, r.stdout, r.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "TIMEOUT"
    except Exception as e:
        return -2, "", str(e)


def build_parallax_clip(input_img, output_mp4, effect, dur, audio_wav, ffmpeg_threads=2):
    """Gera um clip de parallax 2.5D usando ffmpeg local do PC2.

    PC2 tem ffmpeg 8.1.1-full_build-www.gyan.dev.
    Para efeitos de parallax reais, usamos o depth estimation + ffmpeg filter_complex.
    Se depth estimation falhar, cai pra Ken Burns simples.
    """
    input_img = Path(input_img)
    output_mp4 = Path(output_mp4)
    tmp_dir = Path(os.environ.get("TMP", "C:/tmp"))
    tmp_dir.mkdir(parents=True, exist_ok=True)

    base_name = input_img.stem
    depth_map = tmp_dir / f"{base_name}_depth.png"
    tmp_out = tmp_dir / f"{base_name}_raw.mp4"

    ffmpeg_threads = max(1, int(ffmpeg_threads))

    # ── Depth estimation via MiDaS (onnxruntime) ──────────────────────────
    try:
        import torch
        import numpy as np
        from transformers import AutoImageProcessor, AutoModelForDepthEstimation

        log(f"  Loading MiDaS model...")
        processor = AutoImageProcessor.from_pretrained("depth-anything/depth-anything-v2-base-compressed")
        model = AutoModelForDepthEstimation.from_pretrained("depth-anything/depth-anything-v2-base-compressed")

        # Load image
        from PIL import Image
        img = Image.open(input_img).convert("RGB")
        inputs = processor(images=img, return_tensors="pt")

        with torch.no_grad():
            outputs = model(**inputs)
            depth = outputs.predicted_depth

        # Normalize to 0-255
        depth_np = depth.squeeze().numpy()
        depth_np = (depth_np - depth_np.min()) / (depth_np.max() - depth_np.min() + 1e-8)
        depth_img = Image.fromarray((depth_np * 255).astype("uint8"), mode="L")
        depth_img.save(depth_map)

        log(f"  Depth map: {depth_map.name} ({depth_map.stat().st_size // 1024} KB)")

        has_depth = True
    except Exception as e:
        log(f"  Depth estimation failed ({e}) — falling back to Ken Burns")
        has_depth = False

    # ── Build effect parameters ────────────────────────────────────────────
    if effect == "parallax_orbit":
        zoom = "1.05"
        x_shift = "10"
        y_shift = "0"
        duration = str(dur)
        vf = (f"scale=1080:1920:force_original_aspect_ratio=decrease,"
              f"pad=1080:1920:(ow-iw)/2:(oh-ih)/2:color=black,"
              f"zoompan=z='min(zoom+0.001,1.05)':d=1:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
              f"setpts=N/FRAME_RATE/TB")
        if has_depth:
            vf += f",perspective=x0=0:y0=0:x1={x_shift}:y1=0:x2={x_shift}:y2=0:x3=0:y3=0:s=1080x1920"

    elif effect == "parallax_push_in":
        zoom_in = "1.0"
        zoom_out = "1.12"
        duration = str(dur)
        vf = (f"scale=1080:1920:force_original_aspect_ratio=decrease,"
              f"pad=1080:1920:(ow-iw)/2:(oh-ih)/2:color=black,"
              f"zoompan=z='if(lte(zoom,{zoom_out}),{zoom_in}+({zoom_out}-{zoom_in})*t/{duration},{zoom_out})':"
              f"d={duration}*FRAME_RATE:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
              f"setpts=N/FRAME_RATE/TB")

    elif effect == "parallax_float":
        x_center = "iw/2"
        y_base = "ih/2"
        amp_x = "iw*0.02"
        amp_y = "ih*0.015"
        duration = str(dur)
        vf = (f"scale=1080:1920:force_original_aspect_ratio=decrease,"
              f"pad=1080:1920:(ow-iw)/2:(oh-ih)/2:color=black,"
              f"zoompan=z='1.03':d={duration}*FRAME_RATE:"
              f"x='{x_center}+{amp_x}*sin(t*{amp_x}/iw)':"
              f"y='{y_base}+{amp_y}*sin(t*{amp_y}/ih)':"
              f"setpts=N/FRAME_RATE/TB")

    elif effect == "parallax_sweep":
        x_from = "-iw*0.05"
        x_to = "iw*0.05"
        duration = str(dur)
        vf = (f"scale=1080:1920:force_original_aspect_ratio=decrease,"
              f"pad=1080:1920:(ow-iw)/2:(oh-ih)/2:color=black,"
              f"zoompan=z='1.02':d={duration}*FRAME_RATE:"
              f"x='lerp({x_from},{x_to},t/{duration})':"
              f"y='ih/2-(ih/zoom/2)':setpts=N/FRAME_RATE/TB")

    elif effect == "kenburns":
        zoom_in = "1.08"
        zoom_out = "0.96"
        duration = str(dur)
        vf = (f"scale=1080:1920:force_original_aspect_ratio=decrease,"
              f"pad=1080:1920:(ow-iw)/2:(oh-ih)/2:color=black,"
              f"zoompan=z='if(lte(zoom,{zoom_in}),{zoom_out}+({zoom_in}-{zoom_out})*t/{duration},{zoom_in})':"
              f"d={duration}*FRAME_RATE:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
              f"setpts=N/FRAME_RATE/TB")

    elif effect == "shake":
        vf = (f"scale=1080:1920:force_original_aspect_ratio=decrease,"
              f"pad=1080:1920:(ow-iw)/2:(oh-ih)/2:color=black,"
              f"zoompan=z='1.0':d={dur}*FRAME_RATE:"
              f"x='iw/2+(iw*0.01)*sin(t*8)':y='ih/2+(ih*0.01)*cos(t*7)':"
              f"setpts=N/FRAME_RATE/TB")

    elif effect == "static":
        vf = (f"scale=1080:1920:force_original_aspect_ratio=decrease,"
              f"pad=1080:1920:(ow-iw)/2:(oh-ih)/2:color=black,"
              f"zoompan=z='1.0':d=1:s=1080x1920,fps=30")

    else:
        # Default: simple scale
        vf = (f"scale=1080:1920:force_original_aspect_ratio=decrease,"
              f"pad=1080:1920:(ow-iw)/2:(oh-ih)/2:color=black")

    # ── Build ffmpeg command ───────────────────────────────────────────────
    if audio_wav and Path(audio_wav).exists():
        cmd = (
            f'ffmpeg -y -loop 1 -i "{input_img}" -i "{audio_wav}" '
            f'-vf "{vf}" -pix_fmt yuv420p '
            f'-r 30 -t {dur} '
            f'-c:v libx264 -preset fast -crf 23 -threads {ffmpeg_threads} '
            f'-c:a aac -b:a 128k -shortest '
            f'-progress pipe:1 "{tmp_out}"'
        )
    else:
        cmd = (
            f'ffmpeg -y -loop 1 -i "{input_img}" '
            f'-vf "{vf}" -pix_fmt yuv420p '
            f'-r 30 -t {dur} '
            f'-c:v libx264 -preset fast -crf 23 -threads {ffmpeg_threads} '
            f'-progress pipe:1 "{tmp_out}"'
        )

    log(f"  Rendering clip ({effect}, {dur}s)...")
    t0 = time.time()
    rc, stdout, stderr = run_cmd(cmd, timeout=TIMEOUT_CLIP_S)
    elapsed = time.time() - t0

    if rc != 0 or not tmp_out.exists():
        log(f"  FFMPEG FAILED rc={rc} — stderr: {stderr[-200:]}")
        # Try again with simpler filter
        simple_vf = (f"scale=1080:1920:force_original_aspect_ratio=decrease,"
                    f"pad=1080:1920:(ow-iw)/2:(oh-ih)/2:color=black,"
                    f"zoompan=z='1.0':d=1:s=1080x1920,fps=30")
        cmd2 = (
            f'ffmpeg -y -loop 1 -i "{input_img}" '
            f'-vf "{simple_vf}" -pix_fmt yuv420p '
            f'-r 30 -t {dur} '
            f'-c:v libx264 -preset ultrafast -crf 26 -threads {ffmpeg_threads} '
            f'"{tmp_out}"'
        )
        rc, stdout, stderr = run_cmd(cmd2, timeout=60)

    if rc == 0 and tmp_out.exists():
        # Move to final output
        output_mp4.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(tmp_out), str(output_mp4))
        log(f"  OK: {output_mp4.name} ({output_mp4.stat().st_size // 1024 // 1024} MB) em {elapsed:.1f}s")
        return True
    else:
        log(f"  FAILED: rc={rc}, exists={tmp_out.exists()}")
        return False


def main():
    parser = argparse.ArgumentParser(description="render_worker — parallax clip via PC2")
    parser.add_argument("--scene", type=int, required=True)
    parser.add_argument("--effect", required=True)
    parser.add_argument("--input", required=True)
    parser.add_argument("--audio", default="")
    parser.add_argument("--output", required=True)
    parser.add_argument("--dur", type=float, required=True)
    parser.add_argument("--ffmpeg_threads", type=int, default=2)
    args = parser.parse_args()

    log(f"=== render_worker scene={args.scene} effect={args.effect} ===")

    if not Path(args.input).exists():
        log(f"  ERRO: input nao existe: {args.input}")
        sys.exit(1)

    ok = build_parallax_clip(
        input_img=args.input,
        output_mp4=args.output,
        effect=args.effect,
        dur=args.dur,
        audio_wav=args.audio or None,
        ffmpeg_threads=args.ffmpeg_threads,
    )

    if ok:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
