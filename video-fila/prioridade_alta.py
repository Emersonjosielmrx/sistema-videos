r"""prioridade_alta.py — os despachos (alimentar PC2/PC3, disparar STI, encher a pilha, controlador) rodam com prioridade
ACIMA DO NORMAL de CPU (15/11/2026).

Por quê: com o PC1 a 100% (renders, mascote, reels, abastecedores, Chrome), o ssh/scp/taskkill dos despachos ficava
lento a ponto de estourar prazos — em 15/11 o alimentador do PC2 ficou 7 min só esperando um taskkill, e PC2 e desktop
passaram 1,5 h sem Short. Os despachos são leves (99% do tempo esperando rede) e todas as outras máquinas dependem
deles: subir a prioridade deles quase não tira CPU de ninguém e evita que a frota pare por causa da fila de CPU do PC1.
Os filhos (ssh, scp, yt-dlp, rclone) herdam a classe no Windows.

Uso: `import prioridade_alta` no topo do script (ativa sozinho). PRIORIDADE_ALTA=0 desliga.
"""
import os
import sys

ABOVE_NORMAL = 0x00008000


def ativar():
    if os.environ.get("PRIORIDADE_ALTA") == "0" or sys.platform != "win32":
        return False
    try:
        import ctypes
        from ctypes import wintypes
        k = ctypes.windll.kernel32
        # 15/11: sem restype o pseudo-handle (-1) era truncado e a chamada falhava calada (erro 6, handle inválido)
        k.GetCurrentProcess.restype = wintypes.HANDLE
        k.SetPriorityClass.argtypes = (wintypes.HANDLE, wintypes.DWORD)
        k.SetPriorityClass.restype = wintypes.BOOL
        return bool(k.SetPriorityClass(k.GetCurrentProcess(), ABOVE_NORMAL))
    except Exception:  # noqa: BLE001
        return False


ativar()
