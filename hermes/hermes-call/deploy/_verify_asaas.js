// SOMENTE LEITURA — verifica se o Asaas inicializou de fato e se o 401 do /api/billing
// é auth-middleware (endpoint protegido) e não "asaas não configurado".
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
const HOST = envFromDeploy('HERMES_VPS_HOST'), USER = envFromDeploy('HERMES_VPS_USER'), PASS = envFromDeploy('HERMES_VPS_PASS');
function run(c, cmd) {
  return new Promise((res, rej) => {
    c.exec(cmd, (err, stream) => {
      if (err) return rej(err);
      let out = ''; stream.on('data', d => out += d); stream.stderr.on('data', d => out += d);
      stream.on('close', () => res(out));
    });
  });
}
const c = new Client();
c.on('ready', async () => {
  console.log('--- logs de inicialização (asaas/billing) ---');
  console.log(await run(c, "docker logs hermes-call 2>&1 | grep -iE 'asaas|billing|payment' | head -30 || echo 'sem match'"));
  console.log('--- últimas 25 linhas de log ---');
  console.log(await run(c, "docker logs --tail 25 hermes-call 2>&1"));
  console.log('--- endpoints /api que respondem sem auth ---');
  for (const ep of ['/api/version', '/api/health', '/api/billing', '/api/billing/plans', '/api/plans']) {
    const code = (await run(c, `curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8080${ep}`)).trim();
    console.log(ep, '->', code);
  }
  console.log('--- valor real da env Asaas URL no container (não é segredo) ---');
  console.log(await run(c, "docker exec hermes-call printenv HERMES_ASAAS_API_URL"));
  console.log('--- API_KEY presente? (só tamanho, sem vazar) ---');
  console.log(await run(c, "docker exec hermes-call sh -c 'printenv HERMES_ASAAS_API_KEY | wc -c' 2>/dev/null"));
  c.end();
}).on('error', e => console.error('SSH ERRO:', e.message)).connect({ host: HOST, username: USER, password: PASS });
