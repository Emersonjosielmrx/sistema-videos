const { Client } = require('ssh2');
const c = new Client();
c.on('ready', () => {
  c.exec(`docker exec hermes-call grep -c 'MeetingAIPage' /app/client/dist/assets/index-DioXPln6.js; docker exec hermes-call grep -c 'meeting-ai' /app/client/dist/assets/index-DioXPln6.js; docker exec hermes-call grep -c 'meeting' /app/client/dist/assets/index-DioXPln6.js; docker exec hermes-call grep -c 'meet' /app/client/dist/assets/index-DioXPln6.js; docker exec hermes-call grep -c 'Athena' /app/client/dist/assets/index-DioXPln6.js; docker exec hermes-call md5sum /app/client/dist/assets/index-DioXPln6.js; echo "=== verificando source se MeetingAIPage existe ===" && grep -l 'MeetingAIPage' /opt/hipercool-refactor/client/src/pages/*.tsx && echo "=== build/out ===" && ls /opt/build-out/ 2>&1`, (err, stream) => {
    if (err) { console.error(err); return; }
    stream.on('data', d => process.stdout.write(d.toString()));
    stream.stderr.on('data', d => process.stdout.write(d.toString()));
    stream.on('close', () => c.end());
  });
});
c.on('error', e => console.error('SSH error', e.message));
c.connect({ host: '62.171.128.241', port: 22, username: 'root', password: '<SEGREDO_REMOVIDO>', readyTimeout: 30000 });
