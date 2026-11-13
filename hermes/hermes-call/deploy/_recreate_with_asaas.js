// Recria o container hermes-call na VPS .241 com a MESMA imagem golden v0.2.1,
// preservando EXATAMENTE as envs atuais (lidas do próprio container) e ADICIONANDO
// só as 3 envs do Asaas. Backup já foi feito por _backup_pre_asaas.js.
const { Client } = require('ssh2');
const fs = require('fs');
const path = require('path');

function envFromDeploy(key) {
  const p = path.join(__dirname, '.env.deploy');
  for (const line of fs.readFileSync(p, 'utf8').split('\n')) {
    const m = line.match(new RegExp('^\\s*' + key + '\\s*=\\s*(.+?)\\s*$'));
    if (m) return m[1];
  }
  return process.env[key] || '';
}
const HOST = envFromDeploy('HERMES_VPS_HOST');
const USER = envFromDeploy('HERMES_VPS_USER');
const PASS = envFromDeploy('HERMES_VPS_PASS');
const IMAGE = 'fabricadeautomacoesia/hermes-call:v0.2.1';

const ASAAS_KEY = envFromDeploy('HERMES_ASAAS_API_KEY');
const ASAAS_URL = envFromDeploy('HERMES_ASAAS_API_URL');
const ASAAS_TOK = envFromDeploy('HERMES_ASAAS_WEBHOOK_TOKEN');

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

// Aspas simples pra valores; escapa aspas simples internas.
const sq = v => "'" + String(v).replace(/'/g, "'\\''") + "'";

const c = new Client();
c.on('ready', async () => {
  // 1) Captura as envs atuais do container (preserva o que já existe).
  const cur = await run(c, "docker exec hermes-call printenv 2>/dev/null");
  const envMap = {};
  for (const line of cur.split('\n')) {
    const i = line.indexOf('=');
    if (i > 0) envMap[line.slice(0, i)] = line.slice(i + 1);
  }
  // Só mantemos as envs de app relevantes (evita PATH/HOSTNAME do docker default).
  const KEEP = ['WACALLS_PG_URL', 'PORT', 'HERMES_TELEGRAM_TOKEN'];
  const preserved = {};
  for (const k of KEEP) if (envMap[k]) preserved[k] = envMap[k];
  // Também preserva qualquer HERMES_* / WACALLS_* extra que já exista.
  for (const k of Object.keys(envMap)) {
    if ((k.startsWith('HERMES_') || k.startsWith('WACALLS_')) && !preserved[k]) preserved[k] = envMap[k];
  }
  console.log('[envs preservadas do container atual]:', Object.keys(preserved).join(', '));

  // 2) Adiciona Asaas.
  preserved['HERMES_ASAAS_API_KEY'] = ASAAS_KEY;
  preserved['HERMES_ASAAS_API_URL'] = ASAAS_URL;
  preserved['HERMES_ASAAS_WEBHOOK_TOKEN'] = ASAAS_TOK;
  console.log('[envs Asaas adicionadas]: HERMES_ASAAS_API_KEY, HERMES_ASAAS_API_URL, HERMES_ASAAS_WEBHOOK_TOKEN');

  let envArgs = '';
  for (const [k, v] of Object.entries(preserved)) envArgs += '-e ' + sq(k + '=' + v) + ' ';

  const runCmd = 'docker run -d --name hermes-call --restart=always --network host ' +
    envArgs + IMAGE + ' 2>&1';

  // 3) Remove o container atual (backup já garantido) e sobe o novo.
  console.log('[rm container atual]');
  console.log(await run(c, 'docker rm -f hermes-call 2>&1; echo rm-ok'));
  console.log('[sobe container novo com Asaas]');
  console.log(await run(c, runCmd));

  await new Promise(r => setTimeout(r, 9000));

  console.log('[verify] status:');
  console.log(await run(c, 'docker ps --filter name=hermes-call --format "{{.Names}}\t{{.Image}}\t{{.Status}}"'));
  console.log('[verify] envs Asaas no container (só nomes):');
  console.log(await run(c, "docker exec hermes-call printenv 2>/dev/null | grep -oE '^HERMES_ASAAS[A-Z_]*' || echo NENHUMA"));
  console.log('[verify] version:', (await run(c, 'curl -s http://127.0.0.1:8080/api/version')).trim());
  console.log('[verify] billing HTTP:', (await run(c, 'curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8080/api/billing')).trim());
  console.log('[verify] billing body (head):', (await run(c, 'curl -s http://127.0.0.1:8080/api/billing | head -c 300')).trim());
  c.end();
}).on('error', e => console.error('SSH ERRO:', e.message)).connect({ host: HOST, username: USER, password: PASS });
