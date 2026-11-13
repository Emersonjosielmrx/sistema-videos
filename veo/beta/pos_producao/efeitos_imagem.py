# -*- coding: utf-8 -*-
"""efeitos_imagem.py — anima uma imagem estática em clip CURTO (~8s) via ffmpeg.

Portado do D:\\historias-em-frames (efeitos CPU-only, sem GPU, sem crédito):
- parallax/zoompan (advanced_parallax.py) → zoom_in/out, pan, dynamic_tilt (2.5D fake)
- catálogo de movimentos cinematográficos (fx_assets.py MOVEMENTS_*)

Diferença: o historias faz clips longos; aqui a duração é curta (default 8s,
casando com o vídeo do Veo). Tudo ffmpeg puro — nenhuma dependência de IA.

Uso:
    from efeitos_imagem import animar_imagem, ESTILOS
    animar_imagem("foto.jpg", "clip.mp4", duracao=8, estilo="dynamic_tilt")
"""
import subprocess
from pathlib import Path

_FFMPEG = r"D:\hipercool-materiais\bin\ffmpeg.exe"
_FPS = 30

# Estilos disponíveis (nome → descrição curta)
ESTILOS = {
    "zoom_in":      "zoom lento pra dentro (tensão/drama)",
    "zoom_out":     "zoom lento pra fora (revelação/calma)",
    "pan_right":    "desliza pra direita (exploração)",
    "pan_left":     "desliza pra esquerda",
    "pan_up":       "sobe (revela de baixo pra cima)",
    "pan_down":     "desce",
    "dynamic_tilt": "2.5D fake: fundo desfocado + primeiro plano com zoom (ação/épico)",
    "punch_in":     "zoom rápido de impacto (choque/gancho)",
}


def build_filter(estilo, duracao, w=720, h=1280):
    """Retorna a string de filtro ffmpeg pro estilo. Duração em segundos."""
    fps = _FPS
    frames = max(1, int(duracao * fps))
    base = f"scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h}"

    if estilo == "zoom_in":
        zp = (f"zoompan=z='min(1.15,zoom+{0.15/frames:.6f})':d={frames}:"
              f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':fps={fps}:s={w}x{h}")
        return f"{base},{zp}"

    if estilo == "zoom_out":
        zp = (f"zoompan=z='1.15-(on*{0.15/frames:.6f})':d={frames}:"
              f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':fps={fps}:s={w}x{h}")
        return f"{base},{zp}"

    if estilo == "pan_right":
        zp = (f"zoompan=z='1.1':d={frames}:"
              f"x='(iw-iw/1.1)*(on/{frames})':y='ih/2-(ih/zoom/2)':fps={fps}:s={w}x{h}")
        return f"{base},{zp}"

    if estilo == "pan_left":
        zp = (f"zoompan=z='1.1':d={frames}:"
              f"x='(iw-iw/1.1)*(1-on/{frames})':y='ih/2-(ih/zoom/2)':fps={fps}:s={w}x{h}")
        return f"{base},{zp}"

    if estilo == "pan_up":
        zp = (f"zoompan=z='1.1':d={frames}:"
              f"x='iw/2-(iw/zoom/2)':y='(ih-ih/1.1)*(1-on/{frames})':fps={fps}:s={w}x{h}")
        return f"{base},{zp}"

    if estilo == "pan_down":
        zp = (f"zoompan=z='1.1':d={frames}:"
              f"x='iw/2-(iw/zoom/2)':y='(ih-ih/1.1)*(on/{frames})':fps={fps}:s={w}x{h}")
        return f"{base},{zp}"

    if estilo == "punch_in":
        # zoom rápido nos primeiros ~1.5s, depois segura — gancho de impacto
        zp = (f"zoompan=z='min(1.3,zoom+{0.3/(fps*1.5):.6f})':d={frames}:"
              f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':fps={fps}:s={w}x{h}")
        return f"{base},{zp}"

    if estilo == "dynamic_tilt":
        # 2.5D fake: fundo desfocado com zoom-out + primeiro plano central com zoom-in
        bg = (f"zoompan=z='1.1-(on*{0.1/frames:.6f})':d={frames}:"
              f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':fps={fps}:s={w}x{h}")
        fg = (f"zoompan=z='min(1.5,zoom+{0.003:.6f})':d={frames}:"
              f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':fps={fps}:s={w}x{h}")
        return (f"[0:v]{base},split=2[bgb][fgb];"
                f"[bgb]boxblur=10:5,{bg}[bg];"
                f"[fgb]crop=iw*0.6:ih*0.6:iw*0.2:ih*0.2,{fg}[fg];"
                f"[bg][fg]overlay=(W-w)/2:(H-h)/2")

    return build_filter("zoom_in", duracao, w, h)


def animar_imagem(img_path, out_path, duracao=8.0, estilo="zoom_in",
                  w=720, h=1280, com_audio_silencio=True):
    """Anima uma imagem estática em clip mp4 de `duracao` segundos.

    dynamic_tilt usa filter_complex (múltiplos streams); os outros usam -vf.
    Retorna True se gerou o mp4.
    """
    filtro = build_filter(estilo, duracao, w, h)
    is_complex = filtro.startswith("[0:v]")
    # CRITICO: a imagem entra SEM -loop/-t. O zoompan gera todos os frames via
    # d={frames}. Se usar -loop 1 -t, o ffmpeg alimenta N frames e o zoompan
    # gera d frames PARA CADA UM (explosao N*d) -> trava. (bug classico)
    cmd = [_FFMPEG, "-y", "-hide_banner", "-loglevel", "error", "-i", str(img_path)]
    if com_audio_silencio:
        cmd += ["-f", "lavfi", "-t", f"{duracao:.3f}",
                "-i", "anullsrc=channel_layout=stereo:sample_rate=44100"]
    if is_complex:
        # dynamic_tilt: filter_complex; a saída de vídeo é a última cadeia sem label
        cmd += ["-filter_complex", filtro]
        if com_audio_silencio:
            cmd += ["-map", "1:a"]
    else:
        cmd += ["-vf", filtro]
        if com_audio_silencio:
            cmd += ["-map", "0:v", "-map", "1:a"]
    cmd += ["-c:v", "libx264", "-preset", "veryfast", "-crf", "21",
            "-pix_fmt", "yuv420p", "-r", str(_FPS), "-t", f"{duracao:.3f}",
            "-movflags", "+faststart", str(out_path)]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
    if r.returncode != 0:
        print(f"[efeitos_imagem] {estilo} err: {r.stderr[-300:]}", flush=True)
    return r.returncode == 0 and Path(out_path).exists()


def estilo_por_mood(mood):
    """Mapeia clima narrativo → estilo (portado do advanced_parallax)."""
    m = (mood or "").lower()
    if any(x in m for x in ["acao", "ação", "fight", "epico", "épico", "batalha", "impacto"]):
        return "dynamic_tilt"
    if any(x in m for x in ["choque", "gancho", "urgente", "atencao", "atenção"]):
        return "punch_in"
    if any(x in m for x in ["tenso", "drama", "medo", "suspense", "dark"]):
        return "zoom_in"
    if any(x in m for x in ["calmo", "triste", "paz", "melancol"]):
        return "zoom_out"
    if any(x in m for x in ["explora", "viagem", "jornada", "cenario", "cenário"]):
        return "pan_right"
    return "zoom_in"


if __name__ == "__main__":
    import sys
    img = sys.argv[1] if len(sys.argv) > 1 else None
    if not img:
        print("uso: efeitos_imagem.py <imagem> [duracao] [estilo|all]")
        print("estilos:", ", ".join(ESTILOS))
        sys.exit(0)
    dur = float(sys.argv[2]) if len(sys.argv) > 2 else 8.0
    estilo = sys.argv[3] if len(sys.argv) > 3 else "all"
    outdir = Path(__file__).resolve().parent / "tmp" / "amostras_efeitos"
    outdir.mkdir(parents=True, exist_ok=True)
    estilos = list(ESTILOS) if estilo == "all" else [estilo]
    for e in estilos:
        out = outdir / f"efeito_{e}.mp4"
        ok = animar_imagem(img, out, duracao=dur, estilo=e)
        print(f"  {e:14} {'OK' if ok else 'FALHOU'} -> {out}")
    print("pasta:", outdir.resolve())
