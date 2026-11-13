// Lê o resultado da extração: endereço do áudio e do quadro (valem 7 dias) e o tamanho do quadro (em pé ou deitado).
const v = $('🧩 Pega o vídeo').first().json;
const m = ($input.first().json || {}).data || {};
const o = m.output_files || {};
const audio = o[`audio-${v.job}.mp3`], quadro = o[`quadro-${v.job}.jpg`];
if (m.status !== 'succeeded' || !audio || !quadro) throw new Error('Não consegui abrir o vídeo: ' + String(m.error_message || m.status || 'sem resposta').slice(0, 200));
const bin = await this.helpers.httpRequest({ url: quadro, encoding: 'arraybuffer', timeout: 60000 });
const buf = Buffer.from(bin);
// largura e altura do JPEG (marcador SOF0/SOF2)
let w = 0, h = 0;
for (let i = 2; i < buf.length - 9; ) {
  if (buf[i] !== 0xFF) { i++; continue; }
  const mk = buf[i + 1];
  if (mk >= 0xC0 && mk <= 0xC3) { h = buf.readUInt16BE(i + 5); w = buf.readUInt16BE(i + 7); break; }
  i += 2 + buf.readUInt16BE(i + 2);
}
return [{ json: { audio, quadro, largura: w, altura: h, b64: buf.toString('base64') } }];
