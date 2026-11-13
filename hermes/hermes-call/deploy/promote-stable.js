#!/usr/bin/env node
/**
 * PROMOTE STABLE — Hermes Call v3 (refactor)
 * ===========================================
 * Depois de validar o BETA em produção, promove a imagem `hermes-call:beta` a
 * `hermes-call:stable`, criando o NOVO ponto de restauração. A partir daí, um
 * rollback futuro volta pra ESTA versão (a que você acabou de aprovar).
 *
 * Não reinicia nada — só retagueia a imagem. O container beta continua rodando.
 *
 * Uso:
 *   node promote-stable.js
 *
 * Config via env: HERMES_VPS_HOST, HERMES_VPS_USER, HERMES_VPS_PASS
 */

const { Client } = require('ssh2');

const HOST = process.env.HERMES_VPS_HOST || '62.171.128.241';
const USER = process.env.HERMES_VPS_USER || 'root';
const PASSWORD = process.env.HERMES_VPS_PASS || 'sW5pgAG9obRu2';

const IMAGE_BETA = 'hermes-call:beta';
const IMAGE_STABLE = 'hermes-call:stable';

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
  console.log('=== PROMOTE Hermes Call: ' + IMAGE_BETA + ' -> ' + IMAGE_STABLE + ' ===\n');
  const c = await connect();

  const hasBeta = (await run(c, 'docker images -q ' + IMAGE_BETA)).trim();
  if (!hasBeta) {
    c.end();
    throw new Error('Não existe ' + IMAGE_BETA + ' no VPS. Rode deploy-beta.js primeiro.');
  }

  // Guarda a estável anterior como :stable-prev (rede de segurança extra).
  const hadStable = (await run(c, 'docker images -q ' + IMAGE_STABLE)).trim();
  if (hadStable) {
    await run(c, 'docker tag ' + IMAGE_STABLE + ' hermes-call:stable-prev');
    console.log('[safety] estável anterior guardada como hermes-call:stable-prev');
  }

  await run(c, 'docker tag ' + IMAGE_BETA + ' ' + IMAGE_STABLE);
  console.log('[promote] ' + IMAGE_BETA + ' agora é ' + IMAGE_STABLE + ' (novo ponto de restauração).');

  const imgs = (await run(c, "docker images 'hermes-call' --format '{{.Repository}}:{{.Tag}}  {{.ID}}  {{.CreatedSince}}'")).trim();
  console.log('\nImagens hermes-call no VPS:\n' + imgs);

  c.end();
  console.log('\n=== PROMOTE OK ===');
}

main().catch(e => { console.error('\nFALHA:', e.message); process.exit(1); });
