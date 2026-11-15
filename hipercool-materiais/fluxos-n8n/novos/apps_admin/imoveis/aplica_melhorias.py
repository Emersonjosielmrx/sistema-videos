from pathlib import Path
A = Path(__file__).parent

# ── página do imóvel: simulador de financiamento (SAC e Price) ──
p = A / "imovel.html"; t = p.read_text(encoding="utf-8")
a = """      ${I.caracteristicas.length ? `<div class="sec">O que tem</div>"""
assert a in t, "imovel"
t = t.replace(a, """      ${I.finalidade === 'venda' && Number(I.preco) > 0 ? `<div class="sec">🏦 Simule o financiamento</div><div class="card" id="sim">
        <div class="linha"><div><label>Entrada (R$)</label><input id="se" inputmode="numeric"></div><div><label>Prazo</label><select id="sp">${[420, 360, 300, 240, 180, 120].map(m => `<option value="${m}">${m / 12} anos</option>`).join('')}</select></div>
        <div><label>Juros ao ano (%)</label><input id="sj" inputmode="decimal"></div><div><label>Sistema</label><select id="ss"><option value="sac">SAC (parcela cai)</option><option value="price">Price (parcela fixa)</option></select></div></div>
        <div class="carac" id="sr" style="margin-top:12px"></div><p class="mu pq">Simulação aproximada, sem seguro e taxas do banco. A aprovação depende da análise de crédito. Mínimo de entrada costuma ser 20%.</p></div>` : ''}
      ${I.caracteristicas.length ? `<div class="sec">O que tem</div>""")
a = """  const clique = () => api('clique', { loja: LOJA, codigo: COD }, 1);"""
assert a in t
t = t.replace(a, """  if ($('#sim')) {
    const preco = Number(I.preco); $('#se').value = Math.round(preco * 0.2).toLocaleString('pt-BR'); $('#sj').value = String(L.juros_ano || 11.5).replace('.', ',');
    const calc = () => {
      const ent = num($('#se').value), fin = Math.max(0, preco - ent), n = Number($('#sp').value), i = Math.pow(1 + numIn($('#sj').value) / 100, 1 / 12) - 1;
      let p1, pf, tot;
      if ($('#ss').value === 'price') { p1 = pf = i > 0 ? fin * i / (1 - Math.pow(1 + i, -n)) : fin / n; tot = p1 * n; }
      else { const amort = fin / n; p1 = amort + fin * i; pf = amort + amort * i; tot = amort * n + i * amort * n * (n + 1) / 2; }
      $('#sr').innerHTML = `<div><b>${brl(fin).replace(',00', '')}</b><span>financiado</span></div><div><b>${brl(p1)}</b><span>${$('#ss').value === 'price' ? 'parcela fixa' : '1ª parcela'}</span></div>
        ${$('#ss').value === 'sac' ? `<div><b>${brl(pf)}</b><span>última parcela</span></div>` : ''}<div><b>${brl(p1 / 0.3).replace(',00', '')}</b><span>renda mínima aprox.</span></div><div><b>${brl(tot).replace(',00', '')}</b><span>total pago ao banco</span></div>`;
      if (ent < preco * 0.2) $('#sr').insertAdjacentHTML('beforeend', '<div style="grid-column:1/-1;color:var(--av)"><b>⚠️</b><span>Entrada abaixo de 20% pode não ser aceita.</span></div>');
    };
    $$('#sim input, #sim select').forEach(e => e.oninput = calc); calc();
  }
  const clique = () => api('clique', { loja: LOJA, codigo: COD }, 1);""")
p.write_text(t, encoding="utf-8")

# ── painel: postar no Instagram + taxa de juros na config ──
p = A / "painel.html"; t = p.read_text(encoding="utf-8")
a = """      <div class="linha" style="margin-top:8px"><a class="btn" href="${ARQ(V.url)}" download>⬇️ Baixar vídeo</a>${V.pagina ? `<a class="btn" href="${esc(V.pagina)}" target="_blank">📄 Textos para postar</a>` : ''}</div>` : """
assert a in t, "painel video"
t = t.replace(a, """      <div class="linha" style="margin-top:8px"><a class="btn" href="${ARQ(V.url)}" download>⬇️ Baixar vídeo</a><button class="btn pri" id="ig">📸 Postar no Instagram</button></div>` : """)
a = """  if (V.status === 'gerando' && V.job) acompanha(V.job);
}"""
assert a in t
t = t.replace(a, """  if (V.status === 'gerando' && V.job) acompanha(V.job);
  if ($('#ig', m)) $('#ig', m).onclick = () => { m.fechar(); postarInsta(I, r.pode_postar); };
}
async function postarInsta(I, pode) {
  const m = modal(`<h3>📸 Postar ${esc(I.codigo)} no Instagram</h3><p class="mu pq">A IA escreve a legenda com gancho, destaques, chamada e hashtags da região. Revise antes de postar.</p>
    <textarea id="lg" style="min-height:220px">${esc((I.instagram && I.instagram.legenda) || '')}</textarea><button class="btn pq" id="ia" style="margin-top:6px">✨ ${I.instagram && I.instagram.legenda ? 'Escrever outra' : 'Escrever com IA'}</button>
    <div id="rs" class="pq" style="margin-top:10px"></div>
    <div class="acoes"><button class="btn" data-fechar>Fechar</button><button class="btn" id="cp">📋 Copiar legenda</button><a class="btn" href="${ARQ(I.video.url)}" download>⬇️ Vídeo</a>
      ${pode ? '<button class="btn pri" id="ps">📤 Postar como Reel agora</button>' : ''}</div>`);
  const gera = async () => { $('#ia', m).disabled = true; $('#ia', m).textContent = '⏳ escrevendo…'; const r = await api('insta_legenda', { id: I.id }); $('#ia', m).disabled = false; $('#ia', m).textContent = '✨ Escrever outra';
    if (!r.ok) return aviso(r.erro, true); $('#lg', m).value = r.resultado; api('insta_salvar', { id: I.id, legenda: r.resultado }); };
  $('#ia', m).onclick = gera; if (!$('#lg', m).value) gera();
  $('#cp', m).onclick = () => { navigator.clipboard.writeText($('#lg', m).value); aviso('Legenda copiada'); };
  if ($('#ps', m)) $('#ps', m).onclick = async () => { if (!await confirma('Publicar agora no Instagram conectado?')) return;
    $('#ps', m).disabled = true; $('#ps', m).textContent = '⏳ Enviando o Reel (até 2 min)…';
    const r = await api('insta_postar', { id: I.id, legenda: $('#lg', m).value }); $('#ps', m).disabled = false; $('#ps', m).textContent = '📤 Postar como Reel agora';
    $('#rs', m).innerHTML = r.ok ? `✅ Publicado! ${r.link ? `<a href="${esc(r.link)}" target="_blank">ver no Instagram</a>` : ''}` : `<span style="color:var(--er)">❌ ${esc(r.erro)}</span>`; };
}""")
a = """    <label>Frase de apresentação (aparece no topo do site)</label>"""
assert a in t, "config"
t = t.replace(a, """    <label>Juros do simulador de financiamento (% ao ano)</label><input id="jr" inputmode="decimal" value="${String(c.juros_ano ?? 11.5).replace('.', ',')}">
    <label>Frase de apresentação (aparece no topo do site)</label>""")
t = t.replace("sobre: $('#sb').value, cor: $('#co').value, logo: logo || '' }, 'Salvo')", "sobre: $('#sb').value, cor: $('#co').value, logo: logo || '', juros_ano: numIn($('#jr').value) }, 'Salvo')")
p.write_text(t, encoding="utf-8")

# ── gerador do fluxo: imv_api2 + ramos legenda/postar ──
g = A / "gera.py"; s = g.read_text(encoding="utf-8")
s = s.replace('"SELECT imv_api($1::jsonb) AS r"', '"SELECT imv_api2($1::jsonb) AS r"')
if "insta_legenda" not in s:
    s = s.replace('''    ("video_guardar", "={{ $json.r && $json.r.ia === 'video_guardar' }}"),
], [640, -300])''', '''    ("video_guardar", "={{ $json.r && $json.r.ia === 'video_guardar' }}"),
    ("insta_legenda", "={{ $json.r && $json.r.ia === 'insta_legenda' }}"),
    ("insta_postar", "={{ $json.r && $json.r.ia === 'insta_postar' }}"),
], [640, -300])''')
    s = s.replace("[900, -520]), saida=3)", "[900, -520]), saida=5)")
    s = s.replace('grava(f, AQUI, "imoveis.json")', '''SIS_L = ("Você é social media de imobiliária. Escreva a LEGENDA de um Reel do imóvel, em português do Brasil: 1ª linha = gancho forte (até 70 caracteres, com emoji); "
         "depois 3 a 5 destaques em linhas com emoji; preço; localização (bairro/cidade); chamada para ação (\\"chama no direct\\" ou WhatsApp); CRECI se houver; "
         "no fim 8 a 12 hashtags (tipo de imóvel + bairro + cidade + compra/aluguel). Honesta: só o que está nos dados. Sem markdown, sem aspas. Até 1800 caracteres.")
CL = "$('🐘 imv_api').first().json.r.contexto"
il = ia_http(f, "🤖 IA escreve a legenda", "={{ JSON.stringify({ model: 'antigravity/gemini-3-flash', max_tokens: 1500, temperature: 0.7, messages: [{ role: 'system', content: "
             + __import__('json').dumps(SIS_L, ensure_ascii=False).replace("{", "\\\\u007b").replace("}", "\\\\u007d") + " }, { role: 'user', content: JSON.stringify(Object.assign({}, " + CL + ", { video: undefined, token: undefined, legenda: undefined })) }] }) }}", [900, 60], tempo=90000)
f.liga(sw, il, saida=3)
f.liga(il, f.responde_json("📤 Legenda", "$json.choices && $json.choices[0] ? { ok: true, resultado: String($json.choices[0].message.content || '').trim() } : { ok: false, erro: 'A IA não respondeu agora.' }", [1120, 60]))
rl = f.no("📸 Publica o Reel", "n8n-nodes-instagram-token.instagram", 1, {"resource": "post", "operation": "createReel",
          "reelVideoUrl": "=https://webhookn8n6.inovareinteligenciaartificial.com/videos/arquivo/{{ " + CL + ".video }}", "reelCaption": "={{ " + CL + ".legenda }}"},
          [900, 200], {"instagramAccessTokenApi": {"id": "LWfbyGDT9j3MOBGq", "name": "_lucrocomia_"}}, onError="continueRegularOutput")
gp = postgres(f, "🐘 Guarda o post", "SELECT imv_api2($1::jsonb) AS r",
              "={{ JSON.stringify({ acao: 'insta_salvar', token: " + CL + ".token, id: " + CL + ".id, legenda: " + CL + ".legenda, post: $json.id || '' }) }}", [1120, 200])
f.liga(sw, rl, saida=4)
f.cadeia(rl, gp)
f.liga(gp, f.responde_json("📤 Reel publicado", "$('📸 Publica o Reel').first().json.id ? { ok: true, id: $('📸 Publica o Reel').first().json.id, link: $('📸 Publica o Reel').first().json.permalink || '' } : { ok: false, erro: 'O Instagram recusou: ' + String($('📸 Publica o Reel').first().json.error || 'sem resposta').slice(0, 200) }", [1340, 200]))

grava(f, AQUI, "imoveis.json")''')
g.write_text(s, encoding="utf-8")
print("ok", "insta_postar" in s)
