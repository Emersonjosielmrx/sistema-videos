const { Client } = require('ssh2');
const c = new Client();
c.on('ready', () => {
  c.exec(`echo "=== /app/full tree ===" && docker exec hermes-call find /app -type f 2>/dev/null | head -50 && echo "=== /app/client/ ===" && docker exec hermes-call find /app/client -type f 2>/dev/null | head -50 && echo "=== /app/data/ ===" && docker exec hermes-call find /app/data -type f 2>/dev/null | head -20 && echo "=== wacalls -? ===" && docker exec hermes-call wacalls -h 2>&1 | head -30`, (err, stream) => {
    if (err) { console.error(err); return; }
    stream.on('data', d => process.stdout.write(d.toString()));
    stream.stderr.on('data', d => process.stdout.write(d.toString()));
    stream.on('close', () => c.end());
  });
});
c.on('error', e => console.error('SSH error', e.message));
c.connect({ host: '62.171.128.241', port: 22, username: 'root', password: '<SEGREDO_REMOVIDO>', readyTimeout: 30000 });
