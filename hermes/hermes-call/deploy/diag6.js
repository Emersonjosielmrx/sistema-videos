const { Client } = require('ssh2');
const c = new Client();
c.on('ready', () => {
  c.exec('echo "=== Docker logs - últimas 100 linhas (procura build/startup) ===" && docker logs --tail 100 hermes-call 2>&1 | head -80 && echo "=== Tabelas com prefxos hcsrc ===" && ls -la /opt/hermes-call/ 2>&1 | head -15 && echo "=== Verifica se tem cliente novo rodando ===" && curl -s http://127.0.0.1:8080/api/version 2>&1 && echo "=== Container inspect (env vars) ===" && docker inspect hermes-call --format "{{.Config.Env}}" 2>&1 | head -3', (err, stream) => {
    if (err) { console.error(err); return; }
    stream.on('data', d => process.stdout.write(d.toString()));
    stream.stderr.on('data', d => process.stdout.write(d.toString()));
    stream.on('close', () => c.end());
  });
});
c.on('error', e => console.error('SSH error:', e.message));
c.connect({ host: '62.171.128.241', port: 22, username: 'root', password: '<SEGREDO_REMOVIDO>', readyTimeout: 30000 });
