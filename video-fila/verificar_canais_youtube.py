r"""verificar_canais_youtube.py — confere canais do YouTube pela PÁGINA PÚBLICA (sem login, sem conta, sem API):
existe? nome, inscritos e quantos Shorts aparecem na aba /shorts. Cada leitura sai por um IP rotativo da Webshare
grátis (nunca a internet de casa), com pausa entre canais (sem rajada).

    python verificar_canais_youtube.py @handle1 @handle2 ...      → tabela + estado\canais_verificados.jsonl
"""
import json
import random
import re
import sys
import time
from datetime import datetime
from pathlib import Path

from curl_cffi import requests

SAIDA = Path(__file__).resolve().parent / "estado" / "canais_verificados.jsonl"
PROXIES = Path(r"D:\postador-de-videos\secrets\proxies.txt")


def _proxies():
    out = []
    for l in PROXIES.read_text("utf-8").splitlines():
        m = re.match(r"^(?:https?://)?([^:\s]+-rotate):([^@\s]+)@p\.webshare\.io:80$", l.strip())
        if m:
            out.append(f"http://<USUARIO>:<SEGREDO_REMOVIDO>@p.webshare.io:80")
    return out[:-25]  # as últimas 25 são do Groq


def _num(txt):
    """'2,6 mi' / '950 mil' / '1.2M' / '12K' -> int aproximado."""
    t = txt.lower().replace("\xa0", " ").strip()
    m = re.match(r"([\d.,]+)\s*(mi|mil|m|k|bi)?", t)
    if not m:
        return None
    n = float(m.group(1).replace(".", "").replace(",", ".")) if m.group(2) else float(m.group(1).replace(".", "").replace(",", ""))
    mult = {"mi": 1e6, "m": 1e6, "mil": 1e3, "k": 1e3, "bi": 1e9}.get(m.group(2) or "", 1)
    return int(n * mult)


def checar(handle, prox):
    h = handle.lstrip("@").strip()
    url = f"https://www.youtube.com/@{h}/shorts?hl=pt-BR&gl=BR"
    hdr = {"Accept-Language": "pt-BR,pt;q=0.9", "Cookie": "<SEGREDO_REMOVIDO>"}
    ultimo = "?"
    for p in random.sample(prox, min(3, len(prox))):
        try:
            r = requests.get(url, headers=hdr, proxies={"http": p, "https": p}, timeout=40, impersonate="chrome")
        except Exception as e:  # noqa: BLE001
            ultimo = type(e).__name__
            continue
        if r.status_code == 404:
            return {"handle": "@" + h, "existe": False}
        if r.status_code != 200:
            ultimo = f"HTTP {r.status_code}"
            continue
        t = r.text
        nome = re.search(r'<meta property="og:title" content="([^"]+)"', t)
        insc = re.search(r'"(?:subscriberCountText|content)":\{?"?(?:simpleText|content)?"?:?"?([\d.,]+\s*(?:mi|mil|M|K|bi)?)\s*(?:de )?inscritos', t) \
            or re.search(r'([\d.,]+\s*(?:mi|mil|M|K|bi)?)\s*(?:de )?inscritos', t)
        shorts = len(set(re.findall(r'"/shorts/([\w-]{11})"', t)))
        return {"handle": "@" + h, "existe": True, "nome": nome.group(1) if nome else "?",
                "inscritos_txt": insc.group(1).strip() if insc else "?",
                "inscritos": _num(insc.group(1)) if insc else None, "shorts_na_pagina": shorts}
    return {"handle": "@" + h, "existe": None, "erro": ultimo}


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    prox = _proxies()
    res = []
    for h in sys.argv[1:]:
        r = checar(h, prox)
        r["em"] = datetime.now().isoformat(timespec="minutes")
        res.append(r)
        SAIDA.parent.mkdir(parents=True, exist_ok=True)
        with open(SAIDA, "a", encoding="utf-8") as f:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
        print(f"{r['handle']:28} {'EXISTE' if r.get('existe') else ('NÃO EXISTE' if r.get('existe') is False else 'erro ' + str(r.get('erro')))}"
              f"  {r.get('nome', '')[:34]:34} inscritos={r.get('inscritos_txt', '')}  shorts={r.get('shorts_na_pagina', '')}",
              flush=True)
        time.sleep(random.uniform(4, 8))


if __name__ == "__main__":
    main()
