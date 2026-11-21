"""Abre o Chrome do cofre da conta com o FACEBOOK saindo pela casa e o resto (Google/Gmail) pela saída fixa dela
(Webshare rnprmtfo-N), para a dona logar À MÃO (sem digitação por programa). Dona 20/11 16:30: "então abre nesse IP de
casa" — os IPs Webshare são de datacenter e o Facebook prende conta antiga num captcha em loop.
PAC: domínios do Facebook = DIRECT (casa); o resto = PROXY da ponte da conta. Acompanha a tela e toca alarme quando
pedir algo; avisa quando logar. NÃO fecha o Chrome (a dona está usando).
    python fb_abrir_casa.py <email>"""
import base64, ctypes, re, subprocess, sys, time
from pathlib import Path

sys.path.insert(0, r"D:\logins-google"); sys.path.insert(0, r"D:\hipercool-materiais\comum\fish_audio")
import fish_audio
from playwright.sync_api import sync_playwright

LOG = Path(__file__).resolve().parent.parent / "logs"
if sys.stdout:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
email = sys.argv[1]
tag = email.split("@")[0]
cofre, n = fish_audio.checar_conta(email)  # recusa Kaggle
px = fish_audio._subir_ponte(n)
pac = ("function FindProxyForURL(url, host) {"
       " if (dnsDomainIs(host, 'facebook.com') || dnsDomainIs(host, 'facebook.net') || dnsDomainIs(host, 'fbcdn.net')"
       " || dnsDomainIs(host, 'fbsbx.com') || dnsDomainIs(host, 'messenger.com')) return 'DIRECT';"
       f" return 'PROXY 127.0.0.1:{px}'; }}")
pac_url = "data:application/x-ns-proxy-autoconfig;base64," + base64.b64encode(pac.encode()).decode()
porta, proc = cofre.abrir(email, extra=(f"--proxy-pac-url={pac_url}", "--force-webrtc-ip-handling-policy=disable_non_proxied_udp"))
if proc is None:
    raise SystemExit(f"{email}: o Chrome dessa conta já estava aberto por outro programa — feche e rode de novo")


def bip():
    for f in (880, 1175, 1568):
        ctypes.windll.kernel32.Beep(f, 300)


def na_frente():
    ps = (f"$p = Get-CimInstance Win32_Process -Filter \"name='chrome.exe'\" | ? {{ $_.CommandLine -match "
          f"'remote-debugging-port={porta}' -and $_.CommandLine -notmatch '--type=' }} | Select -First 1; "
          "Add-Type 'using System;using System.Runtime.InteropServices;public class W{[DllImport(\"user32.dll\")]public static "
          "extern bool MoveWindow(IntPtr h,int x,int y,int w,int t,bool r);[DllImport(\"user32.dll\")]public static extern bool "
          "SetForegroundWindow(IntPtr h);[DllImport(\"user32.dll\")]public static extern bool ShowWindow(IntPtr h,int c);}'; "
          "$h=(Get-Process -Id $p.ProcessId).MainWindowHandle; [W]::ShowWindow($h,9); [W]::MoveWindow($h,60,30,1300,950,$true); "
          "[W]::SetForegroundWindow($h)")
    subprocess.run(["powershell", "-NoProfile", "-Command", ps], capture_output=True)


with sync_playwright() as p:
    ctx = p.chromium.connect_over_cdp(f"http://127.0.0.1:{porta}").contexts[0]
    # confere o caminho: o resto sai pela Webshare da conta (o Facebook vai DIRECT pelo PAC)
    t = ctx.new_page()
    try:
        t.goto("http://ip-api.com/json/?fields=query,isp", timeout=60000)
        print(f"Google/resto sai por: {t.inner_text('body')[:120]} (esperado rnprmtfo-{n})", flush=True)
    except Exception as e:
        print("não conferi o IP do resto:", str(e)[:100], flush=True)
    t.close()
    pg = ctx.new_page()
    pg.goto("https://www.facebook.com/", wait_until="domcontentloaded", timeout=120000)
    time.sleep(3)
    na_frente(); bip()
    print(f"JANELA NA TELA (porta {porta}): Facebook pela CASA — logue à mão", flush=True)
    ultimo, i = None, 0
    while i < 360:  # acompanha até 30 min
        i += 1
        time.sleep(5)
        try:
            ck = {c["name"]: c["value"] for c in ctx.cookies("https://www.facebook.com")}
            corpo = " ".join(pg.inner_text("body").split())[:200]
        except Exception:
            break
        st = "LOGADO" if "c_user" in ck and "/login" not in pg.url and "checkpoint" not in pg.url \
            and "two_step" not in pg.url else pg.url.split("?")[0][-50:]
        if st != ultimo:
            print(f"{time.strftime('%H:%M:%S')} {st} | {corpo[:150]}", flush=True)
            pg.screenshot(path=str(LOG / f"fb_casa_{tag}_{i:03d}.png"))
            ultimo = st
            if st != "LOGADO" and i > 2:
                bip()
        if st == "LOGADO":
            nome = re.search(r'"NAME":"([^"]+)"', pg.content())
            print(f"LOGADO como {nome.group(1) if nome else '?'} (c_user {ck.get('c_user')})", flush=True)
            break
print("acompanhamento terminou — o Chrome fica aberto", flush=True)
