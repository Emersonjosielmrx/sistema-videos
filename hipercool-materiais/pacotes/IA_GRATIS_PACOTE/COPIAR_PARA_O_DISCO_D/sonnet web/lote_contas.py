# -*- coding: utf-8 -*-
r"""lote_contas.py — para cada conta de empresa que ainda não está no claude-web: cria/entra no claude.ai (PC2),
pega o cookie e cadastra SÓ ela no OmniRoute. Uma por vez. Log: D:\sonnet web\lote_contas.log

    python "D:\sonnet web\lote_contas.py"            # todas as que faltam
    python "D:\sonnet web\lote_contas.py" --max 5    # no máximo 5 nesta rodada
    python "D:\sonnet web\lote_contas.py" --todas-pc2   # todas as contas com Google logado no PC2 (não só empresas)
"""
import json
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, r"D:\postador-de-videos\bin")
sys.path.insert(0, r"D:\sonnet web")
import claude_criar as cc  # noqa: E402
import pegar_cookies as pc  # noqa: E402

BASE = Path(r"D:\sonnet web")
LOG = BASE / "lote_contas.log"
FEITAS = BASE / "contas_no_omniroute.json"
SSH = r"C:\Program Files\Git\usr\bin\ssh.exe"


def log(m):
    linha = f"[{time.strftime('%d/%m %H:%M:%S')}] {m}"
    print(linha, flush=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(linha + "\n")


def _ler(p, padrao):
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return padrao


def cadastrar(email, info):
    entrada = json.dumps({email: info})
    r = subprocess.run([SSH, "-o", "BatchMode=yes", "-o", "ConnectTimeout=15", "hermes-bloqueio",
                        'S=$(docker exec omniroute printenv INITIAL_PASSWORD); '
                        'python3 /opt/omniroute/cadastrar_claude_web.py "$S"; '
                        # health check da VPS leva Cloudflare 403 e marca "expired" à toa (29/10): desligado
                        "sqlite3 /opt/omniroute/data/storage.sqlite \"UPDATE provider_connections SET "
                        "health_check_interval=0, test_status='active' WHERE provider='claude-web' "
                        "AND health_check_interval!=0\""],
                       input=entrada.encode(), capture_output=True, timeout=180, creationflags=0x08000000)
    return (r.stdout + r.stderr).decode("utf-8", "replace").strip()


def _todas_pc2():
    """Todos os perfis com Google logado no PC2 (candidatos a claude-web) -> (email, None). Mais contas = mais cota."""
    import maquina_remota as mr
    out = []
    for perfil, maqs in mr._logins().items():
        if perfil.startswith("_") or perfil.startswith("ig_"):
            continue
        v = (maqs or {}).get("pc2")
        if isinstance(v, dict) and (v.get("google") or v.get("youtube")):
            out.append((f"{perfil}@gmail.com", None))
    return out


def main(a):
    maximo = int(a[a.index("--max") + 1]) if "--max" in a else 99
    feitas = set(_ler(FEITAS, ["sua_conta@gmail.com", "sua_conta@gmail.com", "sua_conta@gmail.com"]))
    fonte = _todas_pc2() if "--todas-pc2" in a else cc.empresas()
    alvos = [(e, n) for e, n in fonte if e not in feitas][:maximo]
    log(f"lote: {len(alvos)} contas a fazer")
    from playwright.sync_api import sync_playwright
    for email, nome in alvos:
        perfil = email.split("@")[0]
        with sync_playwright() as p:
            try:
                r = cc.criar(p, email, nome, maq_forcada="pc2")
            except Exception as e:  # noqa: BLE001
                r = f"{email}: ERRO {type(e).__name__}: {str(e)[:150]}"
        log(r)
        if "CRIADA" not in r and "já tinha conta" not in r:
            continue
        try:
            info = pc.pegar(perfil, "pc2")
        except Exception as e:  # noqa: BLE001
            log(f"{perfil}: cookie ERRO {type(e).__name__}: {str(e)[:150]}")
            continue
        if not info:
            log(f"{perfil}: sem sessionKey depois do login")
            continue
        pc.salvar(email, info)
        saida = cadastrar(email, info)
        log(f"{perfil}: {saida}")
        if "1 criadas" in saida or "atualizada" in saida:
            feitas.add(email)
            FEITAS.write_text(json.dumps(sorted(feitas), indent=2), encoding="utf-8")
    log(f"lote fim: {len(feitas)} contas no claude-web")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main(sys.argv[1:])
