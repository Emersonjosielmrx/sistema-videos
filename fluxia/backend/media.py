import base64
import hashlib
import hmac
import os
import re
import zlib
from pathlib import Path

import httpx
from cryptography.hazmat.primitives import hashes, padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

AI_URL = os.environ.get("FLUXIA_AI_URL", "http://157.173.207.22:20128").rstrip("/")
TRANSCRIBE_MODELS = [m.strip() for m in os.environ.get(
    "FLUXIA_TRANSCRIBE_MODEL", "gemini/gemini-3.5-flash-lite,gemini/gemini-2.5-flash-lite,agy/gemini-3.8-flash-high").split(",") if m.strip()]
TRANSCRIBE_TIMEOUT = float(os.environ.get("FLUXIA_TRANSCRIBE_TIMEOUT", "20"))
MEDIA_HOST = "https://mmg.whatsapp.net"
MAX_MEDIA_BYTES = 20 * 1024 * 1024

# Chave de derivação usada pelo WhatsApp para cada tipo de mídia.
APP_INFO = {
    "imageMessage": b"WhatsApp Image Keys",
    "stickerMessage": b"WhatsApp Image Keys",
    "videoMessage": b"WhatsApp Video Keys",
    "audioMessage": b"WhatsApp Audio Keys",
    "documentMessage": b"WhatsApp Document Keys",
}

EXTENSIONS = {
    "image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp",
    "audio/ogg": ".ogg", "audio/mpeg": ".mp3", "audio/mp4": ".m4a", "audio/aac": ".aac",
    "video/mp4": ".mp4", "application/pdf": ".pdf",
}


class MediaError(Exception):
    pass


def find_media(raw: dict | None) -> tuple[str, dict] | None:
    """Acha o bloco de mídia no protojson do Hermes (inclusive dentro de visualização única e documento com legenda)."""
    if not isinstance(raw, dict):
        return None
    for key in APP_INFO:
        node = raw.get(key)
        if isinstance(node, dict) and node.get("mediaKey"):
            return key, node
    for wrapper in ("viewOnceMessage", "viewOnceMessageV2", "viewOnceMessageV2Extension",
                    "documentWithCaptionMessage", "ephemeralMessage"):
        inner = (raw.get(wrapper) or {}).get("message")
        found = find_media(inner)
        if found:
            return found
    return None


def decrypt(enc: bytes, media_key_b64: str, kind: str) -> bytes:
    media_key = base64.b64decode(media_key_b64)
    expanded = HKDF(algorithm=hashes.SHA256(), length=112, salt=None, info=APP_INFO[kind]).derive(media_key)
    iv, cipher_key, mac_key = expanded[:16], expanded[16:48], expanded[48:80]
    if len(enc) <= 10:
        raise MediaError("arquivo vazio")
    body, mac = enc[:-10], enc[-10:]
    expected = hmac.new(mac_key, iv + body, hashlib.sha256).digest()[:10]
    if not hmac.compare_digest(mac, expected):
        raise MediaError("assinatura da mídia não confere")
    decryptor = Cipher(algorithms.AES(cipher_key), modes.CBC(iv)).decryptor()
    padded = decryptor.update(body) + decryptor.finalize()
    unpadder = padding.PKCS7(128).unpadder()
    return unpadder.update(padded) + unpadder.finalize()


MMS_TYPES = {"imageMessage": "image", "stickerMessage": "image", "videoMessage": "video",
             "audioMessage": "audio", "documentMessage": "document"}


async def download(kind: str, node: dict) -> bytes:
    urls = []
    direct = node.get("directPath") or ""
    if direct.startswith("/"):
        enc_hash = base64.urlsafe_b64encode(base64.b64decode(node.get("fileEncSha256") or "")).decode()
        urls.append(f"{MEDIA_HOST}{direct}&hash={enc_hash}&mms-type={MMS_TYPES[kind]}&__wa-mms=")
    if (node.get("url") or "").startswith("https://"):
        urls.append(node["url"])
    if not urls:
        raise MediaError("mídia sem endereço")
    last = "sem resposta"
    async with httpx.AsyncClient(timeout=60, follow_redirects=True, headers={"Origin": "https://web.whatsapp.com"}) as client:
        for url in urls:
            try:
                resp = await client.get(url)
            except httpx.HTTPError as e:
                last = str(e)[:80]
                continue
            if resp.status_code != 200:
                last = f"download respondeu {resp.status_code}"
                continue
            if len(resp.content) > MAX_MEDIA_BYTES:
                raise MediaError("arquivo grande demais")
            return decrypt(resp.content, node["mediaKey"], kind)
    raise MediaError(last)


def extension(mimetype: str, filename: str = "") -> str:
    base = (mimetype or "").split(";")[0].strip().lower()
    if base in EXTENSIONS:
        return EXTENSIONS[base]
    suffix = Path(filename).suffix.lower()
    return suffix if suffix and len(suffix) <= 6 and suffix[1:].isalnum() else ".bin"


_PAGE_RE = re.compile(rb"/Type\s*/Page(?![a-zA-Z])")
_STREAM_RE = re.compile(rb"stream\r?\n(.*?)\r?\nendstream", re.DOTALL)


def pdf_pages(data: bytes) -> int | None:
    """Conta as páginas de um PDF sem biblioteca: objetos /Type /Page, inclusive dentro de fluxos compactados."""
    count = len(_PAGE_RE.findall(data))
    if not count:
        for m in _STREAM_RE.finditer(data):
            try:
                count += len(_PAGE_RE.findall(zlib.decompress(m.group(1))))
            except zlib.error:
                continue
    return count or None


TRANSCRIBE_PROMPT = ("Transcreva fielmente este áudio de WhatsApp em português do Brasil. Responda só com o texto "
                     "falado, sem aspas nem comentários. Se não houver fala, responda exatamente: [sem fala]")
# Formato que o OmniRoute repassa ao Gemini (input_audio.format = audio/<formato>).
AUDIO_FORMATS = {"audio/ogg": "ogg", "audio/opus": "ogg", "audio/mpeg": "mp3", "audio/mp3": "mp3", "audio/wav": "wav",
                 "audio/x-wav": "wav", "audio/mp4": "aac", "audio/aac": "aac", "audio/x-m4a": "aac", "audio/webm": "webm"}


async def transcribe(audio: bytes, mimetype: str) -> str:
    """01/11: transcreve com o Gemini 3.8 (áudio direto no chat do OmniRoute). O Whisper do Groq parou: a conta
    foi bloqueada ("Organization has been restricted", 400) e todo áudio caía em "não consigo ouvir"."""
    fmt = AUDIO_FORMATS.get((mimetype or "audio/ogg").split(";")[0].strip().lower(), "ogg")
    content = [{"type": "text", "text": TRANSCRIBE_PROMPT},
               {"type": "input_audio", "input_audio": {"data": base64.b64encode(audio).decode(), "format": fmt}}]
    last = ""
    async with httpx.AsyncClient() as client:
        for model in TRANSCRIBE_MODELS:
            try:
                # 09/11: prazo curto por modelo; lento = passa para o próximo (o 2.5 Lite é a reserva do 3.5 Lite)
                resp = await client.post(f"{AI_URL}/v1/chat/completions", timeout=TRANSCRIBE_TIMEOUT,
                                         json={"model": model, "messages": [{"role": "user", "content": content}]})
                resp.raise_for_status()
                text = ((resp.json().get("choices") or [{}])[0].get("message") or {}).get("content") or ""
            except (httpx.HTTPError, ValueError) as e:
                last = f"{model}: {str(e)[:80]}"
                continue
            text = text.strip().strip('"').strip()
            from .agent import is_bad_reply
            if is_bad_reply(text):  # 07/11: aviso do provedor vinha como se fosse o áudio transcrito
                last = f"{model}: devolveu aviso de erro"
                continue
            return "" if text.lower().strip("[]. ") == "sem fala" else text
    raise MediaError(last or "transcrição falhou")
