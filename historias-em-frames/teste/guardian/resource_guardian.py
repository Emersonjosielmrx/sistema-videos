# -*- coding: utf-8 -*-
"""
====================================================================
 resource_guardian.py — Guardiao de recurso das 3 pistas
====================================================================

REGRA DE OURO (imutavel): a pista PROD nunca e desligada por este guardiao.
So o botao manual DESLIGAR_PROD derruba a prod. O guardiao so mexe em beta/teste.

O QUE FAZ:
    A cada ciclo (~60s) mede RAM livre e CPU. Conforme a folga, decide um NIVEL:
      ALTO  (folga)     -> pode rodar as 3 pistas (1+2+3)
      MEDIO (aperto)    -> desliga a TESTE (3), mantem prod+beta (1+2)
      BAIXO (critico)   -> desliga TESTE e BETA, mantem so a prod (1)
    Quando o recurso volta a sobrar, RELIGA beta/teste na ordem de prioridade,
    respeitando o que o usuario habilitou manualmente (override nos botoes).

COMO LIGA/DESLIGA UMA PISTA:
    Cada pista e uma pasta com launch_daemon.py e stop_auto_producer.py proprios.
    Ligar  = roda <dir>\\launch_daemon.py com o python do venv daquela pista.
    Desligar = roda <dir>\\stop_auto_producer.py.
    Se a pista esta ligada e ja tem o daemon vivo, nao faz nada (idempotente).

OVERRIDE MANUAL (os botoes do desktop escrevem aqui):
    guardian/state.json tem, por pista, "habilitada": true/false.
    - habilitada=false  -> usuario DESLIGOU na mao: guardiao NUNCA liga sozinho.
    - habilitada=true   -> usuario deixou disponivel: guardiao pode ligar/desligar
                           conforme o recurso (dentro da regra de ouro).
    A prod, mesmo habilitada, so e LIGADA pelo guardiao se o usuario a deixou on;
    e NUNCA e desligada pelo guardiao.

USO:
    python resource_guardian.py            # loop
    python resource_guardian.py --once     # 1 avaliacao (util pra teste)
    python resource_guardian.py --status   # so mostra nivel e estado atual
"""

import os
import sys
import json
import time
import argparse
import subprocess
from pathlib import Path
from datetime import datetime

try:
    import psutil
except ImportError:
    psutil = None

GUARDIAN_DIR = Path(__file__).resolve().parent
CONFIG_FILE = GUARDIAN_DIR / "guardian_config.json"
STATE_FILE = GUARDIAN_DIR / "state.json"
LOG_FILE = GUARDIAN_DIR / "guardian.log"


# ---------- log ----------
def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"- [{ts}] {msg}\n")
    except Exception:
        pass


# ---------- config / state ----------
def load_config():
    return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))


def load_state():
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    # default: prod habilitada, beta/teste habilitadas (guardiao gerencia)
    return {
        "habilitada": {"prod": True, "beta": True, "teste": True},
        "nivel_atual": None,
        "ciclos_no_nivel": 0,
        "ultimo_nivel_medido": None,
    }


def save_state(state):
    tmp = STATE_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(STATE_FILE)


# ---------- medicao ----------
def medir():
    """Retorna (ram_livre_gb, cpu_pct). Sem psutil, assume folga (nao mexe)."""
    if psutil is None:
        return 999.0, 0.0
    vm = psutil.virtual_memory()
    return vm.available / 1e9, psutil.cpu_percent(interval=1)


def classificar(ram_livre, cpu, cfg):
    """ALTO / MEDIO / BAIXO conforme thresholds."""
    if ram_livre < cfg["ram_livre_gb_baixo"]:
        return "BAIXO"
    if ram_livre < cfg["ram_livre_gb_alto"] or cpu >= cfg["cpu_pct_alto"]:
        return "MEDIO"
    return "ALTO"


# ---------- controle de pista ----------
def _pista_python(pista_dir):
    p = Path(pista_dir) / "venv" / "Scripts" / "python.exe"
    return str(p) if p.exists() else sys.executable


def pista_ligada(pista_dir):
    """True se o daemon da pista esta vivo (lock com PID vivo)."""
    lock = Path(pista_dir) / "workspace" / ".auto_producer.lock"
    if not lock.exists():
        return False
    try:
        pid = int(lock.read_text(encoding="utf-8").strip())
    except Exception:
        return False
    if psutil is not None:
        return psutil.pid_exists(pid)
    return True  # sem psutil, assume vivo se ha lock


def ligar_pista(nome, pista_dir):
    if pista_ligada(pista_dir):
        return False  # ja ligada
    launcher = Path(pista_dir) / "launch_daemon.py"
    if not launcher.exists():
        log(f"  ! {nome}: launch_daemon.py nao existe em {pista_dir} — pulando")
        return False
    try:
        subprocess.Popen([_pista_python(pista_dir), str(launcher)],
                         cwd=str(pista_dir),
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        log(f"  + LIGOU {nome}")
        return True
    except Exception as e:
        log(f"  ! falha ao ligar {nome}: {e}")
        return False


def desligar_pista(nome, pista_dir):
    if not pista_ligada(pista_dir):
        return False  # ja desligada
    stopper = Path(pista_dir) / "stop_auto_producer.py"
    if not stopper.exists():
        log(f"  ! {nome}: stop_auto_producer.py nao existe — pulando")
        return False
    try:
        subprocess.run([_pista_python(pista_dir), str(stopper)],
                      cwd=str(pista_dir), timeout=120,
                      stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        log(f"  - DESLIGOU {nome}")
        return True
    except Exception as e:
        log(f"  ! falha ao desligar {nome}: {e}")
        return False


# ---------- decisao ----------
def pistas_desejadas(nivel):
    """Quais pistas DEVEM rodar em cada nivel (a prod sempre entra na lista)."""
    if nivel == "ALTO":
        return {"prod", "beta", "teste"}
    if nivel == "MEDIO":
        return {"prod", "beta"}
    return {"prod"}  # BAIXO


def aplicar(nivel, cfg, state):
    """Liga/desliga pistas pra bater com o nivel, respeitando:
       - regra de ouro: prod nunca e desligada pelo guardiao;
       - override manual: pista com habilitada=false nunca e ligada."""
    desejadas = pistas_desejadas(nivel)
    habil = state.get("habilitada", {})
    # ordem: desliga primeiro (libera recurso), depois liga
    pistas = cfg["pistas"]
    # DESLIGAR: da menor prioridade (teste) pra maior, nunca a prod
    for nome in sorted(pistas, key=lambda n: -pistas[n]["prioridade"]):
        info = pistas[nome]
        if info.get("nunca_desliga"):
            continue  # prod: intocavel pelo automatico
        if nome not in desejadas:
            desligar_pista(nome, info["dir"])
    # LIGAR: da maior prioridade (prod) pra menor, so as habilitadas
    for nome in sorted(pistas, key=lambda n: pistas[n]["prioridade"]):
        info = pistas[nome]
        if nome in desejadas and habil.get(nome, True):
            ligar_pista(nome, info["dir"])


def status_texto(cfg, state):
    linhas = []
    for nome in sorted(cfg["pistas"], key=lambda n: cfg["pistas"][n]["prioridade"]):
        info = cfg["pistas"][nome]
        on = pista_ligada(info["dir"])
        hab = state.get("habilitada", {}).get(nome, True)
        prot = " [PROTEGIDA]" if info.get("nunca_desliga") else ""
        linhas.append(f"  {nome}: {'LIGADA' if on else 'desligada'} | "
                      f"{'habilitada' if hab else 'DESABILITADA (manual)'}{prot}")
    return "\n".join(linhas)


# ---------- loop ----------
def avaliar_uma_vez(cfg, state, agir=True):
    ram, cpu = medir()
    nivel = classificar(ram, cpu, cfg)

    # confirmacao: so age se o nivel se manteve por N ciclos (anti-flapping)
    if nivel == state.get("ultimo_nivel_medido"):
        state["ciclos_no_nivel"] = state.get("ciclos_no_nivel", 0) + 1
    else:
        state["ciclos_no_nivel"] = 1
        state["ultimo_nivel_medido"] = nivel

    confirmado = state["ciclos_no_nivel"] >= cfg.get("ciclos_confirmacao", 2)
    log(f"RAM livre {ram:.1f}GB | CPU {cpu:.0f}% | nivel={nivel} "
        f"(ciclo {state['ciclos_no_nivel']}, confirmado={confirmado})")

    if agir and confirmado and nivel != state.get("nivel_atual"):
        log(f"APLICANDO nivel {nivel} (era {state.get('nivel_atual')})")
        aplicar(nivel, cfg, state)
        state["nivel_atual"] = nivel

    save_state(state)
    return nivel


def main():
    ap = argparse.ArgumentParser(description="Guardiao de recurso das 3 pistas")
    ap.add_argument("--once", action="store_true", help="1 avaliacao e sai")
    ap.add_argument("--status", action="store_true", help="so mostra estado")
    args = ap.parse_args()

    cfg = load_config()
    state = load_state()

    if psutil is None:
        log("WARN: psutil indisponivel — guardiao nao consegue medir, assumindo folga")

    if args.status:
        ram, cpu = medir()
        print(f"RAM livre: {ram:.1f}GB | CPU: {cpu:.0f}% | "
              f"nivel classificado: {classificar(ram, cpu, cfg)}")
        print(f"nivel_atual aplicado: {state.get('nivel_atual')}")
        print("pistas:")
        print(status_texto(cfg, state))
        return

    if args.once:
        avaliar_uma_vez(cfg, state, agir=True)
        return

    log("GUARDIAO iniciado (prod PROTEGIDA — nunca desligada pelo automatico)")
    try:
        while True:
            cfg = load_config()      # relê config a cada ciclo (edicao vale na hora)
            avaliar_uma_vez(cfg, state, agir=True)
            time.sleep(cfg.get("intervalo_seg", 60))
    except KeyboardInterrupt:
        log("GUARDIAO parado pelo usuario")


if __name__ == "__main__":
    main()
