// Narra o roteiro inteiro (voz neural do Bing; reserva Google) e divide o tempo entre as cenas pelo tamanho das falas.
__VOZ__
const v = $('🧩 Confere o pedido').first().json;
const rot = $('🔎 Revisa os fatos').first().json;
const imgs = $input.all().map(i => i.json).sort((a, b) => a.n - b.n);
if (!imgs.some(i => i.ok)) return [{ json: { ok: false, erro: 'Nenhuma imagem saiu (geradores grátis cheios). Tente mais tarde.' } }];
const falas = rot.cenas.map(c => limpaFala(c.fala));
try {
  const r = await narra(this.helpers, falas.join(' '), v.voz, v.velocidade);
  const pesos = falas.map(f => f.length + 12);
  const soma = pesos.reduce((a, b) => a + b, 0);
  let t = 0;
  const cenas = falas.map((fala, i) => {
    // cena sem imagem usa a imagem que saiu mais perto
    const proprio = imgs.find(x => x.n === i + 1 && x.ok);
    const outra = proprio || imgs.filter(x => x.ok).sort((a, b) => Math.abs(a.n - (i + 1)) - Math.abs(b.n - (i + 1)))[0];
    const ini = t;
    t += r.segundos * pesos[i] / soma;
    return { n: i + 1, fala, ini: Math.round(ini * 100) / 100, fim: Math.round(t * 100) / 100,
      img: v.arquivo + 'img' + outra.n + '.' + outra.ext, img_n: outra.n };
  });
  // as imagens (base64) seguem junto: o montador da nuvem precisa delas e o loop não é lido depois
  return [{ json: { ok: true, b64: r.mp3.toString('base64'), segundos: r.segundos, motor: r.motor, aviso: r.aviso || '', cenas,
    texto: falas.join(' '), imgs } }];
} catch (e) {
  return [{ json: { ok: false, erro: 'A narração falhou: ' + String(e.message || e).slice(0, 200) } }];
}
