# -*- coding: utf-8 -*-
"""
pista_control.py — Liga/desliga uma pista NA MAO (o que os botoes do desktop fazem).

Faz DUAS coisas de uma vez:
  1. Grava a intencao do usuario no guardian/state.json (campo habilitada[pista]).
     - LIGAR  -> habilitada=true  (o guardiao PODE gerenciar essa pista conforme recurso)
     - DESLIGAR -> habilitada=false (o guardiao NUNCA liga essa pista sozinho)
  2. Liga (launch_daemon.py) ou desliga (stop_auto_producer.py) o daemon da pista agora.

Regra de ouro: mesmo pela mao, a prod so e desligada se voce mandar explicitamente
DESLIGAR prod — o guardiao automatico nunca a desliga.

Uso:
    python pista_control.py <pista> <on|off>
    python pista_control.py prod on
    python pista_control.py teste off
"""
import sys
import json
import subprocess
from pathlib import Path

GUARDIAN_DIR = Path(__file__).resolve().parent
CONFIG_FILE = GUARDIAN_DIR / "guardian_config.json"
STATE_FILE = GUARDIAN_DIR / "state.json"


def _load_json(p, default):
    try:
        return json.loads(Path(p).read_text(encoding="utf-8"))
    except Exception:
        return default


def _pista_python(pista_dir):
    p = Path(pista_dir) / "venv" / "Scripts" / "python.exe"
    return str(p) if p.exists() else sys.executable


def set_habilitada(pista, valor):
    state = _load_json(STATE_FILE, {"habilitada": {}})
    state.setdefault("habilitada", {})[pista] = valor
    tmp = STATE_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(STATE_FILE)


def main():
    if len(sys.argv) < 3 or sys.argv[2].lower() not in ("on", "off"):
        print("uso: python pista_control.py <prod|beta|teste> <on|off>")
        sys.exit(2)

    pista = sys.argv[1].lower()
    acao = sys.argv[2].lower()

    cfg = _load_json(CONFIG_FILE, {})
    pistas = cfg.get("pistas", {})
    if pista not in pistas:
        print(f"pista desconhecida: {pista} (validas: {list(pistas)})")
        sys.exit(2)

    pista_dir = pistas[pista]["dir"]
    py = _pista_python(pista_dir)

    if acao == "on":
        set_habilitada(pista, True)
        launcher = Path(pista_dir) / "launch_daemon.py"
        print(f"LIGANDO {pista} ({pista_dir})...")
        subprocess.Popen([py, str(launcher)], cwd=str(pista_dir),
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print(f"  {pista} LIGADA e habilitada (guardiao pode gerenciar).")
    else:
        set_habilitada(pista, False)
        stopper = Path(pista_dir) / "stop_auto_producer.py"
        print(f"DESLIGANDO {pista} ({pista_dir})...")
        subprocess.run([py, str(stopper)], cwd=str(pista_dir), timeout=120,
                      stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print(f"  {pista} DESLIGADA e desabilitada (guardiao NAO liga sozinho).")
        if pistas[pista].get("nunca_desliga"):
            print("  (prod: so voce desliga; o guardiao automatico nunca a desliga)")


if __name__ == "__main__":
    main()
