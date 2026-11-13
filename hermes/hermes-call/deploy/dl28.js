const { Client } = require('ssh2');
const c = new Client();
c.on('ready', () => {
  c.exec('echo "=== hermes.yml no host ===" && cat /opt/traefik-config/dynamic/hermes.yml && echo "=== hermes.yml no container ===" && docker exec traefik cat /etc/traefik/dynamic/hermes.yml && echo "=== arquivos dynamic ===" && docker exec traefik ls -la /etc/traefik/dynamic/ && echo "=== RestartFull docker ===" && docker kill traefik && sleep 2 && docker rm traefik && sleep 1 && docker run -d --name traefik --restart=always --network host -v /opt/traefik-config/traefik.yml:/etc/traefik/traefik.yml:ro -v /opt/traefik-config/dynamic:/etc/traefik/dynamic:ro -v /opt/traefik-config/letsencrypt:/letsencrypt -v /var/run/docker.sock:/var/run/docker.sock:ro traefik:v2.10 && sleep 8 && echo "=== teste ===" && curl -s -o /dev/null -w "code=%{http_code}\n" -H "Host: foo.baz" http://127.0.0.1/ && curl -s -o /dev/null -w "code=%{http_code}\n" -H "Host: hermescall.opus-sem-limites.com.br" http://127.0.0.1/', (err, stream) => {
    if (err) { console.error(err); return; }
    stream.on('data', d => process.stdout.write(d.toString()));
    stream.stderr.on('data', d => process.stdout.write(d.toString()));
    stream.on('close', () => c.end());
  });
});
c.on('error', e => console.error('SSH error:', e.message));
c.connect({ host: '62.171.128.241', port: 22, username: 'root', password: '<SEGREDO_REMOVIDO>', readyTimeout: 60000 });
