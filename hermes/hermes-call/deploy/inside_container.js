const { Client } = require('ssh2');
const c = new Client();
c.on('ready', () => {
  c.exec(`echo === CONTAINER_SRC_MEETING && docker exec hermes-call ls -la /app/client/src/pages/MeetingAIPage.tsx 2>&1; echo === CONTAINER_SRC_APP && docker exec hermes-call ls -la /app/client/src/App.tsx 2>&1; echo === CONTAINER_DIST_LISTING && docker exec hermes-call ls -la /app/client/dist/ 2>&1; echo === CONTAINER_DIST_ASSETS && docker exec hermes-call ls -la /app/client/dist/assets/ 2>&1; echo === CONTAINER_INDEX_HTML && docker exec hermes-call cat /app/client/dist/index.html 2>&1 | head -15; echo === CONTAINER_MEETING_IN_DIST && docker exec hermes-call grep -c MeetingAIPage /app/client/dist/assets/*.js 2>&1; echo === CONTAINER_FUNIL_IN_DIST && docker exec hermes-call grep -c Kanban /app/client/dist/assets/*.js 2>&1; echo === CONTAINER_REACTFLOW && docker exec hermes-call grep -c reactflow /app/client/dist/assets/*.js 2>&1`, (err, stream) => {
    if (err) { console.error(err); return; }
    stream.on('data', d => process.stdout.write(d.toString()));
    stream.stderr.on('data', d => process.stdout.write(d.toString()));
    stream.on('close', () => c.end());
  });
});
c.on('error', e => console.error('SSH error', e.message));
c.connect({ host: '62.171.128.241', port: 22, username: 'root', password: '<SEGREDO_REMOVIDO>', readyTimeout: 60000 });
