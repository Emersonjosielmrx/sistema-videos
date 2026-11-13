const { Client } = require('ssh2');
const c = new Client();
c.on('ready', () => {
  c.exec('echo "=== /opt/hipercool-refactor/client/src/lib/log.ts (conteúdo) ===" && cat /opt/hipercool-refactor/client/src/lib/log.ts 2>&1 | head -20 && echo "=== git log do sources - via Dockerfile ===" && cd /opt/hipercool-refactor && git log --oneline -5 2>&1 | head -10 && echo "=== Client dist do LOCAL ===" && ls -la /opt/hipercool-refactor/client/ 2>&1 | head -15 && echo "=== auth_handlers.go ===" && stat /opt/hipercool-refactor/cmd/server/auth_handlers.go 2>&1 | head -8 && echo "=== _LOG_DEPLOY_2026-07-25.md ===" && cat /opt/hipercool-refactor/_LOG_DEPLOY_2026-07-25.md 2>&1 | head -5', (err, stream) => {
    if (err) { console.error(err); return; }
    stream.on('data', d => process.stdout.write(d.toString()));
    stream.stderr.on('data', d => process.stdout.write(d.toString()));
    stream.on('close', () => c.end());
  });
});
c.on('error', e => console.error('SSH error:', e.message));
c.connect({ host: '62.171.128.241', port: 22, username: 'root', password: '<SEGREDO_REMOVIDO>', readyTimeout: 30000 });
