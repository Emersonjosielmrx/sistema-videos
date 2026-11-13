"""
worker.py — Worker que abre UMA sessão Chrome e engaja N vídeos.

OBJETIVO:
    Esta é a função principal que o ThreadPoolExecutor chama.
    Cada worker recebe UMA conta + lista de vídeos e:
    1. Abre Chrome headless com o perfil da conta
    2. Conecta via Playwright CDP
    3. Para cada vídeo: assiste, curte, comenta, inscreve
    4. Registra progresso e fecha tudo

COMO FUNCIONA:
    engage_batch_session(account, video_list, cfg, progress, progress_lock)
    - Retorna int com quantas ações bem-sucedidas fez

COOLDOWN:
    Se erros consecutivos >= 3, espera exponencialmente:
    5s, 10s, 20s, 40s, 60s (máx)

DEPENDENCIAS:
    - browser.py (launch_chrome, kill_chrome)
    - engagement.py (simulate_watch, do_subscribe, do_like, do_comment)
    - comments.py (get_comment)
    - logger.py (log)
    - flags.py (check_flags)
    - playwright
"""
import time
import random
from datetime import datetime
from pathlib import Path
from playwright.sync_api import sync_playwright

from .browser import launch_chrome, kill_chrome, blacklist_proxy_runtime
from .engagement import (
    simulate_watch, do_subscribe, do_like, do_comment,
    do_reply_comment, read_description, interact_endscreen,
    check_video_dead, detect_ban_signals, engage_community_post,
    discover_sidebar_channels,
)
from .comments import get_comment
from .logger import log
from .flags import check_flags
from .account_health import report_success, report_failure
from .config import BASE_DIR
from .progress import save_progress


def engage_batch_session(account, video_list, cfg, progress, progress_lock):
    """
    Abre Chrome UMA VEZ e engaja múltiplos vídeos na mesma sessão.

    Args:
        account:       email/nome da conta Google
        video_list:    lista de tuplas (vid_key, lang, channel_handle)
        cfg:           dict de configuração
        progress:      dict de progresso (compartilhado entre threads)
        progress_lock: threading.Lock pra acesso seguro ao progress

    Returns:
        int com o número de ações bem-sucedidas

    Fluxo:
        1. launch_chrome() → abre browser
        2. Conecta via Playwright CDP
        3. Loop por cada vídeo:
           - Verifica se já engajou (pula se sim)
           - Navega até o vídeo
           - simulate_watch()
           - do_subscribe() se configurado
           - do_like() se mode permite
           - do_comment() se mode permite
           - Registra no progress
        4. kill_chrome() → fecha tudo
    """
    # Extrair configurações relevantes
    mode = cfg.get("mode", "both")
    should_subscribe = cfg.get("subscribe", True)
    watch_time = cfg.get("watch_time", [10, 30])
    sleep_min = cfg.get("sleep_min", 2)
    sleep_max = cfg.get("sleep_max", 8)

    # Lança o Chrome com perfil da conta
    proc, port = launch_chrome(account, cfg)
    if not proc:
        return 0

    count = 0
    consecutive_errors = 0
    comment_fails = 0
    comment_banned = False

    try:
        with sync_playwright() as p:
            # Conecta ao Chrome via CDP (Chrome DevTools Protocol)
            browser = p.chromium.connect_over_cdp(f"http://127.0.0.1:{port}")
            ctx = browser.contexts[0]
            ctx.set_default_timeout(25000)
            page = ctx.pages[0] if ctx.pages else ctx.new_page()

            for vid_key, lang, handle in video_list:
                # Verifica flags a cada vídeo (permite parar mid-batch)
                check_flags()

                # Pula se já engajou esse vídeo com essa conta
                with progress_lock:
                    if account in progress.get(vid_key, {}).get("engaged_by", []):
                        continue

                # Cooldown exponencial se muitos erros seguidos
                if consecutive_errors >= 3:
                    cooldown = min(60, 5 * (2 ** (consecutive_errors - 3)))
                    log(f"COOLDOWN {account}: {cooldown}s ({consecutive_errors} erros)")
                    time.sleep(cooldown)

                # Variáveis de resultado desta iteração
                liked = False
                commented = False
                subscribed = False
                comment_text = ""
                acted = False

                try:
                    # Normaliza URL (shorts → watch?v=) e detecta se é short
                    clean_url = vid_key.split("&")[0]
                    is_short = False
                    if "/shorts/" in clean_url:
                        is_short = True
                        short_id = clean_url.split("/shorts/")[-1].split("?")[0]
                        clean_url = f"https://www.youtube.com/watch?v={short_id}"

                    # Navega até o vídeo (retry 1x em erro de rede)
                    for attempt in range(2):
                        try:
                            page.goto(clean_url, timeout=90000, wait_until="domcontentloaded")
                            break
                        except Exception as nav_err:
                            if attempt == 0 and any(x in str(nav_err) for x in ["ERR_ABORTED", "ERR_CONNECTION_RESET", "Timeout"]):
                                time.sleep(random.uniform(2, 5))
                                continue
                            raise

                    # Detecção de CAPTCHA/Challenge
                    page_url = page.url
                    if "accounts.google.com" in page_url or "challenge" in page_url:
                        log(f"CAPTCHA detectado para {account} — pausando conta neste lote")
                        break
                    captcha_check = page.evaluate(
                        "() => !!(document.querySelector('iframe[src*=\"recaptcha\"]') "
                        "|| document.querySelector('#captcha-form') "
                        "|| document.title.toLowerCase().includes('verify'))"
                    )
                    if captcha_check:
                        log(f"CAPTCHA detectado para {account} — pausando conta neste lote")
                        break

                    # Simula assistir (Modo RUSH para Shorts)
                    if is_short:
                        actual_wt = [3, 8]  # Shorts: Rápido (3 a 8s)
                    else:
                        actual_wt = watch_time  # Vídeos longos: Normal (ex: 20 a 40s)

                    # Detecção de vídeo morto/privado
                    dead_status = check_video_dead(page)
                    if dead_status == "dead":
                        log(f"VIDEO MORTO: {vid_key[:50]} — marcando pra remoção")
                        with progress_lock:
                            if vid_key not in progress:
                                progress[vid_key] = {"engaged_by": [], "channel": handle, "lang": lang}
                            progress[vid_key]["dead"] = True
                            progress[vid_key]["dead_ts"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        continue

                    # Ban detection periódica (a cada 3 vídeos)
                    if count > 0 and count % 3 == 0:
                        ban_signals = detect_ban_signals(page, account)
                        if ban_signals.get("banned"):
                            sigs = ",".join(ban_signals.get("signals", []))
                            log(f"BAN DETECTADO {account}: {sigs} — pausando conta")
                            with progress_lock:
                                try:
                                    ban_file = BASE_DIR / "ban_detected.txt"
                                    with open(ban_file, "a") as bf:
                                        bf.write(f"{datetime.now().isoformat()}|{account}|{sigs}\n")
                                except: pass
                            break

                    # Navegação orgânica pré-target (30% chance — descoberta natural)
                    if cfg.get("organic_mode", True) and random.random() < 0.3 and count == 0:
                        try:
                            page.goto("https://www.youtube.com", timeout=30000, wait_until="domcontentloaded")
                            time.sleep(random.uniform(2, 4))
                            for _ in range(random.randint(1, 3)):
                                page.keyboard.press("PageDown")
                                time.sleep(random.uniform(0.5, 1.5))
                            time.sleep(random.uniform(1, 3))
                            page.goto(clean_url, timeout=60000, wait_until="domcontentloaded")
                            time.sleep(random.uniform(1, 3))
                        except:
                            pass

                    simulate_watch(page, actual_wt, is_short=is_short)

                    # Leitura de descrição (25% chance — comportamento humano)
                    if not is_short and random.random() < 0.25:
                        read_description(page)

                    # GRADIENTE DE ENGAJAMENTO
                    # Watch: 100%, Like: 70%, Comment: 20%, Reply: 8%
                    should_like = random.random() < 0.7
                    should_comment = random.random() < 0.2
                    should_reply = random.random() < 0.08

                    # Dinamismo Anti-Deteccao (randomiza ações para não fazer tudo 100% das vezes)
                    # 60% tudo, 20% L+C, 10% só L, 10% só C
                    roll = random.random()
                    action_profile = "full"
                    if roll > 0.9: action_profile = "c_only"
                    elif roll > 0.8: action_profile = "l_only"
                    elif roll > 0.6: action_profile = "lc"

                    # SUBSCRIBE (só faz se o profile permitir e config = True)
                    if should_subscribe and action_profile in ("full",):
                        subscribed = do_subscribe(page)

                    # LIKE (respeita gradiente)
                    if mode in ("both", "likes") and action_profile in ("full", "lc", "l_only") and should_like:
                        liked = do_like(page)
                        if liked:
                            acted = True

                    # COMMENT (pula se detectou shadowban de comentário; respeita gradiente)
                    if mode in ("both", "comments") and action_profile in ("full", "lc", "c_only") and not comment_banned and should_comment:
                        comment_text = get_comment(lang, cfg, vid_key=vid_key, title=None, channel=handle, account=account)
                        commented = do_comment(page, comment_text)
                        if commented:
                            acted = True
                            comment_fails = 0
                            log(f"COMMENT OK {account}")
                        else:
                            comment_fails += 1
                            log(f"COMMENT FAIL {account} ({comment_fails}/8)")
                            if comment_fails >= 8:
                                comment_banned = True
                                log(f"COMMENT-BAN detectado para {account} — só like/sub daqui em diante")

                    # REPLY em comentário existente (8% chance, se não baniu comment)
                    if not comment_banned and should_reply and not is_short:
                        replied, reply_text = do_reply_comment(page)
                        if replied:
                            acted = True
                            log(f'REPLY @{handle}/{vid_key.split("/")[-1][:11]} <- {account}: "{reply_text}"')

                    # Interação com cards/endscreen (10% chance)
                    if not is_short and random.random() < 0.10:
                        interact_endscreen(page)

                    # Engajamento em Community Post (5% chance, só se subscrito)
                    if subscribed and random.random() < 0.05:
                        comm_engaged = engage_community_post(page, handle)
                        if comm_engaged:
                            acted = True
                            log(f'COMMUNITY POST @{handle} <- {account}')

                    # Auto-discovery de canais da sidebar (3% chance)
                    if random.random() < 0.03:
                        sidebar_channels = discover_sidebar_channels(page)
                        if sidebar_channels:
                            try:
                                disc_file = BASE_DIR / "data" / "discovered_channels.txt"
                                disc_file.parent.mkdir(exist_ok=True)
                                existing = set()
                                if disc_file.exists():
                                    existing = set(disc_file.read_text("utf-8").splitlines())
                                new_channels = [c for c in sidebar_channels if c not in existing]
                                if new_channels:
                                    with open(disc_file, "a", encoding="utf-8") as f:
                                        for ch in new_channels:
                                            f.write(ch + "\n")
                                    log(f"DISCOVERY: +{len(new_channels)} canais novos da sidebar")
                            except Exception:
                                pass

                    # Verifica se algo deu certo
                    if liked or commented or subscribed:
                        acted = True
                        consecutive_errors = 0
                        report_success(account)
                    else:
                        consecutive_errors += 1

                except Exception as e:
                    consecutive_errors += 1
                    err_msg = str(e)[:200]
                    log(f"ERRO {account}/{vid_key.split('/')[-1][:11]}: {err_msg[:80]}")

                    is_infra_error = any(x in err_msg for x in [
                        "Target page", "browser has been closed",
                        "Browser closed", "Connection closed",
                        "Execution context was destroyed",
                    ])
                    is_proxy_error = any(x in err_msg for x in [
                        "TUNNEL", "ERR_CONNECTION_RESET", "ERR_ABORTED",
                        "Timeout", "ERR_PROXY", "ERR_TIMED_OUT",
                        "net::ERR_", "NS_ERROR", "Navigation failed",
                        "Navigation to", "ERR_FAILED",
                        "ERR_NAME_NOT_RESOLVED", "ERR_CONNECTION_CLOSED",
                        "ERR_CONNECTION_REFUSED",
                    ])

                    if is_infra_error:
                        log(f"Chrome morreu para {account} — saindo do lote (nao é ban)")
                        break

                    if is_proxy_error:
                        try:
                            from .browser import get_proxy_port
                            proxy_port = get_proxy_port(account)
                            blacklist_proxy_runtime(proxy_port)
                        except Exception:
                            pass
                        log(f"Proxy falhou para {account} — nao conta como falha da conta")
                    else:
                        report_failure(account, str(e))

                    if consecutive_errors >= 5 and is_proxy_error:
                        log(f"PROXY: {account} — 5 erros proxy seguidos, trocando proxy na próxima")
                        break

                # Registra progresso se agiu
                if acted:
                    actions = []
                    if liked:
                        actions.append("L")
                    if commented:
                        actions.append("C")
                    if subscribed:
                        actions.append("S")
                    action_str = "+".join(actions) if actions else "?"

                    with progress_lock:
                        if vid_key not in progress:
                            progress[vid_key] = {
                                "engaged_by": [],
                                "channel": handle,
                                "lang": lang,
                                "actions": [],
                            }
                        if "actions" not in progress[vid_key]:
                            progress[vid_key]["actions"] = []
                        progress[vid_key]["engaged_by"].append(account)
                        progress[vid_key]["actions"].append({
                            "acc": account,
                            "liked": liked,
                            "commented": commented,
                            "subscribed": subscribed,
                            "comment": comment_text,
                            "ts": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        })

                    log(
                        f'OK [{action_str}] @{handle}/{vid_key.split("/")[-1][:11]}'
                        f' <- {account} ({lang})'
                        + (f' "{comment_text}"' if commented else "")
                    )
                    count += 1

                    # Salva progresso incrementalmente (a cada 5 ações)
                    if count % 5 == 0:
                        with progress_lock:
                            save_progress(progress)

                # Delay anti-detecção entre vídeos
                delay = random.uniform(sleep_min, sleep_max)
                time.sleep(delay)

                # Modo orgânico: 20% de chance de assistir algo aleatório do feed
                if cfg.get("organic_mode", True) and random.random() < 0.2:
                    try:
                        page.goto("https://www.youtube.com", timeout=30000, wait_until="domcontentloaded")
                        time.sleep(random.uniform(2, 4))
                        # Clica num vídeo aleatório do feed
                        page.evaluate("""() => {
                            const vids = document.querySelectorAll('ytd-rich-item-renderer a#thumbnail');
                            if (vids.length > 3) {
                                const idx = Math.floor(Math.random() * Math.min(vids.length, 10));
                                vids[idx]?.click();
                            }
                        }""")
                        time.sleep(random.uniform(5, 15))
                    except: pass

            browser.close()

    except Exception as e:
        log(f"ERRO sessao {account}: {str(e)[:60]}")

    # Mata o Chrome no final
    kill_chrome(proc)

    return count
