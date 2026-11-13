const { Client } = require('ssh2');
const c = new Client();
c.on('ready', () => {
  c.exec(`echo "=== source mtime ===" && stat /opt/hipercool-refactor/client/src/pages/MeetingAIPage.tsx && echo "=== source head ===" && head -30 /opt/hipercool-refactor/client/src/pages/MeetingAIPage.tsx && echo "=== App.tsx routes ===" && cat /opt/hipercool-refactor/client/src/App.tsx | head -100 && echo "=== Dockerfile ===" && cat /opt/hipercool-refactor/Dockerfile`, (err, stream) => {
    if (err) { console.error(err); return; }
    stream.on('data', d => process.stdout.write(d.toString()));
    stream.stderr.on('data', d => process.stdout.write(d.toString()));
    stream.on('close', () => c.end());
  });
});
c.on('error', e => console.error('SSH error', e.message));
c.connect({ host: '62.171.128.241', port: 22, username: 'root', password: '<SEGREDO_REMOVIDO>', readyTimeout: 30000 });
