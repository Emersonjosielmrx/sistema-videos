const { Client } = require('ssh2'); const fs = require('fs');
const env = fs.readFileSync(__dirname + '/.env.deploy', 'utf8').split('\n').reduce((a, l) => { const m = l.match(/^([A-Z_]+)=(.*)$/); if (m) a[m[1]] = m[2].replace(/\r/, '').replace(/^"|"$/g, ''); return a; }, {});
const c = new Client();
// script python que roda DENTRO do container do 62, conecta no PG e imprime a call_ai
const py = [
  'import urllib.parse as up, json, subprocess, os',
  'url=os.environ["WACALLS_PG_URL"]',
  '# usa o proprio binario? nao tem driver. usa psql via python? nao tem. entao usa o app? nao.',
  '# alternativa: o app expoe a config? nao. entao instala pg driver rapido? sem net garantido.',
  '# em vez disso: le via socket TCP simples com o protocolo? complexo. ',
  '# MELHOR: usa o comando pg_dump? tb sem psql. ',
  'print("PYOK")',
].join('\n');
const cmd = 'docker exec hermes-call python3 -c \'import os;print("URL="+os.environ.get("WACALLS_PG_URL",""))\' 2>&1';
c.on('ready', () => {
  c.exec(cmd, (e, s) => { let o = ''; s.on('data', d => o += d); s.stderr.on('data', d => o += d); s.on('close', () => { console.log(o); c.end(); }); });
});
c.connect({ host: env.HERMES_VPS_HOST, port: 22, username: env.HERMES_VPS_USER, password: env.HERMES_VPS_PASS, readyTimeout: 30000 });
