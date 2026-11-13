"""
Chrome Profile Manager — usa perfis Chrome completos em vez de cookies isolados.
O Google invalida sessões que só têm cookies (detecta novo device/fingerprint).
Com perfil completo, tudo é preservado: cookies, localStorage, IndexedDB, ServiceWorker.
"""
import json
import os
import subprocess
import time
from pathlib import Path
from contextlib import contextmanager

PROFILES_DIR = Path("D:/logins-google/chrome-profiles")
PROFILES_DIR.mkdir(parents=True, exist_ok=True)

ACCOUNTS = {
    "fabrica": "fabricadeautomacoesia@gmail.com",
    "mundosolar1995": "mundosolar1995@gmail.com",
    "canalalucinaai": "canalalucinaai@gmail.com",
    "seebotsia": "seebotsia@gmail.com",
    "emersonjosiel649": "emersonjosiel649@gmail.com",
    "gameoftroneskingsroadbrasil": "gameoftroneskingsroadbrasil@gmail.com",
    "inovaremanhwaversethai": "inovaremanhwaversethai@gmail.com",
    "inovaremanhwaverseviet": "inovaremanhwaverseviet@gmail.com",
    "inovaremanhwaversehindi": "inovaremanhwaversehindi@gmail.com",
    "inovaremanhwaverserussian": "inovaremanhwaverserussian@gmail.com",
    "inovaremanhwaversefrench": "inovaremanhwaversefrench@gmail.com",
    "inovaremanhwaverseita": "inovaremanhwaverseita@gmail.com",
    "inovaremanhwaverseesp": "inovaremanhwaverseesp@gmail.com",
    "inovaremanhwaverseind": "inovaremanhwaverseind@gmail.com",
    "inovaremanhwaverseing": "inovaremanhwaverseing@gmail.com",
    "inovaremanhwaverse": "inovaremanhwaverse@gmail.com",
    "inovaremanhwabr": "inovaremanhwabr@gmail.com",
    "mentoriaiapro": "mentoriaiapro@gmail.com",
    "msenergypara": "msenergypara@gmail.com",
}

PORT_MAP = {
    "fabrica": 9301,
    "mundosolar1995": 9302,
    "canalalucinaai": 9303,
    "seebotsia": 9304,
    "emersonjosiel649": 9305,
    "gameoftroneskingsroadbrasil": 9310,
    "inovaremanhwaversethai": 9311,
    "inovaremanhwaverseviet": 9312,
    "inovaremanhwaversehindi": 9313,
    "inovaremanhwaverserussian": 9314,
    "inovaremanhwaversefrench": 9315,
    "inovaremanhwaverseita": 9316,
    "inovaremanhwaverseesp": 9317,
    "inovaremanhwaverseind": 9318,
    "inovaremanhwaverseing": 9319,
    "inovaremanhwaverse": 9320,
    "inovaremanhwabr": 9321,
    "mentoriaiapro": 9322,
    "msenergypara": 9323,
}

CHROME_PATH = None
for p in [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
]:
    if os.path.exists(p):
        CHROME_PATH = p
        break


def get_profile_dir(account: str) -> Path:
    return PROFILES_DIR / account


def profile_exists(account: str) -> bool:
    return (get_profile_dir(account) / "Default" / "Cookies").exists()


def launch_chrome_for_login(account: str):
    """Abre Chrome com perfil dedicado pra login manual."""
    if not CHROME_PATH:
        raise RuntimeError("Chrome não encontrado")

    profile_dir = get_profile_dir(account)
    profile_dir.mkdir(parents=True, exist_ok=True)
    port = PORT_MAP[account]

    cmd = [
        CHROME_PATH,
        f"--user-data-dir={profile_dir}",
        f"--remote-debugging-port={port}",
        "--no-first-run",
        "--no-default-browser-check",
        f"--profile-directory=Default",
        "https://myaccount.google.com",
    ]

    print(f"Abrindo Chrome pra {account} (porta {port})...")
    print(f"  Perfil: {profile_dir}")
    print(f"  Faça login no Google e depois feche a janela.")
    subprocess.Popen(cmd)
    return port


@contextmanager
def chrome_cdp(account: str, headless: bool = True):
    """Conecta via CDP ao Chrome com perfil completo.

    Se headless=True, lança headless Chrome com perfil existente.
    Se headless=False, espera Chrome já aberto na porta do account.
    """
    from playwright.sync_api import sync_playwright

    profile_dir = get_profile_dir(account)
    port = PORT_MAP[account]

    if headless:
        if not CHROME_PATH:
            raise RuntimeError("Chrome não encontrado")

        chrome_proc = subprocess.Popen([
            CHROME_PATH,
            f"--user-data-dir={profile_dir}",
            f"--remote-debugging-port={port}",
            "--headless=new",
            "--no-first-run",
            "--no-default-browser-check",
            "--disable-gpu",
            "--disable-software-rasterizer",
            "about:blank",
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(3)
    else:
        chrome_proc = None

    try:
        with sync_playwright() as p:
            browser = p.chromium.connect_over_cdp(f"http://127.0.0.1:{port}")
            context = browser.contexts[0]
            page = context.pages[0] if context.pages else context.new_page()
            try:
                yield page, context, browser
            finally:
                browser.close()
    finally:
        if chrome_proc:
            chrome_proc.terminate()
            try:
                chrome_proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                chrome_proc.kill()


def test_session(account: str) -> dict:
    """Testa se a sessão do perfil Chrome funciona."""
    profile_dir = get_profile_dir(account)
    if not profile_dir.exists():
        return {"account": account, "valid": False, "error": "no_profile"}

    try:
        with chrome_cdp(account, headless=True) as (page, ctx, browser):
            page.goto("https://myaccount.google.com", timeout=30000, wait_until="domcontentloaded")
            time.sleep(3)

            url = page.url
            if "accounts.google.com" in url and ("signin" in url.lower() or "ServiceLogin" in url):
                return {"account": account, "valid": False, "error": "redirected_to_login"}

            if "myaccount.google.com" in url:
                email = None
                try:
                    el = page.query_selector('[data-email]')
                    if el:
                        email = el.get_attribute("data-email")
                except Exception:
                    pass
                return {"account": account, "valid": True, "email": email}

            return {"account": account, "valid": False, "error": f"unexpected_url: {url[:100]}"}

    except Exception as e:
        return {"account": account, "valid": False, "error": str(e)}


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "login":
        acc = sys.argv[2] if len(sys.argv) > 2 else "fabrica"
        launch_chrome_for_login(acc)
    elif len(sys.argv) > 1 and sys.argv[1] == "test":
        acc = sys.argv[2] if len(sys.argv) > 2 else None
        accs = [acc] if acc else list(ACCOUNTS.keys())
        for a in accs:
            r = test_session(a)
            status = "OK" if r["valid"] else f"FALHA: {r.get('error')}"
            print(f"  {a}: {status}")
    else:
        print("Uso:")
        print("  python chrome_profile.py login [conta]   — abre Chrome pra login manual")
        print("  python chrome_profile.py test [conta]    — testa sessão")
