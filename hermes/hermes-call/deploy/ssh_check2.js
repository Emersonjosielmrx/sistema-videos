const { Client } = require('ssh2');
const c = new Client();
c.on('ready', () => {
  c.exec('echo "=== File listing at / ===" && ls -la / 2>&1 | head -30 && echo "=== Containers ===" && docker ps -a --format "table {{.Names}}\t{{.Image}}\t{{.CreatedAt}}\t{{.Status}}" && echo "=== Image history ===" && docker history hermes-call:beta --format "table {{.CreatedAt}}\t{{.CreatedBy}}" 2>&1 | head -20 && echo "=== Hermes-call:beta layer commands ===" && docker inspect hermes-call:beta --format "{{.Created}}" 2>&1', (err, stream) => {
    if (err) { console.error(err); return; }
    stream.on('data', d => process.stdout.write(d.toString()));
    stream.stderr.on('data', d => process.stdout.write(d.toString()));
    stream.on('close', () => c.end());
  });
});
c.on('error', e => console.error('SSH error:', e.message));
c.connect({ host: '62.171.128.241', port: 22, username: 'root', password: '<SEGREDO_REMOVIDO>', readyTimeout: 30000 });
