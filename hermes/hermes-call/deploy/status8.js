const { Client } = require('ssh2');
const c = new Client();
c.on('ready', () => {
  c.exec('echo "=== Stage 1 do build ===" && docker build --target client --network host --no-cache -t hermes-call:client-only /opt/hipercool-refactor/. 2>&1 | tail -10 && echo "=== Inspec client-only ===" && docker run --rm hermes-call:client-only ls -la /app/client/dist/ 2>&1 | head -15 && echo "=== md5 dentro do client-only ===" && docker run --rm hermes-call:client-only md5sum /app/client/dist/assets/index-*.js && echo "=== builda client direto ===" && docker run --rm hermes-call:client-only bash -c "grep -c MeetingAIPage /app/client/dist/assets/index-*.js && grep -c meeting-ai /app/client/dist/assets/index-*.js"', (err, stream) => {
    if (err) { console.error(err); return; }
    stream.on('data', d => process.stdout.write(d.toString()));
    stream.stderr.on('data', d => process.stdout.write(d.toString()));
    stream.on('close', () => c.end());
  });
});
c.on('error', e => console.error('SSH error:', e.message));
c.connect({ host: '62.171.128.241', port: 22, username: 'root', password: '<SEGREDO_REMOVIDO>', readyTimeout: 300000 });
