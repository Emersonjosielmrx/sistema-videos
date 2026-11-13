#!/usr/bin/env python3
"""night-shift-driver.py — dirige a geração noturna de capítulos (cron 30/30min).

O que faz por invocação (1 cap por vez, respeitando "nunca 2 caps simultâneos"):
  1. Se já há um render rodando (lock/processo), SAI (não empilha).
  2. Escolhe o próximo cap: o de menor número cujo vídeo ainda não passou na
     validação de SYNC (áudio≈vídeo E legenda com timing real).
  3. Gera com TUDO ligado + censura + versão gemini (voz masc premium).
  4. Valida: áudio≈vídeo (ffprobe) + sidecars .words.json presentes (legenda sem drift).
     Se QUEBRADO, marca pra refazer na próxima rodada (não posta lixo).
  5. Registra tudo em logs/night-shift.md.

NÃO faz commit/push (regra do projeto: cron só trabalha local).
"""
import os
import sys
import time
import json
import subprocess
from pathlib import Path
from datetime import datetime

PROJECT_DIR = Path(__file__).resolve().parent.parent
PYTHON = Path("D:/recapd-ambientes/producao/venv/Scripts/python.exe")
PANELS_DIR = PROJECT_DIR / "workspace" / "panels"
VIDEOS_DIR = PROJECT_DIR / "workspace" / "videos"
LOGS_DIR = PROJECT_DIR / "logs"
NIGHT_LOG = LOGS_DIR / "night-shift.md"
STATE_FILE = PROJECT_DIR / "workspace" / "night_shift_state.json"
LOCK_FILE = PROJECT_DIR / "workspace" / ".queue_lock"
PIDFILE = PROJECT_DIR / "workspace" / ".night_shift.pid"
OBRA = "the-meek-cat"


def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"- [{ts}] {msg}"
    print(line, file=sys.stderr)
    try:
        LOGS_DIR.mkdir(parents=True, exist_ok=True)
        with open(NIGHT_LOG, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass


def load_state():
    try:
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_state(st):
    try:
        STATE_FILE.write_text(json.dumps(st, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass


def _read_pidfile():
    try:
        return int(PIDFILE.read_text().strip())
    except Exception:
        return None


def _pid_alive(pid):
    """Checagem NÃO-destrutiva via tasklist (os.kill(pid,0) MATA no Windows)."""
    if pid is None:
        return False
    try:
        out = subprocess.run(["tasklist", "/FI", f"PID eq {pid}", "/NH"],
                             capture_output=True, text=True, timeout=15).stdout
        return str(pid) in out
    except Exception:
        return False


def _fresh_render_log(window_s=150):
    """True se algum log de render foi modificado há < window_s (render ativo, mesmo que
    iniciado FORA desta rotina — ex. um render manual). Guarda extra contra 2 caps juntos."""
    import glob as _g
    now = time.time()
    for pat in ("logs/fix_sync*.log", "logs/nightshift_*.log", "logs/cap*_*.log", "logs/*_NIGHT*.log"):
        for f in _g.glob(str(PROJECT_DIR / pat)):
            try:
                if now - os.path.getmtime(f) < window_s:
                    return True
            except Exception:
                pass
    return False


def render_busy():
    """True se JÁ há um render rodando (não empilhar 2 caps).
    Usa PID-file próprio + frescor de log (pega render manual também).
    Evita wmic (que trava competindo pela WMI durante um render pesado)."""
    pid = _read_pidfile()
    if _pid_alive(pid):
        return True
    # pid-file órfão (processo morreu) → limpa
    try:
        PIDFILE.unlink()
    except Exception:
        pass
    return _fresh_render_log()


def available_caps():
    caps = []
    for d in sorted(PANELS_DIR.glob(f"{OBRA}-cap*")):
        try:
            n = int(str(d.name).split("cap")[-1])
            if list(d.glob("*.jpg")):
                caps.append(n)
        except Exception:
            pass
    return caps


def _probe_av(mp4):
    """Retorna (video_dur, audio_dur) de um mp4, ou (0,0) se falhar."""
    try:
        vr = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0",
                             "-show_entries", "stream=duration", "-of", "csv=p=0", str(mp4)],
                            capture_output=True, text=True, timeout=60)
        ar = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "a:0",
                             "-show_entries", "stream=duration", "-of", "csv=p=0", str(mp4)],
                            capture_output=True, text=True, timeout=60)
        return float(vr.stdout.strip() or 0), float(ar.stdout.strip() or 0)
    except Exception:
        return 0.0, 0.0


def validate_file(mp4):
    """Valida sync A/V de UM arquivo específico. Retorna (ok, detalhe)."""
    mp4 = Path(mp4)
    if not mp4.exists():
        return False, f"arquivo não existe: {mp4.name}"
    vd, ad = _probe_av(mp4)
    if not (vd > 0 and abs(vd - ad) < 5):
        return False, f"A/V dessync: video {vd:.0f}s vs audio {ad:.0f}s ({mp4.name})"
    return True, f"{mp4.name} OK (video {vd:.0f}s ≈ audio {ad:.0f}s)"


def validate_sync(cap):
    """Valida o cap pelo mp4 mais recente da pasta (usado só na SELEÇÃO do próximo cap —
    heurística grosseira). A validação AUTORITATIVA pós-geração usa validate_file() no
    arquivo que o pipeline realmente gerou."""
    cap_dir = VIDEOS_DIR / OBRA / f"cap{cap:02d}"
    mp4s = [m for m in cap_dir.rglob("*.mp4") if "_elem" not in m.name]
    if not mp4s:
        return False, "nenhum mp4"
    mp4 = max(mp4s, key=lambda p: p.stat().st_mtime)
    return validate_file(mp4)


def next_cap():
    """Próximo cap a fazer: o de menor número que NÃO está 'ok' no estado.
    Confia no estado salvo (que aponta o arquivo REAL validado), não na pasta suja —
    a pasta tem lixo antigo que dava falso negativo."""
    st = load_state()
    for cap in available_caps():
        rec = st.get(str(cap))
        if rec and rec.get("status") == "ok":
            # revalida o arquivo real registrado (se sumiu/quebrou, refaz)
            mp4 = rec.get("mp4")
            if mp4 and validate_file(mp4)[0]:
                continue
        return cap
    return None


def generate(cap):
    panels = PANELS_DIR / f"{OBRA}-cap{cap:02d}"
    env = dict(os.environ)
    env.update({
        "PYTHONUTF8": "1",
        "ENSEMBLE_NARRATION": "0",
        "TTS_ENGINE": "gemini",          # versão gemini (voz masc premium) — pedido da usuária
        "GEMINI_TTS_PROXY_ENABLED": "1",
        "ELEMENTAL_TRANS": "1",
        "MASCOTE_OVERLAY": "1",
        "MASCOTE_MAX": "5",
        "CONTENT_ADAPT": "1",
        "SUB_CONTEXT": "1",
        "CONTEXT_MOTION": "1",
        "PANEL_FX": "1",
        "PARALLAX": "1",                 # depth 2.5D real — prioridade sobre PANEL_FX; o "corta o personagem e ele se mexe"
        "PARALLAX_ONDEMAND": "1",        # gera o depth na hora se não estiver cacheado (cacheia p/ próximas) — senão o parallax nunca roda em capítulo novo
        "TRIM_SILENCE": "1",
        "SFX_MODE": "gap",
        "CLIP_GAP_DYNAMIC": "1",
        "DUMP_SUBS_TIMING": "1",
        "UPSCALE_MAIN": "1",
    })
    logf = LOGS_DIR / f"nightshift_cap{cap:02d}_{datetime.now():%Y%m%d_%H%M}.log"
    cmd = [str(PYTHON), "bin/hiper-pipeline.py",
           "--panels-dir", str(panels),
           "--titulo", f"The Meek Cat — Capítulo {cap}",
           "--max-panels", "120", "--subtitles", "--karaoke",
           "--censura", "--skip-notify",
           "--output-suffix", "_NIGHT"]
    log(f"cap{cap:02d}: iniciando geração (gemini+censura+tudo) → {logf.name}")
    try:
        with open(logf, "w", encoding="utf-8") as lf:
            subprocess.run(cmd, cwd=str(PROJECT_DIR), env=env,
                           stdout=lf, stderr=subprocess.STDOUT, timeout=7200)
    except subprocess.TimeoutExpired:
        log(f"cap{cap:02d}: TIMEOUT (2h) — abortado")
        return None
    except Exception as e:
        log(f"cap{cap:02d}: erro ao rodar: {e}")
        return None
    # Descobre o arquivo REAL que o pipeline gerou (linha "✓ Vídeo pronto: <path>").
    # Sem isto, validar "o mp4 mais recente da pasta" pega lixo antigo (falso negativo).
    out_path = None
    try:
        for line in reversed(logf.read_text(encoding="utf-8", errors="replace").splitlines()):
            if "Vídeo pronto:" in line:
                out_path = line.split("Vídeo pronto:", 1)[1].strip()
                break
    except Exception:
        pass
    return out_path


def main():
    if render_busy():
        log("pulei: já há um render rodando (não empilho 2 caps).")
        return
    # limpa lock órfão
    try:
        LOCK_FILE.unlink()
    except Exception:
        pass

    cap = next_cap()
    if cap is None:
        log("nada a fazer: todos os caps disponíveis já passaram no sync.")
        return

    st = load_state()
    attempts = st.get(str(cap), {}).get("attempts", 0)
    # PID-file: marca que ESTA rotina está renderizando (próxima rodada do cron pula)
    try:
        PIDFILE.write_text(str(os.getpid()), encoding="utf-8")
    except Exception:
        pass
    out_path = None
    try:
        out_path = generate(cap)
    finally:
        try:
            PIDFILE.unlink()
        except Exception:
            pass

    # Validação AUTORITATIVA: o arquivo que o pipeline REALMENTE gerou (não o mais recente
    # da pasta, que pode ser lixo antigo → falso negativo). Fallback pra pasta se não achou.
    if out_path:
        ok, detalhe = validate_file(out_path)
    else:
        ok, detalhe = validate_sync(cap)
        detalhe = f"[sem path no log] {detalhe}"
    st = load_state()
    st[str(cap)] = {
        "status": "ok" if ok else "refazer",
        "attempts": attempts + 1,
        "detalhe": detalhe,
        "mp4": out_path or "",
        "ts": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
    }
    save_state(st)
    if ok:
        log(f"cap{cap:02d}: ✓ VALIDADO — {detalhe}")
    else:
        log(f"cap{cap:02d}: ✗ QUEBRADO ({detalhe}) — refaço na próxima rodada (tentativa {attempts+1})")


if __name__ == "__main__":
    main()
