#!/usr/bin/env python3
"""MotionFrames — depth_prefetch.py
Gera DEPTH MAPS (a etapa cara do parallax 2.5D) de todos os painéis já baixados,
em BACKGROUND, aproveitando a máquina ociosa. NÃO toca no pipeline do hipercool —
só popula um cache que o pipeline vai consumir depois.

Por que só o depth: o depth (~20s/painel, Depth-Anything-V2 em CPU) independe da
duração do clip. O clip de parallax em si (ffmpeg, ~3s) é barato e sai na hora de
gerar o vídeo com a duração certa do áudio. Adiantar o depth = adiantar 90% do custo.

Cache: cache/depth/<md5_da_imagem>.png  (md5 do conteúdo do arquivo → imune a rename
e compartilhável entre as cópias/obras; painel idêntico = 1 depth só).

Educado com a máquina: se houver ffmpeg rodando (render do hipercool), PULA a rodada
inteira (não compete por CPU). Processa 1 painel por vez. Ctrl-C seguro (idempotente).

Uso:
  python depth_prefetch.py                  # varre PANELS_ROOT inteiro
  python depth_prefetch.py --obra taming-noona   # só caps que casam o filtro
  python depth_prefetch.py --limit 50       # para após N depths novos (p/ cron)
  python depth_prefetch.py --once           # processa 1 e sai (p/ cron curto)
"""
import argparse, hashlib, os, subprocess, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent          # D:\hipercool-motionframes
FIX_BIN = Path(r"D:\hipercool-inferior-fix\bin")
PANELS_ROOT = Path(r"D:\hipercool-inferior-fix\workspace\panels")
CACHE_DEPTH = ROOT / "cache" / "depth"
LOG = ROOT / "logs" / "depth_prefetch.log"
TARGET = (720, 1280)   # mesma base do parallax_core
MODEL = "depth-anything/Depth-Anything-V2-Small-hf"

_pipe = None

# Decisão de efeito pré-fabricada (motion_director da -fix). O worker adianta,
# por painel: (1) o depth do parallax E (2) qual dos 121 efeitos aplicar.
# A decisão é uma SUGESTÃO cacheada por md5 — no render, o pipeline ainda aplica
# suas salvaguardas (+18/texto-plano). Usa Haiku (NÃO Gemini) → não compete com a
# quota Gemini que a narração dos vídeos consome (regra #8).
_md_mod = None


def get_motion_director():
    global _md_mod
    if _md_mod is None:
        import importlib.util
        try:
            if str(FIX_BIN) not in sys.path:
                sys.path.insert(0, str(FIX_BIN))
            spec = importlib.util.spec_from_file_location(
                "motion_director", FIX_BIN / "motion_director.py")
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            _md_mod = mod
        except Exception as e:
            log(f"  ⚠ motion_director indisponível ({type(e).__name__}: {str(e)[:60]}) — só depth")
            _md_mod = False
    return _md_mod or None


def log(m):
    line = f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {m}"
    print(line, flush=True)
    try:
        LOG.parent.mkdir(parents=True, exist_ok=True)
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass


def ffmpeg_rodando():
    """True se houver ffmpeg ativo (render do hipercool) — então não competir."""
    try:
        r = subprocess.run(["tasklist", "/fo", "csv", "/nh"],
                           capture_output=True, timeout=15)
        return b"ffmpeg.exe" in r.stdout.lower()
    except Exception:
        return False  # na dúvida, segue (cron pode rodar em máquina sem tasklist)


def md5_arquivo(p, chunk=1 << 20):
    h = hashlib.md5()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(chunk), b""):
            h.update(b)
    return h.hexdigest()


def get_pipe():
    global _pipe
    if _pipe is None:
        from transformers import pipeline
        t0 = time.time()
        log(f"carregando modelo {MODEL} (1x)...")
        _pipe = pipeline("depth-estimation", model=MODEL)
        log(f"modelo carregado em {time.time()-t0:.1f}s")
    return _pipe


def gerar_depth(img_path, out_png):
    from PIL import Image
    img = Image.open(img_path).convert("RGB").resize(TARGET)
    t0 = time.time()
    out = get_pipe()(img)
    out["depth"].convert("L").save(out_png)
    return time.time() - t0


def listar_paineis(filtro_obra=None):
    if not PANELS_ROOT.exists():
        log(f"PANELS_ROOT não existe: {PANELS_ROOT}")
        return []
    paineis = []
    for capdir in sorted(PANELS_ROOT.iterdir()):
        if not capdir.is_dir() or capdir.name.startswith("_"):
            continue
        if filtro_obra and filtro_obra.lower() not in capdir.name.lower():
            continue
        for img in sorted(capdir.glob("*.jpg")):
            if not img.name.startswith("_"):
                paineis.append(img)
    return paineis


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--obra", default=None, help="filtra caps por substring do nome")
    ap.add_argument("--limit", type=int, default=0, help="para após N depths novos")
    ap.add_argument("--once", action="store_true", help="processa 1 e sai")
    ap.add_argument("--ignore-ffmpeg", action="store_true", help="roda mesmo com render ativo")
    ap.add_argument("--no-efeito", action="store_true", help="só depth, não pré-decide efeito")
    args = ap.parse_args()

    CACHE_DEPTH.mkdir(parents=True, exist_ok=True)
    # Liga a triagem por IA (Haiku) na decisão de efeito — worker é o lugar certo p/ isso
    # (ocioso, keyless de Gemini). Sem isto, motion_director só usa pré-filtro por regra.
    if not args.no_efeito:
        os.environ.setdefault("MOTION_DIRECTOR", "1")

    if not args.ignore_ffmpeg and ffmpeg_rodando():
        log("ffmpeg ativo (render do hipercool) → PULANDO rodada p/ não competir por CPU.")
        return 0

    paineis = listar_paineis(args.obra)
    log(f"{len(paineis)} painéis candidatos" + (f" (obra~{args.obra})" if args.obra else ""))

    feitos = novos = 0
    t_start = time.time()
    for img in paineis:
        try:
            md5 = md5_arquivo(img)
        except Exception as e:
            log(f"  skip (md5 falhou) {img.name}: {e}")
            continue
        out_png = CACHE_DEPTH / f"{md5}.png"
        if out_png.exists() and out_png.stat().st_size > 0:
            feitos += 1
            continue
        # re-checa ffmpeg a cada painel (render pode começar no meio)
        if not args.ignore_ffmpeg and ffmpeg_rodando():
            log("ffmpeg começou a rodar → parando rodada (retoma na próxima).")
            break
        try:
            dt = gerar_depth(img, out_png)
            novos += 1
            log(f"  ✓ depth {img.parent.name}/{img.name} ({dt:.1f}s) [{novos} novos]")
        except Exception as e:
            log(f"  ✗ falha {img.name}: {type(e).__name__}: {str(e)[:80]}")
            continue
        # Pré-decide o efeito ideal do painel (cacheado por md5). Best-effort:
        # nunca deixa a decisão de efeito derrubar o prefetch de depth.
        if not args.no_efeito:
            md = get_motion_director()
            if md:
                try:
                    dec = md.decidir_efeito(str(img))
                    if dec and dec.get("fonte") not in ("none", None):
                        log(f"     ↳ efeito: {dec.get('efeito')} [{dec.get('categoria')}] ({dec.get('fonte')})")
                except Exception as e:
                    log(f"     ↳ ⚠ decisão de efeito falhou: {type(e).__name__}: {str(e)[:60]}")
        if args.once or (args.limit and novos >= args.limit):
            break

    log(f"FIM: {novos} novos, {feitos} já existiam, {time.time()-t_start:.0f}s total. "
        f"Cache: {len(list(CACHE_DEPTH.glob('*.png')))} depths.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
