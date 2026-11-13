// Volta o container da .241 pra GOLDEN (fabricadeautomacoesia/hermes-call:v0.2.1),
// que é IDÊNTICA à versão de referência que roda na .53 (mesmo image id 21c83411cfd1).
// Preserva as envs do Asaas (o rollback.js padrão não injeta). NÃO toca na .53.
const { Client } = require('ssh2');
const fs = require('fs'), path = require('path');
function envFromDeploy(key){const p=path.join(__dirname,'.env.deploy');for(const l of fs.readFileSync(p,'utf8').split('\n')){const m=l.match(new RegExp('^\\s*'+key+'\\s*=\\s*(.+?)\\s*$'));if(m)return m[1];}return process.env[key]||'';}
const HOST=envFromDeploy('HERMES_VPS_HOST'),USER=envFromDeploy('HERMES_VPS_USER'),PASS=envFromDeploy('HERMES_VPS_PASS');
const GOLDEN='fabricadeautomacoesia/hermes-call:v0.2.1';
const DB_URL='postgres://hermes_call_v3test:hermes_call_v3test@localhost:5432/wacalls_main?sslmode=disable';
const TG=envFromDeploy('HERMES_TELEGRAM_TOKEN')||'<SEGREDO_REMOVIDO>';
function run(c,cmd){return new Promise((res,rej)=>{c.exec(cmd,(e,s)=>{if(e)return rej(e);let o='';s.on('data',d=>o+=d);s.stderr.on('data',d=>o+=d);s.on('close',()=>res(o));});});}
const sq=v=>"'"+String(v).replace(/'/g,"'\\''")+"'";
const c=new Client();
c.on('ready',async()=>{
  console.log('=== RESTORE GOLDEN (.241) preservando Asaas ===');
  // monta envs (mesma lógica do deploy-beta: Asaas + Google + admin + monitor + coupons)
  let env='';
  const add=(k,v)=>{if(v)env+='-e '+sq(k+'='+v)+' ';};
  add('HERMES_ASAAS_API_KEY',envFromDeploy('HERMES_ASAAS_API_KEY'));
  add('HERMES_ASAAS_API_URL',envFromDeploy('HERMES_ASAAS_API_URL'));
  add('HERMES_ASAAS_WEBHOOK_TOKEN',envFromDeploy('HERMES_ASAAS_WEBHOOK_TOKEN'));
  for(const k of ['HERMES_GOOGLE_CLIENT_ID','HERMES_GOOGLE_CLIENT_SECRET','HERMES_GOOGLE_REDIRECT_URL','HERMES_OAUTH_SUCCESS_URL']) add(k,envFromDeploy(k));
  add('HERMES_ADMIN_EMAIL',envFromDeploy('HERMES_ADMIN_EMAIL')||'admin@hermescall.com');
  add('HERMES_MONITOR_BOT_TOKEN',envFromDeploy('HERMES_MONITOR_BOT_TOKEN'));
  add('HERMES_MONITOR_CHAT_ID',envFromDeploy('HERMES_MONITOR_CHAT_ID'));
  add('HERMES_FREE_COUPONS',envFromDeploy('HERMES_FREE_COUPONS'));
  const runCmd='docker run -d --name hermes-call --restart=always --network host '+
    '-e '+sq('WACALLS_PG_URL='+DB_URL)+' -e '+sq('PORT=8080')+' -e '+sq('HERMES_TELEGRAM_TOKEN='+TG)+' '+
    env+GOLDEN+' 2>&1';
  console.log('[rm beta]', (await run(c,'docker rm -f hermes-call 2>&1; echo ok')).trim());
  console.log('[run golden]', (await run(c,runCmd)).trim());
  await new Promise(r=>setTimeout(r,9000));
  console.log('[verify] status:', (await run(c,"docker ps --filter name=hermes-call --format '{{.Image}} | {{.Status}}'")).trim());
  console.log('[verify] version:', (await run(c,'curl -s http://127.0.0.1:8080/api/version')).trim());
  console.log('[verify] bundle servido:', (await run(c,"curl -s http://127.0.0.1:8080/ | grep -oE 'index-[A-Za-z0-9_]+\\.js' | head -1")).trim(), '(golden = index-BYgTiieN.js)');
  console.log('[verify] Asaas envs:', (await run(c,"docker exec hermes-call printenv 2>/dev/null | grep -oE '^HERMES_ASAAS[A-Z_]*' | tr '\\n' ' '")).trim());
  console.log('[verify] root UI:', (await run(c,'curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8080/')).trim());
  c.end();
}).on('error',e=>console.error('SSH ERRO:',e.message)).connect({host:HOST,username:USER,password:PASS,readyTimeout:30000});
