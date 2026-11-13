# Teste: o modelo de imagem do Google aceita imagem de referência? (/v1/images/edits ou campo image no generations)
import base64
import json
import re
import sys
import urllib.error
import urllib.request
import uuid
from pathlib import Path

sys.path.append(r"D:\flow-imagens")
import google_imagem as gi  # noqa: E402

base, tok = gi._gateway()
e = gi.atualizar_lista(gi._ler())
cid = sorted(gi.na_fila(e), key=lambda k: e["contas"][k].get("ok", 0))[0]
ref = Path(__file__).parent / "poses" / "de_quatro_costas_cama.png"
PROMPT = ("Redraw this exact pose and framing as a new anime image: same body proportions, but the woman has long pink "
          "hair and wears a tiny pink bikini. No text.")
H = {"Authorization": "Bearer " + tok, "x-omniroute-connection": cid}


def salvar(d, nome):
    b = ((d.get("data") or [{}])[0]).get("b64_json")
    if b:
        (Path(__file__).parent / "teste" / nome).write_bytes(base64.b64decode(b))
        return "IMAGEM SALVA " + nome
    return "sem imagem: " + json.dumps(d)[:200]


# 1) multipart /v1/images/edits (padrão OpenAI)
bd = uuid.uuid4().hex
partes = []
for k, v in (("model", gi.MODELO), ("prompt", PROMPT), ("response_format", "b64_json")):
    partes.append(f"--{bd}\r\nContent-Disposition: form-data; name=\"{k}\"\r\n\r\n{v}\r\n".encode())
partes.append(f"--{bd}\r\nContent-Disposition: form-data; name=\"image\"; filename=\"ref.png\"\r\nContent-Type: image/png\r\n\r\n".encode()
              + ref.read_bytes() + b"\r\n")
partes.append(f"--{bd}--\r\n".encode())
req = urllib.request.Request(base + "/v1/images/edits", data=b"".join(partes),
                             headers={**H, "Content-Type": f"multipart/form-data; boundary={bd}"})
try:
    with urllib.request.urlopen(req, timeout=240) as r:
        print("edits:", salvar(json.loads(r.read()), "ref_google_edits.png"))
except urllib.error.HTTPError as ex:
    print("edits HTTP", ex.code, ex.read().decode()[:300])

# 2) generations com campo image (base64)
b64 = base64.b64encode(ref.read_bytes()).decode()
for campo in ("image", "images", "reference_images"):
    val = "data:image/png;base64," + b64 if campo == "image" else ["data:image/png;base64," + b64]
    corpo = {"model": gi.MODELO, "prompt": PROMPT, "n": 1, "response_format": "b64_json", campo: val}
    req = urllib.request.Request(base + "/v1/images/generations", data=json.dumps(corpo).encode(),
                                 headers={**H, "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=240) as r:
            print(campo, ":", salvar(json.loads(r.read()), f"ref_google_{campo}.png"))
    except urllib.error.HTTPError as ex:
        print(campo, "HTTP", ex.code, ex.read().decode()[:200])
