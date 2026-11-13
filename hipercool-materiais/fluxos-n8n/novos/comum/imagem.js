// ── Imagens grátis e sem chave ──
// FLUX.1-schnell no Hugging Face (melhor, sem marca; cota grátis por IP acaba rápido) e Pollinations (reserva, selo
// "pollinations.ai" no canto; limita pedidos seguidos por IP: 402/429 = esperar e tentar de novo).
// Precisa de gradio.js antes (gradioChama, urlDe).
const TAMANHOS = { '9:16': [576, 1024], '16:9': [1024, 576], '1:1': [768, 768], '4:5': [768, 960], '3:4': [672, 896] };

async function imagemFlux(helpers, prompt, formato, semente) {
  const [w, h] = TAMANHOS[formato] || TAMANHOS['9:16'];
  const d = await gradioChama(helpers, 'black-forest-labs-flux-1-schnell', 'infer', [prompt, semente || 0, !semente, w, h, 4]);
  const url = urlDe(d);
  if (!url) throw new Error('FLUX: sem imagem');
  const img = Buffer.from(await helpers.httpRequest({ url, encoding: 'arraybuffer', timeout: 30000 }));
  return { img, tipo: 'image/webp', ext: 'webp', motor: 'flux-schnell (Hugging Face)' };
}

async function imagemPollinations(helpers, prompt, formato, semente, tentativas = 3) {
  const [w, h] = TAMANHOS[formato] || TAMANHOS['9:16'];
  const url = 'https://image.pollinations.ai/prompt/' + encodeURIComponent(prompt) + '?width=' + w + '&height=' + h +
    '&model=flux&seed=' + (semente || Math.floor(Math.random() * 1e6));
  let ultimo = '';
  for (let t = 0; t < tentativas; t++) {
    try {
      const img = Buffer.from(await helpers.httpRequest({ url, encoding: 'arraybuffer', timeout: 25000 }));
      if (img.length > 2000) return { img, tipo: 'image/jpeg', ext: 'jpg', motor: 'pollinations (flux)', url };
      ultimo = 'imagem vazia';
    } catch (e) {
      ultimo = String(e.message || e).slice(0, 100);
    }
    await new Promise(r => setTimeout(r, 6000 * (t + 1)));
  }
  throw new Error('Pollinations: ' + ultimo);
}

// Tenta FLUX e depois Pollinations. Devolve { img (Buffer), tipo, ext, motor, aviso }.
async function geraImagem(helpers, prompt, formato, semente, usarHF = true) {
  let aviso = '';
  if (usarHF) {
    try {
      return await imagemFlux(helpers, prompt, formato, semente);
    } catch (e) {
      aviso = String(e.message || e).slice(0, 160);
    }
  }
  const r = await imagemPollinations(helpers, prompt, formato, semente);
  r.aviso = aviso;
  return r;
}
