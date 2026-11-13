// Painel do radar: lê o último retrato e desenha a página.
__PAGINA__
let r = null;
try { r = JSON.parse($input.first().json.retrato || 'null'); } catch (e) { r = null; }
const n = x => x == null ? '–' : Number(x).toLocaleString('pt-BR');
const d = x => x == null ? '' : (x > 0 ? ' <span class="ok">+' + n(x) + '</span>' : x < 0 ? ' <span class="erro">' + n(x) + '</span>' : ' <span class="aviso">=</span>');
const dataBR = s => s ? new Date(s).toLocaleString('pt-BR', { timeZone: 'America/Sao_Paulo' }) : '–';
let corpo = '<h1>📊 Radar dos canais</h1>';
if (!r) {
  corpo += '<p class="sub">Ainda não há leitura. Aperte o botão (leva 1 a 2 minutos) e recarregue.</p>';
} else {
  const t = r.totais;
  corpo += '<p class="sub">Leitura de ' + dataBR(r.quando) + (r.anterior ? ' · comparado com ' + dataBR(r.anterior) : '') +
    '. Dados públicos do YouTube (sem login, sem chave).</p>' +
    '<div class="linha">' +
    '<div class="cartao"><div class="aviso">Inscritos (todos)</div><h2>' + n(t.inscritos) + d(t.d_inscritos) + '</h2></div>' +
    '<div class="cartao"><div class="aviso">Views dos 15 últimos de cada</div><h2>' + n(t.views_recentes) + '</h2></div>' +
    '<div class="cartao"><div class="aviso">Vídeos novos em 7 dias</div><h2>' + n(t.novos_7d) + '</h2></div></div>';
  if (r.alertas.length) corpo += '<div class="cartao"><h2>Alertas</h2>' + r.alertas.map(a => '<div>' + escHtml(a) + '</div>').join('') + '</div>';
  if (r.destaques.length) corpo += '<div class="cartao"><h2>Quem mais ganhou views desde a última leitura</h2>' +
    r.destaques.map(v => '<div>+' + n(v.ganho) + ' · <a href="https://youtu.be/' + v.id + '" target="_blank">' + escHtml(v.titulo) + '</a> <span class="selo">' + escHtml(v.canal) + '</span></div>').join('') + '</div>';
  corpo += '<div class="cartao" style="overflow-x:auto"><h2>Canais</h2><table style="width:100%;border-collapse:collapse;font-size:.92rem">' +
    '<tr style="text-align:left"><th>Canal</th><th>Inscritos</th><th>Vídeos</th><th>Views (15 últ.)</th><th>Novos 7d</th><th>Último vídeo</th></tr>' +
    r.canais.slice().sort((a, b) => (b.d_inscritos || 0) - (a.d_inscritos || 0) || (b.views_recentes - a.views_recentes)).map(c =>
      '<tr style="border-top:1px solid var(--linha)"><td><a href="https://www.youtube.com/channel/' + c.yt_id + '" target="_blank">' + escHtml(c.nome) +
      '</a> <span class="selo">' + escHtml(c.status || '') + '</span></td><td>' + n(c.inscritos) + d(c.d_inscritos) + '</td><td>' + n(c.videos) + d(c.d_videos) +
      '</td><td>' + n(c.views_recentes) + '</td><td>' + c.novos_7d + '</td><td>' + (c.ultimo_video ? dataBR(c.ultimo_video).slice(0, 10) : '–') + '</td></tr>').join('') +
    '</table></div>';
  corpo += '<div class="cartao"><h2>Mais vistos entre os recentes</h2>' + r.mais_vistos.map(v => '<div>' + n(v.views) +
    ' · <a href="https://youtu.be/' + v.id + '" target="_blank">' + escHtml(v.titulo) + '</a> <span class="selo">' + escHtml(v.canal) + '</span></div>').join('') + '</div>';
}
corpo += '<button id="ir">Atualizar agora</button><p id="estado" class="aviso">Atualiza sozinho todo dia às 7h20.</p>';
const script = `document.getElementById('ir').onclick = async () => {
  const b = document.getElementById('ir'); b.disabled = true;
  document.getElementById('estado').textContent = 'Lendo os canais... (1 a 2 minutos; depois recarregue a página)';
  try { await fetch('gratis-radar-atualizar', { method: 'POST' }); } catch (e) {}
  setTimeout(() => location.reload(), 90000);
};`;
return [{ json: { html: pagina('Radar dos canais', corpo, script) } }];
