// O PC devolve o resultado: guarda o arquivo (se houver, até ~15 MB) e o status final com o link.
const TOKEN = __TOKEN__;
const ent = $input.first().json;
const b = ent.body || {};
const h = ent.headers || {};
const base = (h['x-forwarded-proto'] || 'https') + '://' + (h['x-forwarded-host'] || h.host);
if (String(h['x-ponte-token'] || b.token || '') !== TOKEN) return [{ json: { ok: false, codigo: 401, erro: 'token da ponte errado' } }];
const id = String(b.id || '').toLowerCase().replace(/[^a-z0-9]/g, '');
if (!id) return [{ json: { ok: false, codigo: 400, erro: 'sem id' } }];
let nome = '';
let b64 = '';
if (b.arquivo_b64) {
  const ext = String(b.extensao || 'bin').toLowerCase().replace(/[^a-z0-9]/g, '').slice(0, 5) || 'bin';
  nome = id + '-resultado.' + ext;
  b64 = String(b.arquivo_b64);
  if (b64.length > 21e6) return [{ json: { ok: false, codigo: 413, erro: 'arquivo grande demais para a ponte (máx. ~15 MB)' } }];
}
const status = { id, acao: String(b.acao || ''), etapa: b.ok ? 'pronto' : 'erro', maquina: String(b.maquina || ''),
  terminou: new Date().toISOString(), mensagem: String(b.mensagem || '').slice(0, 1000), dados: b.dados || {},
  arquivo: nome ? base + '/webhook/ponte-pc/arquivo?id=' + nome : null };
return [{ json: { ok: true, id, nome, b64, tem_arquivo: !!nome, status: JSON.stringify(status) } }];
