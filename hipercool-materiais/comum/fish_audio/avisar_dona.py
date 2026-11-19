"""avisar_dona.py — janela do Chrome SEMPRE NO TOPO + apito sonoro quando a dona precisa agir (login/captcha do Fish).

Mesma receita que já funcionou no criador de contas (captcha_lab): maximiza a janela do processo `pid`, põe
HWND_TOPMOST e dá foco; apito = WAV tocado pela saída de áudio normal (winsound.Beep não sai nas caixas da dona).
Dona 17/11: apitar UMA vez por captcha, não a cada vez. Dona 19/11 (Fish): "tela visível acima de todas na hora
do chat e com aviso sonoro". Autossuficiente de propósito (não importa nada pesado), para rodar no python da produção.
"""
import math
import struct
import threading
import time
import wave
from pathlib import Path

AQUI = Path(__file__).resolve().parent
WAV = AQUI / "alarme_login.wav"


def _garantir_wav():
    if WAV.exists():
        return
    taxa = 22050
    with wave.open(str(WAV), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(taxa)
        quadros = bytearray()
        for i in range(int(taxa * 1.3)):
            f = 2400 if (i // int(taxa * 0.33)) % 2 == 0 else 1500  # agudo/grave alternando
            v = 1 if math.sin(2 * math.pi * f * i / taxa) >= 0 else -1  # onda quadrada = som mais forte
            quadros += struct.pack("<h", int(v * 30000))
        w.writeframes(bytes(quadros))


def apito(segundos=4):
    """Toca o alarme em segundo plano (não trava o chamador)."""
    try:
        _garantir_wav()
    except Exception:  # noqa: BLE001
        return

    def _tocar():
        try:
            import winsound
            fim = time.time() + segundos
            while time.time() < fim:
                winsound.PlaySound(str(WAV), winsound.SND_FILENAME)
        except Exception:  # noqa: BLE001
            pass
    threading.Thread(target=_tocar, daemon=True).start()


def na_frente(pid):
    """Maximiza, põe SEMPRE NO TOPO (HWND_TOPMOST) e dá foco às janelas visíveis do processo `pid`. Devolve
    quantas janelas arrumou. Só Windows; qualquer falha é engolida (é conveniência, não requisito)."""
    if not pid:
        return 0
    try:
        import ctypes
        from ctypes import wintypes
        u = ctypes.windll.user32
        achadas = []

        @ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
        def _cb(h, _l):
            p = wintypes.DWORD()
            u.GetWindowThreadProcessId(h, ctypes.byref(p))
            if p.value == pid and u.IsWindowVisible(h) and u.GetWindowTextLengthW(h) > 0:
                r = wintypes.RECT()
                u.GetWindowRect(h, ctypes.byref(r))
                if (r.right - r.left) > 500 and (r.bottom - r.top) > 400 and u.GetParent(h) == 0:
                    achadas.append(h)
            return True

        u.EnumWindows(_cb, 0)
        for h in achadas:
            # SetForegroundWindow sozinho falha quando este processo não tem o foco (medido 19/11: janela ficou
            # atrás). Minimizar e restaurar destrava o foreground; aí maximiza, põe no topo um instante e solta.
            u.ShowWindow(h, 6)   # SW_MINIMIZE
            time.sleep(0.12)
            u.ShowWindow(h, 3)   # SW_MAXIMIZE
            u.SetWindowPos(h, -1, 0, 0, 0, 0, 0x0001 | 0x0002)  # HWND_TOPMOST
            u.keybd_event(0x12, 0, 0, 0)  # Alt: o Windows só deixa SetForegroundWindow depois de uma tecla
            u.keybd_event(0x12, 0, 2, 0)
            try:
                u.BringWindowToTop(h)
            except Exception:  # noqa: BLE001
                pass
            u.SetForegroundWindow(h)
            u.SetWindowPos(h, -2, 0, 0, 0, 0, 0x0001 | 0x0002)  # HWND_NOTOPMOST (fica clicável normal, mas na frente)
        return len(achadas)
    except Exception:  # noqa: BLE001
        return 0


def em_foco(pid):
    """True se a janela em primeiro plano pertence a este pid (a dona já está nela — não re-forçar)."""
    if not pid:
        return False
    try:
        import ctypes
        from ctypes import wintypes
        u = ctypes.windll.user32
        h = u.GetForegroundWindow()
        p = wintypes.DWORD()
        u.GetWindowThreadProcessId(h, ctypes.byref(p))
        return p.value == pid
    except Exception:  # noqa: BLE001
        return False


def chamar(pid, apitar=True):
    """Traz a janela à frente e (opcional) apita uma vez. Use `apitar=False` nos lembretes (não repetir o som)."""
    n = na_frente(pid)
    if apitar:
        apito()
    return n


if __name__ == "__main__":
    import sys
    chamar(int(sys.argv[1]) if len(sys.argv) > 1 else 0)
    time.sleep(5)
