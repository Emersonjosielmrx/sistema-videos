const { Client } = require('ssh2');
const c = new Client();
c.on('ready', () => {
  c.exec('echo "=== TODOS os containers ===" && docker ps -a --format "table {{.Names}}\t{{.Image}}\t{{.Status}}" && echo "=== Logs: procurando mensagens de START no init ===" && docker logs --tail 200 hermes-call 2>&1 | grep -iE "build|version|start|channel|listen|v0\.|v1\." | head -30 && echo "=== Detalhes de quando o container reiniciou ===" && docker inspect hermes-call --format "{{.State.StartedAt}}" 2>&1', (err, stream) => {
    if (err) { console.error(err); return; }
    stream.on('data', d => process.stdout.write(d.toString()));
    stream.stderr.on('data', d => process.stdout.write(d.toString()));
    stream.on('close', () => c.end());
  });
});
c.on('error', e => console.error('SSH error:', e.message));
c.connect({ host: '62.171.128.241', port: 22, username: 'root', password: '<SEGREDO_REMOVIDO>', readyTimeout: 30000 });
