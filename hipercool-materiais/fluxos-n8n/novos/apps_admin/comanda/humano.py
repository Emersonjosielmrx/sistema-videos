# Teste "como humano" da Comanda: tudo pelos botões da tela, do cadastro ao fechamento do caixa.
import sys, time, json, traceback
from pathlib import Path
from playwright.sync_api import sync_playwright
BASE = "https://webhookn8n6.inovareinteligenciaartificial.com/webhook"
FT = Path(__file__).parent.parent / "_teste_fotos"
OUT = Path(__file__).parent / "prints_humano"; OUT.mkdir(exist_ok=True)
for f in OUT.glob("*.png"): f.unlink()
erros, passos, n = [], [], [0]


def foto(pg, nome):
    n[0] += 1; pg.screenshot(path=OUT / f"{n[0]:02d}_{nome}.png")


def fecha_modais(pg):
    for _ in range(4):
        if pg.locator(".modal-fundo").count() == 0: break
        pg.locator(".modal-fundo").last.click(position={"x": 3, "y": 3}); pg.wait_for_timeout(200)


def passo(nome, fn):
    t = time.time()
    try:
        fecha_modais(PG); fn(); passos.append(f"OK   {time.time()-t:5.1f}s {nome}")
    except Exception as e:
        passos.append(f"FALHOU {time.time()-t:5.1f}s {nome}: {str(e).splitlines()[0][:160]}")
        try: foto(PG, "FALHA_" + nome.replace(" ", "_")[:30])
        except Exception: pass


def M(x):
    return x.locator(".modal").last


def toast(pg, timeout=60000):
    pg.wait_for_selector(".toast", timeout=timeout); t = pg.locator(".toast").last.inner_text(); return t





D = {}
with sync_playwright() as p:
    b = p.chromium.launch(headless=True, channel="chrome", args=["--disable-gpu"])
    ctx = b.new_context(viewport={"width": 1280, "height": 860}, locale="pt-BR")
    PG = pg = ctx.new_page()
    pg.on("pageerror", lambda e: erros.append(f"JS: {e}"))
    pg.on("response", lambda r: r.status >= 500 and erros.append(f"HTTP {r.status} {r.url[:90]}"))
    dlg = []
    pg.on("dialog", lambda d: d.accept(dlg.pop(0) if dlg else "teste"))

    def cadastro():
        pg.goto(f"{BASE}/comanda"); pg.fill("#nome", "Boteco Humano Teste"); pg.select_option("#tipo", "bar"); pg.fill("#mesas", "6")
        pg.fill("#dono", "Maria"); pg.fill("#senha", "segredo1"); pg.click("#criar")
        pg.wait_for_selector("#ok:not([hidden])", timeout=20000); D["loja"] = pg.locator("#ok b").first.inner_text(); foto(pg, "cadastro_ok")
        pg.locator("#ok a.btn").click(); pg.wait_for_selector(".mesas", timeout=20000)
    passo("cadastro e entrar direto no painel", cadastro)

    def config():
        pg.click('[data-aba="config"]'); pg.wait_for_selector("#pk", timeout=15000)
        pg.fill("#pk", "11999998888"); pg.fill("#pn", "Boteco Humano"); pg.fill("#pc", "Sao Paulo"); pg.fill("#tx", "10")
        pg.set_input_files("#lf", str(FT / "logo.png")); pg.wait_for_timeout(2500)
        pg.click("#sv"); toast(pg); pg.wait_for_timeout(1500)
        pg.wait_for_selector(".qr canvas, .qr img", timeout=15000); foto(pg, "config_qr")
    passo("configurar Pix, logo e ver QR das mesas", config)

    def importar():
        pg.click('[data-aba="produtos"]'); pg.wait_for_selector("#imp", timeout=15000); pg.click("#imp")
        M(pg).locator("textarea").fill("CERVEJAS\nheineken long neck 12,90\nbrahma 600ml ... 14\n\nPETISCOS\nbolinho de bacalhau (6un) 32\ncalabresa acebolada 38,50")
        pg.click("#ler"); pg.wait_for_function("document.querySelector('#ler').textContent.includes('Salvar')", timeout=90000); foto(pg, "importar_previa")
        pg.click("#ler"); t = toast(pg); assert "importado" in t.lower(), t
    passo("importar cardápio com IA (botão)", importar)

    def novo_produto():
        pg.wait_for_selector("#np", timeout=15000); pg.click("#np"); pg.wait_for_selector(".modal #nm")
        M(pg).locator("#nm").fill("Hambúrguer artesanal"); M(pg).locator("#ct").select_option(label="🍔 Lanches")
        M(pg).locator("#ff").set_input_files(str(FT / "prato.jpg")); pg.wait_for_selector(".modal #fv img", timeout=30000)
        M(pg).locator("#dc").fill("pão brioche, blend 180g, cheddar, cebola caramelizada")
        M(pg).locator("#ia").click(); pg.wait_for_function("document.querySelector('.modal #ia').textContent.includes('escrever com IA') && document.querySelector('.modal #dc').value.length > 20 && !document.querySelector('.modal #dc').value.includes('blend 180g, cheddar, cebola')", timeout=60000)
        D["desc"] = M(pg).locator("#dc").input_value()
        M(pg).locator("#pr").fill("36,90"); M(pg).locator("#ma").click(); M(pg).locator("[data-an]").last.fill("Bacon extra"); M(pg).locator("[data-ap]").last.fill("6")
        foto(pg, "produto_novo"); M(pg).locator("#ok").click(); t = toast(pg); assert "salvo" in t.lower(), t
        pg.wait_for_timeout(1200); assert pg.locator("text=Hambúrguer artesanal").count() > 0
    passo("criar produto com foto, descrição da IA e adicional", novo_produto)

    def ficha():
        pg.locator(".prod", has_text="Hambúrguer artesanal").locator("[data-ep]").click(); pg.wait_for_selector(".modal #fi"); M(pg).locator("#fi").click()
        pg.wait_for_selector(".modal #ma"); M(pg).locator("#ma").last.click(); M(pg).locator("[data-i]").last.select_option(label="Pão brioche (un)")
        M(pg).locator("#ma").last.click(); M(pg).locator("[data-i]").last.select_option(label="Blend 160 g (un)")
        foto(pg, "ficha"); M(pg).locator("#ok").last.click(); t = toast(pg); assert "ficha" in t.lower(), t
        fecha_modais(pg); pg.wait_for_timeout(1000)
        assert "margem" in pg.locator(".prod", has_text="Hambúrguer artesanal").inner_text()
    passo("ficha técnica e margem aparecendo", ficha)

    def esgotado():
        pg.locator(".prod", has_text="Suco natural").locator(".chave span").click(); t = toast(pg); assert "esgotado" in t.lower(), t
    passo("marcar Suco como esgotado", esgotado)

    def equipe():
        pg.click('[data-aba="equipe"]'); pg.wait_for_selector("#nu");
        for nm, lg, pp in (("João Garçom", "joao", "garcom"), ("Chef Ana", "ana", "cozinha")):
            pg.click("#nu"); M(pg).locator("#nm").fill(nm); M(pg).locator("#lg").fill(lg); M(pg).locator("#sn").fill("123456"); M(pg).locator("#pp").select_option(pp); M(pg).locator("#ok").click(); toast(pg); pg.wait_for_timeout(800)
        foto(pg, "equipe")
    passo("cadastrar garçom e cozinheira", equipe)

    def abrir_caixa():
        pg.click('[data-aba="caixa"]'); pg.wait_for_selector("#tr"); pg.fill("#tr", "100,00"); pg.click("#ab"); toast(pg); pg.wait_for_selector("#fc")
    passo("abrir caixa com R$ 100 de troco", abrir_caixa)

    def lancar():
        pg.click('[data-aba="mesas"]'); pg.wait_for_selector('[data-m="2"]'); pg.click('[data-m="2"]'); pg.click("[data-add]")
        M(pg).locator("#busca").fill("hamb"); M(pg).locator("[data-p]").first.click(); pg.wait_for_selector(".modal #ob")
        M(pg).locator("[data-a]").first.check(); M(pg).locator("#ma").click(); M(pg).locator("#ob").fill("ponto da carne mal passado")
        M(pg).locator("#ok").click(); M(pg).locator("#busca").fill("heineken"); M(pg).locator("[data-p]").first.click(); M(pg).locator("#ok").click()
        M(pg).locator("#busca").fill("suco"); assert M(pg).locator("[data-p]").first.is_disabled(), "suco esgotado deveria estar bloqueado"
        foto(pg, "lancar_carrinho"); pg.click("#env"); t = toast(pg); assert "cozinha" in t.lower(), t
        pg.wait_for_selector("[data-receber]"); D["total2"] = M(pg).locator("h3").inner_text(); foto(pg, "comanda_mesa2")
    passo("garçom lança 2 hambúrgueres com bacon + cerveja; suco bloqueado", lancar)

    def cliente():
        ctx2 = b.new_context(viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True, locale="pt-BR"); c = ctx2.new_page()
        c.on("pageerror", lambda e: erros.append(f"JS cliente: {e}"))
        pg.click('[data-aba="config"]'); pg.wait_for_selector("[data-qr]"); url = pg.locator("[data-qr]").nth(4).get_attribute("data-qr")
        c.goto(url); c.wait_for_selector("[data-p]", timeout=20000); foto(c, "cliente_cardapio")
        c.locator("[data-p]", has_text="Bolinho").first.click(); c.locator("#ma").click(); c.click("#ok"); c.wait_for_timeout(300)
        c.click("#vc"); c.wait_for_selector("#env"); foto(c, "cliente_carrinho"); c.click("#env"); c.wait_for_selector("text=Pedido enviado", timeout=20000)
        c.locator("[data-fechar]").last.click(); c.click("#cg"); c.wait_for_timeout(800); c.click("#ct"); c.wait_for_selector("#pc"); c.click("#pc"); c.wait_for_timeout(1000); foto(c, "cliente_conta")
        ctx2.close()
    passo("cliente pede pelo QR (mesa 5), chama garçom e pede conta", cliente)

    def cozinha():
        ctx3 = b.new_context(viewport={"width": 1024, "height": 768}, locale="pt-BR"); k = ctx3.new_page()
        k.goto(f"{BASE}/comanda-painel?l={D['loja']}&u=ana"); k.fill("#sn", "123456"); k.click("#ent"); k.wait_for_selector(".cozinha", timeout=20000)
        abas = k.locator("[data-aba]").all_inner_texts(); assert not any("Caixa" in a for a in abas), abas
        foto(k, "cozinha_ana")
        for _ in range(4):
            bt = k.locator('[data-v="pronto"]').first
            if bt.count() == 0: break
            bt.click(); k.wait_for_timeout(900)
        foto(k, "cozinha_prontos"); ctx3.close()
    passo("cozinheira entra, só vê cozinha/produtos e marca tudo pronto", cozinha)

    def garcom_limites():
        ctx4 = b.new_context(viewport={"width": 390, "height": 844}, is_mobile=True, locale="pt-BR"); g = ctx4.new_page()
        g.on("dialog", lambda d: d.accept("cliente desistiu"))
        g.goto(f"{BASE}/comanda-painel?l={D['loja']}&u=joao"); g.fill("#sn", "123456"); g.click("#ent"); g.wait_for_selector(".mesas", timeout=20000)
        foto(g, "garcom_mesas"); g.click('[data-m="2"]'); g.wait_for_selector("[data-add]")
        assert g.locator("[data-receber]").count() == 0, "garçom não deveria ver Receber"
        g.locator("[data-can]").first.click(); t = toast(g); D["garcom_cancel"] = t; foto(g, "garcom_cancelar")
        ctx4.close()
    passo("garçom: não vê Receber e não cancela item já pronto", garcom_limites)

    def receber():
        pg.click('[data-aba="mesas"]'); pg.wait_for_timeout(1500); foto(pg, "mesas_com_chamados")
        pg.click('[data-m="2"]'); pg.wait_for_selector("[data-receber]"); pg.click("[data-receber]"); pg.wait_for_selector("#fin")
        pg.wait_for_selector("#pixqr canvas, #pixqr img", timeout=10000)
        pg.click("#maisf"); pg.locator("[data-v]").nth(0).fill("50,00"); pg.locator("[data-f]").nth(1).select_option("dinheiro")
        pg.locator("[data-v]").nth(1).fill("100"); pg.wait_for_timeout(300); D["troco_txt"] = pg.inner_text("#res"); foto(pg, "receber_pix_dinheiro")
        pg.click("#fin"); t = toast(pg); D["receber"] = t; assert "fechada" in t.lower(), t
    passo("receber mesa 2: Pix R$50 + dinheiro R$100 com troco", receber)

    def juntar():
        pg.wait_for_timeout(800); pg.click('[data-m="5"]'); pg.wait_for_selector("[data-mais]"); pg.click("[data-mais]")
        M(pg).locator("#pr").fill("1"); M(pg).locator("#tr").click(); toast(pg); pg.wait_for_selector("[data-receber]"); D["mesa1"] = M(pg).locator("h3").inner_text()
        pg.click("[data-mais]"); M(pg).locator("#ds").fill("5"); M(pg).locator("#salva").click(); toast(pg)
        pg.wait_for_selector("[data-receber]"); pg.click("[data-receber]"); pg.wait_for_selector("#fin"); pg.fill("#np", "3"); pg.click("#div"); pg.wait_for_timeout(300)
        D["dividido"] = pg.locator("[data-v]").evaluate_all("els => els.map(e => e.value)"); foto(pg, "dividir_3"); pg.click("#fin"); toast(pg)
    passo("transferir mesa 5→1, desconto R$5, dividir em 3", juntar)

    def nota():
        pg.click('[data-aba="estoque"]'); pg.wait_for_selector("#nota"); pg.click("#nota"); M(pg).locator("#f").set_input_files(str(FT / "nota.jpg"))
        pg.wait_for_selector(".modal [data-q]", timeout=90000); foto(pg, "nota_lida"); D["nota_itens"] = M(pg).locator("[data-q]").count()
        M(pg).locator("#ok").click(); t = toast(pg); assert "entrada" in t.lower(), t; pg.wait_for_timeout(1500); foto(pg, "estoque_depois")
    passo("entrada pela FOTO da nota fiscal (botão)", nota)

    def fechar_caixa():
        pg.click('[data-aba="caixa"]'); pg.wait_for_selector("#sg"); pg.click("#sg"); M(pg).locator("#v").fill("20"); M(pg).locator("#o").fill("gelo"); M(pg).locator("#ok").click(); toast(pg)
        pg.wait_for_selector("#fc"); foto(pg, "caixa_aberto"); pg.click("#fc"); pg.fill('.modal [data-k="dinheiro"]', "150"); M(pg).locator("#ok").click()
        pg.wait_for_selector("text=Caixa fechado", timeout=20000); D["caixa"] = pg.locator(".modal").last.inner_text()[:200]; foto(pg, "caixa_fechado")
    passo("sangria e fechar caixa contando R$150", fechar_caixa)

    def relatorio():
        fecha_modais(pg); pg.click('[data-aba="relatorios"]'); pg.wait_for_selector("#ia"); pg.click("#ia")
        pg.wait_for_function("!document.querySelector('#iar').textContent.includes('Analisando') && document.querySelector('#iar').textContent.length > 120", timeout=90000)
        D["analise"] = pg.inner_text("#iar")[:400]; pg.set_viewport_size({"width": 1280, "height": 1600}); foto(pg, "relatorio")
    passo("relatório + análise da IA (botão)", relatorio)
    b.close()

print("\n".join(passos))
print("ERROS:", erros or "nenhum")
print(json.dumps(D, ensure_ascii=False, indent=1))
