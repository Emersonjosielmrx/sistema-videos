const { Client } = require('ssh2');
const c = new Client();
c.on('ready', () => {
  c.exec('sleep 5 && echo "=== API routers ===" && curl -s http://127.0.0.1:8082/api/http/routers 2>&1 && echo "" && echo "=== API services ===" && curl -s http://127.0.0.1:8082/api/http/services 2>&1 && echo "" && echo "=== Full logs ===" && docker logs --tail 100 traefik 2>&1 | head -60', (err, stream) => {
    if (err) { console.error(err); return; }
    stream.on('data', d => process.stdout.write(d.toString()));
    stream.stderr.on('data', d => process.stdout.write(d.toString()));
    stream.on('close', () => c.end());
  });
});
c.on('error', e => console.error('SSH error:', e.message'));
c.connect({ host: '62.171.128.241', port: 22, username: 'root', password: '<SEGREDO_REMOVIDO>', readyTimeout: 30000 });
