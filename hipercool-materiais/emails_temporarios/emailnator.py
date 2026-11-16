r"""emailnator.py — Gmail temporário de verdade (@gmail.com com pontos/+ ou @googlemail.com) do emailnator.com.
O site fica atrás de Cloudflare + botwafguard, então a API interna é chamada de DENTRO da página (Chrome headless pelo
proxy grátis rotativo do Webshare). Mesmo Chrome fica aberto entre criar e ler (o cookie da sessão vale só nele).

    python emailnator.py sondar          # descobre os endpoints de leitura
    python emailnator.py criar [tipo]    # tipo: dotGmail (padrão), plusGmail, googleMail, domain
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import testar_provedores as tp  # noqa: E402

TIPOS = {"domain": 1, "plusGmail": 2, "dotGmail": 3, "googleMail": 8}
JS = """async ([u, b]) => {
  const r = await fetch(u, {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify(b)});
  return [r.status, (await r.text()).slice(0, 400000)];  // 15/11: corte em 3000 quebrava o JSON (caixa "vazia")
}"""
LIMPA = """() => document.querySelectorAll('.fc-consent-root,.fc-message-root,.fc-dialog-overlay').forEach(e => e.remove())"""


class Emailnator:
    def __init__(self):
        from playwright.sync_api import sync_playwright
        rot = tp.sessao().proxies["http"]
        user, resto = rot.split("//", 1)[1].split(":", 1)
        self._pw = sync_playwright().start()
        self.br = self._pw.chromium.launch(channel="chrome", headless=True, proxy={
            "server": "http://p.webshare.io:80", "username": user, "password": resto.split("@", 1)[0]})
        self.page = self.br.new_page(user_agent=tp.UA)
        self.page.goto("https://www.emailnator.com/", timeout=60000, wait_until="domcontentloaded")
        self.page.wait_for_timeout(8000)
        self.page.evaluate(LIMPA)

    def post(self, url, corpo):
        st, txt = self.page.evaluate(JS, [url, corpo])
        try:
            return st, json.loads(txt)
        except ValueError:
            return st, txt[:300]

    def criar(self, tipo="dotGmail"):
        st, j = self.post("/api/generate-email", {"ids": [TIPOS[tipo]]})
        if st != 200 or not isinstance(j, dict) or "email" not in j:
            raise RuntimeError(f"emailnator generate {st}: {str(j)[:200]}")
        return j["email"]

    def ler(self, email):
        st, j = self.post("/api/message-list", {"email": email})
        if st != 200:
            raise RuntimeError(f"emailnator message-list {st}: {str(j)[:200]}")
        msgs = j.get("messageData", j.get("messages", [])) if isinstance(j, dict) else []
        return [{"de": m.get("from"), "assunto": m.get("subject"), "id": m.get("messageID") or m.get("id")}
                for m in msgs if not str(m.get("messageID", "")).startswith("ADS")]

    def corpo(self, msg_id):
        """Corpo (HTML/texto) de uma mensagem: GET /api/message/<id> (achado 15/11 clicando no site)."""
        st, txt = self.page.evaluate("""async (u) => { const r = await fetch(u);
            return [r.status, (await r.text()).slice(0, 400000)]; }""", f"/api/message/{msg_id}")
        if st != 200:
            raise RuntimeError(f"emailnator message {st}: {txt[:150]}")
        return txt

    def fechar(self):
        try:
            self.br.close()
        finally:
            self._pw.stop()


if __name__ == "__main__":
    a = sys.argv[1:] or ["sondar"]
    e = Emailnator()
    try:
        if a[0] == "sondar":
            em = e.criar("dotGmail")
            print("email", em)
            for u in ("/api/message-list", "/api/inbox", "/api/messages", "/message-list"):
                print(u, e.post(u, {"email": em}))
        else:
            em = e.criar(a[1] if len(a) > 1 else "dotGmail")
            print(em, e.ler(em))
    finally:
        e.fechar()
