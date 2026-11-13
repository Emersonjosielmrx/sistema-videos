const { Client } = require('ssh2');
const c = new Client();
c.on('ready', () => {
  c.exec('echo "=== Antes ===" && docker images "hermes-call" --format "table {{.Repository}}:{{.Tag}}\t{{.ID}}\t{{.CreatedAt}}" && echo "=== Remove build cache ===" && docker builder prune -af 2>&1 | tail -10 && echo "=== Remove :beta (para forçar fresh build) ===" && docker rmi hermes-call:beta 2>&1 && echo "=== Tagueia :stable manual como safe-point ===" && docker tag hermes-call:stable hermes-call:stable-prev-rollback && echo "=== Após ===" && docker images "hermes-call" --format "table {{.Repository}}:{{.Tag}}\t{{.ID}}\t{{.CreatedAt}}"', (err, stream) => {
    if (err) { console.error(err); return; }
    stream.on('data', d => process.stdout.write(d.toString()));
    stream.stderr.on('data', d => process.stdout.write(d.toString()));
    stream.on('close', () => c.end());
  });
});
c.on('error', e => console.error('SSH error:', e.message));
c.connect({ host: '62.171.128.241', port: 22, username: 'root', password: '<SEGREDO_REMOVIDO>', readyTimeout: 30000 });
