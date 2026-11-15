from pathlib import Path
A = Path(__file__).parent
p = A / "painel.html"; t = p.read_text(encoding="utf-8")

# função de impressão em cupom 80 mm (janela própria, imprime e fecha)
a = "// ═════════ MESAS ═════════"
assert a in t
t = t.replace(a, """// ═════════ IMPRESSÃO (cupom 80 mm, qualquer impressora térmica ou comum) ═════════
function imprimir(titulo, linhas) {
  const w = window.open('', '_blank', 'width=380,height=640'); if (!w) return aviso('Libere os pop-ups para imprimir.', true);
  w.document.write(`<!DOCTYPE html><html><head><meta charset="utf-8"><title>${esc(titulo)}</title><style>@page{size:80mm auto;margin:3mm}body{font-family:ui-monospace,Consolas,monospace;font-size:13px;width:72mm;margin:0;color:#000}
    h1{font-size:17px;text-align:center;margin:0 0 4px}.c{text-align:center}.g{font-size:16px;font-weight:700}.l{display:flex;justify-content:space-between;gap:6px}.o{font-weight:700;padding-left:10px}hr{border:0;border-top:1px dashed #000;margin:6px 0}</style></head>
    <body>${linhas}<hr><div class="c">${new Date().toLocaleString('pt-BR')}</div><script>window.onload=()=>{window.print();setTimeout(()=>window.close(),400)}<\\/script></body></html>`);
  w.document.close();
}
function imprimirConta(mesa, c) {
  imprimir('Conta mesa ' + mesa, `<h1>${esc(EU.loja.nome)}</h1><div class="c">CONFERÊNCIA · MESA ${mesa}</div><hr>
    ${c.itens.filter(i => i.status !== 'cancelado').map(i => `<div class="l"><span>${i.qtd}x ${esc(i.nome)}</span><span>${brl(i.qtd * i.preco_unit)}</span></div>${i.adicionais.length ? `<div>&nbsp;+ ${i.adicionais.map(esc).join(', ')}</div>` : ''}`).join('')}
    <hr><div class="l"><span>Subtotal</span><span>${brl(c.subtotal)}</span></div><div class="l"><span>Serviço ${Number(c.servico_pct)}%</span><span>${brl(c.subtotal * c.servico_pct / 100)}</span></div>
    ${Number(c.desconto) ? `<div class="l"><span>Desconto</span><span>-${brl(c.desconto)}</span></div>` : ''}<div class="l g"><span>TOTAL</span><span>${brl(c.total)}</span></div>
    ${c.pessoas > 1 ? `<div class="l"><span>Por pessoa (${c.pessoas})</span><span>${brl(c.total / c.pessoas)}</span></div>` : ''}<hr><div class="c">Não é documento fiscal</div>`);
}
function imprimirPedido(itens) {
  const porMesa = {}; itens.forEach(i => (porMesa[i.mesa] = porMesa[i.mesa] || []).push(i));
  imprimir('Pedido cozinha', Object.entries(porMesa).map(([m, l]) => `<h1>MESA ${m}</h1>${l.map(i => `<div class="g">${i.qtd}x ${esc(i.nome)}</div>${i.adicionais.length ? `<div>+ ${i.adicionais.map(esc).join(', ')}</div>` : ''}${i.obs ? `<div class="o">>> ${esc(i.obs)}</div>` : ''}`).join('')}<hr>`).join(''));
}

// ═════════ MESAS ═════════""")

# botão imprimir conta na comanda
a = """      ${c ? `<button class="btn" data-mais>⋯ Mais</button>` : ''}"""
assert a in t
t = t.replace(a, """      ${c ? `<button class="btn" data-mais>⋯ Mais</button><button class="btn" data-imp>🖨️ Conta</button>` : ''}""")
a = """    $('[data-mais]', m).onclick = () => { m.fechar(); maisComanda(mesa, c); };"""
assert a in t
t = t.replace(a, a + """\n    $('[data-imp]', m).onclick = () => imprimirConta(mesa, c);""")

# cozinha: imprimir os novos + impressão automática opcional
a = """      <select id="dst" style="width:auto">"""
assert a in t
t = t.replace(a, """      <label style="display:flex;gap:6px;align-items:center;font-weight:400;margin:0;font-size:14px"><input type="checkbox" id="autoimp" style="width:auto;min-height:0" ${guarda.ler('cmd_autoimp') ? 'checked' : ''}> imprimir sozinho</label>
      <button class="btn" id="impn">🖨️ Imprimir novos</button><select id="dst" style="width:auto">""")
a = """    $('#dst').onchange = e => { destino = e.target.value; guarda.gravar('cmd_destino', destino); desenha(); };"""
assert a in t
t = t.replace(a, a + """
    const novosIt = j.itens.filter(i => i.status === 'novo');
    $('#impn').onclick = () => novosIt.length ? imprimirPedido(novosIt) : aviso('Nenhum pedido novo.');
    $('#autoimp').onchange = e => guarda.gravar('cmd_autoimp', e.target.checked ? '1' : null);
    const jaImpressos = new Set(JSON.parse(guarda.ler('cmd_impressos') || '[]'));
    const faltam = novosIt.filter(i => !jaImpressos.has(i.id));
    if ($('#autoimp').checked && faltam.length) { imprimirPedido(faltam); faltam.forEach(i => jaImpressos.add(i.id)); guarda.gravar('cmd_impressos', JSON.stringify([...jaImpressos].slice(-300))); }""")
p.write_text(t, encoding="utf-8")
print("ok")
