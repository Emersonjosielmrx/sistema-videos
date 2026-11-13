#!/usr/bin/env node
/**
 * Sync ambient audio files to VPS (deploy-beta.js skips mp3/wav/ogg).
 * Only uploads files with actual content (skips 0-byte placeholders).
 */
const { Client } = require('ssh2');
const fs = require('fs');
const path = require('path');

const HOST = process.env.HERMES_VPS_HOST || '62.171.128.241';
const USER = process.env.HERMES_VPS_USER || 'root';
const PASSWORD = process.env.HERMES_VPS_PASS || 'sW5pgAG9obRu2';

const LOCAL_DIR = path.resolve(__dirname, '..', 'client', 'public', 'audio', 'ambient');
const REMOTE_DIR = '/opt/hipercool-refactor/client/public/audio/ambient';

function walk(dir, base = '') {
  let files = [];
  for (const name of fs.readdirSync(dir)) {
    const full = path.join(dir, name);
    const rel = base ? base + '/' + name : name;
    const stat = fs.statSync(full);
    if (stat.isDirectory()) { files = files.concat(walk(full, rel)); continue; }
    if (stat.size === 0) continue;
    files.push({ local: full, rel, size: stat.size });
  }
  return files;
}

function run(c, cmd) {
  return new Promise((ok, fail) => {
    let out = '';
    c.exec(cmd, (e, ch) => {
      if (e) return fail(e);
      ch.on('data', d => out += d);
      ch.stderr.on('data', d => out += d);
      ch.on('close', () => ok(out.trim()));
    });
  });
}

async function main() {
  const files = walk(LOCAL_DIR);
  console.log(`${files.length} ambient audio files to sync (non-zero)`);
  if (!files.length) return;

  const c = new Client();
  await new Promise((ok, fail) => {
    c.on('ready', ok).on('error', fail)
     .connect({ host: HOST, port: 22, username: USER, password: PASSWORD, readyTimeout: 20000 });
  });

  const sftp = await new Promise((ok, fail) => c.sftp((e, s) => e ? fail(e) : ok(s)));

  const dirs = new Set();
  files.forEach(f => dirs.add(path.dirname(REMOTE_DIR + '/' + f.rel)));
  await run(c, 'mkdir -p ' + [...dirs].map(d => `'${d}'`).join(' '));

  for (const f of files) {
    const remote = REMOTE_DIR + '/' + f.rel;
    await new Promise((ok, fail) =>
      sftp.fastPut(f.local, remote, e => e ? fail(e) : ok()));
    console.log(`  ✓ ${f.rel} (${(f.size / 1024).toFixed(0)}KB)`);
  }

  c.end();
  console.log(`\nDone. Files at ${REMOTE_DIR} on VPS.`);
  console.log('In Docker container they resolve at /app/client/dist/audio/ambient/ (via Dockerfile COPY).');
  console.log('NOTE: Docker image must be rebuilt to include these in the container, OR mount the dir.');
}

main().catch(e => { console.error(e); process.exit(1); });
