const { Client } = require('ssh2');
const c = new Client();
c.on('ready', () => {
  c.exec(`echo "=== rotas no App.tsx ===" && grep -A1 'path=' /opt/hipercool-refactor/client/src/App.tsx | head -40 && echo "=== meeting navigation ===" && grep -i 'meet' /opt/hipercool-refactor/client/src/stores/navigation.ts | head -10 && echo "=== bundle tem MeetingAIPage? ===" && docker exec hermes-call grep -l 'MeetingAIPage\|Meeting' /app/client/dist/assets/index-DioXPln6.js | head -5 && echo "=== caracteres de Meeting no bundle ===" && docker exec hermes-call grep -c 'Meeting' /app/client/dist/assets/index-DioXPln6.js && echo "=== catalogo de strings de meeting no bundle ===" && docker exec hermes-call grep -oE '[A-Z][a-zA-Z]{2,30}Meeting[A-Z][a-zA-Z]{0,30}' /app/client/dist/assets/index-DioXPln6.js | sort -u | head -30 && echo "=== busca rotas meeting ===" && docker exec hermes-call grep -oE '"/meeting[a-zA-Z]*"|"/meet[a-zA-Z]*"' /app/client/dist/assets/index-DioXPln6.js | sort -u | head -20`, (err, stream) => {
    if (err) { console.error(err); return; }
    stream.on('data', d => process.stdout.write(d.toString()));
    stream.stderr.on('data', d => process.stdout.write(d.toString()));
    stream.on('close', () => c.end());
  });
});
c.on('error', e => console.error('SSH error', e.message));
c.connect({ host: '62.171.128.241', port: 22, username: 'root', password: '<SEGREDO_REMOVIDO>', readyTimeout: 30000 });
