# COMUM — fonte única: D:\hipercool-materiais\comum\_tg_safe.py. Mudou esta cópia? python D:\hipercool-materiais\bin\recursos.py subir _tg_safe.py --de <projeto>
"""_tg_safe.py — Telegram helpers (versão simplificada pro hipercool).

Sem mirror, sem broadcast, sem TTS em texto. Apenas send() e send_video().
Padroniza HTML parse_mode.
"""
import html
import json
import os
import sys
import urllib.parse
import urllib.request
from pathlib import Path

DEFAULT_CHAT = "7988990790"
SECRETS_DIR = Path(__file__).resolve().parent.parent / "secrets"
# 18/10: nenhum projeto tem secrets/telegram-*.json; sem isto todo aviso daqui morria calado. O bot que o dono lê é o
# do postador (mesmo arquivo do notificar.py e do vigia_melhorias).
BOT_POSTADOR = Path(r"D:\postador-de-videos\config\telegram.json")

TELEGRAM_MAX_CHARS = 4096
TELEGRAM_CHUNK_CHARS = 3900
TELEGRAM_VIDEO_MAX_BYTES = 50 * 1024 * 1024
TELEGRAM_VIDEO_CAPTION_MAX = 1024

TOKENS = {}


def _conta(account="aviso-video-gerado"):
    """(token, chat) do bot: secrets/telegram-<account>.json se existir; senão o bot do postador."""
    if TOKENS.get(account) is None:
        p = SECRETS_DIR / f"telegram-{account}.json"
        if p.exists():
            d = json.loads(p.read_text(encoding="utf-8"))
            TOKENS[account] = (d["bot_token"], str(d.get("chat_id") or DEFAULT_CHAT))
        else:
            d = json.loads(BOT_POSTADOR.read_text(encoding="utf-8"))
            TOKENS[account] = (d["bot_token"], str(d["chat_id"]))
    return TOKENS[account]


def _token(account="aviso-video-gerado"):
    return _conta(account)[0]


def chat(account="aviso-video-gerado"):
    return _conta(account)[1]


def esc(s):
    """Escapa string pra interpolar dentro de HTML do Telegram."""
    return html.escape(str(s), quote=False)


def b(s):    return f"<b>{esc(s)}</b>"
def i(s):    return f"<i>{esc(s)}</i>"
def code(s): return f"<code>{esc(s)}</code>"
def pre(s):  return f"<pre>{esc(s)}</pre>"


_PROJETOS = {"hipercool-videos": "hipercool", "recapd-ambientes": "recapd", "historias-em-frames": "historias",
             "postador-de-videos": "postador"}
ORIGEM = next((_PROJETOS[p] for p in Path(__file__).resolve().parts if p in _PROJETOS), "vídeos")


def send(text, chat_id=None, account="aviso-video-gerado",
         parse_mode="HTML", silent=False, timeout=15, origem=None, importante=False):
    """Envia mensagem. Texto > 3900 chars é dividido em chunks.
    Retorna True se todos os chunks foram enviados.
    19/10 (dono: "manda muita mensagem"): sem chat_id explícito vai pelo PORTÃO ÚNICO (D:\\video-fila\\avisos.py) —
    repetido não sai e rotina (importante=False) vai pro resumo das 9h/14h/21h.
    """
    if chat_id is None and text:
        try:
            if r"D:\video-fila" not in sys.path:
                sys.path.insert(0, r"D:\video-fila")
            import avisos
            avisos.enviar(text, origem or ORIGEM, importante=importante, html_ok=bool(parse_mode))
            return True
        except Exception:  # noqa: BLE001 — sem o portão manda direto, como antes
            pass
    token, padrao = _conta(account)
    chat_id = chat_id or padrao
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    if not text:
        return True
    chunks = [text[j:j + TELEGRAM_CHUNK_CHARS]
              for j in range(0, len(text), TELEGRAM_CHUNK_CHARS)]
    for ch in chunks:
        payload = {
            "chat_id": str(chat_id),
            "text": ch,
            "disable_web_page_preview": "true",
        }
        if parse_mode:
            payload["parse_mode"] = parse_mode
        if silent:
            payload["disable_notification"] = "true"
        data = urllib.parse.urlencode(payload).encode("utf-8")
        try:
            req = urllib.request.Request(url, data=data, method="POST")
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                if resp.status != 200:
                    return False
        except Exception as e:
            # Fallback plaintext
            if parse_mode:
                import re as _re
                plain = _re.sub(r"<[^>]+>", "", ch)
                p2 = {"chat_id": str(chat_id), "text": plain}
                d2 = urllib.parse.urlencode(p2).encode("utf-8")
                try:
                    r2 = urllib.request.Request(url, data=d2, method="POST")
                    with urllib.request.urlopen(r2, timeout=timeout):
                        pass
                except Exception:
                    return False
            else:
                print(f"[tg_safe] send falhou: {e}", file=sys.stderr)
                return False
    return True


def send_telegram(msg, importante=False):
    """Nome usado pelo historias (story_pipeline, queue_runner, night_shift_driver); antes não existia aqui."""
    return send(esc(msg), importante=importante)


def _build_multipart(fields, file_field, file_path, file_mime="video/mp4"):
    """Constrói corpo multipart/form-data + boundary. stdlib-only."""
    import uuid as _uuid
    boundary = "----hipercool" + _uuid.uuid4().hex
    crlf = b"\r\n"
    body = []
    for k, v in fields.items():
        if v is None:
            continue
        body.append(f"--{boundary}".encode())
        body.append(f'Content-Disposition: form-data; name="{k}"'.encode())
        body.append(b"")
        body.append(str(v).encode("utf-8"))
    body.append(f"--{boundary}".encode())
    filename = os.path.basename(file_path)
    body.append(
        f'Content-Disposition: form-data; name="{file_field}"; filename="{filename}"'.encode()
    )
    body.append(f"Content-Type: {file_mime}".encode())
    body.append(b"")
    with open(file_path, "rb") as f:
        body.append(f.read())
    body.append(f"--{boundary}--".encode())
    body.append(b"")
    return crlf.join(body), boundary


def send_video(mp4_path, chat_id=None, account="aviso-video-gerado",
               caption="", parse_mode="HTML", silent=False, timeout=120):
    """Envia vídeo MP4 com legenda opcional. Limite 50MB."""
    if not os.path.exists(mp4_path):
        print(f"[tg_safe] send_video: arquivo não existe: {mp4_path}", file=sys.stderr)
        return False
    size = os.path.getsize(mp4_path)
    if size > TELEGRAM_VIDEO_MAX_BYTES:
        print(f"[tg_safe] send_video: {mp4_path} > 50MB. Enviando só legenda.",
              file=sys.stderr)
        if caption:
            return send(caption + "\n\n[!] (vídeo > 50MB, não anexado)",
                        chat_id, account, parse_mode, silent, timeout)
        return False
    if caption and len(caption) > TELEGRAM_VIDEO_CAPTION_MAX:
        caption = caption[:TELEGRAM_VIDEO_CAPTION_MAX - 4] + "…"

    token, padrao = _conta(account)
    chat_id = chat_id or padrao
    url = f"https://api.telegram.org/bot{token}/sendVideo"
    fields = {
        "chat_id": str(chat_id),
        "caption": caption or "",
        "supports_streaming": "true",
    }
    if parse_mode:
        fields["parse_mode"] = parse_mode
    if silent:
        fields["disable_notification"] = "true"
    body, boundary = _build_multipart(fields, "video", mp4_path)
    headers = {"Content-Type": f"multipart/form-data; boundary={boundary}"}
    try:
        req = urllib.request.Request(url, data=body, headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status == 200
    except Exception as e:
        print(f"[tg_safe] sendVideo falhou ({account} -> {chat_id}): {e}",
              file=sys.stderr)
        return False
