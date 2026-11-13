const { Client } = require('ssh2');
const c = new Client();
c.on('ready', () => {
  c.exec(`docker run --rm hermes-call:client-only sh -c 'find /app/client/dist -name "*.js" -o -name "*.html" | head -20 && echo === && head -1 /app/client/dist/assets/index-*.js | cut -c1-200 && echo === && echo CHECK_TREESHAKE && grep -c "if (view ===" /app/client/dist/assets/index-*.js && echo === && grep -oE "view === [a-zA-Z-]+" /app/client/dist/assets/index-*.js | sort -u | head -30'`, (err, stream) => {
    if (err) { console.error(err); return; }
    stream.on('data', d => process.stdout.write(d.toString()));
    stream.stderr.on('data', d => process.stdout.write(d.toString()));
    stream.on('close', () => c.end());
  });
});
c.on('error', e => console.error('SSH error', e.message));
c.connect({ host: '62.171.128.241', port: 22, username: 'root', password: '<SEGREDO_REMOVIDO>', readyTimeout: 60000 });
