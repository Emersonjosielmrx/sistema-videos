const { Client } = require('ssh2');
const c = new Client();
c.on('ready', () => {
  c.exec('docker exec traefik sh -c "echo BACKUP && cp /etc/traefik/dynamic/hermes-teste.yml /etc/traefik/dynamic/hermes-teste.yml.bak && echo REMOVE && rm /etc/traefik/dynamic/hermes-teste.yml && echo LIST && ls /etc/traefik/dynamic/" && echo "=== Aguarda 5s ===" && sleep 5 && curl -s -o /dev/null -w "teste: HTTP %{http_code}\n" --connect-timeout 10 http://hermescallteste.opus-sem-limites.com.br/ 2>&1 && curl -s -o /dev/null -w "prod: HTTP %{http_code}\n" --connect-timeout 10 https://hermescall.opus-sem-limites.com.br/ 2>&1', (err, stream) => {
    if (err) { console.error(err); return; }
    stream.on('data', d => process.stdout.write(d.toString()));
    stream.stderr.on('data', d => process.stdout.write(d.toString()));
    stream.on('close', () => c.end());
  });
});
c.on('error', e => console.error('SSH error:', e.message));
c.connect({ host: '62.171.128.241', port: 22, username: 'root', password: '<SEGREDO_REMOVIDO>', readyTimeout: 30000 });
