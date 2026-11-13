const { Client } = require('ssh2');
const c = new Client();
c.on('ready', () => {
  c.exec('echo "=== /opt/hipercool-refactor ===" && ls -la /opt/hipercool-refactor/ 2>&1 | head -15 && echo "=== Detalhes do Dockerfile ===" && stat /opt/hipercool-refactor/Dockerfile 2>&1 | head -8 && echo "=== Idem do client/src/lib/log.ts ===" && stat /opt/hipercool-refactor/client/src/lib/log.ts 2>&1 | head -8 && echo "=== local dist files ===" && ls -la /opt/hipercool-refactor/client/dist/assets/ 2>&1 | head -10', (err, stream) => {
    if (err) { console.error(err); return; }
    stream.on('data', d => process.stdout.write(d.toString()));
    stream.stderr.on('data', d => process.stdout.write(d.toString()));
    stream.on('close', () => c.end());
  });
});
c.on('error', e => console.error('SSH error:', e.message));
c.connect({ host: '62.171.128.241', port: 22, username: 'root', password: '<SEGREDO_REMOVIDO>', readyTimeout: 30000 });
