"""
scan_new_channels.py — Descobre quais contas novas têm canal YouTube ativo
e puxa seus vídeos/shorts pra adicionar ao all_channel_videos_full.json.

Usa Playwright headless pra acessar youtube.com/@handle e listar vídeos.
"""
import json, time, sys, random
from pathlib import Path
from playwright.sync_api import sync_playwright

sys.path.append("D:/projetos-navegador/shared")
from google_session import ACCOUNTS, PORT_MAP, get_profile_dir

ALL_VIDEOS_FILE = Path("D:/projetos-navegador/all_channel_videos_full.json")

# Canais que já estão no arquivo (não precisam ser escaneados)
with open(ALL_VIDEOS_FILE, "r", encoding="utf-8") as f:
    existing = json.load(f)
EXISTING_HANDLES = set(existing.keys())

# Handles alternativos que já estão cobertos (nome do canal != nome da conta)
ALREADY_COVERED = {
    "fabricadeautomacoesia",  # está como "fabricadeautomacoesia" no json
    "inovaremanhwaversefrench",  # está como "inovaremanhwafrench" no json
    "inovaremanhwaverseing",  # está como "inovaremanhwaverseeng" no json
}

# Contas que potencialmente têm canal (excluir as que já estão na lista)
NEW_ACCOUNTS = [
    acc for acc in ACCOUNTS.keys()
    if acc not in EXISTING_HANDLES
    and acc not in ALREADY_COVERED
]

print(f"Contas a escanear: {len(NEW_ACCOUNTS)}")
print(NEW_ACCOUNTS)


def scan_channel(page, handle):
    """
    Acessa youtube.com/@handle e puxa vídeos e shorts.
    Retorna dict {"videos": [...], "shorts": [...], "status": "ok/empty/blocked"}
    """
    result = {"videos": [], "shorts": [], "status": "unknown"}

    # Tenta acessar a página do canal
    try:
        page.goto(f"https://www.youtube.com/@{handle}/videos", timeout=20000, wait_until="domcontentloaded")
        time.sleep(3)

        # Verifica se canal existe
        content = page.content()
        if "Esta página não está disponível" in content or "This page isn" in content or "404" in page.title():
            result["status"] = "not_found"
            return result

        if "foi encerrad" in content or "terminated" in content or "suspended" in content:
            result["status"] = "blocked"
            return result

        # Pega URLs de vídeos
        videos = page.evaluate("""() => {
            const links = document.querySelectorAll('a#video-title-link, a.yt-simple-endpoint[href*="/watch"]');
            return [...new Set([...links].map(a => a.href).filter(h => h.includes('/watch')))];
        }""")
        result["videos"] = videos[:30]  # Máx 30 vídeos

        # Agora pega shorts
        page.goto(f"https://www.youtube.com/@{handle}/shorts", timeout=20000, wait_until="domcontentloaded")
        time.sleep(3)

        shorts = page.evaluate("""() => {
            const links = document.querySelectorAll('a[href*="/shorts/"]');
            return [...new Set([...links].map(a => a.href).filter(h => h.includes('/shorts/')))];
        }""")
        result["shorts"] = shorts[:50]  # Máx 50 shorts

        if result["videos"] or result["shorts"]:
            result["status"] = "ok"
        else:
            result["status"] = "empty"

    except Exception as e:
        result["status"] = f"error: {str(e)[:60]}"

    return result


def main():
    # Usa porta isolada (9399) pra não conflitar com o mega_engage rodando
    # e perfil temporário pra não prender nenhuma conta
    import subprocess, tempfile
    CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    SCAN_PORT = 9399
    temp_profile = Path("D:/projetos-navegador/_scan_temp_profile")
    temp_profile.mkdir(exist_ok=True)

    chrome_args = [
        CHROME_PATH,
        f"--user-data-dir={temp_profile}",
        f"--remote-debugging-port={SCAN_PORT}",
        "--headless=new", "--no-first-run", "--disable-gpu", "--mute-audio",
        "--disable-software-rasterizer",
        "about:blank"
    ]
    proc = subprocess.Popen(chrome_args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(6)
    port = SCAN_PORT

    results = {}

    try:
        with sync_playwright() as p:
            browser = p.chromium.connect_over_cdp(f"http://127.0.0.1:{port}")
            ctx = browser.contexts[0]
            ctx.set_default_timeout(15000)
            page = ctx.pages[0] if ctx.pages else ctx.new_page()

            for handle in NEW_ACCOUNTS:
                print(f"Escaneando @{handle}...", end=" ", flush=True)
                try:
                    data = scan_channel(page, handle)
                except Exception as e:
                    # Se o browser morreu (taskkill do mega_engage), relança
                    print(f"reconectando... ", end="", flush=True)
                    try:
                        browser.close()
                    except:
                        pass
                    proc.terminate()
                    time.sleep(3)
                    proc = subprocess.Popen(chrome_args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    time.sleep(6)
                    browser = p.chromium.connect_over_cdp(f"http://127.0.0.1:{port}")
                    ctx = browser.contexts[0]
                    page = ctx.pages[0] if ctx.pages else ctx.new_page()
                    data = scan_channel(page, handle)

                results[handle] = data
                print(f"{data['status']} | {len(data['videos'])}v + {len(data['shorts'])}s")
                time.sleep(random.uniform(2, 4))

            browser.close()
    except Exception as e:
        print(f"ERRO geral: {e}")
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except:
            proc.kill()

    # Salva resultado do scan
    with open("D:/projetos-navegador/scan_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    # Adiciona canais com vídeos ao all_channel_videos_full.json
    added = 0
    for handle, data in results.items():
        if data["status"] == "ok" and (data["videos"] or data["shorts"]):
            existing[handle] = {
                "lang": "pt",  # Default PT pra contas brasileiras
                "videos": data["videos"],
                "shorts": data["shorts"],
            }
            added += 1
            print(f"  + ADICIONADO: @{handle} ({len(data['videos'])}v + {len(data['shorts'])}s)")

    if added:
        with open(ALL_VIDEOS_FILE, "w", encoding="utf-8") as f:
            json.dump(existing, f, indent=2, ensure_ascii=False)
        print(f"\n=== {added} canais adicionados ao all_channel_videos_full.json ===")
    else:
        print("\nNenhum canal novo com vídeos encontrado.")

    # Resumo das bloqueadas/sem canal
    print("\n--- CONTAS SEM CANAL/BLOQUEADAS ---")
    for handle, data in results.items():
        if data["status"] != "ok":
            print(f"  {handle}: {data['status']}")


if __name__ == "__main__":
    main()
