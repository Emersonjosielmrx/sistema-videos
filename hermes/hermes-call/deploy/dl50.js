const { Client } = require('ssh2');
const c = new Client();
c.on('ready', () => {
  c.exec(`echo "=== Resolvendo DNS ===" && dig hermescall.opus-sem-limites.com.br +short 2>&1 || nslookup hermescall.opus-sem-limites.com.br 2>&1 && echo "=== Resolvendo DNS secundario ===" && dig hermescall.inovareinteligenciaartificial.com +short 2>&1 || nslookup hermescall.inovareinteligenciaartificial.com 2>&1 && echo "=== curl /landing/ headers ===" && curl -sI https://hermescall.opus-sem-limites.com.br/landing/ && echo "=== Server header ===" && curl -s -D - -o /dev/null https://hermescall.opus-sem-limites.com.br/landing/`, (err, stream) => {
    if (err) { console.error(err); return; }
    stream.on('data', d => process.stdout.write(d.toString()));
    stream.stderr.on('data', d => process.stdout.write(d.toString()));
    stream.on('close', () => c.end());
  });
});
c.on('error', e => console.error('SSH error', e.message));
c.connect({ host: '62.171.128.241', port: 22, username: 'root', password: '<SEGREDO_REMOVIDO>', readyTimeout: 30000 });
