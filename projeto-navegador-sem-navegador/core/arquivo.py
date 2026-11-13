# -*- coding: utf-8 -*-
r"""core/arquivo.py — gravação atômica (30/10). Os cookies e tokens daqui são lidos pela produção (youtube_http do
gemini-argo, postador, Veo) enquanto as tarefas (manter_cookies, ouvinte passivo, upload_http) os regravam: um
write_text direto deixa o arquivo pela metade por alguns ms e quem lê nessa hora recebe JSON quebrado.

    from core.arquivo import gravar_json, gravar_texto
    gravar_json(caminho, dados, indent=1)
"""
import contextlib
import json
import os
import time
from pathlib import Path


def gravar_texto(caminho, texto, encoding="utf-8"):
    """tmp no mesmo diretório + replace. No Windows o replace falha se outro processo está com o arquivo aberto
    naquele instante: tenta de novo por ~10 s antes de desistir."""
    alvo = Path(caminho)
    tmp = alvo.with_name(f"{alvo.name}.{os.getpid()}.tmp")
    tmp.write_text(texto, encoding)
    for i in range(20):
        try:
            tmp.replace(alvo)
            return alvo
        except PermissionError:
            time.sleep(0.05 * (i + 1))
    with contextlib.suppress(OSError):
        tmp.unlink()
    raise PermissionError(f"não consegui gravar {alvo} (arquivo preso por outro processo)")


def gravar_json(caminho, dados, indent=1, ensure_ascii=False):
    return gravar_texto(caminho, json.dumps(dados, ensure_ascii=ensure_ascii, indent=indent))
