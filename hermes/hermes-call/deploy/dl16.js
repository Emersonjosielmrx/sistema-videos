const { Client } = require('ssh2');
const c = new Client();
c.on('ready', () => {
  c.exec('echo "=== curl teste HTTP ===" && curl -sv -H "Host: hermescallteste.opus-sem-limites.com.br" http://127.0.0.1/ 2>&1 | head -20 && echo "=== curl prod HTTP ===" && curl -sv -H "Host: hermescall.opus-sem-limites.com.br" http://127.0.0.1/ 2>&1 | head -10 && echo "=== curl teste HTTPS ===" && curl -sk -v --resolve hermescallteste.opus-sem-limites.com.br:443:127.0.0.1 https://hermescallteste.opus-sem-limites.com.br/ 2>&1 | head -30', (err, stream) => {
    if (err) { console.error(err); return; }
    stream.on('data', d => process.stdout.write(d.toString()));
    stream.stderr.on('data', d => process.stdout.write(d.toString()));
    stream.on('close', () => c.end());
  });
});
c.on('error', e => console.error('SSH error:', e.message));
c.connect({ host: '62.171.128.241', port: 22, username: 'root', password: '<SEGREDO_REMOVIDO>', readyTimeout: 30000 });
