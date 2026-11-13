const { Client } = require('ssh2');
const c = new Client();
c.on('ready', () => {
  c.exec(`echo === CONTAINER_MODTIME_INDEX && docker exec hermes-call stat /app/client/dist/assets/index-DioXPln6.js && echo === CONTAINER_INDEXHTML_BUNDLE && docker exec hermes-call grep -oE 'index-[A-Za-z0-9_]+\.js' /app/client/dist/index.html && echo === CONTAINER_INDEXHTML && docker exec hermes-call ls -la /app/client/dist/ && echo === CONTAINER_BUILD_ID && docker exec hermes-call sh -c 'cat /app/client/dist/index.html | grep -oE "app/client/dist"' && echo === DISK_INDEXHTML_BUNDLE && grep -oE 'index-[A-Za-z0-9_]+\.js' /opt/hipercool-refactor/client/dist/index.html && echo === DISK_INDEXHTML_LISTING && ls -la /opt/hipercool-refactor/client/dist/ && echo === DISK_BUNDLE_HASH && md5sum /opt/hipercool-refactor/client/dist/assets/index-DioXPln6.js && echo === DISK_BUNDLE_FUNIL && grep -c Kanban /opt/hipercool-refactor/client/dist/assets/index-DioXPln6.js && echo === DISK_BUNDLE_MEETINGAI && grep -c MeetingAIPage /opt/hipercool-refactor/client/dist/assets/index-DioXPln6.js && echo === DISK_BUNDLE_REACTFLOW && grep -c reactflow /opt/hipercool-refactor/client/dist/assets/index-DioXPln6.js && echo === BUILD_OUTPUT && ls -la /opt/hipercool-refactor/client/dist/assets/`, (err, stream) => {
    if (err) { console.error(err); return; }
    stream.on('data', d => process.stdout.write(d.toString()));
    stream.stderr.on('data', d => process.stdout.write(d.toString()));
    stream.on('close', () => c.end());
  });
});
c.on('error', e => console.error('SSH error', e.message));
c.connect({ host: '62.171.128.241', port: 22, username: 'root', password: '<SEGREDO_REMOVIDO>', readyTimeout: 60000 });
