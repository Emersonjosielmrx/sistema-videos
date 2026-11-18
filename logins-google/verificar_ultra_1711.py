"""17/11 dona: ver em quais contas SEM canal (fora do Kaggle) a oferta Google AI Ultra 12 meses aparece.
Cada conta ganha um IP Webshare fixo PRÓPRIO (rnprmtfo-91..99, nunca usados) e passa a sair sempre por ele.
UMA conta a cada 20 min, só LÊ a página (nunca clica em Assinar), fecha o Chrome. Resultado em ultra_resultado_1711.json."""
import json, re, sys, time
sys.path.insert(0, r"D:\logins-google")
import cofre
from playwright.sync_api import sync_playwright
LINK = open(r"C:\Users\Haylla\AppData\Local\Temp\ultra_link.txt").read().strip()
IPS = [n for n, _ip in json.load(open(r"C:\Users\Haylla\AppData\Local\Temp\ips_livres.json")) if n != 100]
CONTAS = ["canalalucinaai@gmail.com", "canalhistoriacomia@gmail.com", "comoseriasecomia@gmail.com",
          "e4487017@gmail.com", "emersongenc@gmail.com", "emersongencshin@gmail.com", "emersonjosiel1995@gmail.com",
          "emersonjosiel649@gmail.com", "en1653964@gmail.com"]
SAIDA = r"D:\logins-google\ultra_resultado_1711.json"
LOG = open(r"D:\logins-google\ultra_1711.log", "a", encoding="utf-8")
def L(m):
    m = f"[{time.strftime('%H:%M:%S')}] {m}"; print(m, flush=True); LOG.write(m + "\n"); LOG.flush()
try:
    res = json.load(open(SAIDA, encoding="utf-8"))
except Exception:
    res = {"aulacomia@gmail.com": {"oferta": True, "ip": "rnprmtfo-90", "detalhe": "12 meses grátis + YT Premium 1 mês; cartão Mastercard-8753"}}
for i, (email, n) in enumerate(zip(CONTAS, IPS)):
    if email in res:
        continue
    reg = json.load(open(cofre.REGISTRO, encoding="utf-8")); c = reg.get("contas", reg)
    if email not in c:
        L(f"{email}: não está no cofre — pulo"); continue
    if c[email].get("kaggle_proxy") and c[email]["kaggle_proxy"] != f"rnprmtfo-{n}":
        L(f"{email}: já tem IP fixo {c[email]['kaggle_proxy']} — uso o dele")
    else:
        c[email]["kaggle_proxy"] = f"rnprmtfo-{n}"
        c[email]["_ip_fixo_obs"] = f"17/11 dona (oferta AI Ultra): IP fixo próprio rnprmtfo-{n}, nunca usado por outra conta"
        json.dump(reg, open(cofre.REGISTRO, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    r = {"ip": c[email]["kaggle_proxy"]}
    proc = None
    if cofre._cdp_vivo(c[email]["porta"]):  # 17/11: Chrome aberto (dona usando) — não entra junto
        L(f"{email}: Chrome já aberto (em uso) — pulo"); continue
    try:
        porta, proc = cofre.abrir(email, "https://api.ipify.org", visivel=False)
        with sync_playwright() as p:
            br = p.chromium.connect_over_cdp(f"http://127.0.0.1:{porta}")
            pg = br.contexts[0].pages[0] if br.contexts[0].pages else br.contexts[0].new_page()
            time.sleep(6)
            r["ip_visto"] = pg.evaluate("() => document.body.innerText").strip()[:40]
            if r["ip_visto"].startswith("191.36."):
                r["erro"] = "saiu pela CASA — abortado"; L(f"{email}: SAIU PELA CASA — parei"); res[email] = r
                json.dump(res, open(SAIDA, "w", encoding="utf-8"), ensure_ascii=False, indent=1); break
            pg.goto(LINK, wait_until="domcontentloaded", timeout=90000); time.sleep(15)
            t = pg.evaluate("() => document.body.innerText")
            r["url"] = pg.url[:80]
            if "teste gratuito de 12 meses" in t:
                r["oferta"] = True
                m = re.search(r"(Mastercard|Visa|Elo|American Express|Amex)[-\s]?\d{4}", t)
                r["cartao"] = m.group(0) if m else "sem cartão salvo"
            elif "Ocorreu um erro no nosso sistema" in t or "Something went wrong" in t:
                r["oferta"] = None; r["detalhe"] = "erro do Google na página (não é 'sem oferta') — tentar de novo depois"
            elif "accounts.google.com" in pg.url or "Fazer login" in t or "Sign in" in t:
                r["oferta"] = None; r["detalhe"] = "não logada / pediu login"
            else:
                r["oferta"] = False; r["detalhe"] = re.sub(r"\s+", " ", t)[:200]
            try:
                br.new_browser_cdp_session().send("Browser.close")
            except Exception:
                pass
    except Exception as e:
        r["erro"] = f"{type(e).__name__}: {str(e)[:150]}"
    res[email] = r
    json.dump(res, open(SAIDA, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    L(f"{email}: {r}")
    if i < len(CONTAS) - 1:
        time.sleep(60)  # dona 17/11: 1 min entre contas
L("FIM")
