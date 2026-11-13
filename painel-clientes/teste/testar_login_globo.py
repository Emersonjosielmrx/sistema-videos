# -*- coding: utf-8 -*-
"""31/10: confere no painel publicado que globo/globo entra e cai no cliente Globo Solar (não imprime a chave)."""
import json
import urllib.request

URL = "https://clientes.opus-sem-limites.com.br"
req = urllib.request.Request(f"{URL}/api/entrar", data=json.dumps({"usuario": "globo", "senha": "globo"}).encode(),
                             headers={"Content-Type": "application/json"}, method="POST")
d = json.loads(urllib.request.urlopen(req, timeout=30).read())
print("login ok:", bool(d.get("chave") or d.get("k")), "| campos:", sorted(d))
chave = d.get("chave") or d.get("k")
if chave:
    r = urllib.request.Request(f"{URL}/api/eu", headers={"X-Chave": chave})
    try:
        print("eu:", json.loads(urllib.request.urlopen(r, timeout=30).read()))
    except Exception as e:  # noqa: BLE001
        print("eu: (rota não existe ou outro nome)", type(e).__name__)
