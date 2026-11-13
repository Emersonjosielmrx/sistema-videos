#!/usr/bin/env node
/**
 * ROLLBACK PROD — Hermes Call v3 (VPS de produção .53)
 * =====================================================
 * Volta o serviço Swarm de produção pra imagem ANTERIOR, gravada em deploy/.prod-prev
 * pelo deploy-prod.js antes de cada atualização. Só troca a imagem do serviço — não
 * toca no Postgres, nas env vars, nas redes nem nos labels do Traefik.
 *
 * As migrations são aditivas (ADD COLUMN IF NOT EXISTS / CREATE IF NOT EXISTS), então
 * a imagem anterior continua lendo o banco normalmente após o rollback.
 *
 * Uso:
 *   node deploy/rollback-prod.js                 # volta pra imagem do .prod-prev
 *   node deploy/rollback-prod.js --tag v0.2.0    # volta pra uma tag específica do Docker Hub
 *   node deploy/rollback-prod.js --dry-run       # mostra o que faria
 *
 * Config: deploy/.env.deploy (DOCKERHUB_REPO). Prod via env PROD_VPS_HOST/USER/PASS.
 */

const { Client } = require('ssh2');
const fs = require('fs');
const path = require('path');

function loadEnv() {
  const p = path.join(__dirname, '.env.deploy');
  const env = {};
  if (fs.existsSync(p)) {
    for (const line of fs.readFileSync(p, 'utf8').split('\n')) {
      const s = line.trim();
      if (!s || s.startsWith('#')) continue;
      const i = s.indexOf('='); if (i === -1) continue;
      env[s.slice(0, i).trim()] = s.slice(i + 1).trim();
    }
  }
  return env;
}
const ENV = loadEnv();

const PROD_HOST = process.env.PROD_VPS_HOST || ENV.PROD_VPS_HOST || '209.145.60.53';
const PROD_USER = process.env.PROD_VPS_USER || ENV.PROD_VPS_USER || 'root';
const PROD_PASS = process.env.PROD_VPS_PASS || ENV.PROD_VPS_PASS || '';
const REPO = ENV.DOCKERHUB_REPO || 'fabricadeautomacoesia/hermes-call';
const PROD_SERVICE = process.env.PROD_SERVICE || 'hermes_call_refactor_hermes-call-refactor';
const PREV_FILE = path.join(__dirname, '.prod-prev');

const DRY = process.argv.includes('--dry-run');
function arg(name) { const i = process.argv.indexOf(name); return i !== -1 ? process.argv[i + 1] : null; }

function connect(host, user, pass) {
  return new Promise((res, rej) => {
    if (!pass) return rej(new Error('senha vazia pra ' + host + ' (configure PROD_VPS_PASS ou .env.deploy).'));
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
  const tagArg = arg('--tag');
  let target = tagArg ? (REPO + ':' + tagArg) : null;
  if (!target) {
    if (!fs.existsSync(PREV_FILE)) throw new Error('não há deploy/.prod-prev (nenhum deploy-prod anterior). Use --tag vX.Y.Z.');
    target = fs.readFileSync(PREV_FILE, 'utf8').trim();
    if (!target) throw new Error('.prod-prev vazio. Use --tag vX.Y.Z.');
  }

  console.log('=== ROLLBACK PROD Hermes Call -> ' + PROD_HOST + ' ===');
  console.log('  serviço : ' + PROD_SERVICE);
  console.log('  imagem  : ' + target + (tagArg ? ' (--tag)' : ' (.prod-prev)'));
  if (DRY) { console.log('  *** DRY-RUN ***\n  (dry) docker pull ' + target + '\n  (dry) docker service update --with-registry-auth --image ' + target + ' --replicas 1 ' + PROD_SERVICE); return; }
  console.log('');

  const p = await connect(PROD_HOST, PROD_USER, PROD_PASS);

  const svc = (await run(p, "docker service ls --filter name=" + PROD_SERVICE + " --format '{{.Name}}'")).trim();
  if (!svc) { p.end(); throw new Error('serviço ' + PROD_SERVICE + ' não existe na .53.'); }

  console.log('[.53] docker pull ' + target + ' ...');
  const pull = await run(p, 'docker pull ' + target + ' 2>&1 | tail -3');
  console.log('  ' + pull.trim().replace(/\n/g, '\n  '));
  if (/denied|unauthorized|manifest unknown|not found/i.test(pull)) {
    p.end(); throw new Error('pull falhou pra ' + target + '. Tag existe/publicada?');
  }

  console.log('[.53] revertendo serviço...');
  const upd = await run(p, 'docker service update --with-registry-auth --image ' + target + ' --replicas 1 ' + PROD_SERVICE + ' 2>&1 | tail -12');
  console.log('  ' + upd.trim().replace(/\n/g, '\n  '));

  console.log('[.53] aguardando convergir...');
  let ok = false;
  for (let i = 0; i < 24; i++) {
    await new Promise(r => setTimeout(r, 5000));
    const rep = (await run(p, "docker service ls --filter name=" + PROD_SERVICE + " --format '{{.Replicas}}'")).trim();
    process.stdout.write('  réplicas: ' + rep + '   \r');
    if (/^([1-9]\d*)\/\1$/.test(rep)) { ok = true; console.log('\n  convergiu: ' + rep); break; }
  }
  p.end();
  if (!ok) throw new Error('rollback não convergiu. Verifique docker service ps ' + PROD_SERVICE + ' na .53.');
  console.log('\n=== ROLLBACK PROD OK — ' + target + ' restaurada ===');
}

main().catch(e => { console.error('\nFALHA:', e.message); process.exit(1); });
