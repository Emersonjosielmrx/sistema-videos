const { Client } = require('ssh2');
const c = new Client();
c.on('ready', () => {
  c.exec('echo "=== com caracteres visiveis ===" && cat -A /opt/traefik-config/dynamic/hermes.yml && echo "=== md5 ===" && md5sum /opt/traefik-config/dynamic/hermes.yml && echo "=== stat ===" && stat /opt/traefik-config/dynamic/hermes.yml && echo "=== acesso fs ===" && ls -la /opt/traefik-config/dynamic/ && echo "=== Testa yaml parse ===" && python3 -c "import yaml; print(yaml.safe_load(open(\'/opt/traefik-config/dynamic/hermes.yml\')))" 2>&1 || echo "no python3" && echo "=== debug traefik file provider ===" && docker exec traefik ls -la /etc/traefik/dynamic/ && echo "=== inside container cat ===" && docker exec traefik cat -A /etc/traefik/dynamic/hermes.yml', (err, stream) => {
    if (err) { console.error(err); return; }
    stream.on('data', d => process.stdout.write(d.toString()));
    stream.stderr.on('data', d => process.stdout.write(d.toString()));
    stream.on('close', () => c.end());
  });
});
c.on('error', e => console.error('SSH error:', e.message'));
c.connect({ host: '62.171.128.241', port: 22, username: 'root', password: '<SEGREDO_REMOVIDO>', readyTimeout: 30000 });
