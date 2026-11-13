const { Client } = require('ssh2');
const c = new Client();
c.on('ready', () => {
  c.exec(`echo "=== docker buildkit cache ===" && cat /var/lib/docker/buildkit/cache.db 2>/dev/null | head -100 && echo "=== imagem info ===" && docker image inspect hermes-call:beta --format "{{json .Config.Labels}}" 2>&1 | head -10 && echo "=== history ===" && docker history hermes-call:beta --no-trunc 2>&1 | head -20 && echo "=== build args ===" && docker image inspect hermes-call:beta --format "{{json .Config.Env}}" 2>&1 && echo "=== buildkit prune ===" && docker builder prune --help 2>&1 | head -5`, (err, stream) => {
    if (err) { console.error(err); return; }
    stream.on('data', d => process.stdout.write(d.toString()));
    stream.stderr.on('data', d => process.stdout.write(d.toString()));
    stream.on('close', () => c.end());
  });
});
c.on('error', e => console.error('SSH error', e.message));
c.connect({ host: '62.171.128.241', port: 22, username: 'root', password: '<SEGREDO_REMOVIDO>', readyTimeout: 30000 });
c.end();
