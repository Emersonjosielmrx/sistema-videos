// Troca o TTS pra edge-tts / voz FEMININA (Francisca), coerente com a persona.
const { Client } = require('ssh2');
const c = new Client();
const url = 'postgres://hermes_call_v3test:hermes_call_v3test@localhost:5432/wacalls_main?sslmode=disable';

// SQL em UMA linha (multi-linha quebrava o psql -c).
const upd = `UPDATE settings SET value = value || '{"tts_provider":"edge-tts","tts_voice":"pt-BR-FranciscaNeural"}'::jsonb WHERE key='voice';`;
const sel = `SELECT value->>'tts_provider' AS prov, value->>'tts_voice' AS voice FROM settings WHERE key='voice';`;

function psql(sql) { return `psql ${JSON.stringify(url)} -c ${JSON.stringify(sql)} 2>&1`; }

c.on('ready', () => {
  c.exec(`${psql(upd)}; ${psql(sel)}`, (e, s) => {
    if (e) { console.error(e.message); c.end(); return; }
    s.on('data', d => process.stdout.write(d.toString()));
    s.stderr.on('data', d => process.stderr.write(d.toString()));
    s.on('close', () => c.end());
  });
}).connect({ host: '62.171.128.241', username: 'root', password: '<SEGREDO_REMOVIDO>' });
