const { Client } = require('ssh2');
const c = new Client();
c.on('ready', () => {
  c.exec('echo === IMAGES && docker images hermes-call --format "table {{.Tag}}\t{{.ID}}\t{{.CreatedAt}}\t{{.Size}}" && echo === TAGS && docker images | grep -E "hermes-call" && echo === CONTAINER_HISTORY && docker history hermes-call:latest --format "table {{.CreatedBy}}\t{{.CreatedAt}}" 2>&1 | head -10', (err, stream) => {
    if (err) { console.error(err); return; }
    stream.on('data', d => process.stdout.write(d.toString()));
    stream.stderr.on('data', d => process.stdout.write(d.toString()));
    stream.on('close', () => c.end());
  });
});
c.on('error', e => console.error('SSH error', e.message));
c.connect({ host: '62.171.128.241', port: 22, username: 'root', password: '<SEGREDO_REMOVIDO>', readyTimeout: 30000 });
