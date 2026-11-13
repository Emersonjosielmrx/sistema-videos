// Ligação de teste parametrizada: ajusta o som ambiente do perfil Solar B2B e
// dispara UMA ligação conversacional pro número de teste.
//   node _test_call.js <ambient> <fraseGatilho>
//   ambient: call_center | office | coffee_shop | none
const crypto = require('crypto');
const BASE = 'https://hermescall.opus-sem-limites.com.br';
const SECRET = '<SEGREDO_REMOVIDO>';
const USER = '4e8adf4a-6530-47e2-af4c-1c268e6e68d7';
const SID = 'a060fd394e42c828f9c72210f5a1d223';
const PROFILE_ID = 'f07a4b86-1323-4f58-b626-390ec3e36877'; // Solar B2B
const TEST_NUMBER = '5591985685106';

const ambient = process.argv[2] || 'call_center';
const phrase = process.argv[3] || '';

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
  // 1. Pega o perfil Solar B2B inteiro.
  const profs = await api('GET', '/api/agent-profiles');
  const prof = (profs.body.profiles || []).find(p => p.id === PROFILE_ID);
  if (!prof) { console.error('perfil nao encontrado'); process.exit(1); }

  // 2. Ajusta o som ambiente (reenvia o perfil inteiro; Create é upsert por nome).
  prof.background_noise = ambient === 'none' ? '' : ambient;
  prof.background_noise_volume = ambient === 'none' ? 0 : 0.15;
  const up = await api('POST', '/api/agent-profiles', prof);
  console.log(`[perfil] ambient=${ambient} vol=${prof.background_noise_volume} -> ${up.status} ${JSON.stringify(up.body)}`);

  // 3. Dispara a ligação conversacional pro número de teste.
  const req = {
    name: `TESTE ${ambient} ${new Date().toISOString().slice(11, 19)}`,
    profile_id: PROFILE_ID,
    conversational: true,
    convo_max_ms: 600000, // 10min: teto de duração (desliga antes com 1min de silêncio)
    capture_reply: true,
    numbers: [TEST_NUMBER],
    concurrency: 1,
  };
  if (phrase) req.tts_message = phrase; // frase de gatilho de abertura (se informada)

  const bc = await api('POST', `/api/sessions/${SID}/broadcast`, req);
  console.log(`[ligacao] -> ${bc.status} ${JSON.stringify(bc.body)}`);
  if (bc.body && bc.body.campaignId) {
    console.log(`\nCAMPAIGN_ID=${bc.body.campaignId}`);
    console.log(`(acompanhe: GET /api/sessions/${SID}/broadcast/${bc.body.campaignId})`);
  }
})().catch(e => { console.error('ERRO', e.message); process.exit(1); });
