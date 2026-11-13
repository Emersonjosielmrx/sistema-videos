const { Client } = require('ssh2');
const c = new Client();
c.on('ready', () => {
  c.exec(`echo === DISK_HASH && md5sum /opt/hipercool-refactor/client/dist/assets/index-DioXPln6.js && echo === DISK_FUNIL && grep -c Kanban /opt/hipercool-refactor/client/dist/assets/index-DioXPln6.js && echo === DISK_MEETINGAI && grep -c MeetingAIPage /opt/hipercool-refactor/client/dist/assets/index-DioXPln6.js && echo === DISK_REACTFLOW && grep -c reactflow /opt/hipercool-refactor/client/dist/assets/index-DioXPln6.js && echo === DISK_LIST && ls -la /opt/hipercool-refactor/client/dist/assets/ && echo === DISK_INDEXHTML && cat /opt/hipercool-refactor/client/dist/index.html | grep -oE 'index-[A-Za-z0-9_]+'`, (err, stream) => {
    if (err) { console.error(err); return; }
    stream.on('data', d => process.stdout.write(d.toString()));
    stream.stderr.on('data', d => process.stdout.write(d.toString()));
    stream.on('close', () => c.end());
  });
});
c.on('error', e => console.error('SSH error', e.message));
c.connect({ host: '62.171.128.241', port: 22, username: 'root', password: '<SEGREDO_REMOVIDO>', readyTimeout: 30000 });
