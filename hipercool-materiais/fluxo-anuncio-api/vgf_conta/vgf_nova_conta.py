r"""Cria (ou reaproveita) uma conta no Very Good FFmpeg com uma conta Google do cofre, gera a chave da API, guarda a
chave num arquivo SEM mostrar no log, testa a chave e (opcional) cria a credencial no n8n6.

Uso:
  python vgf_nova_conta.py <email_google_do_cofre> [--visivel] [--n8n]
    --visivel  abre o Chrome com janela (só se o login sem janela falhar; avise a dona antes)
    --n8n      cria a credencial "Very Good FFmpeg (Bearer) <email>" no n8n6 e mostra o id

Saída: vgf_chave_<email>.txt nesta pasta (1 chave por linha; a 1ª é a usada) + prints em provas\.
Base: ..\vgf_painel.py (a conta aulacomia@gmail.com, 30/10), que continua intocado."""
import json, re, sys, urllib.request, urllib.error
from pathlib import Path

sys.path.insert(0, r"D:\logins-google")
import cofre  # noqa: E402
from playwright.sync_api import sync_playwright  # noqa: E402

AQUI = Path(__file__).parent
args = [a for a in sys.argv[1:] if not a.startswith("--")]
if not args:
    sys.exit(__doc__)
CONTA = args[0]
VISIVEL = "--visivel" in sys.argv
ARQ = AQUI / f"vgf_chave_{CONTA}.txt"
PROVAS = AQUI / "provas"
PROVAS.mkdir(exist_ok=True)
SITE = "https://verygoodffmpeg.com"


def mostra(pg, rotulo):
    t = re.sub(r"\s+", " ", pg.inner_text("body", timeout=30000))
    print(f"## {rotulo}: {pg.url} | {t[:300]}", flush=True)
    try:   # print só da tela visível: o full_page travava em página comprida
        pg.screenshot(path=str(PROVAS / f"{CONTA}_{rotulo}.png"), timeout=15000)
    except Exception:  # noqa: BLE001
        print("   (sem print)", flush=True)
    return t


def entra(ctx, pg):
    """Entra pelo /sign-in. Já logado, ele manda ao painel; senão aperta 'Continue with Google' e escolhe a conta."""
    pg.goto(SITE + "/sign-in", wait_until="networkidle", timeout=90000)
    pg.wait_for_timeout(6000)
    if "/sign-in" not in pg.url and "/sign-up" not in pg.url:
        return
    bt = pg.locator("button:has-text('Google'), a:has-text('Google')").first
    if not bt.count():
        mostra(pg, "01_sem_botao_google")
        sys.exit("não achei o botão do Google no /sign-in (veja o print em provas)")
    antes = len(ctx.pages)   # o Google às vezes abre em janela nova, às vezes na mesma aba
    try:
        bt.click(timeout=10000)
    except Exception:  # noqa: BLE001
        pass
    pg.wait_for_timeout(6000)
    g = ctx.pages[-1] if len(ctx.pages) > antes else pg
    g.wait_for_load_state("domcontentloaded", timeout=60000)
    g.wait_for_timeout(4000)
    if "accounts.google.com" in g.url:
        # tela "Escolha uma conta": espera carregar e clica no item da conta (o texto exato do e-mail)
        try:
            g.wait_for_load_state("networkidle", timeout=30000)
        except Exception:  # noqa: BLE001
            pass
        for sel in (f"[data-identifier='{CONTA}']", f"[data-email='{CONTA}']", f"text={CONTA}"):
            item = g.locator(sel).first
            try:
                item.wait_for(state="visible", timeout=15000)
                item.click(timeout=10000)
                break
            except Exception:  # noqa: BLE001
                continue
        g.wait_for_timeout(7000)
        for txt in ("Continuar", "Continue", "Permitir", "Allow"):   # tela de consentimento da 1ª vez
            b = g.locator(f"button:has-text('{txt}')").first
            if b.count() and b.is_visible():
                b.click(timeout=8000)
                g.wait_for_timeout(5000)
                break
    for i in range(45):   # volta do Google passa por /sign-in/sso-callback antes do painel (/dash): espera até 90 s
        if "/sign-in" not in pg.url and "/sign-up" not in pg.url and "accounts.google" not in pg.url:
            break
        if i % 5 == 2:   # conta nova: o Clerk pede o "Verify you are human" do Cloudflare; clica na caixinha
            for fr in pg.frames:
                if "challenges.cloudflare.com" in (fr.url or ""):
                    try:
                        fr.locator("input[type=checkbox], label, body").first.click(timeout=5000)
                        print("   clicou no Cloudflare", flush=True)
                    except Exception:  # noqa: BLE001
                        pass
        pg.wait_for_timeout(2000)
    if "/sign-in" in pg.url and "sso-callback" not in pg.url:
        mostra(pg, "02_login_nao_passou")
        sys.exit("o login com Google não passou (veja o print); tente com --visivel")


def acha_chaves(pg):
    t = pg.inner_text("body", timeout=30000)
    vals = [i.get_attribute("value") or "" for i in pg.locator("input").all()]
    achadas = sorted(set(re.findall(r"\b(?:vgf|sk|key)?[_-]?[A-Za-z0-9_\-]{30,90}\b", t + " " + " ".join(vals))))
    for b in pg.locator("button:has-text('Copy'), [aria-label*=copy i]").all():
        try:
            pg.evaluate("navigator.clipboard.writeText('')")
            b.click(timeout=3000)
            pg.wait_for_timeout(700)
            c = (pg.evaluate("navigator.clipboard.readText()") or "").strip()
            if len(c) > 20 and c not in achadas:
                achadas.insert(0, c)   # a copiada pelo botão é a chave de verdade: vai primeiro
        except Exception:  # noqa: BLE001
            pass
    return achadas


def testa(chave):
    """Pede um lugar no armazenamento temporário (não gasta minuto de ffmpeg): 200 = chave boa."""
    r = urllib.request.Request(SITE + "/api/tmp-file", method="POST", data=b"{}",
                               headers={"Authorization": "Bearer " + chave, "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(r, timeout=60) as x:
            return x.status, bool((json.loads(x.read()).get("data") or {}).get("upload_url"))
    except urllib.error.HTTPError as e:
        return e.code, False


porta, proc = cofre.abrir(CONTA, url="about:blank", visivel=VISIVEL)
with sync_playwright() as pw:
    br = pw.chromium.connect_over_cdp(f"http://127.0.0.1:{porta}")
    try:
        ctx = br.contexts[0]
        ctx.grant_permissions(["clipboard-read", "clipboard-write"], origin=SITE)
        pg = ctx.new_page()
        entra(ctx, pg)
        if "/dash" not in pg.url:   # depois do login às vezes cai na página inicial: vai ao painel
            pg.goto(SITE + "/dash", wait_until="networkidle", timeout=90000)
            pg.wait_for_timeout(6000)
        mostra(pg, "03_painel")
        links = sorted({a.get_attribute("href") or "" for a in pg.locator("a").all()})
        print("links do painel:", [l for l in links if l.startswith("/")][:30], flush=True)
        for l in links:
            if re.search(r"key|token|api", l, re.I) and l.startswith("/") and "docs" not in l and "reference" not in l:
                pg.goto(SITE + l, wait_until="networkidle", timeout=90000)
                pg.wait_for_timeout(5000)
                break
        mostra(pg, "04_pagina_das_chaves")
        if not acha_chaves(pg):   # conta nova: ainda não tem chave
            for nome in ("Create API key", "Create key", "New API key", "Generate", "Create"):
                b = pg.locator("button", has_text=nome).first
                if b.count() and b.is_visible():
                    b.click(timeout=8000)
                    pg.wait_for_timeout(2500)
                    campo = pg.locator("input[type=text]:visible").first
                    if campo.count() and not campo.input_value():
                        campo.fill("n8n")
                        for ok in ("Create", "Save", "Confirm", "Generate"):
                            c = pg.locator("[role=dialog] button, form button", has_text=ok).first
                            if c.count() and c.is_visible():
                                c.click(timeout=8000)
                                pg.wait_for_timeout(3000)
                                break
                    print("criou a chave com o botão:", nome, flush=True)
                    break
        mostra(pg, "05_chave")
        achadas = acha_chaves(pg)
    finally:
        cofre.fechar(proc, br, nome=CONTA)

boas = [a for a in achadas if testa(a)[0] == 200]
print("candidatas:", [a[:5] + "..." + a[-4:] + f"({len(a)})" for a in achadas], "| boas:", len(boas), flush=True)
if not boas:
    sys.exit("nenhuma chave funcionou (veja os prints em provas)")
ARQ.write_text("\n".join(boas))
print("chave guardada em", ARQ.name, flush=True)

if "--n8n" in sys.argv:
    n8n = (AQUI.parent / "n8n6_chave.txt").read_text().strip()
    corpo = {"name": f"Very Good FFmpeg (Bearer) {CONTA}", "type": "httpHeaderAuth",
             "data": {"name": "Authorization", "value": "Bearer " + boas[0]}}
    req = urllib.request.Request("https://n8n6.inovareinteligenciaartificial.com/api/v1/credentials", method="POST",
                                 data=json.dumps(corpo).encode(), headers={"X-N8N-API-KEY": n8n, "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        x = json.loads(r.read())
    print("credencial no n8n6:", x.get("id"), x.get("name"), flush=True)
