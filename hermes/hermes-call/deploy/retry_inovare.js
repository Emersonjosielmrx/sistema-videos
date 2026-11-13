const { Client } = require('ssh2');
const c = new Client();
c.on('ready', () => {
  console.log('CONNECTED');
  c.exec('echo HELLO && hostname && pwd', (err, stream) => {
    stream.on('data', d => console.log(d.toString()));
    stream.stderr.on('data', d => console.log(d.toString()));
    stream.on('close', () => c.end());
  });
});
c.on('error', e => console.error('ERR', e.message));
c.on('debug', info => console.log('DEBUG', JSON.stringify(info)));
c.connect({ host: '209.145.60.53', port: 22, username: 'root', password: '<SEGREDO_REMOVIDO>', readyTimeout: 30000, debug: (info) => process.stderr.write('DEBUG: ' + JSON.stringify(info) + '\n') });
