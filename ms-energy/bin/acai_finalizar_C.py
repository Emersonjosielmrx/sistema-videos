# -*- coding: utf-8 -*-
"""Finaliza reels dos arquivados na PALETA C (dona 05/11 13h): selo roxo profundo + cartão final dourado + trilha.
    D:\\veo\\venv\\Scripts\\python.exe acai_finalizar_C.py arquivado_xxx [arquivado_yyy ...]"""
import sys
from pathlib import Path

sys.path.insert(0, r"D:\ms-energy\bin")
import acai_arquivados as aa  # noqa: E402
from PIL import Image  # noqa: E402

FILA = Path(r"D:\ms-energy\videos\acai\fila_para_postar")
CARTAO = Path(r"D:\ms-energy\videos\acai\paletas\C_reels\1.jpg")

if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    c = Image.open(CARTAO)
    for nome in sys.argv[1:]:
        print(aa.finalizar(FILA / nome, (61, 15, 59), c), flush=True)
