const { Client } = require('ssh2');
const c = new Client();
c.on('ready', () => {
  c.exec('echo "=== client/dist mtime ===" && ls -la /opt/hipercool-refactor/client/dist/ 2>&1 | head -10 && echo "=== assets mtime ===" && ls -la /opt/hipercool-refactor/client/dist/assets/ 2>&1 | head -10 && echo "=== dist criado? ===" && docker exec hermes-call bash -c "ls -la /app/client/dist/assets/index-*.js && md5sum /app/client/dist/assets/index-*.js" && echo "=== Tem MeetingAIPage no dist do host? ===" && grep -c MeetingAIPage /opt/hipercool-refactor/client/dist/assets/index-*.js 2>&1 && echo "=== check if dist no host vai pro build ===" && stat /opt/hipercool-refactor/client/dist/index.html', (err, stream) => {
    if (err) { console.error(err); return; }
    stream.on('data', d => process.stdout.write(d.toString()));
    stream.stderr.on('data', d => process.stdout.write(d.toString()));
    stream.on('close', () => c.end());
  });
});
c.on('error', e => console.error('SSH error', e.message));
c.connect({ host: '62.171.128.241', port: 22, username: 'root', password: '<SEGREDO_REMOVIDO>', readyTimeout: 30000 });
