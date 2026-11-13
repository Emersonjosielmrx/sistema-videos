const { Client } = require('ssh2');
const c = new Client();
c.on('ready', () => {
  c.exec(`echo === SRC_NO_VPS && ls /opt/hipercool-refactor/client/src/pages/ | grep -i meeting && echo === HASH && md5sum /opt/hipercool-refactor/client/src/pages/MeetingAIPage.tsx && echo === SIZE && wc -l /opt/hipercool-refactor/client/src/pages/MeetingAIPage.tsx && echo === HEAD && head -1 /opt/hipercool-refactor/client/src/pages/MeetingAIPage.tsx && echo === && head -1 /opt/hipercool-refactor/client/src/lib/api.ts && echo === && echo "=== tsconfig path ===" && cat /opt/hipercool-refactor/client/tsconfig.json && echo === BUILD OUTPUT && find /opt/hipercool-refactor/client/dist -name "*.js" -newer /opt/hipercool-refactor/client/src/pages/MeetingAIPage.tsx 2>&1`, (err, stream) => {
    if (err) { console.error(err); return; }
    stream.on('data', d => process.stdout.write(d.toString()));
    stream.stderr.on('data', d => process.stdout.write(d.toString()));
    stream.on('close', () => c.end());
  });
});
c.on('error', e => console.error('SSH error', e.message));
c.connect({ host: '62.171.128.241', port: 22, username: 'root', password: '<SEGREDO_REMOVIDO>', readyTimeout: 30000 });
