const { Client } = require('ssh2');
const c = new Client();
c.on('ready', () => {
  c.exec('echo "=== LSP src on VPS ===" && ls /opt/hipercool-refactor/client/src/pages/ | grep -i meet && echo "=== Source size ===" && stat /opt/hipercool-refactor/client/src/pages/MeetingAIPage.tsx | head -10 && echo "=== mtime local ===" && stat /d/hipercool-refactor/client/src/pages/MeetingAIPage.tsx 2>&1 | head -10 && echo "=== diff local vs vps ===" && diff /d/hipercool-refactor/client/src/pages/MeetingAIPage.tsx /opt/hipercool-refactor/client/src/pages/MeetingAIPage.tsx 2>&1 | head -20 && echo "=== build stamp atual ===" && curl -s http://127.0.0.1:8080/api/version && echo "=== dist mtime ===" && stat /opt/hipercool-refactor/client/dist/assets/index-*.js 2>&1', (err, stream) => {
    if (err) { console.error(err); return; }
    stream.on('data', d => process.stdout.write(d.toString()));
    stream.stderr.on('data', d => process.stdout.write(d.toString()));
    stream.on('close', () => c.end());
  });
});
c.on('error', e => console.error('SSH error', e.message));
c.connect({ host: '62.171.128.241', port: 22, username: 'root', password: '<SEGREDO_REMOVIDO>', readyTimeout: 30000 });
