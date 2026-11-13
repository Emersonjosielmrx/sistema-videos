// Um item por arquivo (imagens das cenas + voz), com o binário, para o nó HTTP subir ao montador grátis.
const voz = $('🎙️ Narra o roteiro').first().json;
const imgs = voz.imgs.filter(i => i.ok && i.b64);
const saida = [];
for (const c of voz.cenas) {
  const im = imgs.find(x => x.n === c.img_n);
  if (!im) continue;
  const nome = 'cena' + c.n + '.' + im.ext;
  saida.push({ json: { tipo: 'img', n: c.n, nome },
    binary: { data: await this.helpers.prepareBinaryData(Buffer.from(im.b64, 'base64'), nome, im.tipo) } });
}
saida.push({ json: { tipo: 'voz', n: 0, nome: 'voz.mp3' },
  binary: { data: await this.helpers.prepareBinaryData(Buffer.from(voz.b64, 'base64'), 'voz.mp3', 'audio/mpeg') } });
return saida;
