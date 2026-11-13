// SOMENTE LEITURA — estado da VPS antes do deploy. Confirma imagem em execução,
// o que :stable aponta, e conectividade SSH (sem brute-force).
const { Client } = require('ssh2');
const fs = require('fs'), path = require('path');
function envFromDeploy(key){const p=path.join(__dirname,'.env.deploy');for(const l of fs.readFileSync(p,'utf8').split('\n')){const m=l.match(new RegExp('^\\s*'+key+'\\s*=\\s*(.+?)\\s*$'));if(m)return m[1];}return process.env[key]||'';}
const HOST=envFromDeploy('HERMES_VPS_HOST'),USER=envFromDeploy('HERMES_VPS_USER'),PASS=envFromDeploy('HERMES_VPS_PASS');
function run(c,cmd){return new Promise((res,rej)=>{c.exec(cmd,(e,s)=>{if(e)return rej(e);let o='';s.on('data',d=>o+=d);s.stderr.on('data',d=>o+=d);s.on('close',()=>res(o));});});}
const c=new Client();
c.on('ready',async()=>{
  console.log('=== estado VPS',HOST,'===');
  console.log('container em execução:');
  console.log(await run(c,"docker ps --filter name=hermes-call --format '{{.Names}} | {{.Image}} | {{.Status}}'"));
  console.log('imagem do container (Config.Image):', (await run(c,"docker inspect hermes-call --format '{{.Config.Image}}' 2>/dev/null")).trim());
  console.log('digest da imagem em execução:');
  const img=(await run(c,"docker inspect hermes-call --format '{{.Config.Image}}' 2>/dev/null")).trim();
  console.log(await run(c,"docker inspect "+img+" --format '{{json .RepoDigests}}' 2>/dev/null"));
  console.log(':stable aponta pra (image id):', (await run(c,'docker images -q hermes-call:stable')).trim() || 'NÃO EXISTE');
  console.log('golden v0.2.1 image id:', (await run(c,'docker images -q fabricadeautomacoesia/hermes-call:v0.2.1')).trim());
  console.log('REMOTE_SRC existe?', (await run(c,'test -d /opt/hipercool-refactor && echo sim || echo NAO')).trim());
  console.log('billing atual:', (await run(c,'curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8080/api/billing')).trim());
  c.end();
}).on('error',e=>console.error('SSH ERRO:',e.message)).connect({host:HOST,username:USER,password:PASS,readyTimeout:30000});
