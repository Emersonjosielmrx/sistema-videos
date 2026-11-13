// Recria SÓ o container hermes-call:beta com o env corrigido (aspas simples pro
// token Asaas que começa com "$"). Não rebuilda a imagem — só sobe o container de novo.
const { Client } = require('ssh2');
const fs = require('fs');
const path = require('path');

const HOST = '62.171.128.241', USER = 'root', PASS = 'sW5pgAG9obRu2';
const CONTAINER = 'hermes-call', IMAGE_BETA = 'hermes-call:beta';
const DB_URL = 'postgres://hermes_call_v3test:hermes_call_v3test@localhost:5432/wacalls_main?sslmode=disable';
const TG_TOKEN = '<SEGREDO_REMOVIDO>';

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

function run(c, cmd) {
  return new Promise((res, rej) => {
    c.exec(cmd, (err, stream) => {
      if (err) return rej(err);
      let out = '';
      stream.on('data', d => out += d);
      stream.stderr.on('data', d => out += d);
      stream.on('close', () => res(out));
    });
  });
}

let env = '';
const add = (k, v) => { if (v) env += "-e '" + k + "=" + v + "' "; };
add('HERMES_ASAAS_API_KEY', envFromDeploy('HERMES_ASAAS_API_KEY'));
add('HERMES_ASAAS_API_URL', envFromDeploy('HERMES_ASAAS_API_URL'));
add('HERMES_ASAAS_WEBHOOK_TOKEN', envFromDeploy('HERMES_ASAAS_WEBHOOK_TOKEN'));
for (const k of ['HERMES_GOOGLE_CLIENT_ID','HERMES_GOOGLE_CLIENT_SECRET','HERMES_GOOGLE_REDIRECT_URL','HERMES_OAUTH_SUCCESS_URL']) add(k, envFromDeploy(k));
add('HERMES_ADMIN_EMAIL', envFromDeploy('HERMES_ADMIN_EMAIL') || 'admin@hermescall.com');
add('HERMES_MONITOR_BOT_TOKEN', envFromDeploy('HERMES_MONITOR_BOT_TOKEN'));
add('HERMES_MONITOR_CHAT_ID', envFromDeploy('HERMES_MONITOR_CHAT_ID'));
add('HERMES_FREE_COUPONS', envFromDeploy('HERMES_FREE_COUPONS'));

const runCmd = 'docker run -d --name ' + CONTAINER + ' --restart=always --network host ' +
  "-e 'WACALLS_PG_URL=" + DB_URL + "' " +
  "-e 'PORT=8080' " +
  "-e 'HERMES_TELEGRAM_TOKEN=" + TG_TOKEN + "' " +
  env + IMAGE_BETA + ' 2>&1';

const c = new Client();
c.on('ready', async () => {
  console.log('[stop/rm container antigo]');
  console.log(await run(c, 'docker rm -f ' + CONTAINER + ' 2>/dev/null; echo ok'));
  console.log('[sobe container novo]');
  console.log(await run(c, runCmd));
  await new Promise(r => setTimeout(r, 8000));
  console.log('[verify] key Asaas no container:');
  console.log(await run(c, 'docker exec ' + CONTAINER + ' printenv HERMES_ASAAS_API_KEY | sed "s/\\(.\\{14\\}\\).*/\\1.../"'));
  console.log('[verify] version:', (await run(c, 'curl -s http://127.0.0.1:8080/api/version')).trim());
  c.end();
}).connect({ host: HOST, username: USER, password: PASS });
