#!/usr/bin/env node
/**
 * DEPLOY PROD — Hermes Call v3  (build na .241  →  Docker Hub  →  roda na .53)
 * ===========================================================================
 * Objetivo: a VPS de PRODUÇÃO (.53) roda SÓ A IMAGEM pronta, sem código-fonte.
 * O build acontece só na VPS de BUILD (.241, que tem a fonte e o Docker Hub login).
 * A .53 apenas faz `docker pull` + troca a imagem do serviço Swarm — nunca vê fonte.
 *
 * Fluxo:
 *   1. [.241] Garante que existe a imagem `hermes-call:beta` (a mais recente buildada
 *      pelo deploy-beta.js). Com --build, roda o build antes (sync já tem que ter sido
 *      feito pelo deploy-beta.js; aqui NÃO sincronizamos fonte).
 *   2. [.241] Retagueia beta → REPO:vX.Y.Z + REPO:stable + REPO:latest e faz `docker push`
 *      (login via token do deploy/.env.deploy). REPO = DOCKERHUB_REPO (fabricadeautomacoesia/hermes-call).
 *   3. [.53]  Guarda a imagem ATUAL do serviço como ponto de rollback (deploy/.prod-prev),
 *      faz `docker pull REPO:vX.Y.Z` e `docker service update --image ... --replicas 1
 *      --with-registry-auth`. Preserva env, redes, labels Traefik e o Postgres (não toca).
 *   4. [.53]  Aguarda o serviço convergir (1/1) e reporta status + versão.
 *
 * A imagem é multi-stage: o estágio final (debian-slim) leva só o binário `wacalls`
 * e o client compilado — ZERO código-fonte. Extrair fonte da .53 é impossível.
 *
 * Uso:
 *   node deploy/deploy-prod.js                 # publica a :beta atual da .241 e sobe na .53
 *   node deploy/deploy-prod.js --build         # builda a :beta na .241 antes de publicar
 *   node deploy/deploy-prod.js --version 0.2.2 # grava VERSION e usa essa tag
 *   node deploy/deploy-prod.js --tag v0.2.1    # NÃO builda/pusha: só aponta a .53 pra uma tag já publicada
 *   node deploy/deploy-prod.js --dry-run       # mostra o que faria, sem executar nada destrutivo
 *
 * Config: deploy/.env.deploy (DOCKERHUB_USER/TOKEN/REPO, HERMES_VPS_* da build).
 *         Prod (.53) via env: PROD_VPS_HOST, PROD_VPS_USER, PROD_VPS_PASS.
 */

const { Client } = require('ssh2');
const fs = require('fs');
const path = require('path');

const ROOT = path.resolve(__dirname, '..');

// ---------- .env.deploy (segredos git-ignored) ----------
function loadEnv() {
  const p = path.join(__dirname, '.env.deploy');
  const env = {};
  if (fs.existsSync(p)) {
    for (const line of fs.readFileSync(p, 'utf8').split('\n')) {
      const s = line.trim();
      if (!s || s.startsWith('#')) continue;
      const i = s.indexOf('=');
      if (i === -1) continue;
      env[s.slice(0, i).trim()] = s.slice(i + 1).trim();
    }
  }
  return env;
}
const ENV = loadEnv();

// ---------- BUILD VPS (.241) ----------
const BUILD_HOST = process.env.HERMES_VPS_HOST || ENV.HERMES_VPS_HOST || '62.171.128.241';
const BUILD_USER = process.env.HERMES_VPS_USER || ENV.HERMES_VPS_USER || 'root';
const BUILD_PASS = process.env.HERMES_VPS_PASS || ENV.HERMES_VPS_PASS || '';

// ---------- PROD VPS (.53) ----------
const PROD_HOST = process.env.PROD_VPS_HOST || ENV.PROD_VPS_HOST || '209.145.60.53';
const PROD_USER = process.env.PROD_VPS_USER || ENV.PROD_VPS_USER || 'root';
const PROD_PASS = process.env.PROD_VPS_PASS || ENV.PROD_VPS_PASS || '';

const REMOTE_SRC = '/opt/hipercool-refactor';
const IMAGE_BETA = 'hermes-call:beta';
const REPO = ENV.DOCKERHUB_REPO || 'fabricadeautomacoesia/hermes-call';
const DOCKER_USER = ENV.DOCKERHUB_USER || 'fabricadeautomacoesia';
const DOCKER_TOKEN = ENV.DOCKERHUB_TOKEN || '';

// Serviço Swarm de produção (o app; NÃO é o Postgres/piper/whisper).
const PROD_SERVICE = process.env.PROD_SERVICE || 'hermes_call_refactor_hermes-call-refactor';
const PREV_FILE = path.join(__dirname, '.prod-prev'); // grava a imagem anterior p/ rollback

// ---------- flags ----------
const DO_BUILD = process.argv.includes('--build');
const DRY = process.argv.includes('--dry-run');
function arg(name) {
  const i = process.argv.indexOf(name);
  return i !== -1 ? process.argv[i + 1] : null;
}

function versionTag() {
  const forced = arg('--version');
  const vf = path.join(ROOT, 'VERSION');
  if (forced) { fs.writeFileSync(vf, forced + '\n'); return 'v' + forced; }
  try { const v = fs.readFileSync(vf, 'utf8').trim(); return v ? 'v' + v : 'dev'; }
  catch { return 'dev'; }
}

function connect(host, user, pass) {
  return new Promise((res, rej) => {
    if (!pass) return rej(new Error('senha vazia pra ' + host + ' (configure PROD_VPS_PASS / HERMES_VPS_PASS ou .env.deploy).'));
    const c = new Client();
    c.on('ready', () => res(c));
    c.on('error', rej);
    c.connect({ host, port: 22, username: user, password: pass, readyTimeout: 30000 });
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
  const TAG = versionTag();
  const imgVer = REPO + ':' + TAG;
  const imgStable = REPO + ':stable';
  const imgLatest = REPO + ':latest';
  const onlyTag = arg('--tag'); // pular build/push e só apontar a .53 pra uma tag existente

  console.log('=== DEPLOY PROD Hermes Call ===');
  console.log('  build VPS : ' + BUILD_USER + '@' + BUILD_HOST + '  (fonte + push)');
  console.log('  prod  VPS : ' + PROD_USER + '@' + PROD_HOST + '  (só imagem)');
  console.log('  repo hub  : ' + REPO);
  console.log('  tag       : ' + (onlyTag || TAG));
  console.log('  serviço   : ' + PROD_SERVICE);
  if (DRY) console.log('  *** DRY-RUN: nada será executado ***');
  console.log('');

  const targetImage = onlyTag ? (REPO + ':' + onlyTag) : imgVer;

  // ============ FASE 1+2: BUILD + PUSH (na .241) ============
  if (!onlyTag) {
    if (!DOCKER_TOKEN) throw new Error('falta DOCKERHUB_TOKEN em deploy/.env.deploy (necessário pro push).');
    console.log('[.241] conectando...');
    if (DRY) {
      console.log('  (dry) verificaria/buildaria ' + IMAGE_BETA);
      console.log('  (dry) docker tag ' + IMAGE_BETA + ' -> ' + [imgVer, imgStable, imgLatest].join(', '));
      console.log('  (dry) docker login + docker push das 3 tags');
    } else {
      const b = await connect(BUILD_HOST, BUILD_USER, BUILD_PASS);

      if (DO_BUILD) {
        const appVer = TAG;
        console.log('[.241] buildando ' + IMAGE_BETA + ' ' + appVer + ' (usa a fonte já sincronizada em ' + REMOTE_SRC + ')...');
        const build = await run(b, 'cd ' + REMOTE_SRC +
          ' && ( docker build --network host --build-arg APP_VERSION=' + appVer +
          ' --build-arg APP_CHANNEL=stable -t ' + IMAGE_BETA + ' . ; echo BUILD_RC:$? ) 2>&1 | tail -20');
        console.log(build.trim());
        if (!/BUILD_RC:0\b/.test(build)) { b.end(); throw new Error('build falhou; nada publicado.'); }
      }

      const betaId = (await run(b, 'docker images -q ' + IMAGE_BETA)).trim();
      if (!betaId) { b.end(); throw new Error('não existe ' + IMAGE_BETA + ' na .241. Rode deploy-beta.js (ou use --build).'); }
      console.log('[.241] imagem base ' + IMAGE_BETA + ' = ' + betaId);

      console.log('[.241] retagueando -> ' + TAG + ', stable, latest ...');
      for (const t of [imgVer, imgStable, imgLatest]) await run(b, 'docker tag ' + IMAGE_BETA + ' ' + t);

      console.log('[.241] docker login (' + DOCKER_USER + ') + push ...');
      // login via stdin, sem deixar token no histórico de processos.
      await run(b, 'printf %s ' + JSON.stringify(DOCKER_TOKEN) + ' | docker login -u ' + DOCKER_USER + ' --password-stdin 2>&1');
      for (const t of [imgVer, imgStable, imgLatest]) {
        const p = await run(b, 'docker push ' + t + ' 2>&1 | tail -3');
        console.log('  push ' + t + ':\n    ' + p.trim().replace(/\n/g, '\n    '));
        // detecção grosseira de falha de permissão/repo
        if (/denied|unauthorized|not authorized|repository does not exist/i.test(p)) {
          b.end();
          throw new Error('PUSH NEGADO pra ' + t + '. A conta ' + DOCKER_USER + ' tem acesso de escrita a ' + REPO + '? Veja o log acima.');
        }
      }
      b.end();
      console.log('[.241] publicado: ' + [imgVer, imgStable, imgLatest].join(', '));
    }
  } else {
    console.log('[.241] pulado (--tag ' + onlyTag + ': usando imagem já publicada).');
  }

  // ============ FASE 3+4: PULL + UPDATE (na .53) ============
  console.log('\n[.53] conectando...');
  if (DRY) {
    console.log('  (dry) leria imagem atual do serviço e salvaria em .prod-prev');
    console.log('  (dry) docker pull ' + targetImage);
    console.log('  (dry) docker service update --with-registry-auth --image ' + targetImage + ' --replicas 1 ' + PROD_SERVICE);
    console.log('\n=== DRY-RUN OK (nada mudou) ===');
    return;
  }
  const p = await connect(PROD_HOST, PROD_USER, PROD_PASS);

  // confere que o serviço existe
  const svcLine = (await run(p, "docker service ls --filter name=" + PROD_SERVICE + " --format '{{.Name}} {{.Image}} {{.Replicas}}'")).trim();
  if (!svcLine) { p.end(); throw new Error('serviço ' + PROD_SERVICE + ' não existe na .53.'); }
  console.log('[.53] serviço atual: ' + svcLine);

  // ponto de rollback: imagem atual do serviço
  const curImg = (await run(p, "docker service inspect " + PROD_SERVICE + " --format '{{.Spec.TaskTemplate.ContainerSpec.Image}}'")).trim().split('@')[0];
  if (curImg) { fs.writeFileSync(PREV_FILE, curImg + '\n'); console.log('[.53] rollback salvo (.prod-prev): ' + curImg); }

  console.log('[.53] docker pull ' + targetImage + ' ...');
  const pull = await run(p, 'docker pull ' + targetImage + ' 2>&1 | tail -4');
  console.log('  ' + pull.trim().replace(/\n/g, '\n  '));
  if (/denied|unauthorized|manifest unknown|not found/i.test(pull)) {
    p.end();
    throw new Error('PULL falhou pra ' + targetImage + ' na .53 (repo privado sem login? tag não publicada?). Veja o log.');
  }

  console.log('[.53] atualizando serviço (imagem + 1 réplica, preservando env/rede/labels/DB)...');
  const upd = await run(p, 'docker service update --with-registry-auth' +
    ' --image ' + targetImage + ' --replicas 1 ' + PROD_SERVICE + ' 2>&1 | tail -15');
  console.log('  ' + upd.trim().replace(/\n/g, '\n  '));

  // aguarda convergência
  console.log('[.53] aguardando convergir...');
  let ok = false;
  for (let i = 0; i < 24; i++) {
    await new Promise(r => setTimeout(r, 5000));
    const rep = (await run(p, "docker service ls --filter name=" + PROD_SERVICE + " --format '{{.Replicas}}'")).trim();
    process.stdout.write('  réplicas: ' + rep + '   \r');
    if (/^([1-9]\d*)\/\1$/.test(rep)) { ok = true; console.log('\n  convergiu: ' + rep); break; }
  }
  if (!ok) {
    const ps = await run(p, 'docker service ps ' + PROD_SERVICE + ' --no-trunc --format "{{.Name}} {{.CurrentState}} {{.Error}}" 2>&1 | head -6');
    console.log('\n[.53] NÃO convergiu. Últimas tasks:\n  ' + ps.trim().replace(/\n/g, '\n  '));
    p.end();
    throw new Error('serviço não subiu. Rode: node deploy/rollback-prod.js');
  }

  const ver = (await run(p, "docker service logs " + PROD_SERVICE + " --tail 20 2>&1 | grep -iE 'listening|version|rodando' | tail -3")).trim();
  if (ver) console.log('[.53] logs:\n  ' + ver.replace(/\n/g, '\n  '));

  p.end();
  console.log('\n=== DEPLOY PROD OK ===');
  console.log('  produção rodando ' + targetImage + ' (sem código-fonte).');
  console.log('  rollback:  node deploy/rollback-prod.js');
}

main().catch(e => { console.error('\nFALHA:', e.message); process.exit(1); });
