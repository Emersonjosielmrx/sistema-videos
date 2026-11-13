const { Client } = require('ssh2');
const c = new Client();
c.on('ready', () => {
  c.exec(`echo === STABLE_DIST_FILES && docker run --rm --entrypoint sh hermes-call:stable -c 'ls -la /app/client/dist/assets/ 2>&1' && echo === STABLE_HASH && docker run --rm --entrypoint sh hermes-call:stable -c 'md5sum /app/client/dist/assets/*.js 2>&1' && echo === STABLE_BUNDLE_NAME && docker run --rm --entrypoint sh hermes-call:stable -c 'grep -oE "index-[A-Za-z0-9_]+" /app/client/dist/index.html 2>&1' && echo === STABLE_VIEWS && docker run --rm --entrypoint sh hermes-call:stable -c 'grep -oE "view:[\\\\\"][a-z_-]+" /app/client/dist/assets/index-*.js 2>&1 | sort -u' && echo === STABLE_ATHENA && docker run --rm --entrypoint sh hermes-call:stable -c 'grep -c Athena /app/client/dist/assets/index-*.js 2>&1' && echo === STABLE_PREV_DIST && docker run --rm --entrypoint sh hermes-call:stable-prev -c 'ls -la /app/client/dist/assets/ 2>&1' && echo === STABLE_PREV_HASH && docker run --rm --entrypoint sh hermes-call:stable-prev -c 'md5sum /app/client/dist/assets/*.js 2>&1' && echo === STABLE_PREV_ATHENA && docker run --rm --entrypoint sh hermes-call:stable-prev -c 'grep -c Athena /app/client/dist/assets/index-*.js 2>&1'`, (err, stream) => {
    if (err) { console.error(err); return; }
    stream.on('data', d => process.stdout.write(d.toString()));
    stream.stderr.on('data', d => process.stdout.write(d.toString()));
    stream.on('close', () => c.end());
  });
});
c.on('error', e => console.error('SSH error', e.message));
c.connect({ host: '62.171.128.241', port: 22, username: 'root', password: '<SEGREDO_REMOVIDO>', readyTimeout: 60000 });
