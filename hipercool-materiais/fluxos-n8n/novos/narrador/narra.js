// Narra o texto do pedido (POST {texto, voz, velocidade}) e devolve o MP3.
__VOZ__
const b = $input.first().json.body || {};
const texto = String(b.texto || '').slice(0, 5000);
try {
  const r = await narra(this.helpers, texto, String(b.voz || 'thalita'), Number(b.velocidade) || 0);
  const bin = await this.helpers.prepareBinaryData(r.mp3, 'narracao.mp3', 'audio/mpeg');
  return [{ json: { ok: true, motor: r.motor, segundos: r.segundos, aviso: encodeURIComponent(r.aviso || '') }, binary: { data: bin } }];
} catch (e) {
  return [{ json: { ok: false, erro: 'Não consegui gerar a voz agora: ' + String(e.message || e).slice(0, 200) } }];
}
