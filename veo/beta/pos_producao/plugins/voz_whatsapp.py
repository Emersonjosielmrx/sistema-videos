"""voz_whatsapp: injeta audio de voz PT-BR + WhatsApp no video.

Composicao:
  1) Gera audio com TTS (Gemini 3.1 primário, Edge Thalita fallback)
  2) Texto sempre termina com "WhatsApp {whatsapp}"
  3) Volume moderado + fade in/out
  4) Mixa no audio do video (mantem o audio original Veo em volume baixo)

Configuracao:
  - GEMINI_API_KEY para TTS premium (Gemini 3.1 Flash-TTS)
  - Caso nao tenha, cai pra edge-tts keyless 'pt-BR-ThalitaMultilingualNeural'

Texto base (customizavel em pos_producao/assets/voz_config.json):
  - "Atendimento 24h no WhatsApp com IA. Fale comigo agora: {whatsapp}"
"""

import json
import subprocess
from pathlib import Path

SUFFIX = "vozwpp"
_BASE = Path(__file__).resolve().parent.parent.parent
_ASSETS = _BASE / "pos_producao" / "assets"
_AUDIO_CACHE = _BASE / "pos_producao" / "audios_cache"
_AUDIO_CACHE.mkdir(parents=True, exist_ok=True)
_FFMPEG = r"D:\hipercool-materiais\bin\ffmpeg.exe"
_VOZ_CFG = _ASSETS / "voz_config.json"

_DEFAULT_CFG = {
    "whatsapp": "{whatsapp}",
    "frases": [
        "Atendimento 24 horas no WhatsApp com IA. Fale comigo agora: {whatsapp}",
        "Tenha seu proprio agente de IA no WhatsApp. Chama no Zap: {whatsapp}",
        "Vendendo no WhatsApp com inteligencia artificial. WhatsApp: {whatsapp}",
    ],
    "voz": "pt-BR-ThalitaMultilingualNeural",
    "volume_voz": 1.0,
    "volume_original": 0.25,
    "fade_in_s": 0.5,
    "fade_out_s": 1.0,
}


def _carregar_cfg():
    if _VOZ_CFG.exists():
        try:
            with open(_VOZ_CFG, "r", encoding="utf-8") as f:
                d = json.load(f)
            merged = dict(_DEFAULT_CFG)
            merged.update(d)
            return merged
        except Exception:
            pass
    return dict(_DEFAULT_CFG)


def _escolher_frase(stem: str, frases: list) -> str:
    import hashlib
    h = int(hashlib.md5(stem.encode("utf-8")).hexdigest(), 16)
    return frases[h % len(frases)]


# ---------- TTS Gemini 3.1 (primario) ----------

def _tts_gemini(texto: str, saida_wav: Path) -> bool:
    api_key = (None
               or __import__("os").environ.get("GEMINI_API_KEY")
               or __import__("os").environ.get("GOOGLE_API_KEY")
               or __import__("os").environ.get("LLM_API_KEY"))
    if not api_key:
        return False
    try:
        try:
            from google import genai
            client = genai.Client(api_key=api_key)
            r = client.models.generate_content(
                model="gemini-2.5-flash-preview-tts",
                contents=texto,
                config={
                    "response_modalities": ["AUDIO"],
                    "speech_config": {
                        "voice_config": {
                            "prebuilt_voice_config": {"voice_name": "Aoede"}
                        }
                    },
                },
            )
            data = r.candidates[0].content.parts[0].inline_data.data
            saida_wav.write_bytes(data)
        except Exception:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            # SDK antigo nao suporta TTS bem; fallback p/ Edge
            return False
        return saida_wav.exists() and saida_wav.stat().st_size > 1000
    except Exception:
        return False


# ---------- TTS Edge keyless (fallback) ----------

def _tts_edge(texto: str, saida_wav: Path, voz: str) -> bool:
    try:
        import asyncio
        import edge_tts
    except ImportError:
        return False
    async def _gen():
        comm = edge_tts.Communicate(texto, voice=voz)
        await comm.save(str(saida_wav))
    try:
        asyncio.run(_gen())
    except Exception:
        return False
    return saida_wav.exists() and saida_wav.stat().st_size > 1000


def _numero():
    """O numero fica fora do git (16/10: estava em 5 arquivos versionados): secrets/contato.json. Sem ele, None."""
    try:
        return json.loads((_BASE / "secrets" / "contato.json").read_text(encoding="utf-8")).get("whatsapp")
    except Exception:
        return None


def _gerar_audio(stem: str, cfg: dict, saida_wav: Path) -> bool:
    numero = _numero()
    if not numero:
        return False  # sem contato nao fala "{whatsapp}": o plugin so nao roda
    texto = _escolher_frase(stem, cfg["frases"]).replace("{whatsapp}", numero)
    if not _tts_gemini(texto, saida_wav):
        if not _tts_edge(texto, saida_wav, cfg["voz"]):
            return False
    return True


# ---------- mixagem no video ----------

def _mixar_audio(video_mp4: str, voz_wav: str, output_mp4: str, cfg: dict) -> bool:
    """Mixagem: voz volume 1.0 + audio original 0.25 (ducking leve)."""
    vf = (
        f"[0:a]volume={cfg['volume_original']},afade=t=in:st=0:d={cfg['fade_in_s']}[orig];"
        f"[1:a]volume={cfg['volume_voz']},afade=t=in:st=0:d={cfg['fade_in_s']},"
        f"afade=t=out:st=999:d={cfg['fade_out_s']}[voz];"
        f"[orig][voz]amix=inputs=2:duration=shortest[a]"
    )
    cmd = [
        _FFMPEG, "-y", "-hide_banner", "-loglevel", "error",
        "-i", video_mp4,
        "-i", voz_wav,
        "-filter_complex", vf,
        "-map", "0:v", "-map", "[a]",
        "-c:v", "copy",
        "-c:a", "aac", "-b:a", "128k",
        "-shortest",
        "-movflags", "+faststart",
        output_mp4,
    ]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        return r.returncode == 0 and Path(output_mp4).exists()
    except Exception:
        return False


def processar(input_mp4: str, output_mp4: str, meta: dict) -> bool:
    if not Path(_FFMPEG).exists() or not Path(input_mp4).exists():
        return False
    cfg = _carregar_cfg()
    stem = meta.get("stem", "")
    voz_wav = _AUDIO_CACHE / f"{stem}__vozwpp.wav"
    if not _gerar_audio(stem, cfg, voz_wav):
        return False
    return _mixar_audio(input_mp4, str(voz_wav), output_mp4, cfg)
