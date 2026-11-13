const { Client } = require('ssh2');
const c = new Client();
c.on('ready', () => {
  const cmd = [
    'echo === STRINGS',
    "grep -oE 'wakeWord|aiName|Athena|Configurar|BrainCircuit|MeetingAIPage' /opt/hipercool-refactor/client/dist/assets/index-DioXPln6.js | sort -u",
    'echo === VIEWS',
    "grep -oE 'meeting-ai|follow_up|prometheus|knowledge|funil' /opt/hipercool-refactor/client/dist/assets/index-DioXPln6.js | sort -u",
    'echo === PAGES_DEFINED',
    "grep -oE 'MeetingAIPage|FollowUpPage|RecordingsPage|MassCallPage|TelephonyPage|CostsHubPage|HelpPage|PrometheusPage' /opt/hipercool-refactor/client/dist/assets/index-DioXPln6.js | sort -u",
    'echo === AI_ICONS',
    "grep -oE 'Video, Plus|Bot, Send|Ear, Mic|ShieldCheck, Activity' /opt/hipercool-refactor/client/dist/assets/index-DioXPln6.js | sort -u",
    'echo === UNIQUE_VPS',
    "grep -oE 'HermesCall|Junte-se|HermesCall IA' /opt/hipercool-refactor/client/dist/assets/index-DioXPln6.js | sort -u",
  ].join(' && ');
  c.exec(cmd, (err, stream) => {
    if (err) { console.error(err); return; }
    stream.on('data', d => process.stdout.write(d.toString()));
    stream.stderr.on('data', d => process.stdout.write(d.toString()));
    stream.on('close', () => c.end());
  });
});
c.on('error', e => console.error('SSH error', e.message));
c.connect({ host: '62.171.128.241', port: 22, username: 'root', password: '<SEGREDO_REMOVIDO>', readyTimeout: 30000 });
