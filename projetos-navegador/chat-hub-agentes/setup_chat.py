"""
Chat Hub Agentes — automação COMPLETA do Google Chat (coordenação entre agentes).

Operações disponíveis:
  - verificar_acesso(conta)             → confirma acesso ao Chat
  - criar_espaco(conta, nome)           → cria espaço/sala
  - listar_espacos(conta)               → lista espaços disponíveis
  - enviar_mensagem(conta, alvo, texto) → envia mensagem num espaço/DM
  - ler_mensagens(conta, espaco)        → lê mensagens recentes
  - adicionar_membro(conta, esp, email) → adiciona membro ao espaço
  - criar_webhook(conta, espaco)        → cria webhook de entrada (incoming)
  - enviar_via_webhook(url, texto)      → posta mensagem via webhook (sem browser)
  - setup_espacos_padrao(conta)         → cria Inovare-Pipeline/Alertas/Logs

CLI:
  python setup_chat.py                                 → dry run
  python setup_chat.py --live
  python setup_chat.py --acao enviar --conta X --alvo "Inovare-Logs" --texto "oi"
  python setup_chat.py --acao ler --conta X --espaco "Inovare-Alertas"
  python setup_chat.py --acao webhook_send --url https://chat.googleapis.com/... --texto "alerta"
"""
import json
import sys
import time
import urllib.request
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "shared"))
from google_session import ACCOUNTS, google_browser, save_session

CHAT_DIR = Path(__file__).resolve().parent
STATUS_FILE = CHAT_DIR / "chat_status.json"
MESSAGES_LOG = CHAT_DIR / "messages.jsonl"
WEBHOOKS_FILE = CHAT_DIR / "webhooks.json"
CHAT_URL = "https://chat.google.com"
ESPACOS_PADRAO = ["Inovare-Pipeline", "Inovare-Alertas", "Inovare-Logs"]


def _sessao_expirada(page):
    return "accounts.google.com" in page.url


def _log(entrada):
    with open(MESSAGES_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(entrada, ensure_ascii=False) + "\n")


def verificar_acesso(conta):
    """Confirma acesso ao Google Chat."""
    try:
        with google_browser(conta) as (page, context, browser):
            page.goto(CHAT_URL, timeout=45000, wait_until="domcontentloaded")
            time.sleep(6)
            if _sessao_expirada(page):
                return {"conta": conta, "status": "sessao_expirada"}
            if "chat.google.com" in page.url or "mail.google.com/chat" in page.url:
                save_session(context, conta)
                return {"conta": conta, "status": "ok", "url": page.url}
            return {"conta": conta, "status": "redirect", "url": page.url}
    except Exception as e:
        return {"conta": conta, "status": "erro", "erro": str(e)}


def criar_espaco(conta, nome_espaco):
    """Cria um espaço/sala no Google Chat."""
    try:
        with google_browser(conta) as (page, context, browser):
            page.goto(CHAT_URL, timeout=45000, wait_until="domcontentloaded")
            time.sleep(6)
            if _sessao_expirada(page):
                return {"sucesso": False, "erro": "sessao_expirada"}

            create_btn = page.query_selector('button[aria-label*="Create"], button[aria-label*="New space"], button[aria-label*="Criar"], button[aria-label*="chat ou espaço"]')
            if create_btn:
                create_btn.click()
                time.sleep(2)
                esp_opt = page.query_selector('[role="menuitem"]:has-text("space"), [role="menuitem"]:has-text("espaço")')
                if esp_opt:
                    esp_opt.click()
                    time.sleep(2)
                name_input = page.query_selector('input[aria-label*="name"], input[aria-label*="nome"], input[type="text"]')
                if name_input:
                    name_input.fill(nome_espaco)
                    time.sleep(1)
                    ok = page.query_selector('button:has-text("Create"), button:has-text("Criar")')
                    if ok:
                        ok.click()
                        time.sleep(3)
                        save_session(context, conta)
                        _log({"ts": datetime.now(timezone.utc).isoformat(), "acao": "criar_espaco", "conta": conta, "espaco": nome_espaco})
                        return {"sucesso": True, "espaco": nome_espaco}
            return {"sucesso": False, "erro": "UI de criar espaço não encontrada"}
    except Exception as e:
        return {"sucesso": False, "erro": str(e)}


def listar_espacos(conta):
    """Lista espaços disponíveis."""
    try:
        with google_browser(conta) as (page, context, browser):
            page.goto(CHAT_URL, timeout=45000, wait_until="domcontentloaded")
            time.sleep(7)
            if _sessao_expirada(page):
                return {"conta": conta, "espacos": [], "erro": "sessao_expirada"}
            espacos = []
            for el in page.query_selector_all('[role="listitem"], [data-group-id], span[class*="space"]'):
                t = el.inner_text().strip().split("\n")[0]
                if t and len(t) < 80:
                    espacos.append(t)
            save_session(context, conta)
            return {"conta": conta, "espacos": list(dict.fromkeys(espacos))[:40]}
    except Exception as e:
        return {"conta": conta, "espacos": [], "erro": str(e)}


def _abrir_espaco(page, alvo):
    item = page.query_selector(f'[role="listitem"]:has-text("{alvo}"), span:has-text("{alvo}")')
    if item:
        item.click()
        time.sleep(3)
        return True
    return False


def enviar_mensagem(conta, alvo, texto):
    """Envia mensagem num espaço ou DM."""
    try:
        with google_browser(conta) as (page, context, browser):
            page.goto(CHAT_URL, timeout=45000, wait_until="domcontentloaded")
            time.sleep(6)
            if _sessao_expirada(page):
                return {"sucesso": False, "erro": "sessao_expirada"}

            _abrir_espaco(page, alvo)
            composer = page.query_selector('div[contenteditable="true"], textarea[aria-label*="message"], div[aria-label*="Send a message"], div[aria-label*="Enviar mensagem"]')
            if composer:
                composer.click()
                time.sleep(0.5)
                composer.type(texto, delay=25)
                time.sleep(0.5)
                page.keyboard.press("Enter")
                time.sleep(2)
                save_session(context, conta)
                _log({"ts": datetime.now(timezone.utc).isoformat(), "acao": "enviar", "conta": conta, "alvo": alvo, "texto": texto})
                return {"sucesso": True, "alvo": alvo}
            return {"sucesso": False, "erro": "composer não encontrado"}
    except Exception as e:
        return {"sucesso": False, "erro": str(e)}


def ler_mensagens(conta, espaco, max_msg=20):
    """Lê mensagens recentes de um espaço."""
    try:
        with google_browser(conta) as (page, context, browser):
            page.goto(CHAT_URL, timeout=45000, wait_until="domcontentloaded")
            time.sleep(6)
            if _sessao_expirada(page):
                return {"conta": conta, "mensagens": [], "erro": "sessao_expirada"}
            _abrir_espaco(page, espaco)
            mensagens = []
            for el in page.query_selector_all('[data-message-id], [role="listitem"] [class*="message"], div[class*="text-content"]')[-max_msg:]:
                t = el.inner_text().strip()
                if t and len(t) < 500:
                    mensagens.append(t)
            save_session(context, conta)
            return {"conta": conta, "espaco": espaco, "mensagens": mensagens}
    except Exception as e:
        return {"conta": conta, "mensagens": [], "erro": str(e)}


def adicionar_membro(conta, espaco, email):
    """Adiciona um membro ao espaço."""
    try:
        with google_browser(conta) as (page, context, browser):
            page.goto(CHAT_URL, timeout=45000, wait_until="domcontentloaded")
            time.sleep(6)
            if _sessao_expirada(page):
                return {"sucesso": False, "erro": "sessao_expirada"}
            _abrir_espaco(page, espaco)
            menu = page.query_selector('button[aria-label*="member"], button[aria-label*="membro"], button[aria-label*="Add people"]')
            if menu:
                menu.click()
                time.sleep(2)
                inp = page.query_selector('input[type="text"], input[aria-label*="people"]')
                if inp:
                    inp.fill(email)
                    time.sleep(1)
                    page.keyboard.press("Enter")
                    add = page.query_selector('button:has-text("Add"), button:has-text("Adicionar"), button:has-text("Send")')
                    if add:
                        add.click()
                        time.sleep(2)
                    save_session(context, conta)
                    return {"sucesso": True, "espaco": espaco, "email": email}
            return {"sucesso": False, "erro": "UI de membros não encontrada"}
    except Exception as e:
        return {"sucesso": False, "erro": str(e)}


def criar_webhook(conta, espaco):
    """Cria webhook de entrada num espaço (guarda a URL localmente)."""
    try:
        with google_browser(conta) as (page, context, browser):
            page.goto(CHAT_URL, timeout=45000, wait_until="domcontentloaded")
            time.sleep(6)
            if _sessao_expirada(page):
                return {"sucesso": False, "erro": "sessao_expirada"}
            _abrir_espaco(page, espaco)
            menu = page.query_selector('button[aria-label*="settings"], button[aria-label*="Apps"], button[aria-label*="webhook"]')
            if menu:
                menu.click()
                time.sleep(2)
                wh = page.query_selector(':has-text("Webhook"), :has-text("Manage webhooks")')
                if wh:
                    wh.click()
                    time.sleep(2)
                    url_el = page.query_selector('input[readonly], code')
                    url = url_el.get_attribute("value") if url_el else ""
                    if url:
                        webhooks = {}
                        if WEBHOOKS_FILE.exists():
                            webhooks = json.loads(WEBHOOKS_FILE.read_text(encoding="utf-8"))
                        webhooks[f"{conta}_{espaco}"] = url
                        WEBHOOKS_FILE.write_text(json.dumps(webhooks, indent=2), encoding="utf-8")
                        save_session(context, conta)
                        return {"sucesso": True, "espaco": espaco, "webhook_salvo": True}
            save_session(context, conta)
            return {"sucesso": False, "erro": "UI de webhook não encontrada (precisa criar manualmente 1x)"}
    except Exception as e:
        return {"sucesso": False, "erro": str(e)}


def enviar_via_webhook(url_webhook, texto):
    """Posta mensagem via webhook — não precisa de browser/sessão."""
    payload = json.dumps({"text": texto}).encode("utf-8")
    req = urllib.request.Request(url_webhook, data=payload, method="POST")
    req.add_header("Content-Type", "application/json; charset=UTF-8")
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            _log({"ts": datetime.now(timezone.utc).isoformat(), "acao": "webhook", "texto": texto})
            return {"sucesso": True, "http": resp.status}
    except Exception as e:
        return {"sucesso": False, "erro": str(e)}


def setup_espacos_padrao(conta):
    """Cria os espaços Inovare padrão."""
    resultados = []
    for esp in ESPACOS_PADRAO:
        r = criar_espaco(conta, esp)
        resultados.append({"espaco": esp, "sucesso": r.get("sucesso", False)})
        if r.get("erro") == "sessao_expirada":
            break
    return {"conta": conta, "resultados": resultados}


FUNCIONALIDADES = {
    "verificar":     {"func": verificar_acesso,   "desc": "Confirma acesso ao Chat"},
    "criar_espaco":  {"func": criar_espaco,       "desc": "Cria espaço/sala"},
    "listar":        {"func": listar_espacos,     "desc": "Lista espaços"},
    "enviar":        {"func": enviar_mensagem,    "desc": "Envia mensagem"},
    "ler":           {"func": ler_mensagens,      "desc": "Lê mensagens recentes"},
    "membro":        {"func": adicionar_membro,   "desc": "Adiciona membro"},
    "webhook":       {"func": criar_webhook,      "desc": "Cria webhook de entrada"},
    "webhook_send":  {"func": enviar_via_webhook, "desc": "Posta via webhook (sem browser)"},
    "padrao":        {"func": setup_espacos_padrao,"desc": "Cria espaços Inovare padrão"},
}


def setup_chat_hub(dry_run=True):
    print(f"[Chat Hub Agentes] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Funcionalidades: {', '.join(FUNCIONALIDADES.keys())}")
    status = {"espacos_padrao": ESPACOS_PADRAO, "contas": {}, "ultima_execucao": datetime.now(timezone.utc).isoformat()}
    for conta in ACCOUNTS:
        if dry_run:
            print(f"  [DRY RUN] verificaria Chat: {conta}")
            status["contas"][conta] = {"dry_run": True}
        else:
            print(f"  {conta}...", end=" ", flush=True)
            r = verificar_acesso(conta)
            print(r["status"])
            status["contas"][conta] = r
    STATUS_FILE.write_text(json.dumps(status, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nStatus salvo em {STATUS_FILE}")
    return status


if __name__ == "__main__":
    args = sys.argv[1:]
    if "--acao" in args:
        acao = args[args.index("--acao") + 1]
        conta = args[args.index("--conta") + 1] if "--conta" in args else "fabrica"
        if acao == "verificar":
            r = verificar_acesso(conta)
        elif acao == "criar_espaco":
            r = criar_espaco(conta, args[args.index("--nome") + 1])
        elif acao == "listar":
            r = listar_espacos(conta)
        elif acao == "enviar":
            r = enviar_mensagem(conta, args[args.index("--alvo") + 1], args[args.index("--texto") + 1])
        elif acao == "ler":
            r = ler_mensagens(conta, args[args.index("--espaco") + 1])
        elif acao == "membro":
            r = adicionar_membro(conta, args[args.index("--espaco") + 1], args[args.index("--email") + 1])
        elif acao == "webhook":
            r = criar_webhook(conta, args[args.index("--espaco") + 1])
        elif acao == "webhook_send":
            r = enviar_via_webhook(args[args.index("--url") + 1], args[args.index("--texto") + 1])
        elif acao == "padrao":
            r = setup_espacos_padrao(conta)
        else:
            r = {"erro": f"ação desconhecida: {acao}"}
        print(json.dumps(r, indent=2, ensure_ascii=False))
    else:
        dry = "--live" not in args
        if dry:
            print("Modo DRY RUN\n")
        setup_chat_hub(dry_run=dry)
