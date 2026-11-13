// Continua a campanha Solar: dispara os números que FALTAM (nunca discados) da lista
// completa "energia solar 0807". O backend respeita o limite diário anti-ban da linha
// (para sozinho ao bater o teto do dia) e o horário comercial. O resto continua depois.
//   node _solar_continuar.js            -> dispara a lista inteira que falta
//   node _solar_continuar.js 50         -> só os primeiros 50 (teste de ritmo)
const crypto = require('crypto');
const fs = require('fs');
const BASE = 'https://hermescall.opus-sem-limites.com.br';
const SECRET = '<SEGREDO_REMOVIDO>';
const USER = '4e8adf4a-6530-47e2-af4c-1c268e6e68d7';
const SID = 'a060fd394e42c828f9c72210f5a1d223';
const PROFILE_ID = 'f07a4b86-1323-4f58-b626-390ec3e36877'; // Solar B2B

let numbers = JSON.parse(fs.readFileSync(__dirname + '/_solar_faltam.json', 'utf8'));
const limit = parseInt(process.argv[2] || '0', 10);
if (limit > 0) numbers = numbers.slice(0, limit);

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
    name: `Solar B2B - LISTA COMPLETA ${new Date().toISOString().slice(0, 10)}`,
    profile_id: PROFILE_ID,
    numbers,
    conversational: true,
    convo_max_ms: 600000,
    capture_reply: true,
    concurrency: 1,
    gap_min_ms: 25000,      // gap anti-ban (25-50s entre ligações)
    gap_max_ms: 50000,
    max_ring_ms: 45000,
    tts_message: 'Alô?... Oi, tudo bem com você?',
    voice_pool: ['cgSgspJ2msm6clMCkdW9', 'XrExE9yKIg1WjnnlVkGX', 'Xb7hH8MSUJpSbSDYk0k2'],
    respect_schedule: false, // 13h47 sábado já passou da janela 9-13h; desligado pra
                             // dialar AGORA (senão pularia tudo). Anti-ban diário ainda vale.
    smart_order: true,       // liga primeiro pra quem tem mais chance de atender
  };
  console.log(`Disparando ${numbers.length} números (backend para no teto diário anti-ban)...`);
  const bc = await api('POST', `/api/sessions/${SID}/broadcast`, req);
  console.log(`[disparo] -> ${bc.status} ${JSON.stringify(bc.body)}`);
  if (bc.body && bc.body.campaignId) console.log(`CAMPAIGN_ID=${bc.body.campaignId}`);
})().catch(e => { console.error('ERRO', e.message); process.exit(1); });
