const { Client } = require('ssh2');
const c = new Client();
c.on('ready', () => {
  c.exec('echo "=== /tmp/hcsrc ===" && ls -la /tmp/hcsrc 2>&1 | head -3 && echo "=== /opt/hermes-call ===" && ls -la /opt/hermes-call 2>&1 | head -3 && echo "=== find / -name Dockerfile -path *hermes* 2>/dev/null ===" && find / -name "Dockerfile" -newer /tmp -mtime -2 2>/dev/null | head -5 && echo "=== find / -name deploy-beta.js 2>/dev/null ===" && find / -name "deploy-beta.js" 2>/dev/null | head -3 && echo "=== /root/.bash_history ===" && tail -30 /root/.bash_history 2>&1 | head -30', (err, stream) => {
    if (err) { console.error(err); return; }
    stream.on('data', d => process.stdout.write(d.toString()));
    stream.stderr.on('data', d => process.stdout.write(d.toString()));
    stream.on('close', () => c.end());
  });
});
c.on('error', e => console.error('SSH error:', e.message));
c.connect({ host: '62.171.128.241', port: 22, username: 'root', password: '<SEGREDO_REMOVIDO>', readyTimeout: 30000 });
