const { Client } = require('ssh2');
const c = new Client();
c.on('ready', () => {
  c.exec('docker kill traefik && sleep 2 && docker rm traefik && sleep 1 && docker run -d --name traefik --restart=always --network host -v /opt/traefik-config/traefik.yml:/etc/traefik/traefik.yml:ro -v /opt/traefik-config/dynamic:/etc/traefik/dynamic:ro -v /opt/traefik-config/letsencrypt:/letsencrypt -v /var/run/docker.sock:/var/run/docker.sock:ro traefik:v2.10 --api --api.insecure --api.dashboard --log.level=DEBUG --accesslog=true --accesslog.filepath=/tmp/access.log 2>&1 && sleep 12 && echo "=== API routers ===" && curl -s http://127.0.0.1:8080/api/http/routers && echo "" && echo "=== API services ===" && curl -s http://127.0.0.1:8080/api/http/services && echo "" && echo "=== Curl com headers ===" && curl -sv -H "Host: hermescall.opus-sem-limites.com.br" http://127.0.0.1/ 2>&1 | head -10 && echo "=== Acess log ===" && cat /tmp/access.log 2>&1 | head -10', (err, stream) => {
    if (err) { console.error(err); return; }
    stream.on('data', d => process.stdout.write(d.toString()));
    stream.stderr.on('data', d => process.stdout.write(d.toString()));
    stream.on('close', () => c.end());
  });
});
c.on('error', e => console.error('SSH error:', e.message));
c.connect({ host: '62.171.128.241', port: 22, username: 'root', password: '<SEGREDO_REMOVIDO>', readyTimeout: 60000 });
