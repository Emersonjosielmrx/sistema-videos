#!/usr/bin/env python3
"""
scene-images.py — Gera imagens de cena via APIs grátis keyless (Pollinations),
com resize ffmpeg pro formato alvo (16:9 horizontal e/ou 9:16 vertical).

Pollinations devolve resolução baixa/horizontal (~1024x576) mesmo pedindo outra,
então SEMPRE passamos por um resize ffmpeg (scale increase + crop central).

Uso:
  python bin/scene-images.py --prompts-file prompts.json --out-dir workspace/scenes/slug --format 16x9
  prompts.json = ["prompt cena 1", "prompt cena 2", ...]
"""
import argparse, json, subprocess, sys, time, urllib.parse, urllib.request
from pathlib import Path

POLLINATIONS = "https://image.pollinations.ai/prompt/"
STYLE_SUFFIX = ", cinematic dramatic lighting, photographic realism, highly detailed, no text, no watermark"

FORMATS = {
    "16x9": (1920, 1080),
    "9x16": (1080, 1920),
}


def log(m):
    print(f"[{time.strftime('%H:%M:%S')}] {m}", flush=True)


def fetch_pollinations(prompt, raw_path, seed, model="flux", timeout=120):
    """Baixa 1 imagem do Pollinations (keyless). Retorna True se OK."""
    full = prompt + STYLE_SUFFIX
    enc = urllib.parse.quote(full)
    # pedimos grande; o serviço pode devolver menor (resize resolve depois)
    url = f"{POLLINATIONS}{enc}?width=1280&height=720&nologo=true&seed={seed}&model={model}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            data = r.read()
        if len(data) < 2000:  # provavelmente erro/placeholder
            return False
        Path(raw_path).write_bytes(data)
        return True
    except Exception as e:
        log(f"  [!] Pollinations falhou (seed={seed}): {e}")
        return False


def resize_to(raw_path, out_path, w, h):
    """Resize+crop central pro formato exato via ffmpeg."""
    cmd = [
        "ffmpeg", "-y", "-i", str(raw_path),
        "-vf", f"scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h}",
        "-q:v", "2", str(out_path),
    ]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    return r.returncode == 0 and Path(out_path).exists()


def gen_scene(prompt, idx, out_dir, fmt, raw_dir):
    """Gera 1 cena: baixa (com retries de seed) + resize. Cache por arquivo."""
    w, h = FORMATS[fmt]
    out_path = out_dir / f"image_{idx}.jpg"
    if out_path.exists() and out_path.stat().st_size > 5000:
        log(f"  cena {idx}: [CACHE] {out_path.name}")
        return True
    raw = raw_dir / f"raw_{idx}.jpg"
    # retry trocando seed/modelo até conseguir
    attempts = [("flux", idx), ("flux", idx + 1000), ("turbo", idx), ("flux", idx + 7777)]
    for model, seed in attempts:
        if fetch_pollinations(prompt, raw, seed, model=model):
            if resize_to(raw, out_path, w, h):
                log(f"  cena {idx}: OK ({model}/seed={seed}) -> {out_path.name} [{w}x{h}]")
                return True
        time.sleep(1)
    log(f"  [X] cena {idx}: TODAS as tentativas falharam")
    return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--prompts-file", required=True, help="JSON com lista de prompts")
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--format", choices=list(FORMATS), default="16x9")
    args = ap.parse_args()

    prompts = json.loads(Path(args.prompts_file).read_text(encoding="utf-8"))
    if isinstance(prompts, dict):
        prompts = prompts.get("prompts", [])
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    raw_dir = out_dir / "_raw"
    raw_dir.mkdir(exist_ok=True)

    log(f"Gerando {len(prompts)} cenas [{args.format}] -> {out_dir}")
    ok = 0
    for i, p in enumerate(prompts, 1):
        if gen_scene(p, i, out_dir, args.format, raw_dir):
            ok += 1
    log(f"Concluído: {ok}/{len(prompts)} cenas")
    sys.exit(0 if ok == len(prompts) else 1)


if __name__ == "__main__":
    main()
