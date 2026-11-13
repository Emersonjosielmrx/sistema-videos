// ── Vozes grátis e sem chave ──
// 1º Bing Tradutor (voz NEURAL da Microsoft): pega os códigos da página pública do tradutor e pede o áudio como o
//    próprio site faz. MP3 16 kHz 32 kbps -> segundos = bytes × 8 ÷ 32000.
//    Só as vozes Multilingual aprovadas pela dona (Antonio e Francisca são PROIBIDAS em todos os projetos).
// 2º Google Tradutor (reserva, voz mais robótica): MP3 24 kHz 64 kbps -> segundos = bytes × 8 ÷ 64000.
const UA_VOZ = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0 Safari/537.36 Edg/141.0';
const VOZES_BING = {
  thalita: ['pt-BR-ThalitaMultilingualNeural', 'Female'], andrew: ['en-US-AndrewMultilingualNeural', 'Male'],
  brian: ['en-US-BrianMultilingualNeural', 'Male'], emma: ['en-US-EmmaMultilingualNeural', 'Female'] };

function limpaFala(s) {
  return String(s || '').replace(/[\u{1F000}-\u{1FAFF}\u{2600}-\u{27BF}\u{FE0F}\u{200D}]/gu, '')
    .replace(/[*_#`~|<>]/g, ' ').replace(/\s+/g, ' ').trim();
}

function pedacos(texto, max) {
  const out = [];
  let resto = texto;
  while (resto.length > max) {
    let corte = Math.max(resto.lastIndexOf('. ', max), resto.lastIndexOf('! ', max), resto.lastIndexOf('? ', max));
    if (corte < max * 0.4) corte = Math.max(corte, resto.lastIndexOf(', ', max), resto.lastIndexOf('; ', max));
    if (corte < max * 0.3) corte = resto.lastIndexOf(' ', max);
    if (corte < 1) corte = max;
    out.push(resto.slice(0, corte + 1).trim());
    resto = resto.slice(corte + 1).trim();
  }
  if (resto) out.push(resto);
  return out;
}

const escXml = s => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');

async function vozBing(helpers, texto, voz, velocidade) {
  const pag = await helpers.httpRequest({ url: 'https://www.bing.com/translator', returnFullResponse: true, timeout: 20000,
    headers: { 'User-Agent': UA_VOZ, 'Accept-Language': 'pt-BR,pt;q=0.9' } });
  const h = String(pag.body || '');
  const ig = /IG:"([^"]+)"/.exec(h);
  const iid = /data-iid="(translator\.\d+)"/.exec(h);
  const ab = /params_AbusePreventionHelper\s*=\s*\[(\d+),"([^"]+)",(\d+)\]/.exec(h);
  if (!ig || !ab) throw new Error('Bing: a página do tradutor não trouxe os códigos');
  const sc = (pag.headers && (pag.headers['set-cookie'] || pag.headers['Set-Cookie'])) || [];
  const cookie = [].concat(sc).map(c => String(c).split(';')[0]).join('; ');
  const [nomeVoz, genero] = VOZES_BING[voz] || VOZES_BING.thalita;
  const taxa = Math.max(-50, Math.min(100, Number(velocidade) || 0));
  const partes = [];
  for (const p of pedacos(texto, 900)) {
    const ssml = "<speak version='1.0' xml:lang='pt-BR'><voice xml:lang='pt-BR' xml:gender='" + genero + "' name='" + nomeVoz +
      "'><prosody rate='" + (taxa >= 0 ? '+' : '') + taxa + "%'>" + escXml(p) + '</prosody></voice></speak>';
    const corpo = 'ssml=' + encodeURIComponent(ssml) + '&token=' + encodeURIComponent(ab[2]) + '&key=' + ab[1];
    const audio = await helpers.httpRequest({ method: 'POST', timeout: 30000, encoding: 'arraybuffer', body: corpo,
      url: 'https://www.bing.com/tfettts?isVertical=1&&IG=' + ig[1] + '&IID=' + (iid ? iid[1] : 'translator.5023') + '.1',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded', 'User-Agent': UA_VOZ, Cookie: cookie,
        Referer: 'https://www.bing.com/translator', Origin: 'https://www.bing.com' } });
    const b = Buffer.from(audio);
    if (b.length < 800) throw new Error('Bing: áudio vazio');
    partes.push(b);
  }
  const mp3 = Buffer.concat(partes);
  return { mp3, motor: 'bing-' + nomeVoz, segundos: Math.round(mp3.length * 8 / 32000 * 100) / 100 };
}

async function vozGoogle(helpers, texto) {
  const partes = [];
  for (const p of pedacos(texto, 180)) {
    let b = null;
    for (let t = 0; t < 3 && !b; t++) {
      try {
        const d = await helpers.httpRequest({ timeout: 20000, encoding: 'arraybuffer', headers: { 'User-Agent': UA_VOZ },
          url: 'https://translate.google.com/translate_tts?ie=UTF-8&client=tw-ob&tl=pt-BR&q=' + encodeURIComponent(p) });
        b = Buffer.from(d);
      } catch (e) {
        await new Promise(r => setTimeout(r, 1200 * (t + 1)));
      }
    }
    if (!b || b.length < 500) throw new Error('Google: sem áudio');
    partes.push(b);
  }
  const mp3 = Buffer.concat(partes);
  return { mp3, motor: 'google-tradutor', segundos: Math.round(mp3.length * 8 / 64000 * 100) / 100 };
}

// Tenta a voz neural; se falhar, a do Google. Devolve { mp3, motor, segundos, aviso }.
async function narra(helpers, texto, voz, velocidade) {
  const fala = limpaFala(texto);
  if (!fala) throw new Error('texto vazio');
  if (voz !== 'google') {
    try {
      return await vozBing(helpers, fala, voz, velocidade);
    } catch (e) {
      const r = await vozGoogle(helpers, fala);
      r.aviso = 'voz neural indisponível agora (' + String(e.message || e).slice(0, 120) + '); usada a voz do Google';
      return r;
    }
  }
  return await vozGoogle(helpers, fala);
}
