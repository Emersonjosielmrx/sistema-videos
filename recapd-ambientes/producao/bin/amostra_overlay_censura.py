#!/usr/bin/env python3
"""amostra_overlay_censura.py — gera AMOSTRAS de overlay em cima do painel censurado.

Problema: o painel +18 censurado fica TODO borrado e feio. Solução: pôr um overlay
por cima (placa +18 / mascote tapando / faixa interativa) pra ficar estiloso e virar
oportunidade de engajamento.

Este script SÓ gera imagens de amostra pra aprovação visual. NÃO integra no pipeline
(isso vem depois que você escolher qual estilo). Usa ffmpeg leve (imagem estática).

⚠️ NÃO rodar com um render de vídeo ativo (compete por ffmpeg). Checa sozinho e aborta.

Uso:
  PYTHONUTF8=1 D:/recapd-ambientes/producao/venv/Scripts/python.exe bin/amostra_overlay_censura.py
Saída: _amostras_overlay_censura/  (abre pra usuária comparar)
"""
import os
import sys
import glob
import subprocess
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
OUT_DIR = PROJECT_DIR / "_amostras_overlay_censura"
MASCOTE_DIR = Path("D:/hipercool-materiais/assets/mascote")
FONT = "C:/Windows/Fonts/impact.ttf"
FONT_ESC = "C\\:/Windows/Fonts/impact.ttf"  # ffmpeg escapa ':' no Windows


def _ffmpeg():
    import shutil
    return shutil.which("ffmpeg") or "ffmpeg"


def render_ativo():
    """True se há um render de vídeo rolando (não competir)."""
    try:
        out = subprocess.run(["tasklist", "/FI", "IMAGENAME eq ffmpeg.exe", "/NH"],
                             capture_output=True, timeout=15).stdout.decode("utf-8", "replace")
        n = out.count("ffmpeg.exe")
        # 0 = livre. >0 = tem ffmpeg (pode ser render). Confirma com log fresco.
        if n == 0:
            return False
        import time
        for pat in ("logs/nightshift_*.log", "logs/cap*_*.log"):
            for f in glob.glob(str(PROJECT_DIR / pat)):
                if time.time() - os.path.getmtime(f) < 180:
                    return True
        return False
    except Exception:
        return False


def achar_painel_censurado():
    """Acha um painel +18 já censurado (borrado) pra usar de base. Se não achar,
    pega um painel qualquer e borra na hora só pra amostra."""
    # 1) procura saída de censura já existente
    for pat in ("workspace/censura_cache/*.jpg", "_negtest/*.jpg"):
        achados = glob.glob(str(PROJECT_DIR / pat))
        if achados:
            return achados[0], False
    # 2) fallback: painel qualquer → borra na hora
    for pat in ("workspace/panels/the-meek-cat-cap05/*.jpg",):
        achados = sorted(glob.glob(str(PROJECT_DIR / pat)))
        if achados:
            return achados[len(achados)//2], True
    return None, False


def borrar(img_in, img_out):
    subprocess.run([_ffmpeg(), "-y", "-i", str(img_in),
                    "-vf", "gblur=sigma=40", "-q:v", "2", str(img_out)],
                   check=True, capture_output=True, timeout=60)


def amostra_placa18(base, out):
    """Placa/selo +18 PROIBIDO estilo aviso vermelho, centralizado."""
    vf = (
        "drawbox=x=0:y=ih*0.38:w=iw:h=ih*0.24:color=black@0.55:t=fill,"
        f"drawtext=fontfile='{FONT_ESC}':text='+18':fontcolor=red:fontsize=h/6:"
        "x=(w-text_w)/2:y=h*0.40:box=1:boxcolor=white@0.9:boxborderw=20,"
        f"drawtext=fontfile='{FONT_ESC}':text='CONTEUDO PROIBIDO':fontcolor=white:fontsize=h/22:"
        "x=(w-text_w)/2:y=h*0.55"
    )
    subprocess.run([_ffmpeg(), "-y", "-i", str(base), "-vf", vf, "-q:v", "2", str(out)],
                   check=True, capture_output=True, timeout=60)


def amostra_mascote(base, out):
    """Mascote (pose envergonhada) tapando a cena no canto."""
    pose = MASCOTE_DIR / "pose_shy.png"
    if not pose.exists():
        pose = MASCOTE_DIR / "pose_point.png"
    fc = (
        "[1:v]scale=-1:ih*0.55[m];"  # não dá pra usar ih do overlay; escala fixa abaixo
    )
    # Escala a mascote pra ~55% da altura do painel e cola embaixo-direita.
    fc = "[1:v]scale=iw:ih[m0];[0:v][m0]overlay=W-w-20:H-h-20"
    # mais simples: escala a mascote a uma altura fixa relativa via scale2ref
    fc = "[1:v][0:v]scale2ref=oh*mdar:ih*0.6[m][bg];[bg][m]overlay=W-w-20:H-h-10"
    subprocess.run([_ffmpeg(), "-y", "-i", str(base), "-i", str(pose),
                    "-filter_complex", fc, "-q:v", "2", str(out)],
                   check=True, capture_output=True, timeout=60)


def amostra_faixa(base, out):
    """Fita de isolamento diagonal + CTA (engajamento)."""
    vf = (
        "drawbox=x=-50:y=ih*0.44:w=iw+100:h=ih*0.12:color=yellow@0.85:t=fill,"
        f"drawtext=fontfile='{FONT_ESC}':text='CENA CENSURADA':fontcolor=black:fontsize=h/20:"
        "x=(w-text_w)/2:y=h*0.46,"
        f"drawtext=fontfile='{FONT_ESC}':text='VEJA SEM CENSURA NO LINK':fontcolor=white:fontsize=h/30:"
        "x=(w-text_w)/2:y=h*0.62:box=1:boxcolor=red@0.8:boxborderw=10"
    )
    subprocess.run([_ffmpeg(), "-y", "-i", str(base), "-vf", vf, "-q:v", "2", str(out)],
                   check=True, capture_output=True, timeout=60)


def amostra_redacted(base, out):
    """Carimbo REDACTED / SCENE MISSING estilo censura de documento."""
    vf = (
        "drawbox=x=0:y=ih*0.42:w=iw:h=ih*0.16:color=black:t=fill,"
        f"drawtext=fontfile='{FONT_ESC}':text='[ REDACTED ]':fontcolor=white:fontsize=h/16:"
        "x=(w-text_w)/2:y=h*0.44"
    )
    subprocess.run([_ffmpeg(), "-y", "-i", str(base), "-vf", vf, "-q:v", "2", str(out)],
                   check=True, capture_output=True, timeout=60)


def amostra_loading(base, out):
    """Meme 'loading 18+…' com selo redondo."""
    vf = (
        "drawbox=x=0:y=0:w=iw:h=ih:color=black@0.35:t=fill,"
        f"drawtext=fontfile='{FONT_ESC}':text='loading 18+...':fontcolor=white:fontsize=h/14:"
        "x=(w-text_w)/2:y=(h-text_h)/2,"
        f"drawtext=fontfile='{FONT_ESC}':text='imagina a cena':fontcolor=yellow:fontsize=h/28:"
        "x=(w-text_w)/2:y=h*0.60"
    )
    subprocess.run([_ffmpeg(), "-y", "-i", str(base), "-vf", vf, "-q:v", "2", str(out)],
                   check=True, capture_output=True, timeout=60)


def main():
    if render_ativo():
        print("⚠ Render de vídeo ativo — ABORTANDO pra não competir. Rode quando a máquina estiver livre.")
        sys.exit(0)

    painel, precisa_borrar = achar_painel_censurado()
    if not painel:
        print("ERRO: não achei nenhum painel de base. Confira workspace/panels/.")
        sys.exit(1)

    OUT_DIR.mkdir(exist_ok=True)
    base = OUT_DIR / "0_base_censurada.jpg"
    if precisa_borrar:
        print(f"Borrando painel de base: {Path(painel).name}")
        borrar(painel, base)
    else:
        subprocess.run(["cp", str(painel), str(base)], check=True)

    amostras = [
        ("1_placa18", amostra_placa18),
        ("2_mascote", amostra_mascote),
        ("3_faixa_cta", amostra_faixa),
        ("4_redacted", amostra_redacted),
        ("5_loading18", amostra_loading),
    ]
    for nome, fn in amostras:
        out = OUT_DIR / f"{nome}.jpg"
        try:
            fn(base, out)
            print(f"✓ {nome}")
        except Exception as e:
            err = getattr(e, "stderr", b"")
            if isinstance(err, bytes):
                err = err.decode("utf-8", "replace")
            print(f"✗ {nome}: {str(e)[:100]} {err[-200:] if err else ''}")

    print(f"\nAmostras em: {OUT_DIR}")


if __name__ == "__main__":
    main()
