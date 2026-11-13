"""print_perfis_chrome.py — abre perfis do Chrome NORMAL (disco C) numa página e tira print SÓ da janela nova, mesmo
atrás de outras (PrintWindow) — a dona usa o PC enquanto roda (23/10). Fecha a janela depois do print (WM_CLOSE).

    python print_perfis_chrome.py <url> "Profile 39=daniel" "Profile 53=travelbds25" ...
Prints em yt_prints\\pc1_<nome>.png.
"""
import ctypes
import os
import subprocess
import sys
import time
from ctypes import wintypes

from PIL import Image

u, g = ctypes.windll.user32, ctypes.windll.gdi32
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
# onde salvar (desktop: PRINT_SAIDA=C:\postador-worker\yt_prints, PRINT_PREFIXO=desk_)
SAIDA = os.environ.get("PRINT_SAIDA", r"D:\logins-google\yt_prints")
PREFIXO = os.environ.get("PRINT_PREFIXO", "pc1_")


def janelas_chrome():
    out = set()

    @ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    def cb(h, _):
        c = ctypes.create_unicode_buffer(64)
        u.GetClassNameW(h, c, 64)
        if c.value == "Chrome_WidgetWin_1" and u.IsWindowVisible(h) and u.GetWindowTextLengthW(h) > 0:
            out.add(h)
        return True
    u.EnumWindows(cb, 0)
    return out


def print_janela(h, caminho):
    r = wintypes.RECT()
    u.GetWindowRect(h, ctypes.byref(r))
    w, a = r.right - r.left, r.bottom - r.top
    hdc = u.GetWindowDC(h)
    mem = g.CreateCompatibleDC(hdc)
    bmp = g.CreateCompatibleBitmap(hdc, w, a)
    g.SelectObject(mem, bmp)
    u.PrintWindow(h, mem, 2)  # PW_RENDERFULLCONTENT
    cab = (ctypes.c_byte * 40)()
    ctypes.memmove(cab, (ctypes.c_uint32 * 10)(40, w, (-a) & 0xFFFFFFFF, 0x200001, 0, 0, 0, 0, 0, 0), 40)
    buf = (ctypes.c_byte * (w * a * 4))()
    g.GetDIBits(mem, bmp, 0, a, buf, cab, 0)
    Image.frombuffer("RGBA", (w, a), bytes(buf), "raw", "BGRA", 0, 1).convert("RGB").save(caminho)
    g.DeleteObject(bmp)
    g.DeleteDC(mem)
    u.ReleaseDC(h, hdc)


def main(url, pares):
    os.makedirs(SAIDA, exist_ok=True)
    for par in pares:
        perfil, nome = par.split("=", 1)
        antes = janelas_chrome()
        subprocess.Popen([CHROME, f"--profile-directory={perfil}", "--new-window", "--window-size=1400,900", url])
        nova = None
        for _ in range(40):
            time.sleep(0.5)
            novas = janelas_chrome() - antes
            if novas:
                nova = novas.pop()
                break
        if not nova:
            print(nome, "janela não apareceu", flush=True)
            continue
        time.sleep(14)
        # o Chrome não desenha a página com a janela atrás de outras: traz pra frente uns segundos
        u.ShowWindow(nova, 9)
        u.SetForegroundWindow(nova)
        time.sleep(5)
        # o PrintWindow não pega o conteúdo do Chrome (sai em branco): print da área da janela, com ela na frente
        from PIL import ImageGrab
        r = wintypes.RECT()
        u.GetWindowRect(nova, ctypes.byref(r))
        ImageGrab.grab(bbox=(r.left, r.top, r.right, r.bottom)).save(os.path.join(SAIDA, f"{PREFIXO}{nome}.png"))
        u.PostMessageW(nova, 0x0010, 0, 0)  # WM_CLOSE: a dona pediu pra não deixar aberta
        print(nome, "print ok", flush=True)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2:])
