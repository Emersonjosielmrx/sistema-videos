const { Client } = require('ssh2');
const c = new Client();
c.on('ready', () => {
  c.exec(`echo === OPUS_VIEWS && grep -oE 'view:"[a-z_-]+"' /opt/hipercool-refactor/client/dist/assets/index-DioXPln6.js | sort -u; echo === OPUS_VIEW_BUTTONS && grep -oE 'view:"[a-z_-]+"' /opt/hipercool-refactor/client/dist/assets/index-DioXPln6.js | sort -u | head -40; echo === OPUS_VIEWS_COMPLETE && grep -oE 'meeting-ai|cost|crm|funnel|know|recordings|agenda|follow_up' /opt/hipercool-refactor/client/dist/assets/index-DioXPln6.js | sort -u`, (err, stream) => {
    if (err) { console.error(err); return; }
    stream.on('data', d => process.stdout.write(d.toString()));
    stream.stderr.on('data', d => process.stdout.write(d.toString()));
    stream.on('close', () => c.end());
  });
});
c.on('error', e => console.error('SSH error', e.message));
c.connect({ host: '62.171.128.241', port: 22, username: 'root', password: '<SEGREDO_REMOVIDO>', readyTimeout: 30000 });
