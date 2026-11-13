const { Client } = require('ssh2');
const c = new Client();
c.on('ready', () => {
  c.exec('echo "=== Backup do estado quebrado ===" && mv /opt/traefik-config/dynamic/hermes-teste.yml /tmp/hermes-teste-broken.yml && echo "=== Cria rota NO-OP (apenas healthcheck, sem forwarding) ===" && cat > /opt/traefik-config/dynamic/hermes-teste.yml <<EOF_YAML
http:
  routers:
    hermes-teste-disabled:
      rule: "Host(\\"hermescallteste.opus-sem-limites.com.br\\")"
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
EOF_YAML
 && echo "=== Conteudo novo ===" && cat /opt/traefik-config/dynamic/hermes-teste.yml && echo "=== Restart traefik ===" && docker restart traefik 2>&1 && echo "=== Aguarda 5s ===" && sleep 5 && echo "=== Status ===" && docker logs --tail 10 traefik 2>&1 | head -10 && echo "=== Testa rotas ===" && curl -s -o /dev/null -w "teste: HTTP %{http_code}\n" --connect-timeout 10 http://hermescallteste.opus-sem-limites.com.br/ 2>&1 && curl -s -o /dev/null -w "prod: HTTP %{http_code}\n" --connect-timeout 10 https://hermescall.opus-sem-limites.com.br/ 2>&1', (err, stream) => {
    if (err) { console.error(err); return; }
    stream.on('data', d => process.stdout.write(d.toString()));
    stream.stderr.on('data', d => process.stdout.write(d.toString()));
    stream.on('close', () => c.end());
  });
});
c.on('error', e => console.error('SSH error:', e.message));
c.connect({ host: '62.171.128.241', port: 22, username: 'root', password: '<SEGREDO_REMOVIDO>', readyTimeout: 30000 });
