// Rebuild Hermes Call sem cache de build
//
// ⚠️  PERIGO — LEIA ANTES DE USAR
// Este script builda a imagem a partir do fonte que ESTÁ NA VPS
// (/opt/hipercool-refactor), que pode estar desatualizado/contaminado e NÃO é
// rastreado pelo git. Foi por um build assim que a versão boa (v0.2.1) se
// perdeu. Ele também SOBRESCREVE a tag hermes-call:latest e recria o container
// de produção.
//
// A versão correta de produção é a imagem imutável:
//   fabricadeautomacoesia/hermes-call:v0.2.1  (= :stable, digest e9076d20...)
// Para restaurar produção, prefira dar `docker run` dessa imagem (ver
// project memory / _GOLDEN_v0.2.1/), NÃO rebuildar daqui.
//
// Se REALMENTE precisa rebuildar da VPS, rode com a flag de confirmação:
//   node deploy/rebuild.js --sim-eu-quero-rebuildar-da-vps
//
// Antes de sobrescrever, o script salva a imagem atual como
// hermes-call:prev-<timestamp> para permitir rollback.

const { Client } = require('ssh2');

if (!process.argv.includes('--sim-eu-quero-rebuildar-da-vps')) {
  console.error('\n╔════════════════════════════════════════════════════════════════════╗');
  console.error('║  rebuild.js BLOQUEADO por segurança                                 ║');
  console.error('╚════════════════════════════════════════════════════════════════════╝');
  console.error('\nEste script builda do fonte NÃO-VERSIONADO da VPS e sobrescreve a');
  console.error('imagem/container de produção. Foi assim que a v0.2.1 se perdeu.\n');
  console.error('Produção correta = imagem imutável fabricadeautomacoesia/hermes-call:v0.2.1');
  console.error('Para restaurar, use `docker run ...:v0.2.1` (ver _GOLDEN_v0.2.1/).\n');
  console.error('Se tem CERTEZA que quer rebuildar da VPS mesmo assim:');
  console.error('  node deploy/rebuild.js --sim-eu-quero-rebuildar-da-vps\n');
  process.exit(1);
}

const STAMP = new Date().toISOString().replace(/[-:T]/g, '').slice(0, 13);
const c = new Client();
c.on('ready', () => {
  // 1) backup da imagem atual antes de sobrescrever (rollback)
  const backup = 'docker tag hermes-call:latest hermes-call:prev-' + STAMP + ' 2>/dev/null; echo "[rebuild] backup -> hermes-call:prev-' + STAMP + '"';
  c.exec(backup + ' && cd /opt/hipercool-refactor && docker build --network host --no-cache -t hermes-call:latest . 2>&1 | tail -30', (err, stream) => {
    if (err) { console.error(err); return; }
    stream.on('data', d => process.stdout.write(d.toString()));
    stream.stderr.on('data', d => process.stdout.write(d.toString()));
    stream.on('close', () => {
      c.exec('docker rm -f hermes-call && docker run -d --name hermes-call --restart=always --network host -e "WACALLS_PG_URL=postgres://hermes_call_v3test:hermes_call_v3test@localhost:5432/wacalls_main?sslmode=disable" -e "PORT=8080" -e "HERMES_TELEGRAM_TOKEN=<SEGREDO_REMOVIDO>" hermes-call:latest && sleep 8 && curl -s http://127.0.0.1:8080/api/version && echo "" && docker exec hermes-call bash -c "md5sum /app/client/dist/assets/index-*.js && grep -c MeetingAIPage /app/client/dist/assets/index-*.js && grep -c meeting-ai /app/client/dist/assets/index-*.js"', (err2, stream2) => {
        if (err2) { console.error(err2); return; }
        stream2.on('data', d => process.stdout.write(d.toString()));
        stream2.stderr.on('data', d => process.stdout.write(d.toString()));
        stream2.on('close', () => { console.log('\n[rebuild] rollback: docker tag hermes-call:prev-' + STAMP + ' hermes-call:latest && recriar container'); c.end(); });
      });
    });
  });
});
c.on('error', e => console.error('SSH error:', e.message));
c.connect({ host: '62.171.128.241', port: 22, username: 'root', password: '<SEGREDO_REMOVIDO>', readyTimeout: 60000 });
