const { Client } = require('ssh2');
const c = new Client();
c.on('ready', () => {
  c.exec(`echo === INOVARE_MEETINGAI_FULL && grep -c MeetingAIPage /tmp/inovare.js; echo === INOVARE_KANBAN && grep -c Kanban /tmp/inovare.js; echo === INOVARE_FUNIL && grep -c -i funil /tmp/inovare.js; echo === INOVARE_FOLLOW && grep -c -i follow_up /tmp/inovare.js; echo === INOVARE_AIPAGE && grep -c -i aiPage /tmp/inovare.js; echo === INOVARE_BRAIN && grep -c BrainCircuit /tmp/inovare.js; echo === INOVARE_REACTFLOW && grep -c -i reactflow /tmp/inovare.js; echo === INOVARE_BIGSTRINGS && grep -oE 'index BYgTiieN|MeetingAI|FollowUp|CampaignSettings|Prometheus' /tmp/inovare.js | head -20`, (err, stream) => {
    if (err) { console.error(err); return; }
    stream.on('data', d => process.stdout.write(d.toString()));
    stream.stderr.on('data', d => process.stdout.write(d.toString()));
    stream.on('close', () => c.end());
  });
});
c.on('error', e => console.error('SSH error', e.message));
c.connect({ host: '62.171.128.241', port: 22, username: 'root', password: '<SEGREDO_REMOVIDO>', readyTimeout: 60000 });
