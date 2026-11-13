"""Roda na Colab: baixa manhwa-drive:colab_recap/raiz (ou uma subpasta) pela API do Drive, só o que mudou (tamanho).
Token de 1 h que o PC grava em MyDrive/colab_recap/token_manhwa.json (cliente.gravar_token). Sem rclone na Colab.

  python baixar_drive.py                    tudo (código + assets)
  python baixar_drive.py D/recapd-ambientes/producao/bin D/recapd-ambientes/producao/config ...
"""
import json
import sys
import time
from pathlib import Path

import requests

TOKEN = Path("/content/drive/MyDrive/colab_recap/token_manhwa.json")
DESTINO = Path("/content/raiz")
API = "https://www.googleapis.com/drive/v3/files"
PASTA = "application/vnd.google-apps.folder"


def _token(s):
    s.headers["Authorization"] = f"Bearer {json.loads(TOKEN.read_text())['access_token']}"


def _listar(s, pasta_id):
    pagina = None
    while True:
        for tentativa in range(8):  # limite de taxa / token de 1 h vencido (o PC renova o arquivo a cada 30 min)
            r = s.get(API, params={"q": f"'{pasta_id}' in parents and trashed=false", "pageSize": 1000,
                                   "fields": "nextPageToken,files(id,name,mimeType,size)", "pageToken": pagina})
            if r.status_code in (401, 403, 429, 500, 502, 503) and tentativa < 7:
                time.sleep(2 ** tentativa)
                _token(s)
                continue
            break
        r.raise_for_status()
        d = r.json()
        yield from d["files"]
        pagina = d.get("nextPageToken")
        if not pagina:
            return


def _baixar(s, pasta_id, destino, cont):
    destino.mkdir(parents=True, exist_ok=True)
    for f in _listar(s, pasta_id):
        alvo = destino / f["name"]
        if f["mimeType"] == PASTA:
            _baixar(s, f["id"], alvo, cont)
        elif not (alvo.exists() and alvo.stat().st_size == int(f.get("size", -1))):
            _baixar_um(s, f, alvo, cont)


def _baixar_um(s, f, alvo, cont):
    for tentativa in range(6):  # 403/429 passageiro (limite de taxa do Drive, visto 24/10)
        with s.get(f"{API}/{f['id']}", params={"alt": "media"}, stream=True) as r:
            if r.status_code != 200:
                corpo = r.text
                passageiro = r.status_code in (401, 429, 500, 502, 503) or "ateLimit" in corpo
                if passageiro and tentativa < 5:
                    time.sleep(2 ** tentativa)
                    _token(s)
                    continue
                print(f"PULEI {alvo} ({r.status_code}): {corpo[:300]}", flush=True)  # não segura o resto
                cont[1] += 1
                return
            with open(alvo, "wb") as out:
                for bloco in r.iter_content(1 << 20):
                    out.write(bloco)
            cont[0] += 1
            return


def _achar(s, raiz_id, caminho):
    atual = raiz_id
    for nome in caminho.split("/"):
        atual = next(f["id"] for f in _listar(s, atual) if f["name"] == nome)
    return atual


def baixar(partes=()):
    t = json.loads(TOKEN.read_text())
    s = requests.Session()
    _token(s)
    cont = [0, 0]
    for parte in partes or [""]:
        pid = _achar(s, t["raiz_id"], parte) if parte else t["raiz_id"]
        _baixar(s, pid, DESTINO / parte if parte else DESTINO, cont)
    print(f"baixar_drive: {cont[0]} arquivos baixados, {cont[1]} pulados", flush=True)


def baixar_original(pid, destino):
    """Original de um pedido: manhwa-drive:colab_recap/fila_src/<pid>/source.mp4 -> destino."""
    t = json.loads(TOKEN.read_text())
    s = requests.Session()
    _token(s)
    pasta = _achar(s, t["src_id"], pid)
    cont = [0, 0]
    for f in _listar(s, pasta):
        if f["name"] == "source.mp4":
            _baixar_um(s, f, Path(destino), cont)
    if not Path(destino).exists():
        raise RuntimeError(f"original de {pid} não baixou")


if __name__ == "__main__":
    baixar(sys.argv[1:])
