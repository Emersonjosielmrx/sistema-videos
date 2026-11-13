# 02/11 dona: "uma segunda pasta tentando com o Google imagem". O google_imagem.gerar só manda texto; aqui testo se o
# /v1/images/generations (ou /edits) do OmniRoute passa as referências (capa do parceiro) pro modelo do Google.
import base64
import json
import sys
import urllib.request
from pathlib import Path

import google_imagem as g

REF = Path(sys.argv[1])
SAIDA = Path(sys.argv[2])
e = g.atualizar_lista(g._ler())
cid = sorted(g.na_fila(e), key=lambda k: e["contas"][k].get("ok", 0))[0]
base, tok = g._gateway()
b64 = base64.b64encode(REF.read_bytes()).decode()
url = "data:image/jpeg;base64," + b64
PROMPT = ("Redraw this anime thumbnail with the same hero and background, and add three gorgeous adult women in tiny "
          "bikinis around him. No text.")
VARIANTES = {"image": url, "images": [url], "image_url": url, "reference_images": [url], "input_image": url}
H = {"Content-Type": "application/json", "Authorization": "Bearer " + tok, "x-omniroute-connection": cid}
for rota in ("/v1/images/edits", "/v1/images/generations"):
    for campo, valor in VARIANTES.items():
        corpo = {"model": g.MODELO, "prompt": PROMPT, "n": 1, "response_format": "b64_json", "aspect_ratio": "16:9",
                 campo: valor}
        req = urllib.request.Request(base + rota, data=json.dumps(corpo).encode(), headers=H)
        try:
            with urllib.request.urlopen(req, timeout=240) as r:
                d = json.loads(r.read())
            b = ((d.get("data") or [{}])[0]).get("b64_json")
            if b:
                out = SAIDA.with_name(f"{SAIDA.stem}_{rota.split('/')[-1]}_{campo}.png")
                out.write_bytes(base64.b64decode(b))
                print("OK", rota, campo, out)
            else:
                print("sem imagem", rota, campo, str(d)[:200])
        except urllib.error.HTTPError as ex:
            print("HTTP", ex.code, rota, campo, ex.read().decode("utf-8", "replace")[:200])
        if rota == "/v1/images/generations" and campo != "image":
            pass
