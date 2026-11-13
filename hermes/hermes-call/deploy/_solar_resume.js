// Redispara a campanha "Solar B2B - AGENDADO 9h" (16 números) que ficou toda em
// "queued" e monitora o progresso. Reusa a config original (perfil Solar, voice_pool,
// gaps, abertura). Uso: node _solar_resume.js [--monitor]
const crypto = require('crypto');
const BASE = 'https://hermescall.opus-sem-limites.com.br';
const SECRET = '<SEGREDO_REMOVIDO>';
const USER = '4e8adf4a-6530-47e2-af4c-1c268e6e68d7';
const SID = 'a060fd394e42c828f9c72210f5a1d223';
const PROFILE_ID = 'f07a4b86-1323-4f58-b626-390ec3e36877';

const NUMBERS = [
  '551332523924', '5514998926565', '551935177084', '5519996002434',
  '5519996789200', '5519996274637', '5519999252846', '5521969508333',
  '5524993348016', '553183515964', '553191962796', '553497759166',
  '553533312583', '553584191099', '554187419616', '554192243122',
];

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
    name: `Solar B2B - RETOMADA ${new Date().toISOString().slice(11, 16)}`,
    profile_id: PROFILE_ID,
    numbers: NUMBERS,
    conversational: true,
    convo_max_ms: 600000,
    capture_reply: true,
    concurrency: 1,
    gap_min_ms: 25000,
    gap_max_ms: 50000,
    max_ring_ms: 45000,
    tts_message: 'Alô?... Oi, tudo bem com você?',
    voice_pool: ['cgSgspJ2msm6clMCkdW9', 'XrExE9yKIg1WjnnlVkGX', 'Xb7hH8MSUJpSbSDYk0k2'],
    // respect_schedule OMITIDO de propósito: dispara AGORA (a janela 9-13h já quase
    // fechou; o dono pediu pra continuar e analisar as ligações ao vivo).
  };
  const bc = await api('POST', `/api/sessions/${SID}/broadcast`, req);
  console.log(`[disparo] -> ${bc.status} ${JSON.stringify(bc.body)}`);
  if (bc.body && bc.body.campaignId) {
    console.log(`CAMPAIGN_ID=${bc.body.campaignId}`);
  }
})().catch(e => { console.error('ERRO', e.message); process.exit(1); });
