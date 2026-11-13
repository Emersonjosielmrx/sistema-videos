const { Client } = require('ssh2');
const c = new Client();
c.on('ready', () => {
  c.exec('echo "=== HTTPS REAL prod ===" && curl -s -o /dev/null -w "code=%{http_code}\n" https://hermescall.opus-sem-limites.com.br/ && echo "=== HTTPS REAL teste ===" && curl -s -o /dev/null -w "code=%{http_code}\n" https://hermescallteste.opus-sem-limites.com.br/ && echo "=== HTTP REAL prod (redirect) ===" && curl -sv -o /dev/null -w "code=%{http_code}\n" http://hermescall.opus-sem-limites.com.br/ 2>&1 | head -10 && echo "=== HTTP REAL teste ===" && curl -s -o /dev/null -w "code=%{http_code}\n" http://hermescallteste.opus-sem-limites.com.br/', (err, stream) => {
    if (err) { console.error(err); return; }
    stream.on('data', d => process.stdout.write(d.toString()));
    stream.stderr.on('data', d => process.stdout.write(d.toString()));
    stream.on('close', () => c.end());
  });
});
c.on('error', e => console.error('SSH error:', e.message));
c.connect({ host: '62.171.128.241', port: 22, username: 'root', password: '<SEGREDO_REMOVIDO>', readyTimeout: 30000 });
