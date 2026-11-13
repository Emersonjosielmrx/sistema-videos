// Script temporário: consulta sessões e campanhas na VPS via SSH+docker+psql.
const { Client } = require('ssh2');
const c = new Client();

const q1 = "SELECT id, name, jid, state, paired, connected FROM sessions ORDER BY connected DESC;";
const q2 = "SELECT id, name, status, created_at FROM campaigns ORDER BY created_at DESC LIMIT 10;";

// psql roda DENTRO do container (sh -c) pra que $WACALLS_PG_URL expanda lá.
function inContainer(sql) {
  const inner = `psql "$WACALLS_PG_URL" -c ${JSON.stringify(sql)}`;
  return `docker exec "$CID" sh -c ${JSON.stringify(inner)} 2>&1`;
}

c.on('ready', () => {
  const cmd =
    'CID=$(docker ps -qf name=hermes-call | head -1); ' +
    'echo "CID=$CID"; echo "=== SESSOES ==="; ' +
    inContainer(q1) + '; echo "=== CAMPANHAS ==="; ' + inContainer(q2);
  c.exec(cmd, (err, stream) => {
    if (err) { console.error('EXEC ERR', err.message); c.end(); return; }
    stream.on('data', d => process.stdout.write(d.toString()));
    stream.stderr.on('data', d => process.stderr.write(d.toString()));
    stream.on('close', () => c.end());
  });
}).connect({ host: '62.171.128.241', username: 'root', password: '<SEGREDO_REMOVIDO>' });
