#!/usr/bin/env node
/**
 * DEPLOY BETA — Hermes Call v3 (refactor)
 * ========================================
 * Sobe a nova leva de features como BETA, PRESERVANDO a versão estável que já
 * está rodando pra permitir rollback de 1 comando.
 *
 * Estratégia de segurança (o que evita perder a versão que funciona):
 *   1. ANTES de buildar, retagueia a imagem que está no ar como `hermes-call:stable`
 *      (só na primeira vez / se ainda não existir uma :stable — assim a :stable
 *      sempre aponta pra última versão comprovadamente boa).
 *   2. Builda a imagem nova como `hermes-call:beta`.
 *   3. Sobe o container a partir da :beta. Se algo der errado, `rollback.js`
 *      volta pra :stable.
 *   4. Só depois de você validar o beta é que se promove com `promote-stable.js`
 *      (retagueia :beta -> :stable como novo ponto de restauração).
 *
 * Uso:
 *   node deploy-beta.js            # sync fontes + build :beta na VPS + sobe container
 *   node deploy-beta.js --no-sync  # rebuilda :beta com o que já está no VPS
 *   node deploy-beta.js --pull     # NÃO builda: puxa :next do Docker Hub (publicado
 *                                  # pelo release.js/CI) e sobe. Fonte única da imagem.
 *
 * Config via env: HERMES_VPS_HOST, HERMES_VPS_USER, HERMES_VPS_PASS
 */

const { Client } = require('ssh2');
const fs = require('fs');
const path = require('path');

const HOST = envFromDeploy('HERMES_VPS_HOST') || process.env.HERMES_VPS_HOST || '62.171.128.241';
const USER = envFromDeploy('HERMES_VPS_USER') || process.env.HERMES_VPS_USER || 'root';
const PASSWORD = envFromDeploy('HERMES_VPS_PASS') || process.env.HERMES_VPS_PASS || 'sW5pgAG9obRu2';

const ROOT = path.resolve(__dirname, '..');
const REMOTE_SRC = '/opt/hipercool-refactor';
const IMAGE_BETA = 'hermes-call:beta';
const IMAGE_STABLE = 'hermes-call:stable';
const IMAGE_LATEST = 'hermes-call:latest'; // tag que o deploy antigo usava
const CONTAINER = 'hermes-call';
const DB_URL = 'postgres://hermes_call_v3test:hermes_call_v3test@127.0.0.1:5432/wacalls_main?sslmode=disable';
const TG_TOKEN = process.env.HERMES_TELEGRAM_TOKEN || '<SEGREDO_REMOVIDO>';

const NO_SYNC = process.argv.includes('--no-sync');
// --pull: em vez de buildar na VPS, puxa a imagem :next JÁ PUBLICADA no Docker Hub
// (pelo release.js / CI). Fonte única da imagem: o que foi testado no CI é o que sobe.
const PULL = process.argv.includes('--pull');

// Lê uma chave de deploy/.env.deploy (segredos git-ignored). Fallback: process.env.
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

// Repo no Docker Hub (pra o modo --pull). Lê de deploy/.env.deploy se existir.
function dockerhubRepo() {
  return envFromDeploy('DOCKERHUB_REPO') || 'fabricadeautomacoesia/hermes-call';
}

// Versão do arquivo VERSION → injetada no build (o Dockerfile aceita APP_VERSION/APP_CHANNEL
// e grava no binário via ldflags). Este deploy é sempre canal beta.
function appVersionTag() {
  try {
    const v = fs.readFileSync(path.join(ROOT, 'VERSION'), 'utf8').trim();
    return v ? 'v' + v : 'dev';
  } catch { return 'dev'; }
}

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
    // Pula binários nativos pesados (~3.7M) que travavam o upload SFTP: os .dll são
    // de Windows (inúteis no Linux) e o .so é RECOMPILADO pelo Dockerfile (stage opus).
    if (/\.(dll|so|a|dylib)$/i.test(name)) continue;
    // Pula áudios grandes fora de audio/ambient (evita travar SFTP com mídia pesada).
    // Inclui os ambient (< 2MB cada, ~10MB total) que o container precisa p/ background noise.
    if (/\.(mp3|wav|ogg|m4a)$/i.test(name)) {
      const inAmbient = /[/\\]audio[/\\]ambient[/\\]/.test(dir) || dir.endsWith('ambient');
      const stat = fs.statSync(path.join(dir, name));
      if (!inAmbient || stat.size === 0 || stat.size > 2 * 1024 * 1024) continue;
    }
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
  // Upload PARALELO (pool de N) — o fastPut serial levava ~1.5s/arquivo (10+ min em
  // centenas de arquivos), o que parecia "travado". Com concorrência cai pra ~1 min.
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
  console.log('=== DEPLOY BETA Hermes Call v3 -> ' + HOST + ' ===\n');
  const c = await connect();
  const sftp = await new Promise((res, rej) => c.sftp((e, s) => e ? rej(e) : res(s)));
  await run(c, 'mkdir -p ' + REMOTE_SRC);

  // -------- 1. Ponto de restauração: garante que exista uma :stable --------
  // Se ainda não há :stable, congela a imagem que está rodando AGORA como estável.
  const hasStable = (await run(c, 'docker images -q ' + IMAGE_STABLE)).trim();
  if (!hasStable) {
    // Descobre a imagem do container em execução (ou cai pra :latest do deploy antigo).
    let curImg = (await run(c, "docker inspect --format '{{.Config.Image}}' " + CONTAINER + ' 2>/dev/null')).trim();
    if (!curImg) curImg = IMAGE_LATEST;
    const exists = (await run(c, 'docker images -q ' + curImg)).trim();
    if (exists) {
      await run(c, 'docker tag ' + curImg + ' ' + IMAGE_STABLE);
      console.log('[safety] imagem estável congelada: ' + curImg + ' -> ' + IMAGE_STABLE);
    } else {
      console.log('[safety] AVISO: não achei imagem atual pra congelar como :stable (primeiro deploy?).');
    }
  } else {
    console.log('[safety] já existe ' + IMAGE_STABLE + ' (ponto de restauração preservado).');
  }

  if (PULL) {
    // -------- Modo --pull: usa a imagem :next publicada no Docker Hub --------
    const repo = dockerhubRepo();
    const remoteNext = repo + ':next';
    console.log('[pull] puxando ' + remoteNext + ' do Docker Hub...');
    const pull = await run(c, 'docker pull ' + remoteNext + ' 2>&1 | tail -5');
    console.log(pull.trim());
    const ok = (await run(c, 'docker images -q ' + remoteNext)).trim();
    if (!ok) throw new Error('docker pull falhou pra ' + remoteNext + ' (rode release.js --version X.Y.Z-beta.N antes).');
    // Retagueia localmente como :beta pra o resto do fluxo (rollback/promote) seguir igual.
    await run(c, 'docker tag ' + remoteNext + ' ' + IMAGE_BETA);
    console.log('  ' + remoteNext + ' -> ' + IMAGE_BETA);
  } else {
    // -------- 2. Sync das fontes (modo build-na-VPS) --------
    if (!NO_SYNC) {
      console.log('[sync] enviando fontes...');
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
      console.log('  ' + total + ' arquivos enviados');
    }

    // -------- 3. Build da imagem :beta --------
    const appVer = appVersionTag();
    console.log('[build] docker build :beta ' + appVer + ' (beta) (compila MLow + client + Go, ~3-6min)...');
    // ID da imagem :beta ANTES do build, pra detectar se o build realmente gerou uma
    // imagem NOVA. Sem isso, um build que falha deixa a :beta antiga e o deploy sobe
    // versão velha achando que deu certo (bug real que mascarou uma falha).
    const prevImg = (await run(c, 'docker images -q ' + IMAGE_BETA)).trim();
    // `echo BUILD_RC:$?` logo após o docker build (ANTES do pipe) captura o código de
    // saída REAL do build — o `| tail` sozinho mascara a falha (retorna sucesso do tail).
    const build = await run(c, 'cd ' + REMOTE_SRC +
      ' && ( docker build --network host' +
      ' --build-arg APP_VERSION=' + appVer + ' --build-arg APP_CHANNEL=beta' +
      ' -t ' + IMAGE_BETA + ' . ; echo BUILD_RC:$? ) 2>&1 | tail -20');
    console.log(build.trim());
    if (!/BUILD_RC:0\b/.test(build)) {
      throw new Error('build da imagem beta FALHOU (não subi nada; a versão anterior segue no ar). Veja o log acima.');
    }
    const newImg = (await run(c, 'docker images -q ' + IMAGE_BETA)).trim();
    if (!newImg) throw new Error('build não gerou imagem :beta.');
    if (prevImg && newImg === prevImg) {
      throw new Error('build não gerou imagem NOVA (:beta idêntica à anterior). Abortando pra não subir versão velha.');
    }
  }

  // -------- 4. Sobe o container a partir da :beta --------
  console.log('\n[deploy] subindo container beta...');
  await run(c, 'systemctl stop hermes-call 2>/dev/null; systemctl disable hermes-call 2>/dev/null; echo ok');
  await run(c, 'docker rm -f ' + CONTAINER + ' 2>/dev/null; echo ok');
  // Asaas (pagamentos): token da plataforma, lido do .env.deploy (git-ignored).
  const ASAAS_KEY = envFromDeploy('HERMES_ASAAS_API_KEY');
  const ASAAS_URL = envFromDeploy('HERMES_ASAAS_API_URL');
  const ASAAS_WH = envFromDeploy('HERMES_ASAAS_WEBHOOK_TOKEN');
  // IMPORTANTE: usa ASPAS SIMPLES nos valores. O token Asaas começa com "$"
  // ($aact_prod_...); com aspas duplas o shell da VPS expandia "$aact..." como variável
  // e mandava a key VAZIA pro container (gateway "indisponível"). Aspas simples não
  // expandem $. (Valores não contêm aspas simples, então é seguro.)
  let asaasEnv = '';
  if (ASAAS_KEY) asaasEnv += "-e 'HERMES_ASAAS_API_KEY=" + ASAAS_KEY + "' ";
  if (ASAAS_URL) asaasEnv += "-e 'HERMES_ASAAS_API_URL=" + ASAAS_URL + "' ";
  if (ASAAS_WH) asaasEnv += "-e 'HERMES_ASAAS_WEBHOOK_TOKEN=" + ASAAS_WH + "' ";

  // Google OAuth (login social): só injeta se configurado (senão fica "em breve").
  for (const k of ['HERMES_GOOGLE_CLIENT_ID', 'HERMES_GOOGLE_CLIENT_SECRET', 'HERMES_GOOGLE_REDIRECT_URL', 'HERMES_OAUTH_SUCCESS_URL']) {
    const v = envFromDeploy(k);
    if (v) asaasEnv += "-e '" + k + "=" + v + "' ";
  }
  // Conta admin isenta de cobrança (default no código é admin@hermescall.com).
  const ADMIN_EMAIL = envFromDeploy('HERMES_ADMIN_EMAIL') || 'admin@hermescall.com';
  asaasEnv += "-e 'HERMES_ADMIN_EMAIL=" + ADMIN_EMAIL + "' ";
  // Monitor interno do dono (bot de avisos): cadastro/ligação/erro. Só liga se ambos setados.
  const MON_TOKEN = envFromDeploy('HERMES_MONITOR_BOT_TOKEN');
  const MON_CHAT = envFromDeploy('HERMES_MONITOR_CHAT_ID');
  if (MON_TOKEN) asaasEnv += "-e 'HERMES_MONITOR_BOT_TOKEN=" + MON_TOKEN + "' ";
  if (MON_CHAT) asaasEnv += "-e 'HERMES_MONITOR_CHAT_ID=" + MON_CHAT + "' ";
  // Cupons que liberam acesso grátis (allowlist; sistema de afiliados). Sem isso, nenhum cupom vale.
  const FREE_COUPONS = envFromDeploy('HERMES_FREE_COUPONS');
  if (FREE_COUPONS) asaasEnv += "-e 'HERMES_FREE_COUPONS=" + FREE_COUPONS + "' ";

  // Segredo de assinatura dos JWT. SEM isso o código cai no default público
  // ("hermes-call-default-secret-change-me" em internal/auth/jwt.go) e QUALQUER
  // um forja token de qualquer usuário/admin. Obrigatório e lido do .env.deploy.
  const JWT_SECRET = envFromDeploy('HERMES_JWT_SECRET');
  if (!JWT_SECRET) {
    throw new Error('HERMES_JWT_SECRET ausente no .env.deploy — abortando pra não subir com o secret default público.');
  }
  asaasEnv += "-e 'HERMES_JWT_SECRET=" + JWT_SECRET + "' ";

  // Volume persistente pras gravações. SEM isto os MP3 iam pra /tmp DENTRO do
  // container (efêmero) e todo redeploy apagava tudo — o banco guardava o registro
  // mas o arquivo sumia, então o <audio> no painel ficava 0:00/0:00 sem tocar nada.
  const REC_HOST_DIR = '/opt/hermes-data/recordings';
  await run(c, 'mkdir -p ' + REC_HOST_DIR);
  // Porta fixa do WebRTC com o navegador (discador). SEM WACALLS_PUBLIC_IP +
  // WACALLS_UDP_PORT o bridge cai em portas efêmeras e NÃO anuncia o IP público —
  // com iceServers:[] no browser, a mídia nunca conecta (liga mas não ouve/fala).
  // Precisa também da porta liberada no firewall (ufw allow 50000).
  await run(c, 'ufw allow 50000/udp >/dev/null 2>&1; ufw allow 50000/tcp >/dev/null 2>&1; echo fw-ok');
  const runCmd = 'docker run -d --name ' + CONTAINER + ' --restart=always --network host ' +
    '-v "' + REC_HOST_DIR + ':/data/recordings" ' +
    '-e "WACALLS_RECORDING_DIR=/data/recordings" ' +
    '-e "WACALLS_PUBLIC_IP=auto" ' +
    '-e "WACALLS_UDP_PORT=50000" ' +
    '-e "WACALLS_PG_URL=' + DB_URL + '" ' +
    '-e "PORT=8080" ' +
    '-e "HERMES_TELEGRAM_TOKEN=' + TG_TOKEN + '" ' +
    asaasEnv +
    IMAGE_BETA + ' 2>&1';
  console.log(await run(c, runCmd));

  await new Promise(r => setTimeout(r, 8000));

  // -------- 5. Validação --------
  console.log('[verify]');
  const active = (await run(c, "docker ps --filter name=" + CONTAINER + " --format '{{.Status}}'")).trim();
  console.log('  container:', active || 'NÃO ESTÁ RODANDO');
  const ver = (await run(c, 'curl -s http://127.0.0.1:8080/api/version')).trim();
  const root = (await run(c, 'curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8080/')).trim();
  console.log('  /api/version:', ver);
  console.log('  root (200=UI ok):', root);
  console.log('  logs:', (await run(c, 'docker logs --tail 8 ' + CONTAINER + ' 2>&1')).trim());

  c.end();
  if (!active) {
    console.error('\n⚠ Container beta não subiu! Rode: node deploy/rollback.js');
    process.exit(1);
  }
  console.log('\n=== DEPLOY BETA OK ===');
  console.log('Valide em https://hermescall.opus-sem-limites.com.br (deve mostrar channel=beta em /api/version).');
  console.log('Se estiver bom:  node deploy/promote-stable.js   (marca este beta como nova estável)');
  console.log('Se der errado:   node deploy/rollback.js          (volta pra imagem estável anterior)');
}

main().catch(e => { console.error('\nFALHA:', e.message); process.exit(1); });
