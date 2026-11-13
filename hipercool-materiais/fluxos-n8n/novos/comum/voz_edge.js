// ── Voz neural da Microsoft (a mesma do "Ler em voz alta" do Edge), grátis e sem chave ──
// Fala direto com o serviço do Edge por WebSocket. Devolve o MP3 (Buffer). Sem instalar nada: usa o WebSocket que
// já vem no Node do n8n. Se o n8n não tiver WebSocket (versão antiga), dá erro e o fluxo usa a voz do Google.
function sha256hex(texto) {
  // SHA-256 em JS puro (o Code do n8n nem sempre deixa usar o módulo crypto)
  const K = [0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5, 0x3956c25b, 0x59f111f1, 0x923f82a4, 0xab1c5ed5, 0xd807aa98,
    0x12835b01, 0x243185be, 0x550c7dc3, 0x72be5d74, 0x80deb1fe, 0x9bdc06a7, 0xc19bf174, 0xe49b69c1, 0xefbe4786, 0x0fc19dc6,
    0x240ca1cc, 0x2de92c6f, 0x4a7484aa, 0x5cb0a9dc, 0x76f988da, 0x983e5152, 0xa831c66d, 0xb00327c8, 0xbf597fc7, 0xc6e00bf3,
    0xd5a79147, 0x06ca6351, 0x14292967, 0x27b70a85, 0x2e1b2138, 0x4d2c6dfc, 0x53380d13, 0x650a7354, 0x766a0abb, 0x81c2c92e,
    0x92722c85, 0xa2bfe8a1, 0xa81a664b, 0xc24b8b70, 0xc76c51a3, 0xd192e819, 0xd6990624, 0xf40e3585, 0x106aa070, 0x19a4c116,
    0x1e376c08, 0x2748774c, 0x34b0bcb5, 0x391c0cb3, 0x4ed8aa4a, 0x5b9cca4f, 0x682e6ff3, 0x748f82ee, 0x78a5636f, 0x84c87814,
    0x8cc70208, 0x90befffa, 0xa4506ceb, 0xbef9a3f7, 0xc67178f2];
  const bytes = Buffer.from(texto, 'utf8');
  const l = bytes.length;
  const tam = ((l + 9 + 63) >> 6) << 6;
  const m = Buffer.alloc(tam);
  bytes.copy(m);
  m[l] = 0x80;
  m.writeUInt32BE(Math.floor((l * 8) / 0x100000000), tam - 8);
  m.writeUInt32BE((l * 8) >>> 0, tam - 4);
  let h = [0x6a09e667, 0xbb67ae85, 0x3c6ef372, 0xa54ff53a, 0x510e527f, 0x9b05688c, 0x1f83d9ab, 0x5be0cd19];
  const w = new Array(64);
  const rotr = (x, n) => (x >>> n) | (x << (32 - n));
  for (let i = 0; i < tam; i += 64) {
    for (let t = 0; t < 16; t++) w[t] = m.readUInt32BE(i + t * 4);
    for (let t = 16; t < 64; t++) {
      const s0 = rotr(w[t - 15], 7) ^ rotr(w[t - 15], 18) ^ (w[t - 15] >>> 3);
      const s1 = rotr(w[t - 2], 17) ^ rotr(w[t - 2], 19) ^ (w[t - 2] >>> 10);
      w[t] = (w[t - 16] + s0 + w[t - 7] + s1) >>> 0;
    }
    let [a, b, c, d, e, f, g, hh] = h;
    for (let t = 0; t < 64; t++) {
      const S1 = rotr(e, 6) ^ rotr(e, 11) ^ rotr(e, 25);
      const ch = (e & f) ^ (~e & g);
      const t1 = (hh + S1 + ch + K[t] + w[t]) >>> 0;
      const S0 = rotr(a, 2) ^ rotr(a, 13) ^ rotr(a, 22);
      const mj = (a & b) ^ (a & c) ^ (b & c);
      const t2 = (S0 + mj) >>> 0;
      hh = g; g = f; f = e; e = (d + t1) >>> 0; d = c; c = b; b = a; a = (t1 + t2) >>> 0;
    }
    h = [a, b, c, d, e, f, g, hh].map((x, k) => (x + h[k]) >>> 0);
  }
  return h.map(x => x.toString(16).padStart(8, '0')).join('');
}

function idAleatorio() {
  let s = '';
  for (let i = 0; i < 32; i++) s += Math.floor(Math.random() * 16).toString(16);
  return s;
}

const escapaXml = s => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
  .replace(/"/g, '&quot;').replace(/'/g, '&apos;');

async function vozEdge(texto, voz = 'pt-BR-FranciscaNeural', velocidade = '+0%', tom = '+0Hz') {
  if (typeof WebSocket === 'undefined') throw new Error('este n8n não tem WebSocket no Code (voz neural indisponível)');
  const TOKEN = '<SEGREDO_REMOVIDO>';
  const VERSAO = '1-130.0.2849.68';
  let seg = Math.floor(Date.now() / 1000) + 11644473600;
  seg -= seg % 300;
  const gec = sha256hex(String(BigInt(seg) * 10000000n) + TOKEN).toUpperCase();
  const id = idAleatorio();
  const url = 'wss://speech.platform.bing.com/consumer/speech/synthesize/readaloud/edge/v1?TrustedClientToken=' + TOKEN +
    '&Sec-MS-GEC=' + gec + '&Sec-MS-GEC-Version=' + VERSAO + '&ConnectionId=' + id;
  let ws;
  try {
    ws = new WebSocket(url, { headers: { Origin: 'chrome-extension://jdiccldimpdaibmpdkjnbmckianbfold',
      'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36 Edg/130.0.0.0' } });
  } catch (e) {
    ws = new WebSocket(url);
  }
  ws.binaryType = 'arraybuffer';
  return await new Promise((ok, falha) => {
    const partes = [];
    let acabou = false;
    const fim = (erro) => {
      if (acabou) return;
      acabou = true;
      clearTimeout(relogio);
      try { ws.close(); } catch (e) { /* já fechou */ }
      if (erro) falha(erro);
      else if (!partes.length) falha(new Error('edge: não veio áudio'));
      else ok(Buffer.concat(partes));
    };
    const relogio = setTimeout(() => fim(new Error('edge: demorou demais')), 90000);
    ws.onopen = () => {
      const ts = new Date().toString();
      ws.send('X-Timestamp:' + ts + '\r\nContent-Type:application/json; charset=utf-8\r\nPath:speech.config\r\n\r\n' +
        '{"context":{"synthesis":{"audio":{"metadataoptions":{"sentenceBoundaryEnabled":"false","wordBoundaryEnabled":"false"},' +
        '"outputFormat":"audio-24khz-48kbitrate-mono-mp3"}}}}');
      const ssml = "<speak version='1.0' xmlns='http://www.w3.org/2001/10/synthesis' xml:lang='pt-BR'><voice name='" + voz +
        "'><prosody pitch='" + tom + "' rate='" + velocidade + "' volume='+0%'>" + escapaXml(texto) + '</prosody></voice></speak>';
      ws.send('X-RequestId:' + id + '\r\nContent-Type:application/ssml+xml\r\nX-Timestamp:' + ts + 'Z\r\nPath:ssml\r\n\r\n' + ssml);
    };
    ws.onmessage = (ev) => {
      if (typeof ev.data === 'string') {
        if (ev.data.includes('Path:turn.end')) fim();
        return;
      }
      const b = Buffer.from(ev.data);
      if (b.length < 2) return;
      const n = b.readUInt16BE(0);
      if (b.slice(2, 2 + n).toString().includes('Path:audio')) partes.push(b.slice(2 + n));
    };
    ws.onerror = (e) => fim(new Error('edge: ' + ((e && (e.message || (e.error && e.error.message))) || 'erro na conexão')));
    ws.onclose = (e) => { if (!acabou) fim(partes.length ? null : new Error('edge: conexão fechada (' + (e && e.code) + ')')); };
  });
}
