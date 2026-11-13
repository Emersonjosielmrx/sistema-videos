r"""gerar.py — monta as landing pages dos produtos (site\<slug>\index.html) e a vitrine (site\index.html) a partir do
conteudo.json, no visual da landing oficial do Hermes Call (css\landing.css copiado de
D:\hermes\hermes-call\_LANDING_OFICIAL). Dona 24/10/2026: as páginas antigas da VPS 157 sumiram.

    python gerar.py      # depois: python publicar.py
"""
import html
import json
from pathlib import Path
from urllib.parse import quote

BASE = Path(__file__).resolve().parent
SITE = BASE / "site"
LOGO = "https://i.postimg.cc/25jW9WFk/image.png"
DOMINIO = "https://www.inovareinteligenciaartificial.com"
EXTRA_CSS = """
.lp-hero{min-height:88vh;display:flex;flex-direction:column;justify-content:center;align-items:center;text-align:center;
 padding:8rem 1.5rem 4rem;max-width:960px;margin:0 auto}
.lp-hero h1{font-size:clamp(2.2rem,5vw,4rem);line-height:1.1;margin-bottom:1.5rem;font-weight:800}
.lp-hero p{font-size:clamp(1.05rem,2vw,1.3rem);color:var(--text-muted);max-width:760px;margin:0 auto 2.5rem}
.lp-hero .tag{font-family:'Space Grotesk',sans-serif;letter-spacing:2px;text-transform:uppercase;color:var(--accent);
 font-size:.9rem;margin-bottom:1rem}
.lp-dor{max-width:820px;margin:0 auto;text-align:center;font-size:1.2rem;line-height:1.7;color:var(--text-main)}
.lp-cta{display:inline-flex;align-items:center;gap:.6rem;font-size:1.1rem;padding:1rem 2rem;border-radius:999px;
 text-decoration:none}
.lp-final{text-align:center;padding:6rem 1.5rem}
.lp-final h2{font-size:clamp(1.8rem,4vw,2.8rem);margin-bottom:1rem}
.lp-grid-prod{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:1.5rem;max-width:1200px;margin:0 auto}
.lp-grid-prod a{text-decoration:none;color:inherit}
.lp-wa{position:fixed;right:20px;bottom:20px;width:60px;height:60px;border-radius:50%;background:#25D366;color:#fff;
 display:flex;align-items:center;justify-content:center;font-size:2rem;z-index:9999;box-shadow:0 8px 25px rgba(0,0,0,.4)}
@media(max-width:768px){.nav-links{display:none}}
html.gsap .reveal{opacity:1;transform:none;transition:none}
.lp-cta{position:relative;overflow:hidden;will-change:transform}
.lp-cta::after{content:"";position:absolute;top:0;left:0;width:40%;height:100%;pointer-events:none;
 background:linear-gradient(90deg,transparent,rgba(255,255,255,.45),transparent);transform:translateX(-150%) skewX(-20deg);
 animation:lp-brilho 3.2s ease-in-out infinite}
@keyframes lp-brilho{0%,55%{transform:translateX(-150%) skewX(-20deg)}100%{transform:translateX(320%) skewX(-20deg)}}
.lp-cta{animation:lp-pulso 1.8s ease-in-out 1.2s infinite}
@keyframes lp-pulso{0%,100%{transform:scale(1)}50%{transform:scale(1.05)}}
@media(prefers-reduced-motion:reduce){.lp-cta,.lp-cta::after{animation:none}.lp-cta::after{display:none}}
@keyframes lp-marquee{0%{transform:translateX(0)}100%{transform:translateX(-50%)}}
@keyframes lp-pisca{0%,100%{opacity:1}50%{opacity:0}}
.price-card .btn-primary,.price-card .btn-outline{display:block;text-align:center;margin-top:auto}
.lp-hero .lp-cta + .lp-cta{margin-left:.6rem}
"""
# 28/10 (dona: GSAP nas landing pages): reveal das seções ao rolar, cartões em cascata, parallax leve no hero e pulso
# no botão de CTA. Sem GSAP (CDN fora) fica o reveal antigo por IntersectionObserver; prefers-reduced-motion = parado.
# Contador de preço/economia NÃO: as páginas não têm esses números (inventar número é proibido nas propagandas).
GSAP = "https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.5"
REVEAL_JS = f"""<script src="{GSAP}/gsap.min.js" defer></script>
<script src="{GSAP}/ScrollTrigger.min.js" defer></script>
<script>window.addEventListener('DOMContentLoaded',function(){{
var calmo=window.matchMedia('(prefers-reduced-motion: reduce)').matches;
var els=document.querySelectorAll('.reveal');
if(calmo){{els.forEach(function(e){{e.classList.add('active')}});return}}
if(!window.gsap||!window.ScrollTrigger){{var o=new IntersectionObserver(function(es){{
 es.forEach(function(e){{if(e.isIntersecting){{e.target.classList.add('active');o.unobserve(e.target)}}}})}},{{threshold:.1}});
 els.forEach(function(el){{o.observe(el)}});return}}
gsap.registerPlugin(ScrollTrigger);document.documentElement.classList.add('gsap');
gsap.utils.toArray('.section-title,.lp-dor,.lp-final h2,.faq-accordion').forEach(function(el){{
 gsap.from(el,{{y:40,opacity:0,duration:.9,ease:'power3.out',scrollTrigger:{{trigger:el,start:'top 88%',once:true}}}})}});
gsap.utils.toArray('.features-grid,.lp-grid-prod').forEach(function(g){{
 gsap.from(g.children,{{y:50,opacity:0,duration:.8,ease:'power3.out',stagger:.12,
  scrollTrigger:{{trigger:g,start:'top 85%',once:true}}}})}});
var h=document.querySelector('.lp-hero');
if(h){{gsap.from(h.children,{{y:30,opacity:0,duration:.9,ease:'power3.out',stagger:.12}});
 // parallax só no desktop e só posição (no celular com CPU lenta ele derrubava os quadros por segundo)
 if(window.matchMedia('(min-width: 769px)').matches)
  gsap.to(h,{{yPercent:-10,ease:'none',scrollTrigger:{{trigger:h,start:'top top',end:'bottom top',scrub:.5}}}})}}
// pulso do botão = CSS (lp-pulso): animação de JS em todo quadro pesava no celular
}});</script>"""


def e(s):
    return html.escape(s or "", quote=True)


def icone(c):
    return c if c.startswith("fa-brands") or c.startswith("fa-solid") else f"fa-solid {c}"


def wa(numero, produto):
    return f"https://wa.me/{numero}?text=" + quote(f"Olá, quero saber mais sobre o {produto}")


def pagina(titulo, descricao, corpo, numero):
    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{e(titulo)}</title>
<meta name="description" content="{e(descricao)}">
<meta property="og:title" content="{e(titulo)}">
<meta property="og:description" content="{e(descricao)}">
<meta property="og:image" content="{LOGO}">
<meta property="og:type" content="website">
<link rel="icon" href="{LOGO}">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=Space+Grotesk:wght@400;500;600;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
<link rel="stylesheet" href="/css/landing.css">
<style>{EXTRA_CSS}{HERO_CSS}</style>
</head>
<body>
<nav class="navbar" id="navbar">
 <a href="/" class="nav-brand"><img src="{LOGO}" alt="Inovare AI" style="height:35px;width:auto;object-fit:contain"></a>
 <div class="nav-links"><a href="/">Produtos</a><a href="#como-funciona">Como funciona</a><a href="#planos">Planos</a><a href="#faq">Dúvidas</a></div>
 <a href="https://wa.me/{numero}" target="_blank" rel="noopener" class="btn-primary">Fale conosco</a>
</nav>
{corpo}
<footer><p>&copy; 2026 Inovare AI - Fábrica de Automação. Todos os direitos reservados.</p></footer>
<a class="lp-wa" href="https://wa.me/{numero}" target="_blank" rel="noopener" aria-label="WhatsApp"><i class="fa-brands fa-whatsapp"></i></a>
{REVEAL_JS}
</body>
</html>
"""


PLANOS = json.loads((BASE / "planos.json").read_text(encoding="utf-8"))["produtos"]
INTEGRACOES = [("fa-brands fa-whatsapp", "WhatsApp"), ("fa-brands fa-instagram", "Instagram"),
               ("fa-brands fa-facebook", "Facebook"), ("fa-brands fa-telegram", "Telegram"), ("fa-solid fa-plug", "n8n"),
               ("fa-solid fa-comments", "Chatwoot"), ("fa-solid fa-robot", "IA de última geração")]
ENTREGA = [("fa-handshake-angle", "1. Implantação com especialista",
            "A nossa equipe configura tudo, conecta os seus canais e ensina a IA com as informações da sua empresa."),
           ("fa-graduation-cap", "2. Treinamento da equipe", "Mostramos para você e para a sua equipe como usar o painel."),
           ("fa-chart-line", "3. Ajustes contínuos", "Acompanhamos os primeiros dias e ajustamos a IA para as novas dúvidas.")]


def secoes_hermes(p, numero):
    """28/10 (dona: "as landing pages são com base na do Hermes Call; é pegar ela e mudar pras coisas que queremos"):
    os blocos da landing oficial (digitação, integrações, gancho, comparativo, como entregamos, planos) com o
    conteúdo de planos.json. Devolve (antes_dos_passos, depois_dos_itens)."""
    x = PLANOS.get(p["slug"])
    if not x:
        return "", ""
    frases = json.dumps(x["objetivos"], ensure_ascii=False)
    marquee = "".join(f'<span style="font-size:1.3rem;color:var(--text-muted);margin-right:3.5rem;opacity:.7">'
                      f'<i class="{i}"></i> {e(t)}</span>' for i, t in INTEGRACOES) * 2
    antes = f"""
<div style="overflow:hidden;white-space:nowrap;padding:1.6rem 0;background:rgba(0,0,0,.5);border-top:1px solid rgba(255,255,255,.05);border-bottom:1px solid rgba(255,255,255,.05)">
 <div style="display:inline-block;animation:lp-marquee 22s linear infinite">{marquee}</div></div>
<section class="section" style="padding-top:3rem;padding-bottom:2rem">
 <div style="text-align:center;max-width:900px;margin:0 auto;font-size:clamp(1.2rem,3vw,1.8rem);font-weight:600;line-height:1.5;min-height:80px">
  <span style="color:#fff">Eu sou o {e(p['nome'])}. Meu objetivo é</span> <span id="lp-digita" style="color:var(--secondary)"></span><span style="color:var(--secondary);animation:lp-pisca 1s infinite">|</span></div>
</section>
<section class="section bg-darker">
 <div class="reveal delay-100" style="max-width:800px;margin:0 auto;text-align:center">
  <i class="{icone(p['icone'])}" style="font-size:3rem;color:var(--accent);margin-bottom:1.5rem"></i>
  <h2 style="font-size:clamp(1.5rem,4vw,2.5rem);margin-bottom:1.5rem;line-height:1.3">{e(x['gancho'][0])}</h2>
  <p style="font-size:1.2rem;color:var(--text-muted);line-height:1.8">{e(x['gancho'][1])}</p></div>
</section>
<script>document.addEventListener('DOMContentLoaded',function(){{var f={frases},i=0,c=0,apaga=false,el=document.getElementById('lp-digita');
if(!el)return;if(window.matchMedia('(prefers-reduced-motion: reduce)').matches){{el.textContent=f[0];return}}
(function passo(){{var t=f[i];el.textContent=t.substring(0,apaga?--c:++c);var v=apaga?30:50;
if(!apaga&&c===t.length){{v=2000;apaga=true}}else if(apaga&&c===0){{apaga=false;i=(i+1)%f.length;v=500}}setTimeout(passo,v)}})()}});</script>"""
    linhas = list(x["comparativo"])
    if x.get("atendente"):
        menor = x["planos"][0][1]
        linhas += [["Custo mensal estimado", "~ R$ 2.500 (salário + encargos)", f"A partir de {menor.replace('a partir de ', '')}"]]
    comp = "".join(f"""<div class="comp-row"><div class="comp-col font-medium">{e(a)}</div>
<div class="comp-col human-col text-red-400">{e(b)}</div><div class="comp-col text-green-400">{e(c)}</div></div>"""
                   for a, b, c in linhas)
    entrega = "".join(f"""<details class="glass" style="margin-bottom:1rem;padding:1.5rem;border-radius:12px;border:1px solid var(--glass-border)"{' open' if n == 0 else ''}>
<summary style="font-size:1.15rem;font-weight:600;color:#fff;display:flex;align-items:center;gap:1rem;cursor:pointer">
<i class="fa-solid {i}" style="color:var(--accent)"></i> {e(t)}</summary>
<p style="color:var(--text-muted);line-height:1.5;margin-top:1rem">{e(d)}</p></details>""" for n, (i, t, d) in enumerate(ENTREGA))
    cards = []
    for n, (nome, preco, periodo, itens) in enumerate(x["planos"]):
        destaque = len(x["planos"]) > 1 and n == len(x["planos"]) - 1 and len(x["planos"]) <= 3
        msg = quote(f"Olá, quero o plano {nome} ({preco.replace('a partir de ', '')}) do {p['nome']}.")
        lis = "".join(f'<li><i class="fa-solid fa-check"></i> {e(t)}</li>' for t in itens)
        cards.append(f"""<div class="price-card{' vip' if destaque else ''} reveal delay-{min(n + 1, 4)}00">
{'<div class="card-badge card-badge-accent">MAIS COMPLETO</div>' if destaque else ''}<h3>{e(nome)}</h3>
<div class="price-value">{e(preco)}<span>{e(periodo)}</span></div><ul class="price-features">{lis}</ul>
<a href="https://wa.me/{numero}?text={msg}" target="_blank" rel="noopener" class="{'btn-primary lp-cta' if destaque else 'btn-outline'}">
<i class="fa-brands fa-whatsapp"></i> Quero este</a></div>""")
    depois = f"""
<section id="comparativo" class="section bg-darker">
 <h2 class="section-title">Do jeito tradicional x com o {e(p['nome'])}</h2>
 <div class="comparison-container reveal"><div class="comp-table">
  <div class="comp-header"><div class="comp-col">Critério</div><div class="comp-col human-col">Tradicional</div>
  <div class="comp-col text-gradient" style="font-weight:800">{e(p['nome'])}</div></div>{comp}</div></div>
</section>
<section class="section">
 <h2 class="section-title">Como entregamos o seu projeto</h2>
 <div class="reveal delay-100" style="max-width:800px;margin:0 auto;text-align:left">{entrega}</div>
</section>
<section id="planos" class="section bg-darker">
 <h2 class="section-title">Planos</h2>
 <div class="pricing-grid">{''.join(cards)}</div>
 <p style="text-align:center;margin-top:2.5rem;color:var(--text-muted);font-size:.9rem"><i class="fa-solid fa-lock" style="color:#25D366"></i> Pagamento seguro · Pix e cartão</p>
</section>"""
    return antes, depois


HERO_CSS = """
.lp-scrub{position:relative}
.lp-sticky{position:sticky;top:0;height:100vh;overflow:hidden;background:#050508}
.lp-sticky canvas{position:absolute;inset:0;width:100%;height:100%;display:block}
.lp-veu{position:absolute;inset:0;background:linear-gradient(90deg,rgba(5,5,8,.92) 0%,rgba(5,5,8,.55) 42%,transparent 65%)}
.lp-hero.lp-hero-scrub{position:relative;z-index:2;min-height:100vh;height:100vh;max-width:620px;margin:0 0 0 6vw;
 align-items:flex-start;text-align:left;padding:6rem 1.5rem 3rem}
.lp-hero-scrub p{margin-left:0}.lp-hero-scrub .lp-botoes{justify-content:flex-start!important}
.lp-dica{position:absolute;bottom:1.4rem;left:50%;transform:translateX(-50%);z-index:3;font-size:.7rem;letter-spacing:2px;
 text-transform:uppercase;color:rgba(255,255,255,.55)}
@media(max-width:768px){
 .lp-veu{background:linear-gradient(180deg,rgba(5,5,8,.95) 0%,rgba(5,5,8,.8) 38%,rgba(5,5,8,.15) 62%,rgba(5,5,8,.5) 100%)}
 .lp-hero.lp-hero-scrub{margin:0 auto;max-width:none;align-items:center;text-align:center;justify-content:flex-start;padding-top:5.5rem}
 .lp-hero-scrub h1{font-size:1.9rem}.lp-hero-scrub p{font-size:1rem;margin:0 auto 1.2rem}
 .lp-hero-scrub .lp-botoes{justify-content:center!important}}
"""


def hero_rolagem(hero, n):
    """28/10 (dona: imagens no topo como no Hermes Call, trocando ao rolar = ilusão de movimento, tipo Apple): o topo
    fica preso enquanto a rolagem passa pelos quadros (hero_quadros.py) desenhados num canvas já carregado (sem
    piscar). Sem quadros = hero normal."""
    if not n:
        return hero
    return f"""<div class="lp-scrub" id="lp-scrub" style="height:{140 + n * 6}vh"><div class="lp-sticky">
<canvas id="lp-canvas" aria-hidden="true"></canvas><div class="lp-veu"></div>{hero}
<div class="lp-dica">role para ver a conversa</div></div></div>
<script>(function(){{var N={n},imgs=[],cv=document.getElementById('lp-canvas'),cx=cv.getContext('2d'),box=document.getElementById('lp-scrub'),atual=-1;
for(var i=0;i<N;i++){{var im=new Image();im.src='quadros/q'+String(i).padStart(2,'0')+'.webp';imgs.push(im)}}
function tam(){{var r=window.devicePixelRatio||1;cv.width=cv.clientWidth*r;cv.height=cv.clientHeight*r;atual=-1;pinta()}}
function pinta(){{var top=box.getBoundingClientRect().top,alt=box.offsetHeight-window.innerHeight;
var p=Math.min(Math.max(-top/Math.max(alt,1),0),1),k=Math.round(p*(N-1)),im=imgs[k];
if(k===atual||!im.complete){{if(!im.complete)im.onload=pinta;return}}atual=k;
var W=cv.width,H=cv.height,s=Math.max(W/1600,H/1000),dw=1600*s,dh=1000*s,fx=cv.clientWidth<769?0.72:0.5;
var dx=Math.min(0,Math.max(W-dw,W/2-fx*dw)),dy=(H-dh)/2;cx.drawImage(im,dx,dy,dw,dh)}}
window.addEventListener('scroll',function(){{requestAnimationFrame(pinta)}},{{passive:true}});
window.addEventListener('resize',tam);imgs[0].onload=tam;if(imgs[0].complete)tam()}})();</script>"""


def faq_preco(p, faq):
    """O FAQ antigo dizia 'A partir de R$ 199' em TODOS os produtos: agora o menor preço do planos.json."""
    x = PLANOS.get(p["slug"])
    if not x:
        return faq
    menor = x["planos"][0][1].replace("a partir de ", "")
    return [[q, (f"A partir de {menor}. Veja os planos acima ou fale com a gente no WhatsApp."
                 if q.lower().startswith("quanto custa") else r)] for q, r in faq]


def produto(p, numero):
    link = wa(numero, p["nome"])
    antes, depois = secoes_hermes(p, numero)
    p = {**p, "faq": faq_preco(p, p["faq"])}
    passos = "".join(f"""<div class="feature-card glass" style="text-align:center">
<div style="font-size:3rem;color:var(--accent);font-weight:800;margin-bottom:1rem;opacity:.3">0{i}</div>
<h3 style="font-size:1.3rem;margin-bottom:1rem">{e(t)}</h3><p style="color:var(--text-muted);line-height:1.5">{e(d)}</p></div>"""
                     for i, (t, d) in enumerate(p["passos"], 1))
    itens = "".join(f"""<div class="feature-card flashlight-card reveal delay-{min(i, 4)}00">
<i class="{icone(c)} feature-icon"></i><h3>{e(t)}</h3><p>{e(d)}</p></div>""" for i, (c, t, d) in enumerate(p["itens"], 1))
    faq = "".join(f"""<div class="faq-item"><div class="faq-header" onclick="this.parentElement.classList.toggle('active')">
{e(q)} <i class="fa-solid fa-chevron-down"></i></div><div class="faq-content"><p>{e(r)}</p></div></div>"""
                  for q, r in p["faq"])
    n_quadros = len(list((SITE / p["slug"] / "quadros").glob("q*.webp")))
    hero = f"""<section class="lp-hero{' lp-hero-scrub' if n_quadros else ''}">
 <div class="tag"><i class="{icone(p['icone'])}"></i> {e(p['nome'])}</div>
 <h1>{p['titulo']}</h1>
 <p>{e(p['subtitulo'])}</p>
 <div class="lp-botoes" style="display:flex;gap:.7rem;flex-wrap:wrap;justify-content:center">
 <a class="btn-primary lp-cta" href="{link}" target="_blank" rel="noopener"><i class="fa-brands fa-whatsapp"></i> Quero testar</a>
 {'<a class="btn-outline" href="#planos" style="padding:1rem 2rem;border-radius:999px"><i class="fa-solid fa-tags"></i> Ver planos</a>' if p['slug'] in PLANOS else ''}</div>
</section>"""
    corpo = f"""
{hero_rolagem(hero, n_quadros)}
{antes}
<section class="section"><p class="lp-dor reveal">{e(p['dor'])}</p></section>
<section id="como-funciona" class="section">
 <h2 class="section-title">Como funciona</h2>
 <div class="features-grid reveal delay-100">{passos}</div>
</section>
<section id="features" class="section bg-darker">
 <h2 class="section-title">O que está incluso</h2>
 <div class="features-grid">{itens}</div>
</section>
{depois}
<section class="lp-final">
 <h2>Pronto para colocar o {e(p['nome'])} para trabalhar?</h2>
 <p style="color:var(--text-muted);margin-bottom:2rem">Fale com a gente no WhatsApp e peça uma demonstração.</p>
 <a class="btn-primary lp-cta" href="{link}" target="_blank" rel="noopener"><i class="fa-brands fa-whatsapp"></i> Falar no WhatsApp</a>
</section>
<section id="faq" class="section bg-darker">
 <h2 class="section-title">Perguntas Frequentes</h2>
 <div class="faq-accordion reveal delay-200">{faq}</div>
</section>"""
    texto = p["subtitulo"]
    return pagina(f"{p['nome']} - Inovare AI", texto, corpo, numero)


def vitrine(prods, numero):
    cards = "".join(f"""<a href="/{p['slug']}/"><div class="feature-card flashlight-card reveal delay-{min(i % 4 + 1, 4)}00">
<i class="{icone(p['icone'])} feature-icon"></i><h3>{e(p['nome'])}</h3><p>{e(p['subtitulo'])}</p></div></a>"""
                    for i, p in enumerate(prods))
    cards = f"""<a href="https://hermescall.opus-sem-limites.com.br" target="_blank" rel="noopener"><div class="feature-card flashlight-card reveal delay-100">
<i class="fa-solid fa-phone feature-icon"></i><h3>Hermes Call</h3><p>Ligações e atendimento por IA no WhatsApp 24h, com voz real e clonada.</p></div></a>""" + cards
    corpo = f"""
<section class="lp-hero" style="min-height:70vh">
 <div class="tag">Inovare AI - Fábrica de Automação</div>
 <h1>Automação com IA para <span class='text-gradient'>vender, atender e crescer</span></h1>
 <p>Soluções prontas para WhatsApp, redes sociais, agenda, vendas e infraestrutura. Escolha a sua.</p>
 <a class="btn-primary lp-cta" href="https://wa.me/{numero}" target="_blank" rel="noopener"><i class="fa-brands fa-whatsapp"></i> Falar com a gente</a>
</section>
<section id="como-funciona" class="section bg-darker">
 <h2 class="section-title">Nossos produtos</h2>
 <div class="lp-grid-prod">{cards}</div>
</section>"""
    return pagina("Inovare AI - Fábrica de Automação", "Soluções de automação com IA para o seu negócio.", corpo, numero)


def main():
    d = json.loads((BASE / "conteudo.json").read_text(encoding="utf-8"))
    n = d["whatsapp"]
    for p in d["produtos"]:
        pasta = SITE / p["slug"]
        pasta.mkdir(parents=True, exist_ok=True)
        (pasta / "index.html").write_text(produto(p, n), encoding="utf-8")
    (SITE / "index.html").write_text(vitrine(d["produtos"], n), encoding="utf-8")
    print(f"{len(d['produtos'])} páginas + vitrine em {SITE}")


if __name__ == "__main__":
    main()
