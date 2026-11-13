const { Client } = require('ssh2');
const c = new Client();
c.on('ready', () => {
  c.exec(`grep -n 'meeting-ai\|MeetingAI' /opt/hipercool-refactor/client/src/App.tsx | head -10 && echo "=== Switch do View ===" && grep -n 'switch\|case' /opt/hipercool-refactor/client/src/App.tsx | head -30 && echo "=== renderView function ===" && grep -B2 -A10 'meeting' /opt/hipercool-refactor/client/src/App.tsx | head -50 && echo "=== NavConfig items ===" && cat /opt/hipercool-refactor/client/src/stores/navigation.ts | head -60`, (err, stream) => {
    if (err) { console.error(err); return; }
    stream.on('data', d => process.stdout.write(d.toString()));
    stream.stderr.on('data', d => process.stdout.write(d.toString()));
    stream.on('close', () => c.end());
  });
});
c.on('error', e => console.error('SSH error', e.message));
c.connect({ host: '62.171.128.241', port: 22, username: 'root', password: '<SEGREDO_REMOVIDO>', readyTimeout: 30000 });
