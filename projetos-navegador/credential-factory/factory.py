"""
Orquestrador da Fábrica de Credenciais — executa todos os submódulos.

CLI:
  python factory.py                    → seco (dry run: só lista)
  python factory.py --live             → escaneia tudo de verdade
  python factory.py --acao youtube     → só YouTube (verificar canais)
  python factory.py --acao cloudflare  → só Cloudflare (verificar tokens)
  python factory.py --acao gemini      → chama key_factory (já existente)
"""
import json
import sys
import time
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, r"D:\logins-google")
import cofre

FACTORY_DIR = Path(__file__).resolve().parent
PROJECT_DIR = FACTORY_DIR.parent
STATUS_FILE = FACTORY_DIR / "factory_status.json"

if str(FACTORY_DIR) not in sys.path:
    sys.path.insert(0, str(FACTORY_DIR))


def _contas_do_cofre():
    reg = cofre._ler()
    return list(reg["contas"].keys())


def resumo_youtube(dry_run=True):
    """Verifica status de canais YouTube em todas as contas."""
    from youtube_channel import verificar_canal, verificar_todas, listar_sem_canal

    if dry_run:
        contas = _contas_do_cofre()
        print(f"  [DRY RUN] YouTube: {len(contas)} contas no cofre")
        return {"modulo": "youtube", "dry_run": True, "total_contas": len(contas)}

    return verificar_todas()


def resumo_cloudflare(dry_run=True):
    """Verifica status de tokens Cloudflare."""
    from cloudflare_tokens import verificar_conta

    if dry_run:
        contas = _contas_do_cofre()
        print(f"  [DRY RUN] Cloudflare: {len(contas)} contas no cofre")
        return {"modulo": "cloudflare", "dry_run": True, "total_contas": len(contas)}

    contas = _contas_do_cofre()
    resultados = []
    for email in contas:
        apelido = email.split("@")[0]
        print(f"  {apelido}...", end=" ", flush=True)
        r = verificar_conta(apelido)
        print(r["status"])
        resultados.append(r)
        time.sleep(2)
    return {"modulo": "cloudflare", "resultados": resultados}


def resumo_gemini(dry_run=True):
    """Chama o key_factory existente."""
    key_factory_dir = PROJECT_DIR / "key-factory"
    sys.path.insert(0, str(key_factory_dir))
    try:
        from key_factory import escanear_todas
        if dry_run:
            contas = _contas_do_cofre()
            print(f"  [DRY RUN] Gemini: {len(contas)} contas no cofre")
            return {"modulo": "gemini", "dry_run": True, "total_contas": len(contas)}
        return escanear_todas()
    except ImportError:
        return {"modulo": "gemini", "erro": "key_factory não importável"}


MODULOS = {
    "youtube":    {"func": resumo_youtube,    "desc": "Canais YouTube (verificar/criar)"},
    "cloudflare": {"func": resumo_cloudflare, "desc": "API Tokens Cloudflare"},
    "gemini":     {"func": resumo_gemini,     "desc": "API Keys Gemini (key-factory)"},
}


def executar(dry_run=True, modulos=None):
    print(f"[Fábrica de Credenciais] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Modo: {'DRY RUN' if dry_run else 'LIVE'}")
    print(f"  Módulos: {', '.join(modulos or MODULOS.keys())}\n")

    resultados = {}
    for nome, info in MODULOS.items():
        if modulos and nome not in modulos:
            continue
        print(f"--- {info['desc']} ---")
        r = info["func"](dry_run=dry_run)
        resultados[nome] = r
        print()

    status = {
        "executado_em": datetime.now(timezone.utc).isoformat(),
        "modo": "dry_run" if dry_run else "live",
        "resultados": resultados,
    }
    STATUS_FILE.write_text(json.dumps(status, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Status salvo em {STATUS_FILE}")
    return status


if __name__ == "__main__":
    args = sys.argv[1:]
    dry = "--live" not in args
    modulos = None
    if "--acao" in args:
        idx = args.index("--acao")
        if idx + 1 < len(args):
            modulos = [args[idx + 1]]

    executar(dry_run=dry, modulos=modulos)
