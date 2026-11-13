"""limpar_relatorios_windows.py — apaga os relatórios de erro do Windows (dumps) que enchem o C: (dono 18/10/2026:
"crie um script pra ficar apagando esses relatórios periodicamente"). Só .dmp de LiveKernelReports, Minidump e
MEMORY.DMP com mais de 1 dia — só o PoW32kWatchdog de 30/09 tinha 2,8 GB. Precisa de admin: tarefa
`LimparRelatoriosWindows` roda como SYSTEM, todo dia 04:40.
"""
import time
from datetime import datetime
from pathlib import Path

PASTAS = [Path(r"C:\Windows\LiveKernelReports"), Path(r"C:\Windows\Minidump")]
SOLTOS = [Path(r"C:\Windows\MEMORY.DMP")]
IDADE = 24 * 3600
LOG = Path(__file__).resolve().parent / "limpar_relatorios_windows.log"


def main():
    limite, total, n = time.time() - IDADE, 0, 0
    dumps = [f for p in PASTAS if p.exists() for f in p.rglob("*.dmp")] + [f for f in SOLTOS if f.exists()]
    for f in dumps:
        try:
            st = f.stat()
            if st.st_mtime < limite:
                f.unlink()
                total += st.st_size
                n += 1
        except OSError:
            continue
    with open(LOG, "a", encoding="utf-8") as fh:
        fh.write(f"[{datetime.now():%d/%m %H:%M}] apagou {n} dumps, liberou {total / 1e6:.0f} MB\n")
    print(f"apagou {n} dumps, liberou {total / 1e6:.0f} MB")


if __name__ == "__main__":
    main()
