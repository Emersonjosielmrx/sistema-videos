const { Client } = require('ssh2');
const c = new Client();
c.on('ready', () => {
  c.exec(`echo "=== Listar scripts deploy ===" && cd /opt/hipercool-refactor && ls deploy/ 2>&1 | head -10 && echo "=== Show deploy/ contents ===" && ls -la deploy/ 2>&1 && echo "=== Scripts raiz ===" && ls *.js *.sh 2>&1 | head -10 && echo "=== show deploy-beta.js ===" && head -50 deploy/deploy-beta.js 2>&1 || head -50 deploy/deploy.js 2>&1 || echo "no deploy.js"`, (err, stream) => {
    if (err) { console.error(err); return; }
    stream.on('data', d => process.stdout.write(d.toString()));
    stream.stderr.on('data', d => process.stdout.write(d.toString()));
    stream.on('close', () => c.end());
  });
});
c.on('error', e => console.error('SSH error', e.message));
c.connect({ host: '62.171.128.241', port: 22, username: 'root', password: '<SEGREDO_REMOVIDO>', readyTimeout: 30000 });
