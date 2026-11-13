// Formulário da fábrica de vídeos grátis.
__PAGINA__
const corpo = `
<h1>🎬 Fábrica de vídeos grátis</h1>
<p class="sub">Você dá o tema; a IA escreve o roteiro, gera as imagens, narra e monta o vídeo. Tudo grátis e sem chave
(Pollinations, Hugging Face e Bing Tradutor). Leva de 2 a 8 minutos.</p>
<div class="cartao">
  <label for="tema">Tema do vídeo</label>
  <textarea id="tema" maxlength="300" style="min-height:80px">3 curiosidades sobre o Sol que quase ninguém sabe</textarea>
  <div class="linha">
    <div><label for="tipo">Tipo</label><select id="tipo">
      <option value="curiosidades">Curiosidades</option><option value="historia">História narrada</option>
      <option value="dicas">Dicas / passo a passo</option><option value="noticia">Explicação de notícia</option>
      <option value="produto">Apresentação de produto/serviço</option></select></div>
    <div><label for="duracao">Duração</label><select id="duracao"><option value="30">~30 s</option>
      <option value="45" selected>~45 s</option><option value="60">~60 s</option></select></div>
    <div><label for="estilo">Estilo das imagens</label><select id="estilo"><option value="foto">Foto realista</option>
      <option value="cinema">Cinema</option><option value="ilustracao">Ilustração</option><option value="anime">Anime</option>
      <option value="3d">3D animação</option></select></div>
  </div>
  <div class="linha">
    <div><label for="voz">Voz</label><select id="voz"><option value="thalita">Thalita</option><option value="andrew">Andrew</option>
      <option value="brian">Brian</option><option value="emma">Emma</option><option value="google">Google (reserva)</option></select></div>
    <div><label for="velocidade">Ritmo</label><select id="velocidade"><option value="0">Normal</option>
      <option value="10" selected>Um pouco rápido</option><option value="20">Rápido (Shorts)</option></select></div>
    <div><label for="modo">Formato</label><select id="modo">
      <option value="navegador">Vertical 9:16 (montado no seu navegador)</option>
      <option value="nuvem">Deitado 16:9 (montado na nuvem, pronto)</option></select></div>
  </div>
  <button id="ir">Criar vídeo</button>
  <p id="estado" class="aviso"></p>
</div>
<div class="cartao aviso"><b>Como sai:</b> deitado 16:9 vem pronto (montador grátis do Hugging Face, 1280x720, legenda
palavra a palavra). Vertical 9:16 é montado no seu navegador na página do resultado (deixe a aba aberta e à vista
durante a montagem). Outros fluxos: <code>POST</code> aqui com <code>{"tema":"...","modo":"nuvem"}</code> → <code>{"link":"..."}</code>.</div>`;
const script = `
const $ = id => document.getElementById(id);
$('ir').onclick = async () => {
  $('ir').disabled = true; $('estado').className = 'aviso'; $('estado').textContent = 'Enviando...';
  try {
    const corpo = {}; for (const k of ['tema', 'tipo', 'duracao', 'estilo', 'voz', 'velocidade', 'modo']) corpo[k] = $(k).value;
    const r = await fetch(location.pathname, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(corpo) });
    const j = await r.json();
    if (!j.ok) throw new Error(j.erro || 'falhou');
    $('estado').className = 'ok'; $('estado').innerHTML = 'Começou! Abrindo o andamento... <a href="' + j.link + '">' + j.link + '</a>';
    location.href = j.link;
  } catch (e) { $('estado').className = 'erro'; $('estado').textContent = 'Não deu: ' + e.message; $('ir').disabled = false; }
};`;
return [{ json: { html: pagina('Fábrica de vídeos grátis', corpo, script) } }];
