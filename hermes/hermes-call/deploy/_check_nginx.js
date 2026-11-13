const { Client } = require('ssh2');
const c = new Client();
c.on('ready', () => {
  c.exec('ls /opt/hermes-call/dist/ 2>&1 | head -20; echo "==="; cat /opt/hermes-call/dist/index.html 2>&1 | head -5; echo "==="; ls -la /opt/hermes-call/ 2>&1', (err, stream) => {
    let out = '';
    stream.on('data', d => out += d.toString());
    stream.stderr.on('data', d => out += d.toString());
    stream.on('close', () => { console.log(out); c.end(); });
  });
});
c.on('error', e => { console.error(e); process.exit(1); });
c.connect({ host: '62.171.128.241', port: 22, username: 'root', password: '<SEGREDO_REMOVIDO>' });
