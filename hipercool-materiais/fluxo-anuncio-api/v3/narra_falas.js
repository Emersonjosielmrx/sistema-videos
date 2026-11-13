// Narra cada trecho do roteiro com a voz do Google Tradutor (grátis, sem chave, voz feminina em português).
// O Google aceita até ~200 letras por pedido: fala longa vai em pedaços e os MP3 são emendados.
// O MP3 do Google tem taxa fixa de 64 kbps, então a duração sai do tamanho: segundos = bytes × 8 ÷ 64000.
const v = $('🧩 Confere o pedido').first().json;
const ed = $('🧩 Junta tudo').first().json;
const limpa = s => String(s || '').replace(/[\u{1F000}-\u{1FAFF}☀-➿️‍]/gu, '').replace(/\s+/g, ' ').trim();
function pedacos(texto, max = 180) {
  const out = [];
  let resto = texto;
  while (resto.length > max) {
    let corte = Math.max(resto.lastIndexOf('. ', max), resto.lastIndexOf(', ', max), resto.lastIndexOf('! ', max), resto.lastIndexOf('? ', max));
    if (corte < 40) corte = resto.lastIndexOf(' ', max);
    if (corte < 1) corte = max;
    out.push(resto.slice(0, corte + 1).trim());
    resto = resto.slice(corte + 1).trim();
  }
  if (resto) out.push(resto);
  return out;
}
const saida = [];
for (const s of ed.segmentos) {
  const texto = limpa(s.texto);
  if (!texto) continue;
  const partes = [];
  for (const p of pedacos(texto)) {
    let buf = null;
    for (let tentativa = 0; tentativa < 3 && !buf; tentativa++) {
      try {
        const dados = await this.helpers.httpRequest({
          url: 'https://translate.google.com/translate_tts?ie=UTF-8&client=tw-ob&tl=pt-BR&q=' + encodeURIComponent(p),
          headers: { 'User-Agent': 'Mozilla/5.0' }, encoding: 'arraybuffer', timeout: 30000 });
        buf = Buffer.from(dados);
      } catch (e) {
        await new Promise(r => setTimeout(r, 1500 * (tentativa + 1)));
      }
    }
    if (buf && buf.length > 1000) partes.push(buf);
  }
  if (!partes.length) continue;
  const mp3 = Buffer.concat(partes);
  saida.push({ json: { n: s.n, id: `voz-${v.job}-${s.n}.mp3`, b64: mp3.toString('base64'), dur: Math.round(mp3.length * 8 / 64000 * 1000) / 1000 } });
}
if (saida.length < 2) throw new Error('A voz do Google não respondeu agora. Tente de novo em alguns minutos.');
return saida;
