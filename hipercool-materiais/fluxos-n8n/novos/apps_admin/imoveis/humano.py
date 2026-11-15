# Teste "como humano" da Vitrine: cadastro, fotos pelo seletor, IA pelo botão, publicar, vídeo pelo botão, cliente manda contato.
import time, json
from pathlib import Path
from playwright.sync_api import sync_playwright
BASE = "https://webhookn8n6.inovareinteligenciaartificial.com/webhook"
FT = Path(__file__).parent.parent / "_teste_fotos"
OUT = Path(__file__).parent / "prints_humano"; OUT.mkdir(exist_ok=True)
for f in OUT.glob("*.png"): f.unlink()
erros, passos, D, n = [], [], {}, [0]


def foto(pg, nome, cheia=False):
    n[0] += 1; pg.screenshot(path=OUT / f"{n[0]:02d}_{nome}.png", full_page=cheia)


def M(pg):
    return pg.locator(".modal").last


def toast(pg, timeout=60000):
    pg.wait_for_selector(".toast", timeout=timeout); return pg.locator(".toast").last.inner_text()


def passo(nome, fn):
    t = time.time()
    try:
        fn(); passos.append(f"OK     {time.time()-t:5.1f}s {nome}")
    except Exception as e:
        passos.append(f"FALHOU {time.time()-t:5.1f}s {nome}: {str(e).splitlines()[0][:160]}")
        try: foto(PG, "FALHA")
        except Exception: pass


with sync_playwright() as p:
    b = p.chromium.launch(headless=True, channel="chrome", args=["--disable-gpu"])
    ctx = b.new_context(viewport={"width": 1280, "height": 860}, locale="pt-BR"); PG = pg = ctx.new_page()
    pg.on("pageerror", lambda e: erros.append(f"JS: {e}"))
    pg.on("response", lambda r: r.status >= 500 and erros.append(f"HTTP {r.status} {r.url[:90]}"))
    pg.on("dialog", lambda d: d.accept())

    def cadastro():
        pg.goto(f"{BASE}/imoveis-criar"); pg.fill("#nome", "Carla Humana Imóveis"); pg.fill("#creci", "54321-F"); pg.fill("#cidade", "Curitiba")
        pg.fill("#whatsapp", "41999990000"); pg.fill("#dono", "Carla"); pg.fill("#senha", "segredo1"); pg.click("#criar")
        pg.wait_for_selector("#ok:not([hidden])", timeout=20000); D["loja"] = pg.locator("#ok b").first.inner_text(); pg.locator("#ok a.btn").click()
        pg.wait_for_selector(".kpis", timeout=20000); foto(pg, "inicio_vazio")
    passo("criar vitrine e cair no painel", cadastro)

    def cadastrar():
        pg.locator("button", has_text="Cadastrar imóvel").first.click(); pg.wait_for_selector(".modal #tt")
        M(pg).locator("#ff").set_input_files([str(FT / f"ap{i}.jpg") for i in range(1, 6)])
        pg.wait_for_function("document.querySelectorAll('.modal .foto').length === 5 && !document.querySelector('.modal .foto .cp[style*=\"#000\"]')", timeout=90000)
        foto(pg, "fotos_subidas")
        M(pg).locator("#pr").fill("1250000"); M(pg).locator("#br").fill("Batel"); M(pg).locator("#ar").fill("140")
        M(pg).locator("#nt").fill("Apartamento alto padrão, reformado em 2025, 2 vagas, prédio com piscina e academia")
        t = time.time(); M(pg).locator("#ia").click()
        pg.wait_for_function("document.querySelector('.modal #ia') && document.querySelector('.modal #ia').textContent.includes('Preencher') && document.querySelector('.modal #tt').value.length > 10", timeout=150000)
        D["ia_seg"] = round(time.time() - t, 1); D["titulo"] = M(pg).locator("#tt").input_value() if pg.locator(".modal").count() else ""
        foto(pg, "ia_preencheu")
        D["dicas"] = M(pg).locator("#dicas").inner_text()[:300]; D["quartos_ia"] = M(pg).locator("#qt").input_value(); D["vagas"] = M(pg).locator("#vg").input_value()
        D["titulo"] = M(pg).locator("#tt").input_value(); D["desc"] = M(pg).locator("#ds").input_value()[:200]
        M(pg).locator(".modal").evaluate("m => m.scrollTop = 99999") if False else None
        M(pg).locator("#sp").click()
    passo("cadastrar: 5 fotos pelo seletor + Preencher com IA", cadastrar)

    def video():
        pg.wait_for_selector("text=Gerar agora o vídeo", timeout=20000); foto(pg, "pergunta_video"); M(pg).locator("[data-s]").click()
        pg.wait_for_selector(".modal #ir", timeout=20000); M(pg).locator("#du").select_option("15"); M(pg).locator("#ir").click()
        t = time.time(); pg.wait_for_selector(".modal #and:not([hidden])", timeout=60000); pg.wait_for_timeout(8000); foto(pg, "video_andando")
        pg.wait_for_selector(".modal video", timeout=420000); D["video_seg"] = round(time.time() - t); pg.wait_for_timeout(2000); foto(pg, "video_pronto")
    passo("publicar e gerar vídeo pelo botão (espera até ficar pronto)", video)

    def rascunho():
        for _ in range(3):
            if pg.locator(".modal-fundo").count(): pg.locator(".modal-fundo").last.click(position={"x": 3, "y": 3})
        pg.locator("button", has_text="Cadastrar imóvel").first.click(); pg.wait_for_selector(".modal #tt")
        M(pg).locator("#tt").fill("Terreno de esquina"); M(pg).locator("#tp").select_option("terreno"); M(pg).locator("#pr").fill("300000")
        M(pg).locator("#sp").click(); D["publicar_sem_foto"] = toast(pg)
        M(pg).locator("#sr").click(); D["rascunho"] = toast(pg); pg.wait_for_timeout(1500); foto(pg, "lista_imoveis", True)
    passo("tentar publicar sem foto (deve barrar) e salvar rascunho", rascunho)

    def cliente():
        c = b.new_context(viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True, locale="pt-BR").new_page()
        c.on("pageerror", lambda e: erros.append(f"JS cliente: {e}"))
        c.goto(f"{BASE}/imoveis?l={D['loja']}"); c.wait_for_selector(".im"); D["site_qtd"] = c.inner_text("#qt"); foto(c, "site_cel", True)
        c.select_option("#fq", "3"); c.wait_for_timeout(300); D["filtro_3q"] = c.inner_text("#qt"); c.select_option("#fq", "0")
        c.locator(".im").first.click(); c.wait_for_selector("h1"); c.wait_for_timeout(2000); foto(c, "imovel_cel", True)
        c.locator("[data-i]").first.click(); c.wait_for_timeout(600); c.mouse.click(370, 30) if False else None; foto(c, "galeria_cel")
        c.keyboard.press("Escape"); c.locator(".lb .x").click() if c.locator(".lb").count() else None
        c.fill("#nm", "Roberto"); c.fill("#tl", "(41) 98888-7777"); c.select_option("#it", "financiamento"); c.fill("#ms", "Aceita FGTS?"); c.click("#env")
        c.wait_for_selector("text=Recebemos", timeout=20000); foto(c, "contato_enviado")
    passo("cliente no celular: site, filtro, imóvel, galeria e mandar contato", cliente)

    def leads():
        pg.click('[data-aba="leads"]'); pg.wait_for_selector(".lead", timeout=15000); pg.locator("[data-l]").first.select_option("visita"); D["lead"] = toast(pg)
        foto(pg, "leads"); pg.click('[data-aba="inicio"]'); pg.wait_for_selector(".kpis"); pg.wait_for_timeout(800); foto(pg, "inicio_cheio", True)
    passo("ver interessado, mudar para 'visita marcada' e ver números", leads)
    b.close()

print("\n".join(passos)); print("ERROS:", erros or "nenhum"); print(json.dumps(D, ensure_ascii=False, indent=1))
