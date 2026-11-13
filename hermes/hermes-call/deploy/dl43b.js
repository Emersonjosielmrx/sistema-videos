const { Client } = require('ssh2');
const c = new Client();
c.on('ready', () => {
  c.exec('docker exec hermes-call bash -c "stat /app/client/dist/index.html && echo ASSETS && ls -la /app/client/dist/assets/ | head -30 && echo INDEX && cat /app/client/dist/index.html" 2>&1', (err, stream) => {
    if (err) { console.error(err); return; }
    stream.on('data', d => process.stdout.write(d.toString()));
    stream.stderr.on('data', d => process.stdout.write(d.toString()));
    stream.on('close', () => c.end());
  });
});
c.on('error', e => console.error('SSH error:', e.message));
c.connect({ host: '62.171.128.241', port: 22, username: 'root', password: '<SEGREDO_REMOVIDO>', readyTimeout: 30000 });
