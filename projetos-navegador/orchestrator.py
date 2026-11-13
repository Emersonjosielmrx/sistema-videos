"""
Orquestrador Central — roda todos os projetos-navegador em sequência.
Usado pelo cron de 12h pra avançar todos os objetivos continuamente.
"""
import json
import sys
import subprocess
import time
from pathlib import Path
from datetime import datetime, timezone

BASE_DIR = Path("D:/projetos-navegador")
PYTHON = "D:/hipercool-videos/venv/Scripts/python.exe"
LOG_FILE = BASE_DIR / "orchestrator.log"
STATUS_FILE = BASE_DIR / "orchestrator_status.json"

PROJECTS = [
    {"name": "Atualizador de Sessões", "dir": "auto-refresh-sessoes", "script": "session_health_check.py", "needs_session": True, "priority": 1, "funcoes": 2},
    {"name": "Fábrica de Chaves", "dir": "key-factory", "script": "key_factory.py", "needs_session": True, "priority": 1, "funcoes": 6},
    {"name": "Blogger + AdSense", "dir": "blogger-adsense", "script": "setup_blogger.py", "needs_session": True, "priority": 2, "funcoes": 9},
    {"name": "Nuvem (Cloud Run/Registry/Functions)", "dir": "cloud-run", "script": "setup_gcp.py", "needs_session": True, "priority": 2, "funcoes": 10},
    {"name": "Hospedagem Firebase", "dir": "firebase-hosting", "script": "setup_firebase.py", "needs_session": True, "priority": 2, "funcoes": 8},
    {"name": "Central de Chat (Agentes)", "dir": "chat-hub-agentes", "script": "setup_chat.py", "needs_session": True, "priority": 3, "funcoes": 9},
    {"name": "Gerenciador YouTube", "dir": "youtube-manager", "script": "setup_youtube.py", "needs_session": True, "priority": 3, "funcoes": 17},
    {"name": "Redes Sociais", "dir": "redes-sociais", "script": "setup_social.py", "needs_session": False, "priority": 3, "funcoes": 5},
    {"name": "Armazenamento Drive", "dir": "drive-storage", "script": "setup_drive.py", "needs_session": True, "priority": 4, "funcoes": 10},
    {"name": "APIs da Nuvem", "dir": "cloud-apis", "script": "setup_apis.py", "needs_session": True, "priority": 4, "funcoes": 7},
    {"name": "SEO + Search Console", "dir": "seo-search-console", "script": "setup_seo.py", "needs_session": True, "priority": 4, "funcoes": 8},
    {"name": "Compartilhamento de Banda", "dir": "bandwidth-sharing", "script": "setup_bandwidth.py", "needs_session": False, "priority": 5, "funcoes": 3},
    {"name": "Mineração em Colab", "dir": "mining-colab", "script": "setup_mining.py", "needs_session": False, "priority": 5, "funcoes": 3},
    {"name": "Trabalhadores Colab", "dir": "colab-workers", "script": "setup_colab.py", "needs_session": False, "priority": 5, "funcoes": 2},
    {"name": "Volume no Meet", "dir": "meet-volume", "script": "setup_meet.py", "needs_session": True, "priority": 6, "funcoes": 8},
    {"name": "Play Store", "dir": "play-store", "script": "setup_play_store.py", "needs_session": True, "priority": 6, "funcoes": 9},
    {"name": "Fábrica de Credenciais", "dir": "credential-factory", "script": "factory.py", "needs_session": True, "priority": 1, "funcoes": 3},
]


def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def check_sessions_health():
    """Verifica se as sessões estão vivas."""
    health_file = BASE_DIR / "auto-refresh-sessoes" / "session_health.json"
    if health_file.exists():
        data = json.loads(health_file.read_text(encoding="utf-8"))
        return data.get("valid", 0) > 0, data.get("valid", 0), data.get("total", 0)
    return False, 0, 0


def run_project(project, dry_run=True):
    """Roda um projeto individual."""
    script_path = BASE_DIR / project["dir"] / project["script"]
    if not script_path.exists():
        return {"name": project["name"], "status": "script_not_found"}

    args = [PYTHON, str(script_path)]
    if not dry_run:
        args.append("--live")

    env = dict(__import__("os").environ)
    env["PYTHONUTF8"] = "1"

    try:
        result = subprocess.run(
            args,
            capture_output=True,
            text=True,
            timeout=120,
            env=env,
            cwd=str(BASE_DIR),
        )
        return {
            "name": project["name"],
            "status": "ok" if result.returncode == 0 else "error",
            "returncode": result.returncode,
            "output_lines": result.stdout.strip().split("\n")[-5:] if result.stdout else [],
            "error": result.stderr.strip()[-200:] if result.stderr else None,
        }
    except subprocess.TimeoutExpired:
        return {"name": project["name"], "status": "timeout"}
    except Exception as e:
        return {"name": project["name"], "status": "exception", "error": str(e)}


def run_all(dry_run=True):
    """Roda todos os projetos em ordem de prioridade."""
    log(f"{'='*60}")
    log(f"Orquestrador iniciado — {'DRY RUN' if dry_run else 'LIVE'}")
    log(f"{'='*60}")

    has_sessions, valid, total = check_sessions_health()
    log(f"Sessões: {valid}/{total} válidas")

    results = []
    sorted_projects = sorted(PROJECTS, key=lambda p: p["priority"])

    for project in sorted_projects:
        if project["needs_session"] and not has_sessions and not dry_run:
            log(f"  SKIP {project['name']} (sem sessões válidas)")
            results.append({"name": project["name"], "status": "skipped_no_session"})
            continue

        log(f"  Rodando: {project['name']}...")
        r = run_project(project, dry_run=dry_run)
        log(f"    → {r['status']}")
        results.append(r)

    status = {
        "last_run": datetime.now(timezone.utc).isoformat(),
        "mode": "dry_run" if dry_run else "live",
        "sessions_valid": valid,
        "projects_run": len(results),
        "projects_ok": sum(1 for r in results if r["status"] == "ok"),
        "projects_error": sum(1 for r in results if r["status"] in ("error", "exception", "timeout")),
        "projects_skipped": sum(1 for r in results if r["status"].startswith("skip")),
        "results": results,
    }

    STATUS_FILE.write_text(json.dumps(status, indent=2, ensure_ascii=False), encoding="utf-8")
    log(f"\nResumo: {status['projects_ok']} OK, {status['projects_error']} erros, {status['projects_skipped']} pulados")
    log(f"Status salvo em {STATUS_FILE}")

    return status


if __name__ == "__main__":
    dry = "--live" not in sys.argv
    run_all(dry_run=dry)
