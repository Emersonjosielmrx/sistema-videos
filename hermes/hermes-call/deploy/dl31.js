const { Client } = require('ssh2');
const c = new Client();
c.on('ready', () => {
  c.exec('echo "=== Portas 80/443 ===" && ss -tlnp | grep -E ":(80|443)\b" && echo "=== ss all tcp ===" && ss -tlnp && echo "=== netstat ===" && netstat -tlnp 2>/dev/null | head -30 && echo "=== iptables ===" && iptables -t nat -L -n 2>&1 | head -30 && echo "=== process list ===" && ps -ef | grep -E "traefik|nginx|caddy|haproxy" | grep -v grep', (err, stream) => {
    if (err) { console.error(err); return; }
    stream.on('data', d => process.stdout.write(d.toString()));
    stream.stderr.on('data', d => process.stdout.write(d.toString()));
    stream.on('close', () => c.end());
  });
});
c.on('error', e => console.error('SSH error:', e.message));
c.connect({ host: '62.171.128.241', port: 22, username: 'root', password: '<SEGREDO_REMOVIDO>', readyTimeout: 30000 });
