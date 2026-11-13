const { Client } = require('ssh2');
const c = new Client();
c.on('ready', () => {
  c.exec('docker exec hermes-call printenv 2>&1 | grep -iE "HERMES_AI_MODEL|HERMES_AI_PROVIDER" ; echo "---defaults-se-vazio---"; docker exec hermes-call sh -c "echo provider=\$HERMES_AI_PROVIDER model=\$HERMES_AI_MODEL" 2>&1', (err, stream) => {
    let out=''; stream.on('data',d=>out+=d); stream.stderr.on('data',d=>out+=d);
    stream.on('close',()=>{console.log(out||'(nenhuma env AI setada → usa default do codigo: anthropic / claude-sonnet-4-20250514)');c.end();});
  });
});
c.on('error',e=>{console.error(e);process.exit(1);});
c.connect({host:'62.171.128.241',port:22,username:'root',password:'<SEGREDO_REMOVIDO>'});
