const { Client } = require('ssh2');
const c = new Client();
c.on('ready', () => {
  c.exec(`echo "=== Tem reactflow? ===" && ls /opt/hipercool-refactor/client/node_modules/reactflow 2>&1 | head -5 && echo "=== package.json tem reactflow? ===" && grep -i 'reactflow' /opt/hipercool-refactor/client/package.json && echo "=== imports do AgentOrchestratorFlow ===" && head -20 /opt/hipercool-refactor/client/src/components/settings/AgentOrchestratorFlow.tsx && echo "=== other reactflow refs ===" && grep -rn 'reactflow' /opt/hipercool-refactor/client/src 2>/dev/null | head -10 && echo "=== Versao do node local ===" && node --version`, (err, stream) => {
    if (err) { console.error(err); return; }
    stream.on('data', d => process.stdout.write(d.toString()));
    stream.stderr.on('data', d => process.stdout.write(d.toString()));
    stream.on('close', () => c.end());
  });
});
c.on('error', e => console.error('SSH error', e.message));
c.connect({ host: '62.171.128.241', port: 22, username: 'root', password: '<SEGREDO_REMOVIDO>', readyTimeout: 30000 });
