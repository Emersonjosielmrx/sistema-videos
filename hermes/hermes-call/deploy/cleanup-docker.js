#!/usr/bin/env node
/**
 * Limpa imagens Docker antigas do hermes-call na VPS.
 * Mantém apenas: :beta, :stable, :stable-prev
 */

const { Client } = require('ssh2');
const path = require('path');
const fs = require('fs');

function envFromDeploy(key) {
  const p = path.join(__dirname, '.env.deploy');
  if (fs.existsSync(p)) {
    for (const line of fs.readFileSync(p, 'utf8').split('\n')) {
      const m = line.match(new RegExp('^\\s*' + key + '\\s*=\\s*(.+?)\\s*$'));
      if (m) return m[1];
    }
  }
  return process.env[key] || '';
}

const HOST = envFromDeploy('HERMES_VPS_HOST') || process.env.HERMES_VPS_HOST || '62.171.128.241';
const USER = envFromDeploy('HERMES_VPS_USER') || process.env.HERMES_VPS_USER || 'root';
const PASSWORD = envFromDeploy('HERMES_VPS_PASS') || process.env.HERMES_VPS_PASS || 'sW5pgAG9obRu2';

const KEEP_TAGS = new Set(['beta', 'stable', 'stable-prev']);

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
  console.log('=== CLEANUP Docker images hermes-call @ ' + HOST + ' ===\n');
  const c = await connect();

  const raw = (await run(c, "docker images 'hermes-call' --format '{{.Repository}}:{{.Tag}}  {{.ID}}'")).trim();
  if (!raw) {
    console.log('Nenhuma imagem hermes-call encontrada.');
    c.end();
    return;
  }

  console.log('Imagens encontradas:');
  const lines = raw.split('\n');
  const toRemove = [];

  for (const line of lines) {
    const [fullTag, id] = line.trim().split(/\s+/);
    const tag = fullTag.replace('hermes-call:', '');
    const keep = KEEP_TAGS.has(tag);
    console.log('  ' + (keep ? 'KEEP' : ' DEL') + '  ' + fullTag + '  (' + id + ')');
    if (!keep) toRemove.push(fullTag);
  }

  if (toRemove.length === 0) {
    console.log('\nNada pra limpar — todas as imagens são necessárias.');
    c.end();
    return;
  }

  console.log('\nRemovendo ' + toRemove.length + ' imagens antigas...');
  for (const img of toRemove) {
    const out = (await run(c, 'docker rmi ' + img + ' 2>&1')).trim();
    console.log('  ' + img + ': ' + (out.includes('Untagged') || out.includes('Deleted') ? 'OK' : out));
  }

  // Limpar imagens dangling
  await run(c, 'docker image prune -f 2>/dev/null');

  console.log('\nImagens restantes:');
  const after = (await run(c, "docker images 'hermes-call' --format '{{.Repository}}:{{.Tag}}  {{.ID}}  {{.CreatedSince}}'")).trim();
  console.log(after);

  c.end();
  console.log('\n=== CLEANUP OK ===');
}

main().catch(e => { console.error('\nFALHA:', e.message); process.exit(1); });
