const { Client } = require('ssh2');
const c = new Client();
c.on('ready', () => {
  c.exec('echo "=== Traefik logs ===" && docker logs --tail 80 traefik 2>&1 | tail -50 && echo "=== Traefik api routers ===" && docker exec traefik wget -qO- http://127.0.0.1:8082/api/http/routers 2>&1 || echo "8082 n\u00e3o up" && echo "=== Traefik api services ===" && docker exec traefik wget -qO- http://127.0.0.1:8082/api/http/services 2>&1 || echo "no api"', (err, stream) => {
    if (err) { console.error(err); return; }
    stream.on('data', d => process.stdout.write(d.toString()));
    stream.stderr.on('data', d => process.stdout.write(d.toString()));
    stream.on('close', () => c.end());
  });
});
c.on('error', e => console.error('SSH error:', e.message));
c.connect({ host: '62.171.128.241', port: 22, username: 'root', password: '<SEGREDO_REMOVIDO>', readyTimeout: 30000 });
