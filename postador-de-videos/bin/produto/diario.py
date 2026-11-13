"""Produção diária dos vídeos PROFISSIONAIS de produto (tarefa Produto_Videos, 2x por dia).

Para cada conta de produto (config\\marcas_instagram.json com "produto"): se a fila tem menos de ALVO vídeos prontos,
gera 1. Veo em dias alternados por conta (o crédito do Veo é dividido com o entretenimento e o MS Energy); sem conta
livre no Veo o vídeo sai só com imagem do Flow + conversa animada. Uma rodada por vez (trava) e espera memória.

    D:\\veo\\venv\\Scripts\\python.exe -m produto.diario [--alvo 3] [--conta X]
"""
import argparse
import hashlib
import sys
import time
from datetime import date, datetime
from pathlib import Path

BIN = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BIN))
from produto import fila, kit, variacoes, video  # noqa: E402

TRAVA = Path(r"D:\video-fila\produto_tmp\.rodando")


def log(m):
    print(f"[{datetime.now():%H:%M:%S}] {m}", flush=True)


def _memoria_ok(minimo_gb=1.3, espera_max_s=1200):
    try:
        import psutil
    except ImportError:
        return True
    t0 = time.time()
    while psutil.virtual_memory().available / 2 ** 30 < minimo_gb:
        if time.time() - t0 > espera_max_s:
            return False
        log(f"  memória baixa ({psutil.virtual_memory().available / 2 ** 30:.1f} GB) — espero 60 s")
        time.sleep(60)
    return True


def _trava_viva():
    """28/10: a rodada de 27/10 21:21 morreu no Veo e a trava (sem dono) segurou a de 04:41 -> a trava guarda o PID e
    só vale enquanto esse processo vive (trava antiga sem PID = regra das 10 h)."""
    if not TRAVA.exists() or time.time() - TRAVA.stat().st_mtime >= 10 * 3600:  # 26/10: o editor leva até ~3 h/vídeo
        return False
    pid = TRAVA.read_text("utf-8", errors="ignore").split("|")[-1].strip()
    if not pid.isdigit():
        return True
    try:
        import psutil
        return psutil.pid_exists(int(pid)) and "python" in psutil.Process(int(pid)).name().lower()
    except Exception:  # noqa: BLE001
        return True


def _marcar_trava():
    import os
    TRAVA.write_text(f"{datetime.now().isoformat()}|{os.getpid()}", "utf-8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--alvo", type=int, default=3)
    ap.add_argument("--conta")
    ap.add_argument("--um", help=argparse.SUPPRESS)  # filho: gera 1 vídeo desta conta e sai (sem trava própria)
    ap.add_argument("--variante", help=argparse.SUPPRESS)
    a = ap.parse_args()
    if a.um:
        video.gerar(a.um, log=log, variante=a.variante or None)
        return
    TRAVA.parent.mkdir(parents=True, exist_ok=True)
    if _trava_viva():
        log("outra rodada em andamento — saio")
        return
    _marcar_trava()
    try:  # v1 do ccv: prioridade baixa (ffmpeg, Remotion e Chrome filhos herdam) — não atrapalha as outras linhas
        import psutil
        psutil.Process().nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
    except Exception:  # noqa: BLE001
        pass
    try:
        variacoes.medir(log)  # atualiza as views antes de escolher as variações do dia
    except Exception as e:  # noqa: BLE001
        log(f"[variações] medir falhou: {type(e).__name__}: {str(e)[:120]}")
    try:
        for conta in ([a.conta] if a.conta else kit.contas_produto()):
            n = len(fila.pendentes(conta))
            if n >= a.alvo:
                log(f"{conta}: {n} prontos na fila — nada a fazer")
                continue
            if not _memoria_ok():
                log("memória não aliviou em 20 min — paro a rodada")
                break
            # 25/10 (dono): ele como personagem em todos os produtos, VARIANDO o formato; o agente de variações
            # (variacoes.py, Thompson pelas views) escolhe abre/fecha, mesma foto, uma cena ou sem ele
            variante = variacoes.escolher(conta, log)
            # 29/10 (dona: "seu projeto está enchendo o disco"): com todos os vídeos no MESMO processo ele chegou a
            # 4,9 GB de memória privada parada (modelos/quadros de cada vídeo) e o pagefile do D: foi a 17 GB -> cada
            # vídeo num processo filho, que devolve tudo ao terminar
            import subprocess
            r = subprocess.run([sys.executable, "-u", "-m", "produto.diario", "--um", conta,
                                *(["--variante", variante] if variante else [])], cwd=str(BIN),
                               stdout=sys.stdout, stderr=subprocess.STDOUT,  # sem isto o filho escrevia no console
                               creationflags=0x08000000)                     # invisível e o log ficava vazio
            if r.returncode:
                log(f"{conta}: ERRO (vídeo saiu com código {r.returncode})")
            _marcar_trava()
    finally:
        TRAVA.unlink(missing_ok=True)


if __name__ == "__main__":
    if sys.stdout:  # pythonw (tarefa agendada) não tem stdout
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
