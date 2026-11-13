# -*- coding: utf-8 -*-
# COMUM — fonte única: D:\hipercool-materiais\comum\sem_janela.py. Mudou esta cópia? python D:\hipercool-materiais\bin\recursos.py subir sem_janela.py --de <projeto>
"""sem_janela.py — processos filhos SEM janela na tela (pedido do dono, 15/10: "as janelas de cmd e python enchem
a tela, atrapalha digitar").

As tarefas agendadas rodam escondidas (pythonw / rodar_oculto.vbs), mas um processo SEM console (pythonw) que abre
um programa de console (python.exe do render, powershell, tasklist, ssh, rclone, ffmpeg) faz o Windows criar uma
janela NOVA pra cada um. Importar este módulo no começo do ponto de entrada põe CREATE_NO_WINDOW em todo
subprocess que não escolheu flags: o filho ganha um console invisível e os netos herdam esse console (sem janela).
Programas gráficos (Chrome do postador) não são afetados.
"""
import subprocess
import sys

CREATE_NO_WINDOW = 0x08000000

if sys.platform == "win32" and not getattr(subprocess.Popen, "_sem_janela", False):
    _init_original = subprocess.Popen.__init__

    def _init(self, *args, **kwargs):
        if not kwargs.get("creationflags"):
            kwargs["creationflags"] = CREATE_NO_WINDOW
        _init_original(self, *args, **kwargs)

    subprocess.Popen.__init__ = _init
    subprocess.Popen._sem_janela = True
