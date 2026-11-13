const { Client } = require('ssh2');
const c = new Client();
c.on('ready', () => {
  c.exec('echo "=== container mount info ===" && docker inspect hermes-call --format "{{json .Mounts}}" && echo "=== wacalls process ===" && pgrep -af wacalls && echo "=== wacalls in host pwd ===" && docker exec hermes-call bash -c "ls -la /app/client/dist/" && echo "=== md5 bundle ===" && docker exec hermes-call md5sum /app/client/dist/assets/index-*.js && echo "=== hash content ===" && docker exec hermes-call bash -c "head -c 200 /app/client/dist/assets/index-*.js" && echo "=== ImageInspect NewBuild ===" && docker image inspect hermes-call:latest --format "{{json .Config.Labels}}" && echo "=== check build cache ===" && ls /var/lib/docker/buildkit/ 2>&1 | head -5', (err, stream) => {
    if (err) { console.error(err); return; }
    stream.on('data', d => process.stdout.write(d.toString()));
    stream.stderr.on('data', d => process.stdout.write(d.toString()));
    stream.on('close', () => c.end());
  });
});
c.on('error', e => console.error('SSH error', e.message));
c.connect({ host: '62.171.128.241', port: 22, username: 'root', password: '<SEGREDO_REMOVIDO>', readyTimeout: 30000 });
