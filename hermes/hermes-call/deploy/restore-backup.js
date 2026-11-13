#!/usr/bin/env node
/**
 * RESTAURAR BACKUP LOCAL no VPS
 * Checkout do tag de backup, sync sources, rebuild Docker, deploy.
 */
const { execSync } = require('child_process');
const { Client } = require('ssh2');
const fs = require('fs');
const path = require('path');

const TAG = process.argv[2] || 'backup-wt-20260724-1947';
const HOST = '62.171.128.241';
const USER = 'root';
const PASSWORD = '<SEGREDO_REMOVIDO>';

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
  console.log('=== RESTAURAR BACKUP LOCAL: ' + TAG + ' ===\n');

  console.log('[1] checkout do tag em working tree (descartando mudanças locais)...');
  try {
    execSync(`cd /d/hipercool-refactor && git stash push -u -m "pre-restore-${Date.now()}"`, { stdio: 'inherit' });
    execSync(`cd /d/hipercool-refactor && git checkout ${TAG}`, { stdio: 'inherit' });
    console.log('  OK - working tree agora em ' + TAG);
  } catch (e) {
    console.error('  Falha no checkout:', e.message);
    process.exit(1);
  }

  console.log('\n[2] fazendo deploy (sync + build + run)...');
  const c = await connect();
  try {
    const out = await run(c, 'cd /opt/hipercool-refactor && docker ps --filter name=hermes-call --format "{{.Status}}" && echo --- && md5sum /opt/hipercool-refactor/client/src/pages/MeetingAIPage.tsx 2>/dev/null');
    console.log('  VPS antes do sync:');
    console.log(out.split('---').map(s => '    ' + s.trim()).join('\n  '));
  } catch (e) {}

  c.end();
  console.log('\n[3] rodando deploy-docker.js...');
  try {
    execSync('cd /d/hipercool-refactor && node deploy/deploy-docker.js', { stdio: 'inherit' });
  } catch (e) {
    console.error('  Deploy falhou:', e.message);
    process.exit(1);
  }

  console.log('\n[4] verificando prod...');
  const c2 = await connect();
  const bundle = (await run(c2, "curl -s https://hermescall.opus-sem-limites.com.br/ | grep -oE 'index-[A-Za-z0-9_]+\\.js'")).trim();
  const ver = (await run(c2, 'curl -s https://hermescall.opus-sem-limites.com.br/api/version')).trim();
  const athenaCount = (await run(c2, `curl -s https://hermescall.opus-sem-limites.com.br/assets/${bundle} 2>/dev/null | grep -c Athena`)).trim();
  const viewsList = (await run(c2, `curl -s https://hermescall.opus-sem-limites.com.br/assets/${bundle} 2>/dev/null | grep -oE 'view:"[a-z_-]+"' | sort -u`)).trim();
  console.log('  bundle:', bundle);
  console.log('  version:', ver);
  console.log('  Athena count:', athenaCount);
  console.log('  views no bundle:');
  console.log(viewsList.split('\n').map(s => '    ' + s).join('\n'));
  c2.end();

  console.log('\n=== RESTAURAÇÃO COMPLETA ===');
  console.log('Verifique em https://hermescall.opus-sem-limites.com.br/ se está correto.');
}

main().catch(e => { console.error('\nFALHA:', e.message); process.exit(1); });
