const { Client } = require('ssh2');
const c = new Client();
c.on('ready', () => {
  c.exec(`docker exec hermes-call grep -oE 'meet[a-zA-Z]*|reuniao[a-zA-Z]*|reuniao|Meeting' /app/client/dist/assets/index-DioXPln6.js | sort -u | head -30`, (err, stream) => {
    if (err) { console.error(err); return; }
    stream.on('data', d => process.stdout.write(d.toString()));
    stream.stderr.on('data', d => process.stdout.write(d.toString()));
    stream.on('close', () => c.end());
  });
});
c.on('error', e => console.error('SSH error:', e.message));
c.connect({ host: '62.171.128.241', port: 22, username: 'root', password: '<SEGREDO_REMOVIDO>', readyTimeout: 30000 });
