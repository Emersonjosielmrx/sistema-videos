const { Client } = require('ssh2');
const c = new Client();
c.on('ready', () => {
  c.exec(`curl -s -o /tmp/opus.js https://hermescall.opus-sem-limites.com.br/assets/index-DioXPln6.js && curl -s -o /tmp/inovare.js https://hermescall.inovareinteligenciaartificial.com/assets/index-BYgTiieN.js && echo === OPUS_HASH && md5sum /tmp/opus.js && echo === INOVARE_HASH && md5sum /tmp/inovare.js && echo === OPUS_SIZE && wc -c /tmp/opus.js && echo === INOVARE_SIZE && wc -c /tmp/inovare.js && echo === OPUS_MEETINGAI && grep -c MeetingAIPage /tmp/opus.js && echo === INOVARE_MEETINGAI && grep -c MeetingAIPage /tmp/inovare.js && echo === OPUS_KANBAN && grep -c Kanban /tmp/opus.js && echo === INOVARE_KANBAN && grep -c Kanban /tmp/inovare.js && echo === OPUS_FUNIL && grep -c funil /tmp/opus.js && echo === INOVARE_FUNIL && grep -c funil /tmp/inovare.js`, (err, stream) => {
    if (err) { console.error(err); return; }
    stream.on('data', d => process.stdout.write(d.toString()));
    stream.stderr.on('data', d => process.stdout.write(d.toString()));
    stream.on('close', () => c.end());
  });
});
c.on('error', e => console.error('SSH error', e.message));
c.connect({ host: '62.171.128.241', port: 22, username: 'root', password: '<SEGREDO_REMOVIDO>', readyTimeout: 60000 });
