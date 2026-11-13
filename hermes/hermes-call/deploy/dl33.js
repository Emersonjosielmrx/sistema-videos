const { Client } = require('ssh2');
const c = new Client();
c.on('ready', () => {
  c.exec('echo "=== Lancar debug traefik ===" && curl -sv -H "Host: hermescall.opus-sem-limites.com.br" http://127.0.0.1/ 2>&1 | head -25 && echo "===" && echo "=== Direto 8080 bypassando traefik ===" && curl -s -H "Host: hermescall.opus-sem-limites.com.br" http://127.0.0.1:8080/ | head -20 && echo "=== debug traefik api direto ===" && curl -s http://127.0.0.1:8080/api/rawdata 2>&1 | head -50', (err, stream) => {
    if (err) { console.error(err); return; }
    stream.on('data', d => process.stdout.write(d.toString()));
    stream.stderr.on('data', d => process.stdout.write(d.toString()));
    stream.on('close', () => c.end());
  });
});
c.on('error', e => console.error('SSH error:', e.message));
c.connect({ host: '62.171.128.241', port: 22, username: 'root', password: '<SEGREDO_REMOVIDO>', readyTimeout: 30000 });
