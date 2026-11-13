#!/usr/bin/env python3
"""
story-pipeline.py — Pipeline keyless de vídeo de história ORIGINAL.

Fluxo (tudo grátis, sem chave paga exceto Gemini que já é do projeto):
  1. Gemini: gera roteiro original (tema livre) segmentado em N cenas (texto + prompt visual)
  2. edge-tts: narra cada cena (pt-BR), keyless
  3. Pollinations: 1 imagem por cena, keyless (via scene-images.py)
  4. ffmpeg: clip Ken Burns (zoompan) por cena, com duração = áudio da cena
  5. concat -> vídeo NORMAL
  6. hyperframes: 1 passada ffmpeg (scale+crop, áudio intacto)

Formatos: 16x9 (longo) e/ou 9x16 (shorts).

Uso:
  python bin/story-pipeline.py --tema "perdeu tudo e recomeçou" --cenas 6 --format 16x9
"""
import argparse, json, re, subprocess, sys, time, urllib.parse, urllib.request
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT / "bin"))
import gemini_llm

WORK = PROJECT / "workspace" / "stories"
FORMATS = {"16x9": (1920, 1080), "9x16": (1080, 1920)}
NARRATOR_VOICE = "pt-BR-FranciscaNeural"


def log(m):
    print(f"[{time.strftime('%H:%M:%S')}] {m}", flush=True)


def slugify(s):
    s = re.sub(r"[^\w\s-]", "", s.lower()).strip()
    return re.sub(r"[\s_-]+", "-", s)[:40]


def gerar_roteiro(tema, n_cenas):
    """Gemini gera história original em N cenas: cada uma {texto, image_prompt}."""
    system = (
        "Voce e um roteirista de videos curtos de SUPERACAO/INSPIRACAO para YouTube em portugues brasileiro. "
        "Cria historias ORIGINAIS (NUNCA usa marcas, obras ou personagens existentes). "
        "Emocional, gancho forte no inicio, virada no meio, final inspirador."
    )
    user = (
        f"Tema da historia: {tema}\n\n"
        f"Crie uma historia original dividida em EXATAMENTE {n_cenas} cenas.\n"
        "Para cada cena devolva:\n"
        "  - 'texto': 1-2 frases da narracao em portugues (12-30 palavras), continuas entre cenas\n"
        "  - 'image_prompt': descricao visual EM INGLES da cena (1-2 frases, sem texto/letras na imagem)\n\n"
        "Saida JSON ESTRITA (sem markdown):\n"
        '{"titulo":"...","tags":["...","..."],"cenas":[{"texto":"...","image_prompt":"..."}]}\n'
        f"DEVE ter EXATAMENTE {n_cenas} cenas."
    )
    txt = gemini_llm.generate_text(user, system=system, max_tokens=4096, temperature=1.0)
    if not txt:
        return None
    txt = re.sub(r"^```json\s*", "", txt.strip())
    txt = re.sub(r"\s*```$", "", txt)
    try:
        return json.loads(txt)
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", txt, re.DOTALL)
        return json.loads(m.group(0)) if m else None


def narrar(texto, out_mp3, voice=NARRATOR_VOICE):
    """edge-tts CLI keyless."""
    cmd = [sys.executable, "-m", "edge_tts", "--voice", voice,
           "--text", texto, "--write-media", str(out_mp3)]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    return r.returncode == 0 and Path(out_mp3).exists()


def audio_dur(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                        "-of", "csv=p=0", str(path)], capture_output=True, text=True, timeout=30)
    try:
        return float(r.stdout.strip())
    except ValueError:
        return 0.0


def clip_ken_burns(img, audio, out, w, h, dur):
    """Clip com zoompan (Ken Burns) + áudio da cena. fps=25."""
    fps = 25
    frames = max(1, int(dur * fps))
    # zoom lento 1.0 -> 1.10 ao longo do clip, centralizado
    zoom = f"zoompan=z='min(zoom+0.0010,1.10)':d={frames}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={w}x{h}:fps={fps}"
    cmd = [
        "ffmpeg", "-y",
        "-loop", "1", "-i", str(img),
        "-i", str(audio),
        "-filter_complex", f"[0:v]scale={w*2}:{h*2},{zoom},setsar=1[v]",
        "-map", "[v]", "-map", "1:a",
        "-c:v", "libx264", "-preset", "fast", "-crf", "22", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "160k",
        "-t", f"{dur:.3f}", "-shortest",
        str(out),
    ]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    if r.returncode != 0:
        log(f"  [X] ken burns: {r.stderr[-200:]}")
    return r.returncode == 0 and Path(out).exists()


def concat_clips(clips, out):
    lst = out.parent / "_concat.txt"
    lst.write_text("".join(f"file '{c.as_posix()}'\n" for c in clips), encoding="utf-8")
    cmd = ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(lst),
           "-c", "copy", "-movflags", "+faststart", str(out)]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    if r.returncode != 0:  # fallback re-encode se -c copy falhar
        cmd = ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(lst),
               "-c:v", "libx264", "-crf", "22", "-c:a", "aac", "-movflags", "+faststart", str(out)]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=900)
    return r.returncode == 0 and Path(out).exists()


def hyperframes(normal, out):
    cmd = ["ffmpeg", "-y", "-i", str(normal),
           "-vf", "scale=iw*1.05:ih*1.05:flags=lanczos,crop=iw/1.05:ih/1.05",
           "-c:v", "libx264", "-preset", "fast", "-crf", "22",
           "-c:a", "copy", "-movflags", "+faststart", "-pix_fmt", "yuv420p", str(out)]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=1800)
    return r.returncode == 0 and Path(out).exists()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tema", required=True)
    ap.add_argument("--cenas", type=int, default=6)
    ap.add_argument("--format", choices=list(FORMATS), default="16x9")
    ap.add_argument("--slug", default=None)
    args = ap.parse_args()

    w, h = FORMATS[args.format]
    slug = args.slug or slugify(args.tema)
    base = WORK / slug
    base.mkdir(parents=True, exist_ok=True)
    log(f"=== HISTÓRIA: {args.tema} | {args.cenas} cenas | {args.format} | slug={slug} ===")

    # 1. Roteiro (cache)
    roteiro_f = base / "roteiro.json"
    if roteiro_f.exists():
        roteiro = json.loads(roteiro_f.read_text(encoding="utf-8"))
        log(f"  Roteiro [CACHE]: {roteiro.get('titulo')}")
    else:
        roteiro = gerar_roteiro(args.tema, args.cenas)
        if not roteiro or "cenas" not in roteiro:
            log("[X] Falha no roteiro"); sys.exit(1)
        roteiro_f.write_text(json.dumps(roteiro, ensure_ascii=False, indent=2), encoding="utf-8")
        log(f"  Roteiro: {roteiro.get('titulo')} ({len(roteiro['cenas'])} cenas)")

    cenas = roteiro["cenas"]

    # 2. Narração por cena (edge-tts)
    audio_dir = base / "audio"; audio_dir.mkdir(exist_ok=True)
    for i, c in enumerate(cenas, 1):
        mp3 = audio_dir / f"cena_{i}.mp3"
        if mp3.exists() and mp3.stat().st_size > 1000:
            continue
        if not narrar(c["texto"], mp3):
            log(f"[X] TTS falhou cena {i}"); sys.exit(1)
        log(f"  narração cena {i}: {audio_dur(mp3):.1f}s")

    # 3. Imagens (Pollinations via scene-images.py)
    img_dir = base / f"img_{args.format}"
    prompts_f = base / "prompts.json"
    prompts_f.write_text(json.dumps([c["image_prompt"] for c in cenas], ensure_ascii=False), encoding="utf-8")
    r = subprocess.run([sys.executable, str(PROJECT / "bin" / "scene-images.py"),
                        "--prompts-file", str(prompts_f), "--out-dir", str(img_dir),
                        "--format", args.format], timeout=1800)
    if r.returncode != 0:
        log("[!] algumas imagens falharam, seguindo com o que tem")

    # 4. Clips Ken Burns
    clips_dir = base / f"clips_{args.format}"; clips_dir.mkdir(exist_ok=True)
    clips = []
    for i, c in enumerate(cenas, 1):
        img = img_dir / f"image_{i}.jpg"
        mp3 = audio_dir / f"cena_{i}.mp3"
        out = clips_dir / f"clip_{i}.mp4"
        if not img.exists():
            log(f"  [!] sem imagem cena {i}, pulando"); continue
        dur = audio_dur(mp3)
        if clip_ken_burns(img, mp3, out, w, h, dur):
            clips.append(out)
    if not clips:
        log("[X] Nenhum clip gerado"); sys.exit(1)

    # 5. Concat -> NORMAL
    out_dir = PROJECT / "workspace" / "videos" / "historias" / slug / args.format
    out_dir.mkdir(parents=True, exist_ok=True)
    normal = out_dir / "normal.mp4"
    if not concat_clips(clips, normal):
        log("[X] concat falhou"); sys.exit(1)
    log(f"  ✅ NORMAL: {normal} ({normal.stat().st_size/1e6:.1f} MB, {audio_dur(normal):.1f}s)")

    # 6. Hyperframes
    hyper = out_dir / "hyperframes.mp4"
    if hyperframes(normal, hyper):
        log(f"  ✅ HYPERFRAMES: {hyper} ({hyper.stat().st_size/1e6:.1f} MB)")

    log("=== CONCLUÍDO ===")


if __name__ == "__main__":
    main()
