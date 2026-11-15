# Teste "como humano" da Central do Instagram: login, sorteio (lista colada → roleta → vídeo baixado), gincana (IA cria pistas,
# salva, ranking público), menção (config + cupom), site (gerar + abrir). Os eventos (direct/menção) são simulados no endpoint.
import json, time, urllib.request
from pathlib import Path
from playwright.sync_api import sync_playwright
B = "https://webhookn8n6.inovareinteligenciaartificial.com/webhook"
OUT = Path(__file__).parent / "prints_humano"; OUT.mkdir(exist_ok=True)
for f in OUT.glob("*"): f.unlink()
SEG = (Path(__file__).parent / ".segredo_eventos").read_text().strip()
erros, passos, D, n = [], [], {}, [0]


def foto(pg, nome, cheia=False):
    n[0] += 1; pg.screenshot(path=OUT / f"{n[0]:02d}_{nome}.png", full_page=cheia)


def M(pg): return pg.locator(".modal").last
def toast(pg, t=60000): pg.wait_for_selector(".toast", timeout=t); return pg.locator(".toast").last.inner_text()


def passo(nome, fn):
    t = time.time()
    try:
        for _ in range(3):
            if PG.locator(".modal-fundo").count(): PG.locator(".modal-fundo").last.click(position={"x": 3, "y": 3}); PG.wait_for_timeout(200)
        fn(); passos.append(f"OK     {time.time()-t:5.1f}s {nome}")
    except Exception as e:
        passos.append(f"FALHOU {time.time()-t:5.1f}s {nome}: {str(e).splitlines()[0][:170]}")
        try: foto(PG, "FALHA")
        except Exception: pass


def evento(ev):
    req = urllib.request.Request(B + "/insta-eventos", data=json.dumps({"segredo": SEG, "evento": ev}).encode(), headers={"Content-Type": "application/json"})
    return urllib.request.urlopen(req, timeout=60).read().decode()


with sync_playwright() as p:
    b = p.chromium.launch(headless=True, channel="chrome", args=["--disable-gpu", "--autoplay-policy=no-user-gesture-required"])
    ctx = b.new_context(viewport={"width": 1280, "height": 860}, locale="pt-BR", accept_downloads=True); PG = pg = ctx.new_page()
    pg.on("pageerror", lambda e: erros.append(f"JS: {e}"))
    pg.on("dialog", lambda d: d.accept("loja de café especial"))

    def entrar():
        pg.goto(f"{B}/insta-painel?c=lucrocomia"); pg.fill("#sn", "segredo1"); pg.click("#ent"); pg.wait_for_selector(".kpis", timeout=20000); foto(pg, "inicio")
    passo("entrar na Central", entrar)

    def sorteio():
        pg.click('[data-aba="sorteio"]'); pg.wait_for_selector("#nv"); pg.click("#nv"); pg.wait_for_selector(".modal .post", timeout=30000)
        pg.locator(".modal .post").first.click(); M(pg).locator("#tt").fill("Sorteio de Teste da Aula"); M(pg).locator("#pr").fill("Mentoria de 1 hora")
        M(pg).locator("summary").click()
        M(pg).locator("#cola").fill("\n".join("@" + x for x in ["maria.silva", "joao_pedro", "ana.costa", "carlos.ia", "bia.santos", "lucas.dev", "fernanda.m", "rafa_lima", "julia.r", "pedro.h", "camila_x", "thiago.b"]))
        M(pg).locator("#usa").click(); foto(pg, "sorteio_novo")
        with ctx.expect_page() as nova:
            M(pg).locator("#ok").click()
        s = nova.value; s.on("pageerror", lambda e: erros.append(f"JS sorteio: {e}")); s.set_viewport_size({"width": 1280, "height": 900})
        s.wait_for_selector("#ir", timeout=20000); s.wait_for_timeout(800); foto(s, "sorteio_antes")
        s.click("#ir"); s.wait_for_timeout(3500); foto(s, "sorteio_girando")
        s.wait_for_selector("#baixar a", timeout=30000); foto(s, "sorteio_resultado")
        D["ganhador"] = s.inner_text("#res"); D["video"] = s.inner_text("#baixar")[:120]
        with s.expect_download() as dl:
            s.click("#baixar a")
        arq = OUT / ("video_sorteio" + Path(dl.value.suggested_filename).suffix); dl.value.save_as(arq); D["video_bytes"] = arq.stat().st_size
        url = s.url; pub = b.new_page(); pub.goto(url + "&publico=1"); pub.wait_for_selector("#res .gan", timeout=20000); pub.wait_for_timeout(500)
        D["publico_mostra_chave"] = "Chave revelada" in pub.inner_text("body"); D["publico_sem_botao"] = pub.locator("#ir").count() == 0; foto(pub, "sorteio_publico", True); pub.close(); s.close()
    passo("sorteio: lista colada → roleta → baixar vídeo → página pública", sorteio)

    def gincana():
        pg.click('[data-aba="gincana"]'); pg.wait_for_selector("#nv"); pg.click("#nv"); pg.wait_for_selector(".modal #tt")
        M(pg).locator("#tt").fill("Caça ao Café"); M(pg).locator("#pr").fill("1 kg de café especial"); M(pg).locator("#pl").fill("CAFE")
        M(pg).locator("#ia").click(); pg.wait_for_function("document.querySelector('.modal [data-r]') && document.querySelector('.modal [data-r]').value.length > 0", timeout=90000)
        # a 1ª pista abre agora (para testar as respostas)
        agora = time.strftime("%Y-%m-%dT%H:%M", time.localtime(time.time() - 120)); depois = time.strftime("%Y-%m-%dT%H:%M", time.localtime(time.time() + 3 * 3600))
        M(pg).locator('[data-a="0"]').fill(agora); M(pg).locator('[data-a="0"]').dispatch_event("change")
        M(pg).locator('[data-f="0"]').fill(depois); M(pg).locator('[data-f="0"]').dispatch_event("change")
        D["resposta1"] = M(pg).locator('[data-r="0"]').input_value(); foto(pg, "gincana_pistas_ia")
        M(pg).locator("#ok").click(); D["gincana"] = toast(pg); pg.wait_for_timeout(1200); foto(pg, "gincana_lista")
    passo("gincana: IA cria pistas, 1ª pista aberta agora, salvar", gincana)

    def jogar():
        conta = "28591422727189335"
        D["ev_inscricao"] = evento({"eventType": "message", "senderId": "9001", "recipientId": conta, "text": "cafe"})
        D["ev_errada"] = evento({"eventType": "message", "senderId": "9001", "recipientId": conta, "text": "chá"})
        D["ev_certa"] = evento({"eventType": "message", "senderId": "9001", "recipientId": conta, "text": D["resposta1"].lower()})
        evento({"eventType": "message", "senderId": "9002", "recipientId": conta, "text": "CAFE"})
        evento({"eventType": "message", "senderId": "9002", "recipientId": conta, "text": D["resposta1"]})
        D["ev_falso"] = evento({"eventType": "message", "senderId": "9003", "recipientId": conta, "text": "CAFE"}) if False else "-"
        pg.wait_for_timeout(5000)
        g = pg.locator("a", has_text="Ranking público").first.get_attribute("href"); r = b.new_page(viewport={"width": 420, "height": 900}); r.goto(g)
        r.wait_for_selector(".rk", timeout=20000); D["ranking"] = r.locator(".rk").all_inner_texts(); foto(r, "gincana_ranking_publico", True); r.close()
    passo("gincana: 2 jogadores pelo direct (simulado), errar/acertar, ranking", jogar)

    def mencao():
        pg.click('[data-aba="mencao"]'); pg.wait_for_selector("#sv"); pg.fill("#cp", "CAFEZIN"); pg.fill("#ds", "15% de desconto"); pg.click("#sv"); toast(pg)
        evento({"eventType": "message", "senderId": "9005", "recipientId": "28591422727189335", "attachments": [{"type": "story_mention", "payload": {"url": "https://picsum.photos/seed/cafe/600/900.jpg"}}]})
        pg.wait_for_timeout(15000); pg.click('[data-aba="inicio"]'); pg.wait_for_timeout(500); pg.click('[data-aba="mencao"]'); pg.wait_for_selector("#sv")
        linhas = pg.locator("table tr").all_inner_texts(); D["mencao_linha"] = linhas[1][:300] if len(linhas) > 1 else "nenhuma"
        cup = pg.locator("table tr").nth(1).locator("b").first.inner_text() if len(linhas) > 1 else ""
        D["cupom"] = cup; foto(pg, "mencao")
        if cup:
            pg.fill("#cc", cup); pg.click("#cv"); pg.wait_for_timeout(1200); D["cupom_1x"] = pg.inner_text("#cr")
            pg.click("#cv"); pg.wait_for_timeout(1200); D["cupom_2x"] = pg.inner_text("#cr")
    passo("menção: config + story_mention simulado + cupom usado 2x", mencao)

    def site():
        pg.click('[data-aba="site"]'); pg.wait_for_selector("#gr"); pg.fill("#wa", "11999998888"); pg.click("#sw"); toast(pg)
        pg.click("#gr"); pg.wait_for_selector("iframe", timeout=120000); pg.wait_for_timeout(1500); foto(pg, "site_painel")
        s = b.new_page(viewport={"width": 1280, "height": 900}); s.goto(f"{B}/insta-site?c=lucrocomia"); s.wait_for_selector(".hero", timeout=20000); s.wait_for_timeout(2500)
        D["site_produtos"] = s.locator(".pr").count(); foto(s, "site_pc", True)
        c = b.new_page(viewport={"width": 390, "height": 844}, is_mobile=True); c.goto(f"{B}/insta-site?c=lucrocomia"); c.wait_for_selector(".hero"); c.wait_for_timeout(2000); foto(c, "site_cel", True); c.close(); s.close()
    passo("site: gerar pelo botão e abrir (PC e celular)", site)
    b.close()
print("\n".join(passos)); print("ERROS:", erros or "nenhum"); print(json.dumps(D, ensure_ascii=False, indent=1))
