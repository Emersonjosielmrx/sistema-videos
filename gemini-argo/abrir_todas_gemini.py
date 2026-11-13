#!/usr/bin/env python3
"""
abrir_todas_gemini.py — Abre todas as 25 contas no Gemini visivelmente na tela
"""
import sys, os, time, subprocess, json
from pathlib import Path

sys.path.insert(0, r"D:\logins-google")
sys.path.insert(0, r"D:\postador-de-videos\bin\netbooks")
import cofre
import chrome_conta

URL_GEMINI = "https://gemini.google.com/app"

CONTAS = [
    "canalanimescomia",
    "canalhistoriacomia",
    "contapessoal",
    "emersonjosiel0",
    "emersonjosiel2027",
    "emersonjosiel2031",
    "emersonjosiel2032",
    "entrevistacomia",
    "fabricadeautomacoesia",
    "gabriellyvitoriaisabelaaraujo",
    "inovaremanhwaverse",
    "inovaremanhwaverse2",
    "jogoscomia",
    "mundosolar1995",
    "rezaulkarimul355",
    "seebotsia",
    "simonerebecaluizasilva",
    "emersonjosiel2026",
    "en1653964",
    "inovaremanhwaversefrench",
    "inovaremanhwaversehindi",
    "inovaremanhwaverseind",
    "inovaremanhwaverseita",
    "inovaremanhwaverseviet",
    "maiteanajessicajesus"
]

def main():
    print(f"Iniciando abertura de {len(CONTAS)} contas no Gemini...")
    chrome_conta._liberar_ram()

    abertas = 0
    for idx, c in enumerate(CONTAS, 1):
        email, e = cofre.conta(c)
        porta = e["porta"]
        pasta = Path(e["pasta"])
        pasta.mkdir(parents=True, exist_ok=True)

        # Posição em cascata
        offset_x = 30 + ((idx - 1) % 8) * 35
        offset_y = 20 + ((idx - 1) % 8) * 30

        # Se a porta já estiver aberta, pula ou só loga
        if cofre._cdp_vivo(porta):
            print(f"[{idx:02d}/{len(CONTAS)}] {email} já estava aberta na porta {porta}")
            continue

        cmd = [
            cofre.CHROME,
            f"--remote-debugging-port={porta}",
            f"--user-data-dir={pasta}",
            f"--profile-directory={e.get('sub') or 'Default'}",
            *cofre.FLAGS,
            f"--window-position={offset_x},{offset_y}",
            "--window-size=1200,800",
            URL_GEMINI
        ]

        subprocess.Popen(cmd)
        abertas += 1
        print(f"[{idx:02d}/{len(CONTAS)}] Aberta: {email} (porta {porta})")

        # Intervalo para não dar pico de CPU
        time.sleep(1.0)

        # Enxugar memória a cada 4 janelas
        if abertas % 4 == 0:
            try:
                chrome_conta._enxugar_win()
                livre = chrome_conta._ram_livre_mb()
                print(f"  --> RAM livre no momento: {livre} MB")
            except Exception:
                pass

    chrome_conta._enxugar_win()
    print(f"\nFinalizado! Total abertas nesta rodada: {abertas}. RAM livre final: {chrome_conta._ram_livre_mb()} MB")

if __name__ == "__main__":
    main()
