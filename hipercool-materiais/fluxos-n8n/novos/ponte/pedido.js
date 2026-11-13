// Recebe um pedido para o PC (de outro fluxo ou da página). Só ações conhecidas; exige o token da ponte.
const TOKEN = __TOKEN__;
const ACOES = __ACOES__;
const ent = $input.first().json;
const b = ent.body || {};
const h = ent.headers || {};
const base = (h['x-forwarded-proto'] || 'https') + '://' + (h['x-forwarded-host'] || h.host);
if (String(h['x-ponte-token'] || b.token || '') !== TOKEN) return [{ json: { ok: false, codigo: 401, erro: 'token da ponte errado' } }];
const acao = String(b.acao || '');
if (!ACOES[acao]) return [{ json: { ok: false, codigo: 400, erro: 'ação desconhecida: ' + acao + ' (use: ' + Object.keys(ACOES).join(', ') + ')' } }];
const id = (Date.now().toString(36) + Math.random().toString(36).slice(2, 6)).toLowerCase();
const pedido = { id, acao, dados: b.dados || {}, origem: String(b.origem || 'página').slice(0, 60), criado: new Date().toISOString() };
const status = { id, acao, descricao: ACOES[acao], etapa: 'na_fila', criado: pedido.criado, origem: pedido.origem };
return [{ json: { ok: true, id, pedido: JSON.stringify(pedido), status: JSON.stringify(status),
  status_url: base + '/webhook/ponte-pc/status?id=' + id } }];
