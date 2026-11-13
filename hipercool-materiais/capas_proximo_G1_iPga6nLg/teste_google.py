# Teste 01/11 (dona): o modelo de imagem do Google pelo Antigravity/OmniRoute (o "gateway" do capa_ia_anime, desligado
# desde 20/10 por 403/429) gera as mesmas capas A e C do G1 que ela aprovou? Só texto: esse endpoint não recebe
# imagem de referência, então o protagonista não vem da capa do parceiro.
import base64
import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, r"D:\recapd-ambientes\producao\bin")
import capa_ia_anime as c  # noqa: E402
import gerar_g1 as g  # noqa: E402

OUT = Path(__file__).parent / "teste_google"
OUT.mkdir(exist_ok=True)
base, tok = c._gateway()
print("gateway:", base, "com token" if tok else "SEM TOKEN", "| modelo:", c.MODELO, flush=True)
for letra in sys.argv[1:] or "AC":
    t = time.time()
    corpo = json.dumps({"model": c.MODELO, "prompt": g.CAPAS[letra], "n": 1, "response_format": "b64_json",
                        "size": "1792x1024", "aspect_ratio": "16:9"}).encode()
    req = urllib.request.Request(base + "/v1/images/generations", data=corpo,
                                 headers={"Content-Type": "application/json", "Authorization": "Bearer " + tok})
    try:
        with urllib.request.urlopen(req, timeout=180) as r:
            b = ((json.loads(r.read()).get("data") or [{}])[0]).get("b64_json")
        if b:
            (OUT / f"google_{letra}.png").write_bytes(base64.b64decode(b))
            print(letra, "OK", int(time.time() - t), "s", flush=True)
        else:
            print(letra, "sem imagem na resposta", flush=True)
    except urllib.error.HTTPError as e:
        print(letra, "HTTP", e.code, e.read().decode("utf-8", "replace")[:300], flush=True)
    except Exception as e:  # noqa: BLE001
        print(letra, type(e).__name__, str(e)[:300], flush=True)
