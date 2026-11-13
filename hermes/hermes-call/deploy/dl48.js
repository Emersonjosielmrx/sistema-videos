const { Client } = require('ssh2');
const c = new Client();
c.on('ready', () => {
  c.exec(`echo "=== Estrutura /app ===" && docker exec hermes-call ls -la /app/ && echo "=== Tem landing dir? ===" && docker exec hermes-call ls -la /app/landing/ 2>&1 | head -20 && echo "=== index.html landing ===" && docker exec hermes-call stat /app/landing/index.html 2>&1 && echo "=== find landing files ===" && docker exec hermes-call find /app -maxdepth 3 -name "landing" -o -name "*.html" 2>/dev/null | head -20`, (err, stream) => {
    if (err) { console.error(err); return; }
    stream.on('data', d => process.stdout.write(d.toString()));
    stream.stderr.on('data', d => process.stdout.write(d.toString()));
    stream.on('close', () => c.end());
  });
});
c.on('error', e => console.error('SSH error', e.message));
c.connect({ host: '62.171.128.241', port: 22, username: 'root', password: '<SEGREDO_REMOVIDO>', readyTimeout: 30000 });
