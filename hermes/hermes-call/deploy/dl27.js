const { Client } = require('ssh2');
const c = new Client();
c.on('ready', () => {
  c.exec('echo "=== Host inexistente ===" && curl -s -o /dev/null -w "code=%{http_code}\n" -H "Host: foo.bar.baz" http://127.0.0.1/ && echo "=== Host vazio ===" && curl -s -o /dev/null -w "code=%{http_code}\n" -H "Host: " http://127.0.0.1/ && echo "=== sem Host ===" && curl -s -o /dev/null -w "code=%{http_code}\n" http://127.0.0.1/ && echo "=== teste host prod ===" && curl -s -o /dev/null -w "code=%{http_code}\n" -H "Host: hermescall.opus-sem-limites.com.br" http://127.0.0.1/ && echo "=== teste host teste ===" && curl -s -o /dev/null -w "code=%{http_code}\n" -H "Host: hermescallteste.opus-sem-limites.com.br" http://127.0.0.1/', (err, stream) => {
    if (err) { console.error(err); return; }
    stream.on('data', d => process.stdout.write(d.toString()));
    stream.stderr.on('data', d => process.stdout.write(d.toString()));
    stream.on('close', () => c.end());
  });
});
c.on('error', e => console.error('SSH error:', e.message));
c.connect({ host: '62.171.128.241', port: 22, username: 'root', password: '<SEGREDO_REMOVIDO>', readyTimeout: 30000 });
