const { Client } = require('ssh2');
const c = new Client();
c.on('ready', () => {
  const cmd = `docker logs hermes-call 2>&1 | wc -l; echo '---all---'; docker logs hermes-call 2>&1 | tail -40`;
  c.exec(cmd, (err, stream) => {
    if (err) { console.error(err); return; }
    stream.on('close', () => c.end()).on('data', d => process.stdout.write(d.toString()));
    stream.stderr.on('data', d => process.stderr.write(d.toString()));
  });
}).connect({host: '62.171.128.241', port: 22, username: 'root', password: '<SEGREDO_REMOVIDO>'});
