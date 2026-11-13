# -*- coding: utf-8 -*-
# 06/11: aplica o visual do Hermes Call (preto, verde 152°, Plus Jakarta Sans) e o modo celular (cartões) ao
# PAGINA_NOVA do painel_creditos.py. Roda 1 vez: python _estilo_hermes.py
from pathlib import Path

p = Path(__file__).with_name("painel_creditos.py")
s = p.read_text("utf-8")
ini = s.index("PAGINA_NOVA = r'''")
a = s.index("<style>", ini)
b = s.index("</style>", a)
css = Path(__file__).with_name("_estilo_hermes.css").read_text("utf-8")
s = s[:a] + "<style>\n" + css + "\n</style>" + s[b + len("</style>"):]

TROCAS = [
    ('<td class="n">${esc(c.nome)}', '<td class="n" data-r="Conta">${esc(c.nome)}'),
    ("<td>${barra(c.ps,c.rs)}</td>", '<td data-r="Semana">${barra(c.ps,c.rs)}</td>'),
    ("<td>${barra(c.p5,c.r5)}</td>", '<td data-r="Janela 5 h">${barra(c.p5,c.r5)}</td>'),
    ("<td>${spark(c.hist)}</td>", '<td data-r="3 dias">${spark(c.hist)}</td>'),
    ('<td><span class="tag ${qm[0]}">', '<td data-r="Quem usa"><div><span class="tag ${qm[0]}">'),
    ("pontos a mais que o nosso uso (3 h)</small>`:''}</td>",
     "pontos a mais que o nosso uso (3 h)</small>`:''}</div></td>"),
    ("<td><b>${c.uso3h}</b> / ${c.uso24h}</td>",
     '<td data-r="Pedidos 3 h / 24 h"><span><b>${c.uso3h}</b> / ${c.uso24h}</span></td>'),
    ("<td>${c.grupo===1&&c.libera?`<b>${br(c.libera)}</b><small>em ${falta(c.libera)}</small>`:'—'}</td>",
     "<td data-r=\"Libera em\"><div>${c.grupo===1&&c.libera?`<b>${br(c.libera)}</b><small>em ${falta(c.libera)}</small>`:'—'}</div></td>"),
    ("<td class=\"${idade==null||idade>20?'velho':''}\">",
     "<td data-r=\"Leitura\" class=\"${idade==null||idade>20?'velho':''}\">"),
    ("<td>${ac}</td></tr>`", "<td data-r=\"\"><div class=\"acs\">${ac}</div></td></tr>`"),
    ('<div class="top"><div><h1 id="tit">Créditos das contas</h1>',
     '<div class="pg"><div class="top"><div><h1 id="tit">Créditos das contas</h1>'),
    ('<div class="toast" id="toast"></div>', '</div><div class="toast" id="toast"></div>'),
    ('<label class="sub"><input type="checkbox" id="auto" checked style="flex:none"> atualizar sozinho (30 s)</label></div>',
     '<label class="lbl"><input type="checkbox" id="auto" checked> atualizar sozinho (30 s)</label>'
     '<button class="tema" id="tema">claro / escuro</button></div>'),
    ("$('tit').textContent='Créditos das contas — '+D.prov;",
     "$('tit').innerHTML='Créditos das contas — <em>'+esc(D.prov)+'</em>';"),
    ("$('q').oninput=desenhar;",
     "$('q').oninput=desenhar;try{if(localStorage.tema)document.documentElement.dataset.tema=localStorage.tema}catch(e){}\n"
     "$('tema').onclick=()=>{const t=document.documentElement.dataset.tema==='claro'?'':'claro';"
     "document.documentElement.dataset.tema=t;try{localStorage.tema=t}catch(e){}};"),
    ("const cor=p=>p>30?'var(--ok)':p>0?'var(--meio)':'var(--zero)';",
     "const cor=p=>p>30?'hsl(var(--primary))':p>0?'hsl(var(--warn))':'hsl(var(--bad))';"),
    ('stroke="var(--pri)"', 'stroke="hsl(var(--primary))"'),
    ('<small style="color:var(--meio)">', '<small style="color:hsl(var(--warn))">'),
    ('<title>Créditos das contas</title>', '<meta name="color-scheme" content="dark light"><title>Créditos das contas</title>'),
]
falt = [o for o, _ in TROCAS if o not in s]
for o, n in TROCAS:
    s = s.replace(o, n, 1)
p.write_text(s, "utf-8")
print("trocas", len(TROCAS) - len(falt), "de", len(TROCAS), "| não achadas:", falt)
