const { Client } = require('ssh2');
const c = new Client();
c.on('ready', () => {
  c.exec('echo "=== Bundle file mod time ===" && stat /app/client/dist/index.html 2>&1 || docker exec hermes-call stat /app/client/dist/index.html && echo "=== assets list ===" && docker exec hermes-call ls -la /app/client/dist/assets/ | head -30 && echo "=== index html head ===" && docker exec hermes-call cat /app/client/dist/index.html | head -50 && echo "=== Busca funcao meet na bundle ===" && docker exec hermes-call grep -l "Meet\|meet\|reuniao" /app/client/dist/assets/*.{js,css} 2>/dev/null | head -10 && echo "=== busca meet no código fonte ===" && find /opt/hipercool-refactor -path '*/node_modules' -prune -o -name "*.tsx" -print -o -name "*.ts" -print 2>/dev/null | xargs grep -l -i "meet\|reuniao" 2>/dev/null | head -20', (err, stream) => {
    if (err) { console.error(err); return; }
    stream.on('data', d => process.stdout.write(d.toString()));
    stream.stderr.on('data', d => process.stdout.write(d.toString()));
    stream.on('close', () => c.end());
  });
});
c.on('error', e => console.error('SSH error:', e.message));
c.connect({ host: '62.171.128.241', port: 22, username: 'root', password: '<SEGREDO_REMOVIDO>', readyTimeout: 30000 });
