"""_tts_helper: helper de TTS PT-BR para a propaganda.

Antes era um plugin (tts_gemini_or_edge) que injetava fala no video principal
substituindo o audio do Veo. Agora virou helper usado pelo plugin
propaganda_inteligente, que gera fala da CTA (copy + whatsapp) e mixa no slide.

Hierarquia (custo/qualidade):
  1. Gemini 2.5 flash TTS (Google AI) - melhor qualidade
  2. Edge-TTS voz 'Thalita' PT-BR - fallback keyless, CPU-only

Para nao quebrar o pipeline se Gemini falhar:
  - tenta Edge automaticamente
  - se ambos falharem, propaganda fica sem TTS (silencio - ainda funciona)
"""

import os
import subprocess
from pathlib import Path

_BASE = Path(__file__).resolve().parent.parent.parent  # D:\veo\beta
_AUDIOS_CACHE = _BASE / "pos_producao" / "audios_cache"
_AUDIOS_CACHE.mkdir(parents=True, exist_ok=True)
_FFMPEG = r"D:\hipercool-materiais\bin\ffmpeg.exe"


def _gemini_tts(texto: str, saida_wav: Path) -> bool:
    """Tenta gerar fala com Gemini TTS. Retorna True se ok."""
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY") or os.environ.get("LLM_API_KEY")
    if not api_key:
        return False
    try:
        from google import genai  # tipo Gemini 3.x SDK
    except ImportError:
        try:
            import google.generativeai as genai  # tipo antigo
        except ImportError:
            return False
    try:
        client = genai.Client(api_key=api_key)
        config = {
            "response_modalities": ["AUDIO"],
            "speech_config": {
                "voice_config": {
                    "prebuilt_voice_config": {"voice_name": "Aoede"}
                }
            }
        }
        resp = client.models.generate_content(
            model="gemini-2.5-flash-preview-tts",
            contents=texto,
            config=config,
        )
        audio_bytes = resp.candidates[0].content.parts[0].inline_data.data
        saida_wav.write_bytes(audio_bytes)
        return saida_wav.exists() and saida_wav.stat().st_size > 1000
    except Exception:
        return False


def _edge_tts(texto: str, saida_wav: Path) -> bool:
    """Fallback: edge-tts (keyless) com voz Thalita PT-BR."""
    try:
        import asyncio
        import edge_tts
    except ImportError:
        return False
    async def _gen():
        comm = edge_tts.Communicate(texto, voice="pt-BR-ThalitaMultilingualNeural")
        await comm.save(str(saida_wav))
    try:
        asyncio.run(_gen())
        return saida_wav.exists() and saida_wav.stat().st_size > 1000
    except Exception:
        return False


def gerar_tts_cta(texto: str, cache_key: str) -> Path | None:
    """Gera fala PT-BR do texto, com cache. Retorna Path do wav ou None.

    cache_key: identificador unico do texto (slug do produto, hash do copy).
    """
    fala_wav = _AUDIOS_CACHE / f"tts_cta_{cache_key}.wav"
    if fala_wav.exists() and fala_wav.stat().st_size > 1000:
        return fala_wav
    if not _gemini_tts(texto, fala_wav):
        if not _edge_tts(texto, fala_wav):
            return None
    return fala_wav if fala_wav.exists() and fala_wav.stat().st_size > 1000 else None