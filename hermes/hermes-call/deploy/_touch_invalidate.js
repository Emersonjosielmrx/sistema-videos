// Invalida o cache do Docker build sem usar --no-cache (apt-get update falhou).
// Faz "touch" em todos os .go sob cmd/server e internal, o que altera mtime e
// invalida o passo "COPY . ." no cache do BuildKit.
const { Client } = require('ssh2');
const HOST = '62.171.128.241';
const USER = 'root';
const PASS = 'sW5pgAG9obRu2';
const c = new Client();
c.on('ready', () => {
  c.exec('cd /opt/hipercool-refactor && find cmd internal -name "*.go" -exec touch {} + && echo touched && find cmd/server -name "*.go" | head -3', (err, stream) => {
    if (err) { console.error(err); process.exit(1); }
    stream.on('data', d => process.stdout.write(d));
    stream.on('close', () => c.end());
  });
}).connect({ host: HOST, username: USER, password: PASS });
