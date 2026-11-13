// Monta a edição para o Shotstack: cada trecho do roteiro vira uma voz (ElevenLabs, gerada pelo próprio Shotstack) com
// apelido "v1", "v2"...; a foto, a manchete, o selo de preço e a legenda de cada cena ficam presos ao tempo dessa voz.
// No fim, 3 s de silêncio seguram o cartão final. A versão só com música é a MESMA edição com a voz no volume zero
// e sem legenda (o Shotstack reaproveita a voz já gerada, sem cobrar de novo).
const v = $('🧩 Confere o pedido').first().json;
const ed = $('🧩 Junta tudo').first().json;
// ambiente do Shotstack: 'stage' = sandbox (render grátis, com marca d'água) · 'v1' = produção (gasta créditos, sem marca)
// Trocou para 'v1'? Troque também a chave na credencial (a de produção é outra).
const AMBIENTE = 'stage';
const FORMATOS = { vertical: [1080, 1920], quadrado: [1080, 1080], deitado: [1920, 1080] };
const [W, H] = FORMATOS[v.op.formato] || FORMATOS.vertical;
const vertical = H > W;
const k = Math.min(W, H) / 1080;
// vozes da página -> vozes do ElevenLabs que falam português (o Shotstack não tem as vozes da Microsoft)
const VOZES = { 'pt-BR-ThalitaMultilingualNeural': 'Sarah', 'pt-BR-FranciscaNeural': 'Laura', 'en-US-AndrewMultilingualNeural': 'Chris', 'en-US-BrianMultilingualNeural': 'Brian' };
const TRILHAS = {
  animado: 'https://files.catbox.moe/qpmdb1.mp3', calmo: 'https://files.catbox.moe/xoym41.mp3', chill: 'https://files.catbox.moe/2rqu0z.mp3',
  elegante: 'https://files.catbox.moe/yb6h1l.mp3', emocional: 'https://files.catbox.moe/tomvef.mp3', latino: 'https://files.catbox.moe/kic00y.mp3',
  tropical: 'https://files.catbox.moe/x14vcg.mp3', urgente: 'https://files.catbox.moe/2gttp6.mp3',
};
const SILENCIO = 'https://files.catbox.moe/6v3qjd.mp3';
const clara = c => { const n = parseInt(String(c).slice(1), 16); return ((n >> 16) * 299 + ((n >> 8) & 255) * 587 + (n & 255) * 114) / 1000 > 150; };
const cor = /^#[0-9A-Fa-f]{6}$/.test(ed.cor || '') ? ed.cor : '#F59E0B';
const corTexto = clara(cor) ? '#111111' : '#FFFFFF';
const destaque = clara(cor) ? cor : '#FFD400';
const limpa = s => String(s || '').replace(/[\u{1F000}-\u{1FAFF}☀-➿️‍]/gu, '').trim();
const foto = u => /\.(jpe?g|png)$/i.test(u) && !/\?/.test(u) ? u : 'https://wsrv.nl/?url=' + encodeURIComponent(u) + '&w=2560&h=2560&fit=inside&output=jpg&q=90';
// movimento de câmera do diretor -> efeito do Shotstack
const EFEITO = { zoom_in: 'zoomInSlow', zoom_out: 'zoomOutSlow', pan_esq: 'slideLeftSlow', pan_dir: 'slideRightSlow', pan_cima: 'slideUpSlow', pan_baixo: 'slideDownSlow', parado: undefined };
const TRANS = { fade: 'fade', fadeblack: 'fade', fadewhite: 'fade', dissolve: 'fade', slideleft: 'slideLeft', slideright: 'slideRight', wipeleft: 'wipeLeft',
  wiperight: 'wipeRight', smoothleft: 'carouselLeft', smoothright: 'carouselRight', circleopen: 'zoom', radial: 'zoom', zoomin: 'zoom', hblur: 'fade', pixelize: 'fade' };

// caixa de texto (manchete, preço, contatos): rich-text com fundo colorido e cantos arredondados
function texto(t, alias, y, tam, fundo, corT, peso) {
  return {
    asset: { type: 'rich-text', text: limpa(t),
      font: { family: 'Montserrat', size: Math.round(tam * k), weight: peso || 800, color: corT || corTexto },
      ...(fundo ? { background: { color: fundo, borderRadius: Math.round(18 * k), wrap: true, padding: Math.round(20 * k) } }
        : { stroke: { width: 3, color: '#000000' } }),
      align: { horizontal: 'center', vertical: 'middle' }, animation: { preset: 'fadeIn', duration: 0.4 } },
    start: alias, length: alias, width: Math.round(W * 0.9), height: Math.round(tam * k * 2.4), position: 'center', offset: { x: 0, y: y },
  };
}

function edicao(muda) {
  const vozes = [], fotos = [], textos = [], legendas = [];
  ed.segmentos.forEach((s, i) => {
    const a = 'v' + (i + 1), alias = 'alias://' + a;
    vozes.push({ alias: a, asset: { type: 'audio', prompt: limpa(s.texto), model: 'elevenlabs-multilingual-v2',
      options: { voice: VOZES[v.op.voz] || 'Sarah', language: 'pt' }, volume: muda ? 0 : 1 }, start: 'auto', length: 'auto' });
    const ef = EFEITO[s.movimento];
    fotos.push({ asset: { type: 'image', src: foto(v.fotos[s.foto] || v.fotos[0]) }, start: alias, length: alias, fit: 'crop',
      ...(ef ? { effect: ef } : {}), transition: { in: i ? (TRANS[s.transicao] || 'fade') : 'fade' } });
    if (s.texto_tela) textos.push(texto(s.texto_tela, alias, vertical ? 0.36 : 0.36, vertical ? 62 : 54, cor));
    if (s.selo_preco && v.dados.preco) textos.push(texto(v.dados.preco, alias, vertical ? -0.08 : -0.02, vertical ? 84 : 64, cor));
    // legenda com o texto EXATO do roteiro (a transcrição automática do Shotstack ouviu "switch" no lugar de "suíte"):
    // as palavras sobem uma a uma no ritmo médio da voz (~15 letras por segundo)
    // fala longa = letra menor, para caber na caixa (com 64 px uma fala de 110 letras dava 6 linhas e cortava)
    const n = limpa(s.texto).length, tam = (vertical ? 64 : 50) * (n <= 60 ? 1 : n <= 100 ? 0.82 : 0.7);
    if (!muda && v.op.legendas) legendas.push({ asset: { type: 'rich-text', text: limpa(s.texto),
      font: { family: 'Montserrat', size: Math.round(tam * k), weight: 800, color: '#FFFFFF' },
      stroke: { width: 5, color: '#000000' }, align: { horizontal: 'center', vertical: 'middle' },
      animation: { preset: 'ascend', style: 'word', duration: Math.max(0.6, Math.round(limpa(s.texto).length / 15 * 0.85 * 10) / 10) } },
      start: alias, length: alias, width: Math.round(W * 0.88), height: Math.round(H * (vertical ? 0.24 : 0.3)), position: 'bottom', offset: { x: 0, y: vertical ? 0.1 : 0.04 } });
  });
  if (v.op.cartao_final) {
    vozes.push({ alias: 'fim', asset: { type: 'audio', src: SILENCIO }, start: 'auto', length: 'auto' });
    const fim = 'alias://fim';
    const f0 = v.fotos[ed.segmentos[0].foto] || v.fotos[0];
    fotos.push({ asset: { type: 'image', src: 'https://wsrv.nl/?url=' + encodeURIComponent(f0) + `&w=${W}&h=${H}&fit=cover&blur=14&mod=0.5&output=jpg&q=80` },
      start: fim, length: fim, fit: 'crop', effect: 'zoomInSlow', transition: { in: 'fade' } });
    textos.push(texto(v.dados.marca || v.dados.titulo, fim, 0.28, vertical ? 72 : 58, null, '#FFFFFF'));
    if (ed.cta) textos.push(texto(ed.cta, fim, 0.1, vertical ? 66 : 54, cor));
    if (v.dados.preco) textos.push(texto(v.dados.preco, fim, -0.05, vertical ? 60 : 48, null, '#FFFFFF'));
    (ed.contatos || []).slice(0, 3).forEach((c, j) => textos.push(texto(c, fim, -0.18 - j * 0.075, vertical ? 46 : 38, null, '#FFFFFF', 700)));
  }
  const tracks = [];
  if (v.logo) tracks.push({ clips: [{ asset: { type: 'image', src: 'https://wsrv.nl/?url=' + encodeURIComponent(v.logo) + '&w=600&h=600&fit=inside&output=png' }, start: 0, length: 'end', fit: 'contain', scale: vertical ? 0.16 : 0.12, position: 'topRight', offset: { x: -0.03, y: -0.02 } }] });
  if (legendas.length) tracks.push({ clips: legendas });
  if (textos.length) tracks.push({ clips: textos });
  tracks.push({ clips: fotos }, { clips: vozes });   // no Shotstack a primeira trilha fica por cima
  return {
    timeline: { background: '#000000', soundtrack: { src: TRILHAS[ed.clima] || TRILHAS.elegante, effect: 'fadeOut', volume: muda ? 0.8 : 0.12 },
      fonts: [{ src: 'https://fonts.gstatic.com/s/montserrat/v31/JTUHjIg1_i6t8kCHKm4532VJOt5-QNFgpCvr70w-.ttf' }], tracks },   // Montserrat 800
    output: { format: 'mp4', fps: 30, size: { width: W, height: H }, poster: { capture: 1.2 } },
  };
}

const pedidos = [{ json: { versao: 'narrado', ambiente: AMBIENTE, corpo: JSON.stringify(edicao(false)) } }];
if (v.op.versao_musica) pedidos.push({ json: { versao: 'musica', ambiente: AMBIENTE, corpo: JSON.stringify(edicao(true)) } });
return pedidos;
