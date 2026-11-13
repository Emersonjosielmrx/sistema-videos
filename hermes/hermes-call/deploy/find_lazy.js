const { Client } = require('ssh2');
const c = new Client();
c.on('ready', () => {
  c.exec(`echo === APP_TSX_MEETING_CONTEXT && grep -B5 -A5 'MeetingAI' /opt/hipercool-refactor/client/src/App.tsx && echo === && grep -B2 -A2 'meeting' /opt/hipercool-refactor/client/src/App.tsx && echo === ROUTER_USAGE && grep -B2 -A4 'View.*meeting' /opt/hipercool-refactor/client/src/App.tsx | head -30 && echo === ENV_BUILD && echo "verifica se tem .env.production" && ls /opt/hipercool-refactor/client/.env* 2>&1 && echo === && echo "tsconfig compiler" && cat /opt/hipercool-refactor/client/tsconfig.json 2>&1 && echo === && echo "tsconfig.node" && cat /opt/hipercool-refactor/client/tsconfig.node.json 2>&1`, (err, stream) => {
    if (err) { console.error(err); return; }
    stream.on('data', d => process.stdout.write(d.toString()));
    stream.stderr.on('data', d => process.stdout.write(d.toString()));
    stream.on('close', () => c.end());
  });
});
c.on('error', e => console.error('SSH error', e.message));
c.connect({ host: '62.171.128.241', port: 22, username: 'root', password: '<SEGREDO_REMOVIDO>', readyTimeout: 30000 });
