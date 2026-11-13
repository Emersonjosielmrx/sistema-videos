const { Client } = require('ssh2');
const c = new Client();
c.on('ready', () => {
  c.exec('echo "=== Backup p/ /tmp (ro writable) ===" && docker cp traefik:/etc/traefik/dynamic/hermes-teste.yml /tmp/hermes-teste.yml.bak && echo "=== Conteúdo backup ===" && cat /tmp/hermes-teste.yml.bak && echo "=== Sobrescreve hermes-teste.yml com route quebrada (aponta p/ 127.0.0.1:9999) ===" && docker exec -i traefik sh -c "cat > /etc/traefik/dynamic/hermes-teste.yml" <<EOF_OUTER\nhttp:\n  routers:\n    hermes-teste:\n      rule: "Host(\\`hermescallteste.opus-sem-limites.com.br\\`)"\n      service: hermes-teste-svc\n      entryPoints:\n        - web\n        - websecure\n      tls:\n        certResolver: le\n  services:\n    hermes-teste-svc:\n      loadBalancer:\n        servers:\n          - url: "http://127.0.0.1:9999/"\nEOF_OUTER\n && echo "=== Container filesystem check ===" && docker exec traefik sh -c "ls -la /etc/traefik/dynamic/ && cat /etc/traefik/dynamic/hermes-teste.yml 2>&1 | head -20"', (err, stream) => {
    if (err) { console.error(err); return; }
    stream.on('data', d => process.stdout.write(d.toString()));
    stream.stderr.on('data', d => process.stdout.write(d.toString()));
    stream.on('close', () => c.end());
  });
});
c.on('error', e => console.error('SSH error:', e.message));
c.connect({ host: '62.171.128.241', port: 22, username: 'root', password: '<SEGREDO_REMOVIDO>', readyTimeout: 30000 });
