"""trava_render.py - um render pesado do veo por vez (item BX-03 de D:\\veo\\docs\\PLANO_MELHORIAS_VEO.md).

Quem renderiza: pos_producao\\montar_final.montar (worker_noite, blitz_*, driver_noite_novos...) e
D:\\postador-de-videos\\bin\\limpar_veo.py (de hora em hora, antes da rede). Dois ao mesmo tempo disputam CPU num PC
que tambem grava/gera, e um deles estoura o timeout.

Copiada da ideia da Trava de D:\\manhwa-react\\mr\\rede.py, com 2 diferencas: cria o arquivo de forma atomica
(O_EXCL: dois processos nao passam juntos) e e reentrante no mesmo processo (o worker que segura a trava pode chamar
montar() sem travar em si mesmo). Trava com mais de 90 min e de processo morto.

    from trava_render import trava_render, TravaOcupada
    with trava_render("limpar_veo"):             # ocupada -> TravaOcupada na hora
    with trava_render("montar", esperar_s=1800): # espera ate 30 min
"""
import os
import time
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

TRAVA = Path(__file__).resolve().parent / "logs" / "render.lock"
ABANDONADA_S = 90 * 60
_minha = 0  # quantas vezes este processo entrou (reentrante)


class TravaOcupada(RuntimeError):
    pass


def _dono():
    try:
        return TRAVA.read_text(encoding="utf-8", errors="replace").strip()
    except OSError:
        return "?"


@contextmanager
def trava_render(quem, esperar_s=0):
    global _minha
    if _minha:
        _minha += 1
        try:
            yield
        finally:
            _minha -= 1
        return
    TRAVA.parent.mkdir(parents=True, exist_ok=True)
    fim = time.time() + esperar_s
    while True:
        try:
            fd = os.open(str(TRAVA), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.write(fd, f"{quem} pid {os.getpid()} desde {datetime.now():%d/%m %H:%M}".encode("utf-8"))
            os.close(fd)
            break
        except FileExistsError:
            try:
                if time.time() - TRAVA.stat().st_mtime > ABANDONADA_S:
                    TRAVA.unlink(missing_ok=True)  # processo morto: libera e tenta de novo
                    continue
            except OSError:
                continue
            if time.time() >= fim:
                raise TravaOcupada(f"render ocupado ({_dono()})")
            time.sleep(10)
    _minha = 1
    try:
        yield
    finally:
        _minha = 0
        TRAVA.unlink(missing_ok=True)
