"""
scheduler.py — Monta a fila de tarefas e distribui entre workers.

OBJETIVO:
    run_batch() é o "cérebro" do bot:
    1. Lê config e verifica se deve rodar (pause, horário)
    2. Carrega lista de vídeos e progresso
    3. Filtra o que falta engajar (respeitando limites diários)
    4. Prioriza canal específico se configurado
    5. Agrupa por conta e distribui em chunks pro ThreadPoolExecutor

COMO FUNCIONA:
    run_batch() → retorna int com total de ações feitas no lote

CHUNK_SIZE = 5:
    Cada browser session processa no máximo 5 vídeos.
    Isso evita OOM (Out of Memory) do Chrome headless.

DEPENDENCIAS:
    - config.py (load_config, VIDEOS_FILE)
    - progress.py (load_progress, save_progress)
    - worker.py (engage_batch_session)
    - logger.py (log)
    - flags.py (check_flags)
    - google_session (shared/) para PORT_MAP, get_profile_dir
    - threading, json, random, subprocess (stdlib)
"""
import json
import random
import subprocess
import threading
import time
from datetime import datetime, date, timedelta
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

from .config import load_config, VIDEOS_FILE, BASE_DIR

import sys
sys.path.append(str(BASE_DIR / "shared"))
from google_session import PORT_MAP, get_profile_dir, CONTAS_SUSPENSAS
from .progress import load_progress, save_progress
from .worker import engage_batch_session
from .logger import log
from .flags import check_flags
from .browser import health_check_proxies
import engage_modules.browser as _browser_mod
from .timezone import is_peak_hour


# Máximo de vídeos por sessão de browser (evita Chrome OOM)
CHUNK_SIZE = 5


def run_batch():
    """
    Executa UM lote completo de engajamento.

    Retorna:
        int com o total de ações feitas neste lote

    Fluxo completo:
        1. Lê configuração
        2. Se pausado → espera 30s, retorna 0
        3. Se fora do horário ativo → espera 60s, retorna 0
        4. Carrega vídeos e progresso
        5. Filtra contas válidas (que têm cookies)
        6. Conta ações de hoje por conta (respeita limite diário)
        7. Monta fila de tarefas (vídeo × conta)
        8. Aplica prioridade e randomização
        9. Agrupa por conta em chunks de CHUNK_SIZE
        10. Dispara workers em paralelo (ThreadPoolExecutor)
        11. Salva progresso e limpa Chrome
    """
    cfg = load_config()
    check_flags()

    # -------------------------------------------------------
    # PAUSA — config diz pra não rodar
    # -------------------------------------------------------
    if cfg.get("paused", False):
        log("Bot PAUSADO. Aguardando 30s...")
        time.sleep(30)
        return 0

    # -------------------------------------------------------
    # HORÁRIO ATIVO — respeita janela de operação
    # -------------------------------------------------------
    active_hours = cfg.get("active_hours", [0, 23])
    current_hour = datetime.now().hour
    h_start, h_end = active_hours[0], active_hours[1]

    if h_start <= h_end:
        # Horário normal (ex: 8h às 22h)
        if not (h_start <= current_hour <= h_end):
            log(f"Fora do horario ativo ({h_start}h-{h_end}h). Aguardando 60s...")
            time.sleep(60)
            return 0
    else:
        # Horário noturno (ex: 22h às 6h)
        if h_end < current_hour < h_start:
            log(f"Fora do horario ativo ({h_start}h-{h_end}h). Aguardando 60s...")
            time.sleep(60)
            return 0

    # -------------------------------------------------------
    # PROXY CHECK — pula batch se não há proxy vivo (evita abrir Chrome à toa)
    # Sem proxy, nenhuma conta consegue abrir o YouTube. Pular o lote evita
    # dezenas de Chrome idle acumulando (o que causava OOM antes).
    # -------------------------------------------------------
    health_check_proxies()
    if not _browser_mod._healthy_proxies:
        if _browser_mod._proxy_status == "quota_esgotada":
            # Caso especial: cota Webshare acabou. Espera MAIS (5min) porque
            # reiniciar/insistir não adianta — só resolve com upgrade/reset da conta.
            log("Sem proxies: COTA WEBSHARE ESGOTADA. Aguardando 300s...")
            time.sleep(300)
        else:
            log("Sem proxies vivos (rede). Aguardando 60s...")
            time.sleep(60)
        return 0

    # -------------------------------------------------------
    # PARÂMETROS DO LOTE
    # -------------------------------------------------------
    max_actions = cfg.get("batch", 50)
    workers = min(cfg.get("workers", 2), 5)
    priority_channel = cfg.get("priority", "")
    max_per_day = min(cfg.get("max_per_account_day", 10), 10)
    max_per_channel_day = min(cfg.get("max_per_channel_day", 20), 20)
    blacklist_ch = set(cfg.get("blacklist_channels", []))
    blacklist_vid = set(cfg.get("blacklist_videos", []))

    # SEGURANÇA: nunca comentar/subscribe pelo bot (flag mais forte de fake engagement)
    cfg["mode"] = "likes"
    cfg["subscribe"] = False

    # -------------------------------------------------------
    # CARREGAR DADOS
    # -------------------------------------------------------
    channel_data = json.loads(VIDEOS_FILE.read_text("utf-8"))
    progress = load_progress()

    # Auto-blacklist: Contas que falharam demais
    BANNED_ACCOUNTS = set()
    try:
        dead_file = BASE_DIR / "dead_accounts.txt"
        if dead_file.exists():
            lines = dead_file.read_text("utf-8").splitlines()
            # Auto-limpeza: arquivo > 7 dias é resetado (ban pode ser temporário)
            if dead_file.stat().st_mtime < time.time() - 7 * 86400:
                dead_file.unlink()
            else:
                BANNED_ACCOUNTS = set(lines)
    except: pass

    # Só usa contas que têm cookies válidos, não estão banidas e não são suspensas
    valid_accs = [
        acc for acc in PORT_MAP.keys()
        if acc not in BANNED_ACCOUNTS
        and acc not in CONTAS_SUSPENSAS
        and list(get_profile_dir(acc).rglob("Cookies"))
    ]

    # -------------------------------------------------------
    # LIMITE DIÁRIO + COOL-DOWN POR CONTA
    # -------------------------------------------------------
    today_str = date.today().isoformat()
    acc_today_count = {}
    channel_today_count = {}
    acc_last_active = {}  # Último dia de atividade de cada conta
    acc_cooldown_days = {}  # Dias de descanso acumulados por conta

    for vid_key, v in progress.items():
        ch = v.get("channel", "")
        for a in v.get("actions", []):
            acc = a.get("acc", "")
            ts = a.get("ts", "")
            if ts.startswith(today_str):
                acc_today_count[acc] = acc_today_count.get(acc, 0) + 1
                channel_today_count[ch] = channel_today_count.get(ch, 0) + 1
            # Rastreia último dia ativo
            if acc and ts:
                acc_last_active[acc] = max(acc_last_active.get(acc, ""), ts[:10])

    # Aplica cool-down: conta que trabalhou ontem tem 40% chance de descansar hoje
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    accounts_on_cooldown = set()
    for acc in valid_accs:
        last_day = acc_last_active.get(acc, "")
        if last_day == yesterday and random.random() < 0.4:
            accounts_on_cooldown.add(acc)
            log(f"Cool-down: {acc} descansando hoje")

    # Filtra contas que não estão em cool-down
    valid_accs = [a for a in valid_accs if a not in accounts_on_cooldown]

    # -------------------------------------------------------
    # ROTAÇÃO DE HORÁRIO POR CONTA (turnos aleatórios)
    # Cada conta tem um "turno" baseado no hash do email + dia.
    # Distribui as contas ao longo do dia pra parecer orgânico.
    # -------------------------------------------------------
    import hashlib
    current_hour = datetime.now().hour
    acc_hour_shift = {}
    for acc in valid_accs:
        h = hashlib.md5(f"{acc}{today_str}".encode()).hexdigest()
        shift_hours = int(h[:2], 16) % 6
        acc_preferred_hour = (8 + shift_hours * 3) % 24
        hour_diff = abs(current_hour - acc_preferred_hour)
        if hour_diff > 12:
            hour_diff = 24 - hour_diff
        acc_hour_shift[acc] = hour_diff

    # Filtra contas muito fora do turno (>4h de diferença)
    valid_accs_in_shift = [a for a in valid_accs if acc_hour_shift.get(a, 0) <= 4]
    if len(valid_accs_in_shift) >= 5:
        valid_accs = valid_accs_in_shift
        log(f"Turno: {len(valid_accs)} contas ativas nesta hora (de {len(valid_accs_in_shift) + len(accounts_on_cooldown)} total)")

    # Lock pra acesso seguro ao progress entre threads
    progress_lock = threading.Lock()

    # -------------------------------------------------------
    # MAPEAMENTO CONTA → CANAL (anti cross-channel)
    # Cada conta só engaja em 1 canal. Distribuído por hash
    # estável (mesmo canal todo dia). Evita que o YouTube veja
    # a mesma conta curtindo em vários canais do mesmo dono.
    # -------------------------------------------------------
    canais_ativos = [h for h in channel_data if h not in blacklist_ch]
    acc_canal = {}
    if canais_ativos:
        for acc in valid_accs:
            h = hashlib.md5(acc.encode()).hexdigest()
            idx = int(h[:8], 16) % len(canais_ativos)
            acc_canal[acc] = canais_ativos[idx]

    # -------------------------------------------------------
    # MONTAR FILA DE TAREFAS
    # Cada tarefa = (conta, url_video, idioma, canal)
    # -------------------------------------------------------
    task_queue = []

    # Faz uma cópia de quantos cada canal usou hoje pra decrementar limite dinamicamente
    current_channel_counts = dict(channel_today_count)

    for handle, data in channel_data.items():
        # Pula canais na blacklist ou que ja bateram limite diario global
        if handle in blacklist_ch:
            continue
        if current_channel_counts.get(handle, 0) >= max_per_channel_day:
            continue

        lang = data["lang"]
        all_urls = data["videos"] + data["shorts"]

        for video_url in all_urls:
            vid_key = video_url.split("&")[0]

            # Pula vídeos na blacklist
            if vid_key in blacklist_vid:
                continue

            # Inicializa progresso do vídeo se não existir
            if vid_key not in progress:
                progress[vid_key] = {
                    "engaged_by": [],
                    "channel": handle,
                    "lang": lang,
                }

            # Contas que ainda não engajaram esse vídeo E estão mapeadas pra este canal
            remaining_accs = [
                a for a in valid_accs
                if a not in progress[vid_key]["engaged_by"]
                and acc_canal.get(a) == handle
            ]
            # Respeita limite diário
            remaining_accs = [
                a for a in remaining_accs
                if acc_today_count.get(a, 0) < max_per_day
            ]

            for acc in remaining_accs:
                task_queue.append((acc, vid_key, lang, handle))

    # -------------------------------------------------------
    # PRIORIDADE — vídeos recentes + com poucos engajamentos primeiro
    # O JSON vem na ordem do YouTube: índice 0 = mais recente.
    # Vídeos com poucos engajamentos ganham boost de prioridade.
    # Horários de pico (timezone) também influenciam.
    # -------------------------------------------------------

    # Mapear posição original de cada vídeo no canal (menor = mais recente)
    video_position = {}
    for handle, data in channel_data.items():
        all_urls = data["videos"] + data["shorts"]
        for idx, url in enumerate(all_urls):
            vid_key = url.split("&")[0]
            video_position[vid_key] = idx

    # Contar engajamentos por vídeo (pra priorizar os com poucos)
    video_engagement_count = {}
    for vid_key, v in progress.items():
        video_engagement_count[vid_key] = len(v.get("engaged_by", []))

    # Randomizar dentro de mesma faixa pra não ser previsível por canal
    if cfg.get("randomize_order", True):
        random.shuffle(task_queue)

    # Ordenar por múltiplos critérios:
    # 1. Engajamentos (menos = mais urgente, normalizado em faixas de 5)
    # 2. Posição no canal (menor = mais recente)
    # 3. Peak hour bonus
    task_queue.sort(key=lambda t: (
        video_engagement_count.get(t[1], 0) // 5,
        video_position.get(t[1], 9999),
        -is_peak_hour(t[2]),
    ))

    if priority_channel and priority_channel in channel_data:
        priority_tasks = [t for t in task_queue if t[3] == priority_channel]
        other_tasks = [t for t in task_queue if t[3] != priority_channel]

        n_priority = int(max_actions * 0.7)
        task_queue = priority_tasks[:n_priority] + other_tasks

    task_queue = task_queue[:max_actions]

    # -------------------------------------------------------
    # AGRUPAR POR CONTA (cada conta abre 1 browser por chunk)
    # -------------------------------------------------------
    by_account = {}
    for acc, vid_key, lang, handle in task_queue:
        by_account.setdefault(acc, []).append((vid_key, lang, handle))

    log(
        f"Fila: {len(task_queue)} tarefas | "
        f"{len(by_account)} contas | "
        f"workers={workers} | mode={cfg.get('mode', 'both')}"
    )

    # -------------------------------------------------------
    # EXECUTAR EM PARALELO (com stagger entre workers)
    # -------------------------------------------------------
    actions_done = 0
    stagger_delay = cfg.get("stagger_seconds", 30)

    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {}
        worker_count = 0
        for acc, tasks in by_account.items():
            # Divide em chunks de CHUNK_SIZE (evita OOM)
            chunks = [
                tasks[i:i + CHUNK_SIZE]
                for i in range(0, len(tasks), CHUNK_SIZE)
            ]
            for chunk in chunks:
                future = executor.submit(
                    engage_batch_session, acc, chunk, cfg, progress, progress_lock
                )
                futures[future] = acc
                worker_count += 1
                # Stagger: espera entre submissões pra não abrir tudo ao mesmo tempo
                if worker_count % workers == 0 and stagger_delay > 0:
                    time.sleep(stagger_delay)

        # Coleta resultados conforme terminam (timeout 20min = 1200s)
        batch_timeout = 1200
        try:
            for future in as_completed(futures, timeout=batch_timeout):
                acc = futures[future]
                try:
                    count = future.result()
                    actions_done += count
                except Exception as e:
                    log(f"ERRO thread {acc}: {str(e)[:80]}")
        except TimeoutError:
            log(f"TIMEOUT batch apos {batch_timeout}s — cancelando workers restantes")
            for future in futures:
                future.cancel()

    # -------------------------------------------------------
    # FINALIZAR LOTE
    # -------------------------------------------------------
    save_progress(progress)

    # NÃO faz mais taskkill global (matava browsers de outras threads)
    # Cada worker mata seu próprio Chrome via kill_chrome(proc)
    time.sleep(3)

    return actions_done
