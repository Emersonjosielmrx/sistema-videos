const { Client } = require('ssh2');
const c = new Client();
c.on('ready', () => {
  c.exec(`cd /opt/hipercool-refactor && echo "=== git log ===" && git log --oneline -10 2>&1 && echo "=== git branch ===" && git branch 2>&1 && echo "=== busca meet no client src ===" && find client/src -type f 2>/dev/null | xargs grep -l -i 'meet' 2>/dev/null | head -20 && echo "=== busca pages em src ===" && ls client/src/pages/ 2>&1 | head -30 && echo "=== App.tsx routes ===" && grep -E 'route|path' client/src/App.tsx 2>&1 | head -30`, (err, stream) => {
    if (err) { console.error(err); return; }
    stream.on('data', d => process.stdout.write(d.toString()));
    stream.stderr.on('data', d => process.stdout.write(d.toString()));
    stream.on('close', () => c.end());
  });
});
c.on('error', e => console.error('SSH error', e.message));
c.connect({ host: '62.171.128.241', port: 22, username: 'root', password: '<SEGREDO_REMOVIDO>', readyTimeout: 30000 });
