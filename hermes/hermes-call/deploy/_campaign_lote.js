// Dispara um LOTE da campanha Solar B2B com rotação de vozes premade + anti-bloqueio.
const crypto = require('crypto');
const BASE = 'https://hermescall.opus-sem-limites.com.br';
const SECRET = '<SEGREDO_REMOVIDO>';
const USER = '4e8adf4a-6530-47e2-af4c-1c268e6e68d7';
const SID = 'a060fd394e42c828f9c72210f5a1d223';
const PROFILE = 'f07a4b86-1323-4f58-b626-390ec3e36877'; // Solar B2B

const NUMS = ["5511942259820","5511944552748","5511999777600","551332523924","5514998926565","5515996419161","551630423850","5517991156336","5518996296679","551935177084"];
// Rotação de vozes premade (Jessica, Matilda, Alice) — as que funcionam em conta free.
const VOICE_POOL = ["cgSgspJ2msm6clMCkdW9", "XrExE9yKIg1WjnnlVkGX", "Xb7hH8MSUJpSbSDYk0k2"];

const b = s => Buffer.from(s).toString('base64').replace(/=/g, '').replace(/\+/g, '-').replace(/\//g, '_');
function jwt() {
  const n = Math.floor(Date.now() / 1e3);
  const h = b(JSON.stringify({ alg: 'HS256', typ: 'JWT' }));
  const p = b(JSON.stringify({ sub: USER, iat: n, exp: n + 3600 }));
  const s = b(crypto.createHmac('sha256', SECRET).update(h + '.' + p).digest());
  return `${h}.${p}.${s}`;
}

(async () => {
  const req = {
    name: 'Solar B2B - LOTE TESTE 10 (rotação vozes)',
    profile_id: PROFILE,
    tts_message: 'Oi, tudo bem?',            // gatilho de saudação (não apresentação)
    conversational: true,
    convo_max_ms: 600000,                     // 10min teto (desliga com 1min silêncio)
    capture_reply: true,
    voice_pool: VOICE_POOL,                   // rotação de vozes por ligação
    numbers: NUMS,
    concurrency: 1,                           // 1 por vez (anti-ban)
    gap_min_ms: 20000, gap_max_ms: 45000,     // gap aleatório 20-45s entre ligações
  };
  const r = await fetch(`${BASE}/api/sessions/${SID}/broadcast`, {
    method: 'POST',
    headers: { Authorization: 'Bearer ' + jwt(), 'Content-Type': 'application/json' },
    body: JSON.stringify(req),
  });
  console.log('status:', r.status);
  console.log(await r.text());
})().catch(e => { console.error('ERRO', e.message); process.exit(1); });
