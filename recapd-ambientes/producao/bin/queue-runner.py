#!/usr/bin/env python3
"""queue-runner.py — Fila serial de capítulos (NUNCA 2 simultâneos).

Protege as chaves Gemini: só começa o próximo capítulo quando o atual
terminar a fase de LLM+TTS (ou seja, quando entrar na fase de código puro: clips, concat, etc).

O ponto de handoff é: quando o narration_cache E os áudios TTS estão prontos.
A partir daí, a montagem é puro FFmpeg (sem API).

Uso:
    python bin/queue-runner.py --caps 2 3 4 5 6 7 8 9
    python bin/queue-runner.py --caps 3-9
    python bin/queue-runner.py --caps 2 --dual   # 4 vídeos (Normal + HyperFrames)

Fluxo por capítulo:
    1. Scrape (tia-fetcher.py)
    2. Split (panel-splitter.py)
    3. LLM + TTS (hiper-pipeline.py — fase que usa chaves)
    4. Montagem de clips (FFmpeg puro — pode rodar em paralelo com scrape do próximo)
    5. Legendas, trilha, censura (FFmpeg puro)
"""
import argparse
import json
import os
import re
import subprocess
import sys
import threading
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import worker_client

PROJECT_DIR = Path(__file__).resolve().parent.parent
PYTHON = Path(sys.executable)  # cross-platform: usa o interpretador atual (venv Scripts/python.exe no Windows, venv/bin/python no *nix)
VIDEOS_DIR = PROJECT_DIR / "workspace" / "videos"
LOCK_FILE = PROJECT_DIR / "workspace" / ".queue_lock"
WORKERS_CONFIG = PROJECT_DIR / "workers.json"
QUEUE_STATE = PROJECT_DIR / "workspace" / "queue_state.json"


def load_state():
    """Lê queue_state.json (mapa obra→cap→{status,ts,mp4}). Falha graciosa → {}."""
    try:
        import json as _j
        return _j.loads(QUEUE_STATE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_state(state):
    try:
        import json as _j
        QUEUE_STATE.write_text(_j.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass


def mark_state(obra, cap, status):
    """Atualiza o estado de 1 cap ao FIM (ok/falha). Não interfere se IGNORAR_ESTADO."""
    if os.environ.get("IGNORAR_ESTADO") == "1":
        return
    import time as _t
    st = load_state()
    st.setdefault(obra, {})[str(cap)] = {"status": status, "ts": _t.strftime("%Y-%m-%dT%H:%M:%S")}
    save_state(st)


def should_skip(cap, obra, dual):
    """True se o cap já está 'ok' no estado E o mp4 valida. Respeita as flags de env."""
    if os.environ.get("IGNORAR_ESTADO") == "1" or os.environ.get("FORCAR_REPROCESSAMENTO") == "1":
        return False
    st = load_state().get(obra, {}).get(str(cap))
    if not st or st.get("status") != "ok":
        return False
    return validate_mp4(cap, obra, dual)


def log(msg):
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {msg}", file=sys.stderr)


def _pid_alive(pid):
    """Checagem NÃO-destrutiva de PID. No Windows os.kill(pid,0) chama
    TerminateProcess (mata o processo vivo!), então usamos tasklist."""
    if os.name == "nt":
        try:
            out = subprocess.run(
                ["tasklist", "/FI", f"PID eq {pid}", "/NH"],
                capture_output=True, text=True, timeout=10).stdout
            return str(pid) in out
        except Exception:
            return False
    try:
        os.kill(pid, 0)
        return True
    except PermissionError:
        return True
    except OSError:
        return False


def is_locked():
    """Verifica se outra instância está rodando."""
    if LOCK_FILE.exists():
        try:
            pid = int(LOCK_FILE.read_text().strip())
        except ValueError:
            LOCK_FILE.unlink(missing_ok=True)
            return False
        if _pid_alive(pid):
            return True
        LOCK_FILE.unlink(missing_ok=True)  # PID morto — limpar lock obsoleto
    return False


def acquire_lock():
    if is_locked():
        log("⚠ Outra instância do queue-runner está ativa. Saindo.")
        sys.exit(1)
    LOCK_FILE.write_text(str(os.getpid()))
    time.sleep(0.5)
    # Re-check: evita race condition se 2 instâncias iniciaram juntas
    try:
        pid_in_file = int(LOCK_FILE.read_text().strip())
    except (ValueError, OSError):
        pid_in_file = -1
    if pid_in_file != os.getpid():
        log("⚠ Race condition detectada — outra instância ganhou o lock. Saindo.")
        sys.exit(1)


def release_lock():
    LOCK_FILE.unlink(missing_ok=True)


def run_chapter(cap_num, dual=False, obra="the-meek-cat",
                base_url="https://tiamanhw.com/manhwa/{obra}/capitulo-{n}/",
                titulo_base=None):
    """Executa um capítulo completo: scrape → split → pipeline."""
    slug = f"{obra}-cap{cap_num:02d}"
    url = base_url.format(obra=obra, n=cap_num)
    if titulo_base:
        titulo = f"{titulo_base} — Capítulo {cap_num}"
    else:
        titulo = f"{obra.replace('-', ' ').title()} — Capítulo {cap_num}"
    panels_dir = PROJECT_DIR / "workspace" / "panels" / slug
    cache_dir = PROJECT_DIR / "workspace" / "cache" / slug

    log(f"╔══════════════════════════════════════════╗")
    log(f"║  CAPÍTULO {cap_num}: {titulo}")
    log(f"╚══════════════════════════════════════════╝")

    has_content = panels_dir.exists() and len(list(panels_dir.glob("*.jpg"))) >= 10
    
    # Passo 1: Scrape (se não tiver no cache e nem os painéis prontos)
    if not has_content and (not cache_dir.exists() or len(list(cache_dir.glob("*.jpg"))) < 5):
        log(f"  ▶ Scrape: {url}")
        r = subprocess.run(
            [str(PYTHON), "bin/tia-fetcher.py", "--url", url, "--slug", slug, "--max-panels", "50"],
            capture_output=True, text=True, timeout=120, cwd=str(PROJECT_DIR)
        )
        if r.returncode != 0:
            log(f"  ✗ Scrape falhou: {r.stderr[-200:]}")
            return False
        log(f"  ✓ Scrape OK")
    else:
        log(f"  ✓ Scrape [CACHE]")

    # Passo 2: Split (se não tiver painéis cortados)
    if not panels_dir.exists() or len(list(panels_dir.glob("*.jpg"))) < 10:
        log(f"  ▶ Split")
        r = subprocess.run(
            [str(PYTHON), "bin/panel-splitter.py", "--split",
             "--input", str(cache_dir), "--out", str(panels_dir), "--no-open"],
            capture_output=True, text=True, timeout=120, cwd=str(PROJECT_DIR)
        )
        if r.returncode != 0:
            log(f"  ✗ Split falhou: {r.stderr[-200:]}")
            return False
        log(f"  ✓ Split OK")
    else:
        log(f"  ✓ Split [CACHE]")

    # Passo 3: Pipeline
    if dual:
        log(f"  ▶ Dual Pipeline (4 vídeos)")
        cmd = [str(PYTHON), "bin/dual-pipeline.py",
               "--panels-dir", str(panels_dir),
               "--titulo", titulo,
               "--max-panels", "120"]
    else:
        log(f"  ▶ Pipeline Normal (2 vídeos)")
        cmd = [str(PYTHON), "bin/hiper-pipeline.py",
               "--panels-dir", str(panels_dir),
               "--titulo", titulo,
               "--max-panels", "120",
               "--subtitles", "--karaoke", "--censura",
               "--skip-notify"]

    r = subprocess.run(cmd, capture_output=False,
                       timeout=int(os.environ.get("BRANCH_TIMEOUT_S", "21600")), cwd=str(PROJECT_DIR))  # default 6h (era 2h)
    if r.returncode != 0:
        log(f"  ✗ Pipeline falhou (exit {r.returncode})")
        return False

    log(f"  ✓ Capítulo {cap_num} — CONCLUÍDO")
    return True


def load_workers():
    """Lê workers.json. Sempre garante o 'local'. Falha graciosa → só local."""
    local_only = [{"name": "local", "mode": "local", "gemini_key_range": None}]
    try:
        cfg = json.loads(WORKERS_CONFIG.read_text(encoding="utf-8"))
    except Exception as e:
        log(f"  ⚠ workers.json ausente/inválido ({e}); usando só local.")
        return local_only, {"min_caps": 2}
    workers = cfg.get("workers", [])
    if not any(w.get("mode") == "local" for w in workers):
        workers = local_only + workers
    dist = cfg.get("distribute", {"min_caps": 2})
    return workers, dist


def online_remote_workers(workers):
    """Filtra os workers remotos que respondem ao /health AGORA (HTTP, nunca ping)."""
    alive = []
    for w in workers:
        if w.get("mode") != "http" or not w.get("enabled", True):
            continue
        h = worker_client.health(w["host"], w["port"], timeout=2.0)
        if h:
            w = {**w, "_cores": h.get("cores", 1)}
            alive.append(w)
            log(f"  ✓ worker '{w['name']}' online ({w['host']}:{w['port']}, {h.get('cores','?')} cores)")
        else:
            log(f"  ✗ worker '{w['name']}' offline ({w['host']}:{w['port']}) — ignorado")
    return alive


def should_distribute(n_caps, dual, dist_cfg, remotes):
    """Mede ANTES de gerar se VALE A PENA mandar pro worker remoto.

    Regra (pedido da usuária): 1 vídeo só não compensa o custo de ida/volta;
    várias unidades sim. A 'carga' conta vídeos, não capítulos:
      - dual gera 2x (Normal + HyperFrames) por cap.
    Compilado/lote grande → distribui com folga. Abaixo do limiar → tudo local.
    """
    if not remotes:
        return False, "nenhum worker remoto online"
    videos_por_cap = 2 if dual else 1
    carga = n_caps * videos_por_cap
    minimo = int(dist_cfg.get("min_caps", 2))
    if carga < minimo:
        return False, f"carga {carga} < mínimo {minimo} (não compensa mandar pro worker)"
    return True, f"carga {carga} ≥ {minimo} e {len(remotes)} worker(s) online → distribui"


def validate_mp4(cap_num, obra, dual):
    """ffprobe: confirma que o(s) .mp4 do capítulo existe(m) e áudio≈vídeo.
    Retorna True se ao menos 1 vídeo do cap está válido (vídeo-áudio < 5s)."""
    cap_dir = VIDEOS_DIR / obra / f"cap{cap_num:02d}"
    mp4s = list(cap_dir.rglob("*.mp4"))
    if not mp4s:
        log(f"  ✗ validação cap {cap_num}: nenhum .mp4 em {cap_dir}")
        return False
    ok_any = False
    for mp4 in mp4s:
        try:
            vr = subprocess.run(
                ["ffprobe", "-v", "error", "-select_streams", "v:0",
                 "-show_entries", "stream=duration", "-of", "csv=p=0", str(mp4)],
                capture_output=True, text=True, timeout=60)
            ar = subprocess.run(
                ["ffprobe", "-v", "error", "-select_streams", "a:0",
                 "-show_entries", "stream=duration", "-of", "csv=p=0", str(mp4)],
                capture_output=True, text=True, timeout=60)
            vd = float(vr.stdout.strip() or 0)
            ad = float(ar.stdout.strip() or 0)
            if vd > 0 and abs(vd - ad) < 5:
                log(f"  ✓ {mp4.name}: vídeo {vd:.0f}s ≈ áudio {ad:.0f}s")
                ok_any = True
            else:
                log(f"  ✗ {mp4.name}: vídeo {vd:.0f}s vs áudio {ad:.0f}s — QUEBRADO")
        except Exception as e:
            log(f"  ✗ ffprobe falhou em {mp4.name}: {e}")
    return ok_any


def run_chapter_remote(worker, cap_num, dual, obra):
    """Manda o capítulo pro worker remoto via HTTP. Valida o resultado com ffprobe.
    Retorna True só se voltou E validou. Qualquer falha → False (caller faz fallback local)."""
    log(f"  ▶ cap {cap_num} → worker REMOTO '{worker['name']}' ({worker['host']})")
    payload = {
        "cap": cap_num, "obra": obra, "dual": dual,
        "gemini_key_range": worker.get("gemini_key_range"),
        "timeout_s": int(os.environ.get("BRANCH_TIMEOUT_S", "21600")),
    }
    res = worker_client.run_chapter(
        worker["host"], worker["port"], payload,
        timeout=int(os.environ.get("BRANCH_TIMEOUT_S", "21600")) + 120)
    if not res or not res.get("ok"):
        log(f"  ✗ worker '{worker['name']}' falhou/timeout no cap {cap_num} — fallback local")
        return False
    if not validate_mp4(cap_num, obra, dual):
        log(f"  ✗ cap {cap_num} voltou do worker mas NÃO validou — fallback local")
        return False
    log(f"  ✓ cap {cap_num} concluído no worker '{worker['name']}' e validado")
    return True


def parse_caps(caps_arg):
    """Parse '3-9' ou '2 3 4 5' para lista de inteiros."""
    result = []
    for item in caps_arg:
        if '-' in item:
            start, end = item.split('-', 1)
            result.extend(range(int(start), int(end) + 1))
        else:
            result.append(int(item))
    return result


def main():
    parser = argparse.ArgumentParser(description="Fila serial de capítulos")
    parser.add_argument("--caps", nargs="+", required=True,
                        help="Números dos capítulos (ex: 3 4 5 ou 3-9)")
    parser.add_argument("--dual", action="store_true",
                        help="Gera 4 vídeos por capítulo (Normal + HyperFrames)")
    parser.add_argument("--obra", default="the-meek-cat")
    parser.add_argument("--titulo-base", default=None,
                        help="Nome legível da obra (ex: 'O Guerreiro Regressou')")
    parser.add_argument("--workers", choices=["local", "remote", "auto"], default="auto",
                        help="auto (padrão: usa worker remoto se online, senão local) | remote (força) | local (só esta máquina)")
    args = parser.parse_args()

    caps = parse_caps(args.caps)
    log(f"Fila: {len(caps)} capítulos → {caps}")
    log(f"Modo: {'Dual (4 vídeos)' if args.dual else 'Normal (2 vídeos)'}")

    # Decide distribuição ANTES de gerar (mede se vale a pena).
    remotes = []
    distribute = False
    if args.workers in ("remote", "auto"):
        all_workers, dist_cfg = load_workers()
        remotes = online_remote_workers(all_workers)
        if args.workers == "auto":
            if remotes:
                distribute, motivo = should_distribute(len(caps), args.dual, dist_cfg, remotes)
            else:
                distribute, motivo = False, "nenhum worker remoto online (auto → local)"
        else:
            distribute, motivo = should_distribute(len(caps), args.dual, dist_cfg, remotes)
        log(f"  → distribuição: {'SIM' if distribute else 'NÃO'} ({motivo})")
    if not distribute:
        log(f"SERIAL: nunca 2 simultâneos (protege chaves Gemini)")

    acquire_lock()
    try:
        if distribute:
            done, failed = run_distributed(caps, remotes, args)
        else:
            done, failed = 0, 0
            for cap in caps:
                # T3: retoma de onde parou — pula cap já 'ok' validado (estado resiliente).
                if should_skip(cap, args.obra, args.dual):
                    log(f"  ⏭ cap {cap} já feito (status=ok, mp4 válido) → pulando")
                    done += 1
                    continue
                ok = run_chapter(cap, dual=args.dual, obra=args.obra,
                                 titulo_base=args.titulo_base)
                mark_state(args.obra, cap, "ok" if ok else "falha")
                if ok:
                    done += 1
                else:
                    failed += 1
                # Pausa entre capítulos (liberar handles/memória)
                if cap != caps[-1]:
                    log(f"  ⏳ Pausa de 5s entre capítulos...")
                    time.sleep(5)

        log(f"\n═══ FILA CONCLUÍDA: {done} ok, {failed} falhas ═══")
    finally:
        release_lock()


def run_distributed(caps, remotes, args):
    """Despacha capítulos entre máquinas. Cada remoto roda 1 cap por vez (rule #8:
    1 chave por máquina). O restante roda local em série. Worker que cair → o cap
    dele volta pra fila e roda LOCAL (fallback, nunca trava)."""
    pending = list(caps)
    done = failed = 0
    lock = threading.Lock()
    results = {}

    def worker_thread(worker):
        nonlocal done, failed
        while True:
            with lock:
                if not pending:
                    return
                cap = pending.pop(0)
            ok = run_chapter_remote(worker, cap, args.dual, args.obra)
            with lock:
                if ok:
                    results[cap] = "remote"
                    done += 1
                else:
                    # fallback: devolve pra fila pra rodar local
                    pending.append(cap)
                    log(f"  ↩ cap {cap} devolvido à fila (rodará local)")
                    return  # esse worker desistiu; não insiste

    threads = [threading.Thread(target=worker_thread, args=(w,), daemon=True) for w in remotes]
    for t in threads:
        t.start()

    # Enquanto os remotos trabalham, esta máquina também consome a fila (local).
    while True:
        with lock:
            if not pending:
                break
            cap = pending.pop(0)
        ok = run_chapter(cap, dual=args.dual, obra=args.obra, titulo_base=args.titulo_base)
        with lock:
            if ok:
                results[cap] = "local"
                done += 1
            else:
                failed += 1

    for t in threads:
        t.join()
    log(f"  Despacho: " + ", ".join(f"cap{c}={results.get(c,'falhou')}" for c in caps))
    return done, failed


if __name__ == "__main__":
    main()
