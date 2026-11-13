const { Client } = require('ssh2');
const c = new Client();
c.on('ready', () => {
  c.exec(`docker run --rm --entrypoint sh hermes-call:stable-prev -c "ls -la /app/client/dist/assets/ && echo === && md5sum /app/client/dist/assets/index-*.js && echo === && grep -c Athena /app/client/dist/assets/index-*.js && echo === && grep -c Kanban /app/client/dist/assets/index-*.js && echo === && grep -c -i reactflow /app/client/dist/assets/index-*.js && echo === && grep -oE 'view:.[a-z_-]+.' /app/client/dist/assets/index-*.js | sort -u | head -30 && echo === && grep -oE 'index-[A-Za-z0-9_]+' /app/client/dist/index.html"`, (err, stream) => {
    if (err) { console.error(err); return; }
    stream.on('data', d => process.stdout.write(d.toString()));
    stream.stderr.on('data', d => process.stdout.write(d.toString()));
    stream.on('close', () => c.end());
  });
});
c.on('error', e => console.error('SSH error', e.message));
c.connect({ host: '62.171.128.241', port: 22, username: 'root', password: '<SEGREDO_REMOVIDO>', readyTimeout: 60000 });
