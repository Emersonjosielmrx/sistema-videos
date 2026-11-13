const { Client } = require('ssh2');
const c = new Client();
c.on('ready', () => {
  c.exec(`cd /opt/hipercool-refactor/client && ls -la package-lock.json node_modules/.package-lock.json 2>&1 && echo "=== npm ci output ===" && npm ci 2>&1 | tail -30 && echo "=== reactflow ok? ===" && ls node_modules/reactflow 2>&1 | head -5`, (err, stream) => {
    if (err) { console.error(err); return; }
    stream.on('data', d => process.stdout.write(d.toString()));
    stream.stderr.on('data', d => process.stdout.write(d.toString()));
    stream.on('close', () => c.end());
  });
});
c.on('error', e => console.error('SSH error', e.message));
c.connect({ host: '62.171.128.241', port: 22, username: 'root', password: '<SEGREDO_REMOVIDO>', readyTimeout: 180000 });
