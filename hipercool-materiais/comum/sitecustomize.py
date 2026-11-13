# -*- coding: utf-8 -*-
"""sitecustomize.py — copiado para o site-packages de cada Python/venv das tarefas (fonte: D:\\hipercool-materiais\\comum).
Regra da dona (15/10 e 29/10): NENHUMA janela de cmd/python/ssh na tela. Um processo SEM console (pythonw das tarefas)
que abre um programa de console faz o Windows criar uma janela nova para cada um. Aqui, só quando o processo atual não
tem console (GetConsoleWindow() == 0), todo subprocess sem creationflags ganha CREATE_NO_WINDOW: o filho recebe um
console invisível e os netos herdam. Terminal interativo (tem console) não é afetado. Instalado por
D:\\hipercool-materiais\\bin\\instalar_sitecustomize.py (29/10, Fable).
"""
try:
    import sys
    if sys.platform == "win32":
        import ctypes
        if ctypes.windll.kernel32.GetConsoleWindow() == 0:
            import subprocess
            if not getattr(subprocess.Popen, "_sem_janela", False):
                _init_original = subprocess.Popen.__init__

                def _init(self, *args, **kwargs):
                    if not kwargs.get("creationflags"):
                        kwargs["creationflags"] = 0x08000000  # CREATE_NO_WINDOW
                    _init_original(self, *args, **kwargs)

                subprocess.Popen.__init__ = _init
                subprocess.Popen._sem_janela = True
except Exception:  # nunca derrubar um Python por causa disto
    pass
