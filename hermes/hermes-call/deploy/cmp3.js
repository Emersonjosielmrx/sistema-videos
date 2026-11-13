const { Client } = require('ssh2');
const c = new Client();
c.on('ready', () => {
  c.exec('echo "=== Lista src/components na VPS ===" && ls /opt/hipercool-refactor/client/src/components/ 2>&1 | head -20 && echo "=== Local ===" && find /d/hipercool-refactor/client/src/components/ -maxdepth 1 -type d 2>&1 | head -20 && echo "=== Local landing files ===" && ls /d/hipercool-refactor/client/src/components/landing/ 2>&1 | head -10 && echo "=== VPS landing files ===" && ls /opt/hipercool-refactor/client/src/components/landing/ 2>&1 | head -10 && echo "=== VPS public (assets) ===" && ls /opt/hipercool-refactor/client/public/ 2>&1 | head && echo "=== Local public ===" && ls /d/hipercool-refactor/client/public/ 2>&1 | head', (err, stream) => {
    if (err) { console.error(err); return; }
    stream.on('data', d => process.stdout.write(d.toString()));
    stream.stderr.on('data', d => process.stdout.write(d.toString()));
    stream.on('close', () => c.end());
  });
});
c.on('error', e => console.error('SSH error:', e.message));
c.connect({ host: '62.171.128.241', port: 22, username: 'root', password: '<SEGREDO_REMOVIDO>', readyTimeout: 30000 });
