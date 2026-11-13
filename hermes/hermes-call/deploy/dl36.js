const { Client } = require('ssh2');
const c = new Client();
c.on('ready', () => {
  c.exec('echo "=== Restart traefik com DEBUG ===" && docker kill traefik && sleep 2 && docker rm traefik && sleep 1 && docker run -d --name traefik --restart=always --network host -v /opt/traefik-config/traefik.yml:/etc/traefik/traefik.yml:ro -v /opt/traefik-config/dynamic:/etc/traefik/dynamic:ro -v /opt/traefik-config/letsencrypt:/letsencrypt -v /var/run/docker.sock:/var/run/docker.sock:ro traefik:v2.10 --log.level=DEBUG --accesslog=true --accesslog.filepath=/tmp/access.log 2>&1 && sleep 10 && echo "=== debug logs ===" && docker logs traefik 2>&1 | grep -iE "router|service|rule|load|host|hermes" | head -30 && echo "=== access log ===" && docker exec traefik cat /tmp/access.log 2>&1 | head -10 && echo "=== curl foo ===" && curl -s -o /dev/null -w "code=%{http_code}\n" -H "Host: foo.bar" http://127.0.0.1/ && echo "=== access log final ===" && docker exec traefik cat /tmp/access.log 2>&1 | head -10', (err, stream) => {
    if (err) { console.error(err); return; }
    stream.on('data', d => process.stdout.write(d.toString()));
    stream.stderr.on('data', d => process.stdout.write(d.toString()));
    stream.on('close', () => c.end());
  });
});
c.on('error', e => console.error('SSH error:', e.message));
c.connect({ host: '62.171.128.241', port: 22, username: 'root', password: '<SEGREDO_REMOVIDO>', readyTimeout: 60000 });
