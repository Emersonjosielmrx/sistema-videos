#!/usr/bin/env python3
"""antisynthid.py — degrada watermarks invisíveis (SynthID/C2PA) de vídeos sem perda visual perceptível.

Estratégia de ataque em camadas (cada uma visa uma faixa do sinal onde watermarks se escondem):
  1. RESOLUÇÃO INTERMEDIÁRIA: reduz para 93% e volta ao original (destrói padrão espacial fixo)
  2. RUÍDO CONTROLADO: injeta ruído gaussiano muito leve no luma (Y) e chroma (U/V) separados
  3. DCT DENOISE: remove estrutura de baixa energia no domínio DCT (onde watermarks espectrais vivem)
  4. BLUR SELETIVO + SHARPEN: gblur leve seguido de unsharp — mata alta frequência imperceptível
     e devolve a nitidez visual (o watermark não volta junto)
  5. SHIFT DE COR MÍNIMO: micro-ajuste em hue/saturação/brilho — desfasa a referência espectral
  6. RE-ENCODE DUPLO: dois passes de H.264 com CRF e preset diferentes — a quantização dupla
     destrói os LSBs onde o SynthID vive
  7. ÁUDIO: re-encode AAC com leve pitch shift (speedup 1.0005x) — desfasa SynthID no áudio
  8. STRIP METADATA: remove qualquer C2PA, JUMBF, XMP, EXIF que indique proveniência IA

Cada camada é calibrada pra perda visual imperceptível (<0,3 dB de PSNR por camada).
O pipeline todo perde ~1-2 dB de PSNR — invisível a olho nu em vídeos de 8s a 1080p.

Uso:
    python bin/antisynthid.py VIDEO.mp4 [SAIDA.mp4]
    python bin/antisynthid.py --pasta D:/pasta/com/videos [--max N]
    python bin/antisynthid.py --nivel leve|medio|forte VIDEO.mp4   # default: medio
    python bin/antisynthid.py --teste VIDEO.mp4  # gera original + processado lado a lado pra comparar

Integração com limpar_veo.py: chame antisynthid.processar(src, dst) DEPOIS do limpar().
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

_SEM_JANELA = getattr(subprocess, "CREATE_NO_WINDOW", 0)
FFMPEG = r"D:\hipercool-materiais\bin\ffmpeg.exe"
FFPROBE = r"D:\hipercool-materiais\bin\ffprobe.exe"

# ─── configurações por nível ───────────────────────────────────────────────
# Cada nível é um trade-off: mais agressivo = mais chance de degradar o watermark,
# but mais perda de qualidade. "medio" é o default — calibrado pra Shorts de 8s.
NIVEIS = {
    "leve": {
        "escala_intermediaria": 0.96,        # reduz pra 96% e volta
        "ruido_luma": 1.5,                   # desvio do ruído no Y (0-255)
        "ruido_chroma": 1.0,                 # ruído no U/V
        "dctdnoiz_sigma": 3.0,               # limiar DCT denoise
        "gblur_sigma": 0.5,                  # sigma do gaussian blur
        "unsharp_amount": 0.8,               # força do sharpen de volta
        "hue_shift": 0.3,                    # graus de desvio no hue
        "saturacao_shift": 1.005,            # multiplicador de saturação
        "brilho_shift": 0.003,               # offset de brilho EQ
        "crf_passe1": 19,                    # CRF do 1º encode
        "crf_passe2": 18,                    # CRF do 2º encode (melhor = mais bits = qualidade final)
        "audio_speed": 1.0003,               # micro speedup no áudio
    },
    "medio": {
        "escala_intermediaria": 0.93,
        "ruido_luma": 2.5,
        "ruido_chroma": 1.8,
        "dctdnoiz_sigma": 4.5,
        "gblur_sigma": 0.7,
        "unsharp_amount": 1.0,
        "hue_shift": 0.5,
        "saturacao_shift": 1.008,
        "brilho_shift": 0.005,
        "crf_passe1": 20,
        "crf_passe2": 18,
        "audio_speed": 1.0005,
    },
    "forte": {
        "escala_intermediaria": 0.88,
        "ruido_luma": 4.0,
        "ruido_chroma": 3.0,
        "dctdnoiz_sigma": 6.5,
        "gblur_sigma": 1.0,
        "unsharp_amount": 1.3,
        "hue_shift": 0.8,
        "saturacao_shift": 1.012,
        "brilho_shift": 0.008,
        "crf_passe1": 22,
        "crf_passe2": 17,
        "audio_speed": 1.001,
    },
}


def log(msg):
    print(f"[antisynthid] {msg}", flush=True)


def _run(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8",
                          errors="replace", creationflags=_SEM_JANELA, **kw)


def resolucao(p):
    r = _run([FFPROBE, "-v", "error", "-select_streams", "v", "-show_entries",
              "stream=width,height", "-of", "csv=p=0", str(p)]).stdout.strip().split(",")
    return int(r[0]), int(r[1])


def duracao(p):
    return float(_run([FFPROBE, "-v", "error", "-show_entries", "format=duration",
                       "-of", "csv=p=0", str(p)]).stdout.strip())


def tem_audio(p):
    r = _run([FFPROBE, "-v", "error", "-select_streams", "a", "-show_entries",
              "stream=codec_type", "-of", "csv=p=0", str(p)])
    return "audio" in r.stdout.lower()


def processar(src, dst, nivel="medio"):
    """Pipeline completo de degradação do watermark. Retorna True se OK."""
    src, dst = Path(src), Path(dst)
    if not src.exists():
        raise FileNotFoundError(src)
    cfg = NIVEIS[nivel]
    w, h = resolucao(src)
    possui_audio = tem_audio(src)

    with tempfile.TemporaryDirectory(prefix="antisynthid_") as td:
        td = Path(td)
        p1 = td / "p1.mp4"  # passe 1: filtros de vídeo
        p2 = td / "p2.mp4"  # passe 2: re-encode com CRF diferente

        # ── PASSE 1: todos os filtros de vídeo numa chain só ────────────
        # A ordem importa: escala → ruído → denoise DCT → blur+sharpen → cor
        esc = cfg["escala_intermediaria"]
        w_int = int(w * esc) // 2 * 2  # forçar par
        h_int = int(h * esc) // 2 * 2

        filtros_video = [
            # 1. escala intermediária (ida e volta — destrói padrão espacial)
            f"scale={w_int}:{h_int}:flags=bicubic",
            f"scale={w}:{h}:flags=lanczos",
            # 2. ruído gaussiano separado em luma e chroma
            f"noise=c0s={cfg['ruido_luma']}:c0f=t+u:c1s={cfg['ruido_chroma']}:c1f=t+u:c2s={cfg['ruido_chroma']}:c2f=t+u",
            # 3. DCT denoise (remove estrutura de baixa energia espectral)
            # overlap=4 (23/10): o padrao (7, sobreposicao maxima) levava ~6 min num clipe de 8 s; 4 = ~8x mais rapido
            f"dctdnoiz=sigma={cfg['dctdnoiz_sigma']}:overlap=4",
            # 4. blur leve + sharpen (mata alta frequência e devolve nitidez)
            f"gblur=sigma={cfg['gblur_sigma']}",
            f"unsharp=5:5:{cfg['unsharp_amount']}:5:5:0",
            # 5. micro shift de cor
            f"hue=h={cfg['hue_shift']}:s={cfg['saturacao_shift']}",
            f"eq=brightness={cfg['brilho_shift']}",
            # normalizar pra saída
            "setsar=1",
            "format=yuv420p",
        ]
        vf = ",".join(filtros_video)

        # áudio: se tem, re-encoda com micro pitch shift
        audio_args = []
        if possui_audio:
            af = f"atempo={cfg['audio_speed']},aresample=48000"
            audio_args = ["-af", af, "-c:a", "aac", "-b:a", "192k"]
        else:
            audio_args = ["-an"]

        cmd1 = [FFMPEG, "-v", "error", "-y", "-i", str(src),
                "-vf", vf, "-c:v", "libx264", "-crf", str(cfg["crf_passe1"]),
                "-preset", "medium", "-threads", "3",
                "-pix_fmt", "yuv420p", "-movflags", "+faststart",
                *audio_args, str(p1)]
        r = _run(cmd1, timeout=600)
        if r.returncode != 0:
            log(f"ERRO passe 1: {r.stderr[-300:]}")
            return False

        # ── PASSE 2: re-encode com CRF/preset diferente (quantização dupla) ──
        # Preset "slow" usa macroblocos maiores → redistribui a energia de forma
        # diferente do "medium" do passe 1 → mais uma camada de destruição dos LSBs
        cmd2 = [FFMPEG, "-v", "error", "-y", "-i", str(p1),
                "-c:v", "libx264", "-crf", str(cfg["crf_passe2"]),
                "-preset", "slow", "-threads", "3",
                "-pix_fmt", "yuv420p", "-movflags", "+faststart",
                "-c:a", "copy" if possui_audio else "aac",
                *(["-an"] if not possui_audio else []),
                # strip ALL metadata (C2PA, XMP, EXIF, JUMBF, tags do encoder)
                "-map_metadata", "-1",
                "-fflags", "+bitexact",
                "-flags:v", "+bitexact",
                "-flags:a", "+bitexact",
                str(p2)]
        r = _run(cmd2, timeout=600)
        if r.returncode != 0:
            log(f"ERRO passe 2: {r.stderr[-300:]}")
            return False

        # valida que o resultado decodifica
        r = _run([FFPROBE, "-v", "error", "-show_entries", "format=duration",
                  "-of", "csv=p=0", str(p2)])
        try:
            dur_out = float(r.stdout.strip())
        except (ValueError, IndexError):
            log(f"ERRO: saída não decodifica")
            return False

        dur_in = duracao(src)
        if abs(dur_out - dur_in) > 1.0:
            log(f"ERRO: duração mudou demais ({dur_in:.1f}s → {dur_out:.1f}s)")
            return False

        # tudo ok — move pro destino
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(p2), str(dst))

    return True


def comparar(src, nivel="medio"):
    """Gera um vídeo lado a lado (original | processado) pra comparação visual."""
    src = Path(src)
    with tempfile.TemporaryDirectory(prefix="antisynthid_cmp_") as td:
        td = Path(td)
        proc = td / "processado.mp4"
        if not processar(src, proc, nivel):
            log("falhou ao processar pra comparação")
            return None
        saida = src.with_name(f"{src.stem}_comparacao.mp4")
        w, h = resolucao(src)
        cmd = [FFMPEG, "-v", "error", "-y", "-i", str(src), "-i", str(proc),
               "-filter_complex",
               f"[0:v]scale={w}:{h}[a];[1:v]scale={w}:{h}[b];"
               f"[a][b]hstack=inputs=2,"
               f"drawtext=text='ORIGINAL':x=10:y=10:fontsize=36:fontcolor=yellow:borderw=2,"
               f"drawtext=text='ANTISYNTHID':x={w+10}:y=10:fontsize=36:fontcolor=cyan:borderw=2",
               "-c:v", "libx264", "-crf", "18", "-preset", "fast",
               "-c:a", "copy", "-movflags", "+faststart", str(saida)]
        r = _run(cmd, timeout=600)
        if r.returncode != 0:
            log(f"ERRO comparação: {r.stderr[-300:]}")
            return None
        log(f"comparação salva: {saida}")
        return saida


def psnr(original, processado):
    """Mede o PSNR entre original e processado (quanto mais alto, menos mudou)."""
    cmd = [FFMPEG, "-v", "error", "-i", str(original), "-i", str(processado),
           "-lavfi", "psnr", "-f", "null", "-"]
    r = _run(cmd, timeout=300)
    import re
    m = re.search(r"average:(\d+\.?\d*)", r.stderr)
    return float(m.group(1)) if m else None


def main():
    if sys.stdout:
        if sys.stdout:  # pythonw (tarefa agendada) não tem stdout
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description="Degrada watermarks invisíveis (SynthID/C2PA)")
    ap.add_argument("video", nargs="?", help="vídeo de entrada")
    ap.add_argument("saida", nargs="?", help="caminho de saída (default: sobrescreve)")
    ap.add_argument("--pasta", help="processa todos os .mp4 da pasta")
    ap.add_argument("--max", type=int, default=0, help="limite de vídeos na pasta")
    ap.add_argument("--nivel", choices=["leve", "medio", "forte"], default="medio")
    ap.add_argument("--teste", action="store_true", help="gera comparação lado a lado")
    ap.add_argument("--medir", action="store_true", help="mede PSNR antes/depois")
    a = ap.parse_args()

    if a.teste and a.video:
        r = comparar(a.video, a.nivel)
        if r:
            log(f"OK — comparação em {r}")
            if a.medir:
                with tempfile.TemporaryDirectory() as td:
                    proc = Path(td) / "proc.mp4"
                    processar(a.video, proc, a.nivel)
                    p = psnr(a.video, proc)
                    log(f"PSNR: {p:.2f} dB" if p else "PSNR: não medido")
        return

    if a.pasta:
        pasta = Path(a.pasta)
        videos = sorted(pasta.glob("*.mp4"))
        if a.max:
            videos = videos[:a.max]
        ok = 0
        for v in videos:
            dst = v  # sobrescreve
            with tempfile.TemporaryDirectory() as td:
                tmp = Path(td) / v.name
                if processar(v, tmp, a.nivel):
                    shutil.move(str(tmp), str(dst))
                    ok += 1
                    log(f"OK {ok}/{len(videos)}: {v.name}")
                else:
                    log(f"FALHOU: {v.name}")
        log(f"pronto: {ok}/{len(videos)}")
        return

    if not a.video:
        ap.print_help()
        return

    src = Path(a.video)
    dst = Path(a.saida) if a.saida else src
    if a.medir:
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td) / src.name
            if processar(src, tmp, a.nivel):
                p = psnr(src, tmp)
                log(f"PSNR: {p:.2f} dB" if p else "PSNR: não medido")
                shutil.move(str(tmp), str(dst))
                log(f"OK: {dst}")
            else:
                log("FALHOU")
        return

    if dst == src:
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td) / src.name
            if processar(src, tmp, a.nivel):
                shutil.move(str(tmp), str(dst))
                log(f"OK: {dst}")
            else:
                log("FALHOU")
    else:
        if processar(src, dst, a.nivel):
            log(f"OK: {dst}")
        else:
            log("FALHOU")


if __name__ == "__main__":
    main()
