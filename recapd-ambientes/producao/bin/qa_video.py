"""qa_video.py — varredura do VÍDEO INTEIRO sem IA (LONGOS_12, Fable 29/10 — ver FABLE_DECISOES.md D10).

Hoje se confere 3–4 quadros; erro no meio passa (quadro preto, tela congelada, trecho mudo). Aqui uma passada só de
ffmpeg (decodifica em 320 px: rápido) acha, com tempos:
  - preto      blackdetect  ≥ 1,0 s de quadro preto
  - congelado  freezedetect ≥ 6 s de imagem parada (um render que travou, foto sem movimento demais)
  - mudo       silencedetect ≥ 4 s abaixo de −40 dB (trecho sem narração nem música)
  - volume     ebur128: loudness integrada (muito baixo < −24 LUFS, muito alto > −10) e pico
Resultado: dict + qa.json ao lado do vídeo. NÃO trava nada (regra da dona: só censura trava); quem chama avisa.

    python qa_video.py <video.mp4>            # imprime o resumo e grava qa.json
    from qa_video import analisar; r = analisar(mp4)   # r["problemas"] = [str], r["ok"] = sem problema grave
"""
import sys as _sys
_sys.path.insert(0, r"D:\hipercool-materiais\comum")
try:
    import sem_janela  # noqa: E402,F401 — regra da dona: nenhum processo filho abre janela na tela
except ImportError:  # 04/11: no Kaggle (Linux) não há o comum do PC nem janela pra esconder
    pass
import json
import os
import re
import subprocess
import sys
from pathlib import Path

PRETO_S, CONGELADO_S, MUDO_S = 1.0, 6.0, 4.0
MARGEM_INI, MARGEM_FIM = 0.5, 1.5  # fade de entrada/saída não conta
SEM_JANELA = 0x08000000 if sys.platform == "win32" else 0


def _ffmpeg(video):
    vf = f"scale=320:-2,blackdetect=d={PRETO_S}:pic_th=0.98:pix_th=0.10,freezedetect=n=-50dB:d={CONGELADO_S}"
    af = f"silencedetect=n=-40dB:d={MUDO_S},ebur128=peak=true"
    # 04/11 (QA dos longos no Kaggle, pesquisa qc-skill): QA_HWACCEL=cuda decodifica na GPU (NVDEC) — o longo de 80 min
    # em 1080p60 custava ~15 min de CPU só pra decodificar
    hw = ["-hwaccel", os.environ["QA_HWACCEL"]] if os.environ.get("QA_HWACCEL") else []
    cmd = ["ffmpeg", "-hide_banner", "-nostats", "-threads", "2", *hw, "-i", str(video), "-vf", vf, "-af", af,
           "-f", "null", "-"]
    r = subprocess.run(cmd, capture_output=True, text=True, errors="replace", timeout=3600, creationflags=SEM_JANELA)
    if hw and r.returncode != 0:  # GPU não decodificou: refaz na CPU (resultado vazio não pode passar como "ok")
        cmd = [c for c in cmd if c not in hw]
        r = subprocess.run(cmd, capture_output=True, text=True, errors="replace", timeout=3600, creationflags=SEM_JANELA)
    return r.stderr


def _pares(texto, ini_rx, fim_rx, dur):
    """[(ini, fim)] a partir das linhas *_start / *_end; fim aberto = até o final."""
    inis = [float(m.group(1)) for m in re.finditer(ini_rx, texto)]
    fins = [float(m.group(1)) for m in re.finditer(fim_rx, texto)]
    out = []
    for i, a in enumerate(inis):
        b = next((f for f in fins if f > a), dur)
        out.append((round(a, 1), round(b, 1)))
    return out


def analisar(video, gravar=True):
    video = Path(video)
    from anime_probe import video_duration
    dur = video_duration(str(video)) or 0.0
    txt = _ffmpeg(video)
    pretos = _pares(txt, r"black_start:\s*([\d.]+)", r"black_end:\s*([\d.]+)", dur)
    congel = _pares(txt, r"lavfi\.freezedetect\.freeze_start:\s*([\d.]+)", r"lavfi\.freezedetect\.freeze_end:\s*([\d.]+)", dur)
    mudos = _pares(txt, r"silence_start:\s*([\d.]+)", r"silence_end:\s*([\d.]+)", dur)
    meio = lambda a, b: b > MARGEM_INI and a < dur - MARGEM_FIM  # noqa: E731
    pretos = [p for p in pretos if meio(*p)]
    congel = [p for p in congel if meio(*p)]
    mudos = [p for p in mudos if meio(*p)]
    # o ebur128 imprime "I: … LUFS" a cada quadro (começa em −70) e o valor certo só no "Summary:" do fim: a ÚLTIMA
    resumo_txt = txt[txt.rfind("Summary:"):] if "Summary:" in txt else txt
    ms = re.findall(r"I:\s*(-?[\d.]+)\s*LUFS", resumo_txt)
    loud = float(ms[-1]) if ms else None
    ms = re.findall(r"Peak:\s*(-?[\d.]+)\s*dBFS", resumo_txt)
    pico = float(ms[-1]) if ms else None
    problemas = []
    for a, b in pretos:
        problemas.append(f"quadro preto {a:.0f}–{b:.0f} s ({b - a:.1f} s)")
    for a, b in congel:
        problemas.append(f"imagem parada {a:.0f}–{b:.0f} s ({b - a:.1f} s)")
    for a, b in mudos:
        problemas.append(f"mudo {a:.0f}–{b:.0f} s ({b - a:.1f} s)")
    if loud is not None and loud < -24:
        problemas.append(f"volume baixo ({loud:.1f} LUFS)")
    if loud is not None and loud > -10:
        problemas.append(f"volume alto ({loud:.1f} LUFS)")
    if dur <= 0:
        problemas.append("ffprobe não leu a duração")
    grave = bool(pretos) or bool(mudos) or dur <= 0 or any(b - a >= 20 for a, b in congel)
    res = {"video": video.name, "duracao_s": round(dur, 1), "pretos": pretos, "congelados": congel, "mudos": mudos,
           "loudness_lufs": loud, "pico_dbfs": pico, "problemas": problemas, "ok": not grave}
    if gravar:
        try:
            (video.parent / "qa.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
        except OSError:
            pass
    return res


def resumo(res):
    return ("QA ok" if res["ok"] else "QA com problema") + f" ({res['duracao_s']:.0f} s, {res['loudness_lufs']} LUFS)" \
        + (": " + "; ".join(res["problemas"]) if res["problemas"] else "")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    r = analisar(sys.argv[1])
    print(resumo(r))
    print(json.dumps(r, ensure_ascii=False))
