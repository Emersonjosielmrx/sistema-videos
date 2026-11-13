# -*- coding: utf-8 -*-
"""montagem.py — efeitos de MOVIMENTO e IMPACTO no video do Veo e nas junções.

Diferente de efeitos_imagem.py (que anima FOTO parada via zoompan), aqui os
efeitos vão SOBRE o video do Veo (que já tem movimento próprio):

1. punch_gancho()   — zoom rápido de impacto nos primeiros ~2s (crop animado).
                      Pontual pra não embrulhar o movimento do Veo.
2. overlay_alpha()  — sobrepõe um .mov com canal alpha (fogo/raio/glitch/chiado/
                      shockwave) em um instante do video. Assets já existentes em
                      D:\\hipercool-materiais\\assets\\overlays\\elemental.
3. transicao()      — junta dois clips com uma transição elemental (trans_fire/
                      ice/tear/water) sobreposta na emenda.

Tudo ffmpeg CPU-only. Overlays são 1080x1920 (yuva) → escalados pro tamanho do
video. Duração dos overlays: 0.5-1.6s (curtos, ideais pra pontuação).
"""
import subprocess
from pathlib import Path

_FFMPEG = r"D:\hipercool-materiais\bin\ffmpeg.exe"
_FFPROBE = r"D:\hipercool-materiais\bin\ffprobe.exe"
_ELEM = Path(r"D:\hipercool-materiais\assets\overlays\elemental")

# Catálogo curado dos efeitos que fazem sentido no veo (nome → arquivo)
OVERLAYS = {
    "raio":       "fx_lightning.mov",
    "fogo":       "fx_fire_v2.mov",
    "glitch":     "fx_glitch.mov",
    "chiado_tv":  "fx_tvoff.mov",
    "shockwave":  "fx_shockwave.mov",
    "shatter":    "fx_shatter.mov",
    "impacto":    "fx_impact.mov",
    "zoompunch":  "fx_zoompunch.mov",
    "portal":     "fx_portal.mov",
    "starburst":  "fx_starburst.mov",
    "speedlines": "fx_speedlines.mov",
    "smoke":      "fx_smoke.mov",
}
TRANSICOES = {
    "fogo":  "trans_fire.mov",
    "gelo":  "trans_ice.mov",
    "rasgo": "trans_tear.mov",
    "agua":  "trans_water.mov",
}


def _dur(path):
    try:
        r = subprocess.run(
            [_FFPROBE, "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
            capture_output=True, text=True, timeout=20)
        return float(r.stdout.strip())
    except Exception:
        return None


def _wh(path):
    try:
        r = subprocess.run(
            [_FFPROBE, "-v", "error", "-select_streams", "v:0",
             "-show_entries", "stream=width,height", "-of", "csv=p=0:s=x", str(path)],
            capture_output=True, text=True, timeout=20)
        w, h = r.stdout.strip().split("x")[:2]
        return int(w), int(h)
    except Exception:
        return 720, 1280


# ---------------------------------------------------------------------------
# 1. Punch-in no gancho (zoom de impacto nos primeiros segundos)
# ---------------------------------------------------------------------------
def punch_gancho(video_in, video_out, intensidade=0.12, dur_zoom=1.5):
    """Zoom rápido 1.0 -> (1+intensidade) nos primeiros dur_zoom s, depois segura.

    Crop animado pelo tempo (zoompan NÃO serve pra vídeo). Dimensões pares
    garantidas via 2*floor(.../2). Preserva áudio.
    """
    w, h = _wh(video_in)
    z = f"(1+{intensidade}*min(t/{dur_zoom}\\,1))"
    vf = (f"crop=w='2*floor(iw/{z}/2)':h='2*floor(ih/{z}/2)':"
          f"x='(iw-ow)/2':y='(ih-oh)/2',scale={w}:{h},setsar=1")
    cmd = [_FFMPEG, "-y", "-hide_banner", "-loglevel", "error",
           "-i", str(video_in), "-vf", vf,
           "-c:v", "libx264", "-preset", "veryfast", "-crf", "21",
           "-c:a", "copy", "-movflags", "+faststart", str(video_out)]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
    if r.returncode != 0:
        print(f"[montagem] punch err: {r.stderr[-300:]}", flush=True)
    return r.returncode == 0 and Path(video_out).exists()


# ---------------------------------------------------------------------------
# 2. Overlay de efeito alpha num instante do vídeo
# ---------------------------------------------------------------------------
def overlay_alpha(video_in, video_out, efeito="raio", inicio=0.0, escala=1.0):
    """Sobrepõe um overlay alpha (OVERLAYS[efeito]) começando em `inicio` s.

    O overlay é escalado pro tamanho do vídeo (× escala) e centralizado.
    Só aparece durante sua própria duração; o resto do vídeo fica intacto.
    """
    ov = _ELEM / OVERLAYS.get(efeito, OVERLAYS["raio"])
    if not ov.exists():
        print(f"[montagem] overlay ausente: {ov}", flush=True)
        return False
    w, h = _wh(video_in)
    ow, oh = int(w * escala), int(h * escala)
    od = _dur(ov) or 0.8
    fim = inicio + od
    fc = (
        f"[1:v]scale={ow}:{oh},setpts=PTS-STARTPTS+{inicio}/TB[ov];"
        f"[0:v][ov]overlay=(W-w)/2:(H-h)/2:"
        f"enable='between(t,{inicio:.3f},{fim:.3f})':eof_action=pass[v]"
    )
    cmd = [_FFMPEG, "-y", "-hide_banner", "-loglevel", "error",
           "-i", str(video_in), "-i", str(ov),
           "-filter_complex", fc, "-map", "[v]", "-map", "0:a?",
           "-c:v", "libx264", "-preset", "veryfast", "-crf", "21",
           "-c:a", "copy", "-movflags", "+faststart", str(video_out)]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
    if r.returncode != 0:
        print(f"[montagem] overlay err: {r.stderr[-400:]}", flush=True)
    return r.returncode == 0 and Path(video_out).exists()


# ---------------------------------------------------------------------------
# 3. Transição elemental entre dois clips (na emenda)
# ---------------------------------------------------------------------------
def transicao(clip_a, clip_b, video_out, tipo="fogo"):
    """Concatena A+B com a transição elemental sobreposta na emenda.

    Estratégia simples e robusta: concat A+B (mesmo WxH/fps) e sobrepõe o
    trans_*.mov centrado no ponto de junção (dur_A). Áudio = concat dos dois.
    """
    tr = _ELEM / TRANSICOES.get(tipo, TRANSICOES["fogo"])
    if not tr.exists():
        print(f"[montagem] transicao ausente: {tr}", flush=True)
        return False
    w, h = _wh(clip_a)
    da = _dur(clip_a) or 0.0
    td = _dur(tr) or 0.9
    # a transição cobre a emenda MAS preserva o final do clip A (clímax + voz):
    # toca só ~0.12s antes do corte (imperceptível) e o resto por cima do clip B.
    pre = min(0.12, td * 0.15)
    ini = max(0.0, da - pre)
    fim = ini + td
    fc = (
        f"[0:v]scale={w}:{h},setsar=1,fps=30[a];"
        f"[1:v]scale={w}:{h},setsar=1,fps=30[b];"
        f"[a][b]concat=n=2:v=1:a=0[cat];"
        f"[2:v]scale={w}:{h},setpts=PTS-STARTPTS+{ini}/TB[tr];"
        f"[cat][tr]overlay=0:0:enable='between(t,{ini:.3f},{fim:.3f})':eof_action=pass[v];"
        f"[0:a][1:a]concat=n=2:v=0:a=1[aud]"
    )
    cmd = [_FFMPEG, "-y", "-hide_banner", "-loglevel", "error",
           "-i", str(clip_a), "-i", str(clip_b), "-i", str(tr),
           "-filter_complex", fc, "-map", "[v]", "-map", "[aud]",
           "-c:v", "libx264", "-preset", "veryfast", "-crf", "21",
           "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", str(video_out)]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
    if r.returncode != 0:
        print(f"[montagem] transicao err: {r.stderr[-400:]}", flush=True)
    return r.returncode == 0 and Path(video_out).exists()


if __name__ == "__main__":
    import sys
    vid = sys.argv[1]
    outdir = Path(__file__).resolve().parent / "tmp" / "teste_montagem"
    outdir.mkdir(parents=True, exist_ok=True)
    print("=== punch no gancho ===")
    print(" ", punch_gancho(vid, outdir / "1_punch.mp4"))
    print("=== overlay raio (t=0.3) ===")
    print(" ", overlay_alpha(vid, outdir / "2_raio.mp4", "raio", inicio=0.3))
    print("=== overlay chiado_tv (t=0) ===")
    print(" ", overlay_alpha(vid, outdir / "3_chiado.mp4", "chiado_tv", inicio=0.0))
    print("pasta:", outdir.resolve())
