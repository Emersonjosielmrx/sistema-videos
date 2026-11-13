// Lê a resposta do LTX-Video e baixa o MP4 (fica no Redis por 7 dias).
__GRADIO__
const p = $('🧩 Prepara o pedido').first().json;
const ev = $('🌐 Pede o clipe').first().json;
const txt = String($input.first().json.data || '');
try {
  if (!ev || !ev.event_id) throw new Error('o Hugging Face não aceitou o pedido agora (' + JSON.stringify(ev).slice(0, 120) + ')');
  const d = gradioLe(txt, 'LTX-Video');
  const url = urlDe(d);
  if (!url) throw new Error('LTX-Video respondeu sem vídeo');
  const mp4 = Buffer.from(await this.helpers.httpRequest({ url, encoding: 'arraybuffer', timeout: 50000 }));
  if (mp4.length < 5000) throw new Error('vídeo vazio');
  return [{ json: { ok: true, id: p.id, base: p.base, b64: mp4.toString('base64'), bytes: mp4.length,
    prompt_usado: p.prompt_usado, rota: $('🧩 Monta o pedido').first().json.rota } }];
} catch (e) {
  return [{ json: { ok: false, erro: String(e.message || e).slice(0, 300) } }];
}
