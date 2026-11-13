# -*- coding: utf-8 -*-
"""backup_caches.py — cópia de segurança dos caches do hipercool no Google Drive (rclone).

Só COPIA (rclone copy): nunca apaga nada do PC nem do Drive. Os caches continuam no PC
porque o pipeline usa; o Drive guarda tudo o que já existiu (se uma pasta for limpa por
engano — como a de vozes em 2026-10-12 —, dá pra restaurar).

Destino: manhwa-drive:caches-backup/hipercool/<nome>
Tarefa agendada: BackupCachesHipercool (diária, 06:10 — depois do BackupDriveVideos 05:40).

  python bin/backup_caches.py              # sobe o que for novo
  python bin/backup_caches.py --restaurar  # traz de volta o que falta no PC (não sobrescreve)
"""
import subprocess
import sys
from datetime import datetime
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
RCLONE = r"D:\tools\rclone.exe"
DRIVE = "manhwa-drive:caches-backup/hipercool"
LOG = PROJECT / "logs" / "backup_caches.log"
RCLONE_LOG = PROJECT / "logs" / "backup_caches_rclone.log"
CACHES = {
    "tts_cache": Path(r"D:\hipercool-materiais\tts_cache"),          # vozes (caro: TTS)
    "narration_cache": Path(r"D:\hipercool-materiais\narration_cache"),  # roteiro + editorial (visão/LLM)
    "censura_cache": PROJECT / "workspace" / "censura_cache",         # Sightengine + regiões Gemini
    "groq": PROJECT / "workspace" / "cache" / "groq",                 # tempo por palavra
}


def log(msg):
    linha = f"[{datetime.now():%Y-%m-%d %H:%M:%S}] {msg}"
    print(linha, flush=True)
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(linha + "\n")


def rclone(*args):
    r = subprocess.run([RCLONE, *args, "--retries", "5", "--low-level-retries", "20", "--tpslimit", "4",
                        "--timeout", "60s", "--contimeout", "30s", "--drive-stop-on-upload-limit",
                        "--log-file", str(RCLONE_LOG), "--log-level", "INFO"],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    return r.returncode


def main():
    restaurar = "--restaurar" in sys.argv
    if rclone("lsd", "manhwa-drive:") != 0:
        log(f"sem acesso ao Google Drive; refazer a autorização: {RCLONE} config reconnect manhwa-drive:")
        sys.exit(1)
    falhas = 0
    for nome, local in CACHES.items():
        if restaurar:
            local.mkdir(parents=True, exist_ok=True)
            rc = rclone("copy", f"{DRIVE}/{nome}", str(local), "--ignore-existing")
        else:
            if not local.exists():
                log(f"{nome}: pasta {local} não existe, pulando")
                continue
            rc = rclone("copy", str(local), f"{DRIVE}/{nome}")
        n = sum(1 for p in local.iterdir() if p.is_file()) if local.exists() else 0
        log(f"{nome}: {'restaurar' if restaurar else 'backup'} {'OK' if rc == 0 else f'ERRO {rc}'} ({n} arquivos no PC)")
        falhas += rc != 0
    sys.exit(1 if falhas else 0)


if __name__ == "__main__":
    main()
