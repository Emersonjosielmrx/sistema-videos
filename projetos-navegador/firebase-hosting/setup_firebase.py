"""
Firebase Hosting — automação COMPLETA do Firebase (hosting + projetos).

Operações disponíveis:
  - verificar_console(conta)            → lista projetos Firebase
  - criar_projeto(conta, nome)          → cria projeto Firebase via console
  - criar_sample_site()                 → gera site estático (offline)
  - deploy_site(diretorio, projeto)     → deploy via firebase CLI
  - listar_sites(conta)                 → lista sites hospedados
  - config_firestore(conta, projeto)    → abre setup do Firestore
  - ver_analytics(conta, projeto)       → métricas do projeto
  - checar_firebase_cli()               → verifica se firebase-tools está instalado

CLI:
  python setup_firebase.py                             → dry run
  python setup_firebase.py --live
  python setup_firebase.py --acao deploy --diretorio sample-site --projeto meu-projeto
  python setup_firebase.py --acao listar --conta X
"""
import json
import sys
import time
import subprocess
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "shared"))
from google_session import ACCOUNTS, google_browser, save_session

FB_DIR = Path(__file__).resolve().parent
STATUS_FILE = FB_DIR / "firebase_status.json"
FIREBASE_URL = "https://console.firebase.google.com/"


def _sessao_expirada(page):
    return "accounts.google.com" in page.url


def checar_firebase_cli():
    """Verifica se firebase-tools (CLI) está instalado."""
    for cmd in (["firebase", "--version"], ["npx", "firebase", "--version"]):
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
            if r.returncode == 0:
                return {"instalado": True, "versao": r.stdout.strip(), "cmd": cmd[0]}
        except (FileNotFoundError, subprocess.TimeoutExpired):
            continue
    return {"instalado": False}


def criar_sample_site():
    """Gera um site estático de exemplo (offline)."""
    site_dir = FB_DIR / "sample-site"
    site_dir.mkdir(exist_ok=True)
    (site_dir / "index.html").write_text('''<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Inovare Hub</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: system-ui; background: #0a0a0a; color: #e0e0e0; display: flex; align-items: center; justify-content: center; min-height: 100vh; }
        .container { text-align: center; max-width: 600px; padding: 2rem; }
        h1 { font-size: 2.5rem; background: linear-gradient(135deg, #6366f1, #a855f7, #ec4899); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 1rem; }
        p { color: #888; font-size: 1.1rem; line-height: 1.6; }
        .status { margin-top: 2rem; padding: 1rem; border: 1px solid #333; border-radius: 8px; }
        .dot { display: inline-block; width: 8px; height: 8px; background: #22c55e; border-radius: 50%; margin-right: 8px; animation: pulse 2s infinite; }
        @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.3; } }
    </style>
</head>
<body>
    <div class="container">
        <h1>Inovare Hub</h1>
        <p>Plataforma de automação e serviços inteligentes.</p>
        <div class="status"><span class="dot"></span> Sistema operacional</div>
    </div>
</body>
</html>
''', encoding="utf-8")
    (site_dir / "firebase.json").write_text(json.dumps({
        "hosting": {"public": ".", "ignore": ["firebase.json", "**/.*"],
                    "rewrites": [{"source": "**", "destination": "/index.html"}]}
    }, indent=2), encoding="utf-8")
    print(f"  Site de exemplo criado em {site_dir}")
    return {"sucesso": True, "site_dir": str(site_dir)}


def verificar_console(conta):
    """Lista projetos Firebase da conta."""
    try:
        with google_browser(conta) as (page, context, browser):
            page.goto(FIREBASE_URL, timeout=45000, wait_until="domcontentloaded")
            time.sleep(6)
            if _sessao_expirada(page):
                return {"conta": conta, "status": "sessao_expirada"}
            projetos = []
            for card in page.query_selector_all('[class*="project-card"], [class*="ProjectCard"], a[href*="/project/"]'):
                t = card.inner_text().strip().split("\n")[0]
                if t and len(t) < 80:
                    projetos.append(t)
            save_session(context, conta)
            return {"conta": conta, "status": "ok", "projetos": list(dict.fromkeys(projetos))}
    except Exception as e:
        return {"conta": conta, "status": "erro", "erro": str(e)}


def criar_projeto(conta, nome_projeto):
    """Cria um projeto Firebase via console."""
    try:
        with google_browser(conta) as (page, context, browser):
            page.goto(FIREBASE_URL, timeout=45000, wait_until="domcontentloaded")
            time.sleep(6)
            if _sessao_expirada(page):
                return {"sucesso": False, "erro": "sessao_expirada"}
            add = page.query_selector('[class*="create"], button:has-text("Add project"), button:has-text("Adicionar projeto"), a:has-text("Create a project")')
            if add:
                add.click()
                time.sleep(3)
                nome_input = page.query_selector('input[type="text"], input[aria-label*="name"]')
                if nome_input:
                    nome_input.fill(nome_projeto)
                    time.sleep(1)
                    cont = page.query_selector('button:has-text("Continue"), button:has-text("Continuar")')
                    if cont:
                        cont.click()
                        time.sleep(4)
                    save_session(context, conta)
                    return {"sucesso": True, "projeto": nome_projeto, "nota": "pode exigir passos extras (Analytics/billing)"}
            return {"sucesso": False, "erro": "botão criar projeto não encontrado"}
    except Exception as e:
        return {"sucesso": False, "erro": str(e)}


def deploy_site(diretorio="sample-site", projeto=None):
    """Deploy do site via firebase CLI."""
    cli = checar_firebase_cli()
    if not cli["instalado"]:
        return {"sucesso": False, "erro": "firebase CLI não instalado", "instalar": "npm install -g firebase-tools"}
    site_path = FB_DIR / diretorio if not Path(diretorio).is_absolute() else Path(diretorio)
    if not site_path.exists():
        return {"sucesso": False, "erro": f"diretório não existe: {site_path}"}
    cmd = [cli["cmd"], "deploy", "--only", "hosting"]
    if projeto:
        cmd += ["--project", projeto]
    try:
        r = subprocess.run(cmd, cwd=str(site_path), capture_output=True, text=True, timeout=180)
        return {"sucesso": r.returncode == 0, "stdout": r.stdout[-500:], "stderr": r.stderr[-300:]}
    except Exception as e:
        return {"sucesso": False, "erro": str(e)}


def listar_sites(conta):
    """Lista sites hospedados no Firebase Hosting."""
    try:
        with google_browser(conta) as (page, context, browser):
            page.goto(f"{FIREBASE_URL}", timeout=45000, wait_until="domcontentloaded")
            time.sleep(6)
            if _sessao_expirada(page):
                return {"conta": conta, "sites": [], "erro": "sessao_expirada"}
            sites = []
            for el in page.query_selector_all('[class*="hosting"], a[href*="web.app"], a[href*="firebaseapp.com"]'):
                t = el.inner_text().strip()
                if t and len(t) < 100:
                    sites.append(t)
            save_session(context, conta)
            return {"conta": conta, "sites": list(dict.fromkeys(sites))}
    except Exception as e:
        return {"conta": conta, "sites": [], "erro": str(e)}


def config_firestore(conta, projeto):
    """Abre o setup do Firestore de um projeto."""
    try:
        with google_browser(conta) as (page, context, browser):
            page.goto(f"{FIREBASE_URL}project/{projeto}/firestore", timeout=45000, wait_until="domcontentloaded")
            time.sleep(6)
            if _sessao_expirada(page):
                return {"sucesso": False, "erro": "sessao_expirada"}
            create = page.query_selector('button:has-text("Create database"), button:has-text("Criar banco")')
            estado = "banco_ja_existe"
            if create:
                estado = "pronto_pra_criar"
            save_session(context, conta)
            return {"sucesso": True, "projeto": projeto, "firestore": estado}
    except Exception as e:
        return {"sucesso": False, "erro": str(e)}


def ver_analytics(conta, projeto):
    """Métricas do projeto Firebase."""
    try:
        with google_browser(conta) as (page, context, browser):
            page.goto(f"{FIREBASE_URL}project/{projeto}/analytics", timeout=45000, wait_until="domcontentloaded")
            time.sleep(7)
            if _sessao_expirada(page):
                return {"conta": conta, "erro": "sessao_expirada"}
            metricas = []
            for el in page.query_selector_all('[class*="metric"], [class*="kpi"], [class*="card"]'):
                t = el.inner_text().strip()
                if t and len(t) < 100:
                    metricas.append(t)
            save_session(context, conta)
            return {"conta": conta, "projeto": projeto, "metricas": metricas[:20]}
    except Exception as e:
        return {"conta": conta, "erro": str(e)}


FUNCIONALIDADES = {
    "verificar":    {"func": verificar_console,  "desc": "Lista projetos Firebase"},
    "criar_projeto":{"func": criar_projeto,      "desc": "Cria projeto"},
    "sample_site":  {"func": criar_sample_site,  "desc": "Gera site estático (offline)"},
    "deploy":       {"func": deploy_site,        "desc": "Deploy via firebase CLI"},
    "listar":       {"func": listar_sites,       "desc": "Lista sites hospedados"},
    "firestore":    {"func": config_firestore,   "desc": "Setup do Firestore"},
    "analytics":    {"func": ver_analytics,      "desc": "Métricas do projeto"},
    "cli":          {"func": checar_firebase_cli,"desc": "Checa firebase CLI"},
}


def setup_firebase(dry_run=True):
    print(f"[Firebase Hosting] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Funcionalidades: {', '.join(FUNCIONALIDADES.keys())}")
    criar_sample_site()
    cli = checar_firebase_cli()
    print(f"  firebase CLI: {'OK ' + cli.get('versao','') if cli['instalado'] else 'NÃO INSTALADO (npm i -g firebase-tools)'}")
    status = {"firebase_cli": cli, "contas": {}, "ultima_execucao": datetime.now(timezone.utc).isoformat()}
    for conta in ACCOUNTS:
        if dry_run:
            print(f"  [DRY RUN] verificaria Firebase: {conta}")
            status["contas"][conta] = {"dry_run": True}
        else:
            print(f"  {conta}...", end=" ", flush=True)
            r = verificar_console(conta)
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
        projeto = args[args.index("--projeto") + 1] if "--projeto" in args else None
        if acao == "verificar":
            r = verificar_console(conta)
        elif acao == "criar_projeto":
            r = criar_projeto(conta, args[args.index("--nome") + 1])
        elif acao == "sample_site":
            r = criar_sample_site()
        elif acao == "deploy":
            diretorio = args[args.index("--diretorio") + 1] if "--diretorio" in args else "sample-site"
            r = deploy_site(diretorio, projeto)
        elif acao == "listar":
            r = listar_sites(conta)
        elif acao == "firestore":
            r = config_firestore(conta, projeto)
        elif acao == "analytics":
            r = ver_analytics(conta, projeto)
        elif acao == "cli":
            r = checar_firebase_cli()
        else:
            r = {"erro": f"ação desconhecida: {acao}"}
        print(json.dumps(r, indent=2, ensure_ascii=False))
    else:
        setup_firebase(dry_run="--live" not in args)
