const { Client } = require('ssh2');
const c = new Client();
c.on('ready', () => {
  c.exec(`echo "=== Busca arquivos sobre meet/reuniao no código fonte ===" && find /opt/hipercool-refactor -path '*/node_modules' -prune -o -type f \( -name "*.tsx" -o -name "*.ts" -o -name "*.go" -o -name "*.md" \) -print 2>/dev/null | xargs grep -il "meet\|reuniao\|reunião" 2>/dev/null | head -30 && echo "=== commit info ===" && cd /opt/hipercool-refactor && git log --oneline -10 2>&1 && echo "=== git status ===" && git status 2>&1 | head -20 && echo "=== branch ===" && git branch 2>&1`, (err, stream) => {
    if (err) { console.error(err); return; }
    stream.on('data', d => process.stdout.write(d.toString()));
    stream.stderr.on('data', d => process.stdout.write(d.toString()));
    stream.on('close', () => c.end());
  });
});
c.on('error', e => console.error('SSH error', e.message));
c.connect({ host: '62.171.128.241', port: 22, username: 'root', password: '<SEGREDO_REMOVIDO>', readyTimeout: 30000 });
