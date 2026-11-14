r"""alimentar_pc3.py — mantém o desktop (PC3) com Short entre as rodadas do controlador (13/11/2026).

Dona 13/11: "todos têm de estar sempre trabalhando no máximo". Medido em 13/11: o PC3 faz 1 Short em ~16 min e depois
ficava em mediana 13 min (até 145) PARADO esperando o próximo — 6 h ociosas no dia, 20 Shorts. Só o controlador geral
(a cada 10 min, rodada de vários minutos) disparava pra ele; o PC2 e o STI têm alimentador próprio.

Cada rodada: (1) traz o Short pronto (ocioso.buscar_parceiro_pc3); (2) se o PC3 está livre e a dona NÃO está usando
(as mesmas regras do disparo automático do controlador: maquinas.medir("desktop")["ocioso"] — câmera agendada, OBS,
microfone/câmera em uso, render rodando = não dispara), chama o disparar_pc3.py, que tem a trava dele e pega da pilha
única (ocioso.pegar_pronto) quando há Short preparado.
Nunca passa por cima do uso do desktop: com qualquer dúvida na medição, não dispara.

    python alimentar_pc3.py       # 1 rodada (tarefa AlimentarPC3, a cada 5 min, pythonw)
Desligar: criar estado\alimentar_pc3.off (o controlador continua disparando como antes). Log: logs\alimentar_pc3.log.
"""
import os
import subprocess
import sys
import time
from pathlib import Path

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE))
LOG = BASE / "logs" / "alimentar_pc3.log"
TRAVA = BASE / "estado" / "alimentar_pc3.lock"
_SEM_JANELA = getattr(subprocess, "CREATE_NO_WINDOW", 0)


def log(m):
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(f"[{time.strftime('%d/%m %H:%M:%S')}] {m}\n")
    if LOG.stat().st_size > 2_000_000:
        LOG.write_text(LOG.read_text("utf-8")[-500_000:], "utf-8")


def rodada():
    import controle
    import maquinas
    import ocioso
    ocioso.log = log
    if not controle.ligado("parceiro", "producao")[0] or not controle.ligado("controlador", "producao")[0]:
        return
    try:
        if ocioso.buscar_parceiro_pc3():
            return  # ainda fazendo o anterior
    except Exception as e:  # noqa: BLE001
        log(f"[!] trazer o pronto do PC3: {type(e).__name__}: {str(e)[:150]}")
        return
    if (BASE / "estado" / "pc3_parceiro.json").exists() or (BASE / "estado" / "disparar_pc3.lock.ocupada").exists():
        return
    m = maquinas.medir("desktop") or {}
    if m.get("cpu") is None or not m.get("ocioso"):
        # dona usando (câmera/OBS/chamada), fora do ar ou já renderizando: não dispara. Só registra quando muda.
        motivo = str(m.get("motivo") or "sem resposta")[:90]
        marca = BASE / "estado" / "alimentar_pc3_ultimo.txt"
        try:
            if marca.read_text(encoding="utf-8") != motivo:
                raise OSError
        except OSError:
            log(f"PC3 não recebe Short agora: {motivo}")
            marca.write_text(motivo, encoding="utf-8")
        return
    try:
        import transferencias
        if (transferencias._fixos() if hasattr(transferencias, "_fixos") else {}).get("cortes") == "pc1":
            return
    except Exception:  # noqa: BLE001
        pass
    t0 = time.time()
    # processo à parte (trava própria do disparar_pc3.py): se o controlador lançou um agora, este sai sozinho
    r = subprocess.run([sys.executable, str(BASE / "disparar_pc3.py")], cwd=str(BASE), creationflags=_SEM_JANELA,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=1500)
    if r.returncode == 0 and (BASE / "estado" / "pc3_parceiro.json").exists():
        log(f"DISPAROU Short no PC3 (preparo {round(time.time() - t0)} s)")
        (BASE / "estado" / "alimentar_pc3_ultimo.txt").unlink(missing_ok=True)


def main():
    if sys.stdout is None:
        sys.stdout = open(os.devnull, "w", encoding="utf-8")
    if (BASE / "estado" / "alimentar_pc3.off").exists():
        return 0
    import msvcrt
    TRAVA.parent.mkdir(parents=True, exist_ok=True)
    f = open(TRAVA, "a+")
    try:
        msvcrt.locking(f.fileno(), msvcrt.LK_NBLCK, 1)
    except OSError:
        return 0
    try:
        rodada()
    except subprocess.TimeoutExpired:
        log("[!] o disparo do PC3 passou de 25 min — fica pra próxima")
    except Exception as e:  # noqa: BLE001
        log(f"[!] {type(e).__name__}: {str(e)[:200]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
