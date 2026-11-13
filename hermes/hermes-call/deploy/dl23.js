const { Client } = require('ssh2');
const c = new Client();
c.on('ready', () => {
  c.exec('echo "=== processo wacalls ===" && ps -fp 1067158 2>&1 || echo "morto" && echo "=== o que tem na 8080 ===" && curl -s http://127.0.0.1:8080/api/version 2>&1 | head -20 && echo "=== Inspect do wacalls ===" && find / -name "wacalls" -type f 2>/dev/null | head -5 && echo "=== Procurando systemd do wacalls ===" && systemctl status wacalls 2>&1 | head -10 || echo "no systemd"', (err, stream) => {
    if (err) { console.error(err); return; }
    stream.on('data', d => process.stdout.write(d.toString()));
    stream.stderr.on('data', d => process.stdout.write(d.toString()));
    stream.on('close', () => c.end());
  });
});
c.on('error', e => console.error('SSH error:', e.message));
c.connect({ host: '62.171.128.241', port: 22, username: 'root', password: '<SEGREDO_REMOVIDO>', readyTimeout: 30000 });
