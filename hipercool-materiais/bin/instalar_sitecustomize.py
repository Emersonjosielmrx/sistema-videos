# -*- coding: utf-8 -*-
r"""instalar_sitecustomize.py — copia comum\sitecustomize.py para o site-packages de cada Python/venv que as tarefas usam
(regra da dona: nenhuma janela na tela). Rode de novo quando criar um venv novo.
    python D:\hipercool-materiais\bin\instalar_sitecustomize.py
"""
import shutil
import sys
from pathlib import Path

FONTE = Path(r"D:\hipercool-materiais\comum\sitecustomize.py")
ALVOS = [r"C:\Users\Haylla\AppData\Local\Programs\Python\Python313\Lib\site-packages",
         r"D:\veo\venv\Lib\site-packages", r"D:\recapd-ambientes\producao\venv\Lib\site-packages",
         r"D:\hipercool-videos\venv\Lib\site-packages", r"D:\manhwa-react\.venv\Lib\site-packages",
         r"D:\historias-em-frames\venv\Lib\site-packages", r"D:\postador-de-videos\venv\Lib\site-packages",
         r"D:\claude-code-video\venv\Lib\site-packages", r"D:\hipercool-producao\venv\Lib\site-packages"]


def main():
    for a in ALVOS:
        d = Path(a)
        if not d.is_dir():
            continue
        alvo = d / "sitecustomize.py"
        if alvo.exists() and "Fable" not in alvo.read_text("utf-8", errors="ignore"):
            print(f"  {a}: já tem um sitecustomize de outro dono — NÃO sobrescrito")
            continue
        shutil.copy2(FONTE, alvo)
        print(f"  {a}: ok")


if __name__ == "__main__":
    main()
