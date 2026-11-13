// SOMENTE LEITURA — inspeciona o container hermes-call na VPS .241.
// Não cria, não para, não remove nada. Só coleta estado pra documentar backup.
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

const c = new Client();
c.on('ready', async () => {
  console.log('=== HOST', HOST, '===');
  console.log('--- docker ps (hermes) ---');
  console.log(await run(c, 'docker ps -a --filter name=hermes --format "{{.Names}}\t{{.Image}}\t{{.Status}}"'));
  console.log('--- imagem exata + digest do container em execução ---');
  console.log(await run(c, "docker inspect hermes-call --format '{{.Config.Image}}' 2>/dev/null"));
  console.log(await run(c, "docker inspect hermes-call --format '{{.Image}}' 2>/dev/null"));
  console.log('--- RepoDigests da imagem ---');
  const img = (await run(c, "docker inspect hermes-call --format '{{.Config.Image}}' 2>/dev/null")).trim();
  console.log(await run(c, "docker inspect " + img + " --format '{{json .RepoDigests}}' 2>/dev/null"));
  console.log(await run(c, "docker inspect " + img + " --format '{{json .RepoTags}}' 2>/dev/null"));
  console.log('--- envs ASAAS presentes no container (só nomes) ---');
  console.log(await run(c, "docker exec hermes-call printenv 2>/dev/null | grep -oE '^HERMES_ASAAS[A-Z_]*' || echo 'NENHUMA env ASAAS'"));
  console.log('--- todas as envs HERMES_ (só nomes, sem valores) ---');
  console.log(await run(c, "docker exec hermes-call printenv 2>/dev/null | grep -oE '^(HERMES_[A-Z_]*|WACALLS_[A-Z_]*|PORT)=' | sed 's/=$//' | sort"));
  console.log('--- version + billing status ---');
  console.log('version:', (await run(c, 'curl -s http://127.0.0.1:8080/api/version')).trim());
  console.log('billing:', (await run(c, 'curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8080/api/billing')).trim());
  console.log('--- imagens hermes-call locais na VPS ---');
  console.log(await run(c, "docker images --filter reference='*hermes-call*' --format '{{.Repository}}:{{.Tag}}\t{{.ID}}\t{{.CreatedSince}}\t{{.Size}}'"));
  c.end();
}).on('error', e => console.error('SSH ERRO:', e.message)).connect({ host: HOST, username: USER, password: PASS });
