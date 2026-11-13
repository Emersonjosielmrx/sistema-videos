"""
Objetivo 12/14/15: Google Cloud Platform setup automático.
- Cloud Run (deploy containers)
- Container Registry / Artifact Registry (guardar imagens)
- Cloud Functions (serverless)

Usa gcloud CLI ou Console via Playwright.
"""
import json
import sys
import time
import subprocess
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "shared"))
from google_session import ACCOUNTS, google_browser, save_session

GCP_DIR = Path(__file__).resolve().parent
STATUS_FILE = GCP_DIR / "gcp_status.json"

CONSOLE_URL = "https://console.cloud.google.com"
CLOUD_RUN_URL = f"{CONSOLE_URL}/run"
ARTIFACT_REG_URL = f"{CONSOLE_URL}/artifacts"
CLOUD_FUNC_URL = f"{CONSOLE_URL}/functions"


def check_gcloud_cli():
    """Verifica se gcloud CLI está instalado."""
    try:
        r = subprocess.run(["gcloud", "version"], capture_output=True, text=True, timeout=10)
        return r.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def check_gcp_console(account):
    """Verifica acesso ao Console GCP via sessão."""
    try:
        with google_browser(account) as (page, context, browser):
            page.goto(CONSOLE_URL, timeout=45000, wait_until="domcontentloaded")
            time.sleep(5)

            if "accounts.google.com" in page.url:
                return {"account": account, "status": "session_expired"}

            has_project = page.query_selector('[data-project-id], [class*="project"]') is not None

            projects = []
            project_el = page.query_selector('[data-project-id]')
            if project_el:
                projects.append(project_el.get_attribute("data-project-id"))

            save_session(context, account)
            return {
                "account": account,
                "status": "ok",
                "has_project": has_project,
                "projects": projects,
                "console_url": page.url,
            }

    except Exception as e:
        return {"account": account, "status": "error", "error": str(e)}


def enable_cloud_run_api(account):
    """Ativa Cloud Run API no console."""
    try:
        with google_browser(account) as (page, context, browser):
            page.goto(f"{CONSOLE_URL}/apis/library/run.googleapis.com",
                       timeout=45000, wait_until="domcontentloaded")
            time.sleep(5)

            if "accounts.google.com" in page.url:
                return {"success": False, "error": "session_expired"}

            enable_btn = page.query_selector('button:has-text("Enable"), button:has-text("Ativar")')
            if enable_btn:
                enable_btn.click()
                time.sleep(10)
                save_session(context, account)
                return {"success": True, "service": "Cloud Run API"}

            already = page.query_selector('text=API enabled, text=already enabled, text=já ativada')
            if already:
                return {"success": True, "service": "Cloud Run API", "already_enabled": True}

            save_session(context, account)
            return {"success": False, "error": "enable button not found"}

    except Exception as e:
        return {"success": False, "error": str(e)}


def enable_artifact_registry(account):
    """Ativa Artifact Registry API."""
    try:
        with google_browser(account) as (page, context, browser):
            page.goto(f"{CONSOLE_URL}/apis/library/artifactregistry.googleapis.com",
                       timeout=45000, wait_until="domcontentloaded")
            time.sleep(5)

            if "accounts.google.com" in page.url:
                return {"success": False, "error": "session_expired"}

            enable_btn = page.query_selector('button:has-text("Enable"), button:has-text("Ativar")')
            if enable_btn:
                enable_btn.click()
                time.sleep(10)
                save_session(context, account)
                return {"success": True, "service": "Artifact Registry API"}

            save_session(context, account)
            return {"success": True, "service": "Artifact Registry API", "already_enabled": True}

    except Exception as e:
        return {"success": False, "error": str(e)}


def enable_cloud_functions(account):
    """Ativa Cloud Functions API."""
    try:
        with google_browser(account) as (page, context, browser):
            page.goto(f"{CONSOLE_URL}/apis/library/cloudfunctions.googleapis.com",
                       timeout=45000, wait_until="domcontentloaded")
            time.sleep(5)

            if "accounts.google.com" in page.url:
                return {"success": False, "error": "session_expired"}

            enable_btn = page.query_selector('button:has-text("Enable"), button:has-text("Ativar")')
            if enable_btn:
                enable_btn.click()
                time.sleep(10)
                save_session(context, account)
                return {"success": True, "service": "Cloud Functions API"}

            save_session(context, account)
            return {"success": True, "service": "Cloud Functions API", "already_enabled": True}

    except Exception as e:
        return {"success": False, "error": str(e)}


def create_sample_cloud_function():
    """Cria um exemplo de Cloud Function (Python)."""
    func_dir = GCP_DIR / "sample-function"
    func_dir.mkdir(exist_ok=True)

    main_py = func_dir / "main.py"
    main_py.write_text('''import functions_framework

@functions_framework.http
def hello_http(request):
    """HTTP Cloud Function de exemplo."""
    name = request.args.get("name", "World")
    return f"Hello {name}! (Inovare Cloud Function)"
''', encoding="utf-8")

    req_txt = func_dir / "requirements.txt"
    req_txt.write_text("functions-framework==3.*\n", encoding="utf-8")

    print(f"  Sample function criada em {func_dir}")
    return func_dir


def create_sample_cloud_run():
    """Cria exemplo de app pro Cloud Run (Dockerfile + app)."""
    app_dir = GCP_DIR / "sample-cloudrun"
    app_dir.mkdir(exist_ok=True)

    dockerfile = app_dir / "Dockerfile"
    dockerfile.write_text('''FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["python", "app.py"]
''', encoding="utf-8")

    app_py = app_dir / "app.py"
    app_py.write_text('''from flask import Flask, jsonify
import os

app = Flask(__name__)

@app.route("/")
def index():
    return jsonify({
        "service": "Inovare Cloud Run",
        "status": "running",
        "version": "1.0",
    })

@app.route("/health")
def health():
    return jsonify({"status": "healthy"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
''', encoding="utf-8")

    req_txt = app_dir / "requirements.txt"
    req_txt.write_text("flask==3.*\ngunicorn==21.*\n", encoding="utf-8")

    print(f"  Sample Cloud Run app criada em {app_dir}")
    return app_dir


def deploy_cloud_run(nome_servico="inovare-cloudrun", regiao="us-central1", projeto=None):
    """Deploy real do sample-cloudrun via gcloud CLI (source deploy)."""
    if not check_gcloud_cli():
        return {"sucesso": False, "erro": "gcloud CLI não instalado", "instalar": "https://cloud.google.com/sdk/docs/install"}
    app_dir = GCP_DIR / "sample-cloudrun"
    if not app_dir.exists():
        create_sample_cloud_run()
    cmd = ["gcloud", "run", "deploy", nome_servico, "--source", ".",
           "--region", regiao, "--allow-unauthenticated", "--quiet"]
    if projeto:
        cmd += ["--project", projeto]
    try:
        r = subprocess.run(cmd, cwd=str(app_dir), capture_output=True, text=True, timeout=300)
        return {"sucesso": r.returncode == 0, "stdout": r.stdout[-500:], "stderr": r.stderr[-300:]}
    except Exception as e:
        return {"sucesso": False, "erro": str(e)}


def deploy_cloud_function(nome_funcao="hello_http", regiao="us-central1", projeto=None):
    """Deploy real da sample-function via gcloud CLI."""
    if not check_gcloud_cli():
        return {"sucesso": False, "erro": "gcloud CLI não instalado"}
    func_dir = GCP_DIR / "sample-function"
    if not func_dir.exists():
        create_sample_cloud_function()
    cmd = ["gcloud", "functions", "deploy", nome_funcao, "--runtime", "python311",
           "--trigger-http", "--allow-unauthenticated", "--region", regiao,
           "--entry-point", "hello_http", "--source", ".", "--quiet"]
    if projeto:
        cmd += ["--project", projeto]
    try:
        r = subprocess.run(cmd, cwd=str(func_dir), capture_output=True, text=True, timeout=300)
        return {"sucesso": r.returncode == 0, "stdout": r.stdout[-500:], "stderr": r.stderr[-300:]}
    except Exception as e:
        return {"sucesso": False, "erro": str(e)}


def listar_servicos(projeto=None, regiao="us-central1"):
    """Lista serviços Cloud Run via gcloud CLI."""
    if not check_gcloud_cli():
        return {"sucesso": False, "erro": "gcloud CLI não instalado"}
    cmd = ["gcloud", "run", "services", "list", "--region", regiao, "--format", "json"]
    if projeto:
        cmd += ["--project", projeto]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        servicos = json.loads(r.stdout) if r.stdout.strip() else []
        return {"sucesso": True, "servicos": [s.get("metadata", {}).get("name") for s in servicos]}
    except Exception as e:
        return {"sucesso": False, "erro": str(e)}


def ver_logs(nome_servico, projeto=None, limite=50):
    """Lê logs de um serviço Cloud Run via gcloud CLI."""
    if not check_gcloud_cli():
        return {"sucesso": False, "erro": "gcloud CLI não instalado"}
    cmd = ["gcloud", "run", "services", "logs", "read", nome_servico,
           "--limit", str(limite), "--format", "value(textPayload)"]
    if projeto:
        cmd += ["--project", projeto]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        return {"sucesso": r.returncode == 0, "logs": r.stdout[-2000:]}
    except Exception as e:
        return {"sucesso": False, "erro": str(e)}


FUNCIONALIDADES = {
    "verificar":      {"func": check_gcp_console,          "desc": "Verifica acesso ao console GCP"},
    "enable_run":     {"func": enable_cloud_run_api,       "desc": "Ativa Cloud Run API"},
    "enable_registry":{"func": enable_artifact_registry,   "desc": "Ativa Artifact Registry"},
    "enable_func":    {"func": enable_cloud_functions,     "desc": "Ativa Cloud Functions API"},
    "deploy_run":     {"func": deploy_cloud_run,           "desc": "Deploy Cloud Run (gcloud)"},
    "deploy_func":    {"func": deploy_cloud_function,       "desc": "Deploy Cloud Function (gcloud)"},
    "listar":         {"func": listar_servicos,            "desc": "Lista serviços Cloud Run"},
    "logs":           {"func": ver_logs,                   "desc": "Lê logs de um serviço"},
    "sample_run":     {"func": create_sample_cloud_run,    "desc": "Gera app Cloud Run (offline)"},
    "sample_func":    {"func": create_sample_cloud_function,"desc": "Gera Cloud Function (offline)"},
}


def setup_gcp_infra(dry_run=True):
    """Setup completo de infra GCP."""
    print(f"[GCP Infra Setup] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    gcloud_ok = check_gcloud_cli()
    print(f"  gcloud CLI: {'OK' if gcloud_ok else 'NÃO INSTALADO'}")

    sample_func = create_sample_cloud_function()
    sample_run = create_sample_cloud_run()

    status = {
        "gcloud_cli": gcloud_ok,
        "sample_function": str(sample_func),
        "sample_cloudrun": str(sample_run),
        "accounts": {},
        "last_run": datetime.now(timezone.utc).isoformat(),
    }

    if dry_run:
        for acc in ACCOUNTS:
            print(f"  [DRY RUN] Verificaria console GCP: {acc}")
            status["accounts"][acc] = {"dry_run": True}
    else:
        for acc in ACCOUNTS:
            print(f"  Verificando {acc}...", end=" ", flush=True)
            r = check_gcp_console(acc)
            print(r["status"])
            status["accounts"][acc] = r

    STATUS_FILE.write_text(json.dumps(status, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nStatus salvo em {STATUS_FILE}")

    if not gcloud_ok:
        print("\nPra deploy real, instale gcloud CLI:")
        print("  https://cloud.google.com/sdk/docs/install")

    return status


if __name__ == "__main__":
    args = sys.argv[1:]
    if "--acao" in args:
        acao = args[args.index("--acao") + 1]
        conta = args[args.index("--conta") + 1] if "--conta" in args else "fabrica"
        projeto = args[args.index("--projeto") + 1] if "--projeto" in args else None
        if acao == "verificar":
            r = check_gcp_console(conta)
        elif acao == "enable_run":
            r = enable_cloud_run_api(conta)
        elif acao == "enable_registry":
            r = enable_artifact_registry(conta)
        elif acao == "enable_func":
            r = enable_cloud_functions(conta)
        elif acao == "deploy_run":
            nome = args[args.index("--nome") + 1] if "--nome" in args else "inovare-cloudrun"
            r = deploy_cloud_run(nome, projeto=projeto)
        elif acao == "deploy_func":
            nome = args[args.index("--nome") + 1] if "--nome" in args else "hello_http"
            r = deploy_cloud_function(nome, projeto=projeto)
        elif acao == "listar":
            r = listar_servicos(projeto)
        elif acao == "logs":
            r = ver_logs(args[args.index("--nome") + 1], projeto)
        elif acao == "sample_run":
            r = {"app_dir": str(create_sample_cloud_run())}
        elif acao == "sample_func":
            r = {"func_dir": str(create_sample_cloud_function())}
        else:
            r = {"erro": f"ação desconhecida: {acao}"}
        print(json.dumps(r, indent=2, ensure_ascii=False, default=str))
    else:
        dry = "--live" not in args
        if dry:
            print("Modo DRY RUN (--live pra testar com sessões reais)\n")
        setup_gcp_infra(dry_run=dry)
