// SOMENTE LEITURA na VPS .53 (referência mais nova). NÃO altera, NÃO para, NÃO remove
// NADA. Só lê: qual imagem/container roda o Hermes lá, qual bundle serve, e se dá pra
// identificar a imagem no Docker Hub. Regra: .53 é INTOCÁVEL (só leitura).
const { Client } = require('ssh2');
const fs = require('fs'), path = require('path');
function envFromDeploy(key){const p=path.join(__dirname,'.env.deploy');for(const l of fs.readFileSync(p,'utf8').split('\n')){const m=l.match(new RegExp('^\\s*'+key+'\\s*=\\s*(.+?)\\s*$'));if(m)return m[1];}return process.env[key]||'';}
const HOST=envFromDeploy('PROD_VPS_HOST'),USER=envFromDeploy('PROD_VPS_USER'),PASS=envFromDeploy('PROD_VPS_PASS');
function run(c,cmd){return new Promise((res,rej)=>{c.exec(cmd,(e,s)=>{if(e)return rej(e);let o='';s.on('data',d=>o+=d);s.stderr.on('data',d=>o+=d);s.on('close',()=>res(o));});});}
const c=new Client();
c.on('ready',async()=>{
  console.log('=== .53 (REFERÊNCIA, somente leitura) ===');
  console.log('--- docker ps (tudo que parece hermes) ---');
  console.log(await run(c,"docker ps --format '{{.Names}} | {{.Image}} | {{.Status}} | {{.Ports}}' 2>/dev/null | grep -iE 'hermes|call|inovare' || echo 'nenhum via nome'"));
  console.log('--- docker service (Swarm?) ---');
  console.log(await run(c,"docker service ls 2>/dev/null | grep -iE 'hermes|call|inovare' || echo 'sem swarm/servico hermes'"));
  console.log('--- imagens hermes/inovare no host .53 ---');
  console.log(await run(c,"docker images --format '{{.Repository}}:{{.Tag}} | {{.ID}} | {{.CreatedSince}} | {{.Size}}' 2>/dev/null | grep -iE 'hermes|call|inovare' | head -20 || echo nenhuma"));
  console.log('--- bundle JS servido pela landing (identifica a versão do front) ---');
  console.log('via localhost:8080:', (await run(c,"curl -s http://127.0.0.1:8080/ 2>/dev/null | grep -oE 'index-[A-Za-z0-9_]+\\.js' | head -1")).trim() || 'sem resposta 8080');
  console.log('/api/version localhost:8080:', (await run(c,'curl -s --max-time 6 http://127.0.0.1:8080/api/version 2>/dev/null')).trim() || 'sem resposta');
  console.log('--- procura porta do container hermes se não for 8080 ---');
  console.log(await run(c,"docker ps --format '{{.Names}} {{.Ports}}' 2>/dev/null | grep -iE 'hermes|inovare' || echo nenhum"));
  c.end();
}).on('error',e=>console.error('SSH ERRO (.53):',e.message)).connect({host:HOST,username:USER,password:PASS,readyTimeout:30000});
