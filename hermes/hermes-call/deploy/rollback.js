#!/usr/bin/env node
/**
 * ROLLBACK — Hermes Call v3 (refactor)
 * =====================================
 * Volta pra imagem ESTÁVEL (hermes-call:stable) — a última versão comprovadamente
 * boa, congelada pelo deploy-beta.js antes de subir o beta. Uso quando o beta deu
 * problema em produção.
 *
 * Não toca no banco (só troca o container/imagem). O Postgres é compartilhado; as
 * migrations do beta são aditivas (ADD COLUMN IF NOT EXISTS / CREATE IF NOT EXISTS),
 * então a versão estável continua lendo o banco normalmente após o rollback.
 *
 * Uso:
 *   node rollback.js
 *
 * Config via env: HERMES_VPS_HOST, HERMES_VPS_USER, HERMES_VPS_PASS
 */

const { Client } = require('ssh2');
const fs = require('fs');
const path = require('path');

// Lê uma chave do deploy/.env.deploy (git-ignored). Mesma função do deploy-beta.js.
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

const HOST = process.env.HERMES_VPS_HOST || '62.171.128.241';
const USER = process.env.HERMES_VPS_USER || 'root';
const PASSWORD = process.env.HERMES_VPS_PASS || 'sW5pgAG9obRu2';

const IMAGE_STABLE = 'hermes-call:stable';
const CONTAINER = 'hermes-call';
const DB_URL = 'postgres://hermes_call_v3test:hermes_call_v3test@localhost:5432/wacalls_main?sslmode=disable';
const TG_TOKEN = process.env.HERMES_TELEGRAM_TOKEN || '<SEGREDO_REMOVIDO>';

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
  console.log('=== ROLLBACK Hermes Call -> ' + HOST + ' (volta pra ' + IMAGE_STABLE + ') ===\n');
  const c = await connect();

  const hasStable = (await run(c, 'docker images -q ' + IMAGE_STABLE)).trim();
  if (!hasStable) {
    c.end();
    throw new Error('Não existe imagem ' + IMAGE_STABLE + ' no VPS. Nada pra restaurar. ' +
      '(Ela só é criada quando você roda deploy-beta.js pela primeira vez.)');
  }

  console.log('[rollback] parando container atual e subindo a imagem estável...');
  await run(c, 'docker rm -f ' + CONTAINER + ' 2>/dev/null; echo ok');
  // Mesmo JWT secret do deploy-beta.js: sem ele o binário cai no default público.
  const JWT_SECRET = envFromDeploy('HERMES_JWT_SECRET');
  if (!JWT_SECRET) {
    c.end();
    throw new Error('HERMES_JWT_SECRET ausente no .env.deploy — abortando pra não restaurar com o secret default público.');
  }
  const runCmd = 'docker run -d --name ' + CONTAINER + ' --restart=always --network host ' +
    '-e "WACALLS_PG_URL=' + DB_URL + '" ' +
    '-e "PORT=8080" ' +
    '-e "HERMES_TELEGRAM_TOKEN=' + TG_TOKEN + '" ' +
    "-e 'HERMES_JWT_SECRET=" + JWT_SECRET + "' " +
    IMAGE_STABLE + ' 2>&1';
  console.log(await run(c, runCmd));

  await new Promise(r => setTimeout(r, 8000));

  console.log('[verify]');
  const active = (await run(c, "docker ps --filter name=" + CONTAINER + " --format '{{.Status}}'")).trim();
  const ver = (await run(c, 'curl -s http://127.0.0.1:8080/api/version')).trim();
  const root = (await run(c, 'curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8080/')).trim();
  console.log('  container:', active || 'NÃO ESTÁ RODANDO');
  console.log('  /api/version:', ver, '(deve mostrar channel=stable)');
  console.log('  root (200=UI ok):', root);

  c.end();
  if (!active) { console.error('\n⚠ Rollback não subiu o container!'); process.exit(1); }
  console.log('\n=== ROLLBACK OK — versão estável restaurada ===');
}

main().catch(e => { console.error('\nFALHA:', e.message); process.exit(1); });
