const { Client } = require('ssh2');
const c = new Client();
c.on('ready', () => {
  c.exec('echo "=== Inspect hermes-call ===" && docker inspect hermes-call --format "NetworkMode: {{.HostConfig.NetworkMode}}\nCmd: {{.Config.Cmd}}\nEntrypoint: {{.Config.Entrypoint}}" 2>&1 && echo "=== Inspect wacalls do container ===" && docker exec hermes-call ps aux 2>&1 | head -3 && echo "=== bind mount do hermes-call ===" && docker inspect hermes-call --format "{{json .Mounts}}" 2>&1 | head -10 && echo "=== reverse do container ===" && docker exec hermes-call wacalls --help 2>&1 | head -10 || echo "n\u00e3o tem help" && echo "=== test inside container ===" && docker exec hermes-call curl -s http://127.0.0.1:8080/api/version 2>&1 | head -5', (err, stream) => {
    if (err) { console.error(err); return; }
    stream.on('data', d => process.stdout.write(d.toString()));
    stream.stderr.on('data', d => process.stdout.write(d.toString()));
    stream.on('close', () => c.end());
  });
});
c.on('error', e => console.error('SSH error:', e.message));
c.connect({ host: '62.171.128.241', port: 22, username: 'root', password: '<SEGREDO_REMOVIDO>', readyTimeout: 30000 });
