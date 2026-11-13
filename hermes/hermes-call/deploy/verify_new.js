const { Client } = require('ssh2');
const c = new Client();
c.on('ready', () => {
  const cmd = [
    'echo === INDEX_HTML_BUNDLE',
    "curl -s https://hermescall.opus-sem-limites.com.br/ | grep -oE 'index-[A-Za-z0-9_]+\.js'",
    'echo === NEW_BUNDLE_VIEWS',
    "curl -s https://hermescall.opus-sem-limites.com.br/assets/$(curl -s https://hermescall.opus-sem-limites.com.br/ | grep -oE 'index-[A-Za-z0-9_]+\.js') | grep -oE 'view:\"[a-z_-]+\"' | sort -u",
    'echo === MEETINGAI_IN_BUNDLE',
    "curl -s https://hermescall.opus-sem-limites.com.br/assets/$(curl -s https://hermescall.opus-sem-limites.com.br/ | grep -oE 'index-[A-Za-z0-9_]+\.js') | grep -c -E 'Athena|Meet com IA|meeting-ai'",
    'echo === ATHENA_LABEL',
    "curl -s https://hermescall.opus-sem-limites.com.br/assets/$(curl -s https://hermescall.opus-sem-limites.com.br/ | grep -oE 'index-[A-Za-z0-9_]+\.js') | grep -oE 'Meet com IA|Follow-Up|Base de Conhecimento|Promessas|Campanhas|Listas|Chamada em Massa|Mensagem em Massa|Contatos|Relatórios|Gravações' | sort -u",
  ].join(' && ');
  c.exec(cmd, (err, stream) => {
    if (err) { console.error(err); return; }
    stream.on('data', d => process.stdout.write(d.toString()));
    stream.stderr.on('data', d => process.stdout.write(d.toString()));
    stream.on('close', () => c.end());
  });
});
c.on('error', e => console.error('SSH error', e.message));
c.connect({ host: '62.171.128.241', port: 22, username: 'root', password: '<SEGREDO_REMOVIDO>', readyTimeout: 30000 });
