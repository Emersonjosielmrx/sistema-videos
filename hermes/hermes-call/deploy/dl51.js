const { Client } = require('ssh2');
const c = new Client();
c.on('ready', () => {
  c.exec(`echo "=== curl verbose /landing/ ===" && curl -sv https://hermescall.opus-sem-limites.com.br/landing/ 2>&1 | head -25 && echo "=== curl /landing/ direto ===" && curl -sI https://hermescall.opus-sem-limites.com.br/landing/ && echo "=== curl IP direto ===" && curl -sI http://62.171.128.241/landing/ -k && echo "=== curl /landing/ sem slash ===" && curl -sI https://hermescall.opus-sem-limites.com.br/landing`, (err, stream) => {
    if (err) { console.error(err); return; }
    stream.on('data', d => process.stdout.write(d.toString()));
    stream.stderr.on('data', d => process.stdout.write(d.toString()));
    stream.on('close', () => c.end());
  });
});
c.on('error', e => console.error('SSH error', e.message));
c.connect({ host: '62.171.128.241', port: 22, username: 'root', password: '<SEGREDO_REMOVIDO>', readyTimeout: 30000 });
