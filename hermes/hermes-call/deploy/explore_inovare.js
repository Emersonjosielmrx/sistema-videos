const { Client } = require('ssh2');
const c = new Client();
c.on('ready', () => {
  c.exec(`echo === BUNDLE_NAME && curl -s https://hermescall.inovareinteligenciaartificial.com/ | grep -oE 'index-[A-Za-z0-9_]+\\.js' && echo === INOVARE_BUNDLE_HASH && BUNDLE=$(curl -s https://hermescall.inovareinteligenciaartificial.com/ | grep -oE 'index-[A-Za-z0-9_]+\\.js') && curl -s https://hermescall.inovareinteligenciaartificial.com/assets/$BUNDLE | md5sum && echo === SIDE_VIEWS && curl -s https://hermescall.inovareinteligenciaartificial.com/assets/$BUNDLE | grep -oE 'view:"[a-z_-]+"' | sort -u && echo === VERSION && curl -s https://hermescall.inovareinteligenciaartificial.com/api/version && echo === === && echo === SOURCE_DIR && ls /opt/hipercool-refactor/client/src/pages/ 2>&1 | head -30 && echo === SOURCE_MTIMES && stat -c '%y %n' /opt/hipercool-refactor/client/src/App.tsx /opt/hipercool-refactor/client/src/components/layout/Sidebar.tsx /opt/hipercool-refactor/client/src/pages/MeetingAIPage.tsx 2>&1 && echo === GIT_LAST && cd /opt/hipercool-refactor && git log -1 --format='%H %ai %s' 2>&1 && echo === DOCKER_IMAGES && docker images 2>&1 | head -10`, (err, stream) => {
    if (err) { console.error(err); return; }
    stream.on('data', d => process.stdout.write(d.toString()));
    stream.stderr.on('data', d => process.stdout.write(d.toString()));
    stream.on('close', () => c.end());
  });
});
c.on('error', e => console.error('SSH error', e.message));
c.connect({ host: '209.145.60.53', port: 22, username: 'root', password: '<SEGREDO_REMOVIDO>', readyTimeout: 30000 });
