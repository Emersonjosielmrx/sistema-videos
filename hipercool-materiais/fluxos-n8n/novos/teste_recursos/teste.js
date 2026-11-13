// Mostra o que o Code deste n8n deixa usar (para escolher o caminho dos fluxos sem chave).
__VOZ_EDGE__
const q = $input.first().json.query || {};
const r = {};
r.WebSocket = typeof WebSocket;
r.fetch = typeof fetch;
r.crypto_global = typeof crypto;
r.subtle = typeof (globalThis.crypto && globalThis.crypto.subtle);
r.require = typeof require;
try { require('crypto'); r.require_crypto = 'ok'; } catch (e) { r.require_crypto = String(e.message).slice(0, 160); }
r.modulos = {};
for (const m of ['https', 'http', 'tls', 'net', 'dns', 'zlib', 'stream', 'events', 'os', 'fs', 'path', 'child_process',
  'url', 'util', 'buffer', 'ws', 'axios', 'form-data', 'lodash', 'moment', 'luxon']) {
  try { require(m); r.modulos[m] = 'ok'; } catch (e) { r.modulos[m] = String(e.message).slice(0, 80); }
}
r.URL = typeof URL;
r.TextEncoder = typeof TextEncoder;
r.setTimeout = typeof setTimeout;
r.Buffer = typeof Buffer;
r.BigInt = typeof BigInt;
r.node = (typeof process !== 'undefined' && process.version) || 'sem process';
r.sha_teste = sha256hex('abc') === 'ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad';
if (q.dormir) {
  const t0 = Date.now();
  await new Promise(ok => setTimeout(ok, Number(q.dormir) * 1000));
  r.dormiu_s = (Date.now() - t0) / 1000;
}
if (q.sobe) {
  // testa o envio de arquivo (multipart) a um Space do Hugging Face
  const lim = '----n8n' + Math.random().toString(16).slice(2);
  const arq = Buffer.alloc(512);
  for (let i = 0; i < 512; i++) arq[i] = i % 256;  // todos os bytes de 0 a 255: mostra se o envio estraga binário
  r.sha_enviado = require('crypto').createHash('sha1').update(arq).digest('hex');
  const corpo = Buffer.concat([Buffer.from('--' + lim + '\r\nContent-Disposition: form-data; name="files"; filename="t.txt"\r\nContent-Type: text/plain\r\n\r\n'),
    arq, Buffer.from('\r\n--' + lim + '--\r\n')]);
  const modos = { string_binaria: { body: corpo.toString('binary'), json: false },
    string_binaria_latin1: { body: corpo.toString('latin1'), json: false, encoding: 'latin1' },
    arraybuffer: { body: corpo.buffer.slice(corpo.byteOffset, corpo.byteOffset + corpo.length), json: false },
    uint8: { body: new Uint8Array(corpo), json: false } };
  r.sobe = {};
  for (const [nome, extra] of Object.entries(modos)) {
    try {
      const resp = await this.helpers.httpRequest({ method: 'POST', url: 'https://tim13ekd-video-ffmpeg.hf.space/gradio_api/upload',
        headers: { 'Content-Type': 'multipart/form-data; boundary=' + lim }, timeout: 30000, ...extra });
      r.sobe[nome] = String(typeof resp === 'string' ? resp : JSON.stringify(resp)).slice(0, 200);
      const lista = typeof resp === 'string' ? JSON.parse(resp) : resp;
      if (Array.isArray(lista) && lista[0]) {
        const volta = Buffer.from(await this.helpers.httpRequest({ url: 'https://tim13ekd-video-ffmpeg.hf.space/gradio_api/file=' + lista[0],
          encoding: 'arraybuffer', timeout: 30000 }));
        r.sobe[nome] += ' | voltou ' + volta.length + ' bytes, sha ' + require('crypto').createHash('sha1').update(volta).digest('hex');
      }
    } catch (e) {
      r.sobe[nome] = 'ERRO ' + String(e.message).slice(0, 80) + ' | ' + JSON.stringify((e.response && e.response.body) || e.description || '').slice(0, 200);
    }
  }
}
if (q.edge) {
  const t0 = Date.now();
  try {
    const mp3 = await vozEdge('Olá! Esta é a voz neural grátis, direto do n8n, sem chave nenhuma.', q.voz || 'pt-BR-FranciscaNeural');
    r.edge = { ok: true, bytes: mp3.length, s: (Date.now() - t0) / 1000 };
    if (q.audio) {
      const bin = await this.helpers.prepareBinaryData(mp3, 'voz.mp3', 'audio/mpeg');
      return [{ json: r, binary: { data: bin } }];
    }
  } catch (e) {
    r.edge = { ok: false, erro: String(e.message || e).slice(0, 300), s: (Date.now() - t0) / 1000 };
  }
}
return [{ json: r }];
