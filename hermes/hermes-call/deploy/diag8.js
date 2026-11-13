const { Client } = require('ssh2');
const c = new Client();
c.on('ready', () => {
  c.exec('echo "=== Imagens ===" && docker images "hermes-call" --format "table {{.Repository}}:{{.Tag}}\t{{.ID}}\t{{.CreatedAt}}" && echo "=== Container info ===" && docker inspect hermes-call --format "Image={{.Image}}\nCreated={{.Created}}\nStarted={{.State.StartedAt}}" 2>&1 && echo "=== Files dentro do container (extraindo) ===" && docker exec hermes-call sh -c "ls -la /app/client/dist/assets/ && md5sum /app/client/dist/assets/*.js" 2>&1 | head -20', (err, stream) => {
    if (err) { console.error(err); return; }
    stream.on('data', d => process.stdout.write(d.toString()));
    stream.stderr.on('data', d => process.stdout.write(d.toString()));
    stream.on('close', () => c.end());
  });
});
c.on('error', e => console.error('SSH error:', e.message));
c.connect({ host: '62.171.128.241', port: 22, username: 'root', password: '<SEGREDO_REMOVIDO>', readyTimeout: 30000 });
