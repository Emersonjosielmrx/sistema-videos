const { Client } = require('ssh2');
const c = new Client();
c.on('ready', () => {
  c.exec(`docker run --rm hermes-call:client-only sh -c 'echo === ALL_MEETING && grep -c -i "meeting" /app/client/dist/assets/index-*.js && echo === ALL_REUNIAO && grep -c -i "reuniao" /app/client/dist/assets/index-*.js && echo === ALL_Ai_agente && grep -c -i "AI agent" /app/client/dist/assets/index-*.js && echo === ALL_ATHENA && grep -c "Athena" /app/client/dist/assets/index-*.js && echo === ALL_REACTFLOW && grep -c "reactflow" /app/client/dist/assets/index-*.js && echo === ALL_VIDEO_HERO && grep -c "Video" /app/client/dist/assets/index-*.js && echo === ALL_EAR && grep -c "Ear" /app/client/dist/assets/index-*.js && echo === ALL_WAKE && grep -c "wakeWord" /app/client/dist/assets/index-*.js && echo === ALL_REACTFLOW_DIST && find /app/client -name "*.css" -exec grep -l reactflow {} \; 2>&1 | head -3 && echo === ALL_NDX && find /app/client/dist -name "*.js" | xargs grep -l -i "meetingai" 2>&1'`, (err, stream) => {
    if (err) { console.error(err); return; }
    stream.on('data', d => process.stdout.write(d.toString()));
    stream.stderr.on('data', d => process.stdout.write(d.toString()));
    stream.on('close', () => c.end());
  });
});
c.on('error', e => console.error('SSH error', e.message));
c.connect({ host: '62.171.128.241', port: 22, username: 'root', password: '<SEGREDO_REMOVIDO>', readyTimeout: 60000 });
