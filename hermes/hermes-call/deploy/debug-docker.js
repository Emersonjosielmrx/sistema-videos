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

  console.log('=== Docker containers ===');
  console.log(await run(c, 'docker ps --format "table {{.Names}}\t{{.Image}}\t{{.Ports}}\t{{.Status}}" 2>/dev/null || echo "docker not running"'));

  console.log('=== Process details for wacalls PID ===');
  console.log(await run(c, 'ls -la /proc/3526922/exe 2>/dev/null || echo "PID gone"'));
  console.log(await run(c, 'cat /proc/3526922/cgroup 2>/dev/null | head -5 || echo "PID gone"'));

  c.end();
}

main().catch(e => { console.error('FAIL:', e.message); process.exit(1); });
