#!/usr/bin/env node
/**
 * ROLLBACK para stable-prev (imagem de 25h atrás que tem Athena)
 */
const { Client } = require('ssh2');
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
  console.log('=== ROLLBACK Hermes Call -> ' + HOST + ' (volta pra hermes-call:stable-prev) ===\n');
  const c = await connect();

  console.log('[1] salvando latest ruim como latest-buggy antes de sobrescrever...');
  const tagLatest = await run(c, 'docker tag hermes-call:latest hermes-call:latest-buggy 2026-07-25 && echo ok');
  console.log('  ', tagLatest.trim());

  console.log('[2] parando container atual...');
  const rmOut = await run(c, 'docker rm -f hermes-call 2>&1; echo ok');
  console.log('  ', rmOut.trim());

  console.log('[3] subindo hermes-call:stable-prev...');
  const runCmd = 'docker run -d --name hermes-call --restart=always --network host ' +
    '-e "WACALLS_PG_URL=postgres://hermes_call_v3test:hermes_call_v3test@localhost:5432/wacalls_main?sslmode=disable" ' +
    '-e "PORT=8080" ' +
    '-e "HERMES_TELEGRAM_TOKEN=<SEGREDO_REMOVIDO>" ' +
    'hermes-call:stable-prev 2>&1';
  const runOut = await run(c, runCmd);
  console.log('  ', runOut.trim());

  await new Promise(r => setTimeout(r, 10000));

  console.log('[4] verify...');
  const active = (await run(c, "docker ps --filter name=hermes-call --format '{{.Status}}'")).trim();
  const ver = (await run(c, 'curl -s http://127.0.0.1:8080/api/version')).trim();
  const root = (await run(c, 'curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8080/')).trim();
  const bundle = (await run(c, "curl -s http://127.0.0.1:8080/ | grep -oE 'index-[A-Za-z0-9_]+\\.js'")).trim();
  console.log('  container:', active || 'NÃO ESTÁ RODANDO');
  console.log('  /api/version:', ver);
  console.log('  root (200=UI ok):', root);
  console.log('  bundle servido:', bundle);

  c.end();
  if (!active) { console.error('\n⚠ Rollback não subiu o container!'); process.exit(1); }
  console.log('\n=== ROLLBACK OK — stable-prev restaurado ===');
}

main().catch(e => { console.error('\nFALHA:', e.message); process.exit(1); });
