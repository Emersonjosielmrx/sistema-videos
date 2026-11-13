const { Client } = require('ssh2');
const c = new Client();
c.on('ready', () => {
  c.exec('echo "=== Portas em uso ===" && ss -tulpn 2>&1 | grep -E "8080|8081|8000|80" | head -20 && echo "=== Quem escuta 8081? ===" && netstat -tlnp 2>&1 | grep 8081 && echo "=== Processos em background ===" && ps -ef 2>&1 | grep -E "wacalls|hermes|8081" | head -10 && echo "=== docker ps all ===" && docker ps -a --format "table {{.Names}}\t{{.Image}}\t{{.Ports}}\t{{.Status}}"', (err, stream) => {
    if (err) { console.error(err); return; }
    stream.on('data', d => process.stdout.write(d.toString()));
    stream.stderr.on('data', d => process.stdout.write(d.toString()));
    stream.on('close', () => c.end());
  });
});
c.on('error', e => console.error('SSH error:', e.message));
c.connect({ host: '62.171.128.241', port: 22, username: 'root', password: '<SEGREDO_REMOVIDO>', readyTimeout: 30000 });
