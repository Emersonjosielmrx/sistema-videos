const { Client } = require('ssh2');
const c = new Client();
c.on('ready', () => {
  c.exec(`docker run --rm -v /opt/hipercool-refactor/client:/app/client -w /app/client node:24-bookworm sh -c "npm ci 2>&1 | tail -3 && npm run build 2>&1 | tail -10 && echo === && md5sum /app/client/dist/assets/index-*.js && grep -c MeetingAIPage /app/client/dist/assets/index-*.js && grep -c reactflow /app/client/dist/assets/index-*.js"`, (err, stream) => {
    if (err) { console.error(err); return; }
    stream.on('data', d => process.stdout.write(d.toString()));
    stream.stderr.on('data', d => process.stdout.write(d.toString()));
    stream.on('close', () => c.end());
  });
});
c.on('error', e => console.error('SSH error', e.message));
c.connect({ host: '62.171.128.241', port: 22, username: 'root', password: '<SEGREDO_REMOVIDO>', readyTimeout: 300000 });
