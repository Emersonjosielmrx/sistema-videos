"""
warmup.py — Warm-up de contas novas antes de engajar pesado.

Uso:
    python -m engage_modules.warmup
    ou: from engage_modules.warmup import warmup_account

Abre o Chrome, navega no YouTube como humano (scroll, assiste 2-3 vídeos
aleatórios, visita trending), sem curtir/comentar/inscrever.
Isso cria histórico de navegação e evita ban no primeiro lote.
"""
import random
import time
from playwright.sync_api import sync_playwright

from .browser import launch_chrome, kill_chrome
from .logger import log

import sys
from .config import BASE_DIR
sys.path.append(str(BASE_DIR / "shared"))
from google_session import PORT_MAP


WARMUP_URLS = [
    "https://www.youtube.com",
    "https://www.youtube.com/feed/trending",
    "https://www.youtube.com/feed/subscriptions",
    "https://www.youtube.com/shorts",
]


def warmup_account(account, cfg, duration_minutes=5):
    """
    Faz warm-up de uma conta: navega no YouTube sem engajar.

    Args:
        account: email/nome da conta
        cfg: dict de config
        duration_minutes: quanto tempo ficar navegando (default 5min)

    Returns:
        True se completou sem erro, False se falhou
    """
    proc, port = launch_chrome(account, cfg)
    if not proc:
        log(f"WARMUP falhou ao abrir Chrome para {account}")
        return False

    try:
        with sync_playwright() as p:
            browser = p.chromium.connect_over_cdp(f"http://127.0.0.1:{port}")
            ctx = browser.contexts[0]
            ctx.set_default_timeout(12000)
            page = ctx.pages[0] if ctx.pages else ctx.new_page()

            end_time = time.time() + duration_minutes * 60
            videos_watched = 0

            while time.time() < end_time:
                # Visita uma página aleatória do YouTube
                url = random.choice(WARMUP_URLS)
                try:
                    page.goto(url, timeout=20000, wait_until="domcontentloaded")
                except:
                    time.sleep(3)
                    continue

                time.sleep(random.uniform(2, 5))

                # Scroll orgânico
                for _ in range(random.randint(2, 5)):
                    page.keyboard.press("PageDown")
                    time.sleep(random.uniform(1, 3))

                # 50% chance de clicar num vídeo e assistir
                if random.random() < 0.5:
                    try:
                        clicked = page.evaluate("""() => {
                            const vids = document.querySelectorAll(
                                'ytd-rich-item-renderer a#thumbnail, '
                                + 'ytd-video-renderer a#thumbnail'
                            );
                            if (vids.length > 2) {
                                const idx = Math.floor(Math.random() * Math.min(vids.length, 12));
                                vids[idx]?.click();
                                return true;
                            }
                            return false;
                        }""")
                        if clicked:
                            watch_time = random.uniform(8, 25)
                            time.sleep(watch_time)
                            videos_watched += 1
                            # Scroll durante vídeo
                            if random.random() < 0.4:
                                page.keyboard.press("PageDown")
                                time.sleep(random.uniform(1, 2))
                    except:
                        pass

                time.sleep(random.uniform(3, 8))

            browser.close()
            log(f"WARMUP OK {account}: {videos_watched} vídeos em {duration_minutes}min")
            return True

    except Exception as e:
        log(f"WARMUP ERRO {account}: {str(e)[:60]}")
        return False
    finally:
        kill_chrome(proc)


def warmup_all_new(cfg, max_concurrent=3):
    """
    Faz warm-up de todas as contas que nunca engajaram.
    Roda sequencialmente (max_concurrent=1) ou em paralelo.
    """
    from .progress import load_progress
    from concurrent.futures import ThreadPoolExecutor

    progress = load_progress()

    # Contas que já engajaram pelo menos 1 vídeo
    active_accounts = set()
    for v in progress.values():
        for acc in v.get("engaged_by", []):
            active_accounts.add(acc)

    # Contas que nunca fizeram nada = precisam de warm-up
    new_accounts = [acc for acc in PORT_MAP.keys() if acc not in active_accounts]

    if not new_accounts:
        log("WARMUP: Todas as contas já têm histórico. Nada a fazer.")
        return

    log(f"WARMUP: {len(new_accounts)} contas novas detectadas. Iniciando...")

    with ThreadPoolExecutor(max_workers=max_concurrent) as executor:
        futures = [
            executor.submit(warmup_account, acc, cfg)
            for acc in new_accounts
        ]
        for f in futures:
            try:
                f.result()
            except:
                pass

    log(f"WARMUP concluído para {len(new_accounts)} contas.")


if __name__ == "__main__":
    from .config import load_config
    cfg = load_config()
    warmup_all_new(cfg)
