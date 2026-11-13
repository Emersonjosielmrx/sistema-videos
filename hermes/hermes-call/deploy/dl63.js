const { Client } = require('ssh2');
const c = new Client();
c.on('ready', () => {
  c.exec(`echo "=== vite.config.ts ===" && cat /opt/hipercool-refactor/client/vite.config.* 2>&1 && echo "=== lazy import App.tsx ===" && grep -B1 -A3 'MeetingAI' /opt/hipercool-refactor/client/src/App.tsx && echo "=== exports em App.tsx ===" && grep 'MeetingAI' /opt/hipercool-refactor/client/src/App.tsx && echo "=== verifica se meeting/index.html tem overlay ===" && curl -s https://hermescall.opus-sem-limitese.com.br/landing/ | grep -i 'meet' | head -10 && echo "=== bundle em producao carrega vite chunks ===" && curl -s https://hermescall.opus-sem-limitese.com.br/ | grep -oE 'index-[A-Za-z0-9]+.js' | head -5`, (err, stream) => {
    if (err) { console.error(err); return; }
    stream.on('data', d => process.stdout.write(d.toString()));
    stream.stderr.on('data', d => process.stdout.write(d.toString()));
    stream.on('close', () => c.end());
  });
});
c.on('error', e => console.error('SSH error', e.message));
c.connect({ host: '62.171.128.241', port: 22, username: 'root', password: '<SEGREDO_REMOVIDO>', readyTimeout: 30000 });
