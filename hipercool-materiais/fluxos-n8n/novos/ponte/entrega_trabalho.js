// Devolve ao PC o próximo pedido da fila (ou "vazio") e prepara o status "o PC pegou".
const tirado = $input.first().json.pedido;
const maquina = $('🧩 Confere o PC').first().json.maquina;
if (!tirado) return [{ json: { vazio: true, resposta: JSON.stringify({ vazio: true }) } }];
let p = {};
try { p = typeof tirado === 'string' ? JSON.parse(tirado) : tirado; } catch (e) { return [{ json: { vazio: true, resposta: '{"vazio":true}' } }]; }
return [{ json: { vazio: false, id: p.id, resposta: JSON.stringify(p),
  status: JSON.stringify({ id: p.id, acao: p.acao, etapa: 'no_pc', maquina, pegou: new Date().toISOString(), criado: p.criado, origem: p.origem }) } }];
