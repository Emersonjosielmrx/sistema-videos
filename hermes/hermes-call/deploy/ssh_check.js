const { Client } = require('ssh2');
const c = new Client();
c.on('ready', () => {
  c.exec('docker ps --format "table {{.Names}}\t{{.Image}}\t{{.CreatedAt}}\t{{.Status}}" && echo "---APP FILES---" && ls -la /app/client/dist/assets/ 2>&1 && echo "---FILE MD5---" && md5sum /app/client/dist/assets/*.js 2>&1 && echo "---FILE DATES---" && stat /app/client/dist/assets/*.js 2>&1 | grep -E "File|Modify" | head -20', (err, stream) => {
    if (err) { console.error(err); return; }
    stream.on('data', d => process.stdout.write(d.toString()));
    stream.stderr.on('data', d => process.stdout.write(d.toString()));
    stream.on('close', () => c.end());
  });
});
c.on('error', e => console.error('SSH error:', e.message));
c.connect({ host: '62.171.128.241', port: 22, username: 'root', password: '<SEGREDO_REMOVIDO>', readyTimeout: 30000 });
