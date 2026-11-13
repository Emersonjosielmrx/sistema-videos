const { Client } = require('ssh2');
const c = new Client();
c.on('ready', () => {
  c.exec(`echo === MEETING_EXPORT && tail -20 /opt/hipercool-refactor/client/src/pages/MeetingAIPage.tsx && echo === && echo "=== STRINGS EM MEETINGAI ===" && grep -c 'Video' /opt/hipercool-refactor/client/src/pages/MeetingAIPage.tsx && grep -c 'Athena' /opt/hipercool-refactor/client/src/pages/MeetingAIPage.tsx && grep -c 'reactflow' /opt/hipercool-refactor/client/src/pages/MeetingAIPage.tsx && echo === && echo "=== SYNTAX CHECK ===" && cd /opt/hipercool-refactor/client && node -e "console.log(require('fs').readFileSync('src/pages/MeetingAIPage.tsx', 'utf8').slice(0, 500))" 2>&1 && echo === && echo "=== TS CHECK ===" && cd /opt/hipercool-refactor/client && npx tsc --noEmit src/pages/MeetingAIPage.tsx 2>&1 | head -20`, (err, stream) => {
    if (err) { console.error(err); return; }
    stream.on('data', d => process.stdout.write(d.toString()));
    stream.stderr.on('data', d => process.stdout.write(d.toString()));
    stream.on('close', () => c.end());
  });
});
c.on('error', e => console.error('SSH error', e.message));
c.connect({ host: '62.171.128.241', port: 22, username: 'root', password: '<SEGREDO_REMOVIDO>', readyTimeout: 60000 });
