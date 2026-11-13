// Junta os caminhos dos arquivos já enviados ao montador grátis (Space Tim13ekd/video-ffmpeg, 1280x720) e monta o pedido.
// O Space divide as palavras IGUALMENTE entre as imagens e escreve cada trecho numa linha só: com 6 imagens e 80
// palavras a legenda estourava a tela. Por isso cada imagem entra repetida (mesmo arquivo, sem novo envio) em trechos
// de ~4 palavras, na proporção das palavras de cada cena.
__GRADIO__
const ESPACO = 'tim13ekd-video-ffmpeg';
const voz = $('🎙️ Narra o roteiro').first().json;
const itens = $('🧩 Prepara os arquivos').all().map(i => i.json);
const respostas = $input.all().map(i => i.json);
try {
  const caminhos = itens.map((it, k) => ({ ...it, caminho: caminhoDoUpload(respostas[k] && respostas[k].data) }));
  const falhou = caminhos.filter(c => !c.caminho);
  if (falhou.length) throw new Error('o envio de ' + falhou.length + ' arquivo(s) ao montador falhou: ' +
    String((respostas.find(r => !caminhoDoUpload(r.data)) || {}).data || (respostas[0] || {}).error || '').slice(0, 120));
  const porCena = Object.fromEntries(caminhos.filter(c => c.tipo === 'img').map(c => [c.n, arquivoGradio(c.caminho, c.nome)]));
  const audio = caminhos.find(c => c.tipo === 'voz');
  const palavrasCena = voz.cenas.map(c => c.fala.split(/\s+/).filter(Boolean).length);
  const total = palavrasCena.reduce((a, b) => a + b, 0);
  const N = Math.max(voz.cenas.length, Math.ceil(total / 4.5));
  const quantas = palavrasCena.map(w => Math.max(1, Math.round(w * N / total)));
  const imagens = [];
  voz.cenas.forEach((c, i) => { for (let k = 0; k < quantas[i]; k++) imagens.push(porCena[c.n] || Object.values(porCena)[0]); });
  const dados = [imagens, voz.texto, Math.round(voz.segundos / total * 1000) / 1000,
    Math.round(voz.segundos / imagens.length * 1000) / 1000, 0.12, 50, 0.86, arquivoGradio(audio.caminho, 'voz.mp3'),
    'Highlight', 'DejaVu Sans Bold'];
  return [{ json: { ok: true, trechos: imagens.length, url_chamada: 'https://' + ESPACO + '.hf.space/gradio_api/call/generate_slideshow_with_audio',
    corpo: { data: dados } } }];
} catch (e) {
  return [{ json: { ok: false, erro: String(e.message || e).slice(0, 220) } }];
}
