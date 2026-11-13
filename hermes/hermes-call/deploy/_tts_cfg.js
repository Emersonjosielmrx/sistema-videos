const { Client } = require('ssh2');
const c = new Client();
const url = 'postgres://hermes_call_v3test:hermes_call_v3test@localhost:5432/wacalls_main?sslmode=disable';
const q = `SELECT value->>'tts_provider' AS prov, value->>'tts_voice' AS voice, value->>'tts_base_url' AS burl, value->>'tts_credential_id' AS cred FROM settings WHERE key='voice';`;
c.on('ready', () => {
  c.exec(`psql ${JSON.stringify(url)} -c ${JSON.stringify(q)} 2>&1`, (e, s) => {
    if (e) { console.error(e.message); c.end(); return; }
    s.on('data', d => process.stdout.write(d.toString()));
    s.on('close', () => c.end());
  });
}).connect({ host: '62.171.128.241', username: 'root', password: '<SEGREDO_REMOVIDO>' });
