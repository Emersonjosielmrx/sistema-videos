const { Client } = require('ssh2');
const c = new Client();
c.on('ready', () => {
  c.exec('echo "=== Backup do teste.yml ===" && cp /opt/traefik-config/dynamic/hermes-teste.yml /tmp/hermes-teste-original.yml && echo "=== DELETA o teste.yml ===" && rm /opt/traefik-config/dynamic/hermes-teste.yml && echo "=== Confirma que sumiu ===" && ls /opt/traefik-config/dynamic/ && echo "=== Restart traefik ===" && docker restart traefik 2>&1 && echo "=== Aguarda 5s ===" && sleep 5 && echo "=== Testa rotas ===" && curl -s -o /dev/null -w "teste: HTTP %{http_code}\n" --connect-timeout 10 http://hermescallteste.opus-sem-limites.com.br/ 2>&1 && curl -s -o /dev/null -w "teste-https: HTTP %{http_code}\n" --connect-timeout 10 https://hermescallteste.opus-sem-limites.com.br/ 2>&1 && curl -s -o /dev/null -w "prod: HTTP %{http_code}\n" --connect-timeout 10 https://hermescall.opus-sem-limites.com.br/ 2>&1 && curl -s https://hermescall.opus-sem-limites.com.br/api/version 2>&1', (err, stream) => {
    if (err) { console.error(err); return; }
    stream.on('data', d => process.stdout.write(d.toString()));
    stream.stderr.on('data', d => process.stdout.write(d.toString()));
    stream.on('close', () => c.end());
  });
});
c.on('error', e => console.error('SSH error:', e.message));
c.connect({ host: '62.171.128.241', port: 22, username: 'root', password: '<SEGREDO_REMOVIDO>', readyTimeout: 30000 });
