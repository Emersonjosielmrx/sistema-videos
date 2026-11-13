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

  console.log('=== All wacalls processes ===');
  console.log(await run(c, 'ps aux | grep wacalls | grep -v grep'));

  console.log('=== Systemd services related ===');
  console.log(await run(c, 'systemctl list-units --type=service | grep -i "wacalls\\|hermes"'));

  console.log('=== wacalls service file ===');
  console.log(await run(c, 'cat /etc/systemd/system/wacalls.service 2>/dev/null || echo "not found"'));

  console.log('=== hermes-call service file ===');
  console.log(await run(c, 'cat /etc/systemd/system/hermes-call.service 2>/dev/null || echo "not found"'));

  c.end();
}

main().catch(e => { console.error('FAIL:', e.message); process.exit(1); });
