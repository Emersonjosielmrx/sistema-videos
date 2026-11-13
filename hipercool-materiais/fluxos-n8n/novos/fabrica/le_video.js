// Lê a resposta do montador e baixa o MP4 pronto.
__GRADIO__
const ev = $('🌐 Pede a montagem').first().json;
try {
  if (!ev || !ev.event_id) throw new Error('o montador não aceitou o pedido (' + JSON.stringify(ev).slice(0, 120) + ')');
  const d = gradioLe($input.first().json.data, 'montador');
  const url = urlDe(d);
  if (!url) throw new Error('o montador respondeu sem vídeo: ' + JSON.stringify(d).slice(0, 150));
  const mp4 = Buffer.from(await this.helpers.httpRequest({ url, encoding: 'arraybuffer', timeout: 50000 }));
  if (mp4.length < 20000) throw new Error('vídeo vazio');
  return [{ json: { ok: true, b64: mp4.toString('base64'), bytes: mp4.length } }];
} catch (e) {
  return [{ json: { ok: false, erro: String(e.message || e).slice(0, 250) } }];
}
