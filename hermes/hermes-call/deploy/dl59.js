const { Client } = require('ssh2');
const c = new Client();
c.on('ready', () => {
  c.exec(`grep -A2 'meeting-ai\|MeetingAI' /opt/hipercool-refactor/client/src/App.tsx | head -30 && echo "=== NavConfig ===" && grep -A2 'meet' /opt/hipercool-refactor/client/src/stores/navigation.ts | head -30 && echo "=== BuildKit cache ===" && ls -la /var/lib/docker/buildkit/ 2>&1 | head -5 && echo "=== check tmp build_out ===" && ls /opt/build-out/ 2>&1 | head -10 && echo "=== check git ===" && ls -la /opt/hipercool-refactor/.git 2>&1 | head -5 && echo "=== mtime Dockerfile ===" && stat /opt/hipercool-refactor/Dockerfile && echo "=== Dockerfile total ===" && cat /opt/hipercool-refactor/Dockerfile`, (err, stream) => {
    if (err) { console.error(err); return; }
    stream.on('data', d => process.stdout.write(d.toString()));
    stream.stderr.on('data', d => process.stdout.write(d.toString()));
    stream.on('close', () => c.end());
  });
});
c.on('error', e => console.error('SSH error', e.message));
c.connect({ host: '62.171.128.241', port: 22, username: 'root', password: '<SEGREDO_REMOVIDO>', readyTimeout: 30000 });
