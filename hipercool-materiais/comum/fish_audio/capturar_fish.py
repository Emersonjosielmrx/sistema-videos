"""capturar_fish.py — captura a chamada REAL de "Gerar fala" e da leitura de créditos do Fish Audio, para depois
replicar por HTTP puro (sem navegador), no molde do gemini-argo / projeto-navegador-sem-navegador.

Reaproveita o fluxo do fish_audio.py (ponte do IP da conta + cofre), abre a página da voz, gera UMA fala curta e
grava todos os pedidos de rede de fish.audio / api.fish.audio (método, url, cabeçalhos, corpo enviado, resposta) em
captura_fish.jsonl. Também grava o localStorage e os cookies (onde pode estar o token de sessão).

    python capturar_fish.py                      # conta padrão (vendeafiliados3), voz padrão
    python capturar_fish.py --conta <email> --voz <id> --texto "Frase curta de teste."

Regra do projeto: nada de endpoint inventado — o fish_http.py só usa o que sair daqui.
"""
import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, r"D:\logins-google")
AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
import fish_audio as fa  # noqa: E402

DOMINIOS = ("fish.audio", "fishaudio")
IGNORAR_EXT = (".js", ".css", ".woff", ".woff2", ".png", ".jpg", ".jpeg", ".svg", ".ico", ".webp", ".gif")


def interessa(url):
    if not any(d in url for d in DOMINIOS):
        return False
    base = url.split("?")[0].lower()
    return not base.endswith(IGNORAR_EXT)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--conta", default=fa.CONTA_PADRAO)
    ap.add_argument("--voz", default=fa.VOZ_PADRAO)
    ap.add_argument("--texto", default="Isto é um teste de captura.")
    ap.add_argument("--saida", default=str(AQUI / "capturas"))
    a = ap.parse_args()

    out = Path(a.saida)
    out.mkdir(parents=True, exist_ok=True)
    jl = (out / "captura_fish.jsonl").open("w", encoding="utf-8")
    eventos = []  # requestId guid -> registro

    import cofre
    cofre_mod, ip_n = fa.checar_conta(a.conta)
    porta_proxy = fa._subir_ponte(ip_n)
    porta, proc = cofre.abrir(a.conta, extra=(f"--proxy-server=127.0.0.1:{porta_proxy}",))
    from playwright.sync_api import sync_playwright
    pendentes = []  # (req) — bodies lidos no fluxo principal, NUNCA dentro do handler (reentrância derruba a página)

    def drenar():
        while pendentes:
            req = pendentes.pop(0)
            try:
                if not interessa(req.url):
                    continue
                resp = req.response()
                reg = {
                    "t": time.strftime("%H:%M:%S"),
                    "metodo": req.method,
                    "url": req.url,
                    "cab_envio": {k: v for k, v in req.headers.items() if k.lower() != "cookie"},
                    "tem_cookie": "cookie" in {k.lower() for k in req.headers},
                    "enviado": None,
                    "status": resp.status if resp else None,
                    "cab_resp": dict(resp.headers) if resp else None,
                    "resposta": None,
                }
                try:
                    reg["enviado"] = req.post_data
                except Exception:  # noqa: BLE001
                    pass
                if resp is not None:
                    ct = (resp.headers.get("content-type") or "").lower()
                    try:
                        if "audio" in ct or "octet-stream" in ct or "video" in ct:
                            reg["resposta"] = f"(binário {ct}, {len(resp.body())} bytes)"
                        else:
                            reg["resposta"] = resp.text()[:400000]
                    except Exception as e:  # noqa: BLE001
                        reg["resposta"] = f"(sem corpo: {str(e)[:80]})"
                eventos.append(reg)
                jl.write(json.dumps(reg, ensure_ascii=False) + "\n")
                jl.flush()
            except Exception as e:  # noqa: BLE001
                print("drenar falhou:", str(e)[:120], flush=True)

    try:
        with sync_playwright() as p:
            b = p.chromium.connect_over_cdp(f"http://127.0.0.1:{porta}")
            ctx = b.contexts[0]
            pg = next((x for x in ctx.pages if "fish" in x.url), None) or (ctx.pages[0] if ctx.pages else ctx.new_page())
            pg.set_viewport_size({"width": 1280, "height": 900})

            # handler só enfileira; a leitura dos corpos é feita por drenar() no fluxo principal
            ctx.on("requestfinished", lambda req: pendentes.append(req) if interessa(req.url) else None)

            print(">> abrindo página da voz...", flush=True)
            pg.goto(f"https://fish.audio/pt/app/text-to-speech/?modelId={a.voz}",
                    wait_until="domcontentloaded", timeout=90000)
            for _ in range(8):
                time.sleep(1)
                drenar()
            if "/auth" in pg.url or "Iniciar sessão" in pg.inner_text("body")[:3000]:
                pg.screenshot(path=str(out / "_PRECISA_LOGIN.png"))
                raise SystemExit("conta deslogada no Fish Audio — logar pelo cofre (COMO_OPERAR.md, passo 1)")

            # onde mora o token de sessão?
            try:
                ls = pg.evaluate("() => { const o={}; for (let i=0;i<localStorage.length;i++){const k=localStorage.key(i);"
                                 "o[k]=String(localStorage.getItem(k)).slice(0,600);} return o; }")
                (out / "localStorage.json").write_text(json.dumps(ls, ensure_ascii=False, indent=1), encoding="utf-8")
                print(f">> localStorage: {len(ls)} chaves -> localStorage.json", flush=True)
            except Exception as e:  # noqa: BLE001
                print("localStorage falhou:", str(e)[:120], flush=True)
            try:
                ck = ctx.new_cdp_session(pg).send("Network.getAllCookies")["cookies"]
                fish_ck = [c for c in ck if any(d in c.get("domain", "") for d in DOMINIOS)]
                (out / "cookies_fish.json").write_text(json.dumps(fish_ck, ensure_ascii=False, indent=1), encoding="utf-8")
                print(f">> cookies de fish.audio: {len(fish_ck)} -> cookies_fish.json", flush=True)
            except Exception as e:  # noqa: BLE001
                print("cookies falhou:", str(e)[:120], flush=True)

            # fecha avisos, digita e gera UMA fala (mesmo gesto do fish_audio.py)
            for _ in range(3):
                pg.keyboard.press("Escape")
                time.sleep(0.4)
            print(">> digitando e gerando fala...", flush=True)
            antes = pg.locator("button:has(svg.lucide-download)").count()
            ed = pg.locator("[contenteditable='true'], textarea").first
            ed.click()
            pg.keyboard.press("Control+A")
            pg.keyboard.press("Delete")
            pg.keyboard.insert_text(a.texto)
            t0 = time.time()
            pg.get_by_text("Gerar fala", exact=False).first.click(timeout=15000)
            for _ in range(240):
                time.sleep(0.5)
                drenar()
                if pg.locator("button:has(svg.lucide-download)").count() > antes:
                    print(f">> fala gerada em {round(time.time()-t0,1)}s", flush=True)
                    break
            for _ in range(4):
                time.sleep(1)
                drenar()

            # clica no download pra capturar de onde vem o mp3 (link assinado ou /audio/...)
            try:
                botoes = pg.locator("button:has(svg.lucide-download)")
                n = botoes.count()
                if n:
                    with pg.expect_download(timeout=30000) as d:
                        botoes.nth(n - 2 if n >= 2 else 0).click()
                    d.value.save_as(str(out / "amostra_captura.mp3"))
                    print(">> baixei amostra_captura.mp3 pelo botão", flush=True)
            except Exception as e:  # noqa: BLE001
                print("download falhou:", str(e)[:120], flush=True)
            for _ in range(3):
                time.sleep(1)
                drenar()

            # leitura de créditos (outro endpoint a replicar)
            print(">> abrindo cobrança (créditos)...", flush=True)
            try:
                pg.goto("https://fish.audio/pt/app/billing/", wait_until="domcontentloaded", timeout=60000)
                for _ in range(8):
                    time.sleep(1)
                    drenar()
            except Exception as e:  # noqa: BLE001
                print("billing falhou:", str(e)[:120], flush=True)
            drenar()
    finally:
        jl.close()
        try:
            cofre.fechar(proc, nome=a.conta)
        except Exception:  # noqa: BLE001
            pass

    print(f"\n=== {len(eventos)} pedidos de fish.audio capturados em {out/'captura_fish.jsonl'} ===")
    for e in eventos:
        env = (e.get("enviado") or "")[:140].replace("\n", " ")
        print(f"{e['t']} {e['metodo']:4s} {e['status']} {e['url'][:110]} | env:{env} | resp:{len(e.get('resposta') or '')}")


if __name__ == "__main__":
    main()
