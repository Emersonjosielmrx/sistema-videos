const { Client } = require('ssh2');
const c = new Client();
c.on('ready', () => {
  c.exec('echo "=== Backup do teste.yml ===" && docker cp traefik:/etc/traefik/dynamic/hermes-teste.yml /tmp/hermes-teste.yml.bak && ls -la /tmp/hermes-teste.yml.bak && echo "=== Sobrescreve o hermes-teste.yml via volume mount trick ===" && docker run --rm -v /tmp/hermes-teste.yml.bak:/src/hermes-teste.yml -v /var/lib/docker/volumes/traefik_dynamic/_data:/dst alpine cp /src/hermes-teste.yml /dst/hermes-teste.yml 2>&1 || echo "Volume mount falhou, tentar de outro jeito" && echo "=== Verifica os arquivos do diretório dynamic do traefik ===" && docker exec traefik sh -c "ls -la /etc/traefik/dynamic/ 2>&1"', (err, stream) => {
    if (err) { console.error(err); return; }
    stream.on('data', d => process.stdout.write(d.toString()));
    stream.stderr.on('data', d => process.stdout.write(d.toString()));
    stream.on('close', () => c.end());
  });
});
c.on('error', e => console.error('SSH error:', e.message));
c.connect({ host: '62.171.128.241', port: 22, username: 'root', password: '<SEGREDO_REMOVIDO>', readyTimeout: 30000 });
