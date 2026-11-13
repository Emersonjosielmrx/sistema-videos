const { Client } = require('ssh2');
const c = new Client();
c.on('ready', () => {
  c.exec(`echo === MD5 && md5sum /opt/hipercool-refactor/client/dist/assets/index-*.js && echo === MEETING COUNT && grep -c MeetingAIPage /opt/hipercool-refactor/client/dist/assets/index-*.js && echo === VID && grep -c Video /opt/hipercool-refactor/client/dist/assets/index-*.js && echo === ATHENA && grep -c Athena /opt/hipercool-refactor/client/dist/assets/index-*.js && echo === REACTFLOW && grep -c reactflow /opt/hipercool-refactor/client/dist/assets/index-*.js && echo === MEETING_AI && grep -c 'meeting-ai' /opt/hipercool-refactor/client/dist/assets/index-*.js && echo === ORCHESTRATOR && grep -c AgentOrchestratorFlow /opt/hipercool-refactor/client/dist/assets/index-*.js && echo === && grep -c Handle /opt/hipercool-refactor/client/dist/assets/index-*.js && echo === BG && grep -c Background /opt/hipercool-refactor/client/dist/assets/index-*.js`, (err, stream) => {
    if (err) { console.error(err); return; }
    stream.on('data', d => process.stdout.write(d.toString()));
    stream.stderr.on('data', d => process.stdout.write(d.toString()));
    stream.on('close', () => c.end());
  });
});
c.on('error', e => console.error('SSH error', e.message));
c.connect({ host: '62.171.128.241', port: 22, username: 'root', password: '<SEGREDO_REMOVIDO>', readyTimeout: 30000 });
