// Roda o código de um nó Code do n8n fora do n8n, com dados de exemplo no lugar de $('nó').
// Uso: node roda_local.js <codigo.js> <dados.json> [saida.json]
const fs = require('fs');
const [codigo, dadosArq, saida] = process.argv.slice(2);
const dados = JSON.parse(fs.readFileSync(dadosArq, 'utf8'));
const $ = nome => {
  if (!(nome in dados)) throw new Error('sem dados para o nó ' + nome);
  const lista = Array.isArray(dados[nome]) ? dados[nome] : [dados[nome]];
  return { first: () => ({ json: lista[0] }), all: () => lista.map(j => ({ json: j })), item: { json: lista[0] } };
};
const $input = { first: () => ({ json: dados.$input || {} }), all: () => (Array.isArray(dados.$input) ? dados.$input : [dados.$input || {}]).map(j => ({ json: j })) };
const fn = new Function('$', '$input', 'require', fs.readFileSync(codigo, 'utf8'));
const r = fn($, $input, require);
const txt = JSON.stringify(r, null, 2);
if (saida) fs.writeFileSync(saida, txt); else console.log(txt);
