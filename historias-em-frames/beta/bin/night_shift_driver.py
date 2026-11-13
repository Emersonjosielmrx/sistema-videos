# -*- coding: utf-8 -*-
"""night_shift_driver.py — Orquestrador autônomo noturno.

Roda continuamente gerando vídeos de gêneros variados enquanto a máquina está livre.
Respeita COMMAND_STOP, registra tudo em logs/night-shift.md, manda Telegram.
Projetado pra ser chamado via cron ou manualmente antes de dormir.
"""
import os
import sys
import time
import json
import random
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).resolve().parent))

from hp_common import PROJECT_DIR, log
from story_pipeline import run, _check_command_files, COMMAND_STOP

LOG_FILE = PROJECT_DIR / "logs" / "night-shift.md"
MAX_VIDEOS_PER_SESSION = int(os.environ.get("NIGHT_MAX_VIDEOS", "10"))
COOLDOWN_BETWEEN = int(os.environ.get("NIGHT_COOLDOWN", "30"))

GENEROS_POOL = ["superacao", "romance", "terror", "comedia", "drama", "fantasia", "ficscifi"]
TEMAS_POR_GENERO = {
    "superacao": [
        "garoto cego que virou programador",
        "menina da favela que virou medica",
        "ex-presidiario que virou chef",
        "atleta que perdeu as pernas e voltou a competir",
        "imigrante que construiu um imperio",
    ],
    "romance": [
        "vizinhos que se odiavam mas se apaixonaram",
        "reencontro depois de 20 anos",
        "cartas anonimas que mudaram tudo",
        "amor proibido entre familias rivais",
        "o ultimo verao antes da faculdade",
    ],
    "terror": [
        "a casa que ninguem queria comprar",
        "boneca antiga no sotao",
        "ultimo passageiro do onibus da meia-noite",
        "espelho que mostra o futuro",
        "vila que desaparece do mapa todo outubro",
    ],
    "comedia": [
        "estagiario que virou CEO por engano",
        "avó que dominou o TikTok",
        "gato que controla a familia inteira",
        "vizinho que inventava desculpas absurdas",
        "robô doméstico com personalidade demais",
    ],
    "drama": [
        "carta que chegou 30 anos atrasada",
        "gemeos separados na maternidade",
        "professor que salvou um aluno do abismo",
        "segredo de familia revelado no funeral",
        "ultimo dia de um restaurante centenario",
    ],
    "fantasia": [
        "mundo onde sonhos viram realidade por 1 hora",
        "garoto que fala com animais mas ninguem acredita",
        "livraria onde os personagens saem das paginas",
        "relogio que para o tempo mas cobra um preco",
        "floresta que muda de forma toda noite",
    ],
    "ficscifi": [
        "IA que desenvolveu emocoes e fugiu do lab",
        "ultimo humano numa estacao espacial",
        "memoria vendida como moeda",
        "planeta onde o tempo anda ao contrario",
        "clone que descobriu que era o original",
    ],
}


def _log_night(msg):
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"- [{ts}] {msg}\n")


def _pick_job():
    """Escolhe gênero e tema aleatório, evitando repetição recente."""
    genero = random.choice(GENEROS_POOL)
    temas = TEMAS_POR_GENERO.get(genero, [None])
    tema = random.choice(temas) if temas else None
    return genero, tema


def run_night_shift(max_videos=None, preset="night", notify=True):
    """Loop principal do turno noturno."""
    max_v = max_videos or MAX_VIDEOS_PER_SESSION
    generated = 0
    failed = 0
    start = time.time()

    _log_night(f"### Turno noturno iniciado (max={max_v}, preset={preset})")
    log(f"NIGHT SHIFT: iniciando (max={max_v} videos, preset={preset})")

    # Health-check do pool de proxies no inicio do turno: marca os esgotados
    # (402 de banda) pra rotacao pular direto pros vivos. Nao bloqueia a
    # producao se falhar.
    try:
        import proxy_router
        n_live, n_dead, _ = proxy_router.health_check()
        _log_night(f"  proxies: {n_live} vivos, {n_dead} em cooldown")
        log(f"NIGHT: health-check proxies -> {n_live} vivos / {n_dead} mortos")
    except Exception as e:
        log(f"NIGHT: health-check proxies pulou ({e})")

    if notify:
        try:
            from _tg_safe import send_telegram
            send_telegram(f"Turno noturno iniciado: max {max_v} videos, preset={preset}")
        except Exception:
            pass

    for i in range(max_v):
        if COMMAND_STOP.exists():
            _log_night("STOP detectado — encerrando turno")
            log("NIGHT: COMMAND_STOP detectado")
            break

        genero, tema = _pick_job()
        log(f"\nNIGHT [{i+1}/{max_v}]: {genero} — {tema or 'aleatorio'}")
        _log_night(f"Job {i+1}: {genero} / {tema or 'aleatorio'}")

        t0 = time.time()
        try:
            result = run(
                genero=genero,
                tema=tema,
                preset=preset,
                output_suffix=f"_night{i+1}",
                skip_notify=True,
            )
            elapsed = time.time() - t0

            if result and result.get("video"):
                generated += 1
                _log_night(f"  OK: {result['titulo']} ({elapsed:.0f}s)")
            else:
                failed += 1
                _log_night(f"  FALHOU ({elapsed:.0f}s)")

        except Exception as e:
            failed += 1
            _log_night(f"  ERRO: {e}")
            log(f"  NIGHT ERROR: {e}")

        if i < max_v - 1:
            log(f"  Cooldown {COOLDOWN_BETWEEN}s...")
            time.sleep(COOLDOWN_BETWEEN)

    total_time = time.time() - start
    summary = (f"Turno noturno finalizado: {generated} OK, {failed} falhas, "
               f"{total_time/60:.0f} min total")
    _log_night(f"### {summary}")
    log(f"\nNIGHT SHIFT: {summary}")

    if notify:
        try:
            from _tg_safe import send_telegram
            send_telegram(summary)
        except Exception:
            pass

    return {"generated": generated, "failed": failed, "total_time": round(total_time)}


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Night Shift Driver — produção autônoma")
    parser.add_argument("--max", type=int, default=None, help="Max videos")
    parser.add_argument("--preset", default="night", choices=["teste", "final", "night"])
    parser.add_argument("--no-notify", action="store_true")
    args = parser.parse_args()

    run_night_shift(max_videos=args.max, preset=args.preset, notify=not args.no_notify)


if __name__ == "__main__":
    main()
