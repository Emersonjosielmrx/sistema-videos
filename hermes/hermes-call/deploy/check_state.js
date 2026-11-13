const { Client } = require('ssh2');
const c = new Client();
c.on('ready', () => {
  c.exec(`echo === ACTIVE && docker ps --filter name=hermes-call --format "{{.Status}}" && echo === IMAGE && docker inspect hermes-call --format "{{.Config.Image}}" 2>/dev/null && echo === BUNDLE && curl -s http://127.0.0.1:8080/ | grep -oE 'index-[A-Za-z0-9_]+' | head -1 && echo === MD5 && md5sum /opt/hipercool-refactor/client/src/pages/MeetingAIPage.tsx`, (err, stream) => {
    if (err) { console.error(err); return; }
    stream.on('data', d => process.stdout.write(d.toString()));
    stream.stderr.on('data', d => process.stdout.write(d.toString()));
    stream.on('close', () => c.end());
  });
});
c.on('error', e => console.error('SSH error', e.message));
c.connect({ host: '62.171.128.241', port: 22, username: 'root', password: '<SEGREDO_REMOVIDO>', readyTimeout: 30000 });
