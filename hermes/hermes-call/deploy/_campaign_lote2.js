// Dispara 20 números (dos 59, pulando os 10 já discados) — todos com WhatsApp confirmado.
// Rotação de vozes premade + cadência 20-45s (anti-ban).
const crypto = require('crypto');
const BASE = 'https://hermescall.opus-sem-limites.com.br';
const SECRET = '<SEGREDO_REMOVIDO>';
const USER = '4e8adf4a-6530-47e2-af4c-1c268e6e68d7';
const SID = 'a060fd394e42c828f9c72210f5a1d223';
const PROFILE = 'f07a4b86-1323-4f58-b626-390ec3e36877';

// 59 vivos; os 10 primeiros já foram no lote 1 → pega os próximos 20.
const TODOS = ["5511942259820","5511944552748","5511999777600","551332523924","5514998926565","5515996419161","551630423850","5517991156336","5518996296679","551935177084","5519996002434","5519996274637","5519996789200","5519999252846","5521969508333","5524993348016","553183515964","553191962796","553497759166","553498127886","553533312583","553584191099","554187419616","554187926976","554192243122","554192399923","554330170909","554484570923","554491012089","554491434800"];
const NUMS = TODOS.slice(10, 30); // próximos 20
const VOICE_POOL = ["cgSgspJ2msm6clMCkdW9", "XrExE9yKIg1WjnnlVkGX", "Xb7hH8MSUJpSbSDYk0k2"];

function b(s) { return Buffer.from(s).toString('base64').replace(/=/g, '').replace(/\+/g, '-').replace(/\//g, '_'); }
function jwt() {
  const n = Math.floor(Date.now() / 1e3);
  const h = b(JSON.stringify({ alg: 'HS256', typ: 'JWT' }));
  const p = b(JSON.stringify({ sub: USER, iat: n, exp: n + 3600 }));
  const sig = b(crypto.createHmac('sha256', SECRET).update(h + '.' + p).digest());
  return h + '.' + p + '.' + sig;
}

(async () => {
  const req = {
    name: 'Solar B2B - LOTE 2 (20 verificados)',
    profile_id: PROFILE,
    tts_message: 'Oi, tudo bem?',
    conversational: true,
    convo_max_ms: 600000,
    capture_reply: true,
    voice_pool: VOICE_POOL,
    numbers: NUMS,
    concurrency: 1,
    gap_min_ms: 20000, gap_max_ms: 45000,
  };
  const r = await fetch(`${BASE}/api/sessions/${SID}/broadcast`, {
    method: 'POST',
    headers: { Authorization: 'Bearer ' + jwt(), 'Content-Type': 'application/json' },
    body: JSON.stringify(req),
  });
  console.log('status:', r.status, '| numeros:', NUMS.length);
  console.log(await r.text());
})().catch(e => { console.error('ERRO', e.message); process.exit(1); });
