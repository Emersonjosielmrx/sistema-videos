// Página da ponte: PC online?, pedir uma ação e acompanhar.
__PAGINA__
let visto = null;
try { visto = JSON.parse($input.first().json.visto || 'null'); } catch (e) { visto = null; }
const ACOES = __ACOES__;
const online = visto && Date.now() - Date.parse(visto.quando) < 3 * 60e3;
const corpo = `
<h1>🌉 Ponte PC ↔ n8n</h1>
<p class="sub">O n8n deixa o pedido numa fila; o trabalhador do PC busca, faz com os geradores que já existem no PC
(Flow/Nano Banana, ffmpeg...) e devolve o resultado. Sem abrir porta no PC e sem instalar nada no servidor.</p>
<div class="cartao"><b>PC:</b> ${online ? '<span class="ok">online</span> (' + escHtml(visto.maquina) + ', visto ' +
  new Date(visto.quando).toLocaleTimeString('pt-BR', { timeZone: 'America/Sao_Paulo' }) + ')'
  : '<span class="erro">fora do ar</span>' + (visto ? ' (último sinal ' + new Date(visto.quando).toLocaleString('pt-BR', { timeZone: 'America/Sao_Paulo' }) + ')' : '') +
  ' — no PC: <code>D:\\hipercool-materiais\\fluxos-n8n\\ponte-pc\\LIGAR_PONTE.bat</code>'}</div>
<div class="cartao">
  <label for="token">Token da ponte</label><input id="token" type="password" placeholder="está em ponte-pc\\config.json no PC">
  <label for="acao">Ação</label><select id="acao">${Object.entries(ACOES).map(([k, v]) => '<option value="' + k + '">' + escHtml(v) + '</option>').join('')}</select>
  <label for="dados">Dados (JSON)</label><textarea id="dados">{"prompt": "casa moderna com placas solares, fim de tarde", "formato": "9:16"}</textarea>
  <button id="ir">Mandar para o PC</button>
  <p id="estado" class="aviso"></p>
  <div id="saida"></div>
</div>
<div class="cartao aviso">Outros fluxos: <code>POST /webhook/ponte-pc/pedido</code> com cabeçalho <code>X-Ponte-Token</code> e
<code>{"acao":"imagem_flow","dados":{...}}</code> → <code>{"id","status_url"}</code>; depois <code>GET /webhook/ponte-pc/status?id=</code>.</div>`;
const script = `
const $ = id => document.getElementById(id);
$('ir').onclick = async () => {
  let dados; try { dados = JSON.parse($('dados').value || '{}'); } catch (e) { $('estado').textContent = 'JSON dos dados inválido'; return; }
  $('ir').disabled = true; $('estado').className = 'aviso'; $('estado').textContent = 'Enviando...';
  try {
    const r = await fetch('ponte-pc/pedido', { method: 'POST', headers: { 'Content-Type': 'application/json', 'X-Ponte-Token': $('token').value },
      body: JSON.stringify({ acao: $('acao').value, dados, origem: 'página' }) });
    const j = await r.json();
    if (!j.ok) throw new Error(j.erro || 'falhou');
    $('estado').textContent = 'Na fila (' + j.id + '). Esperando o PC...';
    const olha = async () => {
      const s = await (await fetch('ponte-pc/status?id=' + j.id, { cache: 'no-store' })).json();
      $('estado').textContent = 'Situação: ' + s.etapa + (s.maquina ? ' (' + s.maquina + ')' : '') + (s.mensagem ? ' — ' + s.mensagem : '');
      if (s.etapa === 'pronto' || s.etapa === 'erro') {
        $('estado').className = s.etapa === 'pronto' ? 'ok' : 'erro';
        if (s.arquivo) $('saida').innerHTML = /\\.(png|jpe?g|webp)$/.test(s.arquivo) ? '<img src="' + s.arquivo + '" style="max-width:100%;border-radius:10px">'
          : /\\.(mp4|webm)$/.test(s.arquivo) ? '<video controls src="' + s.arquivo + '"></video>' : '<a class="botao" href="' + s.arquivo + '">Baixar</a>';
        $('ir').disabled = false; return;
      }
      setTimeout(olha, 4000);
    };
    olha();
  } catch (e) { $('estado').className = 'erro'; $('estado').textContent = 'Não deu: ' + e.message; $('ir').disabled = false; }
};`;
return [{ json: { html: pagina('Ponte PC', corpo, script) } }];
