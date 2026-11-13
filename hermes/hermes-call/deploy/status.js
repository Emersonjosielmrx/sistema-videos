const { Client } = require('ssh2');
const c = new Client();
c.on('ready', () => {
  c.exec('echo "=== docker ps ===" && docker ps --format "{{.Names}}\t{{.Status}}\t{{.Image}}" && echo "=== images ===" && docker images hermes-call --format "{{.Repository}}:{{.Tag}}\t{{.CreatedAt}}\t{{.ID}}" && echo "=== current container bundle ===" && docker exec hermes-call md5sum /app/client/dist/assets/index-*.js 2>&1 && echo "=== build count ===" && docker exec hermes-call wacalls 2>&1 | head -1 || echo "n cmd" && echo "=== api/version ===" && curl -s http://127.0.0.1:8080/api/version && echo "=== meeting no bundle? ===" && docker exec hermes-call grep -c "MeetingAIPage\|Meeting\|meeting-ai" /app/client/dist/assets/index-*.js', (err, stream) => {
    if (err) { console.error(err); return; }
    stream.on('data', d => process.stdout.write(d.toString()));
    stream.stderr.on('data', d => process.stdout.write(d.toString()));
    stream.on('close', () => c.end());
  });
});
c.on('error', e => console.error('SSH error:', e.message));
c.connect({ host: '62.171.128.241', port: 22, username: 'root', password: '<SEGREDO_REMOVIDO>', readyTimeout: 30000 });
