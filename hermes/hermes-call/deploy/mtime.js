const { Client } = require('ssh2');
const c = new Client();
c.on('ready', () => {
  c.exec(`echo === PAGES_MTIME && ls -la /opt/hipercool-refactor/client/src/pages/MeetingAIPage.tsx /opt/hipercool-refactor/client/src/pages/FollowUpPage.tsx && echo === BUNDLE_MTIME && ls -la /opt/hipercool-refactor/client/dist/assets/ && echo === DISK_HASH_AGAIN && md5sum /opt/hipercool-refactor/client/dist/assets/index-DioXPln6.js && echo === DISK_FUNIL && grep -c Kanban /opt/hipercool-refactor/client/dist/assets/index-DioXPln6.js && echo === DISK_REACTFLOW && grep -c -i reactflow /opt/hipercool-refactor/client/dist/assets/index-DioXPln6.js && echo === DISK_REACTFLOW_HITS && grep -oE 'reactflow|react-flow|@reactflow|ReactFlow|MeetingAIPage' /opt/hipercool-refactor/client/dist/assets/index-DioXPln6.js | sort -u`, (err, stream) => {
    if (err) { console.error(err); return; }
    stream.on('data', d => process.stdout.write(d.toString()));
    stream.stderr.on('data', d => process.stdout.write(d.toString()));
    stream.on('close', () => c.end());
  });
});
c.on('error', e => console.error('SSH error', e.message));
c.connect({ host: '62.171.128.241', port: 22, username: 'root', password: '<SEGREDO_REMOVIDO>', readyTimeout: 30000 });
