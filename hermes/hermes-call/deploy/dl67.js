const { Client } = require('ssh2');
const c = new Client();
c.on('ready', () => {
  c.exec(`echo "=== mtime reactflow referencia ===" && grep -B3 -A3 '"reactflow"' /opt/hipercool-refactor/client/package.json && echo "=== listar node_modules top ===" && ls /opt/hipercool-refactor/client/node_modules/ 2>&1 | head -20 && echo "=== count node_modules ===" && ls /opt/hipercool-refactor/client/node_modules/ 2>&1 | wc -l && echo "=== tamanho node_modules ===" && du -sh /opt/hipercool-refactor/client/node_modules/ 2>&1 && echo "=== node_modules em outros lugares ===" && find /opt/hipercool-refactor -name "node_modules" -type d 2>/dev/null | head -5 && echo "=== Tem package-lock? ===" && ls /opt/hipercool-refactor/client/package-lock.json 2>&1 and echo "=== graph links reactflow ===" => grep -l 'reactflow' /opt/hipercool-refactor/client/node_modules/.package-lock.json 2>/dev/null && echo "=== Locked package ===" && grep -A2 'reactflow' /opt/hipercool-refactor/client/package-lock.json 2>&1 | head -20`, (err, stream) => {
    if (err) { console.error(err); return; }
    stream.on('data', d => process.stdout.write(d.toString()));
    stream.stderr.on('data', d => process.stdout.write(d.toString()));
    stream.on('close', () => c.end());
  });
});
c.on('error', e => console.error('SSH error', e.message));
c.connect({ host: '62.171.128.241', port: 22, username: 'root', password: '<SEGREDO_REMOVIDO>', readyTimeout: 30000 });
