const { Client } = require('ssh2');
const c = new Client();
c.on('ready', () => {
  c.exec('echo "=== docker ps ===" && docker ps -a --format "table {{.Names}}\t{{.Image}}\t{{.Ports}}\t{{.Status}}" && echo "=== docker inspect hermes-call JSON ===" && docker inspect hermes-call --format "{{json .HostConfig.PortBindings}}" 2>&1 && echo "=== tudo na porta 8080 ===" && lsof -i :8080 2>&1 | head -10 && echo "=== PID 1067158 (wacalls no 8080) ===" && ps -fp 1067158 2>&1 | head -5 && echo "=== Acha o hermes-call-teste antigo ===" && find / -name "28fa4d7d2caf" 2>/dev/null | head -5', (err, stream) => {
    if (err) { console.error(err); return; }
    stream.on('data', d => process.stdout.write(d.toString()));
    stream.stderr.on('data', d => process.stdout.write(d.toString()));
    stream.on('close', () => c.end());
  });
});
c.on('error', e => console.error('SSH error:', e.message));
c.connect({ host: '62.171.128.241', port: 22, username: 'root', password: '<SEGREDO_REMOVIDO>', readyTimeout: 30000 });
