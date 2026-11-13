const { Client } = require('ssh2');
const c = new Client();
c.on('ready', () => {
  c.exec(`echo === CONTAINER_CREATED && docker inspect hermes-call --format '{{.Created}}' && echo === IMAGE_CREATED && docker inspect hermes-call:latest --format '{{.Created}}' && echo === GIT_LAST_COMMIT && cd /opt/hipercool-refactor && git log -1 --format='%H %ai %s' && echo === FILES_MTIME && stat -c '%y %n' /opt/hipercool-refactor/client/src/components/layout/Sidebar.tsx /opt/hipercool-refactor/client/src/pages/MeetingAIPage.tsx /opt/hipercool-refactor/cmd/server/httpapi.go 2>&1 | head -10`, (err, stream) => {
    if (err) { console.error(err); return; }
    stream.on('data', d => process.stdout.write(d.toString()));
    stream.stderr.on('data', d => process.stdout.write(d.toString()));
    stream.on('close', () => c.end());
  });
});
c.on('error', e => console.error('SSH error', e.message));
c.connect({ host: '62.171.128.241', port: 22, username: 'root', password: '<SEGREDO_REMOVIDO>', readyTimeout: 30000 });
