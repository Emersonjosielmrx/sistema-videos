const { Client } = require('ssh2');
const c = new Client();
c.on('ready', () => {
  c.exec('echo "=== Bundle achado ===" && curl -s -H "Host: hermescall.opus-sem-limitese.com.br" https://hermescall.opus-sem-limites.com.br/ | head -20 && echo "=== Asset 1 ===" && curl -s -o /dev/null -w "code=%{http_code}\n" -H "Host: hermescall.opus-sem-limites.com.br" https://hermescall.opus-sem-limites.com.br/assets/ && echo "=== API version ===" && curl -s https://hermescall.opus-sem-limites.com.br/api/version && echo "" && echo "=== API rawdata ===" && curl -s https://hermescall.opus-sem-limites.com.br/api/rawdata && echo "" && echo "=== Health ===" && curl -s -o /dev/null -w "code=%{http_code}\n" https://hermescall.opus-sem-limites.com.br/api/health', (err, stream) => {
    if (err) { console.error(err); return; }
    stream.on('data', d => process.stdout.write(d.toString()));
    stream.stderr.on('data', d => process.stdout.write(d.toString()));
    stream.on('close', () => c.end());
  });
});
c.on('error', e => console.error('SSH error:', e.message));
c.connect({ host: '62.171.128.241', port: 22, username: 'root', password: '<SEGREDO_REMOVIDO>', readyTimeout: 30000 });
