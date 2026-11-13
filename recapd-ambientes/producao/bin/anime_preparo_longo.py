"""anime_preparo_longo.py — transcrição do vídeo INTEIRO (Whisper) + roteiro com tempo do recap LONGO, feitos no
TRABALHADOR (Kaggle/VPS/Colab, núcleos livres), não no PC1.

Dona 25/10/2026 ("os longos estão muito atrás dos Cortes"): o Whisper do PC1 parava nos 25 min (o 76SY, de 2h18, virou
roteiro só do começo da história) e, com o PC1 a 100% de CPU, 6 min de áudio passaram de 10 min de Whisper — o longo
inteiro não cabe lá. O alimentador (colab/cliente.py) manda só o original quando o YouTube não dá legenda; o
anime-pipeline.py chama este preparo quando o roteiro ainda não existe.

    python anime_preparo_longo.py <pasta com source.mp4> [título]

Grava na pasta: legenda_tempos.json ([[início_s, texto], ...]), roteiro.txt e roteiro_tempos.json (o segundo do original
que cada frase narra). Sai com 0 se o roteiro ficou pronto.
"""
import json
import logging
import os
import subprocess
import sys
import time
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
SEG_POR_FRASE = 6.6  # igual ao alimentador/anime_worker_daemon: ~6,6 s de narração por frase, 99% da duração


def _garantir_whisper():
    try:
        import faster_whisper  # noqa: F401
    except ImportError:
        logging.info("[preparo] instalando faster-whisper (1ª vez nesta máquina)")
        subprocess.run([sys.executable, "-m", "pip", "install", "-q", "faster-whisper"], check=True, timeout=1200)


def transcrever(video, pasta, dur=0):
    """[[início_s, texto], ...] do áudio inteiro. 'base' (mais fiel) até 40 min de original; acima disso 'tiny' (25/10,
    VPS com 4 núcleos: base = 0,65 s por segundo de áudio — 2h18 levaria 1h30 só de Whisper)."""
    _garantir_whisper()
    from faster_whisper import WhisperModel
    wav = Path(pasta) / "_whisper.wav"
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(video), "-vn", "-ac", "1", "-ar", "16000", str(wav)],
                   check=True, timeout=3600)
    nucleos = os.cpu_count() or 2
    modelo = os.environ.get("LONGO_WHISPER_MODELO") or ("base" if nucleos >= 4 and dur <= 2400 else "tiny")
    t0 = time.time()
    raiz_modelos = str(Path(pasta).resolve().parent / "_modelos_whisper")
    # áudio lido aqui (WAV 16 kHz mono): o decode do faster-whisper usa o PyAV, e a dupla instalada na VPS em 25/10 não
    # combinava ("open() got an unexpected keyword argument 'metadata_errors'")
    import wave
    import numpy as np
    with wave.open(str(wav), "rb") as w:
        audio = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768.0
    cues, info = None, None
    # 02/11 (dona: "aproveitar as GPUs"): no Kaggle o Whisper rodava na CPU (por isso o 'tiny' nos longos > 40 min).
    # Com CUDA: modelo 'small' (mais fiel) em float16 na T4. Qualquer erro (cuDNN/cuBLAS faltando) = CPU como antes.
    try:
        import torch
        tem_gpu = torch.cuda.is_available()
    except Exception:  # noqa: BLE001
        tem_gpu = False
    if tem_gpu and os.environ.get("LONGO_WHISPER_GPU", "1") != "0":
        try:
            _carregar_cuda_libs()
            mod_gpu = os.environ.get("LONGO_WHISPER_MODELO") or "small"
            m = WhisperModel(mod_gpu, device="cuda", compute_type="float16", download_root=raiz_modelos)
            segs, info = m.transcribe(audio, vad_filter=False)
            cues = [[round(s.start, 2), s.text.strip()] for s in segs if s.text.strip()]
            modelo, nucleos = f"{mod_gpu} (GPU)", "T4"
        except Exception as e:  # noqa: BLE001
            logging.warning(f"[preparo] Whisper na GPU falhou ({type(e).__name__}: {str(e)[:120]}) — vai na CPU")
            cues = None
    if cues is None:
        m = WhisperModel(modelo, device="cpu", compute_type="int8", cpu_threads=nucleos, download_root=raiz_modelos)
        segs, info = m.transcribe(audio, vad_filter=False)
        cues = [[round(s.start, 2), s.text.strip()] for s in segs if s.text.strip()]
    wav.unlink(missing_ok=True)
    logging.info(f"[preparo] Whisper {modelo} ({nucleos} núcleos): {len(cues)} trechos, língua {info.language}, "
                 f"até {cues[-1][0] if cues else 0:.0f}s, em {time.time() - t0:.0f}s")
    return cues


def _carregar_cuda_libs():
    """03/11 (dona aprovou o item 8): no Kaggle o faster-whisper dava "Library libcublas.so.12 is not found" e caía na
    CPU (8 min no waaQ). O CTranslate2 abre a lib pelo NOME; carregando antes com RTLD_GLOBAL ele acha. Procura nas
    pastas do CUDA e nas libs nvidia do pip (as do torch); não achou = instala nvidia-cublas-cu12 + cudnn 9 (uma vez)."""
    import ctypes
    import glob
    import site
    import sys as _sys
    nomes = ("libcublasLt.so.12", "libcublas.so.12", "libcudnn.so.9", "libcudnn_ops.so.9", "libcudnn_cnn.so.9")

    def _achar():
        pastas = ["/usr/local/cuda/lib64", "/usr/local/cuda-12*/lib64", "/usr/lib/x86_64-linux-gnu",
                  "/opt/conda/lib"]
        for sp in [*site.getsitepackages(), site.getusersitepackages()]:
            pastas += [f"{sp}/nvidia/*/lib", f"{sp}/torch/lib"]
        achados = {}
        for pat in pastas:
            for d in glob.glob(pat):
                for n in nomes:
                    if n not in achados and Path(d, n).exists():
                        achados[n] = str(Path(d, n))
        return achados

    achados = _achar()
    if "libcublas.so.12" not in achados:
        subprocess.run([_sys.executable, "-m", "pip", "install", "-q", "nvidia-cublas-cu12", "nvidia-cudnn-cu12==9.*"],
                       timeout=900, capture_output=True)
        achados = _achar()
    for n in nomes:  # ordem importa: cublasLt antes do cublas, cudnn antes dos ops
        if n in achados:
            try:
                ctypes.CDLL(achados[n], mode=ctypes.RTLD_GLOBAL)
            except OSError:
                pass
    logging.info(f"[preparo] libs CUDA pro Whisper: {', '.join(sorted(achados)) or 'nenhuma achada'}")


def preparar(pasta, titulo=""):
    import anime_probe
    import anime_script
    pasta = Path(pasta)
    video = pasta / "source.mp4"
    roteiro = pasta / "roteiro.txt"
    dur = anime_probe.video_duration(str(video))
    if dur <= 0:
        logging.error(f"[preparo] original ilegível: {video}")
        return False
    cues_arq = pasta / "legenda_tempos.json"
    cues = json.loads(cues_arq.read_text(encoding="utf-8")) if cues_arq.exists() else []
    if not cues:
        cues = transcrever(video, pasta, dur)
        if not cues:
            logging.error("[preparo] Whisper não achou fala")
            return False
        cues_arq.write_text(json.dumps(cues, ensure_ascii=False), encoding="utf-8")
    if cues[-1][0] < dur * 0.6:  # transcrição bem menor que o vídeo: o roteiro ia contar só um pedaço da história
        logging.warning(f"[preparo] a transcrição vai só até {cues[-1][0]:.0f}s de {dur:.0f}s")
    seg_frase = SEG_POR_FRASE
    try:  # 02/11 dona: o 1º RECAP DE ANIME (fQTiy7) saiu com 71 min de 118 (60%) — manhwa fica 92-113% do original
        if json.loads((Path(pasta) / "pedido.json").read_text(encoding="utf-8")).get("tipo") == "anime_recap":
            os.environ["ANIME_VARIANTE"] = "anime_recap"  # anime_script pede "no mínimo" e refaz bloco curto
    except (OSError, ValueError):
        pass
    if os.environ.get("ANIME_VARIANTE") == "anime_recap":
        seg_frase = 5.0  # frase de anime dura ~4,9 s (cena rápida) contra ~5,7 s no manhwa: alvo maior pro mesmo tempo
    alvo, _apertado = anime_script.alvo_com_teto(max(40, round(dur * 0.99 / seg_frase)))  # teto: cabe na sessão
    frases, tempos = anime_script.rewrite_longo_com_tempo(cues, alvo, dur)
    if frases:
        roteiro.write_text("\n".join(frases) + "\n", encoding="utf-8")
        (pasta / "roteiro_tempos.json").write_text(json.dumps(tempos), encoding="utf-8")
    else:
        anime_script.rewrite_to_file(" ".join(t for _s, t in cues), roteiro, target_lines=alvo)
    ok = roteiro.exists() and roteiro.stat().st_size > 100
    logging.info(f"[preparo] roteiro {'pronto' if ok else 'FALHOU'}: {len(frases) if frases else '?'} frases "
                 f"{'com tempo' if frases else 'sem tempo'} (alvo {alvo}, original {dur / 60:.0f} min) — {titulo[:60]}")
    return ok


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(0 if preparar(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "") else 1)
