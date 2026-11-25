"""Fish Audio pelo site (conta grátis do cofre) — gera falas com uma voz da biblioteca e baixa os áudios.
Dona 18/11: a voz "NARRADOR DO TODO MUNDO ODEIA O CHRIS" (3,78 mi de usos) é a dos Shorts virais — "outro nível
de clone de voz". Leia COMO_OPERAR.md antes de usar.

    python fish_audio.py "Primeira fala." "Segunda fala." -o PASTA            # falas na linha de comando
    python fish_audio.py -f roteiro.txt -o PASTA                                # uma fala por linha
    python fish_audio.py -f roteiro.txt -o PASTA --voz <id_da_voz> --conta <email_do_cofre>

Saída: PASTA/fala_NN.mp3 (take 1 de cada fala), PASTA/fish_tudo.mp3 (todas juntas) e PASTA/relatorio.json
(tempo de cada fala, caracteres, erro). Para sozinho (sem clicar em nada) se aparecer captcha, cobrança ou login.
Regras: conta = só a do cofre registrada para fish_audio (nunca uma conta do Kaggle); 1 conta, sem rodízio de contas
grátis; cada fala até 500 caracteres no grátis (o script corta em frases)."""
import argparse, json, re, subprocess, sys, time
from pathlib import Path

sys.path.insert(0, r"D:\logins-google")
CONTA_PADRAO = "vendeafiliados3@gmail.com"
VOZ_PADRAO = "ac63ad94686b41b3a8e526cc82a99587"  # 25/11: o 4b215a58 (Narrador do Chris) sumiu do Fish (404) — substituto APROVADO pela dona em 25/11 ("Chris novo é muito melhor")
MAX_CHARS = 480  # grátis aceita até 500 por geração; folga
FFMPEG = r"D:\hipercool-materiais\bin\ffmpeg.exe"
PARAR = ("recaptcha", "não sou um robô", "hcaptcha", "turnstile", "verify you are human")


def dividir(texto):
    """Corta texto longo em pedaços de até MAX_CHARS, sempre em fim de frase."""
    frases = re.split(r"(?<=[.!?…])\s+", texto.strip())
    out, at = [], ""
    for f in frases:
        if len(at) + len(f) + 1 > MAX_CHARS and at:
            out.append(at)
            at = f
        else:
            at = f"{at} {f}".strip()
    return out + ([at] if at else [])


PONTE = r"D:\recapd-ambientes\producao\colab\ponte_proxy_fixo.py"
PONTE_PY = r"D:\recapd-ambientes\producao\colab\venv\Scripts\python.exe"
_PONTES = {}  # N -> (proc, porta)


def _subir_ponte(n):
    """Sobe (ou reusa) a ponte local SEM senha para o IP rnprmtfo-N. Devolve a porta local."""
    import socket as _s
    if n in _PONTES:
        return _PONTES[n][1]
    porta = 18500 + n  # porta local própria por IP
    srv = _s.socket(_s.AF_INET, _s.SOCK_STREAM)
    livre = srv.connect_ex(("127.0.0.1", porta)) != 0
    srv.close()
    py = PONTE_PY if Path(PONTE_PY).exists() else sys.executable
    proc = None
    if livre:
        proc = subprocess.Popen([py, PONTE, str(n), str(porta)], creationflags=0x08000000)
        for _ in range(40):
            t = _s.socket(_s.AF_INET, _s.SOCK_STREAM)
            if t.connect_ex(("127.0.0.1", porta)) == 0:
                t.close()
                break
            t.close()
            time.sleep(0.25)
    _PONTES[n] = (proc, porta)
    return porta


def checar_conta(email):
    """Recusa conta do Kaggle; exige que a conta esteja no pool do Fish (fish_proxy = IP próprio). Devolve (cofre, N)."""
    import io, contextlib, cofre, re
    with contextlib.redirect_stdout(io.StringIO()):
        try:
            if cofre.saida_kaggle(email):
                raise SystemExit(f"{email} é conta do Kaggle — PROIBIDO usar no Fish Audio")
        except RuntimeError:
            raise SystemExit(f"{email} é conta do Kaggle (ponte fora) — PROIBIDO usar no Fish Audio")
    _, e = cofre.conta(email)
    m = re.match(r"rnprmtfo-(\d+)", str(e.get("fish_proxy") or ""))
    if not m:
        raise SystemExit(f"{email} não está no pool do Fish (sem fish_proxy). Rode: pool_fish.py montar")
    return cofre, int(m.group(1))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("falas", nargs="*")
    ap.add_argument("-f", "--arquivo")
    ap.add_argument("-o", "--saida", required=True)
    ap.add_argument("--voz", default=VOZ_PADRAO)
    ap.add_argument("--conta", default=CONTA_PADRAO)
    ap.add_argument("--manter-aberto", action="store_true", help="não fecha o Chrome no fim")
    a = ap.parse_args()
    falas = list(a.falas)
    if a.arquivo:
        falas += [l.strip() for l in Path(a.arquivo).read_text(encoding="utf-8").splitlines() if l.strip()]
    pedacos = [p for f in falas for p in dividir(f)]
    if not pedacos:
        raise SystemExit("nenhuma fala")
    out = Path(a.saida)
    out.mkdir(parents=True, exist_ok=True)

    cofre, ip_n = checar_conta(a.conta)
    porta_proxy = _subir_ponte(ip_n)  # saída fixa da conta (IP rnprmtfo próprio, nunca a casa)
    porta, proc = cofre.abrir(a.conta, extra=(f"--proxy-server=127.0.0.1:{porta_proxy}",))
    rel = {"conta": a.conta, "voz": a.voz, "falas": []}
    from playwright.sync_api import sync_playwright
    try:
        with sync_playwright() as p:
            b = p.chromium.connect_over_cdp(f"http://127.0.0.1:{porta}")
            ctx = b.contexts[0]
            pg = ctx.pages[0] if ctx.pages else ctx.new_page()
            pg.set_viewport_size({"width": 1280, "height": 900})
            pg.goto(f"https://fish.audio/pt/app/text-to-speech/?modelId={a.voz}", wait_until="domcontentloaded",
                    timeout=90000)
            time.sleep(8)
            if "/auth" in pg.url or "Iniciar sessão" in pg.inner_text("body")[:3000]:
                pg.screenshot(path=str(out / "_PRECISA_LOGIN.png"))
                raise SystemExit("conta deslogada no Fish Audio — logar pelo cofre (COMO_OPERAR.md, passo 1)")

            def fechar_avisos():
                for _ in range(3):
                    pg.keyboard.press("Escape")
                    time.sleep(0.4)
                for sel in ("button[aria-label*='lose' i]", "button:has(svg.lucide-x)"):
                    try:
                        loc = pg.locator(sel)
                        for k in range(loc.count()):
                            if loc.nth(k).is_visible():
                                loc.nth(k).click(timeout=1500)
                                time.sleep(0.5)
                    except Exception:  # noqa: BLE001
                        pass

            def baixar_ultimo(destino):
                botoes = pg.locator("button:has(svg.lucide-download)")
                n = botoes.count()
                if not n:
                    return False
                with pg.expect_download(timeout=30000) as d:
                    botoes.nth(n - 2 if n >= 2 else 0).click()  # 2 takes por geração: o 1º dos dois últimos
                d.value.save_as(str(destino))
                return True

            for i, txt in enumerate(pedacos):
                fechar_avisos()
                html = pg.content().lower()
                if any(k in html for k in PARAR):
                    pg.screenshot(path=str(out / "_CAPTCHA.png"))
                    raise SystemExit("CAPTCHA na tela — parei; resolver à mão (COMO_OPERAR.md)")
                antes = pg.locator("button:has(svg.lucide-download)").count()
                ed = pg.locator("[contenteditable='true'], textarea").first
                ed.click()
                pg.keyboard.press("Control+A")
                pg.keyboard.press("Delete")
                pg.keyboard.insert_text(txt)
                t0 = time.time()
                pg.get_by_text("Gerar fala", exact=False).first.click(timeout=15000)
                pronto = False
                for _ in range(360):  # até 3 min
                    time.sleep(0.5)
                    fechar_avisos()
                    if pg.locator("button:has(svg.lucide-download)").count() > antes:
                        pronto = True
                        break
                    corpo = pg.inner_text("body").lower()
                    if "créditos insuficientes" in corpo or "insufficient credit" in corpo or "limite" in corpo \
                            and "atualizar" in corpo:
                        pg.screenshot(path=str(out / "_SEM_CREDITO.png"))
                        raise SystemExit("acabou a cota do mês — parei (não assino nada)")
                dt = round(time.time() - t0, 1)
                destino = out / f"fala_{i:02d}.mp3"
                ok = pronto and baixar_ultimo(destino)
                rel["falas"].append({"i": i, "texto": txt, "chars": len(txt), "gerar_s": dt, "ok": bool(ok)})
                print(f"fala {i}: {'OK' if ok else 'FALHOU'} em {dt}s | {txt[:60]}", flush=True)
                if not ok:
                    pg.screenshot(path=str(out / f"_falhou_{i:02d}.png"))
    finally:
        (out / "relatorio.json").write_text(json.dumps(rel, ensure_ascii=False, indent=1), encoding="utf-8")
        if not a.manter_aberto:
            try:
                cofre.fechar(proc, nome=a.conta)
            except Exception:  # noqa: BLE001
                pass

    partes = sorted(out.glob("fala_[0-9][0-9].mp3"))
    if partes:
        lista = out / "_lista.txt"
        lista.write_text("".join(f"file '{p.as_posix()}'\n" for p in partes), encoding="utf-8")
        subprocess.run([FFMPEG, "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(lista), "-af",
                        "apad=pad_dur=0.25", str(out / "fish_tudo.mp3")], check=False)
        lista.unlink()
    ok = [f for f in rel["falas"] if f["ok"]]
    print(f"PRONTO: {len(ok)}/{len(pedacos)} falas em {out}", flush=True)


if __name__ == "__main__":
    main()
