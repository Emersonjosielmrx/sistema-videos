const { Client } = require('ssh2');
const fs = require('fs');
const c = new Client();
c.on('ready', () => {
  // Backup
  c.exec('cp /opt/traefik-config/dynamic/hermes-teste.yml /tmp/hermes-teste-original.yml', (err, stream) => {
    if (err) { console.error(err); return; }
    stream.on('data', d => process.stdout.write(d.toString()));
    stream.stderr.on('data', d => process.stdout.write(d.toString()));
    stream.on('close', () => {
      // Write new config locally, then copy to traefik
      const newConfig = `http:
  routers:
    hermes-teste:
      rule: "Host(\`hermescallteste.opus-sem-limites.com.br\`)"
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
      fs.writeFileSync('/tmp/hermes-teste-new.yml', newConfig);
      c2 = new Client();
      c2.on('ready', () => {
        c2.exec('cp /tmp/hermes-teste-new.yml /opt/traefik-config/dynamic/hermes-teste.yml && echo OK && cat /opt/traefik-config/dynamic/hermes-teste.yml && echo "=== Restart traefik ===" && docker restart traefik 2>&1 && echo "=== Aguarda 5s ===" && sleep 5 && echo "=== Testa rotas ===" && curl -s -o /dev/null -w "teste: HTTP %{http_code}\n" --connect-timeout 10 http://hermescallteste.opus-sem-limites.com.br/ 2>&1 && curl -s -o /dev/null -w "prod: HTTP %{http_code}\n" --connect-timeout 10 https://hermescall.opus-sem-limites.com.br/ 2>&1', (err, stream) => {
          if (err) { console.error(err); return; }
          stream.on('data', d => process.stdout.write(d.toString()));
          stream.stderr.on('data', d => process.stdout.write(d.toString()));
          stream.on('close', () => c2.end());
        });
      });
      c2.on('error', e => console.error('SSH error:', e.message));
      c2.connect({ host: '62.171.128.241', port: 22, username: 'root', password: '<SEGREDO_REMOVIDO>', readyTimeout: 30000 });
    });
  });
});
c.on('error', e => console.error('SSH error:', e.message));
c.connect({ host: '62.171.128.241', port: 22, username: 'root', password: '<SEGREDO_REMOVIDO>', readyTimeout: 30000 });
