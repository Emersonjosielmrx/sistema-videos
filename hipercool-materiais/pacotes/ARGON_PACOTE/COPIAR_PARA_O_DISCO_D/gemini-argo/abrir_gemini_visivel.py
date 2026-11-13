#!/usr/bin/env python3
import sys, os, time, subprocess, json
from pathlib import Path

sys.path.insert(0, r"D:\logins-google")
sys.path.insert(0, r"D:\postador-de-videos\bin\netbooks")
import cofre
import chrome_conta

URL_GEMINI = "https://gemini.google.com/app"

CONTAS_TODAS = [
    # 17 contas que nao abriram com cookies
    "conta_exemplo", "conta_exemplo", "conta_exemplo", "conta_exemplo",
    "conta_exemplo", "conta_exemplo", "conta_exemplo", "conta_exemplo",
    "conta_exemplo", "conta_exemplo", "conta_exemplo",
    "conta_exemplo", "conta_exemplo", "conta_exemplo", "conta_exemplo",
    "conta_exemplo", "conta_exemplo",
    # 8 contas de idade / sem resposta
    "conta_exemplo", "conta_exemplo", "conta_exemplo", "conta_exemplo",
    "conta_exemplo", "conta_exemplo", "conta_exemplo",
    "conta_exemplo"
]

def abrir_uma(apelido, pos_x=60, pos_y=40):
    chrome_conta._liberar_ram()
    email, e = cofre.conta(apelido)
    porta = e["porta"]
    pasta = Path(e["pasta"])
    pasta.mkdir(parents=True, exist_ok=True)

    cmd = [
        cofre.CHROME,
        f"--remote-debugging-port={porta}",
        f"--user-data-dir={pasta}",
        f"--profile-directory={e.get('sub') or 'Default'}",
        *cofre.FLAGS,
        f"--window-position={pos_x},{pos_y}",
        "--window-size=1200,850",
        URL_GEMINI
    ]
    proc = subprocess.Popen(cmd)
    print(f">> Aberta na tela: {email} (porta {porta}, pos {pos_x},{pos_y})")
    time.sleep(1)
    return porta

if __name__ == "__main__":
    contas = sys.argv[1:] if len(sys.argv) > 1 else []
    for idx, c in enumerate(contas):
        # Deslocamento em cascata para as janelas ficarem visíveis lado a lado ou em escada
        px = 40 + (idx % 4) * 50
        py = 30 + (idx % 4) * 40
        abrir_uma(c, px, py)
        time.sleep(1.5)
