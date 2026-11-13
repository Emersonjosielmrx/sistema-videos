const { Client } = require('ssh2');
const c = new Client();
c.on('ready', () => {
  c.exec('echo "=== Para o container atual ===" && docker stop hermes-call 2>&1 && docker rm hermes-call 2>&1 && echo "=== Limpa tudo do docker ===" && docker rmi hermes-call:beta 2>&1 && docker rmi hermes-call:stable 2>&1 && echo "=== builder prune all ===" && docker builder prune -af 2>&1 | tail -5 && echo "=== Imagens restantes ===" && docker images "hermes-call" 2>&1', (err, stream) => {
    if (err) { console.error(err); return; }
    stream.on('data', d => process.stdout.write(d.toString()));
    stream.stderr.on('data', d => process.stdout.write(d.toString()));
    stream.on('close', () => c.end());
  });
});
c.on('error', e => console.error('SSH error:', e.message));
c.connect({ host: '62.171.128.241', port: 22, username: 'root', password: '<SEGREDO_REMOVIDO>', readyTimeout: 30000 });
