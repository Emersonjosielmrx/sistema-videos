"""Teste rapido: verifica login de 5 contas pra dimensionar o problema."""
import sys, os, io, time, json, socket, subprocess

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

sys.path.insert(0, "D:/projetos-navegador")
sys.path.insert(0, "D:/projetos-navegador/shared")
os.chdir("D:/projetos-navegador")

from shared.google_session import PORT_MAP, get_profile_dir, CHROME_PATH

# 5 contas diversas pra amostrar
SAMPLE = [
    "inovaremanhwaverse",
    "fabrica",
    "emersonjosiel649",
    "canalalucinaai",
    "inovaremanhwabr",
]


def check_account(account):
    port = PORT_MAP[account]
    profile = str(get_profile_dir(account))
    if not os.path.exists(profile):
        return "NO_PROFILE"

    subprocess.run(["taskkill", "/F", "/FI", f"WINDOWTITLE eq *{port}*"],
                   capture_output=True, timeout=5)
    time.sleep(1)

    args = [
        CHROME_PATH,
        f"--user-data-dir={profile}",
        f"--remote-debugging-port={port}",
        "--headless=new", "--no-first-run", "--disable-gpu", "--mute-audio",
        "--disable-software-rasterizer", "--disable-dev-shm-usage",
        "--disable-extensions", "--no-sandbox", "--window-size=800,600",
        "about:blank",
    ]
    proc = subprocess.Popen(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    ready = False
    for i in range(15):
        time.sleep(1)
        try:
            s = socket.create_connection(("127.0.0.1", port), timeout=2)
            s.close()
            ready = True
            break
        except:
            continue

    if not ready:
        proc.kill()
        return "CHROME_TIMEOUT"

    try:
        from playwright.sync_api import sync_playwright
        pw = sync_playwright().start()
        browser = pw.chromium.connect_over_cdp(f"http://127.0.0.1:{port}")
        ctx = browser.contexts[0] if browser.contexts else browser.new_context()
        page = ctx.new_page()

        page.goto("https://www.youtube.com/", timeout=20000, wait_until="domcontentloaded")
        time.sleep(3)

        status = page.evaluate("""() => {
            const signin = document.querySelector(
                'a[href*="accounts.google.com"], ' +
                'ytd-button-renderer.style-suggestive a[href*="ServiceLogin"], ' +
                'a[href*="ServiceLogin"]'
            );
            if (signin) return 'NOT_LOGGED_IN';
            const avatar = document.querySelector(
                '#avatar-btn, ' +
                'yt-img-shadow.ytd-topbar-menu-button-renderer img'
            );
            if (avatar) return 'LOGGED_IN';
            return 'UNKNOWN';
        }""")

        page.close()
        browser.close()
        pw.stop()
        proc.kill()
        return status
    except Exception as e:
        proc.kill()
        return f"ERROR: {str(e)[:80]}"


print("=== Amostra de 5 contas ===\n")
for acct in SAMPLE:
    print(f"{acct}: ", end="", flush=True)
    result = check_account(acct)
    print(result)
    time.sleep(2)

print("\nDone.")
