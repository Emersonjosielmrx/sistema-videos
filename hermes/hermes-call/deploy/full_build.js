const { Client } = require('ssh2');
const c = new Client();
c.on('ready', () => {
  c.exec(`docker run --rm -v /opt/hipercool-refactor/client/src:/app/client/src -v /opt/hipercool-refactor/client/package.json:/app/client/package.json -v /opt/hipercool-refactor/client/package-lock.json:/app/client/package-lock.json -v /opt/hipercool-refactor/client/public:/app/client/public -v /opt/hipercool-refactor/client/index.html:/app/client/index.html -v /opt/hipercool-refactor/client/vite.config.ts:/app/client/vite.config.ts -v /opt/hipercool-refactor/client/tsconfig.json:/app/client/tsconfig.json -v /opt/hipercool-refactor/client/tsconfig.node.json:/app/client/tsconfig.node.json -v /opt/hipercool-refactor/client/tailwind.config.ts:/app/client/tailwind.config.ts -v /opt/hipercool-refactor/client/postcss.config.js:/app/client/postcss.config.js -v /opt/hipercool-refactor/client/components.json:/app/client/components.json -w /app/client node:24-bookworm sh -c "npm ci 2>&1 | tail -5 && npm run build 2>&1 | tail -50"`, (err, stream) => {
    if (err) { console.error(err); return; }
    stream.on('data', d => process.stdout.write(d.toString()));
    stream.stderr.on('data', d => process.stdout.write(d.toString()));
    stream.on('close', () => c.end());
  });
});
c.on('error', e => console.error('SSH error:', e.message));
c.connect({ host: '62.171.128.241', port: 22, username: 'root', password: '<SEGREDO_REMOVIDO>', readyTimeout: 300000 });
