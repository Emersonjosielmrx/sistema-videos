const { Client } = require('ssh2');
const c = new Client();
c.on('ready', () => {
  c.exec(`echo === SIDEBAR_MTIME && stat /opt/hipercool-refactor/client/src/components/layout/Sidebar.tsx && echo === SIDEBAR_HASH && md5sum /opt/hipercool-refactor/client/src/components/layout/Sidebar.tsx && echo === SIDEBAR_VIEWS && grep -oE 'view:[^,]+' /opt/hipercool-refactor/client/src/components/layout/Sidebar.tsx | sort -u; echo === SIDEBAR_LINES && wc -l /opt/hipercool-refactor/client/src/components/layout/Sidebar.tsx`, (err, stream) => {
    if (err) { console.error(err); return; }
    stream.on('data', d => process.stdout.write(d.toString()));
    stream.stderr.on('data', d => process.stdout.write(d.toString()));
    stream.on('close', () => c.end());
  });
});
c.on('error', e => console.error('SSH error', e.message));
c.connect({ host: '62.171.128.241', port: 22, username: 'root', password: '<SEGREDO_REMOVIDO>', readyTimeout: 30000 });
