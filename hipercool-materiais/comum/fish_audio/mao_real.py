r"""mao_real.py — mouse e teclado REAIS do Windows (SendInput), para sites cujo reCAPTCHA invisível recusa clique e
digitação feitos por script DENTRO do Chrome (Fish Audio cadastro, 19/11). Para o Chrome é igual a uma pessoa usando.
Também: trazer janela à frente, posicionar lado a lado e tirar print da tela (para eu ver onde clicar).

Usa a tela física: enquanto roda, a dona NÃO pode mexer no mouse/teclado.
"""
import ctypes
import random
import time
from ctypes import wintypes

u = ctypes.windll.user32
u.SetWindowPos.argtypes = [wintypes.HWND, wintypes.HWND, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int,
                           ctypes.c_uint]

INPUT_MOUSE, INPUT_KEYBOARD = 0, 1
KEYEVENTF_KEYUP, KEYEVENTF_UNICODE = 0x0002, 0x0004
MOUSEEVENTF_LEFTDOWN, MOUSEEVENTF_LEFTUP = 0x0002, 0x0004


class MOUSEINPUT(ctypes.Structure):
    _fields_ = [("dx", wintypes.LONG), ("dy", wintypes.LONG), ("mouseData", wintypes.DWORD),
                ("dwFlags", wintypes.DWORD), ("time", wintypes.DWORD), ("dwExtraInfo", ctypes.c_size_t)]


class KEYBDINPUT(ctypes.Structure):
    _fields_ = [("wVk", wintypes.WORD), ("wScan", wintypes.WORD), ("dwFlags", wintypes.DWORD),
                ("time", wintypes.DWORD), ("dwExtraInfo", ctypes.c_size_t)]


class _U(ctypes.Union):
    _fields_ = [("mi", MOUSEINPUT), ("ki", KEYBDINPUT)]


class INPUT(ctypes.Structure):
    _fields_ = [("type", wintypes.DWORD), ("u", _U)]


def _send(*inps):
    arr = (INPUT * len(inps))(*inps)
    u.SendInput(len(inps), arr, ctypes.sizeof(INPUT))


def mover(x, y, passos=25):
    """Move o mouse até (x,y) em pequenos passos, como gente."""
    pt = wintypes.POINT()
    u.GetCursorPos(ctypes.byref(pt))
    x0, y0 = pt.x, pt.y
    for i in range(1, passos + 1):
        t = i / passos
        u.SetCursorPos(int(x0 + (x - x0) * t + random.randint(-1, 1)), int(y0 + (y - y0) * t + random.randint(-1, 1)))
        time.sleep(random.uniform(0.008, 0.02))
    u.SetCursorPos(int(x), int(y))


def clicar(x, y):
    mover(x, y)
    time.sleep(random.uniform(0.08, 0.2))
    _send(INPUT(INPUT_MOUSE, _U(mi=MOUSEINPUT(0, 0, 0, MOUSEEVENTF_LEFTDOWN, 0, 0))))
    time.sleep(random.uniform(0.05, 0.12))
    _send(INPUT(INPUT_MOUSE, _U(mi=MOUSEINPUT(0, 0, 0, MOUSEEVENTF_LEFTUP, 0, 0))))


def digitar(texto):
    for ch in texto:
        c = ord(ch)
        _send(INPUT(INPUT_KEYBOARD, _U(ki=KEYBDINPUT(0, c, KEYEVENTF_UNICODE, 0, 0))),
              INPUT(INPUT_KEYBOARD, _U(ki=KEYBDINPUT(0, c, KEYEVENTF_UNICODE | KEYEVENTF_KEYUP, 0, 0))))
        time.sleep(random.uniform(0.06, 0.16))


def tecla(vk):
    """Tecla virtual (ex.: 0x0D Enter, 0x09 Tab)."""
    _send(INPUT(INPUT_KEYBOARD, _U(ki=KEYBDINPUT(vk, 0, 0, 0, 0))),
          INPUT(INPUT_KEYBOARD, _U(ki=KEYBDINPUT(vk, 0, KEYEVENTF_KEYUP, 0, 0))))


def ctrl(letra):
    """Ctrl+<letra> (ex.: 'a', 'c', 'v')."""
    vk = ord(letra.upper())
    _send(INPUT(INPUT_KEYBOARD, _U(ki=KEYBDINPUT(0x11, 0, 0, 0, 0))),
          INPUT(INPUT_KEYBOARD, _U(ki=KEYBDINPUT(vk, 0, 0, 0, 0))),
          INPUT(INPUT_KEYBOARD, _U(ki=KEYBDINPUT(vk, 0, KEYEVENTF_KEYUP, 0, 0))),
          INPUT(INPUT_KEYBOARD, _U(ki=KEYBDINPUT(0x11, 0, KEYEVENTF_KEYUP, 0, 0))))


def janelas_do_pid(pid):
    achou = []

    @ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    def cb(h, _l):
        p = wintypes.DWORD()
        u.GetWindowThreadProcessId(h, ctypes.byref(p))
        if p.value == pid and u.IsWindowVisible(h) and u.GetWindowTextLengthW(h) > 0 and u.GetParent(h) == 0:
            r = wintypes.RECT()
            u.GetWindowRect(h, ctypes.byref(r))
            if (r.right - r.left) > 300:
                achou.append(h)
        return True
    u.EnumWindows(cb, 0)
    return achou


def frente(h):
    u.ShowWindow(h, 9)
    u.keybd_event(0x12, 0, 0, 0)
    u.keybd_event(0x12, 0, 2, 0)
    u.BringWindowToTop(h)
    u.SetForegroundWindow(h)


def posicionar(h, x, y, w, alt):
    u.ShowWindow(h, 9)
    u.SetWindowPos(h, wintypes.HWND(-1), x, y, w, alt, 0x0040)   # TOPMOST + mostrar


def soltar_topo(h):
    u.SetWindowPos(h, wintypes.HWND(-2), 0, 0, 0, 0, 0x0001 | 0x0002)


def print_tela(caminho):
    from PIL import ImageGrab
    ImageGrab.grab().save(caminho)
    return caminho
