"""baixa_prioridade.py — roda um comando de TESTE (voz, vídeo, análise) com prioridade BAIXA de CPU e de disco, para
não disputar com a produção (CORTES_08, 28/10 21:55: teste de vozes + 44 Chromes + 60 Pythons = PC1 a 100% e um
Short travado no ffmpeg). Fable 29/10 — ver FABLE_DECISOES.md D8.

    python D:\\video-fila\\baixa_prioridade.py <comando e argumentos…>
    ex.: python D:\\video-fila\\baixa_prioridade.py D:\\hipercool-materiais\\python\\venv_vozes\\Scripts\\python.exe teste.py final

Windows: BELOW_NORMAL_PRIORITY_CLASS + I/O "low" (via psutil, se houver). O filho herda. Sem janela.
"""
import subprocess
import sys

BELOW_NORMAL = 0x00004000
SEM_JANELA = 0x08000000


def main(argv):
    if not argv:
        print(__doc__)
        return 2
    # no terminal: herda a saída; em tarefa escondida (sem console) o filho não abre janela
    tem_console = bool(sys.stdout) and hasattr(sys.stdout, "isatty") and sys.stdout.isatty()
    # handles explícitos: com CREATE_NO_WINDOW o filho só escreve na nossa saída se ela for passada
    saida = {k: getattr(sys, k) for k in ("stdout", "stderr") if getattr(sys, k) is not None}
    p = subprocess.Popen(argv, creationflags=BELOW_NORMAL | (0 if tem_console else SEM_JANELA), **saida)
    try:
        import psutil
        pr = psutil.Process(p.pid)
        pr.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
        pr.ionice(psutil.IOPRIO_LOW)
    except Exception:  # noqa: BLE001 — sem psutil: só a classe de CPU já ajuda
        pass
    return p.wait()


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
