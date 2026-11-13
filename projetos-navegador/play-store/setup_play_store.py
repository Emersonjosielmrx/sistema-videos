"""
Play Store — automação COMPLETA do Google Play Console.

Operações disponíveis:
  - verificar_conta(conta)              → checa se tem conta de desenvolvedor
  - listar_apps(conta)                  → lista apps publicados
  - criar_sample_app()                  → gera projeto Android WebView (offline)
  - criar_listing(nome, descricao)      → gera ficha de loja (offline)
  - subir_apk(conta, caminho_apk)       → sobe APK/AAB no console
  - publicar_app(conta, nome)           → envia app pra review
  - ver_reviews(conta, nome)            → lista avaliações do app
  - ver_crashes(conta, nome)            → relatório de falhas
  - responder_review(conta, nome, idx, texto) → responde avaliação

CLI:
  python setup_play_store.py                           → dry run (gera sample app)
  python setup_play_store.py --live
  python setup_play_store.py --acao listar_apps --conta X
  python setup_play_store.py --acao criar_listing --nome "Inovare Hub"
"""
import json
import sys
import time
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "shared"))
from google_session import ACCOUNTS, google_browser, save_session

PLAY_DIR = Path(__file__).resolve().parent
STATUS_FILE = PLAY_DIR / "play_status.json"
HISTORICO = PLAY_DIR / "historico_play.jsonl"
PLAY_CONSOLE_URL = "https://play.google.com/console"


def _sessao_expirada(page):
    return "accounts.google.com" in page.url


def _log(acao, conta, detalhes):
    with open(HISTORICO, "a", encoding="utf-8") as f:
        f.write(json.dumps({"ts": datetime.now(timezone.utc).isoformat(),
                            "acao": acao, "conta": conta, "detalhes": detalhes}, ensure_ascii=False) + "\n")


def verificar_conta(conta):
    """Checa se a conta tem conta de desenvolvedor Play."""
    try:
        with google_browser(conta) as (page, context, browser):
            page.goto(PLAY_CONSOLE_URL, timeout=45000, wait_until="domcontentloaded")
            time.sleep(6)
            if _sessao_expirada(page):
                return {"conta": conta, "status": "sessao_expirada"}
            if "play.google.com/console" in page.url:
                apps = []
                for el in page.query_selector_all('[class*="app-name"], [class*="AppName"], a[href*="/app/"]')[:15]:
                    t = el.inner_text().strip()
                    if t:
                        apps.append(t)
                save_session(context, conta)
                return {"conta": conta, "status": "tem_conta_desenvolvedor", "apps": list(dict.fromkeys(apps))}
            if "signup" in page.url or "register" in page.url:
                return {"conta": conta, "status": "sem_conta_desenvolvedor", "nota": "precisa pagar US$25 e aceitar termos"}
            return {"conta": conta, "status": "indefinido", "url": page.url}
    except Exception as e:
        return {"conta": conta, "status": "erro", "erro": str(e)}


def listar_apps(conta):
    """Lista apps publicados no console."""
    try:
        with google_browser(conta) as (page, context, browser):
            page.goto(f"{PLAY_CONSOLE_URL}/developers", timeout=45000, wait_until="domcontentloaded")
            time.sleep(7)
            if _sessao_expirada(page):
                return {"conta": conta, "apps": [], "erro": "sessao_expirada"}
            apps = []
            for el in page.query_selector_all('[class*="app-name"], a[href*="/app/"], [role="row"]'):
                t = el.inner_text().strip().split("\n")[0]
                if t and len(t) < 100:
                    apps.append(t)
            save_session(context, conta)
            return {"conta": conta, "apps": list(dict.fromkeys(apps))}
    except Exception as e:
        return {"conta": conta, "apps": [], "erro": str(e)}


def criar_sample_app():
    """Gera estrutura de app Android WebView (offline)."""
    app_dir = PLAY_DIR / "sample-app"
    app_dir.mkdir(exist_ok=True)

    (app_dir / "AndroidManifest.xml").write_text('''<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android"
    package="com.inovare.hubapp">
    <uses-permission android:name="android.permission.INTERNET" />
    <application
        android:allowBackup="true"
        android:icon="@mipmap/ic_launcher"
        android:label="Inovare Hub"
        android:theme="@style/Theme.AppCompat.Light.NoActionBar">
        <activity android:name=".MainActivity" android:exported="true">
            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>
        </activity>
    </application>
</manifest>
''', encoding="utf-8")

    (app_dir / "MainActivity.java").write_text('''package com.inovare.hubapp;

import android.app.Activity;
import android.os.Bundle;
import android.webkit.WebView;
import android.webkit.WebViewClient;

public class MainActivity extends Activity {
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        WebView webView = new WebView(this);
        webView.setWebViewClient(new WebViewClient());
        webView.getSettings().setJavaScriptEnabled(true);
        webView.loadUrl("https://inovare-hub.web.app");
        setContentView(webView);
    }
}
''', encoding="utf-8")

    print(f"  Sample app criado em {app_dir}")
    return {"sucesso": True, "app_dir": str(app_dir)}


def criar_listing(nome_app, descricao="", categoria="Entertainment"):
    """Gera ficha de loja (store listing) offline."""
    listing = {
        "nome": nome_app,
        "descricao_curta": descricao[:80] or f"{nome_app} — seu hub de conteúdo",
        "descricao_completa": descricao or f"{nome_app} reúne os melhores conteúdos num só lugar. Recaps, curiosidades e muito mais.",
        "categoria": categoria,
        "email_contato": "inovare.contato@gmail.com",
        "politica_privacidade": "https://inovare-hub.web.app/privacy",
        "assets_necessarios": {
            "icone": "512x512 PNG",
            "feature_graphic": "1024x500 PNG",
            "screenshots": "min 2, 16:9 ou 9:16",
        },
        "gerado_em": datetime.now(timezone.utc).isoformat(),
    }
    caminho = PLAY_DIR / f"listing_{nome_app.lower().replace(' ', '_')}.json"
    caminho.write_text(json.dumps(listing, indent=2, ensure_ascii=False), encoding="utf-8")
    return {"sucesso": True, "arquivo": str(caminho), "listing": listing}


def subir_apk(conta, caminho_apk):
    """Sobe APK/AAB no console."""
    caminho = Path(caminho_apk)
    if not caminho.exists():
        return {"sucesso": False, "erro": f"arquivo não existe: {caminho}"}
    try:
        with google_browser(conta, headless=False) as (page, context, browser):
            page.goto(f"{PLAY_CONSOLE_URL}", timeout=45000, wait_until="domcontentloaded")
            time.sleep(6)
            if _sessao_expirada(page):
                return {"sucesso": False, "erro": "sessao_expirada"}
            file_input = page.query_selector('input[type="file"]')
            if file_input:
                file_input.set_input_files(str(caminho.resolve()))
                time.sleep(8)
                save_session(context, conta)
                _log("subir_apk", conta, caminho.name)
                return {"sucesso": True, "arquivo": caminho.name}
            return {"sucesso": False, "erro": "input de upload não encontrado (navegue até a aba de release)"}
    except Exception as e:
        return {"sucesso": False, "erro": str(e)}


def publicar_app(conta, nome_app):
    """Envia app pra review."""
    try:
        with google_browser(conta) as (page, context, browser):
            page.goto(PLAY_CONSOLE_URL, timeout=45000, wait_until="domcontentloaded")
            time.sleep(6)
            if _sessao_expirada(page):
                return {"sucesso": False, "erro": "sessao_expirada"}
            review_btn = page.query_selector('button:has-text("Send for review"), button:has-text("Enviar para revisão"), button:has-text("Publish")')
            if review_btn:
                review_btn.click()
                time.sleep(3)
                save_session(context, conta)
                _log("publicar_app", conta, nome_app)
                return {"sucesso": True, "app": nome_app}
            return {"sucesso": False, "erro": "botão de review não encontrado"}
    except Exception as e:
        return {"sucesso": False, "erro": str(e)}


def ver_reviews(conta, nome_app):
    """Lista avaliações do app."""
    try:
        with google_browser(conta) as (page, context, browser):
            page.goto(PLAY_CONSOLE_URL, timeout=45000, wait_until="domcontentloaded")
            time.sleep(7)
            if _sessao_expirada(page):
                return {"conta": conta, "reviews": [], "erro": "sessao_expirada"}
            reviews = []
            for el in page.query_selector_all('[class*="review"], [class*="rating-row"], [role="row"]'):
                t = el.inner_text().strip()
                if t and len(t) < 300:
                    reviews.append(t)
            save_session(context, conta)
            return {"conta": conta, "app": nome_app, "reviews": reviews[:20]}
    except Exception as e:
        return {"conta": conta, "reviews": [], "erro": str(e)}


def ver_crashes(conta, nome_app):
    """Relatório de falhas (Android Vitals)."""
    try:
        with google_browser(conta) as (page, context, browser):
            page.goto(f"{PLAY_CONSOLE_URL}", timeout=45000, wait_until="domcontentloaded")
            time.sleep(7)
            if _sessao_expirada(page):
                return {"conta": conta, "erro": "sessao_expirada"}
            crashes = []
            for el in page.query_selector_all('[class*="crash"], [class*="vitals"], [role="row"]'):
                t = el.inner_text().strip()
                if t and ("crash" in t.lower() or "anr" in t.lower() or "%" in t):
                    crashes.append(t[:150])
            save_session(context, conta)
            return {"conta": conta, "app": nome_app, "crashes": crashes[:20]}
    except Exception as e:
        return {"conta": conta, "erro": str(e)}


def responder_review(conta, nome_app, indice, texto):
    """Responde uma avaliação."""
    try:
        with google_browser(conta) as (page, context, browser):
            page.goto(PLAY_CONSOLE_URL, timeout=45000, wait_until="domcontentloaded")
            time.sleep(7)
            if _sessao_expirada(page):
                return {"sucesso": False, "erro": "sessao_expirada"}
            reply_btns = page.query_selector_all('button:has-text("Reply"), button:has-text("Responder")')
            if indice < len(reply_btns):
                reply_btns[indice].click()
                time.sleep(2)
                box = page.query_selector('textarea, div[contenteditable="true"]')
                if box:
                    box.click()
                    box.type(texto, delay=20)
                    send = page.query_selector('button:has-text("Send"), button:has-text("Enviar"), button:has-text("Submit")')
                    if send:
                        send.click()
                        time.sleep(2)
                    save_session(context, conta)
                    return {"sucesso": True, "app": nome_app, "resposta": texto[:50]}
            return {"sucesso": False, "erro": f"review {indice} não encontrada"}
    except Exception as e:
        return {"sucesso": False, "erro": str(e)}


FUNCIONALIDADES = {
    "verificar_conta": {"func": verificar_conta,  "desc": "Checa conta de desenvolvedor"},
    "listar_apps":     {"func": listar_apps,      "desc": "Lista apps publicados"},
    "sample_app":      {"func": criar_sample_app, "desc": "Gera projeto Android (offline)"},
    "criar_listing":   {"func": criar_listing,    "desc": "Gera ficha de loja (offline)"},
    "subir_apk":       {"func": subir_apk,        "desc": "Sobe APK/AAB"},
    "publicar":        {"func": publicar_app,     "desc": "Envia app pra review"},
    "reviews":         {"func": ver_reviews,      "desc": "Lista avaliações"},
    "crashes":         {"func": ver_crashes,      "desc": "Relatório de falhas"},
    "responder":       {"func": responder_review, "desc": "Responde avaliação"},
}


def setup_play_store(dry_run=True):
    print(f"[Play Store] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Funcionalidades: {', '.join(FUNCIONALIDADES.keys())}")
    criar_sample_app()
    status = {"contas": {}, "ultima_execucao": datetime.now(timezone.utc).isoformat()}
    for conta in ACCOUNTS:
        if dry_run:
            print(f"  [DRY RUN] verificaria Play Console: {conta}")
            status["contas"][conta] = {"dry_run": True}
        else:
            print(f"  {conta}...", end=" ", flush=True)
            r = verificar_conta(conta)
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
        nome = args[args.index("--nome") + 1] if "--nome" in args else "Inovare Hub"
        if acao == "verificar_conta":
            r = verificar_conta(conta)
        elif acao == "listar_apps":
            r = listar_apps(conta)
        elif acao == "sample_app":
            r = criar_sample_app()
        elif acao == "criar_listing":
            desc = args[args.index("--desc") + 1] if "--desc" in args else ""
            r = criar_listing(nome, desc)
        elif acao == "subir_apk":
            r = subir_apk(conta, args[args.index("--apk") + 1])
        elif acao == "publicar":
            r = publicar_app(conta, nome)
        elif acao == "reviews":
            r = ver_reviews(conta, nome)
        elif acao == "crashes":
            r = ver_crashes(conta, nome)
        elif acao == "responder":
            idx = int(args[args.index("--indice") + 1]) if "--indice" in args else 0
            r = responder_review(conta, nome, idx, args[args.index("--texto") + 1])
        else:
            r = {"erro": f"ação desconhecida: {acao}"}
        print(json.dumps(r, indent=2, ensure_ascii=False))
    else:
        setup_play_store(dry_run="--live" not in args)
