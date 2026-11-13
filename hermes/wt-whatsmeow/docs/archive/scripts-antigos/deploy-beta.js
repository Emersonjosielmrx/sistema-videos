// Deploy Hermes Call beta → VPS 62.171.128.241
// Faz: build Go, build Vite, SCP do binário e dist/, restart do systemd service.
//
// Uso:  node deploy-beta.js [commit-msg]
// Sem args: deploy silencioso, imprime só status final.
// Com arg: usado como descrição no log remoto.
const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

const VPS = process.env.VPS_HOST || '62.171.128.241';
const VPS_USER = process.env.VPS_USER || 'root';
const REMOTE_DIR = process.env.VPS_DIR || '/opt/hermes-call';
const SERVICE = 'hermescall';
const SSH_KEY = process.env.VPS_KEY || process.env.SSH_KEY_PATH || '';

const run = (cmd, opts = {}) => {
  console.log('$', cmd);
  try {
    return execSync(cmd, { stdio: 'inherit', ...opts });
  } catch (e) {
    if (!opts.allowFail) throw e;
    return null;
  }
};

const scp = (src, dst) => {
  const keyArg = SSH_KEY ? `-i "${SSH_KEY}"` : '';
  run(`scp ${keyArg} -o StrictHostKeyChecking=no ${src} ${VPS_USER}@${VPS}:${dst}`);
};

const ssh = (cmd) => {
  const keyArg = SSH_KEY ? `-i "${SSH_KEY}"` : '';
  run(`ssh ${keyArg} -o StrictHostKeyChecking=no ${VPS_USER}@${VPS} "${cmd}"`);
};

(async () => {
  const stamp = new Date().toISOString().replace(/[-:T]/g, '').slice(0, 14);
  console.log(`\n=== DEPLOY BETA ${stamp} ===\n`);

  // 1) build Go
  console.log('--- building Go binary ---');
  // resolve caminho do go.exe (em Git Bash o "/c/Program Files/Go/bin/go.exe"
  // funciona; em cmd.exe do node precisa aspas duplas).
  const isWin = process.platform === 'win32';
  const goBin = isWin ? '"C:\\Program Files\\Go\\bin\\go.exe"' : 'go';
  run(`${goBin} build -o ./bin/hermescall ./cmd/server`, { cwd: __dirname });

  // 2) build Vite
  console.log('--- building Vite client ---');
  run('npm run build', { cwd: path.join(__dirname, 'client') });

  // 3) compressa tudo num tar.gz pra 1 SCP só
  const tarName = `hermescall-${stamp}.tar.gz`;
  console.log(`--- packaging ${tarName} ---`);
  run(`tar -czf ${tarName} bin/hermescall client/dist`);

  // 4) sobe o tar.gz
  console.log('--- uploading to VPS ---');
  scp(tarName, `${REMOTE_DIR}/`);

  // 5) descompacta e reinicia
  console.log('--- extracting + restarting service ---');
  ssh(`cd ${REMOTE_DIR} && tar -xzf ${tarName} && rm ${tarName} && systemctl restart ${SERVICE} && sleep 2 && systemctl is-active ${SERVICE}`);

  // 6) health check
  console.log('--- health check ---');
  ssh(`curl -s -o /dev/null -w 'HTTP %{http_code}\\n' http://127.0.0.1:8080/healthz || true`);

  // limpa tar.gz local
  try { fs.unlinkSync(tarName); } catch {}

  console.log(`\n=== DONE ${stamp} ===\n`);
})().catch((e) => {
  console.error('DEPLOY FAILED:', e.message);
  process.exit(1);
});