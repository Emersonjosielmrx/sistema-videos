// Página do gerador de clipes de vídeo por IA (LTX-Video no Hugging Face).
__PAGINA__
const corpo = `
<h1>🎥 Clipes de vídeo por IA, grátis</h1>
<p class="sub">Texto → vídeo ou foto → vídeo com o LTX-Video (Hugging Face), sem chave. Clipes de 2 a 5 s, qualidade
abaixo do Veo. A cota grátis acaba depois de alguns clipes por dia.</p>
<div class="cartao">
  <label for="prompt">O que acontece na cena</label>
  <textarea id="prompt" maxlength="800" placeholder="Ex.: drone sobrevoando uma casa com placas solares ao pôr do sol">drone sobrevoando uma casa moderna com placas solares no telhado ao pôr do sol, cinematográfico</textarea>
  <label for="foto">Foto para animar (opcional)</label>
  <input id="foto" type="file" accept="image/*">
  <div class="linha">
    <div><label for="formato">Formato</label><select id="formato"><option value="9:16">Vertical 9:16</option>
      <option value="16:9">Deitado 16:9</option><option value="1:1">Quadrado</option></select></div>
    <div><label for="dur">Duração</label><select id="dur"><option>2</option><option selected>3</option><option>4</option><option>5</option></select></div>
    <div><label for="melhorar">Melhorar o pedido com IA</label><select id="melhorar"><option value="1">Sim</option><option value="0">Não</option></select></div>
  </div>
  <button id="ir">Gerar clipe</button>
  <p id="estado" class="aviso"></p>
  <video id="video" controls loop playsinline hidden></video>
  <a id="baixar" class="botao sec" hidden download="clipe.mp4">Baixar MP4</a>
</div>
<div class="cartao aviso">Outros fluxos: <code>POST</code> aqui com <code>{"prompt":"...","formato":"9:16","duracao":3}</code>
(ou <code>"foto_b64"</code> com a foto em base64) → <code>{"id":"...","status":"..."}</code> na hora; consulte o
<code>status</code> até vir <code>{"etapa":"pronto","url":"..."}</code> (ou <code>"erro"</code>). O link vale 7 dias.</div>`;
const script = `
const $ = id => document.getElementById(id);
function fotoReduzida(arq) {
  return new Promise((ok, falha) => {
    const img = new Image();
    img.onload = () => {
      const m = Math.min(1, 1024 / Math.max(img.width, img.height));
      const c = document.createElement('canvas'); c.width = Math.round(img.width * m); c.height = Math.round(img.height * m);
      c.getContext('2d').drawImage(img, 0, 0, c.width, c.height);
      ok(c.toDataURL('image/jpeg', 0.88));
    };
    img.onerror = () => falha(new Error('não consegui abrir a foto'));
    img.src = URL.createObjectURL(arq);
  });
}
// Plano B: a cota grátis do Hugging Face é por IP. Quando a do servidor acaba, o mesmo pedido sai daqui do navegador
// (IP de quem está usando, cota própria). O Space libera chamadas desta página (CORS).
const HF = 'https://lightricks-ltx-video-distilled.hf.space/gradio_api';
const NEG = 'worst quality, inconsistent motion, blurry, jittery, distorted, watermark, text, subtitles';
async function peloNavegador(s, corpo) {
  $('estado').dataset.extra = ' — a cota grátis do servidor acabou; gerando pelo seu navegador';
  const [w, h] = { '9:16': [480, 832], '16:9': [832, 480], '1:1': [640, 640] }[corpo.formato] || [480, 832];
  let rota = 'text_to_video', foto = null;
  if (corpo.foto_b64) {
    const fd = new FormData();
    fd.append('files', await (await fetch(corpo.foto_b64)).blob(), 'foto.jpg');
    const up = await (await fetch(HF + '/upload', { method: 'POST', body: fd })).json();
    if (!Array.isArray(up) || !up[0]) throw new Error('não consegui mandar a foto ao Hugging Face');
    foto = { path: up[0], orig_name: 'foto.jpg', meta: { _type: 'gradio.FileData' } };
    rota = 'image_to_video';
  }
  const dados = [s.prompt || corpo.prompt, NEG, foto, null, h, w, foto ? 'image-to-video' : 'text-to-video', corpo.duracao, 9, 42, true, 1, true];
  const ev = await (await fetch(HF + '/call/' + rota, { method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ data: dados }) })).json();
  if (!ev.event_id) throw new Error('o Hugging Face não aceitou o pedido agora; tente mais tarde');
  const txt = await (await fetch(HF + '/call/' + rota + '/' + ev.event_id)).text();
  const ultima = txt.split('\\n').filter(l => l.startsWith('data:')).pop() || '';
  let url = null;
  try { const d = JSON.parse(ultima.slice(5)); url = txt.includes('event: complete') && d[0] && d[0].video && d[0].video.url; } catch (e) {}
  if (!url) throw new Error('a cota grátis do Hugging Face acabou (no servidor e neste aparelho); tente daqui a algumas horas');
  return { url: URL.createObjectURL(await (await fetch(url)).blob()), prompt_usado: s.prompt_usado };
}
$('ir').onclick = async () => {
  $('ir').disabled = true; $('video').hidden = true; $('baixar').hidden = true; $('estado').className = 'aviso';
  $('estado').dataset.extra = '';
  const t0 = Date.now();
  const relogio = setInterval(() => { $('estado').textContent = 'Gerando o clipe... ' + Math.round((Date.now() - t0) / 1000) + ' s (de 15 s a 3 min)' + ($('estado').dataset.extra || ''); }, 1000);
  try {
    const arq = $('foto').files[0];
    const corpo = { prompt: $('prompt').value.trim(), formato: $('formato').value, duracao: Number($('dur').value),
      melhorar: $('melhorar').value === '1' };
    if (arq) corpo.foto_b64 = await fotoReduzida(arq);
    const r = await fetch(location.pathname, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(corpo) });
    const p = await r.json();
    if (!p.ok) throw new Error(p.erro || 'falhou');
    // o pedido volta na hora com o código; aqui a página consulta o andamento até o clipe sair (uma consulta que falhar só repete)
    let j = null, falhas = 0;
    while (!j) {
      await new Promise(ok => setTimeout(ok, 3000));
      if (Date.now() - t0 > 12 * 60 * 1000) throw new Error('demorou demais; tente de novo mais tarde');
      try {
        const s = await (await fetch(location.pathname + '-status?id=' + encodeURIComponent(p.id), { cache: 'no-store' })).json();
        falhas = 0;
        if (s.etapa === 'pronto') j = s;
        else if (s.etapa === 'erro' && !s.cota) throw Object.assign(new Error(s.erro || 'falhou'), { doFluxo: true });
        else if (s.etapa === 'erro') j = await peloNavegador(s, corpo).catch(e => { throw Object.assign(e, { doFluxo: true }); });
      } catch (e) {
        if (e.doFluxo || ++falhas > 20) throw e;
      }
    }
    $('video').src = j.url; $('video').hidden = false; $('video').play().catch(() => {});
    $('baixar').href = j.url; $('baixar').hidden = false;
    $('estado').className = 'ok'; $('estado').textContent = 'Pronto em ' + Math.round((Date.now() - t0) / 1000) + ' s' + (j.prompt_usado ? ' — pedido usado: ' + j.prompt_usado : '');
  } catch (e) {
    $('estado').className = 'erro';
    $('estado').textContent = 'Não deu: ' + (e.message === 'Failed to fetch' ? 'a conexão caiu; confira a internet e tente de novo' : e.message);
  }
  clearInterval(relogio); $('ir').disabled = false;
};`;
return [{ json: { html: pagina('Clipes de vídeo grátis', corpo, script) } }];
