// Confere o pedido na hora (sem IA) para responder logo com o código; a geração continua depois da resposta.
const ent = $input.first().json;
const b = ent.body || {};
const h = ent.headers || {};
const base = (h['x-forwarded-proto'] || 'https') + '://' + (h['x-forwarded-host'] || h.host);
const prompt = String(b.prompt || '').replace(/\s+/g, ' ').trim().slice(0, 800);
const temFoto = !!b.foto_b64;
if (!prompt && !temFoto) return [{ json: { ok: false, erro: 'Descreva a cena ou mande uma foto.' } }];
const formato = ['9:16', '16:9', '1:1'].includes(b.formato) ? b.formato : '9:16';
const dur = Math.max(2, Math.min(5, Number(b.duracao) || 3));
const [w, hh] = { '9:16': [480, 832], '16:9': [832, 480], '1:1': [640, 640] }[formato];
let foto = null;
if (temFoto) {
  foto = Buffer.from(String(b.foto_b64).replace(/^data:[^,]+,/, ''), 'base64');
  if (foto.length < 1000 || foto.length > 6e6) return [{ json: { ok: false, erro: 'A foto precisa ter entre 1 KB e 6 MB.' } }];
}
const id = Date.now().toString(36) + require('crypto').randomBytes(3).toString('hex');
const item = { json: { ok: true, id, base, prompt, melhorar: b.melhorar !== false, tem_foto: temFoto, w, hh, dur,
  status: base + '/webhook/gratis-clipe-status?id=' + id } };
if (foto) item.binary = { data: await this.helpers.prepareBinaryData(foto, 'foto.jpg', 'image/jpeg') };
return [item];
