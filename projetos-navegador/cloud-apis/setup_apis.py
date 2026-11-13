"""
Cloud APIs — automação COMPLETA de APIs GCP gratuitas.

Operações disponíveis:
  - habilitar_api(conta, api)      → ativa uma API no console GCP
  - desabilitar_api(conta, api)    → desativa uma API
  - status_api(conta, api)         → verifica se está ativa
  - listar_habilitadas(conta)      → lista APIs ativas na conta
  - ver_quota(conta, api)          → mostra uso/quota da API
  - habilitar_todas(conta)         → ativa todas as APIs gratuitas do catálogo
  - escanear_todas()               → status de todas as APIs em todas as contas

CLI:
  python setup_apis.py                                → dry run
  python setup_apis.py --live
  python setup_apis.py --acao habilitar --conta X --api youtube
  python setup_apis.py --acao listar --conta X
  python setup_apis.py --acao status --conta X --api gemini
"""
import json
import sys
import time
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "shared"))
from google_session import ACCOUNTS, google_browser, save_session

APIS_DIR = Path(__file__).resolve().parent
STATUS_FILE = APIS_DIR / "apis_status.json"
CONSOLE_LIB = "https://console.cloud.google.com/apis/library/{id}"
CONSOLE_ENABLED = "https://console.cloud.google.com/apis/dashboard"
CONSOLE_QUOTA = "https://console.cloud.google.com/apis/api/{id}/quotas"

CATALOGO_APIS = {
    "gemini":      {"nome": "Gemini API (AI Studio)", "id": "generativelanguage.googleapis.com"},
    "youtube":     {"nome": "YouTube Data API v3", "id": "youtube.googleapis.com"},
    "sheets":      {"nome": "Google Sheets API", "id": "sheets.googleapis.com"},
    "drive":       {"nome": "Google Drive API", "id": "drive.googleapis.com"},
    "gmail":       {"nome": "Gmail API", "id": "gmail.googleapis.com"},
    "calendar":    {"nome": "Google Calendar API", "id": "calendar-json.googleapis.com"},
    "chat":        {"nome": "Google Chat API", "id": "chat.googleapis.com"},
    "vision":      {"nome": "Cloud Vision API", "id": "vision.googleapis.com"},
    "translate":   {"nome": "Cloud Translation API", "id": "translate.googleapis.com"},
    "blogger":     {"nome": "Blogger API v3", "id": "blogger.googleapis.com"},
    "docs":        {"nome": "Google Docs API", "id": "docs.googleapis.com"},
    "slides":      {"nome": "Google Slides API", "id": "slides.googleapis.com"},
    "tts":         {"nome": "Cloud Text-to-Speech", "id": "texttospeech.googleapis.com"},
    "speech":      {"nome": "Cloud Speech-to-Text", "id": "speech.googleapis.com"},
}


def _sessao_expirada(page):
    return "accounts.google.com" in page.url


def _resolver_api(api):
    if api in CATALOGO_APIS:
        return CATALOGO_APIS[api]
    for k, v in CATALOGO_APIS.items():
        if api.lower() in v["nome"].lower() or api == v["id"]:
            return v
    return {"nome": api, "id": api}


def habilitar_api(conta, api):
    """Ativa uma API no console GCP."""
    info = _resolver_api(api)
    try:
        with google_browser(conta) as (page, context, browser):
            page.goto(CONSOLE_LIB.format(id=info["id"]), timeout=45000, wait_until="domcontentloaded")
            time.sleep(6)
            if _sessao_expirada(page):
                return {"api": info["nome"], "status": "sessao_expirada"}

            enable_btn = page.query_selector('button:has-text("Enable"), button:has-text("Ativar")')
            if enable_btn and enable_btn.is_visible():
                enable_btn.click()
                time.sleep(12)
                save_session(context, conta)
                return {"api": info["nome"], "status": "habilitada", "conta": conta}

            manage = page.query_selector('button:has-text("Manage"), button:has-text("Gerenciar"), :has-text("API enabled")')
            if manage:
                save_session(context, conta)
                return {"api": info["nome"], "status": "ja_habilitada", "conta": conta}

            save_session(context, conta)
            return {"api": info["nome"], "status": "indefinido", "conta": conta}
    except Exception as e:
        return {"api": info["nome"], "status": "erro", "erro": str(e)}


def desabilitar_api(conta, api):
    """Desativa uma API."""
    info = _resolver_api(api)
    try:
        with google_browser(conta) as (page, context, browser):
            page.goto(CONSOLE_LIB.format(id=info["id"]), timeout=45000, wait_until="domcontentloaded")
            time.sleep(6)
            if _sessao_expirada(page):
                return {"api": info["nome"], "status": "sessao_expirada"}

            manage = page.query_selector('button:has-text("Manage"), button:has-text("Gerenciar")')
            if manage:
                manage.click()
                time.sleep(4)
                disable = page.query_selector('button:has-text("Disable API"), button:has-text("Desativar API")')
                if disable:
                    disable.click()
                    time.sleep(2)
                    confirm = page.query_selector('button:has-text("Disable"), button:has-text("Desativar")')
                    if confirm:
                        confirm.click()
                        time.sleep(3)
                    save_session(context, conta)
                    return {"api": info["nome"], "status": "desabilitada", "conta": conta}
            save_session(context, conta)
            return {"api": info["nome"], "status": "nao_estava_ativa", "conta": conta}
    except Exception as e:
        return {"api": info["nome"], "status": "erro", "erro": str(e)}


def status_api(conta, api):
    """Verifica se uma API está ativa."""
    info = _resolver_api(api)
    try:
        with google_browser(conta) as (page, context, browser):
            page.goto(CONSOLE_LIB.format(id=info["id"]), timeout=45000, wait_until="domcontentloaded")
            time.sleep(6)
            if _sessao_expirada(page):
                return {"api": info["nome"], "status": "sessao_expirada"}

            if page.query_selector('button:has-text("Manage"), button:has-text("Gerenciar"), :has-text("API enabled")'):
                st = "ativa"
            elif page.query_selector('button:has-text("Enable"), button:has-text("Ativar")'):
                st = "inativa"
            else:
                st = "indefinido"
            save_session(context, conta)
            return {"api": info["nome"], "status": st, "conta": conta}
    except Exception as e:
        return {"api": info["nome"], "status": "erro", "erro": str(e)}


def listar_habilitadas(conta):
    """Lista APIs ativas na conta (dashboard)."""
    try:
        with google_browser(conta) as (page, context, browser):
            page.goto(CONSOLE_ENABLED, timeout=45000, wait_until="domcontentloaded")
            time.sleep(7)
            if _sessao_expirada(page):
                return {"conta": conta, "apis": [], "erro": "sessao_expirada"}

            apis = []
            for row in page.query_selector_all('[role="row"], tr, a[href*="/apis/api/"]'):
                txt = row.inner_text().strip().split("\n")[0]
                if txt and "API" in txt and len(txt) < 120:
                    apis.append(txt)
            save_session(context, conta)
            apis = list(dict.fromkeys(apis))
            return {"conta": conta, "apis": apis, "total": len(apis)}
    except Exception as e:
        return {"conta": conta, "apis": [], "erro": str(e)}


def ver_quota(conta, api):
    """Mostra uso/quota de uma API."""
    info = _resolver_api(api)
    try:
        with google_browser(conta) as (page, context, browser):
            page.goto(CONSOLE_QUOTA.format(id=info["id"]), timeout=45000, wait_until="domcontentloaded")
            time.sleep(7)
            if _sessao_expirada(page):
                return {"api": info["nome"], "erro": "sessao_expirada"}

            quotas = []
            for row in page.query_selector_all('[role="row"], tr'):
                txt = row.inner_text().strip()
                if txt and ("%" in txt or "quota" in txt.lower() or "limit" in txt.lower()):
                    quotas.append(txt[:150])
            save_session(context, conta)
            return {"api": info["nome"], "conta": conta, "quotas": quotas[:20]}
    except Exception as e:
        return {"api": info["nome"], "erro": str(e)}


def habilitar_todas(conta):
    """Ativa todas as APIs do catálogo numa conta."""
    resultados = []
    for chave, info in CATALOGO_APIS.items():
        r = habilitar_api(conta, chave)
        resultados.append({"api": chave, "status": r.get("status")})
        if r.get("status") == "sessao_expirada":
            break
    return {"conta": conta, "resultados": resultados}


def escanear_todas():
    """Status resumido de APIs em todas as contas."""
    print(f"[Cloud APIs] {datetime.now().strftime('%H:%M:%S')}")
    resultados = {}
    for conta in ACCOUNTS:
        print(f"  {conta}...", end=" ", flush=True)
        r = listar_habilitadas(conta)
        print(f"{r.get('total', 0)} APIs" if "total" in r else r.get("erro", "?"))
        resultados[conta] = r
    return resultados


FUNCIONALIDADES = {
    "habilitar":    {"func": habilitar_api,    "desc": "Ativa uma API"},
    "desabilitar":  {"func": desabilitar_api,  "desc": "Desativa uma API"},
    "status":       {"func": status_api,       "desc": "Verifica se API está ativa"},
    "listar":       {"func": listar_habilitadas,"desc": "Lista APIs ativas na conta"},
    "quota":        {"func": ver_quota,         "desc": "Mostra uso/quota da API"},
    "habilitar_todas": {"func": habilitar_todas,"desc": "Ativa todas do catálogo"},
    "escanear":     {"func": escanear_todas,    "desc": "Status em todas as contas"},
}


def setup_cloud_apis(dry_run=True):
    print(f"[Cloud APIs] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Catálogo: {len(CATALOGO_APIS)} APIs — {', '.join(CATALOGO_APIS.keys())}")
    status = {"catalogo": {k: v["nome"] for k, v in CATALOGO_APIS.items()},
              "contas": {}, "ultima_execucao": datetime.now(timezone.utc).isoformat()}
    for conta in ACCOUNTS:
        if dry_run:
            print(f"  [DRY RUN] habilitaria APIs: {conta}")
            status["contas"][conta] = {"dry_run": True}
        else:
            status["contas"][conta] = listar_habilitadas(conta)
    STATUS_FILE.write_text(json.dumps(status, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nStatus salvo em {STATUS_FILE}")
    return status


if __name__ == "__main__":
    args = sys.argv[1:]
    if "--acao" in args:
        acao = args[args.index("--acao") + 1]
        conta = args[args.index("--conta") + 1] if "--conta" in args else "fabrica"
        api = args[args.index("--api") + 1] if "--api" in args else None
        if acao == "habilitar":
            r = habilitar_api(conta, api)
        elif acao == "desabilitar":
            r = desabilitar_api(conta, api)
        elif acao == "status":
            r = status_api(conta, api)
        elif acao == "listar":
            r = listar_habilitadas(conta)
        elif acao == "quota":
            r = ver_quota(conta, api)
        elif acao == "habilitar_todas":
            r = habilitar_todas(conta)
        elif acao == "escanear":
            r = escanear_todas()
        else:
            r = {"erro": f"ação desconhecida: {acao}"}
        print(json.dumps(r, indent=2, ensure_ascii=False))
    else:
        dry = "--live" not in args
        if dry:
            print("Modo DRY RUN\n")
        setup_cloud_apis(dry_run=dry)
