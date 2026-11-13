const { Client } = require('ssh2');
const c = new Client();
c.on('ready', () => {
  c.exec('curl -X POST http://127.0.0.1:8000/v1/audio/transcriptions -H "Content-Type: multipart/form-data" -F "file=@/dev/null" -F "model=Systran/faster-whisper-small"', (err, stream) => {
    if (err) throw err;
    stream.on('close', () => {
      c.end();
    }).on('data', (data) => {
      process.stdout.write(data.toString());
    }).stderr.on('data', (data) => {
      process.stderr.write(data.toString());
    });
  });
}).connect({
  host: '62.171.128.241',
  port: 22,
  username: 'root',
  password: '<SEGREDO_REMOVIDO>'
});
