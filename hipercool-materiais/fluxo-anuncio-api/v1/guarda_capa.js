// A JSON2Video apaga o vídeo e a capa em 7 dias; a capa (prévia da página no WhatsApp) fica guardada no Redis por 30 dias.
const it = $input.first();
const chave = Object.keys(it.binary || {})[0];
if (!chave) return [{ json: { ok: false } }];
const buf = await this.helpers.getBinaryDataBuffer(0, chave);
return [{ json: { ok: true, id: require('crypto').randomBytes(6).toString('hex') + '.jpg', b64: buf.toString('base64') } }];
