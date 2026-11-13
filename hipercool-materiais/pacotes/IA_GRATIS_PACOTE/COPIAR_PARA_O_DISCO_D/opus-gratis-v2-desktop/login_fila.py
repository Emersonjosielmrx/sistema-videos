"""Login do Genspark em fila, À MÃO: abre N Chromes visíveis já no "Continuar com Google"; a dona escolhe a conta;
quando aparece um cookie novo do genspark.ai (ou o menu mostra créditos) confere, fecha e abre a próxima.
Uso: python login_fila.py [N=3] [--todas]   (padrão: só contas com logado != True)"""
import sys
import time

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import genspark as g  # noqa: E402
from genspark import cofre  # noqa: E402
from playwright.sync_api import sync_playwright  # noqa: E402

N = int(next((a for a in sys.argv[1:] if a.isdigit()), 3))
dados = g._ler()
_PROVADO = ("já logada (menu)", "login à mão (fila)", "menu")  # logado confirmado pelo menu do rodapé
fila = [c["apelido"] for c in dados["contas"]
        if not (c.get("logado") and c.get("login_detalhe") in _PROVADO) and ("--todas" in sys.argv or not c.get("logado"))]
print(f"{len(fila)} conta(s) na fila, {N} janelas por vez. Ctrl+C para parar.")


def _cookies(ctx):
    return {c["name"] for c in ctx.cookies() if "genspark" in c.get("domain", "")}


def _abrir_modal(pg):
    """Só até o botão do Google (a escolha da conta fica com a dona: o Google recusa o clique automatizado)."""
    if "genspark.ai" not in pg.url:
        g._ir_chat(pg)
    try:
        pg.locator(".sidebar-footer .trigger").locator("visible=true").first.click(timeout=8000)
        time.sleep(1.5)
        pg.get_by_text("Iniciar sessão", exact=False).locator("visible=true").first.click(timeout=4000)
        time.sleep(2.5)
        pg.get_by_text("Continuar com Google", exact=False).locator("visible=true").first.click(timeout=5000)
    except Exception:  # noqa: BLE001
        pass  # se não achar, a dona clica


abertas = {}  # apelido -> (porta, proc, br, base_cookies, desde)
logou, pulou, conferidas = [], [], set()
with sync_playwright() as pw:
    try:
        while fila or abertas:
            # lança os Chromes que faltam de uma vez, já carregando o chat (o SPA carrega em paralelo)
            lote = []
            while fila and len(abertas) + len(lote) < N:
                a = fila.pop(0)
                try:
                    lote.append((a, *cofre.abrir(a, url=g.CHAT_URL, visivel=True)))
                except Exception as e:  # noqa: BLE001
                    print(f"  {a:32} ERRO ao abrir: {str(e)[:70]}")
                    pulou.append(a)
            for a, porta, proc in lote:
                try:
                    br = pw.chromium.connect_over_cdp(f"http://127.0.0.1:{porta}", timeout=45000)
                    for _ in range(20):
                        if br.contexts:
                            break
                        time.sleep(0.5)
                    ctx = br.contexts[0]
                    pg = g._pagina(ctx)
                    _abrir_modal(pg)  # já logada: o modal não abre e a conferência do menu (abaixo) fecha sozinha
                    abertas[a] = (porta, proc, br, _cookies(ctx), time.time())
                    print(f"  {a:32} ABERTA — escolha a conta e clique Continuar")
                except Exception as e:  # noqa: BLE001
                    print(f"  {a:32} ERRO ao abrir: {str(e)[:70]}")
                    pulou.append(a)
            time.sleep(4)
            for a, (porta, proc, br, base, desde) in list(abertas.items()):
                try:
                    ctx = br.contexts[0]
                    voltou = any("genspark.ai" in p.url for p in ctx.pages) and not any(
                        "accounts.google" in p.url for p in ctx.pages)
                    novos = _cookies(ctx) - base
                except Exception:  # noqa: BLE001  janela fechada pela dona
                    print(f"  {a:32} janela fechada — pulei")
                    pulou.append(a)
                    abertas.pop(a)
                    cofre.fechar(proc, None, a)
                    continue
                # cookie novo = acabou de logar; ou nunca saiu do genspark em 25 s = provavelmente já estava logada
                if voltou and (novos or (a not in conferidas and time.time() - desde > 25)):
                    conferidas.add(a)  # pelo caminho dos 25 s confere o menu só uma vez
                    pg = g._pagina(ctx)
                    time.sleep(3)
                    logado, cred = g._menu_conta(pg)
                    if logado:
                        g.marcar_logado(a, True, "login à mão (fila)")
                        if cred is not None:
                            g.marcar_creditos(a, cred)
                        print(f"  {a:32} LOGOU ({cred} créditos)")
                        logou.append(a)
                        abertas.pop(a)
                        cofre.fechar(proc, br, a)
                    else:  # não era login: devolve a janela no botão do Google
                        abertas[a] = (porta, proc, br, base | novos, desde)
                        _abrir_modal(pg)
                elif time.time() - desde > 900:
                    print(f"  {a:32} 15 min sem login — pulei")
                    pulou.append(a)
                    abertas.pop(a)
                    cofre.fechar(proc, br, a)
    except KeyboardInterrupt:
        for a, (porta, proc, br, *_r) in abertas.items():
            cofre.fechar(proc, br, a)
print(f"\nLogaram {len(logou)}; puladas {len(pulou)}: {', '.join(pulou)}")
