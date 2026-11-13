// Página do narrador: escreve o texto, escolhe a voz e ouve/baixa o MP3.
__PAGINA__
const corpo = `
<h1>🎙️ Narrador grátis</h1>
<p class="sub">Voz neural da Microsoft (a do Bing Tradutor), sem chave e sem pagar. Se ela falhar, sai a voz do Google.</p>
<div class="cartao">
  <label for="texto">Texto para narrar</label>
  <textarea id="texto" maxlength="5000" placeholder="Cole aqui o roteiro do vídeo...">Você sabia que o Sol entrega à Terra, em uma hora, mais energia do que o mundo inteiro usa em um ano?</textarea>
  <div class="linha">
    <div><label for="voz">Voz</label><select id="voz">
      <option value="thalita">Thalita (feminina)</option>
      <option value="andrew">Andrew (masculina)</option>
      <option value="brian">Brian (masculina)</option>
      <option value="emma">Emma (feminina)</option>
      <option value="google">Google Tradutor (reserva)</option></select></div>
    <div><label for="vel">Velocidade</label><select id="vel">
      <option value="-10">Mais devagar</option><option value="0" selected>Normal</option>
      <option value="10">Um pouco rápida</option><option value="20">Rápida (Shorts)</option></select></div>
  </div>
  <button id="ir">Gerar narração</button>
  <p id="estado" class="aviso"></p>
  <audio id="som" controls hidden></audio>
  <a id="baixar" class="botao sec" hidden download="narracao.mp3">Baixar MP3</a>
</div>
<div class="cartao aviso">Usa em outros fluxos: <code>POST</code> neste mesmo endereço com <code>{"texto":"...","voz":"thalita","velocidade":0}</code> → devolve o MP3 (cabeçalhos <code>X-Motor</code> e <code>X-Segundos</code>).</div>`;
const script = `
const $ = id => document.getElementById(id);
$('ir').onclick = async () => {
  const texto = $('texto').value.trim();
  if (!texto) { $('estado').textContent = 'Escreva um texto.'; return; }
  $('ir').disabled = true; $('estado').className = 'aviso'; $('estado').textContent = 'Gerando a voz...';
  try {
    const r = await fetch(location.pathname, { method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ texto, voz: $('voz').value, velocidade: Number($('vel').value) }) });
    if (!r.ok || !(r.headers.get('content-type') || '').includes('audio')) {
      const j = await r.json().catch(() => ({}));
      throw new Error(j.erro || ('erro ' + r.status));
    }
    const url = URL.createObjectURL(await r.blob());
    $('som').src = url; $('som').hidden = false; $('som').play().catch(() => {});
    $('baixar').href = url; $('baixar').hidden = false;
    const aviso = decodeURIComponent(r.headers.get('X-Aviso') || '');
    $('estado').className = aviso ? 'aviso' : 'ok';
    $('estado').textContent = 'Pronto: ' + (r.headers.get('X-Segundos') || '?') + ' s, voz ' + (r.headers.get('X-Motor') || '') + (aviso ? ' — ' + aviso : '');
  } catch (e) {
    $('estado').className = 'erro'; $('estado').textContent = 'Não deu: ' + e.message;
  }
  $('ir').disabled = false;
};`;
return [{ json: { html: pagina('Narrador grátis', corpo, script) } }];
