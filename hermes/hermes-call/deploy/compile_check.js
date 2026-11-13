#!/usr/bin/env node
/**
 * COMPILE CHECK — valida que o Go compila SEM buildar imagem nem tocar em produção.
 * Envia os .go de cmd/ e internal/ pro /opt/hipercool-refactor da VPS e roda
 * `go build ./...` num container golang efêmero montando o fonte. Não sobe nada.
 *
 * Uso: node compile_check.js
 * Config via env: HERMES_VPS_HOST, HERMES_VPS_USER, HERMES_VPS_PASS
 */
const { Client } = require('ssh2');
const fs = require('fs');
const path = require('path');

const HOST = process.env.HERMES_VPS_HOST || '62.171.128.241';
const USER = process.env.HERMES_VPS_USER || 'root';
const PASSWORD = process.env.HERMES_VPS_PASS || 'sW5pgAG9obRu2';
const ROOT = path.resolve(__dirname, '..');
const REMOTE_SRC = '/opt/hipercool-refactor';
const SYNC_DIRS = ['cmd', 'internal'];
const SYNC_FILES = ['go.mod', 'go.sum'];

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
    else if (/\.go$/i.test(name)) files.push({ local: full, rel });
  }
  return files;
}
async function upload(c, sftp, localDir, remoteRel) {
  const files = walk(localDir);
  const dirs = new Set();
  files.forEach(f => dirs.add(path.dirname(remoteRel + '/' + f.rel)));
  await run(c, 'mkdir -p ' + [...dirs].map(d => "'" + REMOTE_SRC + '/' + d + "'").join(' '));
  const CONC = 8;
  let idx = 0;
  async function worker() {
    while (idx < files.length) {
      const f = files[idx++];
      await new Promise((res, rej) => sftp.fastPut(f.local, REMOTE_SRC + '/' + remoteRel + '/' + f.rel, e => e ? rej(e) : res()));
    }
  }
  await Promise.all(Array.from({ length: Math.min(CONC, files.length) }, worker));
  return files.length;
}

async function main() {
  console.log('=== COMPILE CHECK -> ' + HOST + ' ===\n');
  const c = await connect();
  const sftp = await new Promise((res, rej) => c.sftp((e, s) => e ? rej(e) : res(s)));
  await run(c, 'mkdir -p ' + REMOTE_SRC);

  let total = 0;
  for (const d of SYNC_DIRS) {
    const local = path.join(ROOT, d);
    if (fs.existsSync(local)) total += await upload(c, sftp, local, d);
  }
  for (const f of SYNC_FILES) {
    const local = path.join(ROOT, f);
    if (!fs.existsSync(local)) continue;
    await new Promise((res, rej) => sftp.fastPut(local, REMOTE_SRC + '/' + f, e => e ? rej(e) : res()));
  }
  console.log('[sync] ' + total + ' arquivos .go enviados\n[build] go build ./... num container golang...');

  const out = await run(c, 'cd ' + REMOTE_SRC +
    ' && ( docker run --rm -v ' + REMOTE_SRC + ':/src -w /src golang:1.26-bookworm sh -c ' +
    '"go build ./... 2>&1" ; echo GO_RC:$? )');
  console.log(out.trim());
  c.end();
  if (!/GO_RC:0\b/.test(out)) {
    console.error('\n❌ COMPILAÇÃO FALHOU');
    process.exit(1);
  }
  console.log('\n✅ COMPILA OK');
}
main().catch(e => { console.error('\nFALHA:', e.message); process.exit(1); });
