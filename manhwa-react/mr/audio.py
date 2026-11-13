"""Cadeia de audio: extracao, reducao de ruido (RNNoise via arnndn), tratamento de voz e loudness em 2 passos."""
import json
import re
from pathlib import Path
from .common import ffmpeg, ffpath, run, log


def extract_wav(cfg, video, out, sr=48000, channels=2):
    ffmpeg(cfg, ["-i", str(video), "-vn", "-ac", str(channels), "-ar", str(sr), "-c:a", "pcm_s16le", str(out)])
    return out


def denoise_chain(cfg):
    A = cfg["audio"]
    model = Path(cfg["paths"]["assets"]) / "models" / f"{A['denoise_model']}.rnnn"
    parts = []
    if A.get("highpass_hz"):
        parts.append(f"highpass=f={A['highpass_hz']}")
    if model.exists():
        parts.append(f"arnndn=m={ffpath(model)}:mix={A.get('denoise_mix', 1.0)}")
    else:
        log(f"AVISO: modelo RNNoise nao encontrado em {model}; usando afftdn")
        parts.append("afftdn=nf=-40:nr=12:tn=1")
    return ",".join(parts)


def voice_chain(cfg):
    A = cfg["audio"]
    parts = []
    if A.get("deesser"):
        parts.append("deesser=i=0.3:m=0.5:f=0.5")
    if A.get("compressor"):
        parts.append(A["compressor"])
    if A.get("voice_eq"):
        parts.append(A["voice_eq"])
    return ",".join(parts)


def clean_audio(cfg, wav_in, wav_out):
    """Ruido -> de-esser -> compressor. Mantem estereo."""
    chain = denoise_chain(cfg)
    vc = voice_chain(cfg)
    if vc:
        chain += "," + vc
    ffmpeg(cfg, ["-i", str(wav_in), "-af", chain, "-ar", "48000", "-c:a", "pcm_s16le", str(wav_out)])
    return wav_out


def loudnorm_two_pass(cfg, wav_in, wav_out):
    A = cfg["audio"]
    base = f"loudnorm=I={A['target_lufs']}:TP={A['true_peak']}:LRA={A['lra']}"
    res = run([cfg["paths"]["ffmpeg"], "-hide_banner", "-i", str(wav_in), "-af", base + ":print_format=json", "-f", "null", "-"], check=False)
    m = re.search(r"\{[^{}]*\"input_i\"[^{}]*\}", res.stderr, re.S)
    if not m:
        log("AVISO: loudnorm passo 1 sem medicao; aplicando passo unico")
        ffmpeg(cfg, ["-i", str(wav_in), "-af", base, "-ar", "48000", "-c:a", "pcm_s16le", str(wav_out)])
        return wav_out
    j = json.loads(m.group(0))
    second = (base + f":measured_I={j['input_i']}:measured_TP={j['input_tp']}:measured_LRA={j['input_lra']}"
              f":measured_thresh={j['input_thresh']}:offset={j['target_offset']}:linear=true:print_format=summary")
    ffmpeg(cfg, ["-i", str(wav_in), "-af", second, "-ar", "48000", "-c:a", "pcm_s16le", str(wav_out)])
    log(f"loudness: {j['input_i']} LUFS -> alvo {A['target_lufs']} LUFS")
    return wav_out


def detect_silences(cfg, wav, noise_db=-40, min_dur=0.35):
    res = run([cfg["paths"]["ffmpeg"], "-hide_banner", "-i", str(wav), "-af", f"silencedetect=noise={noise_db}dB:d={min_dur}", "-f", "null", "-"], check=False)
    sil = []
    start = None
    for line in res.stderr.splitlines():
        m = re.search(r"silence_start:\s*(-?[\d.]+)", line)
        if m:
            start = float(m.group(1))
            continue
        m = re.search(r"silence_end:\s*([\d.]+)", line)
        if m and start is not None:
            sil.append([max(0.0, start), float(m.group(1))])
            start = None
    if start is not None:
        sil.append([start, None])
    log(f"silencios ({noise_db} dB, >= {min_dur}s): {len(sil)}")
    return sil
