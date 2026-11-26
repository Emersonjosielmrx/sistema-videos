const fs=require('fs');const D='/tmp/insta_integra/js/';
function roda(arq, nodes, input, runIndex=0){ const $=n=>({first:()=>({json:nodes[n]}),all:()=>nodes[n].map(j=>({json:j}))}); const $input={first:()=>({json:input}),all:()=>[{json:input}]};
 return new Function('$','$input','$runIndex','require',fs.readFileSync(D+arq,'utf8'))($,$input,runIndex,require); }
const posts=[];const F=['IMAGE','VIDEO','CAROUSEL_ALBUM'];
for(let i=0;i<20;i++)posts.push({id:''+i,timestamp:new Date(Date.now()-i*86400000*1.5).toISOString(),media_type:F[i%3],like_count:F[i%3]==='VIDEO'?40+i:10+i,comments_count:2,caption:'x'.repeat(i*30),permalink:'https://www.instagram.com/p/A'+i+'/'});
const cal={id:'teste-1a2b',dias:[{link:'https://www.instagram.com/p/A1',pilar:'Dicas',objetivo:'atrair'},{link:'https://www.instagram.com/p/A4/',pilar:'Ofertas',objetivo:'vender'}]};
const c=roda('diag_calcula.js',{'Lê meu perfil':{username:'LucroComIA',followers_count:500},'Lê os últimos 30 posts':posts},{'p30cal:teste-1a2b':JSON.stringify(cal)})[0].json;
console.log('hora',c.dados.melhor_hora_exata,'cal',JSON.stringify(c.dados.calendario),'leg',JSON.stringify(c.dados.legendas));
for (const out of ['{"nota_saude":55,"resumo":"ok","o_que_melhorar":["pouco reels"],"mix_formatos":{"carrossel":20,"post":20,"reels":20},"hora_sugerida":"19:00","regras_para_legenda":["legenda curta"]}','lixo']){
 const j=roda('diag_junta.js',{'Calcula métricas do perfil':c},{output:out})[0].json; const dg=JSON.parse(j.diagnostico); console.log('mix',JSON.stringify(dg.mix_formatos),'hora',dg.hora_sugerida,'user',dg.usuario,'ia',dg.ia_ok);
 global.DG=j.diagnostico;}
// produção
const conf={usar_diag:true,hora_diag:true,base:'https://x/webhook',negocio:{perfil:'lucrocomia',nome:'Loja'},cal:JSON.stringify({id:'loja-1',inicio:'2026-12-01',hora:'11:00',negocio:{nome:'Loja'}})};
const velho=JSON.stringify({...JSON.parse(DG),geradoEm:'2026-01-01T00:00:00Z'});
console.log('serve novo', roda('p30_serve.js',{'🧩 Confere o pedido':conf},{diag:DG})[0].json.acao);
console.log('serve velho v0', JSON.stringify(roda('p30_serve.js',{'🧩 Confere o pedido':conf},{diag:velho},0)[0].json));
console.log('serve velho v3', roda('p30_serve.js',{'🧩 Confere o pedido':conf},{diag:velho},3)[0].json.acao);
console.log('serve velho v7', JSON.stringify(roda('p30_serve.js',{'🧩 Confere o pedido':conf},{diag:velho},7)[0].json).slice(0,120));
console.log('serve nada v7', roda('p30_serve.js',{'🧩 Confere o pedido':conf},{diag:null},7)[0].json.acao);
console.log('outra conta', roda('p30_serve.js',{'🧩 Confere o pedido':{...conf,negocio:{perfil:'doceria'}}},{diag:DG})[0].json.motivo);
const s=roda('p30_serve.js',{'🧩 Confere o pedido':conf},{diag:DG})[0].json;
const pr=roda('p30_prepara.js',{},s)[0].json; console.log('prepara',pr.usado,pr.texto.length,JSON.stringify(pr.redacao));
const org=roda('p30_organiza.js',{'🧩 Confere o pedido':conf,'🧩 Prepara o diagnóstico':pr,'🤖 Estrategista':{output:'falhou'}},{})[0].json;
const C=JSON.parse(org.cal); const cont={};C.dias.forEach(d=>cont[d.formato]=(cont[d.formato]||0)+1);
console.log('organiza hora',C.hora,'mix real',JSON.stringify(cont),'seq',C.dias.map(d=>d.formato[0]).join(''),'diag',C.diagnostico.status);
const sem=roda('p30_prepara.js',{},{acao:'sem',motivo:'x'})[0].json;
const org2=JSON.parse(roda('p30_organiza.js',{'🧩 Confere o pedido':{...conf,usar_diag:false},'🧩 Prepara o diagnóstico':sem,'🤖 Estrategista':{output:''}},{})[0].json.cal); console.log('sem diag', org2.hora, org2.diagnostico);
for (const m of [{carrossel:4,post:4,reels:22},{carrossel:1,post:1,reels:28},{carrossel:30,post:30,reels:30}]){
 const j=roda('diag_junta.js',{'Calcula métricas do perfil':c},{output:JSON.stringify({mix_formatos:m})})[0].json; console.log('cap',JSON.stringify(m),'->',JSON.stringify(JSON.parse(j.diagnostico).mix_formatos));}
const fake={dias:Array.from({length:30},(_,i)=>({dia:i+1,formato:i<12?'reels':(i<20?'post':'carrossel'),tema:'t'+(i+1)}))};
const o3=JSON.parse(roda('p30_organiza.js',{'🧩 Confere o pedido':conf,'🧩 Prepara o diagnóstico':pr,'🤖 Estrategista':{output:JSON.stringify(fake)}},{})[0].json.cal);
console.log('anti-3', o3.dias.map(d=>d.formato[0]).join(''), o3.dias.slice(0,4).map(d=>d.tema).join(','));
