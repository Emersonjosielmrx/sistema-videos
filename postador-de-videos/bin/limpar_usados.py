#!/usr/bin/env python3
"""limpar_usados.py — Move videos ja postados no YouTube E TikTok pra _usados.

Logica:
- Estar em _postados/vo3 ou _postados/recaps = ja postou no YouTube
- Estar no tiktok_auto_posted.json = ja postou no TikTok
- Se postou nos DOIS → move pra _usados/ (pode deletar ou mover pra outro disco)

Roda automaticamente no final do postar_tudo_auto.bat ou manualmente.
"""
import json
import shutil
import sys
from datetime import datetime
from pathlib import Path

if sys.stdout:  # pythonw (tarefa agendada) não tem stdout

    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
POSTADOS_VO3 = Path(r"D:\hipercool-materiais\_postados\vo3")
POSTADOS_RECAPS = Path(r"D:\hipercool-materiais\_postados\recaps")
USADOS_DIR = Path(r"D:\hipercool-materiais\_usados")
TIKTOK_LOG = Path(r"D:\postador-de-videos\logs\tiktok_auto_posted.json")
LOG_FILE = Path(r"D:\postador-de-videos\logs\limpar_usados.log")


def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    try:
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass


def load_tiktok_posted():
    if TIKTOK_LOG.exists():
        try:
            return {e["file"] for e in json.loads(TIKTOK_LOG.read_text(encoding="utf-8"))}
        except Exception:
            return set()
    return set()


def mover_usados(pasta_postados, subpasta_usados, tiktok_files):
    dest = USADOS_DIR / subpasta_usados
    dest.mkdir(parents=True, exist_ok=True)
    movidos = 0

    if not pasta_postados.exists():
        return 0

    for mp4 in list(pasta_postados.glob("*.mp4")):
        if mp4.name not in tiktok_files:
            continue

        dst = dest / mp4.name
        if dst.exists():
            dst = dest / f"{mp4.stem}_{datetime.now().strftime('%H%M%S')}{mp4.suffix}"

        try:
            shutil.move(str(mp4), str(dst))
            movidos += 1

            for ext in [".pos.json", ".postar.json", ".json", ".txt"]:
                meta = mp4.with_suffix(ext)
                if meta.exists():
                    shutil.move(str(meta), str(dest / meta.name))
        except Exception as e:
            log(f"  ERRO movendo {mp4.name}: {e}")

    return movidos


def main():
    dry_run = "--dry-run" in sys.argv

    log("=== INICIO limpar_usados ===")

    tiktok_files = load_tiktok_posted()
    log(f"TikTok posted log: {len(tiktok_files)} arquivos")

    if dry_run:
        log("MODO DRY-RUN (nao move nada)")

    total = 0
    for pasta, sub in [(POSTADOS_VO3, "vo3"), (POSTADOS_RECAPS, "recaps")]:
        if not pasta.exists():
            log(f"  {pasta} nao existe, pulando")
            continue

        mp4s = list(pasta.glob("*.mp4"))
        em_ambos = [f for f in mp4s if f.name in tiktok_files]
        so_yt = len(mp4s) - len(em_ambos)

        log(f"  {sub}: {len(mp4s)} total, {len(em_ambos)} em ambos (YT+TikTok), {so_yt} so YouTube")

        if dry_run:
            for f in em_ambos[:5]:
                log(f"    -> moveria: {f.name}")
            if len(em_ambos) > 5:
                log(f"    ... e mais {len(em_ambos)-5}")
        else:
            n = mover_usados(pasta, sub, tiktok_files)
            log(f"  {sub}: {n} movidos pra _usados/{sub}/")
            total += n

    if not dry_run:
        log(f"TOTAL movidos: {total}")
    log("=== FIM limpar_usados ===")


if __name__ == "__main__":
    main()
