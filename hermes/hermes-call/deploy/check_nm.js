const { Client } = require('ssh2');
const c = new Client();
c.on('ready', () => {
  c.exec('ls /opt/hipercool-refactor/client/node_modules 2>&1 | head -3 && echo === && ls /opt/hipercool-refactor/client/node_modules/reactflow 2>&1 | head -3 && echo === && ls /opt/hipercool-refactor/client/node_modules/react 2>&1 | head -3 && echo === && stat /opt/hipercool-refactor/client/node_modules | head -5 && echo === && stat /opt/hipercool-refactor/client | head -5', (err, stream) => {
    if (err) { console.error(err); return; }
    stream.on('data', d => process.stdout.write(d.toString()));
    stream.stderr.on('data', d => process.stdout.write(d.toString()));
    stream.on('close', () => c.end());
  });
});
c.on('error', e => console.error('SSH error', e.message));
c.connect({ host: '62.171.128.241', port: 22, username: 'root', password: '<SEGREDO_REMOVIDO>', readyTimeout: 30000 });
