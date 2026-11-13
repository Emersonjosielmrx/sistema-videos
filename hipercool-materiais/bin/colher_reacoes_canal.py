"""colher_reacoes_canal.py — colhe REAÇÕES REAIS do narrador nos vídeos do canal dele (22/10, plano anti-"é IA").

O dataset de treino (8 min) quase não tem reação (medido em 22/10: 0 aproveitáveis nas 13 vozes). Aqui a colheita
vai aos VÍDEOS do canal do parceiro: legenda automática (pequena, sai pelo proxy) acha interjeições com o tempo
("caraca", "vixe", "eita", risada transcrita...), baixa SÓ 4 s de ÁUDIO em volta (--download-sections, ~100 KB) e
separa a voz da trilha (UVR). O resultado fica em D:\\tmp\\reacoes\\canal_<voz>\\ pra ouvir/aprovar — só depois de
aprovado entra no `humano\\reacoes.json` da voz e no humanizar.

    python colher_reacoes_canal.py --voz mike --canal https://www.youtube.com/@mikemanhwa [--videos 8] [--max 6]

Regras: vozes autorizadas pelo dono; nada é postado; downloads mínimos e 1 por vez (ytdlp_vez)."""
import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

RAIZ = Path(r"D:\hipercool-materiais")
sys.path.insert(0, r"D:\recapd-ambientes\producao\bin")  # ytdlp_vez (cópia comum) + parser de vtt
import ytdlp_vez  # noqa: E402

FFMPEG = str(RAIZ / "bin" / "ffmpeg.exe")
SEPARADOR = Path(r"D:\tools\separador\Scripts\audio-separator.exe")
MODELOS_SEP = Path(r"D:\tools\separador\modelos")
TMP = Path(r"D:\tmp\reacoes")
SEM_JANELA = getattr(subprocess, "CREATE_NO_WINDOW", 0)
INTERJ = re.compile(r"\b(caraca|vixe|eita|rapaziada|nossa senhora|meu deus|olha isso|n[aã]o acredito|"
                    r"que isso|aham|haha+|kkk+|uau|boa essa)\b", re.I)
PALAVRAO = re.compile(r"porra|caralh|merda|puta|foda|cacete|bucet|pqp|viad|arromb", re.I)


def log(m):
    print(m, flush=True)


def _ytdlp(args, rotulo, timeout=240):
    with ytdlp_vez.vez(rotulo):
        return subprocess.run(["yt-dlp", *args], capture_output=True, text=True, timeout=timeout,
                              encoding="utf-8", errors="replace", creationflags=SEM_JANELA)


def _videos(canal, n):
    r = _ytdlp([canal.rstrip("/") + "/videos", "--flat-playlist", "--no-warnings",
                "--print", "%(id)s\x1f%(duration)s\x1f%(title).60s", "--playlist-end", str(n * 2)],
               "reacao: lista do canal")
    out = []
    for l in (r.stdout or "").splitlines():
        p = l.split("\x1f")
        if len(p) == 3 and p[1].replace(".", "").isdigit() and float(p[1]) > 120:
            out.append((p[0], p[2]))
    return out[:n]


def _cues(vid, pasta):
    r = _ytdlp([f"https://www.youtube.com/watch?v={vid}", "--skip-download", "--write-auto-subs",
                "--sub-langs", "pt", "--sub-format", "vtt", "--no-warnings", "-o", str(pasta / vid)],
               "reacao: legenda")
    vtt = next(iter(pasta.glob(f"{vid}*.vtt")), None)
    if not vtt:
        return []
    import importlib.util
    spec = importlib.util.spec_from_file_location("af", r"D:\recapd-ambientes\producao\bin\anime_fetch.py")
    af = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(af)
    return af._parse_vtt_tempos(vtt) or []


def colher(voz, canal, n_videos=8, max_clips=6):
    base = TMP / f"canal_{voz}"
    shutil.rmtree(base, ignore_errors=True)
    base.mkdir(parents=True)
    achados = []
    for vid, titulo in _videos(canal, n_videos):
        if len(achados) >= max_clips:
            break
        if ytdlp_vez.pausado():
            log("[colher] IP em pausa — paro por aqui")
            break
        cues = _cues(vid, base)
        log(f"[colher] {vid} ({titulo[:40]}): {len(cues)} cues")
        for i, (t, txt) in enumerate(cues):
            if len(achados) >= max_clips:
                break
            palavras = str(txt).split()
            if len(palavras) > 4 or not INTERJ.search(str(txt)) or PALAVRAO.search(str(txt)):
                continue
            vizinho = " ".join(str(c[1]) for c in cues[max(0, i - 1):i + 2])
            if PALAVRAO.search(vizinho):
                continue
            a = max(0.0, float(t) - 0.8)
            clip = base / f"cand_{len(achados):02d}_{vid}_{int(t)}s.m4a"
            r = _ytdlp([f"https://www.youtube.com/watch?v={vid}", "-f", "ba[ext=m4a]/ba",
                        "--download-sections", f"*{a:.1f}-{a + 4.5:.1f}", "--no-warnings",
                        "-o", str(clip)], "reacao: busca de secao do audio", timeout=300)
            baixado = next(iter(base.glob(clip.stem + "*")), None)
            if r.returncode != 0 or not baixado:
                if ytdlp_vez.bloqueio((r.stderr or "")):
                    log("[colher] bloqueio no meio — paro")
                    return achados
                continue
            achados.append({"arq": str(baixado), "video": vid, "t": round(float(t), 1), "texto": str(txt)[:60]})
            log(f"[colher]   + {clip.name}: \"{txt}\"")
    # separa a VOZ da trilha (UVR), vira wav mono 44.1k
    finais = []
    for c in achados:
        tmpd = base / "_sep"
        shutil.rmtree(tmpd, ignore_errors=True)
        tmpd.mkdir()
        try:
            subprocess.run([str(SEPARADOR), c["arq"], "-m", "UVR-MDX-NET-Voc_FT.onnx", "--model_file_dir",
                            str(MODELOS_SEP), "--output_dir", str(tmpd), "--output_format", "WAV",
                            "--single_stem", "Vocals"], capture_output=True, timeout=600,
                           creationflags=SEM_JANELA | 0x00004000)
            sep = next(iter(tmpd.glob("*.wav")), None)
            if not sep:
                raise RuntimeError("separador não devolveu wav")
            final = Path(c["arq"]).with_suffix(".voz.wav")
            subprocess.run([FFMPEG, "-y", "-v", "error", "-i", str(sep), "-ac", "1", "-ar", "44100",
                            str(final)], check=True, timeout=60, creationflags=SEM_JANELA)
            finais.append({**c, "voz_wav": str(final)})
        except Exception as e:  # noqa: BLE001
            log(f"[colher] separação falhou em {Path(c['arq']).name}: {str(e)[:80]}")
        finally:
            shutil.rmtree(tmpd, ignore_errors=True)
    (base / "manifest.json").write_text(json.dumps(finais, ensure_ascii=False, indent=1), encoding="utf-8")
    log(f"[colher] {voz}: {len(finais)} candidata(s) com voz separada em {base}")
    return finais


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--voz", required=True)
    p.add_argument("--canal", required=True)
    p.add_argument("--videos", type=int, default=8)
    p.add_argument("--max", type=int, default=6)
    a = p.parse_args()
    colher(a.voz, a.canal, a.videos, a.max)


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
