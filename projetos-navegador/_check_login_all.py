"""Verifica quais contas Chrome ainda estão logadas no YouTube.
Testa 3 contas por vez (para não sobrecarregar) e reporta o status."""
import sys, os, io, time, json, socket, subprocess

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

sys.path.insert(0, "D:/projetos-navegador")
sys.path.insert(0, "D:/projetos-navegador/shared")
os.chdir("D:/projetos-navegador")

from shared.google_session import PORT_MAP, get_profile_dir, CHROME_PATH

RESULTS = {}
TEST_URL = "https://www.youtube.com/"
BATCH_SIZE = 2
TIMEOUT_CHROME = 15


def check_account(account, port):
    """Lança Chrome com perfil, abre YouTube, verifica login."""
    profile = str(get_profile_dir(account))

    if not os.path.exists(profile):
        return "NO_PROFILE"

    # Kill qualquer chrome nessa porta
    subprocess.run(["taskkill", "/F", "/FI", f"WINDOWTITLE eq *{port}*"],
                   capture_output=True, timeout=5)
    # Também tenta por porta
    try:
        subprocess.run(
            f'for /f "tokens=5" %a in (\'netstat -aon ^| findstr ":{port}"\') do taskkill /F /PID %a',
            shell=True, capture_output=True, timeout=5
        )
    except:
        pass
    time.sleep(1)

    args = [
        CHROME_PATH,
        f"--user-data-dir={profile}",
        f"--remote-debugging-port={port}",
        "--headless=new",
        "--no-first-run",
        "--disable-gpu",
        "--mute-audio",
        "--disable-software-rasterizer",
        "--disable-dev-shm-usage",
        "--disable-extensions",
        "--disable-background-networking",
        "--no-sandbox",
        "--window-size=800,600",
        "about:blank",
    ]
    proc = subprocess.Popen(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # Wait for chrome
    ready = False
    for i in range(TIMEOUT_CHROME):
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

        page.goto(TEST_URL, timeout=20000, wait_until="domcontentloaded")
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
                'yt-img-shadow.ytd-topbar-menu-button-renderer img, ' +
                'button#avatar-btn'
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


# Pegar contas que têm perfil
accounts_with_profile = []
for acct, port in sorted(PORT_MAP.items(), key=lambda x: x[1]):
    profile_path = get_profile_dir(acct)
    if profile_path.exists():
        accounts_with_profile.append((acct, port))

print(f"Total contas com perfil Chrome: {len(accounts_with_profile)}")
print(f"Testando em batches de {BATCH_SIZE}...\n")

logged = []
not_logged = []
errors = []

for i in range(0, len(accounts_with_profile), BATCH_SIZE):
    batch = accounts_with_profile[i:i+BATCH_SIZE]
    for acct, port in batch:
        print(f"  [{i+1+batch.index((acct,port))}/{len(accounts_with_profile)}] {acct}:{port} ... ", end="", flush=True)
        status = check_account(acct, port)
        print(status)
        RESULTS[acct] = status

        if status == "LOGGED_IN":
            logged.append(acct)
        elif status == "NOT_LOGGED_IN":
            not_logged.append(acct)
        else:
            errors.append((acct, status))

    # Pequena pausa entre batches
    if i + BATCH_SIZE < len(accounts_with_profile):
        time.sleep(2)

# Summary
print(f"\n{'='*60}")
print(f"RESULTADO FINAL")
print(f"{'='*60}")
print(f"LOGADAS:       {len(logged)}")
print(f"NAO LOGADAS:   {len(not_logged)}")
print(f"ERROS:         {len(errors)}")
print(f"{'='*60}")

if logged:
    print(f"\nContas LOGADAS ({len(logged)}):")
    for a in logged:
        print(f"  ✓ {a}")

if not_logged:
    print(f"\nContas NAO LOGADAS ({len(not_logged)}):")
    for a in not_logged:
        print(f"  ✗ {a}")

if errors:
    print(f"\nErros ({len(errors)}):")
    for a, e in errors:
        print(f"  ? {a}: {e}")

# Salvar resultado
result_path = "D:/projetos-navegador/_login_status.json"
with open(result_path, "w", encoding="utf-8") as f:
    json.dump(RESULTS, f, indent=2, ensure_ascii=False)
print(f"\nResultado salvo em {result_path}")
