// Página do andamento e do resultado. No modo "navegador" o vídeo vertical é montado aqui mesmo (canvas + gravador do
// navegador): nada para instalar no servidor e nenhuma chave.
__PAGINA__
const q = $input.first().json.query || {};
const job = String(q.id || '').toLowerCase().replace(/[^a-z0-9]/g, '').slice(0, 40);
const corpo = `
<h1>🎬 Seu vídeo</h1>
<p class="sub" id="tema">Carregando...</p>
<div class="cartao" id="andamento">
  <b id="etapa">Na fila...</b>
  <div class="barra"><i id="barra"></i></div>
  <p class="aviso" id="detalhe">Leva de 2 a 8 minutos. Pode deixar esta página aberta.</p>
</div>
<div id="resultado" hidden>
  <div class="cartao">
    <h2>Vídeo</h2>
    <p id="aviso" class="aviso"></p>
    <video id="video" controls playsinline hidden></video>
    <a id="baixar_video" class="botao" hidden download="video.mp4">Baixar vídeo</a>
    <div id="montador" hidden>
      <p class="aviso">Montado aqui no seu navegador: aperte o botão e deixe esta aba aberta e à vista até terminar
      (leva o tempo do vídeo). Funciona melhor no Chrome ou Edge do computador.</p>
      <canvas id="tela" style="width:100%;max-width:340px;border-radius:12px;background:#000;display:block;margin:auto"></canvas>
      <button id="montar">🎬 Montar o vídeo</button>
      <div class="barra"><i id="barra_montagem"></i></div>
      <p id="estado_montagem" class="aviso"></p>
      <video id="video_montado" controls playsinline hidden></video>
      <a id="baixar_montado" class="botao" hidden>Baixar vídeo</a>
    </div>
  </div>
  <div class="cartao">
    <h2>Para postar</h2>
    <label>Título</label><pre id="titulo"></pre><button class="botao sec" data-copiar="titulo">Copiar título</button>
    <label>Descrição</label><pre id="descricao"></pre><button class="botao sec" data-copiar="descricao">Copiar descrição</button>
  </div>
  <div class="cartao"><h2>Narração</h2><audio id="voz" controls></audio><p class="aviso" id="info"></p></div>
  <div class="cartao"><h2>Cenas</h2><div class="grade" id="cenas"></div></div>
  <a class="botao sec" href="gratis-video">Fazer outro vídeo</a>
</div>`;
const script = `
const JOB = ${JSON.stringify(job)};
const $ = id => document.getElementById(id);
const ETAPAS = { recebido: [5, 'Pedido recebido'], roteiro: [12, 'Escrevendo o roteiro (IA grátis)'],
  imagens: [30, 'Gerando as imagens das cenas'], narrando: [65, 'Narrando com voz neural'],
  montando: [80, 'Montando o vídeo na nuvem grátis'], pronto: [100, 'Pronto!'], erro: [100, 'Não deu certo'] };
let filme = null;
async function olha() {
  if (!JOB) { $('etapa').textContent = 'Link sem código do vídeo.'; return; }
  try {
    const r = await fetch('gratis-video-status?id=' + JOB, { cache: 'no-store' });
    const s = await r.json();
    if (s.tema) $('tema').textContent = s.tema;
    const e = ETAPAS[s.etapa] || [3, 'Na fila...'];
    $('etapa').textContent = e[1]; $('barra').style.width = (s.pct || e[0]) + '%';
    if (s.detalhe) $('detalhe').textContent = s.detalhe;
    if (s.etapa === 'pronto') return mostra(s);
    if (s.etapa === 'erro') { $('detalhe').className = 'erro'; $('detalhe').textContent = s.erro || 'Falhou.'; return; }
    if (s.etapa === 'desconhecido') { $('detalhe').textContent = 'Vídeo não encontrado (os links valem 3 dias).'; return; }
  } catch (e) { /* tenta de novo */ }
  setTimeout(olha, 3000);
}
function mostra(s) {
  $('andamento').hidden = true; $('resultado').hidden = false;
  $('titulo').textContent = s.titulo || '';
  $('descricao').textContent = (s.descricao || '') + '\\n\\n' + (s.hashtags || []).join(' ');
  $('voz').src = s.voz;
  $('info').textContent = 'Voz: ' + (s.motor_voz || '') + ' · ' + s.segundos + ' s · imagens: ' + (s.motores_imagem || []).join(', ') +
    (s.fonte ? ' · fatos conferidos na ' + s.fonte : '') + (s.revisado ? ' · roteiro revisado' : '');
  $('cenas').innerHTML = (s.imagens || []).map(u => '<a href="' + u + '" target="_blank"><img loading="lazy" src="' + u + '"></a>').join('');
  if (s.aviso) $('aviso').textContent = s.aviso;
  filme = s.filme;
  if (s.video) { $('video').src = s.video; $('video').hidden = false; $('baixar_video').href = s.video; $('baixar_video').hidden = false; }
  else { $('montador').hidden = false; preparaTela(); }
}
document.addEventListener('click', ev => {
  const alvo = ev.target.getAttribute && ev.target.getAttribute('data-copiar');
  if (!alvo) return;
  const t = $(alvo).textContent;
  (navigator.clipboard ? navigator.clipboard.writeText(t) : Promise.reject()).then(
    () => { ev.target.textContent = 'Copiado!'; }, () => { window.prompt('Copie:', t); });
});
// ── montador do navegador ──
const imagens = {};
function carregaImg(url) {
  return new Promise((ok, falha) => {
    const i = new Image(); i.crossOrigin = 'anonymous';
    i.onload = () => ok(i); i.onerror = () => falha(new Error('imagem não carregou'));
    i.src = url;
  });
}
async function preparaTela() {
  const tela = $('tela'); tela.width = filme.largura; tela.height = filme.altura;
  try {
    for (const c of filme.cenas) if (!imagens[c.img]) imagens[c.img] = await carregaImg(c.img);
    desenha(tela.getContext('2d'), 0.4, filme.total);
  } catch (e) { $('estado_montagem').textContent = 'Não carregou as imagens: ' + e.message; }
}
function pintaCena(ctx, img, i, p, W, H, alfa) {
  if (!img) return;
  const z = i % 2 === 0 ? 1.04 + 0.12 * p : 1.16 - 0.12 * p;
  const s = Math.max(W / img.width, H / img.height) * z;
  const w = img.width * s, h = img.height * s;
  const d = [[1, 0], [-1, 0], [0, 1], [0, -1]][i % 4];
  const fx = (w - W) / 2, fy = (h - H) / 2;
  ctx.globalAlpha = alfa;
  ctx.drawImage(img, -fx + d[0] * fx * (p - 0.5) * 0.8, -fy + d[1] * fy * (p - 0.5) * 0.8, w, h);
  ctx.globalAlpha = 1;
}
function fonte(px) { return '900 ' + px + 'px "Arial Black", "Segoe UI Black", Impact, system-ui, sans-serif'; }
function quebra(ctx, texto, max) {
  const linhas = []; let linha = '';
  for (const p of texto.split(' ')) {
    const t = linha ? linha + ' ' + p : p;
    if (ctx.measureText(t).width > max && linha) { linhas.push(linha); linha = p; } else linha = t;
  }
  if (linha) linhas.push(linha);
  return linhas;
}
function caixaTopo(ctx, texto, W, H, alfa) {
  const px = Math.round(Math.min(W, H) * 0.06);
  ctx.font = fonte(px);
  const linhas = quebra(ctx, texto.toUpperCase(), W * 0.84).slice(0, 3);
  const alto = linhas.length * px * 1.25 + px * 0.8, y0 = H * 0.07;
  ctx.globalAlpha = alfa;
  ctx.fillStyle = 'rgba(0,0,0,.6)';
  if (ctx.roundRect) { ctx.beginPath(); ctx.roundRect(W * 0.05, y0, W * 0.9, alto, px * 0.5); ctx.fill(); } else ctx.fillRect(W * 0.05, y0, W * 0.9, alto);
  ctx.fillStyle = '#fff'; ctx.textAlign = 'center'; ctx.textBaseline = 'top';
  linhas.forEach((l, k) => ctx.fillText(l, W / 2, y0 + px * 0.4 + k * px * 1.25));
  ctx.globalAlpha = 1;
}
function legenda(ctx, fala, frac, W, H) {
  const palavras = fala.toUpperCase().split(/\\s+/).filter(Boolean);
  if (!palavras.length) return;
  const grupos = []; let g = [];
  for (const p of palavras) { if (g.length >= 4 || (g.join(' ') + ' ' + p).length > 24) { grupos.push(g); g = []; } g.push(p); }
  if (g.length) grupos.push(g);
  const totalLetras = palavras.join('').length;
  let alvo = Math.max(0, Math.min(1, frac)) * totalLetras, k = 0, soma = 0;
  for (; k < palavras.length - 1; k++) { soma += palavras[k].length; if (soma > alvo) break; }
  let gi = 0, conta = 0;
  for (; gi < grupos.length; gi++) { if (k < conta + grupos[gi].length) break; conta += grupos[gi].length; }
  gi = Math.min(gi, grupos.length - 1);
  const atual = k - conta;
  const px = Math.round(Math.min(W, H) * (W < H ? 0.085 : 0.075));
  ctx.font = fonte(px); ctx.textBaseline = 'middle'; ctx.textAlign = 'left'; ctx.lineJoin = 'round';
  const grupo = grupos[gi];
  const esp = ctx.measureText(' ').width;
  const larguras = grupo.map(p => ctx.measureText(p).width);
  const total = larguras.reduce((a, b) => a + b, 0) + esp * (grupo.length - 1);
  const escala = Math.min(1, (W * 0.9) / total);
  if (escala < 1) ctx.font = fonte(Math.round(px * escala));
  let x = (W - total * escala) / 2;
  const y = H * (W < H ? 0.73 : 0.83);
  grupo.forEach((p, j) => {
    ctx.lineWidth = Math.max(4, px * 0.18); ctx.strokeStyle = '#000'; ctx.strokeText(p, x, y);
    ctx.fillStyle = j === atual ? '#FFE14D' : '#fff'; ctx.fillText(p, x, y);
    x += (larguras[j] + esp) * escala;
  });
}
function desenha(ctx, t, total) {
  const W = filme.largura, H = filme.altura, cs = filme.cenas;
  let i = cs.findIndex(c => t < c.fim); if (i < 0) i = cs.length - 1;
  const c = cs[i];
  const fim = i === cs.length - 1 ? total : c.fim;
  const p = Math.max(0, Math.min(1, (t - c.ini) / Math.max(0.5, fim - c.ini)));
  ctx.fillStyle = '#000'; ctx.fillRect(0, 0, W, H);
  pintaCena(ctx, imagens[c.img], i, p, W, H, 1);
  if (i > 0 && t - c.ini < 0.35) pintaCena(ctx, imagens[cs[i - 1].img], i - 1, 1, W, H, 1 - (t - c.ini) / 0.35);
  if (t < 2.8 && filme.gancho) caixaTopo(ctx, filme.gancho, W, H, Math.min(1, (2.8 - t) / 0.4));
  legenda(ctx, c.fala, (t - c.ini) / Math.max(0.3, c.fim - c.ini), W, H);
  ctx.fillStyle = 'rgba(255,255,255,.25)'; ctx.fillRect(0, H - 8, W, 8);
  ctx.fillStyle = '#2dd4bf'; ctx.fillRect(0, H - 8, W * Math.min(1, t / total), 8);
}
$('montar').onclick = async () => {
  $('montar').disabled = true; $('estado_montagem').className = 'aviso';
  try {
    if (!window.MediaRecorder || !$('tela').captureStream) throw new Error('este navegador não grava vídeo; use Chrome ou Edge');
    $('estado_montagem').textContent = 'Carregando imagens e voz...';
    for (const c of filme.cenas) if (!imagens[c.img]) imagens[c.img] = await carregaImg(c.img);
    const AC = window.AudioContext || window.webkitAudioContext; const ac = new AC();
    const som = await ac.decodeAudioData(await (await fetch(filme.voz)).arrayBuffer());
    const destino = ac.createMediaStreamDestination(); const fonteSom = ac.createBufferSource();
    fonteSom.buffer = som; fonteSom.connect(destino);
    const tela = $('tela'); const ctx = tela.getContext('2d');
    const fluxo = tela.captureStream(30); destino.stream.getAudioTracks().forEach(t => fluxo.addTrack(t));
    const tipos = ['video/mp4;codecs=avc1.42E01E,mp4a.40.2', 'video/mp4', 'video/webm;codecs=vp9,opus', 'video/webm;codecs=vp8,opus', 'video/webm'];
    const tipo = tipos.find(t => MediaRecorder.isTypeSupported(t)) || '';
    const rec = new MediaRecorder(fluxo, tipo ? { mimeType: tipo, videoBitsPerSecond: 6000000, audioBitsPerSecond: 128000 } : {});
    const partes = []; rec.ondataavailable = e => { if (e.data && e.data.size) partes.push(e.data); };
    const parou = new Promise(ok => { rec.onstop = ok; });
    const total = Math.max(filme.total, som.duration + 0.5);
    desenha(ctx, 0, total);
    rec.start(1000);
    const t0 = ac.currentTime + 0.1; fonteSom.start(t0);
    $('estado_montagem').textContent = 'Montando... deixe a aba à vista.';
    await new Promise(ok => {
      const passo = () => {
        const t = Math.max(0, ac.currentTime - t0);
        desenha(ctx, t, total); $('barra_montagem').style.width = Math.min(100, t / total * 100) + '%';
        if (t >= total) ok(); else requestAnimationFrame(passo);
      };
      requestAnimationFrame(passo);
    });
    rec.stop(); await parou; ac.close();
    const ext = (tipo || 'video/webm').includes('mp4') ? 'mp4' : 'webm';
    const url = URL.createObjectURL(new Blob(partes, { type: ext === 'mp4' ? 'video/mp4' : 'video/webm' }));
    $('video_montado').src = url; $('video_montado').hidden = false;
    $('baixar_montado').href = url; $('baixar_montado').download = 'video-' + JOB + '.' + ext; $('baixar_montado').hidden = false;
    $('estado_montagem').className = 'ok';
    $('estado_montagem').textContent = 'Pronto! Arquivo ' + ext.toUpperCase() + (ext === 'webm' ? ' (o YouTube aceita; para o Instagram, converta para MP4).' : '.');
  } catch (e) { $('estado_montagem').className = 'erro'; $('estado_montagem').textContent = 'Não deu: ' + e.message; }
  $('montar').disabled = false;
};
olha();`;
return [{ json: { html: pagina('Seu vídeo — fábrica grátis', corpo, script) } }];
