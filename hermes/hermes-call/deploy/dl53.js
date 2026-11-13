const { Client } = require('ssh2');
const c = new Client();
c.on('ready', () => {
  c.exec(`echo "=== landing/index.html head ===" && docker exec hermes-call head -30 /app/client/dist/landing/index.html && echo "=== BACKUP index.html head ===" && docker exec hermes-call head -30 /app/client/dist/_landing_BACKUP_inovare_20260723-115217/index.html && echo "=== diff ===" && docker exec hermes-call diff -q /app/client/dist/landing/ /app/client/dist/_landing_BACKUP_inovare_20260723-115217/ 2>&1 | head -20 && echo "=== diff index.html ===" && docker exec hermes-call diff /app/client/dist/landing/index.html /app/client/dist/_landing_BACKUP_inovare_20260723-115217/index.html | head -50 && echo "=== mtime BACKUP ===" && docker exec hermes-call stat /app/client/dist/_landing_BACKUP_inovare_20260723-115217/index.html`, (err, stream) => {
    if (err) { console.error(err); return; }
    stream.on('data', d => process.stdout.write(d.toString()));
    stream.stderr.on('data', d => process.stdout.write(d.toString()));
    stream.on('close', () => c.end());
  });
});
c.on('error', e => console.error('SSH error', e.message));
c.connect({ host: '62.171.128.241', port: 22, username: 'root', password: '<SEGREDO_REMOVIDO>', readyTimeout: 30000 });
