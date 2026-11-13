const { Client } = require('ssh2');
const c = new Client();
c.on('ready', () => {
  c.exec('docker tag hermes-call:latest hermes-call:latest-buggy-2026-07-25 2>&1 && echo OK_TAG && docker images | grep latest-buggy', (err, stream) => {
    if (err) { console.error(err); return; }
    stream.on('data', d => process.stdout.write(d.toString()));
    stream.stderr.on('data', d => process.stdout.write(d.toString()));
    stream.on('close', () => c.end());
  });
});
c.on('error', e => console.error('SSH error', e.message));
c.connect({ host: '62.171.128.241', port: 22, username: 'root', password: '<SEGREDO_REMOVIDO>', readyTimeout: 30000 });
