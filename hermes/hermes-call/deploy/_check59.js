// Verifica quais dos 59 números da campanha Solar B2B têm WhatsApp ativo (SEM discar).
const crypto = require('crypto');
const { Client } = require('ssh2');
const BASE = 'https://hermescall.opus-sem-limites.com.br';
const SECRET = '<SEGREDO_REMOVIDO>';
const USER = '4e8adf4a-6530-47e2-af4c-1c268e6e68d7';
const SID = 'a060fd394e42c828f9c72210f5a1d223';
const URL = 'postgres://hermes_call_v3test:hermes_call_v3test@localhost:5432/wacalls_main?sslmode=disable';

function b(s) { return Buffer.from(s).toString('base64').replace(/=/g, '').replace(/\+/g, '-').replace(/\//g, '_'); }
function jwt() {
  const n = Math.floor(Date.now() / 1e3);
  const h = b(JSON.stringify({ alg: 'HS256', typ: 'JWT' }));
  const p = b(JSON.stringify({ sub: USER, iat: n, exp: n + 3600 }));
  const sig = b(crypto.createHmac('sha256', SECRET).update(h + '.' + p).digest());
  return h + '.' + p + '.' + sig;
}

const SQL = "SELECT numbers FROM campaigns WHERE id='f6624693-de2e-96f9-82de-7da0383b06ec';";
const c = new Client();
c.on('ready', function () {
  const cmd = 'psql ' + JSON.stringify(URL) + ' -t -A -c ' + JSON.stringify(SQL);
  c.exec(cmd, function (e, s) {
    if (e) { console.error(e.message); c.end(); return; }
    let out = '';
    s.on('data', function (d) { out += d.toString(); });
    s.on('close', async function () {
      c.end();
      const nums = JSON.parse(out.trim());
      const alive = [], dead = [];
      for (const n of nums) {
        try {
          const r = await fetch(BASE + '/api/sessions/' + SID + '/contacts/check?phone=' + n, { headers: { Authorization: 'Bearer ' + jwt() } });
          const j = await r.json();
          if (j.numberExists || j.exists) alive.push(n); else dead.push(n);
        } catch (err) { dead.push(n); }
        await new Promise(function (x) { setTimeout(x, 250); });
      }
      console.log('TOTAL:', nums.length, '| VIVOS:', alive.length, '| MORTOS:', dead.length);
      console.log('VIVOS:', JSON.stringify(alive));
    });
  });
}).connect({ host: '62.171.128.241', username: 'root', password: '<SEGREDO_REMOVIDO>' });
