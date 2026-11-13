# -*- coding: utf-8 -*-
"""Checagem de contato na tela (telefone/URL/@/QR) — veio de postador-de-videos/bin/comercial_veo.py seguro()
(26/10: o banimento de 16/10 foi número de WhatsApp na tela). Usada pelo cortes_produto (trecho de produto no Short).
Qualquer "sim" ou falha do gateway = NÃO seguro."""
import base64
import json
import re
import subprocess
import urllib.request
from pathlib import Path

GATEWAY = Path(r"D:\veo\beta\secrets\gateway.json")
PERGUNTA = ("Esta imagem e um quadro de um video curto. Existe escrito nela algum NUMERO DE TELEFONE, endereco de site "
            "ou URL, @ de perfil de rede social, ou QR code? (O nome de um produto, a palavra WhatsApp como nome de "
            "funcao e o texto 'LINK NO PERFIL' NAO contam.) Responda SO com JSON: "
            '{"contato": "sim" ou "nao", "o_que": "<o que achou ou vazio>"}')


def seguro(mp4, fracs=(0.2, 0.5, 0.8)):
    """(True, '') se nenhum quadro tem telefone/URL/@/QR; senão (False, motivo)."""
    try:
        gw = json.loads(GATEWAY.read_text(encoding="utf-8"))
        dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                                    str(mp4)], capture_output=True, text=True).stdout.strip() or 0)
        url = gw.get("gateway_url", "").rstrip("/") + "/v1/chat/completions"
        for f in fracs:
            img = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{dur * f:.2f}", "-i", str(mp4), "-frames:v", "1",
                                  "-vf", "scale=540:-2", "-f", "image2", "-vcodec", "mjpeg", "-"], capture_output=True).stdout
            corpo = {"model": "antigravity/gemini-3-flash", "max_tokens": 80, "messages": [{"role": "user", "content": [
                {"type": "text", "text": PERGUNTA},
                {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64," + base64.b64encode(img).decode()}}]}]}
            req = urllib.request.Request(url, data=json.dumps(corpo).encode(), headers={
                "Authorization": "Bearer " + gw["gateway_key"], "Content-Type": "application/json"})
            txt = json.loads(urllib.request.urlopen(req, timeout=90).read())["choices"][0]["message"]["content"]
            m = re.search(r'"contato"\s*:\s*"(\w+)"', txt)
            if not m or m.group(1).lower() != "nao":
                return False, f"quadro {int(f * 100)}%: {txt.strip()[:120]}"
        return True, ""
    except Exception as ex:  # noqa: BLE001
        return False, f"checagem falhou: {type(ex).__name__}: {str(ex)[:100]}"
