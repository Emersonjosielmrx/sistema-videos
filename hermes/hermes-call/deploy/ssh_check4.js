const { Client } = require('ssh2');
const c = new Client();
c.on('ready', () => {
  c.exec('echo "=== /hermes-call/ no VPS ===" && ls -la /hermes-call/ 2>&1 | head -20 && echo "=== Logs do build (procura) ===" && find / -name "*.log" -newer /tmp -mtime -1 2>/dev/null | head -10 && echo "=== /tmp/deploy* ===" && ls -la /tmp/ 2>&1 | head -20 && echo "=== ps -ef | grep deploy/build ===" && ps -ef 2>&1 | grep -iE "deploy|build|node" | head -10 && echo "=== top -b -n 1 ===" && top -b -n 1 2>&1 | head -20', (err, stream) => {
    if (err) { console.error(err); return; }
    stream.on('data', d => process.stdout.write(d.toString()));
    stream.stderr.on('data', d => process.stdout.write(d.toString()));
    stream.on('close', () => c.end());
  });
});
c.on('error', e => console.error('SSH error:', e.message));
c.connect({ host: '62.171.128.241', port: 22, username: 'root', password: '<SEGREDO_REMOVIDO>', readyTimeout: 30000 });
