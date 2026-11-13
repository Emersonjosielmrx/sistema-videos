const { Client } = require('ssh2');
const c = new Client();
c.on('ready', () => {
  c.exec('echo "=== root traefik.yml ===" && cat /opt/traefik-config/traefik.yml && echo "=== docker exec path ===" && docker exec traefik cat /etc/traefik/traefik.yml && echo "=== file dynamic watch? ===" && docker exec traefik ls -la /etc/traefik/dynamic/ && echo "=== debug providers ===" && docker exec traefik wget -qO- http://127.0.0.1:8082/api/overview 2>&1 | head -200 || echo "8082 not exposed"', (err, stream) => {
    if (err) { console.error(err); return; }
    stream.on('data', d => process.stdout.write(d.toString()));
    stream.stderr.on('data', d => process.stdout.write(d.toString()));
    stream.on('close', () => c.end());
  });
});
c.on('error', e => console.error('SSH error:', e.message));
c.connect({ host: '62.171.128.241', port: 22, username: 'root', password: '<SEGREDO_REMOVIDO>', readyTimeout: 30000 });
