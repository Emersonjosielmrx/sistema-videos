
(function () {
  var el = function (s) { return document.querySelector(s); };
  var VIDEO = '', enviando = false;
  function novoId() { var a = new Uint8Array(6); window.crypto.getRandomValues(a); return Array.prototype.map.call(a, function (b) { return ('0' + b.toString(16)).slice(-2); }).join(''); }
  var envioAtual = null;
  function envia(arq) {
    if (arq.size > 120e6) { el('#info').textContent = '⚠️ Vídeo maior que 120 MB.'; return; }
    el('#prev').src = URL.createObjectURL(arq); el('#prev').hidden = false;
    var id = novoId(), vez = 0, meu = {}; envioAtual = meu;
    enviando = true; VIDEO = ''; el('#barra').hidden = false; el('#barra i').style.width = '0%'; el('#info').textContent = 'Enviando…';
    var fim = function (ok, msg) { if (envioAtual !== meu) return; enviando = false;
      el('#info').innerHTML = ok ? '<span class="ok">✅ Vídeo pronto para editar</span> (' + Math.max(1, Math.round(arq.size / 1e6)) + ' MB)' : '';
      if (!ok) el('#info').textContent = '⚠️ ' + msg; if (ok) VIDEO = id; };
    // a conexão caiu: antes de mandar de novo, confere se o vídeo já tinha chegado
    var caiu = function (motivo) { if (envioAtual !== meu) return;
      if (++vez >= 5) return fim(false, motivo + '. Confira a internet e escolha o vídeo de novo.');
      el('#info').textContent = '⚠️ ' + motivo + ' — tentando de novo (' + (vez + 1) + '/5)…';
      setTimeout(function () { andamento(0, true); }, 1500 * vez); };
    var manda = function () { if (envioAtual !== meu) return;
      var fd = new FormData(); fd.append('video', arq, arq.name || 'video.mp4');
      var x = new XMLHttpRequest(); x.open('POST', 'editor-reel-v6-video?id=' + id);
      x.upload.onprogress = function (e) { if (e.lengthComputable && envioAtual === meu) { var p = Math.round(e.loaded / e.total * 100); el('#barra i').style.width = p + '%'; el('#info').textContent = 'Enviando ' + p + '%' + (p === 100 ? ' · guardando…' : ''); } };
      x.onload = function () { var r = {}; try { r = JSON.parse(x.responseText); } catch (e) {}
        if (x.status === 200 && r.ok) andamento(0, false);
        else if (x.status >= 500 || !x.status) caiu('o servidor não respondeu');
        else fim(false, r.erro || 'não deu para enviar'); };
      x.onerror = function () { caiu('a conexão caiu'); };
      x.onabort = x.onerror;
      x.send(fd); };
    // o n8n guarda o vídeo no armazenamento do ffmpeg na nuvem (alguns segundos): pergunta até ficar pronto
    var andamento = function (n, conferindo) { if (envioAtual !== meu) return;
      fetch('editor-reel-v6-video-status?id=' + id, { cache: 'no-store' }).then(function (r) { return r.json(); }).then(function (r) {
        if (envioAtual !== meu) return;
        if (r.pronto) return fim(true);
        if (r.erro) return fim(false, r.erro);
        if (conferindo) return manda();
        el('#info').textContent = 'Guardando o vídeo…';
        if (n < 90) setTimeout(function () { andamento(n + 1, false); }, 2000); else fim(false, 'demorou demais para guardar o vídeo; escolha de novo');
      }).catch(function () { if (conferindo) return manda(); if (n < 90) setTimeout(function () { andamento(n + 1, false); }, 3000); else fim(false, 'a conexão caiu'); }); };
    manda();
  }
  var drop = el('#drop'), inp = el('#arq');
  drop.addEventListener('click', function () { inp.click(); });
  ['dragover', 'dragenter'].forEach(function (t) { drop.addEventListener(t, function (e) { e.preventDefault(); drop.classList.add('on'); }); });
  ['dragleave', 'drop'].forEach(function (t) { drop.addEventListener(t, function (e) { e.preventDefault(); drop.classList.remove('on'); }); });
  drop.addEventListener('drop', function (e) { if (e.dataTransfer.files.length) envia(e.dataTransfer.files[0]); });
  inp.addEventListener('change', function () { if (inp.files.length) envia(inp.files[0]); inp.value = ''; });
  var EXEMPLOS = {"advance": {"info": "rapaz mostrando a instalação no telhado, 39 s", "tipo": "servico", "marca": "Advance Solar", "titulo": "Instalação de energia solar no Residencial Barãoville, Castanhal", "detalhes": "Projeto de energia solar fechado em 19 de setembro e instalado na casa 114 do Residencial Barãoville, em Castanhal-PA. A equipe mostra a instalação das placas no telhado.", "instagram": "advance_novoestrela"}, "globo": {"info": "depoimento de cliente, 30 s", "tipo": "servico", "marca": "Globo Solar Engenharia", "titulo": "Depoimento de cliente satisfeito com a energia solar", "detalhes": "Cliente Jefferson Barros, morador de Ananindeua (Águas Brancas), conta como foi o serviço de instalação de energia solar da Globo Solar Engenharia.", "instagram": "globosolarenergiag"}, "caue": {"info": "vídeo cru, 73 s, cheio de 'tipo', 'assim' e pausas · AG Jornalismo (YouTube, CC BY)", "tipo": "outro", "marca": "AG Jornalismo", "titulo": "Cauê Ueda conta como foi o workshop sobre o centro de São Paulo", "detalhes": "Entrevista com Cauê Ueda, do Coletivo Baixo Centro, sobre um workshop de projeto para o centro de São Paulo que esqueceu as pessoas que moram lá.", "instagram": ""}, "alderon": {"info": "vídeo cru, 75 s, cheio de 'não é' e pausas · AG Jornalismo (YouTube, CC BY)", "tipo": "outro", "marca": "AG Jornalismo", "titulo": "Alderon Costa fala sobre participação popular no centro de SP", "detalhes": "Entrevista com Alderon Costa, da Rede Rua, sobre a falta de participação popular de verdade nos projetos para o centro de São Paulo.", "instagram": ""}, "luciana": {"info": "vídeo cru, 86 s, entrevista sem edição · AG Jornalismo (YouTube, CC BY)", "tipo": "outro", "marca": "AG Jornalismo", "titulo": "Urbanista Luciana Itikawa critica projeto que exclui ambulantes", "detalhes": "Entrevista com a urbanista Luciana Itikawa: o desenho urbano não resolve questões sociais; são as questões sociais que devem pautar o projeto.", "instagram": ""}};
  Array.prototype.forEach.call(document.querySelectorAll('[data-ex]'), function (bt) { bt.addEventListener('click', function () {
    var k = bt.getAttribute('data-ex'), d = EXEMPLOS[k]; envioAtual = null; enviando = false;
    VIDEO = 'exemplo-' + k; el('#prev').src = 'editor-reel-v6-arquivo?id=exemplo-' + k + '.mp4'; el('#prev').hidden = false; el('#barra').hidden = true;
    el('#info').innerHTML = '<span class="ok">✅ Vídeo real de exemplo</span> (' + d.info + ')';
    el('#tipo').value = d.tipo; el('#marca').value = d.marca; el('#titulo').value = d.titulo;
    el('#instagram').value = d.instagram ? '@' + d.instagram : ''; el('#detalhes').value = d.detalhes;
  }); });
  el('#form').addEventListener('submit', function (e) {
    e.preventDefault(); el('#erro').textContent = '';
    if (enviando) { el('#erro').textContent = 'Espere o vídeo terminar de enviar.'; return; }
    if (!VIDEO) { el('#erro').textContent = 'Envie o vídeo (ou use o exemplo).'; return; }
    var d = { video: VIDEO };
    ['tipo', 'marca', 'titulo', 'detalhes', 'instagram', 'trilha'].forEach(function (c) { d[c] = el('#' + c).value; });
    ['cortar_pausas', 'cortar_vicios', 'legendas', 'cartao_final'].forEach(function (c) { d[c] = el('#' + c).checked; });
    if (!el('#cor-ia').checked) d.cor = el('#cor').value;
    var bt = el('#enviar'); bt.disabled = true; bt.textContent = 'Começando…';
    (function pede(n) { fetch('editor-reel-v6', { method: 'POST', headers: { 'Content-Type': 'text/plain' }, body: JSON.stringify(d) }).then(function (r) { return r.json(); }).then(function (r) {
      if (!r.ok) { el('#erro').textContent = (r.erros || ['Não deu para começar.']).join(' '); bt.disabled = false; bt.textContent = '✂️ Editar o meu Reel'; return; }
      location.href = r.link;
    }).catch(function () { if (n < 3) { bt.textContent = 'A conexão caiu, tentando de novo…'; setTimeout(function () { pede(n + 1); }, 2000); return; }
      el('#erro').textContent = 'Falha de conexão. Confira a internet e tente de novo.'; bt.disabled = false; bt.textContent = '✂️ Editar o meu Reel'; }); })(0);
  });
})();
