r"""gerar_ms.py — landing page do cliente MS Energy (energia solar no Pará): site\msenergy\index.html.

Dona 28/10: "não tem landing page da MS, você tem que construir também". Identidade do logo real (vermelho #C81E37
sobre preto, "soluções fotovoltaicas"), fotos REAIS das instalações (D:\ms-energy\assets\fotos_instagram, as aprovadas
pela visão e sem rosto: site\msenergy\img). Só os FATOS do kit (produto\kit.py, msenergysolar.pa): nada de valor de
economia, "zerar a conta" ou garantia. Sem WhatsApp cadastrado: o orçamento grátis é pelo direct do Instagram.
Mesmo GSAP das landings dos produtos (gerar.REVEAL_JS).

    python gerar_ms.py      # depois: publicar (pedir à dona antes)
"""
from pathlib import Path

from gerar import REVEAL_JS, e

BASE = Path(__file__).resolve().parent
PASTA = BASE / "site" / "msenergy"
DIRECT = "https://ig.me/m/msenergycap"
INSTA = "https://www.instagram.com/msenergycap/"

PARA_QUEM = [("casa", "fa-house", "Casas", "Projeto do tamanho do consumo da sua família."),
             ("comercio", "fa-store", "Comércios", "Padaria, loja, mercado: o telhado vira gerador de energia."),
             ("industria", "fa-industry", "Indústrias", "Sistemas maiores, com projeto feito para a sua operação."),
             ("rural", "fa-tractor", "Propriedades rurais", "Usina no solo para fazenda, sítio e irrigação.")]
PASSOS = [("Orçamento grátis", "Chame no direct do Instagram e conte como é o seu consumo."),
          ("Projeto", "A equipe estuda o seu telhado ou terreno e desenha o sistema certo."),
          ("Instalação", "Instalação feita pela equipe da MS Energy."),
          ("Manutenção", "Limpeza e revisão para o sistema seguir gerando.")]
FAQ = [("O orçamento é grátis?", "Sim. É só chamar no direct do Instagram @msenergycap."),
       ("Quanto vou economizar na conta de luz?",
        "Depende do seu consumo e do lugar da instalação. No orçamento grátis a equipe calcula para o seu caso."),
       ("Vocês atendem fazenda e área rural?", "Sim: casas, comércios, indústrias e propriedades rurais."),
       ("Vocês fazem manutenção?", "Sim. A MS Energy faz projeto, instalação e manutenção de sistemas de energia solar."),
       ("Onde a MS Energy atende?", "No Pará. Chame no direct para confirmar a sua cidade.")]
GALERIA = ["comercio", "rural", "instalacao", "g1", "industria", "g2", "manutencao", "g3"]  # par: 2 colunas no celular

CSS = """
:root{--red:#C81E37;--red2:#ff3b55;--bg:#0b0b0d;--bg2:#141418;--txt:#f5f5f7;--muted:#a9a9b2}
*{box-sizing:border-box;margin:0;padding:0}html{scroll-behavior:smooth}
body{background:var(--bg);color:var(--txt);font-family:Inter,system-ui,sans-serif;line-height:1.55;overflow-x:hidden}
a{color:inherit}
.nav{position:fixed;top:0;left:0;right:0;z-index:50;display:flex;justify-content:space-between;align-items:center;
 padding:.7rem 1.2rem;background:rgba(11,11,13,.82);backdrop-filter:blur(8px);border-bottom:1px solid #222}
.nav img{height:42px;border-radius:8px}
.btn{display:inline-flex;align-items:center;gap:.55rem;background:var(--red);color:#fff;text-decoration:none;font-weight:700;
 padding:.85rem 1.6rem;border-radius:999px;box-shadow:0 10px 30px rgba(200,30,55,.35)}
.btn:hover{background:var(--red2)}.nav .btn{padding:.55rem 1.1rem;font-size:.92rem}
.lp-hero{position:relative;min-height:92vh;display:flex;flex-direction:column;justify-content:center;align-items:flex-start;
 padding:7rem 1.4rem 3rem;max-width:1100px;margin:0 auto}
.hero-fundo{position:absolute;inset:0;z-index:-1;background:linear-gradient(90deg,rgba(11,11,13,.92) 0%,rgba(11,11,13,.55) 60%,
 rgba(11,11,13,.25)),url(img/hero.jpg) center/cover}
.lp-hero .tag{color:var(--red2);font-weight:700;letter-spacing:2px;text-transform:uppercase;font-size:.85rem;margin-bottom:1rem}
.lp-hero h1{font-size:clamp(2.1rem,5.4vw,3.8rem);line-height:1.08;max-width:760px;margin-bottom:1.2rem;font-weight:800}
.lp-hero h1 span{color:var(--red2)}
.lp-hero p{color:#ddd;font-size:clamp(1.02rem,2vw,1.25rem);max-width:600px;margin-bottom:2rem}
.selo{display:flex;align-items:baseline;gap:.4rem;margin-top:2.2rem;color:var(--muted)}
.selo b{font-size:2.6rem;color:#fff;font-weight:800}
.section{padding:5rem 1.4rem;max-width:1150px;margin:0 auto}
.escuro{background:var(--bg2);box-shadow:0 0 0 100vmax var(--bg2);clip-path:inset(0 -100vmax)}  /* faixa inteira */
.section-title{font-size:clamp(1.7rem,3.6vw,2.5rem);text-align:center;margin-bottom:2.6rem;font-weight:800}
.section-title span{color:var(--red2)}
.lp-dor{max-width:760px;margin:0 auto;text-align:center;font-size:1.25rem;color:#e8e8ec}
.features-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:1.3rem}
.card{background:#17171c;border:1px solid #26262e;border-radius:18px;overflow:hidden}
.card img{width:100%;height:170px;object-fit:cover;display:block}
.card div{padding:1.1rem 1.2rem 1.3rem}.card h3{font-size:1.15rem;margin:.2rem 0 .4rem}
.card i{color:var(--red2)}.card p{color:var(--muted);font-size:.96rem}
.passo{background:#17171c;border:1px solid #26262e;border-radius:18px;padding:1.5rem 1.3rem}
.passo .n{font-size:2.4rem;font-weight:800;color:var(--red);opacity:.85}.passo h3{margin:.3rem 0 .4rem}
.passo p{color:var(--muted)}
.lp-grid-prod{display:grid;grid-template-columns:repeat(3,1fr);gap:.7rem}
.lp-grid-prod img{width:100%;aspect-ratio:1/1;object-fit:cover;border-radius:14px;display:block}
.faq-accordion{max-width:780px;margin:0 auto}
.faq-item{border-bottom:1px solid #2a2a33}.faq-item summary{cursor:pointer;padding:1.1rem 0;font-weight:600;font-size:1.05rem}
.faq-item p{color:var(--muted);padding:0 0 1.1rem}
.lp-final{text-align:center;padding:5.5rem 1.4rem}.lp-final h2{font-size:clamp(1.8rem,4vw,2.7rem);margin-bottom:.8rem}
.lp-final p{color:var(--muted);margin-bottom:2rem}
footer{text-align:center;color:#777;font-size:.85rem;padding:2rem 1rem 5rem;border-top:1px solid #1f1f25}
.flutua{position:fixed;right:18px;bottom:18px;z-index:60;width:58px;height:58px;border-radius:50%;display:flex;
 align-items:center;justify-content:center;font-size:1.8rem;color:#fff;text-decoration:none;
 background:radial-gradient(circle at 30% 107%,#fdf497 0%,#fd5949 45%,#d6249f 60%,#285AEB 90%);box-shadow:0 8px 25px rgba(0,0,0,.45)}
.lp-cta{position:relative;overflow:hidden;will-change:transform;animation:lp-pulso 1.8s ease-in-out 1.2s infinite}
.lp-cta::after{content:"";position:absolute;top:0;left:0;width:40%;height:100%;pointer-events:none;
 background:linear-gradient(90deg,transparent,rgba(255,255,255,.45),transparent);transform:translateX(-150%) skewX(-20deg);
 animation:lp-brilho 3.2s ease-in-out infinite}
@keyframes lp-brilho{0%,55%{transform:translateX(-150%) skewX(-20deg)}100%{transform:translateX(320%) skewX(-20deg)}}
@keyframes lp-pulso{0%,100%{transform:scale(1)}50%{transform:scale(1.05)}}
.reveal{opacity:0;transform:translateY(2rem);transition:all 1s cubic-bezier(.16,1,.3,1)}.reveal.active{opacity:1;transform:none}
html.gsap .reveal{opacity:1;transform:none;transition:none}
@media(max-width:640px){.lp-grid-prod{grid-template-columns:repeat(2,1fr)}.nav .btn span{display:none}
 .hero-fundo{background:linear-gradient(180deg,rgba(11,11,13,.15) 0%,rgba(11,11,13,.55) 35%,rgba(11,11,13,.9) 75%),
  url(img/hero.jpg) center top/cover}}
@media(prefers-reduced-motion:reduce){.lp-cta,.lp-cta::after{animation:none}.lp-cta::after{display:none}}
"""
# contador do selo "quase 10 anos" (é fato do kit) — só com GSAP e sem prefers-reduced-motion
CONTADOR_JS = """<script>window.addEventListener('load',function(){var el=document.getElementById('anos');
if(!el||!window.gsap||window.matchMedia('(prefers-reduced-motion: reduce)').matches)return;
var o={v:0};gsap.to(o,{v:10,duration:1.6,ease:'power2.out',delay:.6,onUpdate:function(){el.textContent=Math.round(o.v)}})});
</script>"""


def pagina():
    para = "".join(f"""<div class="card"><img src="img/{f}.jpg" alt="{e(t)} com energia solar instalada pela MS Energy"
 loading="lazy"><div><h3><i class="fa-solid {i}"></i> {e(t)}</h3><p>{e(d)}</p></div></div>""" for f, i, t, d in PARA_QUEM)
    passos = "".join(f"""<div class="passo"><div class="n">0{n}</div><h3>{e(t)}</h3><p>{e(d)}</p></div>"""
                     for n, (t, d) in enumerate(PASSOS, 1))
    gal = "".join(f'<img src="img/{g}.jpg" alt="Instalação de energia solar da MS Energy no Pará" loading="lazy">'
                  for g in GALERIA)
    faq = "".join(f"<details class='faq-item'><summary>{e(q)}</summary><p>{e(r)}</p></details>" for q, r in FAQ)
    cta = f'<a class="btn lp-cta" href="{DIRECT}" target="_blank" rel="noopener"><i class="fa-brands fa-instagram"></i> '
    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>MS Energy - Energia solar no Pará | Orçamento grátis</title>
<meta name="description" content="Energia solar para casas, comércios, indústrias e propriedades rurais no Pará. Projeto, instalação e manutenção. Orçamento grátis pelo direct do Instagram.">
<meta property="og:title" content="MS Energy - Energia solar no Pará">
<meta property="og:description" content="Projeto, instalação e manutenção de energia solar. Orçamento grátis.">
<meta property="og:image" content="img/hero.jpg"><link rel="icon" href="img/logo.jpg">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap" rel="stylesheet">
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
<style>{CSS}</style>
</head>
<body>
<nav class="nav"><a href="#"><img src="img/logo.jpg" alt="MS Energy - soluções fotovoltaicas"></a>
 <a class="btn" href="{DIRECT}" target="_blank" rel="noopener"><i class="fa-brands fa-instagram"></i><span> Orçamento grátis</span></a></nav>
<div class="hero-fundo"></div>
<section class="lp-hero">
 <div class="tag">Energia solar no Pará</div>
 <h1>Sua conta de luz alta? <span>Gere a sua própria energia</span> com o sol.</h1>
 <p>Projeto, instalação e manutenção de energia solar para casas, comércios, indústrias e propriedades rurais.</p>
 {cta}Peça seu orçamento grátis</a>
 <div class="selo">quase <b id="anos">10</b> anos no mercado de energia solar</div>
</section>
<section class="section escuro"><p class="lp-dor">Gerar a própria energia com o sol diminui a conta de luz. Quem
 calcula o sistema certo para você é a equipe da MS Energy, no orçamento grátis.</p></section>
<section class="section"><h2 class="section-title">Para <span>quem</span> é</h2><div class="features-grid">{para}</div></section>
<section class="section escuro"><h2 class="section-title">Como <span>funciona</span></h2><div class="features-grid">{passos}</div></section>
<section class="section"><h2 class="section-title">Instalações <span>reais</span> da MS Energy</h2>
 <div class="lp-grid-prod">{gal}</div></section>
<section class="section escuro"><h2 class="section-title">Perguntas <span>frequentes</span></h2><div class="faq-accordion">{faq}</div></section>
<section class="lp-final"><h2>Peça o seu orçamento grátis</h2><p>Chame a MS Energy no direct do Instagram.</p>
 {cta}Chamar no direct</a></section>
<footer>MS Energy - soluções fotovoltaicas · Pará · <a href="{INSTA}" target="_blank" rel="noopener">@msenergycap</a></footer>
<a class="flutua" href="{DIRECT}" target="_blank" rel="noopener" aria-label="Instagram da MS Energy"><i class="fa-brands fa-instagram"></i></a>
{REVEAL_JS}
{CONTADOR_JS}
</body>
</html>
"""


def main():
    PASTA.mkdir(parents=True, exist_ok=True)
    (PASTA / "index.html").write_text(pagina(), encoding="utf-8")
    print(f"MS Energy em {PASTA / 'index.html'}")


if __name__ == "__main__":
    main()
