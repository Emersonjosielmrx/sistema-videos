# -*- coding: utf-8 -*-
r"""acai_design.py — artes PROFISSIONAIS do Açaí O Precioso em HTML/CSS fotografado pelo Chromium (dona 05/11 12h40:
"as artes estão grosseiras, parece que foi feito no Paint, nada profissional"). Tipografia de verdade (Google Fonts),
degradê, sombra, cantos, ícones, fotos reais do perfil/arquivados com recorte suave. 1080x1350 (feed) e 1080x1920.
    D:\veo\venv\Scripts\python.exe acai_design.py amostra
"""
import base64
import sys
from pathlib import Path

FOTOS = Path(r"D:\ms-energy\assets\acai\fotos_boas")
SAIDA = Path(r"D:\ms-energy\videos\acai\fila_para_postar")
ZAP = "(91) 99366-8986"
ZAP2 = "(91) 9270-8006"  # 05/11 dona: os 2 números em toda imagem; os 2 endereços em toda legenda/comentário
END2 = "Rua Elias Nogueira, 16 · Promissão III"
RODAPE_LEG = ("📲 Pedidos e encomendas: (91) 99366-8986 · (91) 9270-8006\n"
              "📍 Unidade 1: Av. Antero Bonifácio, 138 — Promissão I, Paragominas - PA\n"
              "📍 Unidade 2: Rua Elias Nogueira, 16, Paragominas - PA, 68628-531, Brasil")
END = "Av. Antero Bonifácio, 138 · Promissão I"
CID = "Paragominas · PA"
ARROBA = "@acai_oprecioso"

CSS = """
@import url('https://fonts.googleapis.com/css2?family=Anton&family=Poppins:wght@400;600;800&family=Playfair+Display:ital,wght@1,700&display=swap');
*{margin:0;padding:0;box-sizing:border-box}
body{width:1080px;height:1350px;font-family:'Poppins',sans-serif;overflow:hidden;background:#2a0a2c}
.f{position:absolute;inset:0;background-size:cover;background-position:center}
.v{position:absolute;inset:0;background:linear-gradient(180deg,rgba(42,10,44,.05) 0%,rgba(42,10,44,.35) 45%,rgba(42,10,44,.96) 82%)}
.tag{display:inline-block;background:#7AAD0D;color:#fff;font-weight:800;font-size:30px;letter-spacing:3px;
     padding:12px 26px;border-radius:40px;text-transform:uppercase;box-shadow:0 8px 24px rgba(0,0,0,.25)}
.h1{font-family:'Anton';font-size:128px;line-height:1.02;color:#fff;text-transform:uppercase;letter-spacing:1px;
    text-shadow:0 6px 30px rgba(0,0,0,.45)}
.h1 em{font-family:'Playfair Display';font-style:italic;text-transform:none;color:#C9F06B;font-size:.82em}
.sub{font-size:38px;color:#f3e7f3;font-weight:400;margin-top:18px}
.rod{position:absolute;left:0;right:0;bottom:46px;display:flex;justify-content:center;gap:18px;align-items:center;
     color:#fff;font-weight:600;font-size:28px;opacity:.95}
.rod b{background:rgba(255,255,255,.14);padding:8px 20px;border-radius:30px;backdrop-filter:blur(6px)}
.cx{position:absolute;left:70px;right:70px;bottom:150px}
.lst{background:#F6EFF6;width:100%;height:100%;padding:90px 80px}
.lst h2{font-family:'Anton';font-size:96px;color:#5D205C;line-height:1;text-transform:uppercase}
.lst h2 span{color:#7AAD0D}
.it{display:flex;align-items:center;gap:28px;background:#fff;border-radius:28px;padding:26px 34px;margin-top:26px;
    box-shadow:0 14px 34px rgba(93,32,92,.12)}
.n{flex:0 0 86px;height:86px;border-radius:50%;background:linear-gradient(135deg,#7D167B,#B04CAD);color:#fff;
   font-family:'Anton';font-size:48px;display:flex;align-items:center;justify-content:center}
.it p{font-size:40px;font-weight:800;color:#3b1239}
.it small{display:block;font-size:28px;font-weight:400;color:#7a5a79;margin-top:4px}
.cta{position:absolute;inset:0;background:radial-gradient(circle at 30% 20%,#9b2c98 0%,#5D205C 55%,#2a0a2c 100%);
     display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;color:#fff}
.zap{margin-top:40px;background:#25D366;color:#fff;font-family:'Anton';font-size:84px;padding:24px 60px;border-radius:70px;
     box-shadow:0 18px 40px rgba(0,0,0,.35)}
.end{margin-top:46px;font-size:36px;opacity:.95;line-height:1.5}
.logo{font-family:'Playfair Display';font-style:italic;font-size:64px;color:#C9F06B}
"""


def _img(nome):
    return "data:image/jpeg;base64," + base64.b64encode((FOTOS / nome).read_bytes()).decode()


def _pagina(corpo, w=1080, h=1350):
    return (f"<html><head><meta charset='utf-8'><style>{CSS} body{{width:{w}px;height:{h}px}}</style></head>"
            f"<body>{corpo}</body></html>")


def capa(foto, tag, titulo_html, sub, pos="center"):
    return _pagina(f"<div class='f' style=\"background-image:url('{_img(foto)}');background-position:{pos}\"></div><div class='v'></div>"
                   f"<div class='cx'><span class='tag'>{tag}</span><div class='h1' style='margin-top:26px'>{titulo_html}</div>"
                   f"<div class='sub'>{sub}</div></div>"
                   f"<div class='rod'><b>{ARROBA}</b><b>{ZAP}</b><b>{ZAP2}</b></div>")


def lista(titulo_html, itens, foto=None):
    lis = "".join(f"<div class='it'><div class='n'>{i}</div><p>{t}<small>{s}</small></p></div>"
                  for i, (t, s) in enumerate(itens, 1))
    # lista curta deixava a metade de baixo vazia: foto real arredondada preenche (como as artes de agência)
    ft = (f"<div style=\"margin-top:34px;height:{560 - 110 * len(itens)}px;border-radius:34px;"
          f"background:url('{_img(foto)}') center/cover;box-shadow:0 18px 40px rgba(0,0,0,.18)\"></div>"
          if foto and len(itens) <= 4 else "")
    return _pagina(f"<div class='lst'><h2>{titulo_html}</h2>{lis}{ft}</div>"
                   f"<div class='rod' style='color:#5D205C'><b style='background:#eadcea'>{ARROBA}</b>"
                   f"<b style='background:#eadcea'>{ZAP}</b><b style='background:#eadcea'>{ZAP2}</b></div>")


def cta():
    return _pagina(f"<div class='cta'><div class='logo'>Açaí O Precioso</div>"
                   f"<div class='h1' style='font-size:118px;margin-top:20px'>Peça já<br>o seu!</div>"
                   f"<div class='zap'>{ZAP}</div><div class='zap' style='margin-top:22px'>{ZAP2}</div>"
                   f"<div class='end'><b>Unidade 1</b> · {END}<br><b>Unidade 2</b> · {END2}<br><b>{CID}</b></div></div>")


def renderizar(htmls, pasta, w=1080, h=1350):
    from playwright.sync_api import sync_playwright
    pasta.mkdir(parents=True, exist_ok=True)
    arqs = []
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={"width": w, "height": h}, device_scale_factor=1)
        for i, html in enumerate(htmls, 1):
            pg.set_content(html, wait_until="networkidle")
            pg.wait_for_timeout(600)
            a = pasta / f"{i}.jpg"
            pg.screenshot(path=str(a), type="jpeg", quality=94)
            arqs.append(a)
        b.close()
    return arqs


def amostra():
    pasta = SAIDA / "carrossel_beneficios_v2"
    htmls = [
        capa("1e902cb3.jpg", "Açaí nativo", "5 benefícios<br>do <em>açaí puro</em>", "Gostoso e ainda faz bem pra você 💜"),
        lista("Por que <span>açaí</span><br>todo dia?", [
            ("Fonte de energia", "Gorduras boas e carboidrato natural"),
            ("Antioxidante", "Rico em antocianinas, a cor roxa"),
            ("Fibras", "Ajuda na digestão e dá saciedade"),
            ("Imunidade", "Vitaminas e minerais da Amazônia"),
            ("Puro e natural", "Sem mistura, batido na hora")]),
        capa("4354dcd4.jpg", "Na tigela", "Com peixe frito<br>ou <em>camarão</em>", "Do jeito paraense, servido na hora"),
        cta(),
    ]
    (pasta / "legenda.txt").parent.mkdir(parents=True, exist_ok=True)
    (pasta / "legenda.txt").write_text(
        "Além de gostoso, faz bem 💜 Qual benefício você não conhecia?\n\n📲 Pedidos e encomendas: " + ZAP +
        f"\n📍 {END} — {CID}\n\n#açaí #açainativo #paragominas #açaíparaense #acaioprecioso", "utf-8")
    return renderizar(htmls, pasta)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    print(amostra())


# ── LOTE: tudo pronto pra renderizar na PALETA que o cliente escolher (dona 05/11 13h) ─────────────────────────────
_BASE_CORES = {"#2a0a2c": "ESC", "#7AAD0D": "TAG", "#C9F06B": "DESTAQUE", "#F6EFF6": "FUNDO", "#5D205C": "TEXTO",
               "#7D167B": "G1", "#B04CAD": "G2", "#9b2c98": "CTA1", "#eadcea": "PILULA"}
PALETAS = {
    "A": {"ESC": "#2a0a2c", "TAG": "#7AAD0D", "DESTAQUE": "#C9F06B", "FUNDO": "#F6EFF6", "TEXTO": "#5D205C",
          "G1": "#7D167B", "G2": "#B04CAD", "CTA1": "#9b2c98", "PILULA": "#eadcea"},
    "B": {"ESC": "#3a1438", "TAG": "#5D205C", "DESTAQUE": "#F3E3C3", "FUNDO": "#EFE6D6", "TEXTO": "#5D205C",
          "G1": "#5D205C", "G2": "#8A4A88", "CTA1": "#7a3a78", "PILULA": "#e2d5bf"},
    "C": {"ESC": "#1a0619", "TAG": "#C9A24A", "DESTAQUE": "#E8C76A", "FUNDO": "#F7F2EA", "TEXTO": "#3d0f3b",
          "G1": "#3d0f3b", "G2": "#6b2a68", "CTA1": "#4a1347", "PILULA": "#ece2cf"},
    "D": {"ESC": "#0f2a1a", "TAG": "#6A1B6A", "DESTAQUE": "#B9F28A", "FUNDO": "#EEF5EC", "TEXTO": "#1F4D2B",
          "G1": "#1F6B3A", "G2": "#3E9A5B", "CTA1": "#2b7a45", "PILULA": "#d7ead9"},
    "E": {"ESC": "#2a0a2c", "TAG": "#7D167B", "DESTAQUE": "#ffffff", "FUNDO": "#FFFFFF", "TEXTO": "#2b1029",
          "G1": "#7D167B", "G2": "#7D167B", "CTA1": "#7D167B", "PILULA": "#f1e8f1"},
}
HASH = "#açaí #açainativo #paragominas #paragominaspa #açaíparaense #acaioprecioso"

# cada carrossel: lista de slides ("capa", foto, tag, título_html, sub) | ("lista", título_html, [(t, s)]) | ("cta",)
CARROSSEIS = {
    "beneficios": ([("capa", "1e902cb3.jpg", "Açaí nativo", "5 benefícios<br>do <em>açaí puro</em>", "Gostoso e ainda faz bem 💜"),
                    ("lista", "Por que <span>açaí</span><br>todo dia?", [("Fonte de energia", "Gorduras boas e carboidrato natural"),
                     ("Antioxidante", "Rico em antocianinas, a cor roxa"), ("Fibras", "Ajuda na digestão e dá saciedade"),
                     ("Imunidade", "Vitaminas e minerais da Amazônia"), ("Puro e natural", "Sem mistura, batido na hora")]),
                    ("cta",)], "Além de gostoso, faz bem 💜 Qual benefício você não conhecia?"),
    "puro": ([("capa", "49e5a03e.jpg", "100% natural", "Açaí <em>puro</em><br>de verdade", "Sem misturas, do jeito paraense"),
              ("lista", "Como saber se<br>é <span>açaí puro</span>?", [("Sem misturas", "Só o fruto batido, nada mais"),
               ("Cor natural", "Roxo escuro, sem corante"), ("Cheiro ótimo", "Cheiro de açaí fresquinho"),
               ("Sabor incomparável", "Grosso e encorpado")], "191524a4.jpg"), ("cta",)],
             "Açaí puro tem cor, cheiro e sabor de verdade 💜 Aqui é 100% natural!"),
    "acompanhamentos": ([("capa", "4354dcd4.jpg", "Na tigela", "Açaí com<br><em>acompanhamento</em>", "Preparado na hora pra você"),
                         ("lista", "Escolha o <span>seu</span>", [("Filé de dourada", "Frito na hora, sequinho"),
                          ("Charque frito", "O clássico paraense"), ("Calabresa defumada", "Pra quem gosta de sabor forte"),
                          ("Camarão", "Direto pra sua tigela")], "db775002.jpg"), ("cta",)],
                        "Qual acompanhamento combina mais com o seu açaí? 😋 Comenta aqui!"),
    "litro_tigela": ([("capa", "0764a12e.jpg", "Do seu jeito", "No <em>litro</em><br>ou na tigela", "Leve pra casa ou tome aqui"),
                      ("capa", "4354dcd4.jpg", "Tigela na hora", "Com peixe frito<br>ou <em>camarão</em>", "Servido na hora, do jeito paraense"),
                      ("cta",)], "Litro pra levar ou tigela na hora: como você prefere? 💜"),
    "unidade2": ([("capa", "9087290d.jpg", "Novidade", "Agora temos<br>a <em>unidade 2</em>", "Rua Elias Nogueira, 16 · Promissão III", "left bottom"),
                  ("lista", "Duas unidades<br>pra <span>você</span>", [("Unidade 1", "Av. Antero Bonifácio, 138 · Promissão I"),
                   ("Unidade 2", "Rua Elias Nogueira, 16 · Promissão III"), ("Revenda autorizada", "Açaí do Nelson")], "unidade2_placa.jpg"),
                  ("cta",)], "Agora tem Açaí O Precioso mais perto de você 💜 Unidade 2 na Promissão III!"),
    "como_pedir": ([("capa", "191524a4.jpg", "Pedido fácil", "Como pedir<br>seu <em>açaí</em>", "Em 3 passos, sem complicação"),
                    ("lista", "É <span>simples</span>", [("Chama no Zap", ZAP), ("Escolha", "Litro, 500 ml ou tigela"),
                     ("Retire ou receba", "Na loja ou no conforto de casa")], "49e5a03e.jpg"), ("cta",)],
                   "Pedir é fácil 💜 Chama no WhatsApp e garanta o seu!"),
    "encomendas": ([("capa", "0764a12e.jpg", "Encomendas", "Festa, almoço<br>ou <em>família</em>", "A gente separa o seu açaí"),
                    ("lista", "Encomende <span>já</span>", [("Avise com antecedência", "Pelo WhatsApp"),
                     ("Diga a quantidade", "Litros ou 500 ml"), ("Retire na hora marcada", "Fresquinho")], "a3010b0f.jpg"), ("cta",)],
                   "Recebemos encomendas 💜 Domingo em família pede açaí!"),
    "calor": ([("capa", "1e902cb3.jpg", "Dia de calor", "Dia de calor é<br>dia de <em>açaí</em>", "Geladinho e fresquinho"),
               ("cta",)], "Calorão em Paragominas? Já sabe o que fazer 😎💜"),
}


def renderizar_lote(paleta="A", so=None):
    """Renderiza TODOS os carrosséis na paleta escolhida -> fila_para_postar/carrossel_<id>_<paleta>/."""
    import copy
    global CSS
    css0 = CSS
    cores = PALETAS[paleta]
    for hexo, chave in _BASE_CORES.items():
        CSS = CSS.replace(hexo, cores[chave])
    feitos = []
    try:
        for cid, (slides, leg) in CARROSSEIS.items():
            if so and cid not in so:
                continue
            htmls = []
            for s in slides:
                if s[0] == "capa":
                    htmls.append(capa(*s[1:]))
                elif s[0] == "lista":
                    htmls.append(lista(*s[1:]))
                else:
                    htmls.append(cta())
            pasta = SAIDA / f"carrossel_{cid}_{paleta}"
            renderizar(htmls, pasta)
            (pasta / "legenda.txt").write_text(f"{leg}\n\n📲 Pedidos e encomendas: {ZAP}\n📍 {END} — {CID}\n\n{HASH}", "utf-8")
            feitos.append(pasta)
    finally:
        CSS = css0
    return feitos
