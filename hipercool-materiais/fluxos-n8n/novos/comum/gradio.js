// ── Spaces do Hugging Face pela API pública do Gradio (sem chave; cota grátis por IP) ──
// Chamada curta (cabe nos 60 s do Code). Para espera longa, use dois nós HTTP: POST .../call/<rota> e
// GET .../call/<rota>/<event_id> (texto), e depois gradioLe() num Code.
async function gradioChama(helpers, espaco, rota, dados, limite = 50000) {
  const base = 'https://' + espaco + '.hf.space/gradio_api/call/' + rota;
  const r = await helpers.httpRequest({ method: 'POST', url: base, body: { data: dados }, json: true, timeout: 20000 });
  const ev = r && r.event_id;
  if (!ev) throw new Error(espaco + ': sem event_id');
  return gradioLe(String(await helpers.httpRequest({ url: base + '/' + ev, timeout: limite, json: false })), espaco);
}

// Lê a resposta (SSE) da 2ª chamada: devolve o JSON final ou dá erro com o motivo.
function gradioLe(txt, espaco = 'Hugging Face') {
  txt = String(txt || '');
  if (!txt.includes('event: complete')) {
    const m = /event: error\s*\ndata: (.*)/.exec(txt);
    const motivo = m && m[1] !== 'null' ? m[1].slice(0, 200) : 'recusou (a cota grátis do Hugging Face acabou ou a fila está cheia; tente mais tarde)';
    throw new Error(espaco + ': ' + motivo);
  }
  const linhas = txt.split('\n').filter(l => l.startsWith('data:'));
  return JSON.parse(linhas[linhas.length - 1].slice(5));
}

const urlDe = d => { const m = /"url":\s*"([^"]+)"/.exec(JSON.stringify(d)); return m ? m[1] : null; };

// Arquivos para o Space: o Gradio não aceita link de fora nem base64 nas entradas de arquivo, só o caminho de um
// upload (POST .../gradio_api/upload, multipart). O upload tem que ser pelo nó HTTP do n8n (n8nlib.http_envia_arquivo):
// o httpRequest do Code manda o binário como UTF-8 e estraga o arquivo (testado 30/10: 512 bytes viraram 768).
const arquivoGradio = (caminho, nome) => ({ path: caminho, orig_name: nome, meta: { _type: 'gradio.FileData' } });
function caminhoDoUpload(txt) {
  try { const l = JSON.parse(String(txt || '')); return Array.isArray(l) && l[0] ? l[0] : null; } catch (e) { return null; }
}
