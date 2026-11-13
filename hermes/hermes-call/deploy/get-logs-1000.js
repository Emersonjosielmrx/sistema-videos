const { Client } = require('ssh2');
const c = new Client();
c.on('ready', () => {
  c.exec('docker logs --tail 1000 hermes-call', (err, stream) => {
    if (err) throw err;
    stream.on('close', () => {
      c.end();
    }).on('data', (data) => {
      process.stdout.write(data.toString());
    }).stderr.on('data', (data) => {
      process.stderr.write(data.toString());
    });
  });
}).connect({
  host: '62.171.128.241',
  port: 22,
  username: 'root',
  password: '<SEGREDO_REMOVIDO>'
});
