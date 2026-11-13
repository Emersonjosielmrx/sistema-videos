const { Client } = require('ssh2');
const c = new Client();
c.on('ready', () => {
  c.exec('echo "=== Traefik logs ===" && docker logs --tail 30 traefik 2>&1 | head -30 && echo "=== hermes.yml ===" && cat /opt/traefik-config/dynamic/hermes.yml && echo "=== hermes-teste.yml ===" && cat /opt/traefik-config/dynamic/hermes-teste.yml && echo "=== VALIDA yaml ===" && docker exec traefik sh -c "cat /etc/traefik/dynamic/hermes.yml"', (err, stream) => {
    if (err) { console.error(err); return; }
    stream.on('data', d => process.stdout.write(d.toString()));
    stream.stderr.on('data', d => process.stdout.write(d.toString()));
    stream.on('close', () => c.end());
  });
});
c.on('error', e => console.error('SSH error:', e.message));
c.connect({ host: '62.171.128.241', port: 22, username: 'root', password: '<SEGREDO_REMOVIDO>', readyTimeout: 30000 });
