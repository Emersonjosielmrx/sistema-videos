#!/usr/bin/env node
/**
 * DEPLOY CANÔNICO — Hermes Call v3 (refactor)
 * ============================================
 * Um comando: sincroniza o código, compila NO VPS (container golang),
 * builda o frontend, instala via systemd e valida.
 *
 * Uso:
 *   node deploy.js               # deploy completo (backend + frontend)
 *   node deploy.js --back-only   # só recompila/reinstala o binário Go
 *   node deploy.js --front-only  # só rebuilda/reenvia o frontend
 *   node deploy.js --no-sync     # não reenvia fontes, só rebuilda o que já está no VPS
 *
 * Por que compilar no VPS: o PC de dev não tem Go instalado. O VPS tem a
 * imagem docker golang:1.26-bookworm, então o build roda lá dentro (isolado,
 * reproduzível). O frontend (vite) é buildado no PC porque precisa de node_modules.
 *
 * Config via env (ou usa os defaults):
 *   HERMES_VPS_HOST (62.171.128.241), HERMES_VPS_USER (root), HERMES_VPS_PASS
 */

const { Client } = require('ssh2');
const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

// ---- Config ----
const HOST = process.env.HERMES_VPS_HOST || '62.171.128.241';
const USER = process.env.HERMES_VPS_USER || 'root';
const PASSWORD = process.env.HERMES_VPS_PASS || 'sW5pgAG9obRu2';

const ROOT = path.resolve(__dirname, '..');
const CLIENT_DIR = path.join(ROOT, 'client');
const DIST_DIR = path.join(CLIENT_DIR, 'dist');

const REMOTE_SRC = '/opt/hipercool-refactor';       // fontes Go no VPS
const REMOTE_APP = '/opt/hermes-call';              // app instalado (systemd)
const REMOTE_BIN = REMOTE_APP + '/hermes-call';
const REMOTE_DIST = REMOTE_APP + '/dist';
const GO_IMAGE = 'golang:1.26-bookworm';

const DB_URL = 'postgres://hermes_call_v3test:hermes_call_v3test@localhost:5432/wacalls_main?sslmode=disable';

const args = process.argv.slice(2);
const BACK_ONLY = args.includes('--back-only');
const FRONT_ONLY = args.includes('--front-only');
const NO_SYNC = args.includes('--no-sync');

// ---- SSH helpers ----
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
function walk(dir, base = '', skip = []) {
  let files = [];
  for (const name of fs.readdirSync(dir)) {
    if (skip.includes(name)) continue;
    const full = path.join(dir, name);
    const rel = base ? base + '/' + name : name;
    if (fs.statSync(full).isDirectory()) files = files.concat(walk(full, rel, skip));
    else files.push({ local: full, rel });
  }
  return files;
}
async function upload(c, sftp, localDir, remoteDir, skip = []) {
  const files = walk(localDir, '', skip);
  const dirs = new Set();
  files.forEach(f => { const d = path.dirname(f.rel); if (d !== '.') dirs.add(d); });
  await run(c, 'mkdir -p ' + remoteDir + ' ' + [...dirs].map(d => remoteDir + '/' + d).join(' '));
  for (const f of files) {
    await new Promise((res, rej) => sftp.fastPut(f.local, remoteDir + '/' + f.rel, e => e ? rej(e) : res()));
  }
  return files.length;
}

// GUARDRAIL anti-contaminação: a versão boa (v0.2.1) se perdeu porque foi
// buildada de um working-tree NÃO commitado. Nunca mais. Todo deploy exige
// git limpo — assim o hash do commit sempre identifica o que está no ar e dá
// pra reconstruir. Fura só com --allow-dirty explícito (última instância).
function assertCleanGitOrDie() {
  const ALLOW_DIRTY = args.includes('--allow-dirty');
  let dirty = '';
  try { dirty = execSync('git status --porcelain', { cwd: ROOT }).toString().trim(); }
  catch (e) { console.warn('[guardrail] git indisponível, pulando checagem:', e.message); return; }
  const head = (() => { try { return execSync('git rev-parse --short HEAD', { cwd: ROOT }).toString().trim(); } catch { return '???????'; } })();
  if (dirty && !ALLOW_DIRTY) {
    console.error('\n╔══════════════════════════════════════════════════════════════╗');
    console.error('║  DEPLOY BLOQUEADO: working-tree sujo (mudanças não commitadas) ║');
    console.error('╚══════════════════════════════════════════════════════════════╝');
    console.error('\nA versão v0.2.1 se perdeu por buildar de código não commitado.');
    console.error('Commite (ou stashe) antes de deployar. Arquivos pendentes:\n');
    console.error(dirty.split('\n').slice(0, 40).join('\n'));
    console.error('\nPara furar mesmo assim (NÃO recomendado): node deploy/deploy.js --allow-dirty');
    process.exit(1);
  }
  console.log('[guardrail] git HEAD=' + head + (dirty ? ' (SUJO — furado com --allow-dirty)' : ' (limpo) ✓'));
  return head;
}

async function main() {
  console.log('=== DEPLOY Hermes Call v3 -> ' + HOST + ' ===\n');

  const gitHead = assertCleanGitOrDie();

  // Frontend build (local, precisa de node_modules)
  if (!BACK_ONLY) {
    console.log('[build] frontend (vite)...');
    execSync('npx vite build', { cwd: CLIENT_DIR, stdio: 'inherit' });
    // Registra o que foi buildado (rastreabilidade: hash do bundle + commit).
    try {
      const assetsDir = path.join(DIST_DIR, 'assets');
      const bundle = fs.readdirSync(assetsDir).find(f => /^index-.*\.js$/.test(f));
      const crypto = require('crypto');
      const md5 = bundle ? crypto.createHash('md5').update(fs.readFileSync(path.join(assetsDir, bundle))).digest('hex') : 'n/a';
      const stamp = new Date().toISOString();
      const line = `${stamp}\tgit=${gitHead || '???'}\tbundle=${bundle || 'n/a'}\tmd5=${md5}\thost=${HOST}\n`;
      fs.appendFileSync(path.join(ROOT, 'deploy', 'BUILD_LEDGER.tsv'), line);
      console.log('[ledger] ' + line.trim());
    } catch (e) { console.warn('[ledger] falhou registrar:', e.message); }
  }

  const c = await connect();
  const sftp = await new Promise((res, rej) => c.sftp((e, s) => e ? rej(e) : res(s)));
  await run(c, 'mkdir -p ' + REMOTE_APP + ' ' + REMOTE_SRC);

  // Sincroniza fontes Go
  if (!FRONT_ONLY && !NO_SYNC) {
    console.log('[sync] enviando fontes Go...');
    const n1 = await upload(c, sftp, path.join(ROOT, 'cmd'), REMOTE_SRC + '/cmd');
    const n2 = await upload(c, sftp, path.join(ROOT, 'internal'), REMOTE_SRC + '/internal');
    for (const f of ['go.mod', 'go.sum']) {
      await new Promise((res, rej) => sftp.fastPut(path.join(ROOT, f), REMOTE_SRC + '/' + f, e => e ? rej(e) : res()));
    }
    console.log('  ' + (n1 + n2) + ' arquivos Go enviados');
  }

  // Compila no container golang
  if (!FRONT_ONLY) {
    console.log('[build] compilando no container ' + GO_IMAGE + '...');
    // Remove o binário antigo ANTES de buildar — senão um build que falha
    // deixa o binário velho e a validação dá falso positivo.
    await run(c, 'rm -f ' + REMOTE_SRC + '/hermes-call-linux');
    const stamp = new Date().toISOString().slice(0, 16).replace(/[-:T]/g, '').replace(/(\d{8})(\d{4})/, '$1-$2');
    // go mod tidy garante go.sum completo (fontes novas podem trazer imports novos).
    const buildCmd = 'docker run --rm -v ' + REMOTE_SRC + ':/src -w /src ' + GO_IMAGE +
      ' sh -c "go mod tidy && GOOS=linux GOARCH=amd64 CGO_ENABLED=0 go build -ldflags \\"-s -w -X main.buildStamp=' + stamp +
      '\\" -o /src/hermes-call-linux ./cmd/server" 2>&1';
    const out = await run(c, buildCmd);
    if (out.trim()) console.log(out.trim().split('\n').slice(-6).join('\n'));
    const check = await run(c, 'ls -lh ' + REMOTE_SRC + '/hermes-call-linux 2>&1');
    if (!check.includes('hermes-call-linux') || check.includes('No such')) {
      throw new Error('build falhou (binário não gerado):\n' + out);
    }
    console.log('  binário OK:', check.trim());
  }

  // Frontend upload
  if (!BACK_ONLY) {
    console.log('[upload] frontend dist...');
    await run(c, 'rm -rf ' + REMOTE_DIST);
    const n = await upload(c, sftp, DIST_DIR, REMOTE_DIST);
    console.log('  ' + n + ' arquivos');
  }

  // Instala + reinicia via systemd
  console.log('[deploy] instalando + reiniciando serviço...');
  await run(c, 'systemctl stop hermes-call');
  if (!FRONT_ONLY) {
    await run(c, 'cp ' + REMOTE_SRC + '/hermes-call-linux ' + REMOTE_BIN + ' && chmod +x ' + REMOTE_BIN);
  }
  await run(c, 'systemctl start hermes-call && sleep 5');
  const active = (await run(c, 'systemctl is-active hermes-call')).trim();
  console.log('  serviço:', active);

  // Valida
  console.log('[verify]');
  const ver = (await run(c, 'curl -s http://127.0.0.1:8080/api/version')).trim();
  const root = (await run(c, 'curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8080/')).trim();
  const restored = (await run(c, 'journalctl -u hermes-call --no-pager -n 10 | grep -o "sessions restored.*count=[0-9]*" | tail -1')).trim();
  console.log('  /api/version:', ver);
  console.log('  root (200=UI ok):', root);
  console.log('  ' + restored);

  c.end();
  if (active !== 'active') { console.error('\n⚠ Serviço não está ativo!'); process.exit(1); }
  console.log('\n=== DEPLOY OK ===');
  console.log('https://hermescall.opus-sem-limites.com.br');
}

main().catch(e => { console.error('\nFALHA:', e.message); process.exit(1); });
