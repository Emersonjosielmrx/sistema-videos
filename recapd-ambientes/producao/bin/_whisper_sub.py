#!/usr/bin/env python
"""Wrapper isolado pro faster-whisper. Roda em subprocesso próprio pra isolar
o MKL do ctranslate2 — evita "mkl_malloc: failed to allocate memory" quando o
processo pai já carregou outras libs que fragmentam a memória.

Uso: _whisper_sub.py <wav_path> <model_size>
Saída (stdout):
  linha 1: texto transcrito
  linha 2: código do idioma detectado
Retorna rc=0 em sucesso, rc!=0 em falha.
"""
import sys
import os

# Adiciona o venv do recapd-ambientes ao path (onde faster-whisper está instalado).
# O venv pode não estar ativo quando este script roda em subprocess via anime_fetch.py.
if "faster_whisper" not in sys.modules:
    venv_site = r"D:\recapd-ambientes\producao\venv\Lib\site-packages"
    if os.path.exists(venv_site) and venv_site not in sys.path:
        sys.path.insert(0, venv_site)

# MKL/OMP PRECISAM ser setadas ANTES do import do faster_whisper.
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["OMP_NUM_THREADS"] = "1"

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")

wav_path = sys.argv[1] if len(sys.argv) > 1 else None
model_size = sys.argv[2] if len(sys.argv) > 2 else "tiny"

if not wav_path:
    print("Uso: _whisper_sub.py <wav_path> <model_size>", file=sys.stderr)
    sys.exit(1)

from faster_whisper import WhisperModel

# 30/10: a pasta do modelo dependia de onde o processo foi chamado (cwd) — 7 Shorts deram rc=1 ao carregar o modelo.
# Agora procura a pasta que já TEM o modelo (producao\models, bin\models, cwd\models) e carrega sem ir à internet.
_aqui = os.path.dirname(os.path.abspath(__file__))
_raizes = [os.path.join(_aqui, "..", "models"), os.path.join(_aqui, "models"), os.path.join(os.getcwd(), "models")]
_raiz = next((r for r in _raizes if os.path.isdir(os.path.join(r, f"models--Systran--faster-whisper-{model_size}"))), None)
_kw = dict(device="cpu", compute_type="int8", cpu_threads=max(1, min(3, os.cpu_count() // 2)), num_workers=1)
try:
    model = WhisperModel(model_size, download_root=_raiz or _raizes[2], local_files_only=bool(_raiz), **_kw)
except Exception:  # noqa: BLE001 — cache local incompleto: baixa como antes
    model = WhisperModel(model_size, download_root=_raiz or _raizes[2], **_kw)
segments, info = model.transcribe(wav_path, vad_filter=False)
segs = list(segments)
txt = " ".join(seg.text.strip() for seg in segs).strip()
# 23/10: os tempos de cada trecho vão pra <wav>.tempos.json ([[início_s, texto], ...], o formato do legenda_tempos.json):
# sem eles o Short feito pelo Whisper (1 em 3 em 22/10) perdia o "roteiro com tempo" e a narração saía fora do quadro
try:
    import json
    with open(wav_path + ".tempos.json", "w", encoding="utf-8") as fh:
        json.dump([[round(s.start, 2), s.text.strip()] for s in segs if s.text.strip()], fh, ensure_ascii=False)
except OSError:
    pass
print(txt)
print(info.language)
