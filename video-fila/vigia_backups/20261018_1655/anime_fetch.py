"""anime_fetch.py — baixa o vídeo-fonte e sua transcrição.

Módulo isolado. Duas responsabilidades, ambas via yt-dlp:
  1. baixar o mp4 do vídeo.
  2. obter a transcrição — estratégia dupla:
       (a) legenda do YouTube (auto-caption, rápida; YT ainda traduz pra pt);
       (b) fallback Whisper (transcreve o áudio) — só se (a) falhar.

Retorna caminhos locais. NÃO reescreve o roteiro (isso é o anime_script).
O texto da legenda vem CRU (pode estar em qualquer língua) — traduzir/reescrever
é trabalho do anime_script via IA.
"""
import logging
import os
import sys
import re
import subprocess
from pathlib import Path

# O venv do recapd-e-animes é vazio (só pip+psutil).
# faster-whisper foi instalado no Python do SISTEMA (C:/Python313).
# Adiciona o site-packages do sistema no path pra poder importar.
if "faster_whisper" not in sys.modules:
    import site
    sys.path.append(r"C:\Users\Emerson-IA\AppData\Local\Programs\Python\Python313\Lib\site-packages")
    sys.path.extend(site.getsitepackages())

# MKL/OMP (backend do ctranslate2/faster-whisper) lê estas vars UMA VEZ, no load da
# lib. Precisam existir ANTES do 'from faster_whisper import ...' (que é lazy, dentro
# da função) — por isso ficam aqui no topo do módulo. Sem isso, o MKL abre arenas
# grandes por thread e estoura 'mkl_malloc: failed to allocate memory' mesmo com RAM
# sobrando (fragmentação de arena, não falta física).
os.environ.setdefault("MKL_NUM_THREADS", "1")
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("MKL_DYNAMIC", "FALSE")
os.environ.setdefault("MKL_THREADING_LAYER", "SEQUENTIAL")
os.environ.setdefault("HF_HOME", r"D:\hipercool-materiais\models\huggingface")  # pasta COMUM de modelos (dono 17/10)


def download_video(url, out_dir, max_height=720):
    """Baixa o vídeo como mp4. Retorna Path do arquivo ou None.

    Estratégia: tenta filtro por largura (garante vertical 720x1280 se existir).
    Se o arquivo baixado não for vertical, retry com filtro por altura.
    """
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_tmpl = str(out_dir / "source.%(ext)s")

    def _is_vertical(path):
        try:
            out = subprocess.run(
                ["ffprobe", "-v", "error", "-select_streams", "v:0",
                 "-show_entries", "stream=width,height",
                 "-of", "csv=s=x:p=0", str(path)],
                capture_output=True, text=True, timeout=30,
            )
            w, h = out.stdout.strip().split("x")
            return (int(w) / int(h)) < 0.9
        except Exception:
            return False

    def _do_download(fmt_spec):
        cmd = ["yt-dlp", url, "-f", fmt_spec,
               "--merge-output-format", "mp4", "-o", out_tmpl,
               "--no-warnings", "--no-playlist",
               "--cookies-from-browser", "chrome"]
        env = os.environ.copy()
        subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=1800, env=env)
        for f in out_dir.glob("source.*"):
            if f.suffix.lower() in (".mp4", ".mkv", ".webm"):
                return f
        return None

    # 1. Tenta por largura — prioriza bestvideo+bestaudio (YT não tem mais mp4
    #    combinado em 720p; --merge-output-format mp4 resolve o merge).
    fmt_w = (
        f"bestvideo[width<={max_height}]+bestaudio/"
        f"best[width<={max_height}][ext=mp4]/"
        f"best[width<={max_height}]/worst[width>0]"
    )
    try:
        fpath = _do_download(fmt_w)
        if fpath and _is_vertical(str(fpath)):
            return fpath
        if fpath:
            fpath.unlink(missing_ok=True)
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
        logging.warning(f"[fetch] download (width) falhou: {e}")

    # 2. Retry com filtro por altura (mais compatível)
    fmt_h = (
        f"bestvideo[height<={max_height}]+bestaudio/"
        f"best[height<={max_height}][ext=mp4]/"
        f"best[height<={max_height}]/worst[height>0]"
    )
    try:
        return _do_download(fmt_h)
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
        logging.error(f"[fetch] download falhou: {e}")
        return None


def _parse_vtt(vtt_path):
    """Extrai só o texto de um .vtt (descarta timestamps, tags, duplicatas)."""
    lines = []
    seen_last = None
    for raw in Path(vtt_path).read_text(encoding="utf-8", errors="ignore").splitlines():
        s = raw.strip()
        if not s or s == "WEBVTT" or "-->" in s or s.isdigit():
            continue
        if s.startswith(("Kind:", "Language:", "NOTE")):
            continue
        s = re.sub(r"<[^>]+>", "", s)          # tags <c>, <00:00:00>
        s = re.sub(r"\[[^\]]*\]", "", s).strip()  # [Music], [Applause]
        if s and s != seen_last:               # auto-caption repete muito
            lines.append(s)
            seen_last = s
    return " ".join(lines).strip()


def fetch_captions(url, out_dir, langs=("pt", "en", "es", "ko", "ja")):
    """Baixa auto-caption do YouTube (já traduzida pra langs, em ordem de preferência).

    Retorna (texto, lang) do primeiro idioma disponível, ou (None, None).
    """
    out_dir = Path(out_dir)
    for lang in langs:
        stem = str(out_dir / f"cap_{lang}")
        cmd = [
            "yt-dlp", url, "--skip-download",
            "--write-auto-subs", "--sub-langs", lang,
            "--sub-format", "vtt", "-o", stem,
            "--no-warnings", "--no-playlist",
            "--cookies-from-browser", "chrome",
        ]
        try:
            subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=180)
        except Exception:
            continue
        for vtt in out_dir.glob(f"cap_{lang}*.vtt"):
            txt = _parse_vtt(vtt)
            if len(txt) > 100:  # legenda utilizável (mín 100 chars; < 100 vai pro Whisper)
                logging.info(f"[fetch] legenda YT obtida (lang={lang}, {len(txt)} chars)")
                return txt, lang
    logging.warning("[fetch] sem legenda YT utilizável")
    return None, None


def transcribe_whisper(video_path, model_size="tiny", max_seconds=1500):
    """Fallback: transcreve o áudio com faster-whisper via SUBPROCESS ISOLADO.

    Rodar em subprocesso separado evita o erro "mkl_malloc: failed to allocate memory"
    que ocorre quando o whisper carrega num processo já com memória fragmentada por
    outras libs (anime_script, etc.). Cada subprocesso é uma página em branco pro MKL.

    Retorna (texto, lang) ou (None, None).
    """
    # Qual Python do venv usar no subprocess.
    PY = sys.executable  # o mesmo python que roda anime_auto.py
    if not Path(PY).exists():
        for _py in (
            r"D:\recapd-ambientes\producao\venv\Scripts\python.exe",
            r"C:\Users\Haylla\AppData\Local\Programs\Python\Python313\python.exe",
            r"C:\Users\Emerson-IA\AppData\Local\Programs\Python\Python313\python.exe",
        ):
            if Path(_py).exists():
                PY = _py
                break

    wav = Path(video_path).with_suffix(".whisper.wav")
    try:
        subprocess.run(
            ["ffmpeg", "-y", "-t", str(max_seconds), "-i", str(video_path),
             "-vn", "-ac", "1", "-ar", "16000", "-f", "wav", str(wav)],
            check=True, capture_output=True, timeout=600,
        )
    except Exception as e:
        logging.error(f"[fetch] extração de áudio p/ Whisper falhou: {e}")
        return None, None

    whisper_script = Path(__file__).parent / "_whisper_sub.py"
    # Tenta apenas "tiny" para minimizar risco de MemoryError
    for msize in ("tiny",):
        try:
            env = dict(os.environ,
                MKL_NUM_THREADS="1", OMP_NUM_THREADS="1",
                PYTHONIOENCODING="utf-8", PYTHONUTF8="1",
            )
            result = subprocess.run(
                [PY, str(whisper_script), str(wav), msize],
                capture_output=True, text=True, timeout=300,
                encoding="utf-8", errors="replace",
                env=env,
            )
            if result.returncode == 0:
                lines = result.stdout.strip().splitlines()
                if len(lines) >= 2:
                    txt = lines[0].strip()
                    lang = lines[1].strip()
                    if len(txt) > 50:
                        logging.info(f"[fetch] Whisper transcreveu (model={msize}, lang={lang}, {len(txt)} chars)")
                        _cleanup_wav(wav, video_path)
                        return txt, lang
                    logging.warning(f"[fetch] Whisper (model={msize}) texto curto demais ({len(txt)} chars)")
                else:
                    logging.warning(f"[fetch] Whisper (model={msize}) output inesperado: {result.stdout[:100]!r}")
            else:
                logging.error(f"[fetch] Whisper (model={msize}) rc={result.returncode}: {result.stderr[:200]}")
        except Exception as e:
            logging.error(f"[fetch] Whisper (model={msize}) exception: {e}")

    _cleanup_wav(wav, video_path)
    return None, None


def _cleanup_wav(wav, video_path):
    try:
        if Path(wav) != Path(video_path):
            Path(wav).unlink(missing_ok=True)
    except Exception:
        pass


def get_transcript(url, video_path, out_dir):
    """Transcrição com estratégia dupla: legenda YT primeiro, Whisper como fallback.

    Retorna (texto, lang) — texto CRU (língua original/traduzida), pra reescrita depois.
    """
    txt, lang = fetch_captions(url, out_dir)
    if txt:
        return txt, lang
    logging.info("[fetch] tentando fallback Whisper...")
    return transcribe_whisper(video_path)


if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    url = sys.argv[1]
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("_fetch_test")
    txt, lang = fetch_captions(url, out)
    print(f"lang={lang} chars={len(txt or '')}")
    if txt:
        print(txt[:500])
