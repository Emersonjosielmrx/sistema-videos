r"""espiar_xhr.py — abre um site de e-mail temporário no Chrome (headless, pelo proxy grátis rotativo) e lista as
chamadas XHR/fetch que ele faz, para descobrir a API interna. Não toca em conta nenhuma.

    python espiar_xhr.py https://www.emailnator.com/ [segundos]
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import testar_provedores as tp  # noqa: E402


def main(url, seg=15):
    from playwright.sync_api import sync_playwright
    rot = tp.sessao().proxies["http"]
    user, resto = rot.split("//", 1)[1].split(":", 1)
    senha = resto.split("@", 1)[0]
    with sync_playwright() as pw:
        br = pw.chromium.launch(channel="chrome", headless=True,
                                proxy={"server": "http://p.webshare.io:80", "username": user, "password": senha})
        page = br.new_page(user_agent=tp.UA)

        def resp(r):
            if r.request.resource_type in ("xhr", "fetch"):
                try:
                    corpo = r.text()[:220].replace("\n", " ")
                except Exception:  # noqa: BLE001
                    corpo = "?"
                print(r.request.method, r.status, r.url[:120], "|", (r.request.post_data or "")[:120], "=>", corpo, flush=True)
        page.on("response", resp)
        page.goto(url, timeout=60000, wait_until="domcontentloaded")
        page.wait_for_timeout(int(seg) * 1000)
        print("TITULO", page.title())
        print("TEXTO", page.inner_text("body")[:600].replace("\n", " | "))
        br.close()


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else 15)
