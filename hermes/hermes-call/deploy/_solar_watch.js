// Monitora os resultados da campanha Solar retomada (via banco).
const { Client } = require('ssh2');
const CID = process.argv[2] || '3bd104a4286b9c454e4e708c6615743c';
const c = new Client();
c.on('ready', () => {
  const sql = `SELECT r.status, count(*) FROM campaign_results r JOIN campaigns c ON c.id=r.campaign_id WHERE c.name LIKE 'Solar B2B - RETOMADA%' GROUP BY r.status ORDER BY count DESC;`;
  const sql2 = `SELECT number, status, duration_ms, interested, left(coalesce(reply,''),60) AS reply FROM campaign_results r JOIN campaigns c ON c.id=r.campaign_id WHERE c.name LIKE 'Solar B2B - RETOMADA%' AND status <> 'queued' ORDER BY duration_ms DESC;`;
  const run = s => `sudo -u postgres psql -d wacalls_main -c ${JSON.stringify(s)}`;
  c.exec(run(sql) + '; echo ===LIGACOES===; ' + run(sql2), (err, stream) => {
    if (err) throw err;
    stream.on('close', () => c.end())
      .on('data', d => process.stdout.write(d.toString()))
      .stderr.on('data', () => {});
  });
}).connect({ host: '62.171.128.241', port: 22, username: 'root', password: '<SEGREDO_REMOVIDO>' });
