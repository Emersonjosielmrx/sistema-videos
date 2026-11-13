// SOMENTE LEITURA na .53 — investiga /root/agentecall como candidato ao source da
// imagem boa. Compara sinais: bundle já buildado, páginas/abas, git, data dos arquivos.
const { Client } = require('ssh2');
const fs = require('fs'), path = require('path');
function envFromDeploy(key){const p=path.join(__dirname,'.env.deploy');for(const l of fs.readFileSync(p,'utf8').split('\n')){const m=l.match(new RegExp('^\\s*'+key+'\\s*=\\s*(.+?)\\s*$'));if(m)return m[1];}return process.env[key]||'';}
const HOST=envFromDeploy('PROD_VPS_HOST'),USER=envFromDeploy('PROD_VPS_USER'),PASS=envFromDeploy('PROD_VPS_PASS');
function run(c,cmd){return new Promise((res,rej)=>{c.exec(cmd,(e,s)=>{if(e)return rej(e);let o='';s.on('data',d=>o+=d);s.stderr.on('data',d=>o+=d);s.on('close',()=>res(o));});});}
const D='/root/agentecall';
const c=new Client();
c.on('ready',async()=>{
  console.log('=== /root/agentecall (candidato a SOURCE da versão boa) — leitura ===');
  console.log('--- topo do dir ---');
  console.log(await run(c,`ls -la ${D} 2>/dev/null | head -40`));
  console.log('--- git? ---');
  console.log(await run(c,`test -d ${D}/.git && (cd ${D} && echo "remote: $(git remote -v|head -1)"; echo "branch: $(git branch --show-current)"; echo "ultimo commit: $(git log -1 --format=%cd,%h,%s)"; echo "status limpo?: $(git status --short|wc -l) alterados") || echo "sem git"`));
  console.log('--- páginas do frontend (nomes das abas) ---');
  console.log(await run(c,`ls ${D}/client/src/pages/ 2>/dev/null`));
  console.log('--- tem dist buildado? qual bundle? (comparar com index-BYgTiieN.js da imagem boa) ---');
  console.log(await run(c,`ls ${D}/client/dist/assets/ 2>/dev/null | grep -oE 'index-[A-Za-z0-9_]+\\.(js|css)' | head`));
  console.log('--- VERSION / data de modificação recente do source ---');
  console.log('VERSION:', (await run(c,`cat ${D}/VERSION 2>/dev/null`)).trim());
  console.log('arquivos .tsx modificados mais recentes:');
  console.log(await run(c,`find ${D}/client/src -name '*.tsx' -printf '%TY-%Tm-%Td %p\\n' 2>/dev/null | sort -r | head -8`));
  console.log('--- procura marcas da versão reformulada (multi-linha, tour novo) ---');
  console.log(await run(c,`grep -rl 'Novo Hermes Call\\|LINHAS\\|Funcionário Gestor\\|Vitrine de Produtos\\|Antes vs Depois' ${D}/client/src 2>/dev/null | head`));
  c.end();
}).on('error',e=>console.error('SSH ERRO (.53):',e.message)).connect({host:HOST,username:USER,password:PASS,readyTimeout:30000});
