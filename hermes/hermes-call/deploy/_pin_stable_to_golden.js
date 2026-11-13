// Aponta hermes-call:stable para a GOLDEN exata que está no ar agora, pra que
// rollback.js volte pra ela (e não pra uma :stable antiga/errada).
// Também cria uma tag datada de segurança. NÃO derruba nada.
const { Client } = require('ssh2');
const fs = require('fs'), path = require('path');
function envFromDeploy(key){const p=path.join(__dirname,'.env.deploy');for(const l of fs.readFileSync(p,'utf8').split('\n')){const m=l.match(new RegExp('^\\s*'+key+'\\s*=\\s*(.+?)\\s*$'));if(m)return m[1];}return process.env[key]||'';}
const HOST=envFromDeploy('HERMES_VPS_HOST'),USER=envFromDeploy('HERMES_VPS_USER'),PASS=envFromDeploy('HERMES_VPS_PASS');
function run(c,cmd){return new Promise((res,rej)=>{c.exec(cmd,(e,s)=>{if(e)return rej(e);let o='';s.on('data',d=>o+=d);s.stderr.on('data',d=>o+=d);s.on('close',()=>res(o));});});}
const GOLDEN='fabricadeautomacoesia/hermes-call:v0.2.1';
const c=new Client();
c.on('ready',async()=>{
  console.log('=== fixar :stable -> golden ===');
  console.log('golden id:', (await run(c,'docker images -q '+GOLDEN)).trim());
  console.log(':stable ANTES:', (await run(c,'docker images -q hermes-call:stable')).trim());
  // preserva a :stable antiga com nome datado (não perder nada)
  console.log(await run(c,'docker tag hermes-call:stable hermes-call:stable-prev-20260726 2>/dev/null; echo "prev preservada (se existia)"'));
  // aponta :stable e :stable-prev-golden pra golden
  await run(c,'docker tag '+GOLDEN+' hermes-call:stable');
  await run(c,'docker tag '+GOLDEN+' hermes-call:golden-restore-point');
  console.log(':stable DEPOIS:', (await run(c,'docker images -q hermes-call:stable')).trim(), '(deve == golden id)');
  console.log('golden-restore-point:', (await run(c,'docker images -q hermes-call:golden-restore-point')).trim());
  c.end();
}).on('error',e=>console.error('SSH ERRO:',e.message)).connect({host:HOST,username:USER,password:PASS,readyTimeout:30000});
