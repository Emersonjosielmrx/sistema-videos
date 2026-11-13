const { Client } = require('ssh2');
const c = new Client();
c.on('ready', () => {
  c.exec('echo "=== Recriar traefik ===" && docker run -d --name traefik --restart=always --network host -v /opt/traefik-config/traefik.yml:/etc/traefik/traefik.yml:ro -v /opt/traefik-config/dynamic:/etc/traefik/dynamic:ro -v /opt/traefik-config/letsencrypt:/letsencrypt -v /var/run/docker.sock:/var/run/docker.sock:ro traefik:v2.10 2>&1 && echo "=== status ===" && docker ps --format "{{.Names}}\t{{.Status}}\t{{.Image}}" && echo "=== sleep 8s ===" && sleep 8 && echo "=== curl teste host ===" && curl -sv -H "Host: hermescallteste.opus-sem-limites.com.br" http://127.0.0.1/ 2>&1 | head -15 && echo "=== curl prod host ===" && curl -sv -H "Host: hermescall.opus-sem-limites.com.br" http://127.0.0.1/ 2>&1 | head -15 && echo "=== curl prod real ===" && curl -sv https://hermescall.opus-sem-limites.com.br/ 2>&1 | head -15 && echo "=== curl teste real ===" && curl -sv https://hermescallteste.opus-sem-limites.com.br/ 2>&1 | head -15', (err, stream) => {
    if (err) { console.error(err); return; }
    stream.on('data', d => process.stdout.write(d.toString()));
    stream.stderr.on('data', d => process.stdout.write(d.toString()));
    stream.on('close', () => c.end());
  });
});
c.on('error', e => console.error('SSH error:', e.message));
c.connect({ host: '62.171.128.241', port: 22, username: 'root', password: '<SEGREDO_REMOVIDO>', readyTimeout: 45000 });
