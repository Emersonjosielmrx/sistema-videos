const { Client } = require('ssh2');
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

const HOST = '62.171.128.241';
const USER = 'root';
const PASSWORD = '<SEGREDO_REMOVIDO>';

const ROOT = 'D:/hipercool-refactor';
const REMOTE_SRC = '/opt/hipercool-refactor';

const SYNC_DIRS = ['cmd', 'internal', 'client/src', 'client/public', 'native', 'passkey-extension'];
const SYNC_FILES = [
  'go.mod', 'go.sum', 'Dockerfile', '.dockerignore',
  'client/package.json', 'client/package-lock.json', 'client/index.html',
  'client/vite.config.ts', 'client/tsconfig.json', 'client/tsconfig.node.json',
  'client/tailwind.config.ts', 'client/postcss.config.js', 'client/components.json',
];

function connect() {
  return new Promise((res, rej) => {
    const c = new Client();
    c.on('ready', () => res(c));
    c.on('error', rej);
    c.connect({ host: HOST, port: 22, username: USER, password: PASSWORD, readyTimeout: 30000 });
  });
}
function run(c, cmd) {
  return new Promise((res, rej) => {
    c.exec(cmd, (err, stream) => {
      if (err) return rej(err);
      let out = '';
      stream.on('data', d => out += d.toString());
      stream.stderr.on('data', d => out += d.toString());
      stream.on('close', () => res(out));
    });
  });
}
function walk(dir, base = '') {
  let files = [];
  for (const name of fs.readdirSync(dir)) {
    if (name === 'node_modules' || name === 'dist' || name === '.git') continue;
    const full = path.join(dir, name);
    const rel = base ? base + '/' + name : name;
    if (fs.statSync(full).isDirectory()) files = files.concat(walk(full, rel));
    else files.push({ local: full, rel });
  }
  return files;
}
function md5(f) {
  return crypto.createHash('md5').update(fs.readFileSync(f)).digest('hex');
}

async function uploadOne(c, sftp, local, remote) {
  return new Promise((res, rej) => sftp.fastPut(local, remote, e => e ? rej(e) : res()));
}

async function main() {
  console.log('=== SYNC RÁPIDO: só envia arquivos que mudaram ===\n');
  const c = await connect();
  const sftp = await new Promise((res, rej) => c.sftp((e, s) => e ? rej(e) : res(s)));
  await run(c, 'mkdir -p ' + REMOTE_SRC);

  // Pega o remote md5sum list
  console.log('[1] Coletando remote md5s...');
  const remoteFiles = await run(c, `find ${REMOTE_SRC}/cmd ${REMOTE_SRC}/internal ${REMOTE_SRC}/client/src ${REMOTE_SRC}/client/public ${REMOTE_SRC}/native ${REMOTE_SRC}/passkey-extension -type f 2>/dev/null | head -10000 | xargs md5sum 2>/dev/null`);
  const remoteMap = new Map();
  remoteFiles.split('\n').forEach(line => {
    const m = line.match(/^(\w+)\s+(.+)$/);
    if (m) remoteMap.set(m[2].replace(REMOTE_SRC + '/', ''), m[1]);
  });
  console.log('  ', remoteMap.size, 'arquivos remotos conhecidos');

  // Coleta local files e seus md5
  let total = 0, uploaded = 0, skipped = 0;
  for (const d of SYNC_DIRS) {
    const local = path.join(ROOT, d);
    if (!fs.existsSync(local)) continue;
    const files = walk(local, d);
    total += files.length;
    for (const f of files) {
      const remoteRel = f.rel.replace(/\\/g, '/');
      const localMd5 = md5(f.local);
      const remoteMd5 = remoteMap.get(remoteRel);
      if (remoteMd5 === localMd5) {
        skipped++;
        continue;
      }
      // Need upload
      const remote = REMOTE_SRC + '/' + remoteRel;
      await run(c, 'mkdir -p ' + path.posix.dirname(remote));
      await uploadOne(c, sftp, f.local, remote);
      uploaded++;
      if (uploaded % 50 === 0) console.log(`  progresso: ${uploaded} enviados, ${skipped} skipped`);
    }
  }

  for (const f of SYNC_FILES) {
    const local = path.join(ROOT, f);
    if (!fs.existsSync(local)) continue;
    const remote = REMOTE_SRC + '/' + f;
    const localMd5 = md5(local);
    const remoteMd5 = remoteMap.get(f);
    if (remoteMd5 === localMd5) { skipped++; continue; }
    await run(c, 'mkdir -p ' + path.posix.dirname(remote));
    await uploadOne(c, sftp, local, remote);
    uploaded++;
  }

  console.log(`\n[sync] total: ${total} | uploaded: ${uploaded} | skipped (mesmo md5): ${skipped}`);
  c.end();
}

main().catch(e => { console.error('\nFALHA:', e.message); process.exit(1); });
