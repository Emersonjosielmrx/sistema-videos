const { Client } = require('ssh2');
const c = new Client();
c.on('ready', () => {
  c.exec(`echo === INOVARE_BUNDLE_NAME && curl -s https://hermescall.inovareinteligenciaartificial.com/ | grep -oE 'index-[A-Za-z0-9_]+\.js' && echo === INOVARE_INDEXHTML && curl -s https://hermescall.inovareinteligenciaartificial.com/ | head -30 && echo === INOVARE_MEETING_INJECTED && curl -s https://hermescall.inovareinteligenciaartificial.com/assets/$(curl -s https://hermescall.inovareinteligenciaartificial.com/ | grep -oE 'index-[A-Za-z0-9_]+\.js') | grep -oE 'meeting-ai|MeetingAIPage|Meet com IA' | sort -u && echo === INOVARE_LABELS && curl -s https://hermescall.inovareinteligenciaartificial.com/assets/$(curl -s https://hermescall.inovareinteligenciaartificial.com/ | grep -oE 'index-[A-Za-z0-9_]+\.js') | grep -oE 'Meet com IA|Follow-Up|Base de Conhecimento|Promessas|Campanhas' | sort -u`, (err, stream) => {
    if (err) { console.error(err); return; }
    stream.on('data', d => process.stdout.write(d.toString()));
    stream.stderr.on('data', d => process.stdout.write(d.toString()));
    stream.on('close', () => c.end());
  });
});
c.on('error', e => console.error('SSH error', e.message));
c.connect({ host: '62.171.128.241', port: 22, username: 'root', password: '<SEGREDO_REMOVIDO>', readyTimeout: 30000 });
