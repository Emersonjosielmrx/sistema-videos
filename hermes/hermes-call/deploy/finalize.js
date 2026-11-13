const { Client } = require('ssh2');
const c = new Client();
c.on('ready', () => {
  c.exec('echo "=== ANTES ===" && docker ps -a --format "table {{.Names}}\t{{.Image}}\t{{.Status}}" && echo "=== Para hermes-call-teste (não é prod) ===" && docker stop hermes-call-teste 2>&1 && docker rm hermes-call-teste 2>&1 && echo "=== Verifica novo id ===" && docker images "hermes-call" --format "table {{.Repository}}:{{.Tag}}\t{{.ID}}\t{{.CreatedAt}}" && echo "=== Substitui :stable pela nova :beta (a0106d9c) ===" && docker rmi hermes-call:stable 2>&1 && docker tag hermes-call:beta hermes-call:stable && echo "=== Remove tags antigas desnecessárias para economizar espaço ===" && docker rmi hermes-call:stable-prev-rollback 2>&1 && echo "=== Estado final ===" && docker images "hermes-call" --format "table {{.Repository}}:{{.Tag}}\t{{.ID}}\t{{.CreatedAt}}" && echo "=== Containers ===" && docker ps -a --format "table {{.Names}}\t{{.Image}}\t{{.Status}}"', (err, stream) => {
    if (err) { console.error(err); return; }
    stream.on('data', d => process.stdout.write(d.toString()));
    stream.stderr.on('data', d => process.stdout.write(d.toString()));
    stream.on('close', () => c.end());
  });
});
c.on('error', e => console.error('SSH error:', e.message));
c.connect({ host: '62.171.128.241', port: 22, username: 'root', password: '<SEGREDO_REMOVIDO>', readyTimeout: 30000 });
