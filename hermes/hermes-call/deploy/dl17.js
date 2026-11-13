const { Client } = require('ssh2');
const c = new Client();
c.on('ready', () => {
  c.exec('echo "=== Tudo no /opt/traefik-config ===" && find /opt/traefik-config -type f -ls 2>&1 && echo "=== Inspect container traefik mount ===" && docker inspect traefik --format "{{json .Mounts}}" | head -100 && echo "=== docker inspect entryPoints ===" && docker exec traefik cat /etc/traefik/traefik.yml && echo "=== docker exec dynamic ls ===" && docker exec traefik ls -la /etc/traefik/dynamic/', (err, stream) => {
    if (err) { console.error(err); return; }
    stream.on('data', d => process.stdout.write(d.toString()));
    stream.stderr.on('data', d => process.stdout.write(d.toString()));
    stream.on('close', () => c.end());
  });
});
c.on('error', e => console.error('SSH error:', e.message));
c.connect({ host: '62.171.128.241', port: 22, username: 'root', password: '<SEGREDO_REMOVIDO>', readyTimeout: 30000 });
