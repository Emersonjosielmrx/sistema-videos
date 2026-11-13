const { Client } = require('ssh2');
const c = new Client();
c.on('ready', () => {
  const sql = `SELECT r.status, count(*) FROM campaign_results r JOIN campaigns c ON c.id=r.campaign_id WHERE c.name LIKE 'Solar B2B - LISTA COMPLETA%' GROUP BY r.status ORDER BY count DESC;`;
  const sql2 = `SELECT number, status, duration_ms, left(coalesce(reply,''),50) reply FROM campaign_results r JOIN campaigns c ON c.id=r.campaign_id WHERE c.name LIKE 'Solar B2B - LISTA COMPLETA%' AND status NOT IN ('queued') ORDER BY duration_ms DESC LIMIT 25;`;
  const run = s => `sudo -u postgres psql -d wacalls_main -c ${JSON.stringify(s)}`;
  c.exec(run(sql) + '; echo ===DISCADAS===; ' + run(sql2), (err, stream) => {
    if (err) throw err;
    stream.on('close', () => c.end())
      .on('data', d => process.stdout.write(d.toString()))
      .stderr.on('data', () => {});
  });
}).connect({ host: '62.171.128.241', port: 22, username: 'root', password: '<SEGREDO_REMOVIDO>' });
