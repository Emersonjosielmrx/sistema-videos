"""relancar_login_asus.py — 14/11 dona ("o Asus foi reiniciado; tente a cada 20 min reiniciar a fila de login lá,
muitos já foram logados"). Tarefa ReLoginAsus (20/20 min, oculta): se o monitor login_em_lote.py asus não está rodando
e ainda falta conta, relança com 1 janela por vez (o próprio lote pula quem já logou).
Desligar: env RELOGIN_ASUS=0 ou desativar a tarefa.
"""
import os
import subprocess
import sys
from pathlib import Path

BIN = Path(__file__).resolve().parent
LOG = BIN.parent.parent / "logs" / "relancar_login_asus.log"


def rodando():
    r = subprocess.run(["powershell", "-NoProfile", "-c",
                        "Get-CimInstance Win32_Process -Filter \"Name like 'python%'\" | "
                        "? { $_.CommandLine -like '*login_em_lote.py*asus*' -and $_.CommandLine -notlike '*estado*' } | "
                        "Measure-Object | % Count"], capture_output=True, text=True, timeout=90,
                       creationflags=0x08000000)
    return (r.stdout.strip() or "0") != "0"


def main():
    if os.environ.get("RELOGIN_ASUS") == "0":
        return
    import time
    if rodando():
        msg = "lote do Asus já rodando"
    else:
        subprocess.Popen([sys.executable, "-X", "utf8", str(BIN / "login_em_lote.py"), "asus", "1"],
                         cwd=str(BIN.parent.parent), creationflags=0x08000000 | 0x00000008,
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        msg = "lote do Asus relançado (1 janela)"
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(f"[{time.strftime('%d/%m %H:%M')}] {msg}\n")


if __name__ == "__main__":
    main()
