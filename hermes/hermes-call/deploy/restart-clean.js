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

  console.log('Stopping service and killing orphans...');
  await run(c, 'systemctl stop hermes-call');
  await new Promise(r => setTimeout(r, 2000));
  const pids = (await run(c, "lsof -ti :8080 2>/dev/null || true")).trim();
  if (pids) {
    console.log('Killing PIDs on :8080:', pids);
    await run(c, `kill -9 ${pids.replace(/\n/g, ' ')}`);
    await new Promise(r => setTimeout(r, 1000));
  }

  console.log('Copying fresh binary...');
  await run(c, 'cp /opt/hipercool-refactor/hermes-call-linux /opt/hermes-call/hermes-call && chmod +x /opt/hermes-call/hermes-call');

  console.log('Starting service...');
  await run(c, 'systemctl start hermes-call');
  await new Promise(r => setTimeout(r, 6000));

  const active = (await run(c, 'systemctl is-active hermes-call')).trim();
  const ver = (await run(c, 'curl -s http://127.0.0.1:8080/api/version')).trim();
  const logs = await run(c, 'journalctl -u hermes-call --no-pager -n 5');

  console.log('Service:', active);
  console.log('Version:', ver);
  console.log('Logs:', logs);

  c.end();
}

main().catch(e => { console.error('FAIL:', e.message); process.exit(1); });
