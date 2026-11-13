"""tiktok_relogar.py — TikTok deslogado na hora do post: entra de novo com "Continuar com o Google" no MESMO Chrome que o
postador abriu (porta CDP local; vale pro Chrome do PC1 e pro das máquinas pelo túnel), e o postador posta em seguida.

04/11 dona: "qualquer conta que esteja deslogada no TikTok é só logar de novo com o Google, que está logado (conferi ~50
contas)" + "isso já tem que estar no script: se ao postar aparecer deslogado, logar e aí postar; e caso o Google tenha
deslogado, aí sim marca com problema". Mesmo caminho do netbooks\\tiktok_notebooks._logar (botão do Google, escolha da
conta, "Continuar"), sem abrir Chrome nem mexer em máquina. Senha nunca; código por e-mail = lê no Gmail do mesmo perfil.

    relogar(porta, email, log) -> "ok" | "google_deslogado" | "codigo" | "captcha" | "sem_conta" | "falhou: ..."
"""
import json
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "netbooks"))

BOTAO_GOOGLE = re.compile(r"(Continu\w+ com (o )?Google|Continue with Google)", re.I)
GOOGLE_PEDE_LOGIN = re.compile(r"(Fazer login|Sign in|Esqueceu (o )?e-?mail|Forgot email|Digite sua senha|Enter your "
                               r"password|Use outra conta|Use another account)", re.I)


def _logado(pg):
    """O próprio TikTok devolve a conta? '@usuario' | '' (respondeu sem conta) | None (sem resposta)."""
    info = ""
    for _ in range(4):
        try:
            info = pg.evaluate("async () => { try { const r = await fetch('/passport/web/account/info/?aid=1459', "
                               "{credentials: 'include'}); return await r.text(); } catch (e) { return 'ERRO ' + e; } }")
        except Exception as e:  # noqa: BLE001
            info = f"ERRO {e}"
        if info and not str(info).startswith("ERRO") and '"message"' in info:
            break
        time.sleep(5)
    m = re.search(r'"username"\s*:\s*"([^"]+)"', info or "")
    if m:
        return "@" + m.group(1)
    return "" if info and not str(info).startswith("ERRO") and '"message"' in info else None


def relogar(porta, email, log=print, prazo_s=150):
    from playwright.sync_api import sync_playwright
    import tiktok_notebooks as tn  # SEM_APP_JS, _sessao, _codigos_gmail, _digitar_codigo
    email = (email or "").lower()
    with sync_playwright() as p:
        br = p.chromium.connect_over_cdp(f"http://127.0.0.1:{porta}")
        ctx = br.contexts[0]
        ctx.add_init_script(tn.SEM_APP_JS)  # o "abrir app" do TikTok (bytedance://) travava a página
        pg = ctx.new_page()
        try:
            pg.set_viewport_size({"width": 1280, "height": 1000})  # o botão do Google aparece sem rolar
            pg.goto("https://www.tiktok.com/login", timeout=120000)
            pg.wait_for_timeout(5000)
            ja = _logado(pg)
            if ja:
                return "ok"
            botao = pg.get_by_text(BOTAO_GOOGLE).first
            try:
                botao.wait_for(state="attached", timeout=60000)
            except Exception:  # noqa: BLE001
                return "falhou: botão do Google não apareceu"
            for _ in range(10):
                try:
                    if botao.is_visible() and botao.bounding_box() and botao.bounding_box()["y"] < 900:
                        break
                except Exception:  # noqa: BLE001
                    pass
                pg.mouse.move(640, 500)
                pg.mouse.wheel(0, 300)
                pg.wait_for_timeout(700)
            botao.scroll_into_view_if_needed(timeout=30000)
            with ctx.expect_page(timeout=40000) as nova:
                botao.click()
            pop = nova.value
            pop.wait_for_load_state("domcontentloaded")
            fim, sess_t = time.time() + prazo_s, 0.0
            while time.time() < fim:
                if tn._sessao(ctx):
                    sess_t = sess_t or time.time()
                    if pop.is_closed() or time.time() - sess_t > 8:
                        break
                if not pop.is_closed():
                    try:
                        corpo = pop.inner_text("body", timeout=3000)
                    except Exception:  # noqa: BLE001
                        corpo = ""
                    if "challenge/recaptcha" in pop.url or re.search(r"not a robot|não sou um robô", corpo, re.I):
                        return "captcha"
                    escolher = re.search(r"choose an account|escolha uma conta|escolher uma conta", corpo, re.I)
                    # Google sem conta logada neste perfil: pede e-mail/senha em vez de mostrar a conta pra escolher
                    if not escolher and GOOGLE_PEDE_LOGIN.search(corpo) and pop.locator('input[type="email"], '
                                                                                        'input[type="password"]').count():
                        return "google_deslogado"
                    try:
                        if escolher:
                            alvo = pop.locator(f'[data-identifier="{email}"], [data-email="{email}"]') if email else None
                            if not alvo or not alvo.count():
                                alvo = pop.locator("[data-identifier], [data-email]")  # o perfil só tem a conta dele
                            if alvo.count():
                                alvo.first.click(timeout=5000)
                                pop.wait_for_timeout(1500)
                        for t in ("Continuar", "Continue", "Permitir", "Allow"):
                            b = pop.get_by_role("button", name=t)
                            if b.count() and b.first.is_visible():
                                b.first.click()
                                break
                    except Exception:  # noqa: BLE001
                        pass
                try:
                    txt = pg.inner_text("body", timeout=3000).lower()
                except Exception:  # noqa: BLE001
                    txt = ""
                if "nascimento" in txt or "birthday" in txt:
                    return "sem_conta"  # o Google abriria cadastro novo: não cria nada
                if re.search(r"verifi(que se é|ca que és)|verify it'?s you|verifique sua identidade|verification code", txt):
                    antes = tn._codigos_gmail(ctx)[1]
                    try:
                        pg.get_by_text(re.compile(r"^\s*E-?mail\s*$", re.I)).first.click(timeout=8000)
                        pg.wait_for_timeout(3000)
                        for t in ("Enviar código", "Enviar", "Send code"):
                            b = pg.get_by_role("button", name=t)
                            if b.count() and b.first.is_visible() and b.first.is_enabled():
                                b.first.click()
                                break
                    except Exception:  # noqa: BLE001
                        pass
                    if not tn._digitar_codigo(ctx, pg, antes):
                        return "codigo"
                    fim2 = time.time() + 40
                    while time.time() < fim2 and not tn._sessao(ctx):
                        time.sleep(2)
                    break
                time.sleep(2)
            try:  # o TikTok às vezes redireciona no meio (net::ERR_ABORTED) — confere a conta de qualquer jeito
                pg.goto("https://www.tiktok.com/foryou", wait_until="domcontentloaded", timeout=90000)
            except Exception:  # noqa: BLE001
                pass
            pg.wait_for_timeout(8000)
            ok = _logado(pg)
            if ok:
                log(f"  TikTok logado de novo pelo Google: {ok}")
                return "ok"
            return "falhou: o TikTok não confirmou a conta depois do Google"
        finally:
            try:
                pg.close()
            except Exception:  # noqa: BLE001
                pass
            br.close()  # só a conexão CDP — o Chrome continua aberto pro post


ARROBAS = Path(r"D:\postador-de-videos\config\tiktok_arrobas.json")


def arroba(porta):
    """@ do TikTok logado no Chrome desta porta (lido na própria página), ou None se não deu pra ler."""
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        br = p.chromium.connect_over_cdp(f"http://127.0.0.1:{porta}")
        pg = br.contexts[0].new_page()
        try:
            try:
                pg.goto("https://www.tiktok.com/", wait_until="domcontentloaded", timeout=60000)
            except Exception:  # noqa: BLE001
                pass
            pg.wait_for_timeout(4000)
            u = _logado(pg)
            return u or None
        finally:
            try:
                pg.close()
            except Exception:  # noqa: BLE001
                pass
            br.close()


def conferir_conta(conta, porta, cfg_contas, log=print):
    """04/11: os perfis do DESKTOP estavam todos logados no TikTok do Dorama Noturno (@user6824946137963) e 7 posts de
    outras contas caíram lá numa madrugada. Antes de postar: lê o @ do Chrome; (None, motivo) = pode postar? não.
    Regras: @ já registrado pra OUTRA conta = errado; @ diferente do registrado pra ESTA conta = errado; @ novo = registra.
    Semente do registro: os "_obs_arroba" do reuso_plataformas.json. Devolve (True, "@x") ou (False, motivo)."""
    try:
        a = arroba(porta)
    except Exception as e:  # noqa: BLE001
        return False, f"não li o @ do Chrome ({type(e).__name__}) — não posto às cegas"
    if not a:
        return False, "não li o @ do Chrome (sem conta logada?) — não posto às cegas"
    try:
        reg = json.loads(ARROBAS.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        reg = {}
        for c, r in (cfg_contas or {}).items():  # semente: "_obs_arroba": "... TikTok @user123 ..."
            m = re.search(r"@([\w.]+)", str(r.get("_obs_arroba") or ""))
            if m:
                reg[c] = "@" + m.group(1)
    dono = next((c for c, x in reg.items() if x.lower() == a.lower() and c != conta), None)
    if dono:
        return False, f"CONTA ERRADA: o Chrome de {conta} está logado em {a}, que é da conta {dono}"
    if reg.get(conta) and reg[conta].lower() != a.lower():
        return False, f"CONTA ERRADA: o Chrome de {conta} está logado em {a}, mas {conta} é {reg[conta]}"
    if not reg.get(conta):
        reg[conta] = a
        ARROBAS.write_text(json.dumps(reg, ensure_ascii=False, indent=1), encoding="utf-8")
        log(f"  {conta}: @ registrado {a}")
    return True, a


def email_da_conta(conta, r):
    """E-mail do Google desta conta (mesmo mapa do tiktok_notebooks); sem mapa = <perfil>@gmail.com."""
    perfil = r.get("cofre") or r.get("perfil_remoto") or conta
    try:
        import maquina_remota as mr
        return (mr._mapa_perfis().get(perfil) or {}).get("email") or f"{perfil}@gmail.com"
    except Exception:  # noqa: BLE001
        return f"{perfil}@gmail.com"
