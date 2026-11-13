const { Client } = require('ssh2');
const c = new Client();
c.on('ready', () => {
  c.exec(`npx vite build 2>&1 | tail -30 && echo "=== bundle MeetingAI? ===" && ls -la dist/assets/ && echo "=== verifica meeting ===" && grep -c 'MeetingAI\|MeetingAIPage' dist/assets/index-*.js && echo "=== size check ===" && du -sh dist/`, (err, stream) => {
    if (err) { console.error(err); return; }
    stream.on('data', d => process.stdout.write(d.toString()));
    stream.stderr.on('data', d => process.stdout.write(d.toString()));
    stream.on('close', () => c.end());
  });
});
c.on('error', e => console.error('SSH error', e.message));
c.connect({ host: '62.171.128.241', port: 22, username: 'root', password: '<SEGREDO_REMOVIDO>', readyTimeout: 180000 });
