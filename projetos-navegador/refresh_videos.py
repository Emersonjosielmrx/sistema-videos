"""
refresh_videos.py — Atualiza a lista de vídeos dos canais EXISTENTES.

OBJETIVO:
    Puxar vídeos novos de cada canal e ACRESCENTAR no topo do JSON,
    sem apagar os antigos e sem tocar no progresso.

COMO FUNCIONA:
    1. Carrega all_channel_videos_full.json
    2. Abre 1 Chrome headless com perfil temporário (sem gastar conta)
    3. Visita cada canal (@handle/videos e @handle/shorts)
    4. Pega os primeiros 30 vídeos + 50 shorts (mais recentes)
    5. Acrescenta URLs NOVAS no TOPO das listas (videos/shorts)
    6. Salva o JSON atualizado
    7. O progresso não é tocado — vídeos antigos continuam de onde pararam

QUANDO RODAR:
    - 1-2x por dia (ex: 5h e 17h)
    - Via task agendada no PC3

DEPENDENCIAS:
    - Playwright (venv do projeto)
    - Chrome instalado
    - Não precisa de conta Google logada (acesso público)
"""
import json
import time
import subprocess
from pathlib import Path
from playwright.sync_api import sync_playwright

# Caminhos
ALL_VIDEOS_FILE = Path("D:/projetos-navegador/all_channel_videos_full.json")
CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
TEMP_PROFILE = Path("D:/projetos-navegador/_refresh_temp_profile")
REFRESH_PORT = 9398

# Log simples
def log(msg):
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] {msg}")


def refresh_channel(page, handle):
    """
    Visita youtube.com/@handle e retorna vídeos/shorts mais recentes.

    Returns:
        dict {"videos": [...], "shorts": [...], "status": "ok/error/blocked"}
    """
    result = {"videos": [], "shorts": [], "status": "unknown"}

    try:
        # Vídeos
        page.goto(f"https://www.youtube.com/@{handle}/videos", timeout=25000, wait_until="domcontentloaded")
        time.sleep(3)

        content = page.content()
        if "não está disponível" in content or "isn't available" in content or "404" in page.title():
            result["status"] = "not_found"
            return result

        if "encerrad" in content or "terminated" in content or "suspended" in content:
            result["status"] = "blocked"
            return result

        videos = page.evaluate("""() => {
            const links = document.querySelectorAll('a#video-title-link, a.yt-simple-endpoint[href*="/watch"]');
            return [...new Set([...links].map(a => a.href).filter(h => h.includes('/watch')))];
        }""")
        result["videos"] = videos[:30]

        # Shorts
        page.goto(f"https://www.youtube.com/@{handle}/shorts", timeout=25000, wait_until="domcontentloaded")
        time.sleep(3)

        shorts = page.evaluate("""() => {
            const links = document.querySelectorAll('a[href*="/shorts/"]');
            return [...new Set([...links].map(a => a.href).filter(h => h.includes('/shorts/')))];
        }""")
        result["shorts"] = shorts[:50]

        result["status"] = "ok"

    except Exception as e:
        result["status"] = f"error: {str(e)[:60]}"

    return result


def main():
    log("=== REFRESH DE VIDEOS INICIADO ===")

    # Carrega JSON atual
    if not ALL_VIDEOS_FILE.exists():
        log("ERRO: all_channel_videos_full.json não encontrado!")
        return

    with open(ALL_VIDEOS_FILE, "r", encoding="utf-8") as f:
        channel_data = json.load(f)

    total_channels = len(channel_data)
    log(f"Canais a atualizar: {total_channels}")

    # Cria perfil temporário
    TEMP_PROFILE.mkdir(exist_ok=True)

    # Lança Chrome headless
    chrome_args = [
        CHROME_PATH,
        f"--user-data-dir={TEMP_PROFILE}",
        f"--remote-debugging-port={REFRESH_PORT}",
        "--headless=new", "--no-first-run", "--disable-gpu", "--mute-audio",
        "--disable-software-rasterizer",
        "about:blank"
    ]
    proc = subprocess.Popen(chrome_args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(6)

    updated_count = 0
    new_videos_total = 0
    new_shorts_total = 0

    try:
        with sync_playwright() as p:
            browser = p.chromium.connect_over_cdp(f"http://127.0.0.1:{REFRESH_PORT}")
            ctx = browser.contexts[0]
            ctx.set_default_timeout(20000)
            page = ctx.pages[0] if ctx.pages else ctx.new_page()

            for idx, (handle, data) in enumerate(channel_data.items(), 1):
                log(f"[{idx}/{total_channels}] @{handle}...")

                try:
                    fresh = refresh_channel(page, handle)

                    if fresh["status"] == "ok":
                        # Pega URLs antigas
                        old_videos = set(data.get("videos", []))
                        old_shorts = set(data.get("shorts", []))

                        # Identifica novas
                        new_vids = [v for v in fresh["videos"] if v not in old_videos]
                        new_shts = [s for s in fresh["shorts"] if s not in old_shorts]

                        # Acrescenta NOVAS no TOPO (prepend)
                        updated_videos = new_vids + data.get("videos", [])
                        updated_shorts = new_shts + data.get("shorts", [])

                        # Atualiza no dict
                        channel_data[handle]["videos"] = updated_videos
                        channel_data[handle]["shorts"] = updated_shorts

                        new_videos_total += len(new_vids)
                        new_shorts_total += len(new_shts)

                        if new_vids or new_shts:
                            log(f"  +{len(new_vids)}v +{len(new_shts)}s NOVOS")
                            updated_count += 1
                        else:
                            log(f"  sem novos")
                    else:
                        log(f"  {fresh['status']}")

                    time.sleep(2)  # Anti-rate-limit

                except Exception as e:
                    log(f"ERRO: {str(e)[:60]}")

            browser.close()

    except Exception as e:
        log(f"ERRO FATAL: {e}")

    finally:
        # Mata Chrome
        try:
            subprocess.run(["taskkill", "/F", "/T", "/PID", str(proc.pid)], capture_output=True)
        except:
            pass
        try:
            proc.wait(timeout=5)
        except:
            proc.kill()

    # Salva JSON atualizado
    if updated_count > 0:
        log(f"Salvando JSON atualizado...")
        with open(ALL_VIDEOS_FILE, "w", encoding="utf-8") as f:
            json.dump(channel_data, f, indent=2, ensure_ascii=False)
        log(f"=== CONCLUIDO: {updated_count} canais atualizados | +{new_videos_total}v +{new_shorts_total}s ===")
    else:
        log("=== NENHUM VIDEO NOVO ENCONTRADO ===")


if __name__ == "__main__":
    main()
