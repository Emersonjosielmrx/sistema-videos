const { Client } = require('ssh2');
const c = new Client();
c.on('ready', () => {
  c.exec('echo "=== Portas abertas ===" && ss -tlnp | grep -E "(80|443|8082|8080)" && echo "=== Docker networks ===" && docker network ls && echo "=== Inspect rede ===" && docker inspect hermes-call --format "{{json .NetworkSettings.Networks}}" 2>&1 | head -50 && echo "=== Traefik logs recentes ===" && docker logs --tail 50 traefik 2>&1 | tail -30', (err, stream) => {
    if (err) { console.error(err); return; }
    stream.on('data', d => process.stdout.write(d.toString()));
    stream.stderr.on('data', d => process.stdout.write(d.toString()));
    stream.on('close', () => c.end());
  });
});
c.on('error', e => console.error('SSH error:', e.message));
c.connect({ host: '62.171.128.241', port: 22, username: 'root', password: '<SEGREDO_REMOVIDO>', readyTimeout: 30000 });
