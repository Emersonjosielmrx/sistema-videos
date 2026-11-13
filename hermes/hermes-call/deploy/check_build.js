const { Client } = require('ssh2');
const c = new Client();
c.on('ready', () => {
  c.exec(`echo === ASSETS_DIST && ls -la /opt/hipercool-refactor/client/dist/assets/ && echo === INDEX_HTML && grep -oE 'index-[A-Za-z0-9_-]+\.js' /opt/hipercool-refactor/client/dist/index.html && echo === INDEX_HTML_LANDING && grep -oE 'index-[A-Za-z0-9_-]+\.js' /opt/hipercool-refactor/client/dist/landing/index.html && echo === MD5_CHECK_NEW && md5sum /opt/hipercool-refactor/client/dist/assets/index-*.js && echo === CONTAINER_DIST && docker exec hermes-call ls -la /app/client/dist/assets/ && echo === CONTAINER_INDEX && docker exec hermes-call cat /app/client/dist/index.html 2>&1 | head -10 && echo === CONTAINER_LANDING_INDEX && docker exec hermes-call cat /app/client/dist/landing/index.html 2>&1 | head -10 && echo === CONTAINER_HASH && docker exec hermes-call md5sum /app/client/dist/assets/index-*.js && echo === CONTAINER_GREP && docker exec hermes-call sh -c 'grep -c MeetingAIPage /app/client/dist/assets/*.js 2>/dev/null || echo NO_MATCH' && echo === SERVED_BUNDLE_HASH && curl -s https://hermescall.opus-sem-limites.com.br/ | grep -oE 'index-[A-Za-z0-9_-]+\.js'`, (err, stream) => {
    if (err) { console.error(err); return; }
    stream.on('data', d => process.stdout.write(d.toString()));
    stream.stderr.on('data', d => process.stdout.write(d.toString()));
    stream.on('close', () => c.end());
  });
});
c.on('error', e => console.error('SSH error', e.message));
c.connect({ host: '62.171.128.241', port: 22, username: 'root', password: '<SEGREDO_REMOVIDO>', readyTimeout: 30000 });
