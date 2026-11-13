const { Client } = require('ssh2');
const c = new Client();
c.on('ready', () => {
  c.exec('echo "=== Versão Node ===" && docker exec hermes-call sh -c "node -v 2>&1" 2>&1 ; echo "=== Rollup no package-lock.json ===" && grep -E "\"rollup\":" /opt/hipercool-refactor/client/package-lock.json | head -5 ; echo "=== Vite config dist (origem) ===" && grep -E "ui-primitive|icons|@/components/ui" /opt/hipercool-refactor/client/src/AuthGate.tsx 2>&1 | head -5', (err, stream) => {
    if (err) { console.error(err); return; }
    stream.on('data', d => process.stdout.write(d.toString()));
    stream.stderr.on('data', d => process.stdout.write(d.toString()));
    stream.on('close', () => c.end());
  });
});
c.on('error', e => console.error('SSH error:', e.message));
c.connect({ host: '62.171.128.241', port: 22, username: 'root', password: '<SEGREDO_REMOVIDO>', readyTimeout: 30000 });
