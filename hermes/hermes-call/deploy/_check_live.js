// Checa estado ao vivo via API: sessão conectada, perfis de agente, whatsapp/status.
const crypto = require('crypto');
const BASE = 'https://hermescall.opus-sem-limites.com.br';
const SECRET = '<SEGREDO_REMOVIDO>';
const USER = '4e8adf4a-6530-47e2-af4c-1c268e6e68d7';

function b64url(buf) { return Buffer.from(buf).toString('base64').replace(/=/g, '').replace(/\+/g, '-').replace(/\//g, '_'); }
function jwt() {
  const now = Math.floor(Date.now() / 1000);
  const h = b64url(JSON.stringify({ alg: 'HS256', typ: 'JWT' }));
  const p = b64url(JSON.stringify({ sub: USER, iat: now, exp: now + 3600 }));
  const s = b64url(crypto.createHmac('sha256', SECRET).update(h + '.' + p).digest());
  return `${h}.${p}.${s}`;
}

async function get(path) {
  const r = await fetch(BASE + path, { headers: { Authorization: 'Bearer ' + jwt() } });
  const t = await r.text();
  console.log(`\n### GET ${path} → ${r.status}`);
  try { console.log(JSON.stringify(JSON.parse(t), null, 2)); } catch { console.log(t.slice(0, 800)); }
}

(async () => {
  await get('/api/version');
  await get('/api/whatsapp/status');   // endpoint novo
  await get('/api/sessions');
  await get('/api/agent-profiles');
})().catch(e => { console.error('ERRO', e.message); process.exit(1); });
