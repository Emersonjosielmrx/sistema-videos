const { Client } = require('ssh2');
const c = new Client();
c.on('ready', () => {
  c.exec('echo "=== https foo ===" && curl -sk -o /dev/null -w "code=%{http_code}\n" -H "Host: foo.bar" https://127.0.0.1/ && echo "=== https hermescallteste ===" && curl -sk -o /dev/null -w "code=%{http_code}\n" -H "Host: hermescallteste.opus-sem-limites.com.br" https://127.0.0.1/ && echo "=== https hermescall ===" && curl -sk -o /dev/null -w "code=%{http_code}\n" -H "Host: hermescall.opus-sem-limites.com.br" https://127.0.0.1/ && echo "=== api hermescall ===" && curl -sk -H "Host: hermescall.opus-sem-limites.com.br" https://127.0.0.1/api/version && echo "" && echo "=== api hermescallteste ===" && curl -sk -H "Host: hermescallteste.opus-sem-limites.com.br" https://127.0.0.1/api/version && echo ""', (err, stream) => {
    if (err) { console.error(err); return; }
    stream.on('data', d => process.stdout.write(d.toString()));
    stream.stderr.on('data', d => process.stdout.write(d.toString()));
    stream.on('close', () => c.end());
  });
});
c.on('error', e => console.error('SSH error:', e.message));
c.connect({ host: '62.171.128.241', port: 22, username: 'root', password: '<SEGREDO_REMOVIDO>', readyTimeout: 30000 });
