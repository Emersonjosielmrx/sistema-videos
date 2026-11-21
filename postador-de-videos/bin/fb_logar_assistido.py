"""Login assistido no Facebook de uma conta do cofre (dona 20/11/2026: "se precisar de confirmação humana na hora,
como captcha, só abrir na tela que eu faço e soar um alarme sonoro pra eu ir").

Abre o Chrome da conta pela SAÍDA FIXA dela (cofre fish_proxy -> ponte rnprmtfo-N; recusa Kaggle), vai ao Facebook e:
  - já logado (cookie c_user)               -> diz quem é e para (nada a fazer);
  - tela de código (e-mail)                 -> lê o código MAIS NOVO no Gmail da própria conta e digita;
  - formulário de login (sem senha)         -> põe o e-mail e pede "entrar com código" se o Facebook oferecer;
  - captcha / documento / algo humano       -> janela NA TELA + alarme sonoro + Telegram, e espera a dona (até 15 min).
Nunca pede código novo em sequência (cada pedido invalida o anterior). Prints em logs/fb_login_<conta>_*.png.

    python fb_logar_assistido.py <email> [--so-ver]
"""
import ctypes, re, subprocess, sys, time
from pathlib import Path

sys.path.insert(0, r"D:\logins-google"); sys.path.insert(0, r"D:\hipercool-materiais\comum\fish_audio")
import fish_audio
from playwright.sync_api import sync_playwright

LOG = Path(__file__).resolve().parent.parent / "logs"
if sys.stdout:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
email = sys.argv[1]
SO_VER = "--so-ver" in sys.argv
tag = email.split("@")[0]
HUMANO = re.compile(r"captcha|não sou um robô|nao sou um robo|I'm not a robot|documento de identidade|"
                    r"envie uma foto|selfie|vídeo selfie|confirme que é você|confirm it's you|"
                    r"conta (foi )?suspensa|account (has been )?(suspended|disabled)|desativad", re.I)


def alarme(titulo, msg):
    """Janela na frente + bipes + Telegram."""
    print(f"!!! PRECISA DA DONA: {msg}", flush=True)
    try:
        sys.path.insert(0, r"D:\video-fila")
        import avisos
        avisos.enviar(f"Facebook {titulo}: {msg} — a janela está aberta na tela do PC1", "facebook_login", importante=True)
    except Exception:
        pass
    for _ in range(3):
        for f in (880, 1175, 1568):
            ctypes.windll.kernel32.Beep(f, 350)
        time.sleep(0.6)


def janela_na_frente(porta):
    ps = (f"$p = Get-CimInstance Win32_Process -Filter \"name='chrome.exe'\" | ? {{ $_.CommandLine -match "
          f"'remote-debugging-port={porta}' -and $_.CommandLine -notmatch '--type=' }} | Select -First 1; "
          "Add-Type 'using System;using System.Runtime.InteropServices;public class W{[DllImport(\"user32.dll\")]public static "
          "extern bool MoveWindow(IntPtr h,int x,int y,int w,int t,bool r);[DllImport(\"user32.dll\")]public static extern bool "
          "SetForegroundWindow(IntPtr h);[DllImport(\"user32.dll\")]public static extern bool ShowWindow(IntPtr h,int c);}'; "
          "$h=(Get-Process -Id $p.ProcessId).MainWindowHandle; [W]::ShowWindow($h,9); [W]::MoveWindow($h,60,30,1300,950,$true); "
          "[W]::SetForegroundWindow($h)")
    subprocess.run(["powershell", "-NoProfile", "-Command", ps], capture_output=True)


def codigo_mais_novo(ctx, depois_de=None):
    """Lê o código do Facebook mais recente no Gmail da conta (mesmo Chrome, outra aba). (codigo, hora) ou (None, None)."""
    g = ctx.new_page()
    try:
        g.goto("https://mail.google.com/mail/u/0/#search/facebook+c%C3%B3digo", wait_until="commit", timeout=120000)
        time.sleep(15)
        t = " ".join(g.inner_text("body").split())
        m = re.search(r"(\d{5,8}) é seu código[^0-9]{0,200}?(\d{1,2}:\d{2}(?:\s?[AP]M)?)|"
                      r"Seu código do Facebook é (\d{5,8})[^0-9]{0,200}?(\d{1,2}:\d{2}(?:\s?[AP]M)?)", t)
        if not m:
            return None, None
        cod = m.group(1) or m.group(3)
        hora = m.group(2) or m.group(4)
        return cod, hora
    finally:
        g.close()


def estado(pg, ctx):
    ck = {c["name"]: c["value"] for c in ctx.cookies("https://www.facebook.com")}
    corpo = " ".join(pg.inner_text("body").split())
    u = pg.url
    if HUMANO.search(corpo) or "/checkpoint/" in u and "code" not in corpo.casefold():
        return "humano", corpo
    if pg.locator("input[name=approvals_code], input[autocomplete=one-time-code], input[name=code], input[id*=code]").count() \
            or re.search(r"insira o código|digite o código|enter (the )?code|código de (segurança|confirmação)", corpo, re.I):
        return "codigo", corpo
    if "c_user" in ck and "/login" not in u and "/checkpoint" not in u:
        return "logado", corpo
    if pg.locator("input[name=email]").count():
        return "login", corpo
    return "outro", corpo


cofre, n = fish_audio.checar_conta(email)
px = fish_audio._subir_ponte(n)
porta, proc = cofre.abrir(email, extra=(f"--proxy-server=127.0.0.1:{px}",))
print(f"== {email} pela saída rnprmtfo-{n} (porta {porta})", flush=True)
fechar_no_fim = True
try:
    with sync_playwright() as p:
        ctx = p.chromium.connect_over_cdp(f"http://127.0.0.1:{porta}").contexts[0]
        pg = ctx.new_page(); pg.set_viewport_size({"width": 1280, "height": 900})
        pg.goto("https://www.facebook.com/", wait_until="domcontentloaded", timeout=120000)
        time.sleep(8)
        st, corpo = estado(pg, ctx)
        pg.screenshot(path=str(LOG / f"fb_login_{tag}_0.png"))
        print("estado:", st, "|", corpo[:300], flush=True)
        if SO_VER:
            raise SystemExit
        for passo in range(6):
            if st == "logado":
                nome = re.search(r'"NAME":"([^"]+)"', pg.content())
                print("LOGADO como", nome.group(1) if nome else "?", flush=True)
                break
            if st == "humano":
                janela_na_frente(porta)
                alarme(tag, "o Facebook pediu verificação humana (captcha/documento/confirmação)")
                fechar_no_fim = False  # a dona vai mexer: não fecha
                for _ in range(90):  # espera a dona até 15 min
                    time.sleep(10)
                    st, corpo = estado(pg, ctx)
                    if st != "humano":
                        break
                else:
                    print("a dona não resolveu em 15 min — deixo a janela aberta", flush=True)
                    break
                continue
            if st == "codigo":
                cod, hora = codigo_mais_novo(ctx)
                print("código mais novo no Gmail:", cod, hora, flush=True)
                campo = pg.locator("input[name=approvals_code], input[autocomplete=one-time-code], input[name=code], "
                                   "input[id*=code], input[type=text], input[type=number]").first
                if not cod or not campo.count():
                    janela_na_frente(porta)
                    alarme(tag, f"tela de código sem código legível no Gmail ({cod}) — digite o que chegou")
                    fechar_no_fim = False
                    break
                campo.fill(cod); time.sleep(1)
                b = pg.get_by_role("button", name=re.compile("Continuar|Enviar|Confirmar|Continue|Submit", re.I)).first
                (b.click() if b.count() else pg.keyboard.press("Enter"))
                time.sleep(12)
                pg.screenshot(path=str(LOG / f"fb_login_{tag}_{passo + 1}_codigo.png"))
                st, corpo = estado(pg, ctx)
                if st == "codigo":  # código recusado (venceu): não pede outro sozinho — chama a dona
                    janela_na_frente(porta)
                    alarme(tag, "o Facebook recusou o código (vencido?) — peça um novo na tela e me avise")
                    fechar_no_fim = False
                    break
                continue
            if st == "login":
                pg.fill("input[name=email]", email); time.sleep(1)
                janela_na_frente(porta)
                alarme(tag, "tela de login: e-mail preenchido; escolha 'entrar com código'/'esqueci a senha' na tela")
                fechar_no_fim = False
                for _ in range(90):
                    time.sleep(10)
                    st, corpo = estado(pg, ctx)
                    if st in ("codigo", "logado", "humano"):
                        break
                continue
            # outro
            janela_na_frente(porta)
            alarme(tag, f"tela desconhecida ({pg.url[:60]}) — veja na tela")
            fechar_no_fim = False
            break
        pg.screenshot(path=str(LOG / f"fb_login_{tag}_fim.png"))
        print("estado final:", st, flush=True)
except SystemExit:
    pass
finally:
    if fechar_no_fim:
        cofre.fechar(proc, nome=tag)
