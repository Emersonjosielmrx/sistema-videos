// Liga uma vez pro número 5519996789200 (lead fresco que falhou com 463 antes).
const crypto = require('crypto');
const BASE = 'https://hermescall.opus-sem-limites.com.br';
const SECRET = '<SEGREDO_REMOVIDO>';
const USER = '4e8adf4a-6530-47e2-af4c-1c268e6e68d7';
const SID = 'e56b7eae32f4484cab2a0f6088713eeb';
const PROFILE_ID = 'f07a4b86-1323-4f58-b626-390ec3e36877'; // Solar B2B
const TEST_NUMBER = process.argv[2] || '5519996789200';

const b = s => Buffer.from(s).toString('base64').replace(/=/g, '').replace(/\+/g, '-').replace(/\//g, '_');
function jwt() {
  const n = Math.floor(Date.now() / 1e3);
  const h = b(JSON.stringify({ alg: 'HS256', typ: 'JWT' }));
  const p = b(JSON.stringify({ sub: USER, iat: n, exp: n + 3600 }));
  const s = b(crypto.createHmac('sha256', SECRET).update(h + '.' + p).digest());
  return `${h}.${p}.${s}`;
}
async function api(method, path, body) {
  const r = await fetch(BASE + path, {
    method,
    headers: { Authorization: 'Bearer ' + jwt(), 'Content-Type': 'application/json' },
    body: body ? JSON.stringify(body) : undefined,
  });
  const t = await r.text();
  let j; try { j = JSON.parse(t); } catch { j = t; }
  return { status: r.status, body: j };
}

(async () => {
  const req = {
    name: `TESTE LID FALLBACK ${new Date().toISOString().slice(11, 19)}`,
    profile_id: PROFILE_ID,
    tts_message: 'Oi, tudo bem? Aqui é a Hipercool.',
    conversational: true,
    convo_max_ms: 60000,
    capture_reply: false,
    numbers: [TEST_NUMBER],
    concurrency: 1,
  };
  const bc = await api('POST', `/api/sessions/${SID}/broadcast`, req);
  console.log(`[ligacao ${TEST_NUMBER}] -> ${bc.status} ${JSON.stringify(bc.body)}`);
})().catch(e => { console.error('ERRO', e.message); process.exit(1); });
