# -*- coding: utf-8 -*-
"""backup_caches.py — cópia de segurança dos caches do hipercool no Google Drive (rclone).

Só COPIA (rclone copy): nunca apaga nada do PC nem do Drive. Os caches continuam no PC
porque o pipeline usa; o Drive guarda tudo o que já existiu (se uma pasta for limpa por
engano — como a de vozes em 2026-10-12 —, dá pra restaurar).

Destino: manhwa-drive:caches-backup/hipercool/<nome>
Tarefa agendada: BackupCachesHipercool (diária, 06:10 — depois do BackupDriveVideos 05:40).

  python bin/backup_caches.py              # sobe o que é novo (rápido: só arquivos de até 3 dias)
  python bin/backup_caches.py --completo   # varredura inteira (acontece sozinha a cada 7 dias)
  python bin/backup_caches.py --restaurar  # traz de volta o que falta no PC (não sobrescreve)
  python bin/backup_caches.py --checar     # o backup de hoje fechou? avisa no Telegram se não

16/10: a rodada de 15/10 morreu no meio (a tarefa agendada matou em 2 h, 0x8007042B) e NINGUÉM
soube — o log deste script não tem uma linha daquele dia. Por isso, daqui pra frente: pasta cara
primeiro, log no INÍCIO de cada pasta, aviso no Telegram em qualquer falha e teto de tempo próprio,
menor que o da tarefa.
"""
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import sem_janela  # noqa: E402,F401  (rclone sem janela na tela: roda no pythonw)

PROJECT = Path(__file__).resolve().parent.parent
RCLONE = r"D:\tools\rclone.exe"
DRIVE = "manhwa-drive:caches-backup/hipercool"
LOG = PROJECT / "logs" / "backup_caches.log"
RCLONE_LOG = PROJECT / "logs" / "backup_caches_rclone.log"
# Data (YYYY-MM-DD) da última varredura COMPLETA que deu certo. Sem ela o --max-age abriria buraco
# permanente no Drive: arquivo nascido num dia de backup quebrado nunca mais subiria.
MARCA_COMPLETO = PROJECT / "logs" / "backup_caches_completo.txt"
DIAS_COMPLETO = 7          # de quantos em quantos dias a varredura inteira roda sozinha
IDADE_RAPIDA = "3d"        # na rodada rápida, só sobe arquivo mexido nos últimos 3 dias
# A tarefa agendada tem ExecutionTimeLimit=PT2H e MATA o processo ao estourar (15/10: 1h54 só no
# tts_cache e o resto não subiu). Paramos antes, com log e aviso, pra falta de tempo virar recado
# em vez de silêncio.
LIMITE_S = 100 * 60
# ORDEM IMPORTA: do mais caro de refazer pro mais barato. O tts_cache (2323 wavs, ~1 GB) ficou por
# ÚLTIMO de propósito — era o primeiro e sozinho estourava as 2 h da tarefa, deixando narração
# (LLM/visão, o cache mais caro do projeto), censura e groq sem backup nenhum em 15 e 16/10.
CACHES = {
    "narration_cache": Path(r"D:\hipercool-materiais\narration_cache"),  # roteiro + editorial (visão/LLM)
    "censura_cache": PROJECT / "workspace" / "censura_cache",         # Sightengine + regiões Gemini
    "groq": PROJECT / "workspace" / "cache" / "groq",                 # tempo por palavra
    "tts_cache": Path(r"D:\hipercool-materiais\tts_cache"),           # vozes (caro: TTS) — o maior, por último
}


def log(msg):
    linha = f"[{datetime.now():%Y-%m-%d %H:%M:%S}] {msg}"
    print(linha, flush=True)
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(linha + "\n")


def avisar(msg):
    """Telegram. O backup é a ÚNICA rede das vozes (sumiram em 12/10 'por causa desconhecida'):
    falhar calado já custou 15 e 16/10. Aviso quebrado nunca derruba o backup."""
    try:
        import _tg_safe
        _tg_safe.send(f"🎬 hipercool backup: {_tg_safe.esc(msg)}")
    except Exception as e:  # noqa: BLE001
        log(f"(aviso no Telegram falhou: {str(e)[:80]})")


def rclone(*args):
    # --transfers/--checkers acima do padrão (4/8): são milhares de arquivos pequenos e o gargalo é
    # espera de rede, não banda (15/10: 663 MiB em 1h54 = ~100 KiB/s com 4 transferências).
    # O --tpslimit sobe junto pra não virar o novo teto (o Drive aguenta ~10 req/s por usuário).
    r = subprocess.run([RCLONE, *args, "--retries", "5", "--low-level-retries", "20", "--tpslimit", "8",
                        "--transfers", "8", "--checkers", "16",
                        "--timeout", "60s", "--contimeout", "30s", "--drive-stop-on-upload-limit",
                        "--log-file", str(RCLONE_LOG), "--log-level", "INFO"],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    return r.returncode


def _conta(local):
    return sum(1 for p in local.iterdir() if p.is_file()) if local.exists() else 0


def _precisa_completo():
    """Varredura inteira se nunca houve uma ou se a última passou de DIAS_COMPLETO."""
    try:
        ultima = datetime.strptime(MARCA_COMPLETO.read_text(encoding="utf-8").strip()[:10], "%Y-%m-%d")
    except Exception:  # noqa: BLE001  (sem marca legível = nunca rodou completo)
        return True
    return (datetime.now() - ultima).days >= DIAS_COMPLETO


def backup_do_dia_ok(dia=None):
    """Todas as pastas fecharam ('backup OK' ou 'pulando') no dia? Pro `fila.py status` avisar:
    em 15 e 16/10 a tarefa morreu, o log não teve UMA linha e ninguém percebeu por 2 dias."""
    dia = dia or f"{datetime.now():%Y-%m-%d}"
    if not LOG.exists():
        return False
    fechadas = set()
    for linha in LOG.read_text(encoding="utf-8", errors="replace").splitlines():
        if not linha.startswith(f"[{dia}") or "] " not in linha:
            continue
        corpo = linha.split("] ", 1)[1]
        nome = corpo.split(":", 1)[0]
        if nome in CACHES and ("backup OK" in corpo or "pulando" in corpo):
            fechadas.add(nome)
    return all(n in fechadas for n in CACHES)


def main():
    restaurar = "--restaurar" in sys.argv
    if "--checar" in sys.argv:
        ok = backup_do_dia_ok()
        log(f"checagem: backup de hoje {'completo' if ok else 'INCOMPLETO'}")
        if not ok:
            avisar("o backup dos caches de hoje NÃO fechou (ver logs/backup_caches.log)")
        sys.exit(0 if ok else 1)

    completo = restaurar or "--completo" in sys.argv or _precisa_completo()
    if rclone("lsd", "manhwa-drive:") != 0:
        log(f"sem acesso ao Google Drive; refazer a autorização: {RCLONE} config reconnect manhwa-drive:")
        avisar(f"sem acesso ao Google Drive — refazer: {RCLONE} config reconnect manhwa-drive:")
        sys.exit(1)
    t0 = time.time()
    falhas = 0
    for nome, local in CACHES.items():
        if not restaurar and not local.exists():
            log(f"{nome}: pasta {local} não existe, pulando")
            continue
        if time.time() - t0 > LIMITE_S:
            # Melhor parar avisando do que ser morto pela tarefa agendada no meio de um upload.
            log(f"{nome}: SEM TEMPO ({(time.time() - t0) / 60:.0f} min já), fica pra próxima rodada")
            avisar(f"backup parou por tempo antes de {nome} — ver logs/backup_caches.log")
            falhas += 1
            break
        modo = "restaurar" if restaurar else ("backup completo" if completo else f"backup dos últimos {IDADE_RAPIDA}")
        log(f"{nome}: começando {modo} ({_conta(local)} arquivos no PC)")
        if restaurar:
            local.mkdir(parents=True, exist_ok=True)
            rc = rclone("copy", f"{DRIVE}/{nome}", str(local), "--ignore-existing")
        else:
            # --max-age: na rodada do dia a dia só sobe o que mudou; a varredura inteira é semanal.
            extra = [] if completo else ["--max-age", IDADE_RAPIDA]
            rc = rclone("copy", str(local), f"{DRIVE}/{nome}", *extra)
        log(f"{nome}: {'restaurar' if restaurar else 'backup'} {'OK' if rc == 0 else f'ERRO {rc}'} "
            f"({_conta(local)} arquivos no PC, {(time.time() - t0) / 60:.0f} min)")
        if rc != 0:
            avisar(f"{nome}: rclone falhou (rc {rc}) — ver logs/backup_caches_rclone.log")
        falhas += rc != 0
    if completo and not falhas and not restaurar:
        MARCA_COMPLETO.write_text(f"{datetime.now():%Y-%m-%d}\n", encoding="utf-8")
    sys.exit(1 if falhas else 0)


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception as e:  # noqa: BLE001  (morrer calado foi o problema de 15/10)
        log(f"[X] backup abortou: {type(e).__name__}: {str(e)[:200]}")
        avisar(f"backup abortou: {type(e).__name__}: {str(e)[:150]}")
        sys.exit(1)
