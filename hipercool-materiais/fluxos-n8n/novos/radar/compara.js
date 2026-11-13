// Junta os canais, compara com o retrato anterior e marca os alertas (vídeo zerado, canal parado, quem mais cresceu).
let ant = {};
try { ant = JSON.parse($('📖 Lê o retrato anterior').first().json.retrato || '{}'); } catch (e) { ant = {}; }
const antPor = Object.fromEntries((ant.canais || []).map(c => [c.yt_id, c]));
const agora = Date.now();
const H48 = 48 * 3600e3, D3 = 3 * 86400e3, D7 = 7 * 86400e3;
const canais = $input.all().map(i => i.json).map(c => {
  const a = antPor[c.yt_id] || {};
  const viewsAnt = Object.fromEntries((a.ultimos || []).map(v => [v.id, v.views]));
  const ultimos = (c.ultimos || []).map(v => ({ ...v, ganho: viewsAnt[v.id] == null ? null : v.views - viewsAnt[v.id] }));
  const idade = v => agora - Date.parse(v.publicado || 0);
  const ultimo = ultimos.map(v => Date.parse(v.publicado || 0)).sort((x, y) => y - x)[0] || 0;
  return { ...c, ultimos,
    d_inscritos: c.inscritos != null && a.inscritos != null ? c.inscritos - a.inscritos : null,
    d_videos: c.videos != null && a.videos != null ? c.videos - a.videos : null,
    views_recentes: ultimos.reduce((s, v) => s + v.views, 0),
    novos_7d: ultimos.filter(v => idade(v) < D7).length,
    zerados: ultimos.filter(v => idade(v) > H48 && idade(v) < D7 * 2 && v.views < 20).map(v => ({ id: v.id, titulo: v.titulo, views: v.views })),
    parado: ultimo ? agora - ultimo > D3 : true,
    ultimo_video: ultimo ? new Date(ultimo).toISOString() : null };
});
const todos = canais.flatMap(c => c.ultimos.map(v => ({ ...v, canal: c.nome })));
const retrato = {
  quando: new Date().toISOString(), anterior: ant.quando || null,
  totais: { canais: canais.length, inscritos: canais.reduce((s, c) => s + (c.inscritos || 0), 0),
    d_inscritos: canais.reduce((s, c) => s + (c.d_inscritos || 0), 0), views_recentes: canais.reduce((s, c) => s + c.views_recentes, 0),
    novos_7d: canais.reduce((s, c) => s + c.novos_7d, 0) },
  destaques: todos.filter(v => v.ganho != null).sort((a, b) => b.ganho - a.ganho).slice(0, 8),
  mais_vistos: todos.slice().sort((a, b) => b.views - a.views).slice(0, 8),
  alertas: [
    ...canais.filter(c => c.status === 'ativo' && c.parado).map(c => '⏸️ ' + c.nome + ': sem vídeo novo há mais de 3 dias'),
    ...canais.flatMap(c => c.zerados.slice(0, 3).map(v => '🧊 ' + c.nome + ': "' + v.titulo.slice(0, 60) + '" com ' + v.views + ' views depois de 48 h')),
    ...canais.filter(c => !c.ok).map(c => '⚠️ ' + c.nome + ': não deu para ler (' + c.erro + ')') ],
  canais };
return [{ json: { retrato: JSON.stringify(retrato), dia: retrato.quando.slice(0, 10), resumo: retrato.totais, alertas: retrato.alertas.length } }];
