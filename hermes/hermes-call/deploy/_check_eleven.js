const { Client } = require('ssh2');
const c = new Client();
const url = 'postgres://hermes_call_v3test:hermes_call_v3test@localhost:5432/wacalls_main?sslmode=disable';
const q = `SELECT provider, type, name, left(api_key,6)||'...'||right(api_key,4) AS key_preview, created_at FROM credentials WHERE lower(provider)='elevenlabs' ORDER BY created_at;`;
c.on('ready', () => {
  c.exec(`psql ${JSON.stringify(url)} -c ${JSON.stringify(q)} 2>&1`, (e, s) => {
    if (e) { console.error(e.message); c.end(); return; }
    s.on('data', d => process.stdout.write(d.toString()));
    s.on('close', () => c.end());
  });
}).connect({ host: '62.171.128.241', username: 'root', password: '<SEGREDO_REMOVIDO>' });
