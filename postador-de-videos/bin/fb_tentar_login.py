"""Tenta logar no Facebook com e-mail + senha. Se der código, lê no Gmail. Se der captcha/humano, alarme.
    python fb_tentar_login.py <email> <senha>"""
import ctypes, re, sys, time
from pathlib import Path

sys.path.insert(0, r"D:\logins-google"); sys.path.insert(0, r"D:\hipercool-materiais\comum\fish_audio")
import fish_audio
from playwright.sync_api import sync_playwright

LOG = Path(__file__).resolve().parent.parent / "logs"
if sys.stdout:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
email, senha = sys.argv[1], sys.argv[2]
tag = email.split("@")[0]
HUMANO = re.compile(r"captcha|não sou um robô|I'm not a robot|documento|selfie|confirme que é você|confirm it|"
                    r"suspens|disabled|desativad|checkpoint(?!.*code)", re.I)


def alarme(msg):
    print(f"!!! {msg}", flush=True)
    for _ in range(3):
        for f in (880, 1175, 1568):
            ctypes.windll.kernel32.Beep(f, 350)
        time.sleep(0.6)
    try:
        sys.path.insert(0, r"D:\video-fila"); import avisos
        avisos.enviar(f"Facebook {tag}: {msg} — janela aberta no PC1", "facebook_login", importante=True)
    except Exception:
        pass


def janela_na_frente(porta):
    import subprocess
    ps = (f"$p = Get-CimInstance Win32_Process -Filter \"name='chrome.exe'\" | ? {{ $_.CommandLine -match "
          f"'remote-debugging-port={porta}' -and $_.CommandLine -notmatch '--type=' }} | Select -First 1; "
          "Add-Type 'using System;using System.Runtime.InteropServices;public class W{[DllImport(\"user32.dll\")]public static "
          "extern bool MoveWindow(IntPtr h,int x,int y,int w,int t,bool r);[DllImport(\"user32.dll\")]public static extern bool "
          "SetForegroundWindow(IntPtr h);[DllImport(\"user32.dll\")]public static extern bool ShowWindow(IntPtr h,int c);}'; "
          "$h=(Get-Process -Id $p.ProcessId).MainWindowHandle; [W]::ShowWindow($h,9); [W]::MoveWindow($h,60,30,1300,950,$true); "
          "[W]::SetForegroundWindow($h)")
    subprocess.run(["powershell", "-NoProfile", "-Command", ps], capture_output=True)


def codigo_gmail(ctx):
    g = ctx.new_page()
    try:
        g.goto("https://mail.google.com/mail/u/0/#search/facebook+c%C3%B3digo", wait_until="commit", timeout=120000)
        time.sleep(15)
        t = " ".join(g.inner_text("body").split())
        m = re.search(r"(\d{5,8}) é seu código|Seu código[^0-9]{0,30}?(\d{5,8})", t)
        return (m.group(1) or m.group(2)) if m else None
    finally:
        g.close()


cofre, n = fish_audio.checar_conta(email)
px = fish_audio._subir_ponte(n)
porta, proc = cofre.abrir(email, extra=(f"--proxy-server=127.0.0.1:{px}",))
fechar = True
print(f"== {email} pela saída rnprmtfo-{n} (porta {porta})", flush=True)
try:
    with sync_playwright() as p:
        ctx = p.chromium.connect_over_cdp(f"http://127.0.0.1:{porta}").contexts[0]
        pg = ctx.new_page(); pg.set_viewport_size({"width": 1280, "height": 900})
        pg.goto("https://www.facebook.com/", wait_until="domcontentloaded", timeout=120000)
        time.sleep(8)
        corpo = " ".join(pg.inner_text("body").split())
        ck = {c["name"]: c["value"] for c in ctx.cookies("https://www.facebook.com")}
        if "c_user" in ck and "/login" not in pg.url:
            nome = re.search(r'"NAME":"([^"]+)"', pg.content())
            print(f"JÁ LOGADO como {nome.group(1) if nome else '?'}", flush=True)
            pg.screenshot(path=str(LOG / f"fb_login_{tag}_logado.png"))
            raise SystemExit
        # preenche e-mail e senha
        em_campo = pg.locator("input[name=email]").first
        em_campo.fill(email); time.sleep(0.5)
        pw_campo = pg.locator("input[name=pass]").first
        pw_campo.fill(senha); time.sleep(0.5)
        pg.get_by_role("button", name=re.compile("Entrar|Log [Ii]n|Iniciar")).first.click()
        time.sleep(15)
        pg.screenshot(path=str(LOG / f"fb_login_{tag}_1_depois_senha.png"))
        corpo = " ".join(pg.inner_text("body").split())
        u = pg.url
        print("depois da senha:", u[:80], "|", corpo[:300], flush=True)
        # senha errada?
        if "login" in u and re.search(r"incorreta|incorreto|wrong|inválid|invalid|não corresponde", corpo, re.I):
            print("SENHA ERRADA", flush=True); raise SystemExit
        # já logou direto?
        ck = {c["name"]: c["value"] for c in ctx.cookies("https://www.facebook.com")}
        if "c_user" in ck and "/login" not in pg.url and "/checkpoint" not in pg.url:
            nome = re.search(r'"NAME":"([^"]+)"', pg.content())
            print(f"LOGADO como {nome.group(1) if nome else '?'}", flush=True)
            pg.screenshot(path=str(LOG / f"fb_login_{tag}_logado.png"))
            raise SystemExit
        # humano?
        if HUMANO.search(corpo):
            janela_na_frente(porta); alarme(f"verificação humana: {corpo[:200]}")
            fechar = False; raise SystemExit
        # código?
        if re.search(r"insira o código|digite o código|enter.*code|código de|approvals_code", corpo, re.I) \
                or pg.locator("input[name=approvals_code], input[name=code]").count():
            print("pediu código — lendo no Gmail...", flush=True)
            cod = codigo_gmail(ctx)
            print("código:", cod, flush=True)
            if cod:
                campo = pg.locator("input[name=approvals_code], input[name=code], input[type=text], input[type=number]").first
                campo.fill(cod); time.sleep(1)
                b = pg.get_by_role("button", name=re.compile("Continuar|Enviar|Confirmar|Continue|Submit", re.I)).first
                (b.click() if b.count() else pg.keyboard.press("Enter"))
                time.sleep(12)
                pg.screenshot(path=str(LOG / f"fb_login_{tag}_2_codigo.png"))
                corpo = " ".join(pg.inner_text("body").split())
                ck2 = {c["name"]: c["value"] for c in ctx.cookies("https://www.facebook.com")}
                if "c_user" in ck2:
                    nome = re.search(r'"NAME":"([^"]+)"', pg.content())
                    print(f"LOGADO como {nome.group(1) if nome else '?'}", flush=True)
                else:
                    print("código digitado, mas ainda não logou:", corpo[:300], flush=True)
                    janela_na_frente(porta); alarme(f"digitei o código {cod} mas o Facebook não logou — veja na tela")
                    fechar = False
            else:
                janela_na_frente(porta); alarme("pediu código mas não achei no Gmail — veja na tela e toque no 'Enviar código' se houver")
                fechar = False
        else:
            # estado desconhecido
            janela_na_frente(porta); alarme(f"tela desconhecida: {corpo[:200]}")
            fechar = False
        pg.screenshot(path=str(LOG / f"fb_login_{tag}_fim.png"))
except SystemExit:
    pass
finally:
    if fechar:
        cofre.fechar(proc, nome=tag)
    else:
        print(f"janela do Chrome aberta na tela (porta {porta}) — feche quando terminar", flush=True)
