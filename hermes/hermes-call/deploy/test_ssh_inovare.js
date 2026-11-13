const { Client } = require('ssh2');
const c = new Client();
c.on('ready', () => {
  console.log('CONNECTED!');
  c.exec('echo HELLO && hostname && whoami', (err, stream) => {
    stream.on('data', d => console.log(d.toString()));
    stream.stderr.on('data', d => console.log(d.toString()));
    stream.on('close', () => c.end());
  });
});
c.on('error', e => console.error('ERR', e.message));
c.on('keyboard-interactive', (name, instructions, instructionsLang, prompts, finish) => {
  console.log('KBD:', prompts);
  finish(['sW5pgAG9obRu2']);
});
c.connect({ host: '209.145.60.53', port: 22, username: 'root', password: '<SEGREDO_REMOVIDO>', tryKeyboard: true, readyTimeout: 30000 });
