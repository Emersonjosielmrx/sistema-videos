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
      stream.on('close', (code) => res({ out, code }));
    });
  });
}

async function main() {
  console.log('Connecting...');
  const c = await connect();

  console.log('Checking if compiled binary exists...');
  const { out: ls } = await run(c, 'ls -lh /opt/hipercool-refactor/hermes-call-linux 2>&1');
  console.log(ls.trim());

  console.log('Copying binary to /opt/hermes-call/hermes-call...');
  const { out: cp } = await run(c, 'systemctl stop hermes-call && cp /opt/hipercool-refactor/hermes-call-linux /opt/hermes-call/hermes-call && chmod +x /opt/hermes-call/hermes-call');
  if (cp.trim()) console.log(cp.trim());

  console.log('Starting service...');
  await run(c, 'systemctl start hermes-call');
  await new Promise(r => setTimeout(r, 5000));

  const { out: active } = await run(c, 'systemctl is-active hermes-call');
  const { out: ver } = await run(c, 'curl -s http://127.0.0.1:8080/api/version');
  const { out: root } = await run(c, 'curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8080/');
  const { out: logs } = await run(c, 'journalctl -u hermes-call --no-pager -n 10');

  console.log('\nService:', active.trim());
  console.log('Version:', ver.trim());
  console.log('Root:', root.trim());
  console.log('--- Logs ---');
  console.log(logs);

  c.end();
  if (active.trim() !== 'active') { console.error('FAIL!'); process.exit(1); }
  console.log('=== OK ===');
}

main().catch(e => { console.error('FAIL:', e.message); process.exit(1); });
