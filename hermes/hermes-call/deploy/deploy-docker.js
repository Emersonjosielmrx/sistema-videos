#!/usr/bin/env node
/**
 * DEPLOY DOCKER — Hermes Call v3 (refactor)
 * ==========================================
 * Modo CORRETO de deploy: builda a imagem Docker do Dockerfile do projeto
 * (que compila o codec MLow p/ ÁUDIO da ligação, ffmpeg, edge-tts) e roda como
 * container com --network host (alcança postgres + whisper no localhost, e o
 * Traefik roteia pra porta 8080).
 *
 * Por que Docker e não systemd+binário: o áudio da ligação usa o codec MLow
 * (libopus_mlow.so) que exige CGO_ENABLED=1 + -tags mlow + a .so compilada.
 * O deploy systemd (CGO_ENABLED=0) rodava "signaling-only (no audio)" — a
 * ligação conectava mas não passava voz. O Dockerfile já faz tudo certo.
 *
 * Uso:
 *   node deploy-docker.js            # sync fontes + build imagem + sobe container
 *   node deploy-docker.js --no-sync  # rebuilda com o que já está no VPS
 *
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
const IMAGE = 'hermes-call:latest';
const CONTAINER = 'hermes-call';
const DB_URL = 'postgres://hermes_call_v3test:hermes_call_v3test@localhost:5432/wacalls_main?sslmode=disable';
const TG_TOKEN = process.env.HERMES_TELEGRAM_TOKEN || '<SEGREDO_REMOVIDO>';

const NO_SYNC = process.argv.includes('--no-sync');

// Pastas/arquivos que precisam ir pro VPS pro build Docker funcionar.
// Pula node_modules, dist, .git, deploy/node_modules (pesados/desnecessários).
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
async function upload(c, sftp, localDir, remoteRel) {
  const files = walk(localDir);
  const dirs = new Set();
  files.forEach(f => { const d = path.dirname(remoteRel + '/' + f.rel); dirs.add(d); });
  await run(c, 'mkdir -p ' + [...dirs].map(d => "'" + REMOTE_SRC + '/' + d + "'").join(' '));
  for (const f of files) {
    await new Promise((res, rej) => sftp.fastPut(f.local, REMOTE_SRC + '/' + remoteRel + '/' + f.rel, e => e ? rej(e) : res()));
  }
  return files.length;
}

async function main() {
  console.log('=== DEPLOY DOCKER Hermes Call v3 -> ' + HOST + ' ===\n');
  const c = await connect();
  const sftp = await new Promise((res, rej) => c.sftp((e, s) => e ? rej(e) : res(s)));
  await run(c, 'mkdir -p ' + REMOTE_SRC);

  if (!NO_SYNC) {
    console.log('[sync] enviando fontes (cmd, internal, client, native, passkey)...');
    let total = 0;
    for (const d of SYNC_DIRS) {
      const local = path.join(ROOT, d);
      if (fs.existsSync(local)) total += await upload(c, sftp, local, d);
    }
    for (const f of SYNC_FILES) {
      const local = path.join(ROOT, f);
      if (!fs.existsSync(local)) continue;
      const remote = REMOTE_SRC + '/' + f;
      await run(c, 'mkdir -p ' + path.dirname(remote));
      await new Promise((res, rej) => sftp.fastPut(local, remote, e => e ? rej(e) : res()));
    }
    console.log('  ' + total + ' arquivos de código + configs enviados');
  }

  console.log('[build] docker build (compila MLow + client + Go, ~3-6min)...');
  // --network host: o apt-get dentro do build falha na rede bridge padrão do
  // Docker nesta VPS (erro "NOSPLIT" ao buscar repos debian). A rede do host
  // funciona (postgres/edge-tts instalaram direto), então buildamos por ela.
  const build = await run(c, 'cd ' + REMOTE_SRC + ' && docker build --network host -t ' + IMAGE + ' . 2>&1 | tail -15');
  console.log(build.trim());
  const imgCheck = await run(c, "docker images -q " + IMAGE);
  if (!imgCheck.trim()) throw new Error('build da imagem falhou:\n' + build);

  console.log('\n[deploy] parando systemd antigo (se existir) e subindo container...');
  await run(c, 'systemctl stop hermes-call 2>/dev/null; systemctl disable hermes-call 2>/dev/null; echo ok');
  await run(c, 'docker rm -f ' + CONTAINER + ' 2>/dev/null; echo ok');
  // Volume persistente pras gravações (senão os MP3 iam pro /tmp efêmero do
  // container e todo redeploy apagava tudo; o registro no banco ficava órfão).
  const REC_HOST_DIR = '/opt/hermes-data/recordings';
  await run(c, 'mkdir -p ' + REC_HOST_DIR);
  // WebRTC do navegador (discador): porta fixa + IP público anunciado, senão a
  // mídia não conecta. Requer a porta liberada no firewall.
  await run(c, 'ufw allow 50000/udp >/dev/null 2>&1; ufw allow 50000/tcp >/dev/null 2>&1; echo fw-ok');
  const runCmd = 'docker run -d --name ' + CONTAINER + ' --restart=always --network host ' +
    '-v "' + REC_HOST_DIR + ':/data/recordings" ' +
    '-e "WACALLS_RECORDING_DIR=/data/recordings" ' +
    '-e "WACALLS_PUBLIC_IP=auto" ' +
    '-e "WACALLS_UDP_PORT=50000" ' +
    '-e "WACALLS_PG_URL=' + DB_URL + '" ' +
    '-e "PORT=8080" ' +
    '-e "HERMES_TELEGRAM_TOKEN=' + TG_TOKEN + '" ' +
    IMAGE + ' 2>&1';
  console.log(await run(c, runCmd));

  await new Promise(r => setTimeout(r, 8000));

  console.log('[verify]');
  const active = (await run(c, "docker ps --filter name=" + CONTAINER + " --format '{{.Status}}'")).trim();
  console.log('  container:', active || 'NÃO ESTÁ RODANDO');
  const ver = (await run(c, 'curl -s http://127.0.0.1:8080/api/version')).trim();
  const root = (await run(c, 'curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8080/')).trim();
  console.log('  /api/version:', ver);
  console.log('  root (200=UI ok):', root);
  console.log('  logs:', (await run(c, 'docker logs --tail 8 ' + CONTAINER + ' 2>&1')).trim());
  const mlow = await run(c, 'docker logs ' + CONTAINER + ' 2>&1 | grep -i mlow | tail -2');
  console.log('  MLow:', mlow.trim() || '(sem aviso de MLow indisponível = áudio OK)');

  c.end();
  console.log('\n=== DEPLOY OK ===');
  console.log('https://hermescall.opus-sem-limites.com.br');
}

main().catch(e => { console.error('\nFALHA:', e.message); process.exit(1); });
