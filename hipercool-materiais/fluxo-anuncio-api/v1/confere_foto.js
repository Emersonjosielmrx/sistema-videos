// Confere a foto que a página mandou (JPG, PNG ou WEBP de até 25 MB) e prepara para guardar no Redis (30 dias).
// O "código" da foto é aleatório; o endereço público é /webhook/anuncio-video-j2v-arquivo?id=<código>.
const it = $input.first();
const chave = Object.keys(it.binary || {})[0];
if (!chave) return [{ json: { ok: false, erro: 'Nenhuma foto chegou.' } }];
const arq = it.binary[chave];
const EXT = { 'image/jpeg': 'jpg', 'image/jpg': 'jpg', 'image/png': 'png', 'image/webp': 'webp' };
const ext = EXT[String(arq.mimeType || '').toLowerCase()];
if (!ext) return [{ json: { ok: false, erro: /heic|heif/i.test(arq.mimeType + arq.fileName) ? 'Foto HEIC: abra no celular e mande de novo (o iPhone converte para JPG).' : 'Formato não aceito. Envie JPG, PNG ou WEBP.' } }];
const buf = await this.helpers.getBinaryDataBuffer(0, chave);
if (buf.length > 25e6) return [{ json: { ok: false, erro: 'Foto maior que 25 MB.' } }];
const id = require('crypto').randomBytes(6).toString('hex') + '.' + ext;
return [{ json: { ok: true, id, b64: buf.toString('base64') } }];
