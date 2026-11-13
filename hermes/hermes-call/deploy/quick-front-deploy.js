#!/usr/bin/env node
const { Client } = require('ssh2');
const fs = require('fs');
const path = require('path');

const HOST = '62.171.128.241';
const USER = 'root';
const PASSWORD = '<SEGREDO_REMOVIDO>';
const TARBALL = path.resolve(__dirname, '../hermes-dist.tar.gz');
const REMOTE_DIST = '/opt/hermes-call/dist';

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

async function main() {
  console.log('[1] Connecting...');
  const c = await connect();
  console.log('[2] Connected. Opening SFTP...');

  const sftp = await new Promise((res, rej) => c.sftp((e, s) => e ? rej(e) : res(s)));

  console.log('[3] Uploading tarball (' + (fs.statSync(TARBALL).size / 1024 / 1024).toFixed(1) + ' MB)...');
  await new Promise((res, rej) => sftp.fastPut(TARBALL, '/tmp/hermes-dist.tar.gz', e => e ? rej(e) : res()));
  console.log('[4] Upload done. Extracting on VPS...');

  await run(c, `rm -rf ${REMOTE_DIST} && mkdir -p ${REMOTE_DIST} && tar -xzf /tmp/hermes-dist.tar.gz -C ${REMOTE_DIST} && rm /tmp/hermes-dist.tar.gz`);
  console.log('[5] Restarting service...');

  await run(c, 'systemctl restart hermes-call && sleep 5');
  const active = (await run(c, 'systemctl is-active hermes-call')).trim();
  const ver = (await run(c, 'curl -s http://127.0.0.1:8080/api/version')).trim();
  const root = (await run(c, 'curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8080/')).trim();

  console.log('[6] Service:', active);
  console.log('    Version:', ver);
  console.log('    Root (200=UI ok):', root);

  c.end();
  if (active !== 'active') { console.error('FAIL: service not active!'); process.exit(1); }
  console.log('\n=== FRONT DEPLOY OK ===');
}

main().catch(e => { console.error('FAIL:', e.message); process.exit(1); });
