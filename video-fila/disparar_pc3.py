r"""disparar_pc3.py — dispara 1 Short de parceiro no PC3 (desktop) FORA da rodada do controlador (12/11/2026).

Por quê: o disparo do PC3 (ocioso.disparar_parceiro_pc3) BAIXA a fonte aqui antes de mandar — e o download espera a vez
do yt-dlp (até 30 min + o espaçamento entre downloads; o PC2 tem prioridade). Rodando DENTRO da rodada, o controlador
inteiro ficava parado esperando (12/11: rodadas de 09:20 e 08:20 presas 30+ min em ytdlp_vez.vez; painel "controlador
parado"; PC1/PC2 sem disparo nesse tempo). O PC2 já tinha resolvido isso em 30/10 (AlimentarPC2 prepara fora da rodada).

Agora o controlador só lança este processo (job "cortes_desktop": enquanto ele vive, a rodada não lança outro) e segue.
Trava própria (estado\disparar_pc3.lock): nunca 2 ao mesmo tempo. Log: logs\disparar_pc3.log (e o do controlador).

    python disparar_pc3.py
"""
import msvcrt
import sys
import time
from pathlib import Path

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE))
LOG = BASE / "logs" / "disparar_pc3.log"
TRAVA = BASE / "estado" / "disparar_pc3.lock"


def log(m):
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(f"[{time.strftime('%d/%m %H:%M:%S')}] {m}\n")


def main():
    TRAVA.parent.mkdir(parents=True, exist_ok=True)
    f = open(TRAVA, "a+")
    try:
        msvcrt.locking(f.fileno(), msvcrt.LK_NBLCK, 1)
    except OSError:
        log("outro disparo pro PC3 em andamento — este sai")
        return 0
    try:
        import transferencias
        transferencias.log = log
        try:
            r = transferencias.disparar("cortes", "desktop")
            log(f"OK: {r}")
            return 0
        except RuntimeError as e:
            log(f"PC3: {e}")
            return 1
        except Exception as e:  # noqa: BLE001
            log(f"[!] disparo do PC3 falhou: {type(e).__name__}: {e}")
            return 1
    finally:
        try:
            f.seek(0)
            msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, 1)
        except OSError:
            pass
        f.close()


if __name__ == "__main__":
    sys.exit(main())
