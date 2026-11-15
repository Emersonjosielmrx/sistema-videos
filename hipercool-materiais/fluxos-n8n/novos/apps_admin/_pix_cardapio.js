const v = $('Validar pedido').first().json;
const cfg = JSON.parse($('Lê config privada').first().json.cfg);
const menu = JSON.parse($('Lê cardápio do pedido').first().json.menu);
const numero = Number(Object.values($input.first().json)[0]) || 1;
const p = { numero, ...v.pedido };
const brl = x => 'R$ ' + Number(x).toFixed(2).replace('.', ',');

// Pix copia e cola (BR Code do Banco Central), gerado aqui mesmo, sem API
function emv(id, valor) { const s = String(valor); return id + String(s.length).padStart(2, '0') + s; }
function crc16(str) {
  let crc = 0xFFFF;
  for (let i = 0; i < str.length; i++) {
    crc ^= str.charCodeAt(i) << 8;
    for (let j = 0; j < 8; j++) { crc = (crc & 0x8000) ? ((crc << 1) ^ 0x1021) : (crc << 1); crc &= 0xFFFF; }
  }
  return crc.toString(16).toUpperCase().padStart(4, '0');
}
function pixCopiaECola({ chave, nome, cidade, valor, txid }) {
  const ascii = s => String(s || '').normalize('NFD').replace(/[̀-ͯ]/g, '').replace(/[^A-Za-z0-9 ]/g, '').trim().toUpperCase();
  let s = emv('00', '01') + emv('26', emv('00', 'br.gov.bcb.pix') + emv('01', chave)) + emv('52', '0000') + emv('53', '986');
  if (valor > 0) s += emv('54', valor.toFixed(2));
  s += emv('58', 'BR') + emv('59', ascii(nome).slice(0, 25) || 'LOJA') + emv('60', ascii(cidade).slice(0, 15) || 'BRASIL');
  s += emv('62', emv('05', String(txid).replace(/[^A-Za-z0-9]/g, '').slice(0, 25) || '***')) + '6304';
  return s + crc16(s);
}
const pix = p.pagamento === 'pix' && cfg.pix.ativo
  ? pixCopiaECola({ chave: cfg.pix.chave, nome: cfg.pix.nome, cidade: cfg.pix.cidade, valor: p.total, txid: `PED${numero}` })
  : '';

const PAG = { pix: 'Pix (copia e cola gerado)', cartao: 'Cartão', dinheiro: 'Dinheiro' };
const msg = [
  `🛒 *Pedido #${numero}* · ${menu.loja.nome}`,
  `👤 ${p.nome}`,
  '──────────',
  ...p.linhas.map(l => `${l.qtd}x ${l.nome} · ${brl(l.total)}`),
  '──────────',
  `Subtotal: ${brl(p.subtotal)}`,
  p.tipo === 'entrega' ? `Entrega: ${p.taxa > 0 ? brl(p.taxa) : 'grátis'}` : null,
  `*Total: ${brl(p.total)}*`,
  p.tipo === 'entrega' ? `🛵 Entregar em: ${p.endereco}` : '🏃 Vou retirar no local',
  `💳 Pagamento: ${PAG[p.pagamento]}${p.troco ? ` · troco para ${brl(p.troco)}` : ''}`,
  p.obs ? `📝 Obs: ${p.obs}` : null,
].filter(Boolean).join('\n');

return [{ json: {
  resposta: { ok: true, numero, total_fmt: brl(p.total), pix, whatsapp_url: `https://wa.me/${cfg.whatsapp}?text=${encodeURIComponent(msg)}` },
  pedido_str: JSON.stringify({ ...p, pix: !!pix }),
} }];