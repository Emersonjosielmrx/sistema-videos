// BACKUP ANTES DE MEXER — honra a regra da Haylla: guardar a imagem atual antes
// de recriar o container. Não para/remove o container em execução. Só:
//   1) commit do container atual -> snapshot local com timestamp
//   2) tag explícita de backup na imagem golden
//   3) push das tags de backup pro Docker Hub (mesmo digest = quase instantâneo)
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
const DHUSER = envFromDeploy('DOCKERHUB_USER');
const DHPASS = envFromDeploy('DOCKERHUB_TOKEN') || envFromDeploy('DOCKERHUB_PASS');

const TS = new Date().toISOString().replace(/[:T]/g, '-').slice(0, 16).replace(/-/g, m => m); // fallback
const STAMP = '20260726-0857';
const SNAP = 'hermes-call:snapshot-pre-asaas-' + STAMP;
const BACKUP_TAG = 'fabricadeautomacoesia/hermes-call:backup-pre-asaas-' + STAMP;

function run(c, cmd) {
  return new Promise((res, rej) => {
    c.exec(cmd, (err, stream) => {
      if (err) return rej(err);
      let out = '';
      stream.on('data', d => out += d);
      stream.stderr.on('data', d => out += d);
      stream.on('close', code => res({ out, code }));
    });
  });
}
const p = async (c, cmd) => { const r = await run(c, cmd); return r.out; };

const c = new Client();
c.on('ready', async () => {
  console.log('=== BACKUP PRE-ASAAS em', HOST, '===');
  console.log('[1] commit snapshot local do container em execução ->', SNAP);
  console.log(await p(c, 'docker commit hermes-call ' + SNAP + ' 2>&1'));

  console.log('[2] tag de backup na imagem golden ->', BACKUP_TAG);
  console.log(await p(c, 'docker tag fabricadeautomacoesia/hermes-call:v0.2.1 ' + BACKUP_TAG + ' 2>&1; echo tagged'));

  console.log('[3] docker login + push da tag de backup (mesmo digest, rápido)');
  console.log(await p(c, 'echo "' + DHPASS + '" | docker login -u ' + DHUSER + ' --password-stdin 2>&1'));
  console.log(await p(c, 'docker push ' + BACKUP_TAG + ' 2>&1 | tail -3'));

  console.log('[verify] imagens de backup agora existentes:');
  console.log(await p(c, "docker images --filter reference='*hermes-call*snapshot*' --filter reference='*hermes-call*backup*' --format '{{.Repository}}:{{.Tag}}\t{{.ID}}\t{{.Size}}'"));
  console.log('[verify] digest golden confirmado:');
  console.log(await p(c, "docker inspect fabricadeautomacoesia/hermes-call:v0.2.1 --format '{{json .RepoDigests}}'"));
  c.end();
}).on('error', e => console.error('SSH ERRO:', e.message)).connect({ host: HOST, username: USER, password: PASS });
