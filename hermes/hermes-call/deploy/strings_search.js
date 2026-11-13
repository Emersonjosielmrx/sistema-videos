const { Client } = require('ssh2');
const c = new Client();
c.on('ready', () => {
  c.exec(`echo === LOOKING_UNIQUE_STRINGS && grep -oE 'wakeWord|aiName|"Athena"|"Vídeo com IA"|Configurar Athena|"Brain"|"Bot" .* "Athena"' /opt/hipercool-refactor/client/dist/assets/index-DioXPln6.js | sort -u && echo === LOOKING_NAV_VIEW && grep -oE 'meeting-ai|follow_up|knowledge|prometheus|"promises"' /opt/hipercool-refactor/client/dist/assets/index-DioXPln6.js | sort -u && echo === LOOKING_RECORDING && grep -oE 'RecordingsPage|RecordingsPage ' /opt/hipercool-refactor/client/dist/assets/index-DioXPln6.js | sort -u && echo === ALL_PAGE_COMPONENT_REFS && grep -oE 'MeetingAIPage|FollowUpPage|RecordingsPage|KanbanPage|CRMPage' /opt/hipercool-refactor/client/dist/assets/index-DioXPln6.js | sort -u | head -30 && echo === METADATA && grep -oE 'src=\\"[^\\"]+\.tsx\?"|pages/[A-Z][a-zA-Z]+' /opt/hipercool-refactor/client/dist/assets/index-DioXPln6.js | sort -u | head -30`, (err, stream) => {
    if (err) { console.error(err); return; }
    stream.on('data', d => process.stdout.write(d.toString()));
    stream.stderr.on('data', d => process.stdout.write(d.toString()));
    stream.on('close', () => c.end());
  });
});
c.on('error', e => console.error('SSH error', e.message'));
c.connect({ host: '62.171.128.241', port: 22, username: 'root', password: '<SEGREDO_REMOVIDO>', readyTimeout: 30000 });
