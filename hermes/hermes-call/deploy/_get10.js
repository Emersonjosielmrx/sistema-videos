const { Client } = require('ssh2');
const c = new Client();
const url = 'postgres://hermes_call_v3test:hermes_call_v3test@localhost:5432/wacalls_main?sslmode=disable';
const q = `SELECT numbers FROM campaigns WHERE id='f6624693-de2e-96f9-82de-7da0383b06ec';`;
c.on('ready', () => {
  c.exec(`psql ${JSON.stringify(url)} -t -A -c ${JSON.stringify(q)} 2>&1`, (e, s) => {
    if (e) { console.error(e.message); c.end(); return; }
    let out = '';
    s.on('data', d => out += d.toString());
    s.on('close', () => {
      try {
        const arr = JSON.parse(out.trim());
        console.log('TOTAL:', arr.length);
        console.log('PRIMEIROS10:', JSON.stringify(arr.slice(0, 10)));
      } catch (err) { console.log('RAW:', out.slice(0, 300)); }
      c.end();
    });
  });
}).connect({ host: '62.171.128.241', username: 'root', password: '<SEGREDO_REMOVIDO>' });
