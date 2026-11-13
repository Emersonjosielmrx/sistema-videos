const { Client } = require('ssh2');
const c = new Client();
c.on('ready', () => {
  c.exec(`echo === ALL_DTS_MEETING && find /opt/hipercool-refactor/client/src -name '*.tsx' -o -name '*.ts' | xargs grep -l 'MeetingAIPage\|MeetingPage' 2>/dev/null && echo === USAGE && grep -rn 'MeetingAIPage' /opt/hipercool-refactor/client/src 2>&1 && echo === CHECK_EXPORT && grep -E 'export function MeetingAI' /opt/hipercool-refactor/client/src/pages/MeetingAIPage.tsx && echo === && echo "=== Procurando Meeting no default export ===" && grep -E 'export default' /opt/hipercool-refactor/client/src/pages/MeetingAIPage.tsx && echo === && echo "=== outras páginas ===" && grep -l 'export function' /opt/hipercool-refactor/client/src/pages/*.tsx | head -5 && echo === && echo "=== Como Vite resolve ===" && cd /opt/hipercool-refactor/client && grep -c 'export function MeetingAIPage' /app/client/src/pages/MeetingAIPage.tsx 2>&1 || echo done`, (err, stream) => {
    if (err) { console.error(err); return; }
    stream.on('data', d => process.stdout.write(d.toString()));
    stream.stderr.on('data', d => process.stdout.write(d.toString()));
    stream.on('close', () => c.end());
  });
});
c.on('error', e => console.error('SSH error', e.message));
c.connect({ host: '62.171.128.241', port: 22, username: 'root', password: '<SEGREDO_REMOVIDO>', readyTimeout: 30000 });
