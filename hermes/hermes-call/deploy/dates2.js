const { Client } = require('ssh2');
const c = new Client();
c.on('ready', () => {
  c.exec(`stat -c '%y %n' /opt/hipercool-refactor/client/src/components/layout/Sidebar.tsx /opt/hipercool-refactor/client/src/pages/MeetingAIPage.tsx /opt/hipercool-refactor/cmd/server/httpapi.go /opt/hipercool-refactor/client/src/App.tsx 2>&1`, (err, stream) => {
    if (err) { console.error(err); return; }
    stream.on('data', d => process.stdout.write(d.toString()));
    stream.stderr.on('data', d => process.stdout.write(d.toString()));
    stream.on('close', () => c.end());
  });
});
c.on('error', e => console.error('SSH error', e.message));
c.connect({ host: '62.171.128.241', port: 22, username: 'root', password: '<SEGREDO_REMOVIDO>', readyTimeout: 30000 });
