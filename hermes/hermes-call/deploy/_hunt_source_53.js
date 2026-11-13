// SOMENTE LEITURA na .53 — caça o CÓDIGO-FONTE que gerou a imagem boa (v0.2.1).
// NÃO altera/para/remove nada. Só lista diretórios de source e metadados da imagem.
const { Client } = require('ssh2');
const fs = require('fs'), path = require('path');
function envFromDeploy(key){const p=path.join(__dirname,'.env.deploy');for(const l of fs.readFileSync(p,'utf8').split('\n')){const m=l.match(new RegExp('^\\s*'+key+'\\s*=\\s*(.+?)\\s*$'));if(m)return m[1];}return process.env[key]||'';}
const HOST=envFromDeploy('PROD_VPS_HOST'),USER=envFromDeploy('PROD_VPS_USER'),PASS=envFromDeploy('PROD_VPS_PASS');
function run(c,cmd){return new Promise((res,rej)=>{c.exec(cmd,(e,s)=>{if(e)return rej(e);let o='';s.on('data',d=>o+=d);s.stderr.on('data',d=>o+=d);s.on('close',()=>res(o));});});}
const c=new Client();
c.on('ready',async()=>{
  console.log('=== CAÇA AO SOURCE na .53 (somente leitura) ===');
  console.log('--- diretórios de source candidatos ---');
  for(const d of ['/root/hermes-call','/opt/hipercool-refactor','/root/hermes-call-v3','/root/inovare','/opt/hermes-call','/root/hermes_call_refactor']){
    console.log(d+':', (await run(c,`test -d ${d} && echo EXISTE || echo nao`)).trim());
  }
  console.log('--- procura package.json/go.mod recentes (source real) fora de node_modules ---');
  console.log(await run(c,"find /root /opt -maxdepth 3 -name 'go.mod' -not -path '*/node_modules/*' 2>/dev/null | head -20"));
  console.log('--- procura client/src (frontend source .tsx) ---');
  console.log(await run(c,"find /root /opt -maxdepth 4 -type d -name 'src' -path '*client*' 2>/dev/null | head; find /root /opt -maxdepth 4 -type d -name 'client' 2>/dev/null | head"));
  console.log('--- metadados da imagem boa: labels/history (de onde veio) ---');
  console.log(await run(c,"docker inspect fabricadeautomacoesia/hermes-call:v0.2.1 --format '{{json .Config.Labels}}' 2>/dev/null"));
  console.log('--- a imagem tem o source .tsx embutido? (raro, mas checa) ---');
  console.log(await run(c,"docker run --rm --entrypoint sh fabricadeautomacoesia/hermes-call:v0.2.1 -c 'ls /app 2>/dev/null; echo ---; find / -maxdepth 4 -name \"*.tsx\" 2>/dev/null | head -3; echo ---; ls -la /app/client 2>/dev/null' 2>&1 | head -30"));
  console.log('--- git remoto no source Swarm (se existir) ---');
  console.log(await run(c,"for d in /root/hermes-call /root/hermes-call-v3 /root/inovare; do test -d $d/.git && echo \"$d -> $(cd $d && git remote -v 2>/dev/null | head -1) | branch $(cd $d && git branch --show-current 2>/dev/null) | last $(cd $d && git log -1 --format=%cd,%s 2>/dev/null)\"; done"));
  c.end();
}).on('error',e=>console.error('SSH ERRO (.53):',e.message)).connect({host:HOST,username:USER,password:PASS,readyTimeout:30000});
