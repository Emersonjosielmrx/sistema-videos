"""
main.py — Entry point do MEGA ENGAGE v3.

OBJETIVO:
    Loop infinito que:
    1. Verifica flags (stop/restart)
    2. Executa um lote de engajamento
    3. Calcula progresso geral
    4. Se atingiu 100%, para
    5. Senão, espera 15s e repete

COMO RODAR:
    cd D:/projetos-navegador
    D:/hipercool-videos/venv/Scripts/python.exe mega_engage.py

    Ou pelo RODAR_ENGAGE.bat (que também abre proxy e server)

PARA PARAR:
    - Criar arquivo engage_stop.flag na pasta
    - Ou POST /stop no server (porta 8850)
    - Ou Ctrl+C no console

DEPENDENCIAS:
    - config.py (PID_FILE, TARGET_TOTAL)
    - progress.py (load_progress, count_total_engagements)
    - scheduler.py (run_batch)
    - logger.py (log)
    - flags.py (check_flags)
"""
import os
import sys
import time
import msvcrt

from .config import PID_FILE, TARGET_TOTAL, BASE_DIR, load_config
from .progress import load_progress, count_total_engagements
from .scheduler import run_batch
from .logger import log
from .flags import check_flags

LOCK_FILE = BASE_DIR / "engage_bot.lock"


def acquire_lock():
    """
    Garante que só 1 instância do bot roda. Retorna o file handle (que DEVE
    ficar aberto pela vida do processo) ou encerra o processo se outra já roda.

    Como funciona:
      - Abrimos engage_bot.lock e pegamos um lock exclusivo via msvcrt.locking.
      - Se OUTRO processo já tem o lock, msvcrt levanta OSError → este 2º
        processo imprime aviso e sai (sys.exit) sem atrapalhar o 1º.
      - O SO libera o lock AUTOMATICAMENTE quando o processo dono morre, então
        não fica "lock órfão" travando reinícios (não precisa apagar o arquivo).

    IMPORTANTE: nunca apague engage_bot.lock com um bot vivo — isso quebra a
    exclusão e deixa 2 instâncias subirem. Só apague se tiver CERTEZA que o bot
    está parado (nenhum python rodando mega_engage.py).
    """
    try:
        # O_CREAT|O_RDWR cria se não existe e NÃO trunca (evita corrida na largada)
        fd = os.open(str(LOCK_FILE), os.O_CREAT | os.O_RDWR)
        fh = os.fdopen(fd, "r+")
        msvcrt.locking(fh.fileno(), msvcrt.LK_NBLCK, 1)
        fh.seek(0)
        fh.truncate()
        fh.write(str(os.getpid()))
        fh.flush()
        return fh
    except (OSError, IOError):
        print("Outra instancia do bot ja esta rodando (file lock). Saindo.")
        sys.exit(0)


def main():
    """
    Loop principal do bot. Roda até completar a missão ou receber stop.
    Auto-recupera de lotes vazios com backoff progressivo.
    """
    lock_fh = acquire_lock()

    PID_FILE.write_text(str(os.getpid()), encoding="utf-8")

    log("=== MEGA ENGAGE v3 iniciado (batch-session, subscribe, watch-time, fingerprint) ===")

    consecutive_empty = 0

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
            consecutive_empty += 1
            if consecutive_empty >= 10:
                log("10 crashes seguidos. Aguardando 5min antes de retry...")
                time.sleep(300)
                consecutive_empty = 0
            continue

        # Backoff quando lote volta vazio (proxy morto, contas mortas, etc)
        if total == 0:
            consecutive_empty += 1
            cfg = load_config()
            if not cfg.get("paused", False):
                backoff = min(300, 30 * consecutive_empty)
                log(f"Lote vazio #{consecutive_empty}. Retry em {backoff}s...")
                time.sleep(backoff)
                continue
        else:
            consecutive_empty = 0

        progress = load_progress()
        total_done = count_total_engagements(progress)
        pct = (total_done / TARGET_TOTAL * 100) if TARGET_TOTAL else 0
        log(f"Progresso geral: {total_done}/{TARGET_TOTAL} ({pct:.1f}%)")

        if total_done >= TARGET_TOTAL:
            log("=== MISSAO COMPLETA ===")
            break

        log("Proximo lote em 15s...")
        time.sleep(15)

    lock_fh.close()
