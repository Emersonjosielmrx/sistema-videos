const { Client } = require('ssh2');
const c = new Client();
c.on('ready', () => {
  c.exec(`ls /opt/hipercool-refactor/client/src/ 2>&1 && echo "=== pages ===" && ls /opt/hipercool-refactor/client/src/pages/ 2>&1 && echo "=== count files ===" && find /opt/hipercool-refactor/client/src -name '*.tsx' -o -name '*.ts' 2>/dev/null | wc -l && echo "=== busca meet em client/src ===" && grep -rli 'meet' /opt/hipercool-refactor/client/src 2>/dev/null | head -10 && echo "=== busca reuniao ===" && grep -rli 'reuniao' /opt/hipercool-refactor/client/src 2>/dev/null | head -10 && echo "=== App.tsx routes ===" && cat /opt/hipercool-refactor/client/src/App.tsx 2>&1 | grep -iE 'meet|route|path' | head -30`, (err, stream) => {
    if (err) { console.error(err); return; }
    stream.on('data', d => process.stdout.write(d.toString()));
    stream.stderr.on('data', d => process.stdout.write(d.toString()));
    stream.on('close', () => c.end());
  });
});
c.on('error', e => console.error('SSH error', e.message));
c.connect({ host: '62.171.128.241', port: 22, username: 'root', password: '<SEGREDO_REMOVIDO>', readyTimeout: 30000 });
