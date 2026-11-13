#!/usr/bin/env python3
"""teclado.py — roda NO notebook: digita um texto na janela em foco, como se fosse o teclado (XTEST do X11, sem
instalar nada e sem sudo). Usado SÓ pra pôr o E-MAIL na janela de login a pedido da dona (23/10/2026: "digite pelo
menos o e-mail"). Senha NUNCA passa por aqui.

    python3 teclado.py "conta@gmail.com" [--enter]
"""
import ctypes
import os
import subprocess
import sys
import time

NOMES = {"@": "at", ".": "period", "_": "underscore", "-": "minus", "+": "plus"}


def _ambiente():
    try:
        r = subprocess.run(["systemctl", "--user", "show-environment"], capture_output=True, text=True, timeout=10)
        for linha in r.stdout.splitlines():
            k, _, v = linha.partition("=")
            if k in ("DISPLAY", "XAUTHORITY"):
                os.environ[k] = v
    except (OSError, subprocess.TimeoutExpired):
        pass
    os.environ.setdefault("DISPLAY", ":0")


def main(texto, enter):
    if "senha" in texto.lower() or len(texto) > 120:
        sys.exit("só e-mail")
    _ambiente()
    x = ctypes.cdll.LoadLibrary("libX11.so.6")
    t = ctypes.cdll.LoadLibrary("libXtst.so.6")
    x.XOpenDisplay.restype = ctypes.c_void_p
    x.XOpenDisplay.argtypes = [ctypes.c_char_p]
    x.XStringToKeysym.restype = ctypes.c_ulong
    x.XStringToKeysym.argtypes = [ctypes.c_char_p]
    x.XKeysymToKeycode.restype = ctypes.c_ubyte
    x.XKeysymToKeycode.argtypes = [ctypes.c_void_p, ctypes.c_ulong]
    x.XKeycodeToKeysym.restype = ctypes.c_ulong
    x.XKeycodeToKeysym.argtypes = [ctypes.c_void_p, ctypes.c_ubyte, ctypes.c_int]
    t.XTestFakeKeyEvent.argtypes = [ctypes.c_void_p, ctypes.c_uint, ctypes.c_int, ctypes.c_ulong]
    x.XFlush.argtypes = [ctypes.c_void_p]
    d = x.XOpenDisplay(os.environ["DISPLAY"].encode())
    if not d:
        sys.exit("sem acesso à tela")
    shift = x.XKeysymToKeycode(d, x.XStringToKeysym(b"Shift_L"))

    def tecla(kc, com_shift):
        if com_shift:
            t.XTestFakeKeyEvent(d, shift, 1, 0)
        t.XTestFakeKeyEvent(d, kc, 1, 0)
        t.XTestFakeKeyEvent(d, kc, 0, 0)
        if com_shift:
            t.XTestFakeKeyEvent(d, shift, 0, 0)
        x.XFlush(d)
        time.sleep(0.06)

    for c in texto:
        nome = NOMES.get(c, c)
        sym = x.XStringToKeysym(nome.encode())
        kc = x.XKeysymToKeycode(d, sym)
        if not kc:
            sys.exit(f"tecla '{c}' não existe neste teclado")
        tecla(kc, x.XKeycodeToKeysym(d, kc, 0) != sym or c.isupper())
    if enter:
        tecla(x.XKeysymToKeycode(d, x.XStringToKeysym(b"Return")), False)
    print("DIGITADO")


if __name__ == "__main__":
    main(sys.argv[1], "--enter" in sys.argv)
