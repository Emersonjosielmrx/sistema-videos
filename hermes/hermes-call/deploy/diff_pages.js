const { Client } = require('ssh2');
const c = new Client();
c.on('ready', () => {
  c.exec(`echo === LOCAL_PAGES && ls -la /opt/hipercool-refactor/client/src/pages/ && echo === LOCAL_MEETING_HASH && md5sum /opt/hipercool-refactor/client/src/pages/MeetingAIPage.tsx && echo === LOCAL_APP_HASH && md5sum /opt/hipercool-refactor/client/src/App.tsx && echo === LOCAL_NAV_HASH && md5sum /opt/hipercool-refactor/client/src/stores/navigation.ts && echo === LOCAL_PACKAGE && md5sum /opt/hipercool-refactor/client/package.json && echo === LOCAL_PACKAGE_LOCK && md5sum /opt/hipercool-refactor/client/package-lock.json && echo === LOCAL_REACTFLOW && ls -la /opt/hipercool-refactor/client/node_modules/reactflow 2>&1 | head -3 && echo === LOCAL_VITE && ls /opt/hipercool-refactor/client/node_modules/.bin/vite 2>&1`, (err, stream) => {
    if (err) { console.error(err); return; }
    stream.on('data', d => process.stdout.write(d.toString()));
    stream.stderr.on('data', d => process.stdout.write(d.toString()));
    stream.on('close', () => c.end());
  });
});
c.on('error', e => console.error('SSH error', e.message));
c.connect({ host: '62.171.128.241', port: 22, username: 'root', password: '<SEGREDO_REMOVIDO>', readyTimeout: 30000 });
