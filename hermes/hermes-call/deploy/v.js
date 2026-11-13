const { Client } = require('ssh2');
const c = new Client();
c.on('ready', () => {
  c.exec('echo "=== Traefik config ===" && cat /etc/traefik/traefik.yml 2>&1 | head -30 && echo "=== arquivos estáticos ===" && ls /etc/traefik/ 2>&1 && echo "=== dynamic configs ===" && ls /etc/traefik/dynamic/ 2>&1 && cat /etc/traefik/dynamic/*.yml 2>&1 | head -60', (err, stream) => {
    if (err) { console.error(err); return; }
    stream.on('data', d => process.stdout.write(d.toString()));
    stream.stderr.on('data', d => process.stdout.write(d.toString()));
    stream.on('close', () => c.end());
  });
});
c.on('error', e => console.error('SSH error:', e.message));
c.connect({ host: '62.171.128.241', port: 22, username: 'root', password: '<SEGREDO_REMOVIDO>', readyTimeout: 30000 });
