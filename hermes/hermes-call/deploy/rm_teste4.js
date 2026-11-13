const { Client } = require('ssh2');
const c = new Client();
c.on('ready', () => {
  c.exec('echo "=== Mount info do traefik ===" && docker inspect traefik --format "{{json .Mounts}}" 2>&1 | head -30 && echo "=== Procura /etc/traefik no host ===" && find / -name "dynamic" -type d 2>/dev/null | head -5 && echo "=== /opt/traefik ===" && ls -la /opt/traefik/ 2>&1 && echo "=== /srv/traefik ===" && ls -la /srv/traefik/ 2>&1 && echo "=== docker volumes ===" && docker volume ls 2>&1', (err, stream) => {
    if (err) { console.error(err); return; }
    stream.on('data', d => process.stdout.write(d.toString()));
    stream.stderr.on('data', d => process.stdout.write(d.toString()));
    stream.on('close', () => c.end());
  });
});
c.on('error', e => console.error('SSH error:', e.message));
c.connect({ host: '62.171.128.241', port: 22, username: 'root', password: '<SEGREDO_REMOVIDO>', readyTimeout: 30000 });
