// Devolve o arquivo guardado no Redis (texto base64) como arquivo de verdade, para o webhook entregar.
const id = String(($('__GATILHO__').first().json.query || {}).id || '');
const b64 = String($input.first().json.dado || '');
const TIPOS = { jpg: 'image/jpeg', jpeg: 'image/jpeg', png: 'image/png', webp: 'image/webp', mp3: 'audio/mpeg',
  mp4: 'video/mp4', webm: 'video/webm', json: 'application/json', txt: 'text/plain' };
const ext = (id.split('.').pop() || '').toLowerCase();
if (!/^[a-z0-9-]{4,80}\.[a-z0-9]{2,5}$/.test(id) || !b64 || !TIPOS[ext]) return [{ json: { existe: false } }];
const bin = await this.helpers.prepareBinaryData(Buffer.from(b64, 'base64'), id, TIPOS[ext]);
return [{ json: { existe: true }, binary: { data: bin } }];
