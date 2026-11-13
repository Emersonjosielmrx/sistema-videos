// Monta a chamada do LTX-Video: texto → vídeo, ou foto → vídeo com o caminho da foto já enviada ao Space.
__GRADIO__
const p = $('🧩 Prepara o pedido').first().json;
const ESPACO = 'lightricks-ltx-video-distilled';
const NEG = 'worst quality, inconsistent motion, blurry, jittery, distorted, watermark, text, subtitles';
let rota = 'text_to_video';
let dados = [p.prompt, NEG, null, null, p.hh, p.w, 'text-to-video', p.dur, 9, 42, true, 1, true];
if (p.tem_foto) {
  const caminho = caminhoDoUpload(($('🌐 Sobe a foto').first().json || {}).data);
  if (!caminho) return [{ json: { ok: false, erro: 'Não consegui mandar a foto ao Hugging Face agora. Tente de novo.' } }];
  rota = 'image_to_video';
  dados = [p.prompt, NEG, arquivoGradio(caminho, 'foto.jpg'), null, p.hh, p.w, 'image-to-video', p.dur, 9, 42, true, 1, true];
}
return [{ json: { ok: true, rota, url_chamada: 'https://' + ESPACO + '.hf.space/gradio_api/call/' + rota, corpo: { data: dados } } }];
