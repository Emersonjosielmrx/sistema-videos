# -*- coding: utf-8 -*-
# Roda no PC1, SO LEITURA: mostra onde a abertura (resumo) escolhe memes e onde o uso e registrado.
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BIN = Path(r"D:\recapd-ambientes\producao\bin")


def mostra(arq, padrao, antes, depois):
    linhas = (BIN / arq).read_text(encoding="utf-8").splitlines()
    for i, l in enumerate(linhas):
        if re.search(padrao, l):
            print(f"--- {arq}:{i + 1}")
            for j in range(max(0, i - antes), min(len(linhas), i + depois)):
                print(f"{j + 1:4} {linhas[j][:190]}")
            return
    print(f"--- {arq}: '{padrao}' nao achado")


mostra("anime-pipeline.py", r"novos_dir = next\(", 3, 16)
mostra("anime-pipeline.py", r"registrar_uso", 3, 4)
mostra("memes_visuais.py", r"^def _ficha", 0, 4)
mostra("memes_visuais.py", r"^def catalogo", 0, 3)
