const { Client } = require('ssh2');
const c = new Client();
c.on('ready', () => {
  c.exec(`echo === BUNDLE_OPUS && curl -s https://hermescall.opus-sem-limites.com.br/ | grep -oE 'index-[A-Za-z0-9_]+\.js' && BUNDLE=$(curl -s https://hermescall.opus-sem-limites.com.br/ | grep -oE 'index-[A-Za-z0-9_]+\.js') && echo === VIEWS && curl -s https://hermescall.opus-sem-limites.com.br/assets/$BUNDLE | grep -oE 'view:"[a-z_-]+"' | sort -u && echo === ATHENA && curl -s https://hermescall.opus-sem-limites.com.br/assets/$BUNDLE | grep -c Athena && echo === LABELS && curl -s https://hermescall.opus-sem-limites.com.br/assets/$BUNDLE | grep -oE 'Meet com IA|Follow-Up|Base de Conhecimento|Promessas' | sort -u && echo === VERSION && curl -s https://hermescall.opus-sem-limites.com.br/api/version`, (err, stream) => {
    if (err) { console.error(err); return; }
    stream.on('data', d => process.stdout.write(d.toString()));
    stream.stderr.on('data', d => process.stdout.write(d.toString()));
    stream.on('close', () => c.end());
  });
});
c.on('error', e => console.error('SSH error', e.message));
c.connect({ host: '62.171.128.241', port: 22, username: 'root', password: '<SEGREDO_REMOVIDO>', readyTimeout: 30000 });
