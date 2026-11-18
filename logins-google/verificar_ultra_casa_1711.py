"""17/11 dona ("se não tem canal e não tem Kaggle não tem problema, pode fazer com qualquer IP"): contas SEM canal e SEM
Kaggle, pela CASA (1 IP estável — melhor que proxy grátis rotativo), UMA a cada 20 min, só LÊ a página da oferta
(nunca clica em Assinar), fecha o Chrome. Pula conta com Chrome já aberto (em uso pelo sistema)."""
import json, re, sys, time
sys.path.insert(0, r"D:\logins-google")
import cofre
from playwright.sync_api import sync_playwright
LINK = open(r"C:\Users\Haylla\AppData\Local\Temp\ultra_link.txt").read().strip()
CONTAS = ["entrevistacomia", "fabiovideoseducativos", "fabricadeautomacoes0", "fabricadeautomacoesia", "filmescomia1",
          "gameoftroneskingsroadbrasil", "inovaremanhwaverseesp", "inovaremultiatendimento", "jogoscomia", "jornalcomia",
          "mentoriaiapro", "msenergypara", "solarmundo195", "inovaremanhwaverse4", "emersonjosiel2028",
          "inovaremanhwaverse3", "revolutionemerson7", "vendeafiliados3", "emersonjosielmrx1995", "emersonjosiel03"]
SAIDA = r"D:\logins-google\ultra_resultado_1711.json"
LOG = open(r"D:\logins-google\ultra_1711.log", "a", encoding="utf-8")
def L(m):
    m = f"[{time.strftime('%H:%M:%S')}] [casa] {m}"; print(m, flush=True); LOG.write(m + "\n"); LOG.flush()
for i, nome in enumerate(CONTAS):
    email = nome + "@gmail.com"
    try:
        res = json.load(open(SAIDA, encoding="utf-8"))
    except Exception:
        res = {}
    if email in res:
        continue
    if cofre.saida_kaggle(email):
        L(f"{email}: virou conta do Kaggle — pulo"); continue
    r = {"ip": "casa"}
    try:
        _e, d = cofre.conta(email)
        if cofre._cdp_vivo(d["porta"]):
            r["oferta"] = None; r["detalhe"] = "Chrome em uso pelo sistema — deixei pra depois"
        else:
            porta, proc = cofre.abrir(email, "about:blank", visivel=False)
            with sync_playwright() as p:
                br = p.chromium.connect_over_cdp(f"http://127.0.0.1:{porta}")
                pg = br.contexts[0].pages[0] if br.contexts[0].pages else br.contexts[0].new_page()
                pg.goto(LINK, wait_until="domcontentloaded", timeout=90000); time.sleep(15)
                t = pg.evaluate("() => document.body.innerText")
                if "teste gratuito de 12 meses" in t:
                    r["oferta"] = True
                    m = re.search(r"(Mastercard|Visa|Elo|American Express|Amex)[-\s]?\d{4}", t)
                    r["cartao"] = m.group(0) if m else "sem cartão salvo"
                elif "Ocorreu um erro no nosso sistema" in t or "Something went wrong" in t:
                    r["oferta"] = None; r["detalhe"] = "erro do Google na página — tentar depois"
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
    try:
        res = json.load(open(SAIDA, encoding="utf-8"))
    except Exception:
        res = {}
    res[email] = r
    json.dump(res, open(SAIDA, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    L(f"{email}: {r}")
    if i < len(CONTAS) - 1:
        time.sleep(60)  # dona 17/11: 1 min entre contas
L("FIM")
