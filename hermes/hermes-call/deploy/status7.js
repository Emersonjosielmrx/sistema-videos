const { Client } = require('ssh2');
const c = new Client();
c.on('ready', () => {
  c.exec('echo "=== Stage 1 build cache? ===" && docker builder du 2>&1 | head -20 && echo "=== Sem cache ===" && echo "=== Latest build details ===" && docker image inspect hermes-call:latest --format "Created: {{.Created}}\nBuildCache: {{json .Config.Labels}}" 2>&1 && echo "=== procura build logs ===" && find /var/lib/docker/buildkit -name "*.log" 2>/dev/null | head -5 && echo "=== rebilda de novo limpando cache ===" && echo "USER_TRIGGER"', (err, stream) => {
    if (err) { console.error(err); return; }
    stream.on('data', d => process.stdout.write(d.toString()));
    stream.stderr.on('data', d => process.stdout.write(d.toString()));
    stream.on('close', () => c.end());
  });
});
c.on('error', e => console.error('SSH error', e.message));
c.connect({ host: '62.171.128.241', port: 22, username: 'root', password: '<SEGREDO_REMOVIDO>', readyTimeout: 30000 });
