"""
discover_channels.py — Descobre o handle REAL do canal YouTube de cada conta.

Abre o Chrome com o perfil logado de cada conta e acessa
youtube.com/@me ou studio.youtube.com pra pegar o handle verdadeiro.
Depois puxa os vídeos do canal encontrado.
"""
import json, time, sys, random, re, subprocess
from pathlib import Path
from playwright.sync_api import sync_playwright

sys.path.append("D:/projetos-navegador/shared")
from google_session import ACCOUNTS, PORT_MAP, get_profile_dir

CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
ALL_VIDEOS_FILE = Path("D:/projetos-navegador/all_channel_videos_full.json")

with open(ALL_VIDEOS_FILE, "r", encoding="utf-8") as f:
    existing = json.load(f)
EXISTING_HANDLES = set(existing.keys())

# Contas que NÃO são canais já conhecidos no JSON
SKIP = {
    "inovaremanhwaverse", "inovaremanhwabr", "inovaremanhwaverseeng",
    "inovaremanhwaverseesp", "inovaremanhwaversefrench", "inovaremanhwaversehindi",
    "inovaremanhwaverseind", "inovaremanhwaverseita", "inovaremanhwaverserussian",
    "inovaremanhwaversethai", "inovaremanhwaverseviet", "inovaremanhwaverseing",
    "gameoftroneskingsroadbrasil", "fabricadeautomacoesia",
}

# Só escanear contas que não sabemos o canal
ACCOUNTS_TO_SCAN = [
    acc for acc in PORT_MAP.keys()
    if acc not in SKIP
    and acc not in EXISTING_HANDLES
]

print(f"Contas a descobrir canal: {len(ACCOUNTS_TO_SCAN)}")


def discover_channel_handle(account):
    """
    Abre Chrome com o perfil da conta, vai no YouTube e descobre o handle.
    Retorna dict com handle, channel_url, has_videos, status.
    """
    port = PORT_MAP[account]
    profile_dir = get_profile_dir(account)

    chrome_args = [
        CHROME_PATH,
        f"--user-data-dir={profile_dir}",
        f"--remote-debugging-port={port}",
        "--headless=new", "--no-first-run", "--disable-gpu", "--mute-audio",
        "--disable-software-rasterizer",
        "about:blank"
    ]

    proc = subprocess.Popen(chrome_args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(5)

    result = {"handle": None, "channel_url": None, "videos": [], "shorts": [], "status": "unknown"}

    try:
        with sync_playwright() as p:
            browser = p.chromium.connect_over_cdp(f"http://127.0.0.1:{port}")
            ctx = browser.contexts[0]
            ctx.set_default_timeout(15000)
            page = ctx.pages[0] if ctx.pages else ctx.new_page()

            # Método: vai pra youtube.com/account_advanced que mostra channel ID
            # Depois tenta youtube.com/channel/CHANNEL_ID pra pegar o handle
            page.goto("https://www.youtube.com/account_advanced", timeout=20000, wait_until="domcontentloaded")
            time.sleep(4)

            current_url = page.url
            content = page.content()
            handle = None

            # Procura Channel ID na página (formato UC...)
            channel_id = None
            m_cid = re.search(r'(UC[\w-]{22})', content)
            if m_cid:
                channel_id = m_cid.group(1)

            # Se achou channel_id, navega pro canal pra pegar o handle
            if channel_id:
                page.goto(f"https://www.youtube.com/channel/{channel_id}", timeout=15000, wait_until="domcontentloaded")
                time.sleep(3)
                final_url = page.url
                # A URL final redireciona pra /@handle
                m_handle = re.search(r'/@([\w.-]+)', final_url)
                if m_handle:
                    handle = m_handle.group(1)
                else:
                    # Tenta extrair do conteúdo da página do canal
                    page_content = page.content()
                    m_handle = re.search(r'"vanityChannelUrl":"http[s]?://www\.youtube\.com/@([\w.-]+)"', page_content)
                    if m_handle:
                        handle = m_handle.group(1)
                    else:
                        # Usa o channel_id como fallback
                        handle = channel_id

            # Se não achou channel_id, tenta extrair handle do Studio
            if not handle:
                page.goto("https://studio.youtube.com", timeout=20000, wait_until="domcontentloaded")
                time.sleep(4)
                studio_url = page.url
                content = page.content()
                # Studio URL contém channel ID: studio.youtube.com/channel/UCxxxxx
                m_studio = re.search(r'studio\.youtube\.com/channel/(UC[\w-]{22})', studio_url)
                if m_studio:
                    channel_id = m_studio.group(1)
                    page.goto(f"https://www.youtube.com/channel/{channel_id}", timeout=15000, wait_until="domcontentloaded")
                    time.sleep(3)
                    m_handle = re.search(r'/@([\w.-]+)', page.url)
                    if m_handle:
                        handle = m_handle.group(1)

            if handle:
                result["handle"] = handle
                result["channel_url"] = f"https://www.youtube.com/@{handle}"

                # Agora puxa vídeos desse canal
                page.goto(f"https://www.youtube.com/@{handle}/videos", timeout=20000, wait_until="domcontentloaded")
                time.sleep(3)
                videos = page.evaluate("""() => {
                    const links = document.querySelectorAll('a#video-title-link, a.yt-simple-endpoint[href*="/watch"]');
                    return [...new Set([...links].map(a => a.href).filter(h => h.includes('/watch')))];
                }""")
                result["videos"] = videos[:30]

                # Shorts
                page.goto(f"https://www.youtube.com/@{handle}/shorts", timeout=20000, wait_until="domcontentloaded")
                time.sleep(3)
                shorts = page.evaluate("""() => {
                    const links = document.querySelectorAll('a[href*="/shorts/"]');
                    return [...new Set([...links].map(a => a.href).filter(h => h.includes('/shorts/')))];
                }""")
                result["shorts"] = shorts[:50]

                if result["videos"] or result["shorts"]:
                    result["status"] = "ok"
                else:
                    result["status"] = "empty_channel"
            else:
                # Verifica se está logado
                if "accounts.google" in current_url or "signin" in current_url:
                    result["status"] = "not_logged_in"
                elif "suspended" in content or "encerrad" in content or "terminated" in content:
                    result["status"] = "blocked"
                else:
                    result["status"] = "no_channel"

            browser.close()

    except Exception as e:
        result["status"] = f"error: {str(e)[:60]}"

    # Mata o Chrome
    try:
        subprocess.run(["taskkill", "/F", "/T", "/PID", str(proc.pid)], capture_output=True)
    except:
        pass
    try:
        proc.wait(timeout=5)
    except:
        proc.kill()

    time.sleep(2)
    return result


def main():
    all_results = {}

    for i, account in enumerate(ACCOUNTS_TO_SCAN):
        print(f"[{i+1}/{len(ACCOUNTS_TO_SCAN)}] {account}...", end=" ", flush=True)
        data = discover_channel_handle(account)
        all_results[account] = data

        if data["handle"]:
            print(f"CANAL: @{data['handle']} | {len(data['videos'])}v + {len(data['shorts'])}s | {data['status']}")
        else:
            print(f"{data['status']}")

        time.sleep(random.uniform(1, 3))

    # Salva resultado completo
    with open("D:/projetos-navegador/discover_results.json", "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)

    # Adiciona canais com vídeos ao all_channel_videos_full.json
    added = 0
    for account, data in all_results.items():
        handle = data.get("handle")
        if handle and data["status"] == "ok" and handle not in existing:
            existing[handle] = {
                "lang": "pt",
                "videos": data["videos"],
                "shorts": data["shorts"],
            }
            added += 1
            print(f"  + ADICIONADO: @{handle} ({len(data['videos'])}v + {len(data['shorts'])}s)")

    if added:
        with open(ALL_VIDEOS_FILE, "w", encoding="utf-8") as f:
            json.dump(existing, f, indent=2, ensure_ascii=False)
        print(f"\n=== {added} canais novos adicionados! ===")
    else:
        print("\nNenhum canal novo com vídeos encontrado.")

    # Resumo
    print("\n--- RESUMO ---")
    with_channel = [a for a, d in all_results.items() if d.get("handle")]
    without = [a for a, d in all_results.items() if not d.get("handle")]
    print(f"Com canal: {len(with_channel)}")
    print(f"Sem canal/bloqueado: {len(without)}")
    for a in without:
        print(f"  {a}: {all_results[a]['status']}")


if __name__ == "__main__":
    main()
