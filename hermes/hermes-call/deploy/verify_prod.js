const { Client } = require('ssh2');
const c = new Client();
c.on('ready', () => {
  const cmd = `echo === BUNDLE && curl -s https://hermescall.opus-sem-limites.com.br/ | grep -oE 'index-[A-Za-z0-9_]+\.js' && echo === VIEWS && curl -s https://hermescall.opus-sem-limites.com.br/assets/$(curl -s https://hermescall.opus-sem-limites.com.br/ | grep -oE 'index-[A-Za-z0-9_]+\.js') | grep -oE 'view:"[a-z_-]+"' | sort -u && echo === ATHENA && curl -s https://hermescall.opus-sem-limites.com.br/assets/$(curl -s https://hermescall.opus-sem-limites.com.br/ | grep -oE 'index-[A-Za-z0-9_]+\.js') | grep -c Athena && echo === LABELS && curl -s https://hermescall.opus-sem-limites.com.br/assets/$(curl -s https://hermescall.opus-sem-limites.com.br/ | grep -oE 'index-[A-Za-z0-9_]+\.js') | grep -oE 'Meet com IA|Follow-Up|Base de Conhecimento|Promessas' | sort -u && echo === VERSION && curl -s https://hermescall.opus-sem-limites.com.br/api/version`;
  c.exec(cmd, (err, stream) => {
    if (err) { console.error(err); return; }
    stream.on('data', d => process.stdout.write(d.toString()));
    stream.stderr.on('data', d => process.stdout.write(d.toString()));
    stream.on('close', () => c.end());
  });
});
c.on('error', e => console.error('SSH error', e.message));
c.connect({ host: '62.171.128.241', port: 22, username: 'root', password: '<SEGREDO_REMOVIDO>', readyTimeout: 30000 });
