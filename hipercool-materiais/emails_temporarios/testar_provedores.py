r"""testar_provedores.py — testa, pelo proxy GRÁTIS rotativo do Webshare (nunca pela casa), quais serviços de
e-mail temporário deixam (1) criar/obter uma caixa e (2) listar as mensagens dela por HTTP, sem navegador.

Não toca em conta nenhuma (Kaggle/Google/etc.). Resultado em resultado_api.json + impresso.

    python testar_provedores.py                 # testa todos
    python testar_provedores.py mailtm dropmail # só esses
    python testar_provedores.py ler <prov> <estado.json>  # lê de novo a caixa criada antes (teste de chegada)
"""
import json
import random
import string
import sys
import time
import traceback
from datetime import datetime
from pathlib import Path

import requests

DIR = Path(__file__).resolve().parent
PROXIES = Path(r"D:\postador-de-videos\secrets\proxies.txt")
SAIDA = DIR / "resultado_api.json"
CAIXAS = DIR / "caixas"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0 Safari/537.36"


def proxy_gratis():
    """Proxy rotativo de uma conta grátis do Webshare (sem conta nenhuma atrás). Nunca devolve None: sem proxy = erro."""
    linhas = [x.strip() for x in PROXIES.read_text(encoding="utf-8").splitlines()
              if "-rotate:" in x and not x.strip().startswith("#")]
    try:  # só as contas com banda segundo o webshare_saude (402 = sem banda no mês)
        ok = {c["conta"] for c in json.loads(Path(r"D:\video-fila\estado\webshare.json").read_text(encoding="utf-8"))
              ["contas"] if c["estado"] == "ok"}
        linhas = [x for x in linhas if x.split("//", 1)[-1].split("-rotate", 1)[0] in ok] or linhas
    except (OSError, ValueError, KeyError):
        pass
    if not linhas:
        raise RuntimeError("sem proxy rotativo no cofre — não testo pela casa")
    p = random.choice(linhas)
    p = p if p.startswith("http") else "http://" + p
    return {"http": p, "https": p}


def sessao():
    """Sessão por uma conta grátis do Webshare que tem banda AGORA (testa com ~1 KB; 402 = sem banda, troca)."""
    for _ in range(8):
        s = requests.Session()
        s.headers["User-Agent"] = UA
        s.proxies = proxy_gratis()
        s.trust_env = False
        try:
            s.get("http://ipv4.webshare.io/", timeout=15).raise_for_status()
            return s
        except Exception:  # noqa: BLE001
            continue
    raise RuntimeError("nenhuma conta grátis do Webshare com banda agora — não testo pela casa")


def nome(n=10):
    return "".join(random.choices(string.ascii_lowercase, k=1)) + "".join(
        random.choices(string.ascii_lowercase + string.digits, k=n - 1))


# Cada provedor: criar(s) -> dict estado (com "email"); ler(s, estado) -> lista [{de, assunto, id}]
# ---------------------------------------------------------------------------------------------------------
def _mailtm_like(base):
    def criar(s):
        doms = s.get(f"{base}/domains", timeout=25).json()
        doms = doms.get("hydra:member", doms) if isinstance(doms, dict) else doms
        dom = doms[0]["domain"]
        email, senha = f"{nome()}@{dom}", nome(14)
        r = s.post(f"{base}/accounts", json={"address": email, "password": senha}, timeout=25)
        r.raise_for_status()
        tok = s.post(f"{base}/token", json={"address": email, "password": senha}, timeout=25).json()["token"]
        return {"email": email, "senha": senha, "token": tok, "dominios": [d["domain"] for d in doms]}

    def ler(s, st):
        r = s.get(f"{base}/messages", headers={"Authorization": f"Bearer {st['token']}"}, timeout=25).json()
        msgs = r.get("hydra:member", r) if isinstance(r, dict) else r
        return [{"de": m["from"]["address"], "assunto": m.get("subject"), "id": m["id"]} for m in msgs]
    return criar, ler


def guerrilla_criar(s):
    r = s.get("https://api.guerrillamail.com/ajax.php", params={"f": "get_email_address", "lang": "en"}, timeout=25).json()
    return {"email": r["email_addr"], "sid": r["sid_token"]}


def guerrilla_ler(s, st):
    r = s.get("https://api.guerrillamail.com/ajax.php",
              params={"f": "get_email_list", "offset": 0, "sid_token": st["sid"]}, timeout=25).json()
    return [{"de": m["mail_from"], "assunto": m["mail_subject"], "id": m["mail_id"]} for m in r.get("list", [])
            if "guerrillamail" not in m.get("mail_from", "").lower() or "welcome" not in m.get("mail_subject", "").lower()]


def tmlol_criar(s):
    r = s.post("https://api.tempmail.lol/v2/inbox/create", json={}, timeout=25).json()
    return {"email": r["address"], "token": r["token"]}


def tmlol_ler(s, st):
    r = s.get("https://api.tempmail.lol/v2/inbox", params={"token": st["token"]}, timeout=25).json()
    if r.get("expired"):
        raise RuntimeError("caixa expirou")
    return [{"de": m.get("from"), "assunto": m.get("subject"), "id": m.get("_id") or m.get("date")}
            for m in r.get("emails", [])]


DROP = "https://dropmail.me/api/graphql/"


def dropmail_criar(s):
    tok = "web-test-" + nome(12)
    q = "mutation {introduceSession {id, expiresAt, addresses {address}}}"
    r = s.post(DROP + tok, json={"query": q}, timeout=25).json()
    if "data" not in r:
        raise RuntimeError(f"dropmail recusou: {str(r)[:200]}")
    ses = r["data"]["introduceSession"]
    return {"email": ses["addresses"][0]["address"], "sid": ses["id"], "tok": tok}


def dropmail_ler(s, st):
    q = 'query ($id: ID!) {session(id:$id) { mails { fromAddr, headerSubject, id } } }'
    r = s.post(DROP + st["tok"], json={"query": q, "variables": {"id": st["sid"]}}, timeout=25).json()
    ses = (r.get("data") or {}).get("session")
    if ses is None:
        raise RuntimeError(f"sessão sumiu: {str(r)[:150]}")
    return [{"de": m["fromAddr"], "assunto": m["headerSubject"], "id": m["id"]} for m in ses["mails"]]


def maildrop_criar(s):
    caixa = nome(12)
    r = s.post("https://api.maildrop.cc/graphql", json={"query": f'query {{ inbox(mailbox:"{caixa}") {{ id }} }}'},
               timeout=25)
    r.raise_for_status()
    if "errors" in r.json():
        raise RuntimeError(str(r.json())[:200])
    return {"email": f"{caixa}@maildrop.cc", "caixa": caixa}


def maildrop_ler(s, st):
    q = f'query {{ inbox(mailbox:"{st["caixa"]}") {{ id headerfrom subject }} }}'
    r = s.post("https://api.maildrop.cc/graphql", json={"query": q}, timeout=25).json()
    return [{"de": m["headerfrom"], "assunto": m["subject"], "id": m["id"]} for m in r["data"]["inbox"]]


def secmail_criar(s):
    r = s.get("https://www.1secmail.com/api/v1/", params={"action": "genRandomMailbox", "count": 1}, timeout=25)
    r.raise_for_status()
    return {"email": r.json()[0]}


def secmail_ler(s, st):
    u, d = st["email"].split("@")
    r = s.get("https://www.1secmail.com/api/v1/", params={"action": "getMessages", "login": u, "domain": d}, timeout=25)
    r.raise_for_status()
    return [{"de": m["from"], "assunto": m["subject"], "id": m["id"]} for m in r.json()]


def tmplus_criar(s):
    caixa = nome(12)
    r = s.get("https://tempmail.plus/api/mails", params={"email": f"{caixa}@mailto.plus", "limit": 5}, timeout=25)
    r.raise_for_status()
    r.json()
    return {"email": f"{caixa}@mailto.plus"}


def tmplus_ler(s, st):
    r = s.get("https://tempmail.plus/api/mails", params={"email": st["email"], "limit": 20}, timeout=25).json()
    return [{"de": m.get("from_mail"), "assunto": m.get("subject"), "id": m.get("mail_id")} for m in r.get("mail_list", [])]


def tmio_criar(s):
    r = s.post("https://api.internal.temp-mail.io/api/v3/email/new", json={"min_name_length": 10, "max_name_length": 10},
               timeout=25)
    r.raise_for_status()
    j = r.json()
    return {"email": j["email"], "token": j.get("token")}


def tmio_ler(s, st):
    r = s.get(f"https://api.internal.temp-mail.io/api/v3/email/{st['email']}/messages", timeout=25)
    r.raise_for_status()
    return [{"de": m.get("from"), "assunto": m.get("subject"), "id": m.get("id")} for m in r.json()]


def mailnesia_criar(s):
    caixa = nome(12)
    r = s.get(f"https://mailnesia.com/mailbox/{caixa}", timeout=25)
    r.raise_for_status()
    return {"email": f"{caixa}@mailnesia.com", "caixa": caixa}


def mailnesia_ler(s, st):
    import re
    html = s.get(f"https://mailnesia.com/mailbox/{st['caixa']}", timeout=25).text
    ids = re.findall(r'id="(\d+)" class="emailheader"', html) or re.findall(r'/mailbox/[^/]+/(\d+)', html)
    return [{"de": "?", "assunto": "?", "id": i} for i in dict.fromkeys(ids)]


def kitten_criar(s):
    caixa = nome(12)
    r = s.get("https://inboxkitten.com/api/v1/mail/list", params={"recipient": caixa}, timeout=25)
    r.raise_for_status()
    r.json()
    return {"email": f"{caixa}@inboxkitten.com", "caixa": caixa}


def kitten_ler(s, st):
    r = s.get("https://inboxkitten.com/api/v1/mail/list", params={"recipient": st["caixa"]}, timeout=25).json()
    return [{"de": m["message"]["headers"].get("from"), "assunto": m["message"]["headers"].get("subject"),
             "id": m["storage"]["key"]} for m in r]


def harakiri_criar(s):
    caixa = nome(12)
    r = s.get(f"https://harakirimail.com/api/v1/inbox/{caixa}", timeout=25)
    r.raise_for_status()
    r.json()
    return {"email": f"{caixa}@harakirimail.com", "caixa": caixa}


def harakiri_ler(s, st):
    r = s.get(f"https://harakirimail.com/api/v1/inbox/{st['caixa']}", timeout=25).json()
    return [{"de": m.get("from"), "assunto": m.get("subject"), "id": m.get("_id")} for m in r.get("emails", [])]


def mailinator_criar(s):
    caixa = nome(12)
    r = s.get("https://www.mailinator.com/api/v2/domains/public/inboxes/" + caixa, timeout=25)
    r.raise_for_status()
    r.json()
    return {"email": f"{caixa}@mailinator.com", "caixa": caixa}


def mailinator_ler(s, st):
    r = s.get("https://www.mailinator.com/api/v2/domains/public/inboxes/" + st["caixa"], timeout=25).json()
    return [{"de": m.get("from"), "assunto": m.get("subject"), "id": m.get("id")} for m in r.get("msgs", [])]


def devmail_criar(s):
    r = s.put("https://www.developermail.com/api/v1/mailbox", timeout=25).json()
    if not r.get("success"):
        raise RuntimeError(str(r)[:200])
    return {"email": r["result"]["name"] + "@developermail.com", "nome": r["result"]["name"], "tok": r["result"]["token"]}


def devmail_ler(s, st):
    r = s.get(f"https://www.developermail.com/api/v1/mailbox/{st['nome']}",
              headers={"X-MailboxToken": st["tok"]}, timeout=25).json()
    return [{"de": "?", "assunto": "?", "id": i} for i in (r.get("result") or [])]


def yop_criar(s):
    caixa = nome(12)
    r = s.get(f"https://yopmail.com/en/?login={caixa}", timeout=25)
    r.raise_for_status()
    return {"email": f"{caixa}@yopmail.com", "caixa": caixa, "obs": "leitura exige cookie yp/yj do JS (sem API)"}


def yop_ler(s, st):
    raise RuntimeError("yopmail não tem API: a lista vem de inbox?login=..&yp=..&yj=.. com tokens do JS + captcha")


PROVEDORES = {
    "mailtm": (*_mailtm_like("https://api.mail.tm"),),
    "mailgw": (*_mailtm_like("https://api.mail.gw"),),
    "guerrilla": (guerrilla_criar, guerrilla_ler),
    "tempmaillol": (tmlol_criar, tmlol_ler),
    "dropmail": (dropmail_criar, dropmail_ler),
    "maildrop": (maildrop_criar, maildrop_ler),
    "1secmail": (secmail_criar, secmail_ler),
    "tempmailplus": (tmplus_criar, tmplus_ler),
    "tempmailio": (tmio_criar, tmio_ler),
    "mailnesia": (mailnesia_criar, mailnesia_ler),
    "inboxkitten": (kitten_criar, kitten_ler),
    "harakiri": (harakiri_criar, harakiri_ler),
    "mailinator": (mailinator_criar, mailinator_ler),
    "developermail": (devmail_criar, devmail_ler),
    "yopmail": (yop_criar, yop_ler),
}


def testar(nome_p):
    criar, ler = PROVEDORES[nome_p]
    res = {"provedor": nome_p, "em": datetime.now().isoformat(timespec="seconds")}
    for tentativa in range(5):  # proxy grátis cai (402 sem banda / 502): tenta com outra conta do Webshare
        s = sessao()
        try:
            t0 = time.time()
            st = criar(s)
            res.pop("erro", None)
            res.update(criar_ok=True, email=st["email"], seg_criar=round(time.time() - t0, 1), tentativas=tentativa + 1)
            CAIXAS.mkdir(exist_ok=True)
            (CAIXAS / f"{nome_p}.json").write_text(json.dumps(st, ensure_ascii=False), encoding="utf-8")
            try:
                msgs = ler(s, st)
                res.update(ler_ok=True, mensagens=len(msgs))
            except Exception as e:  # noqa: BLE001
                res.update(ler_ok=False, erro_ler=f"{type(e).__name__}: {str(e)[:200]}")
            return res
        except Exception as e:  # noqa: BLE001
            res.update(criar_ok=False, erro=f"{type(e).__name__}: {str(e)[:200]}")
            if not isinstance(e, requests.exceptions.ProxyError):
                break  # erro do serviço (não do proxy): não adianta trocar de IP
    return res


def ler_de_novo(nome_p, arq=None):
    st = json.loads(Path(arq or CAIXAS / f"{nome_p}.json").read_text(encoding="utf-8"))
    return {"provedor": nome_p, "email": st["email"], "mensagens": PROVEDORES[nome_p][1](sessao(), st)}


if __name__ == "__main__":
    a = sys.argv[1:]
    if a[:1] == ["ler"]:
        print(json.dumps(ler_de_novo(a[1], a[2] if len(a) > 2 else None), ensure_ascii=False, indent=1))
        sys.exit(0)
    alvos = a or list(PROVEDORES)
    todos = json.loads(SAIDA.read_text(encoding="utf-8")) if SAIDA.exists() else {}
    for p in alvos:
        r = testar(p)
        todos[p] = r
        print(f"{p:14} criar={'OK' if r.get('criar_ok') else 'X':2} ler={'OK' if r.get('ler_ok') else 'X':2} "
              f"{r.get('email', '')} {r.get('erro', '') or r.get('erro_ler', '')}", flush=True)
    SAIDA.write_text(json.dumps(todos, ensure_ascii=False, indent=1), encoding="utf-8")
