"""
Login automático em massa — abre 5 Chromes, um pra cada conta.
A usuária faz login em cada um, fecha, e os perfis ficam salvos.
Depois disso os scripts usam os perfis completos via CDP.
"""
import sys
import time
import subprocess
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "shared"))
from chrome_profile import CHROME_PATH, PROFILES_DIR, PORT_MAP, ACCOUNTS, test_session


def login_all():
    """Abre Chrome pra cada conta que ainda não tem sessão válida."""
    print("="*60)
    print("LOGIN EM MASSA — Perfis Chrome Completos")
    print("="*60)
    print(f"\nChrome: {CHROME_PATH}")
    print(f"Perfis: {PROFILES_DIR}\n")

    # Primeiro testa quais já funcionam
    need_login = []
    for acc in ACCOUNTS:
        profile_dir = PROFILES_DIR / acc
        if profile_dir.exists():
            r = test_session(acc)
            if r["valid"]:
                print(f"  {acc}: JÁ LOGADO ({r.get('email', '?')})")
                continue
        need_login.append(acc)

    if not need_login:
        print("\nTodas as contas já estão logadas!")
        return

    print(f"\n{len(need_login)} contas precisam de login:")
    for acc in need_login:
        print(f"  - {acc} ({ACCOUNTS[acc]})")

    print("\nAbrindo Chrome pra cada conta...")
    print("Faça login no Google em cada janela e depois FECHE a janela.\n")

    procs = []
    for acc in need_login:
        profile_dir = PROFILES_DIR / acc
        profile_dir.mkdir(parents=True, exist_ok=True)
        port = PORT_MAP[acc]

        cmd = [
            CHROME_PATH,
            f"--user-data-dir={profile_dir}",
            f"--remote-debugging-port={port}",
            "--no-first-run",
            "--no-default-browser-check",
            f"--profile-directory=Default",
            f"--window-name={acc}",
            f"https://accounts.google.com/signin/v2/identifier?flowName=GlifWebSignIn&flowEntry=AddSession&Email={ACCOUNTS[acc]}",
        ]

        print(f"  Abrindo {acc} (porta {port})...")
        proc = subprocess.Popen(cmd)
        procs.append((acc, proc))
        time.sleep(2)

    print(f"\n{'='*60}")
    print("Agora faça login em cada janela.")
    print("Quando terminar, feche TODAS as janelas do Chrome.")
    print(f"{'='*60}\n")

    # Espera todos os processos Chrome fecharem
    print("Esperando Chromes fecharem...")
    for acc, proc in procs:
        proc.wait()
        print(f"  {acc}: Chrome fechado")

    # Verifica quais funcionaram
    print("\nVerificando sessões...\n")
    ok = 0
    for acc in need_login:
        r = test_session(acc)
        if r["valid"]:
            print(f"  {acc}: LOGIN OK ({r.get('email', '?')})")
            ok += 1
        else:
            print(f"  {acc}: FALHA ({r.get('error', '?')})")

    print(f"\nResultado: {ok}/{len(need_login)} contas logadas com sucesso")


if __name__ == "__main__":
    login_all()
