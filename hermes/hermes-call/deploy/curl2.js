const { Client } = require('ssh2');
const c = new Client();
c.on('ready', () => {
  c.exec(`echo === OPUS_HASH && curl -s https://hermescall.opus-sem-limites.com.br/assets/index-DioXPln6.js | md5sum && echo === INOVARE_HASH && curl -s https://hermescall.inovareinteligenciaartificial.com/assets/index-BYgTiieN.js | md5sum && echo === OPUS_MEETINGAI && curl -s https://hermescall.opus-sem-limites.com.br/assets/index-DioXPln6.js | grep -c MeetingAIPage && echo === INOVARE_MEETINGAI && curl -s https://hermescall.inovareinteligenciaartificial.com/assets/index-BYgTiieN.js | grep -c MeetingAIPage && echo === OPUS_FOLLOW_UP && curl -s https://hermescall.opus-sem-limites.com.br/assets/index-DioXPln6.js | grep -c FollowUp && echo === INOVARE_FOLLOW_UP && curl -s https://hermescall.inovareinteligenciaartificial.com/assets/index-BYgTiieN.js | grep -c FollowUp && echo === OPUS_KANBAN && curl -s https://hermescall.opus-sem-limites.com.br/assets/index-DioXPln6.js | grep -c Kanban && echo === INOVARE_KANBAN && curl -s https://hermescall.inovareinteligenciaartificial.com/assets/index-BYgTiieN.js | grep -c Kanban`, (err, stream) => {
    if (err) { console.error(err); return; }
    stream.on('data', d => process.stdout.write(d.toString()));
    stream.stderr.on('data', d => process.stdout.write(d.toString()));
    stream.on('close', () => c.end());
  });
});
c.on('error', e => console.error('SSH error', e.message));
c.connect({ host: '62.171.128.241', port: 22, username: 'root', password: '<SEGREDO_REMOVIDO>', readyTimeout: 30000 });
