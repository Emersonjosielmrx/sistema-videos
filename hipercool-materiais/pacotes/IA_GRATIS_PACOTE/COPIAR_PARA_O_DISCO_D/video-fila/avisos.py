# -*- coding: utf-8 -*-
"""avisos.py SUBSTITUTO (o original manda para os bots do Telegram e não vem no pacote).

Os monitores/zeladores chamam avisos.enviar(...). Aqui:
  - sempre imprime e grava em D:\\video-fila\\avisos.log
  - se existirem as variáveis TELEGRAM_BOT_TOKEN e TELEGRAM_CHAT_ID, manda também pro Telegram
Para configurar o Telegram (opcional), no PowerShell:
  setx TELEGRAM_BOT_TOKEN "123456:ABC..."   (o token do @BotFather)
  setx TELEGRAM_CHAT_ID   "123456789"       (seu id de chat)
"""
import json
import os
import time
import urllib.parse
import urllib.request
from pathlib import Path

LOG = Path(__file__).resolve().parent / "avisos.log"
_ja = {}


def enviar(msg, origem="geral", importante=False, chave=None, html_ok=True, **_):
    if chave and _ja.get(chave):          # mesmo aviso repetido: não manda de novo
        return False
    if chave:
        _ja[chave] = time.time()
    linha = f"[{time.strftime('%d/%m %H:%M')}] [{origem}]{' [!]' if importante else ''} {msg}"
    print(linha)
    try:
        with LOG.open("a", encoding="utf-8") as f:
            f.write(linha + "\n")
    except OSError:
        pass
    tok, chat = os.environ.get("TELEGRAM_BOT_TOKEN"), os.environ.get("TELEGRAM_CHAT_ID")
    if not (tok and chat):
        return True
    dados = {"chat_id": chat, "text": f"[{origem}] {msg}"[:4000]}
    if html_ok:
        dados["parse_mode"] = "HTML"
    try:
        urllib.request.urlopen(f"https://api.telegram.org/bot{tok}/sendMessage",
                               data=urllib.parse.urlencode(dados).encode(), timeout=20)
        return True
    except Exception as e:  # noqa: BLE001
        print("telegram falhou:", e)
        return False
