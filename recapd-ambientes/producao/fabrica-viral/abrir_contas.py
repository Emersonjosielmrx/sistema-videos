# -*- coding: utf-8 -*-
"""Abre Chrome com CDP para cada conta Flow disponivel.
Cada conta usa perfil e porta proprios. Roda UMA VEZ no inicio da sessao."""
import os, sys, time, subprocess, urllib.request

CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
BASE = os.path.dirname(os.path.abspath(__file__))
PROFILES_DIR = os.path.join(BASE, "chrome_profiles")
os.makedirs(PROFILES_DIR, exist_ok=True)

CONTAS = [
    {"nome": "seebotsia", "porta": 9224, "url": "https://labs.google/fx/tools/flow/project/16ecdb5d-2fc1-49f1-a87b-a82d038d76d8"},
    {"nome": "fabrica", "porta": 9226, "url": "https://labs.google/fx/pt/tools/flow/project/678f422c-afc6-463a-8898-35b9b9afe2db"},
    {"nome": "canalalucinaai", "porta": 9227, "url": "https://labs.google/fx/pt/tools/flow/project/771525ce-c5dd-46a0-a84b-4d9e334e07cb"},
    {"nome": "emersonjosiel649", "porta": 9228, "url": "https://labs.google/fx/pt/tools/flow/project/3341e220-7256-475c-9f0a-d9f8581a6fcc"},
]


def porta_viva(porta):
    try:
        r = urllib.request.urlopen(f"http://127.0.0.1:{porta}/json/version", timeout=2)
        return r.status == 200
    except Exception:
        return False


def abrir_conta(conta):
    if porta_viva(conta["porta"]):
        print(f"  {conta[chr(39)+'nome'+chr(39)]} (:{conta[chr(39)+'porta'+chr(39)]}) ja esta aberto")
        return True
    profile = os.path.join(PROFILES_DIR, conta["nome"])
    os.makedirs(profile, exist_ok=True)
    args = [
        CHROME,
        f"--remote-debugging-port={conta[chr(39)+'porta'+chr(39)]}",
        f"--user-data-dir={profile}",
        "--no-first-run", "--no-default-browser-check", "--disable-extensions",
        conta["url"],
    ]
    print(f"  Abrindo {conta[chr(39)+'nome'+chr(39)]} na porta {conta[chr(39)+'porta'+chr(39)]}...")
    subprocess.Popen(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(15):
        time.sleep(2)
        if porta_viva(conta["porta"]):
            print(f"  {conta[chr(39)+'nome'+chr(39)]} OK!")
            return True
    print(f"  AVISO: {conta[chr(39)+'nome'+chr(39)]} nao respondeu em 30s")
    return False


def main():
    print("[contas] Abrindo Chromes para contas Flow...")
    ok = 0
    for c in CONTAS:
        if abrir_conta(c):
            ok += 1
    print(f"[contas] {ok}/{len(CONTAS)} contas disponiveis")
    return ok


if __name__ == "__main__":
    main()
