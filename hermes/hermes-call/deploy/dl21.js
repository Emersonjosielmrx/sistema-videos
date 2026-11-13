const { Client } = require('ssh2');
const c = new Client();
c.on('ready', () => {
  c.exec('echo "=== docker compose stat ===" && cd /opt && ls && cat docker-compose.yml 2>/dev/null | head -50 || echo "no compose" && echo "=== Procura compose ===" && find / -name "docker-compose*.yml" -type f 2>/dev/null | head -10 && echo "=== inspect traefik antigo ===" && docker inspect traefik --format "{{json .HostConfig.NetworkMode}}" 2>/dev/null || echo "removido" && echo "=== Rodando containers ===" && docker ps --format "{{.Names}}\t{{.Image}}\t{{.Ports}}"', (err, stream) => {
    if (err) { console.error(err); return; }
    stream.on('data', d => process.stdout.write(d.toString()));
    stream.stderr.on('data', d => process.stdout.write(d.toString()));
    stream.on('close', () => c.end());
  });
});
c.on('error', e => console.error('SSH error:', e.message));
c.connect({ host: '62.171.128.241', port: 22, username: 'root', password: '<SEGREDO_REMOVIDO>', readyTimeout: 30000 });
