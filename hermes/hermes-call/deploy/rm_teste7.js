const { Client } = require('ssh2');
const c = new Client();
c.on('ready', () => {
  // ssh2 não suporta heredoc rico. Vou usar um truque: 
  // - gerar arquivo via printf com escape
  const newConfig = `http:\n  routers:\n    hermes-teste:\n      rule: "Host(\\\`hermescallteste.opus-sem-limites.com.br\\\`)"\n      service: hermes-teste-svc\n      entryPoints:\n        - web\n      tls:\n        certResolver: le\n  services:\n    hermes-teste-svc:\n      loadBalancer:\n        servers:\n          - url: "http://127.0.0.1:9999/"\n`;
  c.exec(`cp /opt/traefik-config/dynamic/hermes-teste.yml /tmp/hermes-teste-original.yml && echo backup-ok && printf '${newConfig}' > /opt/traefik-config/dynamic/hermes-teste.yml && echo write-ok && cat /opt/traefik-config/dynamic/hermes-teste.yml && echo --- && docker restart traefik 2>&1 && echo --- && sleep 5 && curl -s -o /dev/null -w "teste: HTTP %{http_code}\n" --connect-timeout 10 http://hermescallteste.opus-sem-limites.com.br/ 2>&1 && curl -s -o /dev/null -w "prod: HTTP %{http_code}\n" --connect-timeout 10 https://hermescall.opus-sem-limites.com.br/ 2>&1`, (err, stream) => {
    if (err) { console.error(err); return; }
    stream.on('data', d => process.stdout.write(d.toString()));
    stream.stderr.on('data', d => process.stdout.write(d.toString()));
    stream.on('close', () => c.end());
  });
});
c.on('error', e => console.error('SSH error:', e.message));
c.connect({ host: '62.171.128.241', port: 22, username: 'root', password: '<SEGREDO_REMOVIDO>', readyTimeout: 30000 });
