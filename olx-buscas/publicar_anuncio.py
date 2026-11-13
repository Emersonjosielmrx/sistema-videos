# -*- coding: utf-8 -*-
"""Publica um anúncio na OLX pela conta da dona (Chrome do robô, perfil perfis_chrome/olx).
Uso: python publicar_anuncio.py <anuncio.json> [--publicar]
Sem --publicar: preenche tudo o que reconhece e PARA antes do botão final (print em estado/publicar_*.png).
O formulário da OLX é um assistente de etapas ("Como vai ser o título...", "Continuar"). Cada etapa é reconhecida
pelo texto; etapa desconhecida = para, grava o texto/campos em estado/publicar_etapa.json e o print, para eu ensinar.
"""
import json, re, sys, time
from pathlib import Path
import olx_chat as c
import olx_buscas as o

PR = o.BASE / "estado"


def foto(pg, nome):
    try:
        pg.screenshot(path=str(PR / f"publicar_{nome}.png"), full_page=True)
    except Exception:
        pass


def esperar_ram():
    for _ in range(60):
        if c.ram_livre_mb() >= 1200:
            return
        o.log(f"publicar: RAM {c.ram_livre_mb()} MB, esperando")
        time.sleep(60)
    raise RuntimeError("RAM não liberou em 1 h")


def campos(pg):
    return [(e.evaluate("x => x.tagName"), e.get_attribute("name"), e.get_attribute("type"),
             e.get_attribute("placeholder"), e.get_attribute("id"))
            for e in pg.query_selector_all("input, textarea, select") if e.is_visible() or e.get_attribute("type") == "file"]


def continuar(pg):
    pg.get_by_role("button", name="Continuar").first.click(timeout=8000)
    pg.wait_for_timeout(4000)


def main(arq, publicar):
    a = json.loads(Path(arq).read_text(encoding="utf-8"))
    esperar_ram()
    with c.navegador() as pg:
        # 05/11: os testes repetidos enviaram a carretinha 2x (a OLX manda pra revisão no "Continuar" do preço).
        # Trava: título já existe em qualquer aba da conta = não anuncia de novo.
        for aba in ("publicados", "aguardando-publicacao", "inativos"):
            pg.goto(f"https://conta.olx.com.br/anuncios/{aba}", wait_until="domcontentloaded"); pg.wait_for_timeout(5000)
            if a["titulo"][:60].lower() in pg.evaluate("() => document.body.innerText").lower():
                print(f"JÁ EXISTE em '{aba}': {a['titulo'][:60]} — não vou anunciar de novo"); return
        pg.goto("https://www2.olx.com.br/desapega", wait_until="domcontentloaded"); pg.wait_for_timeout(7000)
        for nome in ("Aceitar", "Começar meu anúncio"):
            try:
                pg.get_by_role("button", name=nome).first.click(timeout=4000); pg.wait_for_timeout(3000)
            except Exception:
                pass
        pg.get_by_text("Produtos", exact=True).first.click(); pg.wait_for_timeout(6000)
        feitas = []
        for passo in range(1, 25):
            for _ in range(20):  # tela de carregamento da IA da OLX ("Preparando o seu anúncio...")
                txt = pg.evaluate("() => document.body.innerText.slice(0, 2500)")
                if "preparando" not in txt.lower() and "preenchendo seu anúncio" not in txt.lower():
                    break
                pg.wait_for_timeout(2000)
            cps = campos(pg)
            foto(pg, f"{passo:02d}")
            t = txt.lower()
            if "título do anúncio" in t and "titulo" not in feitas:
                pg.locator("#subject").fill(a["titulo"][:90]); feitas.append("titulo"); continuar(pg); continue
            if ("descrição" in t or "descreva" in t) and "descricao" not in feitas and pg.locator("textarea").count():
                ta = pg.locator("textarea").first
                ta.click(); ta.fill(a["descricao"]); pg.wait_for_timeout(800)
                if a.get("cep"):  # a OLX preenche o CEP da conta (Paragominas); o item está em outra cidade
                    cep = pg.locator("xpath=//*[contains(text(),'CEP')]/following::input[1]").first
                    cep.click(); cep.fill(""); cep.type(a["cep"], delay=80); pg.wait_for_timeout(3500)
                foto(pg, f"{passo:02d}_descricao")
                n = len(ta.input_value())
                local = pg.evaluate("() => document.body.innerText")
                print(f"descrição: {n} letras; local: {[l for l in local.splitlines() if '- PA' in l][:1]}")
                if n < 50:
                    print("a descrição não entrou — parei"); return
                feitas.append("descricao"); continuar(pg); continue
            if "foto" in t and "fotos" not in feitas and pg.locator("input[type=file]").count():
                pg.locator("input[type=file]").first.set_input_files(a["fotos"][:20])
                pg.wait_for_timeout(8000 + 3000 * len(a["fotos"])); feitas.append("fotos"); foto(pg, f"{passo:02d}b_fotos")
                continuar(pg); continue
            cat_quer = a.get("categoria_final")  # ex.: "Tratores e máquinas agrícolas"
            if cat_quer and "trocar categoria" in t and cat_quer.lower() not in t and "categoria" not in feitas:
                # a IA da OLX escolhe a categoria sozinha e às vezes erra (05/11: "Produção Rural" p/ carretinha)
                pg.get_by_text("Trocar categoria").first.click(); pg.wait_for_timeout(3000)
                foto(pg, f"{passo:02d}_trocar")
                for nivel in a.get("categoria_caminho", []):
                    pg.get_by_text(nivel, exact=True).first.click(); pg.wait_for_timeout(2500)
                feitas.append("categoria"); pg.wait_for_timeout(2000); continue
            if "condição" in t and "condicao" not in feitas and "selecione" in t:
                pg.get_by_text("Selecione", exact=True).first.click(); pg.wait_for_timeout(1500)
                opcoes = [x.inner_text().strip() for x in pg.query_selector_all("[role=option], li") if x.is_visible()]
                print("opções de condição:", opcoes[:12])
                alvo = next((x for x in opcoes if x.lower().startswith("usado")), None)
                if not alvo:
                    foto(pg, f"{passo:02d}_condicao"); print("não achei 'Usado'"); return
                pg.get_by_text(alvo, exact=True).first.click(); pg.wait_for_timeout(1500)
                feitas.append("condicao"); foto(pg, f"{passo:02d}_condicao"); continuar(pg); continue
            if "preço" in t and "preco" not in feitas:
                try:
                    pg.locator("svg, button").filter(has=pg.locator("[d]")).last  # lápis
                    pg.get_by_text("R$", exact=False).first.click(); pg.wait_for_timeout(800)
                except Exception:
                    pass
                inp = pg.locator("input:visible").first
                inp.click(); inp.fill(""); inp.type(str(int(a["preco"])), delay=60); pg.wait_for_timeout(1000)
                foto(pg, f"{passo:02d}_preco")
                print("preço na tela:", [l for l in pg.evaluate("() => document.body.innerText").splitlines() if "R$" in l][:2])
                feitas.append("preco"); continuar(pg); continue
            if "cep" in t and "cep" not in feitas and a.get("cep"):
                pg.locator("input[id*=zip], input[name*=zip], input[placeholder*=CEP]").first.fill(a["cep"])
                pg.wait_for_timeout(3000); feitas.append("cep"); continuar(pg); continue
            botoes = [b.inner_text().strip() for b in pg.query_selector_all("button") if b.is_visible()][:25]
            if ("características" in t and not cps and "Continuar" in botoes and "selecione" not in t
                    and "caracteristicas" not in feitas):
                feitas.append("caracteristicas"); continuar(pg); continue  # nada obrigatório nessa categoria
            # etapa que não conheço (entrega, publicar...): parar e mostrar
            (PR / "publicar_etapa.json").write_text(json.dumps({"passo": passo, "url": pg.url, "feitas": feitas,
                                                                "texto": txt, "campos": cps, "botoes": botoes},
                                                               ensure_ascii=False, indent=1), encoding="utf-8")
            print(f"PAREI na etapa {passo} (feitas: {feitas})")
            print(txt[:1500]); print("campos:", cps); print("botões:", botoes)
            if publicar and any(b.lower() in ("publicar", "publicar anúncio") for b in botoes):
                pg.get_by_role("button", name=re.compile("^Publicar", re.I)).first.click(); pg.wait_for_timeout(8000)
                foto(pg, "final"); print("PUBLICADO?", pg.url, pg.evaluate("() => document.body.innerText.slice(0, 500)"))
            return


if __name__ == "__main__":
    main(sys.argv[1], "--publicar" in sys.argv)
