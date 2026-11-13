const { Client } = require('ssh2');
const c = new Client();
c.on('ready', () => {
  c.exec(`docker exec hermes-call sh -c "echo BUNDLE_HAS_MEETING && grep -c 'MeetingAI\|MeetingAIPage' /app/client/dist/assets/index-DioXPln6.js && echo BUNDLE_HAS_meeting_ai && grep -c 'meeting-ai' /app/client/dist/assets/index-DioXPln6.js && echo BUNDLE_HAS_meeting && grep -c 'meeting' /app/client/dist/assets/index-DioXPln6.js && echo BUNDLE_HAS_meet && grep -c 'meet' /app/client/dist/assets/index-DioXPln6.js && echo BUNDLE_HAS_AI_name && grep -c 'Athena' /app/client/dist/assets/index-DioXPln6.js && echo BUNDLE_HAS_video_frames && ls /app/client/dist/video_frames/ | wc -l && echo IMAGE_HASH && md5sum /app/client/dist/assets/index-DioXPln6.js"`, (err, stream) => {
    if (err) { console.error(err); return; }
    stream.on('data', d => process.stdout.write(d.toString()));
    stream.stderr.on('data', d => process.stdout.write(d.toString()));
    stream.on('close', () => c.end());
  });
});
c.on('error', e => console.error('SSH error', e.message));
c.connect({ host: '62.171.128.241', port: 22, username: 'root', password: '<SEGREDO_REMOVIDO>', readyTimeout: 30000 });
