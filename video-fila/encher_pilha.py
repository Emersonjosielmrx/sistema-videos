r"""encher_pilha.py — mantém a pilha única de Shorts preparados (13/11/2026), FORA da rodada do alimentador do PC2.

Dona 13/11: "o sistema tem de se comportar como um só; todos sempre no máximo". A pilha (ocioso.PILHA_ALVO Shorts já
escolhidos e baixados, em estado\pc2_prontos) é de onde PC2, PC3 e STI pegam o próximo. Encher leva minutos (escolher +
esperar os baixadores de fora) e NÃO pode segurar o disparo: em 13/11, com isso dentro do alimentar_pc2.py, o PC2
ficou das 19:56 às 21:00 sem Short. Aqui é um processo à parte, com trava própria; o disparo de cada máquina continua
no seu script e nunca espera este.

    python encher_pilha.py        # 1 rodada (tarefa EncherPilha, a cada 5 min, pythonw)
Desligar: PILHA_PARALELA=0, ou criar estado\encher_pilha.off. Log: logs\encher_pilha.log.
"""
import os
import sys
import time
from pathlib import Path

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE))
LOG = BASE / "logs" / "encher_pilha.log"
TRAVA = BASE / "estado" / "encher_pilha.lock"


def log(m):
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(f"[{time.strftime('%d/%m %H:%M:%S')}] {m}\n")
    if LOG.stat().st_size > 2_000_000:
        LOG.write_text(LOG.read_text("utf-8")[-500_000:], "utf-8")


def main():
    if sys.stdout is None:
        sys.stdout = open(os.devnull, "w", encoding="utf-8")
    if (BASE / "estado" / "encher_pilha.off").exists():
        return 0
    import msvcrt
    TRAVA.parent.mkdir(parents=True, exist_ok=True)
    f = open(TRAVA, "a+")
    try:
        msvcrt.locking(f.fileno(), msvcrt.LK_NBLCK, 1)
    except OSError:
        return 0  # a rodada anterior ainda está esperando os downloads
    try:
        import controle
        import ocioso
        ocioso.log = log
        if not controle.ligado("parceiro", "producao")[0] or not controle.ligado("controlador", "producao")[0]:
            return 0
        # 13/11 (dona: "todos sempre no máximo"): o alvo da pilha acompanha a hora. De dia o que limita é o download;
        # de madrugada (0-7 h) sobra baixador de fora e IP de casa sem bloqueio — a pilha sobe pra PILHA_ALVO_NOITE
        # (padrão 14) e o dia começa com trabalho pronto pra todas as máquinas. PILHA_ALVO_NOITE=0 desliga.
        noite = int(os.environ.get("PILHA_ALVO_NOITE", "14"))
        if noite and time.localtime().tm_hour < 7:
            ocioso.PILHA_ALVO = max(ocioso.PILHA_ALVO, noite)
        n = ocioso.encher_pilha(max_seg=int(os.environ.get("PILHA_ESPERA_SEG", "300")))
        if n:
            log(f"rodada: +{n} na pilha (alvo {ocioso.PILHA_ALVO})")
    except Exception as e:  # noqa: BLE001
        log(f"[!] {type(e).__name__}: {str(e)[:200]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
