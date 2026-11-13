const { Client } = require('ssh2');
const c = new Client();
c.on('ready', () => {
  c.exec(`echo === STABLE_BUNDLE && docker run --rm hermes-call:stable sh -c 'md5sum /app/client/dist/assets/index-*.js 2>&1 && grep -oE "index-[A-Za-z0-9_]+\.js" /app/client/dist/index.html 2>&1' && echo === STABLE_PREV_BUNDLE && docker run --rm hermes-call:stable-prev sh -c 'md5sum /app/client/dist/assets/index-*.js 2>&1 && grep -oE "index-[A-Za-z0-9_]+\.js" /app/client/dist/index.html 2>&1' && echo === STABLE_VIEW_HASH && docker run --rm hermes-call:stable sh -c 'grep -c Athena /app/client/dist/assets/index-*.js && grep -oE "view:\"[a-z_-]+\"" /app/client/dist/assets/index-*.js | sort -u | head -30' && echo === STABLE_PREV_VIEWS && docker run --rm hermes-call:stable-prev sh -c 'grep -c Athena /app/client/dist/assets/index-*.js && grep -oE "view:\"[a-z_-]+\"" /app/client/dist/assets/index-*.js | sort -u | head -30'`, (err, stream) => {
    if (err) { console.error(err); return; }
    stream.on('data', d => process.stdout.write(d.toString()));
    stream.stderr.on('data', d => process.stdout.write(d.toString()));
    stream.on('close', () => c.end());
  });
});
c.on('error', e => console.error('SSH error', e.message));
c.connect({ host: '62.171.128.241', port: 22, username: 'root', password: '<SEGREDO_REMOVIDO>', readyTimeout: 30000 });
