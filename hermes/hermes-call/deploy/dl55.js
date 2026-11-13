const { Client } = require('ssh2');
const c = new Client();
c.on('ready', () => {
  c.exec(`echo "=== /opt/hipercool-refactor ===" && ls -la /opt/hipercool-refactor/ 2>&1 | head -20 && echo "=== onde tao os sources ===" && ls /opt/ 2>&1 && echo "=== busca em outro lugar ===" && find / -name "App.tsx" -type f 2>/dev/null | head -10 && echo "=== /root/src ===" && ls /root/ 2>&1 | head -20 && echo "=== git do projeto ===" && find / -name ".git" -type d 2>/dev/null | head -10`, (err, stream) => {
    if (err) { console.error(err); return; }
    stream.on('data', d => process.stdout.write(d.toString()));
    stream.stderr.on('data', d => process.stdout.write(d.toString()));
    stream.on('close', () => c.end());
  });
});
c.on('error', e => console.error('SSH error', e.message));
c.connect({ host: '62.171.128.241', port: 22, username: 'root', password: '<SEGREDO_REMOVIDO>', readyTimeout: 30000 });
