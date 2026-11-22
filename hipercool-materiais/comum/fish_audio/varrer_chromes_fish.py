"""varrer_chromes_fish.py — tarefa VarrerChromesFish (15 em 15 min, oculta). 21/11 dona ("há uma grande quantidade de
Chromes abertos muito sem nada; elas não fecham; só deveria ter um script pra fechar quando acabar").

Por que existe: a fábrica (fabrica_fish.py) fecha a conta ociosa, mas (1) quando o Chrome demora > 45 s pra abrir (PC
lento) a fábrica desiste e o Chrome abre depois sem dono; (2) a fábrica ENCERRA quando fica ociosa e reinicia por
outro processo, e os Chromes da anterior ficam; (3) o varredor de dentro da fábrica dava TimeoutExpired (o PowerShell
levava > 240 s pra listar processos com o PC a 100%). Aqui: lista pelo wmic (rápido) e fecha todo Chrome com a ponte
do Fish (--proxy-server=127.0.0.1:185xx) aberto há mais de IDADE_MIN (20) min cuja porta CDP não está em uso pela
fábrica agora (GET :9397/estado). Nunca toca Chrome sem a ponte do Fish (Kaggle, Flow, cofre, o Chrome da dona).
VARRER_FISH=0 desliga.
"""
import json
import os
import re
import subprocess
import urllib.request
from datetime import datetime
from pathlib import Path

LOG = Path(__file__).resolve().parent / "fabrica_fish.log"
IDADE_MIN = int(os.environ.get("FISH_ORFAO_MIN", "20"))
SEM_JANELA = 0x08000000


def log(msg):
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(f"[{datetime.now():%d/%m %H:%M:%S}] [varredor] {msg}\n")


def portas_da_fabrica():
    try:
        with urllib.request.urlopen("http://127.0.0.1:9397/estado", timeout=10) as r:
            d = json.loads(r.read())
    except Exception:  # noqa: BLE001 — fábrica fora = nenhuma conta em uso
        return set()
    out = set()
    for c in (d.get("contas") or {}).values():
        if c.get("porta"):
            out.add(int(c["porta"]))
    try:  # a fábrica anota os Chromes que abriu
        ab = json.loads((LOG.parent / "fabrica_abertos.json").read_text(encoding="utf-8"))
        if (d.get("contas") or {}):
            out |= {int(p) for p in ab}
    except (OSError, ValueError):
        pass
    return out


def main():
    if os.environ.get("VARRER_FISH", "1") == "0":
        return
    r = subprocess.run(["wmic", "process", "where", "name='chrome.exe'", "get",
                        "ProcessId,CreationDate,CommandLine", "/format:csv"],
                       capture_output=True, text=True, timeout=120, creationflags=SEM_JANELA,
                       encoding="utf-8", errors="ignore")
    em_uso = portas_da_fabrica()
    agora = datetime.now()
    fechados = 0
    for linha in r.stdout.splitlines():
        if "proxy-server=127.0.0.1:185" not in linha or "--type=" in linha:
            continue
        partes = linha.rsplit(",", 2)
        if len(partes) < 3:
            continue
        cmd, criado, pid = partes[0], partes[1].strip(), partes[2].strip()
        try:
            idade = (agora - datetime.strptime(criado[:14], "%Y%m%d%H%M%S")).total_seconds() / 60
        except ValueError:
            continue
        m = re.search(r"remote-debugging-port=(\d+)", cmd)
        porta = int(m.group(1)) if m else None
        if idade < IDADE_MIN or porta in em_uso:
            continue
        subprocess.run(["taskkill", "/PID", pid, "/T", "/F"], capture_output=True, creationflags=SEM_JANELA)
        fechados += 1
        log(f"fechei Chrome órfão do Fish (porta {porta}, {idade:.0f} min aberto)")
    if fechados:
        log(f"{fechados} Chrome(s) órfão(s) fechado(s)")


if __name__ == "__main__":
    main()
