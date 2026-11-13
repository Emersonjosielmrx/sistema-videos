// SOMENTE LEITURA — valida o deploy: version, endpoints reais, billing, sessões WhatsApp.
const { Client } = require('ssh2');
const fs = require('fs'), path = require('path');
function envFromDeploy(key){const p=path.join(__dirname,'.env.deploy');for(const l of fs.readFileSync(p,'utf8').split('\n')){const m=l.match(new RegExp('^\\s*'+key+'\\s*=\\s*(.+?)\\s*$'));if(m)return m[1];}return process.env[key]||'';}
const HOST=envFromDeploy('HERMES_VPS_HOST'),USER=envFromDeploy('HERMES_VPS_USER'),PASS=envFromDeploy('HERMES_VPS_PASS');
function run(c,cmd){return new Promise((res,rej)=>{c.exec(cmd,(e,s)=>{if(e)return rej(e);let o='';s.on('data',d=>o+=d);s.stderr.on('data',d=>o+=d);s.on('close',()=>res(o));});});}
const c=new Client();
c.on('ready',async()=>{
  console.log('=== pós-deploy verify ===');
  console.log('container:', (await run(c,"docker ps --filter name=hermes-call --format '{{.Image}} | {{.Status}}'")).trim());
  console.log('version:', (await run(c,'curl -s http://127.0.0.1:8080/api/version')).trim());
  console.log('root(UI):', (await run(c,'curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8080/')).trim());
  console.log('bundle JS servido:', (await run(c,"curl -s http://127.0.0.1:8080/ | grep -oE 'index-[A-Za-z0-9_]+\\.js' | head -1")).trim());
  console.log('--- endpoints (401=protegido OK, 200=publico, 404/500=problema) ---');
  for(const ep of ['/api/version','/api/billing','/api/billing/subscribe','/api/tts/preview','/api/analytics/crm/kpis','/api/projects','/api/sessions']){
    const code=(await run(c,`curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8080${ep}`)).trim();
    console.log('  '+code+'  '+ep);
  }
  console.log('--- Asaas envs no container ---');
  console.log(await run(c,"docker exec hermes-call printenv 2>/dev/null | grep -oE '^HERMES_ASAAS[A-Z_]*' || echo NENHUMA"));
  console.log('--- sessões WhatsApp restauradas ---');
  console.log((await run(c,'docker logs hermes-call 2>&1 | grep -iE "sessions restored|HTTP server listening" | tail -3')).trim());
  console.log('--- erros/panics no boot? ---');
  console.log((await run(c,'docker logs hermes-call 2>&1 | grep -iE "panic|fatal|level=ERROR" | tail -10')).trim() || '  nenhum erro/panic');
  console.log('--- imagens de restauração disponíveis ---');
  console.log(await run(c,"docker images --format '{{.Repository}}:{{.Tag}} {{.ID}}' | grep -E 'stable|golden|v0.2.1' | head"));
  c.end();
}).on('error',e=>console.error('SSH ERRO:',e.message)).connect({host:HOST,username:USER,password:PASS,readyTimeout:30000});
