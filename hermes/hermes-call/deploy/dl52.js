const { Client } = require('ssh2');
const c = new Client();
c.on('ready', () => {
  c.exec(`echo "=== find landing ===" && docker exec hermes-call find / -name "landing" -type d 2>/dev/null | head -10 && echo "=== find /app/client/dist/index.html size ===" && docker exec hermes-call ls -la /app/client/dist/ && echo "=== find index.html ===" && docker exec hermes-call find /app -name "index.html" 2>/dev/null && echo "=== /app/client/dist/landing ===" && docker exec hermes-call ls -la /app/client/dist/landing 2>&1 || echo "no landing" && echo "=== usa SHELL REDIRECT wacalls static dir ===" && docker exec hermes-call ls -la /app/client/dist/ | head -30 && echo "=== file listing do wacalls binary ===" && docker exec hermes-call cat /usr/local/bin/wacalls | head -30 2>&1 || echo "no cat" && echo "=== string no wacalls ===" && docker exec hermes-call strings /usr/local/bin/wacalls 2>&1 | grep -E "landing|static" | head -20`, (err, stream) => {
    if (err) { console.error(err); return; }
    stream.on('data', d => process.stdout.write(d.toString()));
    stream.stderr.on('data', d => process.stdout.write(d.toString()));
    stream.on('close', () => c.end());
  });
});
c.on('error', e => console.error('SSH error', e.message));
c.connect({ host: '62.171.128.241', port: 22, username: 'root', password: '<SEGREDO_REMOVIDO>', readyTimeout: 30000 });
