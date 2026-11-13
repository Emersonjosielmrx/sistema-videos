# -*- coding: utf-8 -*-
r"""status_whatsapp.py — manda um vídeo que acabou de sair no Instagram para o STATUS do WhatsApp do cliente
(dona 30/10/2026). O cliente conecta o WhatsApp dele no Painel de Clientes (botão "conectar WhatsApp": QR code ou
código pelo número); o painel guarda a conta dele no Hermes Call e posta o status pela API do Hermes.

Uso pelos postadores (nunca derruba quem chama: devolve True/False e escreve o motivo no log):
    sys.path.insert(0, r"D:\painel-clientes\coletor")
    import status_whatsapp
    status_whatsapp.mandar_video("advance", mp4, legenda, log=log)

Só biblioteca padrão. Chave de admin do painel em segredos\chaves.json (a mesma do coletor do Instagram).
"""
import base64
import json
import re
import urllib.error
import urllib.request
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
CHAVES = RAIZ / "segredos" / "chaves.json"
PAINEL = "https://clientes.opus-sem-limites.com.br"
MAX_MB = 40  # o status do WhatsApp aceita vídeo curto; acima disso nem tenta


def mandar_video(cliente, mp4, legenda="", log=print):
    mp4 = Path(mp4)
    try:
        if not mp4.exists():
            log(f"status WhatsApp: vídeo não existe ({mp4.name})")
            return False
        if mp4.stat().st_size > MAX_MB * 1024 * 1024:
            log(f"status WhatsApp: vídeo grande demais ({mp4.stat().st_size // 1048576} MB)")
            return False
        chave = json.loads(CHAVES.read_text(encoding="utf-8")).get("admin")
        # status com hashtag parece spam: vai só o texto (a 1ª parte da legenda do Instagram)
        legenda = re.sub(r"[ \t]*#\S+", "", legenda or "").strip()
        legenda = re.sub(r"\n{3,}", "\n\n", legenda)
        corpo = json.dumps({"cliente": cliente, "legenda": legenda[:700],
                            "video_base64": base64.b64encode(mp4.read_bytes()).decode()}).encode()
        req = urllib.request.Request(f"{PAINEL}/api/whatsapp/status", data=corpo,
                                     headers={"Content-Type": "application/json", "X-Chave": chave,
                                              "User-Agent": "painel-clientes-status/1"})
        r = json.loads(urllib.request.urlopen(req, timeout=400).read())
        log(f"status WhatsApp ({cliente}): enviado {r}")
        return True
    except urllib.error.HTTPError as e:
        try:
            msg = json.loads(e.read()).get("erro")
        except Exception:  # noqa: BLE001
            msg = ""
        # 409 = o cliente ainda não conectou o WhatsApp no painel: normal, só registra
        log(f"status WhatsApp ({cliente}): não enviado — {msg or e.code}")
    except Exception as e:  # noqa: BLE001
        log(f"status WhatsApp ({cliente}): falhou {type(e).__name__}: {str(e)[:160]}")
    return False
