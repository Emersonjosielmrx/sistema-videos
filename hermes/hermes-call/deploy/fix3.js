const { Client } = require('ssh2');
const fs = require('fs');

// Regra importante: yaml usa aspas duplas, e o backtick (`) é literal no yaml.
// Vou usar arquivo com conteúdo simples
const newYML = `http:
  routers:
    hermes-teste-disabled:
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

fs.writeFileSync('/tmp/hermes-teste-new.yml', newYML);
console.log('newYML written, length=' + newYML.length);

const c = new Client();
c.on('ready', () => {
  // Use sftp to put the file
  c.sftp((err, sftp) => {
    if (err) { console.error(err); return; }
    sftp.fastPut('/tmp/hermes-teste-new.yml', '/tmp/hermes-teste-new.yml', (err) => {
      if (err) { console.error(err); return; }
      sftp.end();
      // Run shell commands
      c.exec('mv /opt/traefik-config/dynamic/hermes-teste.yml /tmp/hermes-teste-broken.yml && cp /tmp/hermes-teste-new.yml /opt/traefik-config/dynamic/hermes-teste.yml && cat /opt/traefik-config/dynamic/hermes-teste.yml && echo "=== Restart traefik ===" && docker restart traefik 2>&1 && echo "=== Aguarda 5s ===" && sleep 5 && echo "=== Testa ===" && curl -s -o /dev/null -w "teste HTTP %{http_code}\n" --connect-timeout 10 http://hermescallteste.opus-sem-limites.com.br/ 2>&1 && curl -s -o /dev/null -w "prod HTTP %{http_code}\n" --connect-timeout 10 https://hermescall.opus-sem-limites.com.br/ 2>&1', (err, stream) => {
        if (err) { console.error(err); return; }
        stream.on('data', d => process.stdout.write(d.toString()));
        stream.stderr.on('data', d => process.stdout.write(d.toString()));
        stream.on('close', () => c.end());
      });
    });
  });
});
c.on('error', e => console.error('SSH error:', e.message));
c.connect({ host: '62.171.128.241', port: 22, username: 'root', password: '<SEGREDO_REMOVIDO>', readyTimeout: 30000 });
