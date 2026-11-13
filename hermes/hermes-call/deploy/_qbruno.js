const { Client } = require('ssh2');
const c = new Client();
c.on('ready', () => {
  // Pega logs com chamada ativa nas últimas 2h
  const cmd = `docker logs hermes-call --since 2h 2>&1 | grep -iE "voz efetiva|lig acion|agent bruno|agent=.*bruna|got message|onUtterance|system.*bruna|system.*Bruno|system prompt" | tail -30`;
  c.exec(cmd, (err, stream) => {
    if (err) { console.error(err); return; }
    stream.on('close', () => c.end()).on('data', d => process.stdout.write(d.toString()));
    stream.stderr.on('data', d => process.stderr.write(d.toString()));
  });
}).connect({host: '62.171.128.241', port: 22, username: 'root', password: '<SEGREDO_REMOVIDO>'});
