const { Client } = require('ssh2');
const c = new Client();
c.on('ready', () => {
  c.exec(`echo === LOCAL_VPS_HASH && md5sum /opt/hipercool-refactor/client/src/pages/MeetingAIPage.tsx && echo === && head -3 /opt/hipercool-refactor/client/src/pages/MeetingAIPage.tsx && echo === && echo "=== ATÉ ONDE TREE-SHAKE ===" && grep -c -E 'function (MeetingAI|Page)' /opt/hipercool-refactor/client/src/pages/MeetingAIPage.tsx && echo === && echo "=== O que importa ===" && grep -E '^import|MeetingAIPage' /opt/hipercool-refactor/client/src/pages/MeetingAIPage.tsx | head -20 && echo === && echo "=== Como App.tsx importa ===" && grep -B1 -A1 MeetingAI /opt/hipercool-refactor/client/src/App.tsx | head -10 && echo === && echo "=== Tree-shake analysis ===" && grep -rE 'MeetingAIPage' /opt/hipercool-refactor/client/src 2>&1 | head -20`, (err, stream) => {
    if (err) { console.error(err); return; }
    stream.on('data', d => process.stdout.write(d.toString()));
    stream.stderr.on('data', d => process.stdout.write(d.toString()));
    stream.on('close', () => c.end());
  });
});
c.on('error', e => console.error('SSH error', e.message));
c.connect({ host: '62.171.128.241', port: 22, username: 'root', password: '<SEGREDO_REMOVIDO>', readyTimeout: 30000 });
