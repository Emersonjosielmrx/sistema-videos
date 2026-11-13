#!/usr/bin/env python3
"""etapa.py - roda UMA etapa do postar_tudo_auto.bat com prazo (item BX-09 de D:\\veo\\docs\\PLANO_MELHORIAS_VEO.md).

Em 15/10 o TikTok travou ("nenhum Chrome disponivel"), a tarefa morreu (0x8007042B) e as etapas seguintes (Instagram,
limpar_usados, resumo da politica) nao rodaram. Aqui a etapa ganha um prazo: estourou -> encerra a arvore DELA
(taskkill /T so no PID que esta etapa abriu) e sai com 124, e o .bat segue para a proxima.

Uso: python etapa.py <prazo_min> <log> -- <comando ...>
"""
import subprocess
import sys
from datetime import datetime


def main():
    a = sys.argv[1:]
    if len(a) < 4 or a[2] != "--":
        print(__doc__)
        return 2
    prazo, log, cmd = float(a[0]) * 60, a[1], a[3:]
    with open(log, "a", encoding="utf-8", errors="replace") as f:
        p = subprocess.Popen(cmd, stdout=f, stderr=subprocess.STDOUT)
        try:
            return p.wait(timeout=prazo)
        except subprocess.TimeoutExpired:
            subprocess.run(["taskkill", "/T", "/F", "/PID", str(p.pid)], capture_output=True)
            f.write(f"\n[{datetime.now():%d/%m %H:%M}] ETAPA ENCERRADA: passou de {a[0]} min (etapa.py)\n")
            return 124


if __name__ == "__main__":
    sys.exit(main())
