const { Client } = require('ssh2');
const fs = require('fs');
const crypto = require('crypto');
const { execSync } = require('child_process');

const localFiles = [
  'client/src/App.tsx',
  'client/src/components/ErrorBoundary.tsx',
  'client/src/pages/MeetingAIPage.tsx',
  'client/src/pages/RecordingsPage.tsx',
  'client/src/pages/TranscriptsPage.tsx',
  'client/src/lib/log.ts',
  'client/index.html',
  'client/vite.config.js',
  'client/vite.config.ts',
  'client/package.json',
];

const c = new Client();
c.on('ready', () => {
  c.exec('echo "=== VPS md5 ===" && md5sum /opt/hipercool-refactor/client/src/App.tsx /opt/hipercool-refactor/client/src/components/ErrorBoundary.tsx /opt/hipercool-refactor/client/src/pages/MeetingAIPage.tsx /opt/hipercool-refactor/client/src/pages/RecordingsPage.tsx /opt/hipercool-refactor/client/src/pages/TranscriptsPage.tsx /opt/hipercool-refactor/client/src/lib/log.ts /opt/hipercool-refactor/client/index.html /opt/hipercool-refactor/client/vite.config.js /opt/hipercool-refactor/client/vite.config.ts /opt/hipercool-refactor/client/package.json 2>&1', (err, stream) => {
    if (err) { console.error(err); return; }
    stream.on('data', d => process.stdout.write(d.toString()));
    stream.stderr.on('data', d => process.stdout.write(d.toString()));
    stream.on('close', () => {
      console.log('\n=== LOCAL md5 ===');
      for (const f of localFiles) {
        const p = '/d/hipercool-refactor/' + f;
        if (fs.existsSync(p)) {
          const md5 = crypto.createHash('md5').update(fs.readFileSync(p)).digest('hex');
          console.log(md5 + '  ' + f);
        } else {
          console.log('MISSING ' + f);
        }
      }
      c.end();
    });
  });
});
c.on('error', e => console.error('SSH error:', e.message));
c.connect({ host: '62.171.128.241', port: 22, username: 'root', password: '<SEGREDO_REMOVIDO>', readyTimeout: 30000 });
