#!/usr/bin/env node
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
  const c = await connect();

  console.log('[1] Stopping Docker container hermes-call...');
  console.log(await run(c, 'docker stop hermes-call && docker rm hermes-call'));

  console.log('[2] Restarting systemd hermes-call...');
  await run(c, 'systemctl restart hermes-call');
  await new Promise(r => setTimeout(r, 6000));

  const active = (await run(c, 'systemctl is-active hermes-call')).trim();
  const ver = (await run(c, 'curl -s http://127.0.0.1:8080/api/version')).trim();
  const root = (await run(c, 'curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8080/')).trim();
  const ss = await run(c, 'ss -tlnp | grep :8080');
  const logs = (await run(c, 'journalctl -u hermes-call --no-pager -n 5')).trim();

  console.log('\nService:', active);
  console.log('Version:', ver);
  console.log('Root:', root);
  console.log('Port:', ss.trim());
  console.log('Logs:', logs);

  c.end();
  if (active !== 'active') process.exit(1);
  console.log('\n=== OK ===');
}

main().catch(e => { console.error('FAIL:', e.message); process.exit(1); });
