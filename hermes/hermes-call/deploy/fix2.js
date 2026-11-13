const { Client } = require('ssh2');
const c = new Client();
c.on('ready', () => {
  // Texto com aspas simples escapadas
  const newYML = `http:
  routers:
    hermes-teste-disabled:
      rule: "Host(\\x60hermescallteste.opus-sem-limites.com.br\\x60)"
      service: hermes-teste-svc
      entryPoints:
        - web
        - websecure
      tls:
        certResolver: le
  services:
    hermes-teste-svc:
      loadBalancer:
        servers:
          - url: "http://127.0.0.1:9999/"
`;
  // Use base64 para evitar problemas de escape
  const buf = Buffer.from(newYML, 'utf-8');
  const b64 = buf.toString('base64');
  c.exec('mv /opt/traefik-config/dynamic/hermes-teste.yml /tmp/hermes-teste-broken.yml && echo backup-ok && echo ' + b64 + ' | base64 -d > /opt/traefik-config/dynamic/hermes-teste.yml && echo write-ok && echo "=== Conteúdo ===" && cat /opt/traefik-config/dynamic/hermes-teste.yml && echo "=== Restart traefik ===" && docker restart traefik 2>&1 && echo "=== Aguarda 5s ===" && sleep 5 && echo "=== Traefik logs ===" && docker logs --tail 10 traefik 2>&1 | head -15 && echo "=== Testa ===" && curl -s -o /dev/null -w "teste HTTP %{http_code}\n" --connect-timeout 10 http://hermescallteste.opus-sem-limites.com.br/ 2>&1 && curl -s -o /dev/null -w "prod HTTP %{http_code}\n" --connect-timeout 10 https://hermescall.opus-sem-limites.com.br/ 2>&1', (err, stream) => {
    if (err) { console.error(err); return; }
    stream.on('data', d => process.stdout.write(d.toString()));
    stream.stderr.on('data', d => process.stdout.write(d.toString()));
    stream.on('close', () => c.end());
  });
});
c.on('error', e => console.error('SSH error:', e.message));
c.connect({ host: '62.171.128.241', port: 22, username: 'root', password: '<SEGREDO_REMOVIDO>', readyTimeout: 30000 });
