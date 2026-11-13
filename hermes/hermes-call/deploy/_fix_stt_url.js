// Corrige stt_base_url removendo o /v1 duplicado (fix imediato sem rebuild).
const { Client } = require('ssh2');
const c = new Client();
const url = 'postgres://hermes_call_v3test:hermes_call_v3test@localhost:5432/wacalls_main?sslmode=disable';

// jsonb_set com o novo valor. Aspas simples da string JSON escapadas pro SQL.
const upd = `UPDATE settings SET value = jsonb_set(value, '{stt_base_url}', '"https://api.groq.com/openai"') WHERE key='voice';`;
const sel = `SELECT value->>'stt_base_url' AS burl FROM settings WHERE key='voice';`;

function psql(sql) {
  return `psql ${JSON.stringify(url)} -c ${JSON.stringify(sql)} 2>&1`;
}

c.on('ready', () => {
  c.exec(`${psql(upd)}; ${psql(sel)}`, (e, s) => {
    if (e) { console.error(e.message); c.end(); return; }
    s.on('data', d => process.stdout.write(d.toString()));
    s.stderr.on('data', d => process.stderr.write(d.toString()));
    s.on('close', () => c.end());
  });
}).connect({ host: '62.171.128.241', username: 'root', password: '<SEGREDO_REMOVIDO>' });
