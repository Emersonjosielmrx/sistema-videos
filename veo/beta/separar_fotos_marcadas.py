#!/usr/bin/env python3
"""separar_fotos_marcadas.py - acha as fotos de entrada (D:\\veo\\fotos) com marca d'agua de IA no canto ("Grok"...).

Por que (16/10): a foto feita no Grok leva o "Grok" do canto para o video do Veo, e o limpar_veo (com razao) barra o
video na rede. Os 3 primeiros do Veo religado cairam assim. Mesma pergunta e mesmo gateway do
D:\\postador-de-videos\\bin\\limpar_veo.py::marca_ia, so que na foto (o canto inferior direito, ampliado).

Cada resultado vai para logs/marcas_fotos.json na hora (retomavel: quem ja tem resposta e pulado).
    python separar_fotos_marcadas.py            # so classifica
    python separar_fotos_marcadas.py --mover    # move as marcadas para fotos\\_com_marca (o gerador so le a raiz)
"""
import argparse
import base64
import json
import re
import shutil
import subprocess
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, r"D:\postador-de-videos\bin")
from limpar_veo import FFMPEG, GATEWAY, _PERG_MARCA  # noqa: E402

FOTOS = Path(r"D:\veo\fotos")
DESTINO = FOTOS / "_com_marca"
RELATORIO = Path(__file__).resolve().parent / "logs" / "marcas_fotos.json"


def marca_foto(foto, gw):
    """Nome da marca no canto inferior direito da foto ou None. Falha do gateway levanta."""
    img = subprocess.run([FFMPEG, "-v", "error", "-i", str(foto), "-frames:v", "1", "-vf",
                          "crop=iw*0.45:ih*0.12:iw*0.55:ih*0.88,scale=-1:240", "-f", "image2", "-vcodec", "mjpeg",
                          "-"], capture_output=True).stdout
    if not img:
        raise ValueError("ffmpeg nao leu a foto")
    url = gw.get("gateway_url", "http://157.173.207.22:20128").rstrip("/") + "/v1/chat/completions"
    corpo = {"model": "antigravity/gemini-3-flash", "max_tokens": 40, "messages": [{"role": "user", "content": [
        {"type": "text", "text": _PERG_MARCA},
        {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64," + base64.b64encode(img).decode()}}]}]}
    req = urllib.request.Request(url, data=json.dumps(corpo).encode(), headers={
        "Authorization": "Bearer " + gw["gateway_key"], "Content-Type": "application/json"})
    txt = json.loads(urllib.request.urlopen(req, timeout=60).read())["choices"][0]["message"]["content"]
    achou = re.search(r'"marca"\s*:\s*"([^"]*)"', txt)
    nome = (achou.group(1) if achou else txt).strip()
    return None if not nome or re.fullmatch(r"(?i)nenhuma|none|nao|não|-", nome) else nome


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mover", action="store_true")
    a = ap.parse_args()
    gw = json.loads(GATEWAY.read_text(encoding="utf-8"))
    rel = json.loads(RELATORIO.read_text("utf-8")) if RELATORIO.exists() else {}
    # raiz + subpastas por tema (comedia, epocas, guerra, herois, jornal - item AT-06); chave = caminho relativo
    # ("epocas/image (3).jpg"; na raiz so o nome, como antes). _com_marca/_suspeitas ficam de fora.
    fotos = sorted(p for p in FOTOS.rglob("*") if p.is_file() and p.suffix.lower() in (".jpg", ".jpeg", ".png")
                   and not any(parte.startswith("_") for parte in p.relative_to(FOTOS).parts[:-1]))
    for i, foto in enumerate(fotos, 1):
        chave = foto.relative_to(FOTOS).as_posix()
        if "marca" in rel.get(chave, {}):
            continue
        try:
            rel[chave] = {"marca": marca_foto(foto, gw)}
        except Exception as ex:  # noqa: BLE001
            rel[chave] = {"erro": str(ex)[:120]}
        RELATORIO.write_text(json.dumps(rel, ensure_ascii=False, indent=1), "utf-8")
        print(f"[{i}/{len(fotos)}] {chave}: {rel[chave]}", flush=True)
    marcadas = [n for n, r in rel.items() if r.get("marca")]
    erros = [n for n, r in rel.items() if "erro" in r]
    print(f"fotos: {len(fotos)} | com marca: {len(marcadas)} | sem resposta: {len(erros)}")
    if a.mover:
        DESTINO.mkdir(exist_ok=True)
        movidas = 0
        for n in marcadas:
            if (FOTOS / n).exists():
                shutil.move(str(FOTOS / n), str(DESTINO / n))
                movidas += 1
        print(f"movidas para {DESTINO}: {movidas}")


if __name__ == "__main__":
    main()
