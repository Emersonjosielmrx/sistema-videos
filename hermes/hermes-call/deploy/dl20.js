const { Client } = require('ssh2');
const c = new Client();
c.on('ready', () => {
  c.exec('echo "=== acme.json ===" && cat /opt/traefik-config/letsencrypt/acme.json | head -200 && echo "=== stop traefik ===" && docker stop traefik && echo "=== drop traefik fully ===" && docker rm -f traefik && echo "=== rodando? ===" && docker ps -a | grep traefik', (err, stream) => {
    if (err) { console.error(err); return; }
    stream.on('data', d => process.stdout.write(d.toString()));
    stream.stderr.on('data', d => process.stdout.write(d.toString()));
    stream.on('close', () => c.end());
  });
});
c.on('error', e => console.error('SSH error:', e.message));
c.connect({ host: '62.171.128.241', port: 22, username: 'root', password: '<SEGREDO_REMOVIDO>', readyTimeout: 30000 });
