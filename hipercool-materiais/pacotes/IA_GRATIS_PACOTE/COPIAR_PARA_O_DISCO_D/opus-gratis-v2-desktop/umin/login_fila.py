# -*- coding: utf-8 -*-
r"""login_fila.py — contas do 1min.ai com login À MÃO, em fila (mesmo esquema do login_fila do Genspark/Instagram).

Abre N Chromes visíveis (cofre) já no "Log in with Google" do app.1min.ai. A dona escolhe a conta no popup do Google
(e clica Continuar na 1ª vez). Assim que o 1min loga (token no indexedDB), o script cria/lê a API key pela API do app
(js/apikey.js), registra no rodízio (`umin.py add`), passa no /free-credits (visita do dia), FECHA a janela e abre a
próxima conta. Por que à mão: o login automático do Google passou a ser barrado depois de alguns em sequência.

  python login_fila.py            # 3 janelas por vez, todas as contas do pool que ainda não têm chave
  python login_fila.py 4          # 4 janelas por vez
  python login_fila.py a@x.com    # só essas contas
Ctrl+C fecha o que abriu. Janela fechada à mão = conta pulada. 15 min sem login = pulada.
"""
import json
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, r"D:\logins-google")
import cofre  # noqa: E402
from playwright.sync_api import sync_playwright  # noqa: E402

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
import criar_contas as cc  # noqa: E402  (pool, chaves já salvas, registro de falha)

URL = "https://app.1min.ai"
USAR_PROXY = False   # --proxy: manda SÓ o 1min por um IP da Webshare (contorna o IP_LOCKED); Google sai de casa
APIKEY_JS = (AQUI / "js" / "apikey.js").read_text(encoding="utf-8")
TOKEN_JS = """(async () => { try {
  const db = await new Promise((ok, err) => { const r = indexedDB.open('ai'); r.onsuccess = () => ok(r.result); r.onerror = () => err(r.error); });
  const raiz = await new Promise((ok) => { const r = db.transaction('keyvaluepairs','readonly').objectStore('keyvaluepairs').get('persist:root');
    r.onsuccess = () => ok(r.result); r.onerror = () => ok(null); });
  if (!raiz) return '';
  const u = JSON.parse(JSON.parse(raiz).authentication).currentUser;
  return (u && u.token) ? (u.email || 'logado') : '';
} catch (e) { return ''; } })()"""
LIMITE_S = 900


def _pagina(ctx):
    for p in ctx.pages:
        if "app.1min.ai" in p.url:
            return p
    p = ctx.pages[0] if ctx.pages else ctx.new_page()
    p.goto(URL, wait_until="domcontentloaded", timeout=45000)
    return p


def _logado(pg):
    try:
        return pg.evaluate(TOKEN_JS) or ""
    except Exception:  # noqa: BLE001  (página navegando)
        return ""


def _abrir_modal(pg):
    """Deixa a janela no botão do Google: fecha o tour (o fundo dele bloqueia), abre o Log In e clica no Google."""
    try:
        time.sleep(3)
        pg.mouse.click(552, 27)            # X do tour "Workspace Management" (sem tour: área vazia do topo)
        time.sleep(1)
        pg.get_by_text("Log In", exact=True).locator("visible=true").first.click(timeout=6000)
        time.sleep(2)
        pg.get_by_text("Log in with Google").locator("visible=true").first.click(timeout=6000)
    except Exception:  # noqa: BLE001
        pass  # se não achar, a dona clica em Log In > Log in with Google


def _coletar(pg, email):
    """Logou: cria/lê a chave, registra no rodízio e resgata a visita do dia. Devolve texto para o log."""
    if "app.1min.ai" not in pg.url or "/free-credits" in pg.url:
        pg.goto(URL, wait_until="domcontentloaded", timeout=45000)
        time.sleep(3)
    info = pg.evaluate(APIKEY_JS)
    if not info or not info.get("ok"):
        return False, f"chave: {(info or {}).get('erro')}"
    ok, saida = cc.salvar(email, info)
    try:
        pg.goto(URL + "/free-credits", wait_until="domcontentloaded", timeout=45000)
        time.sleep(4)
    except Exception:  # noqa: BLE001
        pass
    return ok, f"chave {info['key'][:6]}…{info['key'][-3:]} {'criada' if info.get('criou') else 'já existia'}; {saida.strip()[-60:]}"


def main(a):
    global USAR_PROXY
    if "--proxy" in a:
        USAR_PROXY = True
        a = [x for x in a if x != "--proxy"]
    n = int(next((x for x in a if x.isdigit()), 3))
    salvas = cc.chaves_salvas()
    fila = [x for x in a if "@" in x] or [e for e in cc.emails_do_pool() if e not in salvas]
    if USAR_PROXY:
        print("PROXY LIGADO: o tráfego do 1min sai por um IP da Webshare (Google continua saindo de casa).", flush=True)
    print(f"{len(fila)} conta(s) na fila, {n} janelas por vez. Escolha a conta no popup do Google. Ctrl+C para parar.",
          flush=True)
    abertas = {}  # email -> (proc, br, pg, desde)
    feitas, puladas = [], []
    with sync_playwright() as pw:
        try:
            while fila or abertas:
                while fila and len(abertas) < n:
                    email = fila.pop(0)
                    try:
                        extra = ()
                        if USAR_PROXY:
                            import proxy_umin
                            ipn = proxy_umin.escolher_ip(email)   # NÃO usar 'n': 'n' é o nº de janelas do lote
                            if ipn is None:
                                print(f"  {email:40} PULEI: proxy Webshare sem túnel ao 1min (não abro pelo IP bloqueado)", flush=True)
                                puladas.append(email)
                                continue
                            extra = proxy_umin.flags(ipn)
                            print(f"  {email:40} (proxy Webshare IP {ipn})", flush=True)
                        porta, proc = cofre.abrir(email, url=URL, visivel=True, extra=extra)
                        if USAR_PROXY and not proc:
                            print(f"  {email:40} PULEI: Chrome já aberto SEM proxy (sairia pelo IP bloqueado)", flush=True)
                            puladas.append(email)
                            cofre.fechar(None, None, email)
                            continue
                        br = pw.chromium.connect_over_cdp(f"http://127.0.0.1:{porta}", timeout=45000)
                        for _ in range(20):
                            if br.contexts:
                                break
                            time.sleep(0.5)
                        pg = _pagina(br.contexts[0])
                        pg.bring_to_front()
                        if not _logado(pg):
                            _abrir_modal(pg)
                        abertas[email] = (proc, br, pg, time.time())
                        print(f"  {email:40} ABERTA — escolha a conta no Google", flush=True)
                    except Exception as e:  # noqa: BLE001
                        print(f"  {email:40} ERRO ao abrir: {str(e)[:80]}", flush=True)
                        puladas.append(email)
                time.sleep(4)
                for email, (proc, br, pg, desde) in list(abertas.items()):
                    try:
                        quem = _logado(pg)
                    except Exception:  # noqa: BLE001
                        quem = None
                    if quem is None or pg.is_closed():
                        print(f"  {email:40} janela fechada — pulei", flush=True)
                        puladas.append(email)
                        abertas.pop(email)
                        cofre.fechar(proc, br, email)
                        continue
                    if quem:
                        if quem not in ("logado", email):  # entrou com OUTRA conta Google nessa janela
                            print(f"  {email:40} ATENÇÃO: logou como {quem} — vou registrar essa", flush=True)
                        try:
                            ok, txt = _coletar(pg, quem if "@" in quem else email)
                        except Exception as e:  # noqa: BLE001
                            ok, txt = False, f"{type(e).__name__}: {str(e)[:80]}"
                        print(f"  {email:40} {'OK   ' if ok else 'FALHA'} {txt}", flush=True)
                        (feitas if ok else puladas).append(email)
                        if not ok:
                            cc.marcar_falha(email, "falha_chave_fila")
                        abertas.pop(email)
                        cofre.fechar(proc, br, email)
                    elif time.time() - desde > LIMITE_S:
                        print(f"  {email:40} 15 min sem login — pulei", flush=True)
                        puladas.append(email)
                        abertas.pop(email)
                        cofre.fechar(proc, br, email)
        except KeyboardInterrupt:
            for email, (proc, br, *_r) in abertas.items():
                cofre.fechar(proc, br, email)
    print(f"\nFIM: {len(feitas)} com chave; {len(puladas)} puladas: {', '.join(puladas)}", flush=True)
    print("Rodízio: python umin.py saldo", flush=True)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main(sys.argv[1:])
