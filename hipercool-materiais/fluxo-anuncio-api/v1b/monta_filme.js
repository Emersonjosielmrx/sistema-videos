// Monta o pedido para a JSON2Video: uma cena por trecho do roteiro (foto com movimento + voz + manchete + selo de preço),
// o cartão final com o contato, a trilha e a legenda que acende junto com a fala. A versão só com música é o MESMO
// filme com a voz muda (mesma duração) e sem legenda.
const v = $('🧩 Confere o pedido').first().json;
const ed = $('🧩 Junta tudo').first().json;
const FORMATOS = { vertical: [1080, 1920], quadrado: [1080, 1080], deitado: [1920, 1080] };
const [W, H] = FORMATOS[v.op.formato] || FORMATOS.vertical;
const vertical = H > W;
// fotos: se não for JPG/PNG (WEBP, HEIC do iPhone...), o wsrv.nl converte para JPG e gira conforme o celular
const foto = u => /\.(jpe?g|png)$/i.test(u) ? u : 'https://wsrv.nl/?url=' + encodeURIComponent(u) + '&w=2560&h=2560&fit=inside&output=jpg&q=90';
// trilhas da Biblioteca de Áudio do YouTube (uso livre), hospedadas no catbox; troque pelas suas se quiser
const TRILHAS = {
  animado: 'https://files.catbox.moe/qpmdb1.mp3', calmo: 'https://files.catbox.moe/xoym41.mp3', chill: 'https://files.catbox.moe/2rqu0z.mp3',
  elegante: 'https://files.catbox.moe/yb6h1l.mp3', emocional: 'https://files.catbox.moe/tomvef.mp3', latino: 'https://files.catbox.moe/kic00y.mp3',
  tropical: 'https://files.catbox.moe/x14vcg.mp3', urgente: 'https://files.catbox.moe/2gttp6.mp3',
};
// transições que a JSON2Video aceita (as outras viram "fade")
const TRANS = ['fade', 'fadeblack', 'fadewhite', 'dissolve', 'slideleft', 'slideright', 'wipeleft', 'wiperight', 'smoothleft', 'smoothright', 'circleopen', 'radial', 'hblur', 'pixelize'];
const clara = c => { const n = parseInt(String(c).slice(1), 16); return ((n >> 16) * 299 + ((n >> 8) & 255) * 587 + (n & 255) * 114) / 1000 > 150; };
const cor = /^#[0-9A-Fa-f]{6}$/.test(ed.cor || '') ? ed.cor : '#F59E0B';
const corTexto = clara(cor) ? '#111111' : '#FFFFFF';
const destaque = clara(cor) ? cor : '#FFD400';   // a palavra falada precisa aparecer sobre a foto
const k = Math.min(W, H) / 1080;                 // escala das letras pelo lado menor do vídeo
const px = n => Math.round(n * k) + 'px';
const limpa = s => String(s || '').replace(/[\u{1F000}-\u{1FAFF}☀-➿️‍]/gu, '').trim();
const wsrv = (url, extra) => 'https://wsrv.nl/?url=' + encodeURIComponent(url) + '&' + extra;

// movimento de câmera: zoom pela JSON2Video (+ aproxima, - afasta) e o "pan" puxa para o ponto de interesse
function movimento(s) {
  const f = s.foco || { x: 0.5, y: 0.5 };
  const lado = (f.x < 0.4 ? 'left' : f.x > 0.6 ? 'right' : '');
  const alto = (f.y < 0.4 ? 'top' : f.y > 0.6 ? 'bottom' : '');
  const rumo = [alto, lado].filter(Boolean).join('-') || undefined;
  switch (s.movimento) {
    case 'zoom_in': return { zoom: 3, pan: rumo };
    case 'zoom_out': return { zoom: -3, pan: rumo };
    case 'pan_esq': return { pan: 'left', 'pan-distance': 0.15 };
    case 'pan_dir': return { pan: 'right', 'pan-distance': 0.15 };
    case 'pan_cima': return { pan: 'top', 'pan-distance': 0.15 };
    case 'pan_baixo': return { pan: 'bottom', 'pan-distance': 0.15 };
    default: return { zoom: 1 };
  }
}

// caixa de texto: a "tela" do elemento é uma faixa do vídeo e o texto fica centralizado nela
function texto(t, y, alt, css) {
  return {
    type: 'text', text: limpa(t), duration: -2, 'fade-in': 0.3, position: 'custom', x: 0, y: Math.round(y), width: W, height: Math.round(alt),
    settings: { 'font-family': 'Montserrat', 'font-weight': '800', 'text-align': 'center', 'vertical-position': 'center', 'horizontal-position': 'center', ...css },
  };
}

// estilo dos textos (versão "textos novos"): letra mais grossa e maior, sombra para ler em qualquer foto,
// manchete em CAIXA ALTA, selo de preço inclinado e um degradê escuro embaixo para a legenda saltar
const SOMBRA = '0 4px 18px rgba(0,0,0,.55)';
const degrade = () => ({ type: 'text', text: ' ', duration: -2, position: 'custom', x: 0, y: Math.round(H * 0.5), width: W, height: Math.round(H * 0.5),
  settings: { background: 'linear-gradient(to bottom, rgba(0,0,0,0) 0%, rgba(0,0,0,.25) 45%, rgba(0,0,0,.7) 100%)', width: W + 'px', height: Math.round(H * 0.5) + 'px' } });

function cenas(muda) {
  const lista = ed.segmentos.map((s, i) => {
    const els = [{ type: 'image', src: foto(v.fotos[s.foto] || v.fotos[0]), resize: 'cover', position: 'center-center', duration: -2, ...movimento(s) }];
    if (!muda && v.op.legendas) els.push(degrade());
    if (s.texto_tela) els.push(texto(s.texto_tela.toUpperCase(), H * (vertical ? 0.08 : 0.05), H * 0.18,
      { 'font-size': px(vertical ? 74 : 58), 'font-weight': '900', 'letter-spacing': '1px', 'line-height': '1.1', color: corTexto, 'background-color': cor,
        padding: '18px 34px', 'border-radius': '22px', 'box-shadow': SOMBRA, 'max-width': Math.round(W * 0.88) + 'px' }));
    if (s.selo_preco && v.dados.preco) els.push(texto(v.dados.preco, H * (vertical ? 0.42 : 0.4), H * 0.16,
      { 'font-size': px(vertical ? 104 : 78), 'font-weight': '900', color: corTexto, 'background-color': cor, padding: '14px 40px',
        'border-radius': '28px', 'box-shadow': SOMBRA, transform: 'rotate(-4deg)', border: Math.round(6 * k) + 'px solid #FFFFFF' }));
    els.push({ type: 'voice', model: 'azure', voice: v.op.voz, text: limpa(s.texto), speed: 1.08, 'extra-time': 0.35, ...(muda ? { muted: true } : {}) });
    const cena = { comment: 'cena ' + s.n, elements: els };
    if (i > 0) cena.transition = { style: TRANS.includes(s.transicao) ? s.transicao : 'fade', duration: 0.5 };
    return cena;
  });
  if (v.op.cartao_final) {
    const f0 = v.fotos[ed.segmentos[0].foto] || v.fotos[0];
    const fundo = wsrv(f0, `w=${W}&h=${H}&fit=cover&blur=14&mod=0.5&output=jpg&q=80`);
    const els = [{ type: 'image', src: fundo, resize: 'cover', position: 'center-center', duration: -2, zoom: 1 }];
    const marca = v.dados.marca || v.dados.titulo;
    els.push(texto(marca.toUpperCase(), H * 0.18, H * 0.16, { 'font-size': px(vertical ? 88 : 66), 'font-weight': '900', 'letter-spacing': '2px', color: '#FFFFFF', 'text-shadow': SOMBRA }));
    if (ed.cta) els.push(texto(ed.cta, H * 0.37, H * 0.15, { 'font-size': px(vertical ? 76 : 58), 'font-weight': '900', color: corTexto, 'background-color': cor,
      padding: '20px 44px', 'border-radius': '999px', 'box-shadow': SOMBRA }));
    if (v.dados.preco) els.push(texto(v.dados.preco, H * 0.53, H * 0.11, { 'font-size': px(vertical ? 80 : 60), 'font-weight': '900', color: destaque, 'text-shadow': SOMBRA }));
    (ed.contatos || []).slice(0, 3).forEach((c, j) => els.push(texto(c, H * (0.67 + j * 0.08), H * 0.075, { 'font-size': px(vertical ? 56 : 44), 'font-weight': '800', color: '#FFFFFF', 'text-shadow': SOMBRA })));
    lista.push({ comment: 'cartão final', duration: 3, transition: { style: 'fadeblack', duration: 0.5 }, elements: els });
  }
  return lista;
}

function filme(muda) {
  const elementos = [];
  const trilha = TRILHAS[ed.clima] || TRILHAS.elegante;
  elementos.push({ type: 'audio', src: trilha, volume: muda ? 0.8 : 0.12, duration: -2 });
  if (v.logo) {
    const lado = Math.round(W * (vertical ? 0.2 : 0.13));
    elementos.push({ type: 'image', src: wsrv(v.logo, `w=${lado}&h=${lado}&fit=contain&cbg=00000000&output=png`), duration: -2,
      position: 'custom', x: W - lado - Math.round(36 * k), y: Math.round(36 * k), width: lado, height: lado });
  }
  // legenda: a JSON2Video transcreve a narração; o Whisper com as palavras do roteiro como dica acertou tudo no teste
  // (o modelo padrão perdeu uma frase e escreveu "Fitas" no lugar de "Fritas")
  const palavras = [...new Set(ed.segmentos.map(s => limpa(s.texto)).join(' ').match(/[A-Za-zÀ-ÿ]{4,}/g) || [])].slice(0, 100);
  if (!muda && v.op.legendas) elementos.push({ type: 'subtitles', language: 'pt-BR', model: 'whisper', settings: {
    keywords: palavras,
    style: 'boxed-word', 'all-caps': true, 'font-family': 'Montserrat', 'font-weight': '900', 'font-size': Math.round((vertical ? 128 : 96) * k),
    'word-color': '#111111', 'box-color': destaque, 'line-color': '#FFFFFF', 'outline-color': '#000000', 'outline-width': 6,
    'shadow-color': '#000000', 'shadow-offset': 3,
    'max-words-per-line': vertical ? 3 : 5, position: 'mid-bottom-center' } });
  return { comment: `anúncio ${v.job}${muda ? ' (só música)' : ''}`, resolution: 'custom', width: W, height: H, quality: 'high', scenes: cenas(muda), elements: elementos };
}

const pedidos = [{ json: { versao: 'narrado', corpo: JSON.stringify(filme(false)) } }];
if (v.op.versao_musica) pedidos.push({ json: { versao: 'musica', corpo: JSON.stringify(filme(true)) } });
return pedidos;
