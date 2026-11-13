const { Client } = require('ssh2');
const c = new Client();
c.on('ready', () => {
  c.exec('sleep 5 && echo "=== teste foo ===" && curl -s -o /dev/null -w "code=%{http_code}\n" -H "Host: foo.baz" http://127.0.0.1/ && echo "=== teste prod ===" && curl -s -o /dev/null -w "code=%{http_code}\n" -H "Host: hermescall.opus-sem-limites.com.br" http://127.0.0.1/ && echo "=== teste teste ===" && curl -s -o /dev/null -w "code=%{http_code}\n" -H "Host: hermescallteste.opus-sem-limites.com.br" http://127.0.0.1/ && echo "=== Logs ===" && docker logs --tail 30 traefik 2>&1 | tail -20', (err, stream) => {
    if (err) { console.error(err); return; }
    stream.on('data', d => process.stdout.write(d.toString()));
    stream.stderr.on('data', d => process.stdout.write(d.toString()));
    stream.on('close', () => c.end());
  });
});
c.on('error', e => console.error('SSH error:', e.message));
c.connect({ host: '62.171.128.241', port: 22, username: 'root', password: '<SEGREDO_REMOVIDO>', readyTimeout: 60000 });
