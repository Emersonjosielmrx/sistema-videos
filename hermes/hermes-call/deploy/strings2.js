const { Client } = require('ssh2');
c.on('ready', () => {
c.exec(`echo === STRINGS && grep -oE 'wakeWord|aiName|Athena|Brain|MeetingAIPage|Configurar' /opt/hipercool-refactor/client/dist/assets/index-DioXPln6.js | sort -u; echo === VIEWS; grep -oE 'meeting-ai|follow_up|prometheus|knowledge' /opt/hipercool-refactor/client/dist/assets/index-DioXPln6.js | sort -u; echo === PAGES_DEFINED; grep -oE 'function\s+\w+\s+export|meeting-AI|meeting-ai\s+[a-z]' /opt/hipercool-refactor/client/dist/assets/index-DioXPln6.js | sort -u | head -20; echo === ALL_UNIQUE_PAGES; grep -oE 'MeetingAIPage|FollowUpPage|RecordingsPage|MassCallPage|TelephonyPage|CostsHubPage|HelpPage' /opt/hipercool-refactor/client/dist/assets/index-DioXPln6.js | sort -u | head -30`, (err, stream) => {
JSEOF
