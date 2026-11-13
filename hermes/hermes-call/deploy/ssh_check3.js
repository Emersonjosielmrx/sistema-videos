const { Client } = require('ssh2');
const c = new Client();
c.on('ready', () => {
  c.exec('echo "=== Docker events (últimas 20) ===" && docker events --since "2026-07-25T07:00:00" --until "2026-07-25T13:00:00" --format "table {{.Time}}\t{{.Type}}\t{{.Actor.Name}}\t{{.Action}}" 2>&1 | head -30 && echo "=== Imagens hermes-call ===" && docker images "hermes-call" --format "table {{.Repository}}:{{.Tag}}\t{{.ID}}\t{{.CreatedAt}}\t{{.Size}}" && echo "=== Container logs do hermes-call (últimas 30 linhas) ===" && docker logs --tail 30 hermes-call 2>&1 | head -50', (err, stream) => {
    if (err) { console.error(err); return; }
    stream.on('data', d => process.stdout.write(d.toString()));
    stream.stderr.on('data', d => process.stdout.write(d.toString()));
    stream.on('close', () => c.end());
  });
});
c.on('error', e => console.error('SSH error:', e.message));
c.connect({ host: '62.171.128.241', port: 22, username: 'root', password: '<SEGREDO_REMOVIDO>', readyTimeout: 30000 });
