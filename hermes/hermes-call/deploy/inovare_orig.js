const { Client } = require('ssh2');
const c = new Client();
c.on('ready', () => {
  c.exec(`echo === INOVARE_FUNNEL_COUNT && grep -oE 'funil|[Ff]unil' /tmp/inovare.js | sort -u | head -10; echo === INOVARE_MEETINGAI_PRESENT && grep -c 'Athena\|Configurar Athena' /tmp/inovare.js; echo === INOVARE_MEETINGAI_VIEWS && grep -oE 'meeting-ai|MeetingAIPage|setView"meeting-ai"' /tmp/inovare.js | sort -u; echo === INOVARE_ALL_NAV_BUTTONS && grep -oE 'label="[^"]+"' /tmp/inovare.js | sort -u | head -40; echo === INOVARE_VIEW_LIST && grep -oE 'view:"[a-z_-]+"' /tmp/inovare.js | sort -u | head -30`, (err, stream) => {
    if (err) { console.error(err); return; }
    stream.on('data', d => process.stdout.write(d.toString()));
    stream.stderr.on('data', d => process.stdout.write(d.toString()));
    stream.on('close', () => c.end());
  });
});
c.on('error', e => console.error('SSH error', e.message));
c.connect({ host: '62.171.128.241', port: 22, username: 'root', password: '<SEGREDO_REMOVIDO>', readyTimeout: 30000 });
