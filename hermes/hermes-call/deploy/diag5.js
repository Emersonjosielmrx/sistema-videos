const { Client } = require('ssh2');
const c = new Client();
c.on('ready', () => {
  c.exec('echo "=== auth_handlers.go na VPS (procurando P1-005) ===" && grep -E "handleAuthRefresh|handleAuthLogout" /opt/hipercool-refactor/cmd/server/auth_handlers.go 2>&1 | head -10 && echo "=== App.tsx na VPS ===" && grep -E "RecordingsPage|TranscriptsPage" /opt/hipercool-refactor/client/src/App.tsx 2>&1 | head -10 && echo "=== RecordingsPage na VPS ===" && head -5 /opt/hipercool-refactor/client/src/pages/RecordingsPage.tsx 2>&1 && echo "=== git tags na VPS (não tem git) - confirma SHA via Dockerfile ===" && md5sum /opt/hipercool-refactor/client/src/lib/log.ts /opt/hipercool-refactor/client/src/App.tsx 2>&1', (err, stream) => {
    if (err) { console.error(err); return; }
    stream.on('data', d => process.stdout.write(d.toString()));
    stream.stderr.on('data', d => process.stdout.write(d.toString()));
    stream.on('close', () => c.end());
  });
});
c.on('error', e => console.error('SSH error:', e.message));
c.connect({ host: '62.171.128.241', port: 22, username: 'root', password: '<SEGREDO_REMOVIDO>', readyTimeout: 30000 });
