# -*- coding: utf-8 -*-
"""Posta em sequência itens da fila do açaí, com intervalo (dona 05/11: "vá postando logo umas 5 pra ele ver")."""
import sys
import time
from pathlib import Path

sys.path.insert(0, r"D:\ms-energy\bin")
import acai_postar_fila as apf  # noqa: E402

FILA = Path(r"D:\ms-energy\videos\acai\fila_para_postar")

if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    intervalo = 180
    for i, nome in enumerate(sys.argv[1:]):
        if (FILA / nome / "postado.json").exists():
            print("já postado:", nome)
            continue
        if i:
            time.sleep(intervalo)
        try:
            print(nome, apf.postar(FILA / nome), flush=True)
        except Exception as e:  # noqa: BLE001
            print(f"falhou {nome}: {type(e).__name__}: {str(e)[:200]}", flush=True)
