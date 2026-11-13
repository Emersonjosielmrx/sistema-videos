r"""medir_instagram_publico.py — seguidores/seguindo/posts de cada conta do Instagram pela PÁGINA PÚBLICA (sem login,
sem sessão de conta nenhuma), cada leitura por um IP rotativo diferente da Webshare grátis (nunca a internet de casa).
Grava D:\video-fila\estado\instagram_publico.jsonl (1 linha por medição) e imprime o ranking com o ganho desde a
última medição.   python D:\video-fila\medir_instagram_publico.py
"""
import json
import random
import re
import sys
import time
from datetime import datetime
from pathlib import Path

from curl_cffi import requests

POST = Path(r"D:\postador-de-videos")
HIST = Path(r"D:\video-fila\estado\instagram_publico.jsonl")
RX = re.compile(r'content="([\d.,KMmil]+) Followers, ([\d.,KMmil]+) Following, ([\d.,KMmil]+) Posts')


def _n(s):
    s = s.replace(",", "")
    mult = 1000 if s[-1:] in "Kk" else 1_000_000 if s[-1:] == "M" else 1
    return int(float(s.rstrip("KkM")) * mult)


def _proxies():
    out = []
    for l in (POST / "secrets" / "proxies.txt").read_text("utf-8").splitlines():
        m = re.match(r"^(?:https?://)?([^:\s]+-rotate):([^@\s]+)@p\.webshare\.io:80$", l.strip())
        if m:
            out.append(f"http://<USUARIO>:<SEGREDO_REMOVIDO>@p.webshare.io:80")
    return out[:-25]  # as últimas 25 são do Groq


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    reuso = json.loads((POST / "config" / "reuso_plataformas.json").read_text("utf-8"))
    contas = list((reuso.get("instagram") or {}).get("contas") or {})
    pausas = json.loads((POST / "config" / "instagram_pausas.json").read_text("utf-8"))
    antes = {}
    if HIST.exists():
        for l in HIST.read_text("utf-8").splitlines():
            try:
                r = json.loads(l)
                antes[r["conta"]] = r
            except (ValueError, KeyError):
                pass
    prox = []
    for p in _proxies():  # 10/11: 21 de 72 sem banda (402) — testa num site neutro e fica só com os que respondem
        try:
            if requests.get("https://api.ipify.org", impersonate="chrome", timeout=20,
                            proxies={"http": p, "https": p}).status_code == 200:
                prox.append(p)
        except Exception:  # noqa: BLE001
            pass
        if len(prox) >= 20:
            break
    if not prox:
        sys.exit("nenhum proxy grátis com banda — não meço pela internet de casa")
    random.shuffle(prox)
    agora = datetime.now().isoformat(timespec="minutes")
    res = []
    for i, c in enumerate(contas):
        r = None
        for tent in range(3):
            p = prox[(i * 3 + tent) % len(prox)]
            try:
                h = requests.get(f"https://www.instagram.com/{c}/", impersonate="chrome", timeout=30,
                                 proxies={"http": p, "https": p})
                m = RX.search(h.text)
                if m:
                    r = {"em": agora, "conta": c, "seguidores": _n(m.group(1)), "seguindo": _n(m.group(2)),
                         "posts": _n(m.group(3))}
                    break
                if h.status_code == 200 and "not-logged-in" in h.text[:3000] and "Followers" not in h.text:
                    r = {"em": agora, "conta": c, "erro": "página sem números (inativa/suspensa?)"}
            except Exception as e:  # noqa: BLE001
                r = {"em": agora, "conta": c, "erro": f"{type(e).__name__}"}
            time.sleep(random.uniform(4, 9))
        r = r or {"em": agora, "conta": c, "erro": "sem resposta com números"}
        res.append(r)
        with open(HIST, "a", encoding="utf-8") as f:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
        time.sleep(random.uniform(8, 20))
    ok = sorted([r for r in res if "seguidores" in r], key=lambda r: -r["seguidores"])
    print(f"{'conta':30} {'seguid.':>8} {'ganho':>6} {'posts':>6}  situação")
    for r in ok:
        a = antes.get(r["conta"], {})
        g = r["seguidores"] - a["seguidores"] if "seguidores" in a else None
        sit = "PAUSA: " + pausas[r["conta"]]["motivo"][:30] if r["conta"] in pausas else "ativa"
        print(f"{r['conta']:30} {r['seguidores']:8} {'' if g is None else f'{g:+d}':>6} {r['posts']:6}  {sit}")
    for r in res:
        if "erro" in r:
            print(f"{r['conta']:30} {'—':>8}        {'':6}  {r['erro']}")


if __name__ == "__main__":
    main()
