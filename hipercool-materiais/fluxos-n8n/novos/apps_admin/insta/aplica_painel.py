from pathlib import Path
A = Path(__file__).parent
p = A / "painel.html"; t = p.read_text(encoding="utf-8")

# sorteio: botão anunciar (story + direct aos ganhadores) e status do anúncio
a = """<td style="white-space:nowrap"><a class="btn pq pri" href="${location.origin}/webhook/insta-sorteio?s=${s.codigo}" target="_blank">${s.sorteado_em ? '▶️ Ver / vídeo' : '🎲 Apresentar'}</a> <button class="btn pq fant er" data-x="${s.codigo}">✕</button></td></tr>`"""
assert a in t, "sorteio"
t = t.replace(a, """<td style="white-space:nowrap"><a class="btn pq pri" href="${location.origin}/webhook/insta-sorteio?s=${s.codigo}" target="_blank">${s.sorteado_em ? '▶️ Ver / vídeo' : '🎲 Apresentar'}</a>
        ${s.sorteado_em ? (s.anuncio && s.anuncio.em ? `<a class="btn pq" target="_blank" href="${location.origin}/videos/arquivo/${s.anuncio.arte}">✅ Anunciado</a>` : `<button class="btn pq" data-an="${s.codigo}">📣 Anunciar</button>`) : ''}
        <button class="btn pq fant er" data-x="${s.codigo}">✕</button></td></tr>`""")
a = """  $('#nv').onclick = novoSorteio;
}"""
assert a in t
t = t.replace(a, """  $$('[data-an]').forEach(b => b.onclick = () => anunciar(b.dataset.an));
  $('#nv').onclick = novoSorteio;
}
function anunciar(codigo) {
  const m = modal(`<h3>📣 Anunciar o resultado</h3><p class="mu">O sistema desenha a arte com o(s) ganhador(es) e:</p>
    <label style="display:flex;gap:8px;align-items:center;font-weight:400"><input type="checkbox" id="st" checked style="width:auto;min-height:0"> Posta no seu story</label>
    <label style="display:flex;gap:8px;align-items:center;font-weight:400"><input type="checkbox" id="av" checked style="width:auto;min-height:0"> Avisa o ganhador no direct (quem entrou pelo comentário)</label>
    <div id="rs" style="margin-top:10px"></div><div class="acoes"><button class="btn" data-fechar>Fechar</button><button class="btn pri" id="ok">Anunciar agora</button></div>`);
  $('#ok', m).onclick = async () => { $('#ok', m).disabled = true; $('#ok', m).textContent = '⏳ Desenhando e postando…';
    const r = await api('sorteio_anunciar', { codigo, story: $('#st', m).checked, avisar: $('#av', m).checked }); $('#ok', m).textContent = 'Anunciar agora';
    if (!r.ok) { $('#ok', m).disabled = false; return aviso(r.erro, true); }
    $('#rs', m).innerHTML = `<img src="${r.arte}" style="width:180px;border-radius:12px"><p class="pq">✅ Pronto! ${r.avisados ? r.avisados + ' ganhador(es) avisado(s) no direct.' : ''} <a href="${r.arte}" download>Baixar a arte</a></p>`;
    telaSorteio(); };
}""")

# gincana: botão encerrar e anunciar + mostra resultado final
a = """<button class="btn pq" style="flex:none" data-e="${g.codigo}">✏️ Editar</button></div>"""
assert a in t, "gincana"
t = t.replace(a, """<button class="btn pq" style="flex:none" data-e="${g.codigo}">✏️ Editar</button>
      ${g.ativa ? `<button class="btn pq" style="flex:none" data-fim="${g.codigo}">🏁 Encerrar e anunciar</button>` : g.final && g.final.arte ? `<a class="btn pq" style="flex:none" target="_blank" href="${location.origin}/videos/arquivo/${g.final.arte}">🏆 Arte do pódio</a>` : ''}</div>""")
a = """  $('#nv').onclick = () => editarGincana(null);"""
assert a in t
t = t.replace(a, """  $$('[data-fim]').forEach(b => b.onclick = async () => {
    if (!await confirma('Encerrar agora? O pódio vai para o seu story e cada jogador recebe a colocação no direct.')) return;
    b.disabled = true; b.textContent = '⏳ Encerrando…'; const r = await api('gincana_encerrar', { codigo: b.dataset.fim });
    if (!r.ok) { b.disabled = false; b.textContent = '🏁 Encerrar e anunciar'; return aviso(r.erro, true); }
    aviso(`🏁 Encerrada! ${r.story ? 'Pódio no story. ' : ''}${r.avisados} jogador(es) avisado(s).`); telaGincana(); });
  $('#nv').onclick = () => editarGincana(null);""")
t = t.replace("""<div class="dica">Como funciona: no horário de cada pista""", """<div class="dica">Quando a última pista fecha, a gincana se encerra sozinha: o pódio vai para o story e cada jogador recebe a colocação no direct. Como funciona: no horário de cada pista""")

# menção: erro de envio visível
a = """<td class="pq">${esc(x.mensagem || x.erro)} ${x.enviado ? '' : x.erro ? '<span class="selo">' + esc(x.erro) + '</span>' : ''}</td></tr>`"""
assert a in t, "mencao"
t = t.replace(a, """<td class="pq">${esc(x.mensagem)} ${x.enviado ? '<span class="selo ok">enviado</span>' : x.erro ? '<span class="selo er">⚠️ ' + esc(x.erro) + '</span>' : ''}</td></tr>`""")

# site: compartilhar
a = """<div class="mu pq">Gerado em ${new Date(s.gerado_em).toLocaleString('pt-BR')} · ${s.visitas} visitas · ${s.cliques} cliques no WhatsApp</div></div>"""
assert a in t, "site"
t = t.replace(a, """<div class="mu pq">Gerado em ${new Date(s.gerado_em).toLocaleString('pt-BR')} · ${s.visitas} visitas · ${s.cliques} cliques no WhatsApp</div>
        <div class="linha" style="margin-top:8px"><button class="btn pq" id="cp" style="flex:none">📋 Copiar link</button><a class="btn pq" style="flex:none" target="_blank" href="https://wa.me/?text=${encodeURIComponent('Conheça nosso site: ' + url)}">💬 Mandar no WhatsApp</a>
        <span class="mu pq" style="flex:1">Dica: coloque este link na bio do Instagram.</span></div></div>""")
a = """  $('#sw').onclick = async () =>"""
t = t.replace(a, """  if ($('#cp')) $('#cp').onclick = () => { navigator.clipboard.writeText(url); aviso('Link copiado'); };
  $('#sw').onclick = async () =>""", 1)
p.write_text(t, encoding="utf-8")

# página do sorteio: link de compartilhar a página pública
s = A / "sorteio.html"; u = s.read_text(encoding="utf-8")
a = """<p class="mu pq" style="margin-top:8px">Link público desta página: <a style="color:#f0abfc" href="${location.origin}/webhook/insta-sorteio?s=${esc(COD)}&publico=1">copiar</a></p>"""
assert a in u, "sorteio.html"
u = u.replace(a, """<p class="mu pq" style="margin-top:8px">Mostre esta página aos seguidores para provar que o sorteio foi limpo:</p>
      <button class="btn pq" style="margin-top:6px" onclick="navigator.clipboard.writeText('${location.origin}/webhook/insta-sorteio?s=${esc(COD)}&publico=1');aviso('Link copiado')">📋 Copiar link público</button>""")
s.write_text(u, encoding="utf-8")
print("ok")
