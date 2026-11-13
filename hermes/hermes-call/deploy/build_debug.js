const { Client } = require('ssh2');
const c = new Client();
c.on('ready', () => {
  c.exec(`docker run --rm -v /opt/hipercool-refactor/client:/app/client -w /app/client node:24-bookworm sh -c "rm -rf node_modules/.vite dist && npm ci 2>&1 | tail -3 && DEBUG=vite:plugin-react npx vite build 2>&1 | grep -iE 'meeting|reexport|treeshake|tree-shake' | head -40 && echo === && grep -c 'MeetingAIPage' /app/client/dist/assets/index-*.js && echo SIZE_FILE && wc -c /app/client/dist/assets/index-*.js && echo === && head -c 500 /app/client/dist/assets/index-*.js"`, (err, stream) => {
    if (err) { console.error(err); return; }
    stream.on('data', d => process.stdout.write(d.toString()));
    stream.stderr.on('data', d => process.stdout.write(d.toString()));
    stream.on('close', () => c.end());
  });
});
c.on('error', e => console.error('SSH error', e.message));
c.connect({ host: '62.171.128.241', port: 22, username: 'root', password: '<SEGREDO_REMOVIDO>', readyTimeout: 300000 });
