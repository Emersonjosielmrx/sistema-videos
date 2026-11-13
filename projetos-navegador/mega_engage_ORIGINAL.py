"""
MEGA ENGAGE v3 - Cross-engagement otimizado.
- Reutiliza sessao do browser (batch de videos por conta)
- Watch time simulado (10-30s)
- Subscribe + Like + Comment
- Fingerprint diversificado (user-agent, viewport)
- Cooldown exponencial por erro
- Delay aleatorio anti-deteccao
"""
import json, time, subprocess, random, sys, os, threading
from pathlib import Path
from datetime import datetime, date
from playwright.sync_api import sync_playwright
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.append("D:/projetos-navegador/shared")
from google_session import ACCOUNTS, PORT_MAP, get_profile_dir

CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
PROGRESS_FILE = Path("D:/projetos-navegador/mega_engage_progress.json")
VIDEOS_FILE = Path("D:/projetos-navegador/all_channel_videos_full.json")
LOG_FILE = Path("D:/projetos-navegador/mega_engage_log.txt")
CONFIG_FILE = Path("D:/projetos-navegador/engage_config.json")
STOP_FLAG = Path("D:/projetos-navegador/engage_stop.flag")
RESTART_FLAG = Path("D:/projetos-navegador/engage_restart.flag")
PID_FILE = Path("D:/projetos-navegador/engage_bot.pid")

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:127.0) Gecko/20100101 Firefox/127.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_5) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Safari/605.1.15",
]

VIEWPORTS = [
    {"width": 1920, "height": 1080}, {"width": 1366, "height": 768},
    {"width": 1536, "height": 864}, {"width": 1440, "height": 900},
    {"width": 1280, "height": 720}, {"width": 1600, "height": 900},
]

COMMENTS_BY_LANG = {
    "pt": ["Muito bom!", "Conteudo incrivel!", "Adorei esse video!", "Excelente trabalho!",
           "Parabens pelo conteudo!", "Top demais!", "Que video massa!", "Sensacional!",
           "Continue assim!", "Melhor canal!", "Amei!", "Show de bola!",
           "Conteudo de qualidade!", "Perfeito!", "Maravilhoso!", "Muito top!",
           "Incrivel demais!", "Arrasou!", "Nota 10!", "Simplesmente perfeito!"],
    "en": ["Awesome video!", "Great content!", "I really enjoyed this!", "Fantastic work!",
           "Keep it up!", "Loved this!", "Amazing!", "So good!", "Brilliant!",
           "This is exactly what I needed!", "Outstanding!", "Well done!",
           "Top tier content!", "Thanks for sharing!", "Really well put together!",
           "Incredible work!", "This deserves more views!", "Subscribed!", "Pure gold!"],
    "es": ["Excelente video!", "Me encanto!", "Muy buen contenido!", "Increible!",
           "Sigue asi!", "Genial!", "Fantastico trabajo!", "Lo mejor!",
           "Contenido de calidad!", "Maravilloso!", "Impresionante!",
           "Gran video!", "Me gusto mucho!", "Perfecto!", "Espectacular!",
           "Que bueno!", "Increible trabajo!", "Contenido top!", "Brutal!"],
    "fr": ["Excellente video!", "J ai adore!", "Tres bon contenu!", "Incroyable!",
           "Continue comme ca!", "Genial!", "Fantastique!", "Le meilleur!",
           "Contenu de qualite!", "Merveilleux!", "Impressionnant!",
           "Super video!", "J ai beaucoup aime!", "Parfait!", "Magnifique!",
           "Bravo!", "Top qualite!", "Exceptionnel!", "Formidable!"],
    "it": ["Video fantastico!", "Mi e piaciuto molto!", "Ottimo contenuto!", "Incredibile!",
           "Continua cosi!", "Geniale!", "Fantastico lavoro!", "Il migliore!",
           "Contenuto di qualita!", "Meraviglioso!", "Impressionante!",
           "Gran bel video!", "Bellissimo!", "Perfetto!", "Stupendo!",
           "Eccezionale!", "Complimenti!", "Bravissimo!", "Magnifico!"],
    "th": ["Great video!", "Love it!", "Amazing content!", "Keep going!",
           "Wonderful!", "So good!", "Best channel!", "Fantastic!",
           "Love this!", "Incredible!", "Nice!", "Perfect!",
           "Well done!", "Excellent!", "Outstanding!"],
    "vi": ["Video tuyet voi!", "Rat thich!", "Noi dung hay!", "Tuyet voi!",
           "Tiep tuc nhe!", "Xuat sac!", "Hay nhat!", "Chat luong cao!",
           "An tuong!", "Hoan hao!", "Sieu pham!", "Hay qua!",
           "Thich qua!", "Tuyet hao!", "Xuat chung!"],
    "hi": ["Great video!", "Very nice!", "Amazing content!", "Keep it up!",
           "Wonderful!", "So good!", "Best!", "Fantastic!",
           "Love this!", "Incredible!", "Nice!", "Perfect!",
           "Well done!", "Excellent!", "Outstanding!"],
    "ru": ["Otlichnoe video!", "Mne ochen ponravilos!", "Krutoi kontent!", "Neveroyatno!",
           "Prodolzhai!", "Genialno!", "Fantasticheska rabota!", "Luchshee!",
           "Kachestvennyi kontent!", "Zamechatelno!", "Vpechatlyayusche!",
           "Super video!", "Ochen ponravilos!", "Idealno!", "Velikolepno!"],
    "id": ["Video keren!", "Sangat suka!", "Konten bagus!", "Luar biasa!",
           "Terus berkarya!", "Hebat!", "Kerja fantastis!", "Yang terbaik!",
           "Konten berkualitas!", "Menakjubkan!", "Memukau!",
           "Video bagus sekali!", "Suka banget!", "Sempurna!", "Mantap!"],
}


def load_config():
    try:
        if CONFIG_FILE.exists():
            return json.loads(CONFIG_FILE.read_text("utf-8"))
    except:
        pass
    return {"workers": 5, "sleep_min": 2, "sleep_max": 8, "batch": 500, "priority": "",
            "mode": "both", "active_hours": [0, 23], "max_per_account_day": 200,
            "blacklist_channels": [], "blacklist_videos": [], "randomize_order": True,
            "comments_extra": {}, "paused": False, "watch_time": [10, 30],
            "subscribe": True, "fingerprint": True}


def load_progress():
    if PROGRESS_FILE.exists():
        return json.loads(PROGRESS_FILE.read_text("utf-8"))
    return {}


def save_progress(progress):
    PROGRESS_FILE.write_text(json.dumps(progress, ensure_ascii=False), encoding="utf-8")


def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def get_comment(lang, cfg):
    extra = cfg.get("comments_extra", {})
    base = list(COMMENTS_BY_LANG.get(lang, COMMENTS_BY_LANG["en"]))
    if isinstance(extra, dict) and lang in extra:
        base.extend(extra[lang])
    elif isinstance(extra, list) and extra:
        base.extend(extra)
    return random.choice(base)


def check_flags():
    if STOP_FLAG.exists():
        STOP_FLAG.unlink()
        log("STOP flag detectada. Encerrando.")
        sys.exit(0)
    if RESTART_FLAG.exists():
        RESTART_FLAG.unlink()
        log("RESTART flag detectada. Reiniciando...")
        os.execv(sys.executable, [sys.executable] + sys.argv)


def engage_batch_session(account, video_list, cfg, progress, progress_lock):
    """Abre Chrome UMA VEZ e engaja multiplos videos na mesma sessao."""
    mode = cfg.get("mode", "both")
    do_subscribe = cfg.get("subscribe", True)
    watch_time = cfg.get("watch_time", [10, 30])
    use_fingerprint = cfg.get("fingerprint", True)
    sleep_min = cfg.get("sleep_min", 2)
    sleep_max = cfg.get("sleep_max", 8)

    port = PORT_MAP.get(account)
    if not port:
        return 0
    profile_dir = get_profile_dir(account)
    acc_list = list(PORT_MAP.keys())
    proxy_idx = acc_list.index(account) % 19 if account in acc_list else 0
    local_proxy_port = 18100 + proxy_idx

    ua = random.choice(USER_AGENTS) if use_fingerprint else USER_AGENTS[0]
    vp = random.choice(VIEWPORTS) if use_fingerprint else VIEWPORTS[0]

    chrome_args = [
        CHROME_PATH,
        f"--user-data-dir={profile_dir}",
        f"--remote-debugging-port={port}",
        "--headless=new", "--no-first-run", "--disable-gpu", "--mute-audio",
        f"--proxy-server=http://127.0.0.1:{local_proxy_port}",
        "--disable-software-rasterizer",
        f"--window-size={vp['width']},{vp['height']}",
        f"--user-agent={ua}",
        "about:blank"
    ]

    proc = subprocess.Popen(chrome_args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(6)

    count = 0
    consecutive_errors = 0

    try:
        with sync_playwright() as p:
            browser = p.chromium.connect_over_cdp(f"http://127.0.0.1:{port}")
            ctx = browser.contexts[0]
            ctx.set_default_timeout(12000)
            page = ctx.pages[0] if ctx.pages else ctx.new_page()

            for vid_key, lang, handle in video_list:
                check_flags()

                with progress_lock:
                    if account in progress.get(vid_key, {}).get("engaged_by", []):
                        continue

                if consecutive_errors >= 3:
                    cooldown = min(60, 5 * (2 ** (consecutive_errors - 3)))
                    log(f"COOLDOWN {account}: {cooldown}s ({consecutive_errors} erros)")
                    time.sleep(cooldown)

                acted = liked = commented = subscribed = False
                comment_text = ""

                try:
                    clean_url = vid_key.split("&")[0]
                    if "/shorts/" in clean_url:
                        short_id = clean_url.split("/shorts/")[-1].split("?")[0]
                        clean_url = f"https://www.youtube.com/watch?v={short_id}"

                    page.goto(clean_url, timeout=30000, wait_until="domcontentloaded")

                    # Watch time simulado
                    wt = random.uniform(watch_time[0], watch_time[1])
                    elapsed = 0
                    while elapsed < wt:
                        wait_chunk = random.uniform(2, 5)
                        time.sleep(wait_chunk)
                        elapsed += wait_chunk
                        if random.random() < 0.3:
                            page.keyboard.press("PageDown")

                    # SUBSCRIBE
                    if do_subscribe:
                        try:
                            sub_js = """() => {
                                const btn = document.querySelector("ytd-subscribe-button-renderer button, #subscribe-button button");
                                if (!btn) return "nf";
                                const label = (btn.textContent || "").toLowerCase();
                                if (label.includes("subscribed") || label.includes("inscrito") || btn.getAttribute("aria-pressed")==="true") return "al";
                                btn.click(); return "ok";
                            }"""
                            r = page.evaluate(sub_js)
                            if r in ("ok", "al"):
                                subscribed = True
                        except:
                            pass

                    # LIKE
                    if mode in ("both", "likes"):
                        try:
                            like_js = """() => { const btn = document.querySelector("like-button-view-model button"); if(!btn) return "nf"; if(btn.getAttribute("aria-pressed")==="true") return "al"; btn.click(); return "ok"; }"""
                            r = page.evaluate(like_js)
                            if r in ("ok", "al"):
                                liked = True
                                acted = True
                        except:
                            pass

                    # COMMENT
                    if mode in ("both", "comments"):
                        try:
                            for _ in range(4):
                                page.keyboard.press("PageDown")
                                time.sleep(random.uniform(0.5, 1.5))
                            has_box = False
                            for _ in range(5):
                                has_box = page.evaluate("() => !!document.querySelector('ytd-comment-simplebox-renderer')")
                                if has_box:
                                    break
                                time.sleep(1)
                            if has_box:
                                page.evaluate("document.querySelector('ytd-comment-simplebox-renderer div#placeholder-area')?.click()")
                                time.sleep(random.uniform(0.8, 1.5))
                                comment_text = get_comment(lang, cfg)
                                cmt_js = """(t) => { const root = document.querySelector("#contenteditable-root"); if(root){root.textContent=t;root.dispatchEvent(new Event("input",{bubbles:true}));setTimeout(()=>{const s=document.querySelector("ytd-button-renderer#submit-button button, #submit-button");if(s){s.removeAttribute("disabled");s.click()}},500)} }"""
                                page.evaluate(cmt_js, comment_text)
                                commented = True
                                acted = True
                                time.sleep(random.uniform(1.5, 3))
                        except:
                            pass

                    if liked or commented or subscribed:
                        acted = True
                        consecutive_errors = 0
                    else:
                        consecutive_errors += 1

                except Exception as e:
                    consecutive_errors += 1
                    log(f"ERRO {account}/{vid_key.split('/')[-1][:11]}: {str(e)[:50]}")

                if acted:
                    actions = []
                    if liked: actions.append("L")
                    if commented: actions.append("C")
                    if subscribed: actions.append("S")
                    action_str = "+".join(actions) if actions else "?"
                    with progress_lock:
                        if vid_key not in progress:
                            progress[vid_key] = {"engaged_by": [], "channel": handle, "lang": lang, "actions": []}
                        if "actions" not in progress[vid_key]:
                            progress[vid_key]["actions"] = []
                        progress[vid_key]["engaged_by"].append(account)
                        progress[vid_key]["actions"].append({
                            "acc": account, "liked": liked, "commented": commented,
                            "subscribed": subscribed, "comment": comment_text,
                            "ts": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        })
                    log(f'OK [{action_str}] @{handle}/{vid_key.split("/")[-1][:11]} <- {account} ({lang})' + (f' "{comment_text}"' if commented else ""))
                    count += 1

                delay = random.uniform(sleep_min, sleep_max)
                time.sleep(delay)

            browser.close()
    except Exception as e:
        log(f"ERRO sessao {account}: {str(e)[:60]}")

    if proc and proc.poll() is None:
        try:
            subprocess.run(["taskkill", "/F", "/T", "/PID", str(proc.pid)], capture_output=True)
        except:
            pass
        try:
            proc.wait(timeout=3)
        except:
            proc.kill()

    return count


def run_batch():
    cfg = load_config()
    check_flags()

    if cfg.get("paused", False):
        log("Bot PAUSADO. Aguardando 30s...")
        time.sleep(30)
        return 0

    active_hours = cfg.get("active_hours", [0, 23])
    current_hour = datetime.now().hour
    h_start, h_end = active_hours[0], active_hours[1]
    if h_start <= h_end:
        if not (h_start <= current_hour <= h_end):
            log(f"Fora do horario ativo ({h_start}h-{h_end}h). Aguardando 60s...")
            time.sleep(60)
            return 0
    else:
        if h_end < current_hour < h_start:
            log(f"Fora do horario ativo ({h_start}h-{h_end}h). Aguardando 60s...")
            time.sleep(60)
            return 0

    max_actions = cfg.get("batch", 500)
    workers = min(cfg.get("workers", 5), 19)
    priority_channel = cfg.get("priority", "")
    max_per_day = cfg.get("max_per_account_day", 200)
    blacklist_ch = set(cfg.get("blacklist_channels", []))
    blacklist_vid = set(cfg.get("blacklist_videos", []))

    channel_data = json.loads(VIDEOS_FILE.read_text("utf-8"))
    progress = load_progress()
    valid_accs = [acc for acc in PORT_MAP.keys() if list(get_profile_dir(acc).rglob("Cookies"))]

    # Count today actions per account
    today_str = date.today().isoformat()
    acc_today_count = {}
    for v in progress.values():
        for a in v.get("actions", []):
            acc = a.get("acc", "")
            ts = a.get("ts", "")
            if ts.startswith(today_str):
                acc_today_count[acc] = acc_today_count.get(acc, 0) + 1

    progress_lock = threading.Lock()

    # Build task queue
    task_queue = []
    for handle, data in channel_data.items():
        if handle in blacklist_ch:
            continue
        lang = data["lang"]
        all_urls = data["videos"] + data["shorts"]
        for video_url in all_urls:
            vid_key = video_url.split("&")[0]
            if vid_key in blacklist_vid:
                continue
            if vid_key not in progress:
                progress[vid_key] = {"engaged_by": [], "channel": handle, "lang": lang}
            remaining_accs = [a for a in valid_accs if a not in progress[vid_key]["engaged_by"]]
            remaining_accs = [a for a in remaining_accs if acc_today_count.get(a, 0) < max_per_day]
            for acc in remaining_accs:
                task_queue.append((acc, vid_key, lang, handle))

    # Priority
    if priority_channel and priority_channel in channel_data:
        priority_tasks = [t for t in task_queue if t[3] == priority_channel]
        other_tasks = [t for t in task_queue if t[3] != priority_channel]
        if cfg.get("randomize_order", True):
            random.shuffle(priority_tasks)
            random.shuffle(other_tasks)
        n_priority = int(max_actions * 0.7)
        task_queue = priority_tasks[:n_priority] + other_tasks
        task_queue = task_queue[:max_actions]
    else:
        if cfg.get("randomize_order", True):
            random.shuffle(task_queue)
        task_queue = task_queue[:max_actions]

    # Group by account (each account gets a batch of videos)
    by_account = {}
    for acc, vid_key, lang, handle in task_queue:
        by_account.setdefault(acc, []).append((vid_key, lang, handle))

    log(f"Fila: {len(task_queue)} tarefas | {len(by_account)} contas | workers={workers} | mode={cfg.get('mode','both')}")

    actions_done = 0
    CHUNK_SIZE = 5  # Max videos per browser session to avoid OOM

    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {}
        for acc, tasks in by_account.items():
            # Split into chunks of CHUNK_SIZE
            chunks = [tasks[i:i+CHUNK_SIZE] for i in range(0, len(tasks), CHUNK_SIZE)]
            for chunk in chunks:
                futures[executor.submit(engage_batch_session, acc, chunk, cfg, progress, progress_lock)] = acc

        for future in as_completed(futures):
            acc = futures[future]
            try:
                count = future.result()
                actions_done += count
            except Exception as e:
                log(f"ERRO thread {acc}: {str(e)[:80]}")

    save_progress(progress)
    # Cleanup between batches
    subprocess.run(["taskkill", "/F", "/IM", "chrome.exe", "/T"], capture_output=True)
    time.sleep(3)
    return actions_done


if __name__ == "__main__":
    PID_FILE.write_text(str(os.getpid()), encoding="utf-8")
    log("=== MEGA ENGAGE v3 iniciado (batch-session, subscribe, watch-time, fingerprint) ===")
    while True:
        try:
            check_flags()
            total = run_batch()
            log(f"=== Lote finalizado: {total} acoes ===")
        except SystemExit:
            break
        except Exception as e:
            log(f"CRASH lote (retry em 30s): {str(e)[:80]}")
            time.sleep(30)
            continue
        progress = load_progress()
        total_done = sum(len(v["engaged_by"]) for v in progress.values())
        total_needed = 1882 * 19
        pct = (total_done / total_needed * 100) if total_needed else 0
        log(f"Progresso geral: {total_done}/{total_needed} ({pct:.1f}%)")
        if total_done >= total_needed:
            log("=== MISSAO COMPLETA ===")
            break
        log("Proximo lote em 15s...")
        time.sleep(15)
