// Ativa TTS=elevenlabs com voz feminina brasileira realista + modelo Flash.
// A chave (APIKey) fica vazia de propósito: o rotador inteligente injeta as chaves
// (mais-crédito primeiro) em runtime. voice = voice_id da biblioteca ElevenLabs.
const { Client } = require('ssh2');
const c = new Client();
const url = 'postgres://hermes_call_v3test:hermes_call_v3test@localhost:5432/wacalls_main?sslmode=disable';

const voiceId = process.argv[2] || 'BKv4Uz2HPF6TFlDgFBKN'; // Marianne - Customer service (3443 usos)
// tts_api_key vazio → rotador assume. tts_provider=elevenlabs, voz + reset ambient continuo.
const upd = `UPDATE settings SET value = value || '{"tts_provider":"elevenlabs","tts_voice":"${voiceId}","tts_api_key":"","tts_base_url":""}'::jsonb WHERE key='voice';`;
const sel = `SELECT value->>'tts_provider' AS prov, value->>'tts_voice' AS voice, value->>'ambient_mode' AS amb, value->>'stt_base_url' AS stt FROM settings WHERE key='voice';`;

function psql(sql) { return `psql ${JSON.stringify(url)} -c ${JSON.stringify(sql)} 2>&1`; }

c.on('ready', () => {
  c.exec(`${psql(upd)}; ${psql(sel)}`, (e, s) => {
    if (e) { console.error(e.message); c.end(); return; }
    s.on('data', d => process.stdout.write(d.toString()));
    s.stderr.on('data', d => process.stderr.write(d.toString()));
    s.on('close', () => c.end());
  });
}).connect({ host: '62.171.128.241', username: 'root', password: '<SEGREDO_REMOVIDO>' });
