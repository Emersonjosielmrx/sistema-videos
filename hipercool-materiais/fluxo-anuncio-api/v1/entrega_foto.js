// Transforma a foto guardada no Redis (texto base64) de volta em arquivo, para o webhook entregar como imagem.
// As fotos de exemplo (exemplo-apartamento-1...) vêm do catbox.moe e são entregues pelo mesmo endereço: assim quem lê
// as fotos (wsrv.nl, a API de vídeo, a página) só precisa alcançar este n8n.
const EXEMPLOS = __EXEMPLOS__;
const id = String($('🔔 Entrega a foto (GET)').first().json.query.id || '');
const MIME = { jpg: 'image/jpeg', png: 'image/png', webp: 'image/webp' };
// as trilhas (trilha-elegante...) também passam por aqui: o catbox derruba downloads de alguns servidores na nuvem
const TRILHAS = __TRILHAS__;
const ex = /^exemplo-([a-z]+)-(\d{1,2})$/.exec(id);
const tr = /^trilha-([a-z]+)$/.exec(id);
if (ex || tr) {
  const url = ex ? (EXEMPLOS[ex[1]] || [])[Number(ex[2]) - 1] : TRILHAS[tr[1]];
  if (!url) return [{ json: { existe: false } }];
  const dados = await this.helpers.httpRequest({ url, encoding: 'arraybuffer', timeout: 60000 });
  const bin = ex ? await this.helpers.prepareBinaryData(Buffer.from(dados), id + '.jpg', 'image/jpeg')
    : await this.helpers.prepareBinaryData(Buffer.from(dados), id + '.mp3', 'audio/mpeg');
  return [{ json: { existe: true }, binary: { data: bin } }];
}
// do Redis: fotos enviadas pela página e capas (código.jpg) e, na versão ffmpeg, as vozes e os textos de cada vídeo
const b64 = String($input.first().json.foto || '');
if (!/^([a-f0-9]{12}\.(jpg|png|webp)|(voz|textos)-[a-z0-9-]{4,60}\.(mp3|ass))$/.test(id) || !b64) return [{ json: { existe: false } }];
const TIPO = { ...MIME, mp3: 'audio/mpeg', ass: 'text/plain' };
const binario = await this.helpers.prepareBinaryData(Buffer.from(b64, 'base64'), id, TIPO[id.split('.').pop()]);
return [{ json: { existe: true }, binary: { data: binario } }];
