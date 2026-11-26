// 🧮 Calcula as métricas do perfil e cruza com os calendários de 30 dias (para saber quais pilares rendem mais).
// Entrada: 🗂️ Lê os calendários (objeto { "p30cal:id": "json" }). Os posts vêm do node 📸 Lê os últimos 30 posts.
const perfil = $('Lê meu perfil').first().json;
const posts = $('Lê os últimos 30 posts').all().map(i => i.json).filter(p => p && p.id && p.timestamp);
const seg = Math.max(1, Number(perfil.followers_count) || 1);
const fuso = 'America/Sao_Paulo';
const FORMATO = { IMAGE: 'Foto', VIDEO: 'Vídeo / Reels', CAROUSEL_ALBUM: 'Carrossel' };
const DIAS = ['domingo', 'segunda', 'terça', 'quarta', 'quinta', 'sexta', 'sábado'];
const r1 = x => Math.round(x * 10) / 10;
const semBarra = s => String(s || '').replace(/\/+$/, '');

// 📅 Posts que nasceram no calendário de 30 dias (o calendário guarda o link de cada post publicado)
const doCalendario = {};
for (const [k, v] of Object.entries($input.first().json || {})) {
  if (!/^p30cal:[a-z0-9-]+$/.test(k)) continue;
  let cal; try { cal = JSON.parse(v); } catch (e) { continue; }
  for (const d of (cal && cal.dias) || []) {
    if (d.link) doCalendario[semBarra(d.link)] = { pilar: d.pilar || '', objetivo: d.objetivo || '', tema: d.tema || '', calendario: cal.id };
  }
}

const lista = posts.map(p => {
  const d = new Date(p.timestamp);
  const interacoes = (Number(p.like_count) || 0) + (Number(p.comments_count) || 0);
  const dia = new Date(d.toLocaleString('en-US', { timeZone: fuso })).getDay();
  const hora = Number(d.toLocaleString('en-US', { timeZone: fuso, hour: '2-digit', hour12: false })) % 24;
  const cal = doCalendario[semBarra(p.permalink)] || null;
  return { id: p.id, formato: FORMATO[p.media_type] || p.media_type, curtidas: Number(p.like_count) || 0, comentarios: Number(p.comments_count) || 0,
    interacoes, engajamento: r1(interacoes / seg * 100), dia: DIAS[dia], hora, data: d.toISOString(),
    legenda: String(p.caption || '').slice(0, 140), tam_legenda: String(p.caption || '').length, link: p.permalink || '',
    imagem: p.media_type === 'VIDEO' ? (p.thumbnail_url || '') : (p.media_url || p.thumbnail_url || ''),
    calendario: cal ? cal.calendario : '', pilar: cal ? cal.pilar : '', objetivo: cal ? cal.objetivo : '' };
});
const media = arr => arr.length ? r1(arr.reduce((s, x) => s + x, 0) / arr.length) : 0;
const agrupa = (arr, chave) => {
  const g = {};
  arr.forEach(p => { if (p[chave]) (g[p[chave]] = g[p[chave]] || []).push(p.interacoes); });
  return Object.entries(g).map(([k, v]) => ({ nome: String(k), posts: v.length, media: media(v) })).sort((a, b) => b.media - a.media);
};
const porFormato = agrupa(lista, 'formato');
const porDia = DIAS.map(d => { const v = lista.filter(p => p.dia === d).map(p => p.interacoes); return { nome: d, posts: v.length, media: media(v) }; });
const faixas = [['madrugada (0h–6h)', 0, 6], ['manhã (6h–12h)', 6, 12], ['tarde (12h–18h)', 12, 18], ['noite (18h–24h)', 18, 24]];
const porHorario = faixas.map(([n, a, b]) => { const v = lista.filter(p => p.hora >= a && p.hora < b).map(p => p.interacoes); return { nome: n, posts: v.length, media: media(v) }; });

// ⏰ Hora exata campeã (só vale com 2 ou mais posts naquela hora, entre 7h e 22h)
const porHora = {};
lista.forEach(p => { (porHora[p.hora] = porHora[p.hora] || []).push(p.interacoes); });
const horaTop = Object.entries(porHora).filter(([h, v]) => v.length >= 2 && Number(h) >= 7 && Number(h) <= 22).map(([h, v]) => ({ h: Number(h), m: media(v), n: v.length })).sort((a, b) => b.m - a.m)[0];
const melhor_hora_exata = horaTop ? String(horaTop.h).padStart(2, '0') + ':00' : '';

// ✍️ Tamanho da legenda: curtas (< 300 letras) x longas
const curtas = lista.filter(p => p.tam_legenda < 300).map(p => p.interacoes), longas = lista.filter(p => p.tam_legenda >= 300).map(p => p.interacoes);
const legendas = { curtas: { posts: curtas.length, media: media(curtas) }, longas: { posts: longas.length, media: media(longas) } };

// 📅 Calendário x resto
const doCal = lista.filter(p => p.calendario), fora = lista.filter(p => !p.calendario);
const calendario = { posts: doCal.length, media_calendario: media(doCal.map(p => p.interacoes)), media_outros: media(fora.map(p => p.interacoes)),
  por_pilar: agrupa(doCal, 'pilar'), por_objetivo: agrupa(doCal, 'objetivo') };

const ult30 = lista.filter(p => Date.now() - new Date(p.data).getTime() < 30 * 86400000).length;
const top = [...lista].sort((a, b) => b.interacoes - a.interacoes).slice(0, 5);
const resumo = {
  perfil: { usuario: perfil.username, seguidores: perfil.followers_count, seguindo: perfil.follows_count, total_posts: perfil.media_count },
  posts_analisados: lista.length, posts_ultimos_30_dias: ult30,
  media_curtidas: media(lista.map(p => p.curtidas)), media_comentarios: media(lista.map(p => p.comentarios)),
  engajamento_medio_percent: media(lista.map(p => p.engajamento)),
  por_formato: porFormato, por_dia: porDia, por_horario: porHorario, melhor_hora_exata, legendas,
  posts_do_calendario_30_dias: calendario,
  top5: top.map(p => ({ formato: p.formato, interacoes: p.interacoes, dia: p.dia, hora: p.hora, legenda: p.legenda, pilar: p.pilar || undefined })),
  piores3: [...lista].sort((a, b) => a.interacoes - b.interacoes).slice(0, 3).map(p => ({ formato: p.formato, interacoes: p.interacoes, legenda: p.legenda, pilar: p.pilar || undefined })),
};
return [{ json: { dados: { perfil, lista, porFormato, porDia, porHorario, melhor_hora_exata, legendas, calendario, top, ult30, resumo, geradoEm: new Date().toISOString() },
  resumo_ia: JSON.stringify(resumo, null, 1) } }];
