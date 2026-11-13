const { Client } = require('ssh2');
const c = new Client();
const url = 'postgres://hermes_call_v3test:hermes_call_v3test@localhost:5432/wacalls_main?sslmode=disable';
// Pega a campanha Solar B2B com mais números (o lote de 59).
const q = `SELECT id, name, total, jsonb_array_length(numbers) AS n_nums FROM campaigns WHERE name ILIKE '%Solar B2B%' ORDER BY total DESC LIMIT 5;`;
c.on('ready', () => {
  c.exec(`psql ${JSON.stringify(url)} -c ${JSON.stringify(q)} 2>&1`, (e, s) => {
    if (e) { console.error(e.message); c.end(); return; }
    s.on('data', d => process.stdout.write(d.toString()));
    s.on('close', () => c.end());
  });
}).connect({ host: '62.171.128.241', username: 'root', password: '<SEGREDO_REMOVIDO>' });
