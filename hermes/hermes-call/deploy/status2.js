const { Client } = require('ssh2');
const c = new Client();
c.on('ready', () => {
  c.exec('echo "=== assets ===" && docker exec hermes-call ls -la /app/client/dist/assets/ 2>&1 | head -10 && echo "=== meeting bundle ===" && docker exec hermes-call bash -c "ls /app/client/dist/assets/index-*.js && echo --- && grep -c MeetingAIPage /app/client/dist/assets/index-*.js && echo --- && grep -c meeting-ai /app/client/dist/assets/index-*.js && echo --- && grep -c Athena /app/client/dist/assets/index-*.js && echo --- && grep -c meeting /app/client/dist/assets/index-*.js" 2>&1', (err, stream) => {
    if (err) { console.error(err); return; }
    stream.on('data', d => process.stdout.write(d.toString()));
    stream.stderr.on('data', d => process.stdout.write(d.toString()));
    stream.on('close', () => c.end());
  });
});
c.on('error', e => console.error('SSH error:', e.message));
c.connect({ host: '62.171.128.241', port: 22, username: 'root', password: '<SEGREDO_REMOVIDO>', readyTimeout: 30000 });
