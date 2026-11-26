function parseJSON(txt) {
  const s = String(txt || '').replace(/^\s*```(?:json)?\s*/i, '').replace(/```\s*$/i, '').trim();
  try { return JSON.parse(s); } catch (e) {}
  const a = s.indexOf('{'), b = s.lastIndexOf('}');
  if (a > -1 && b > a) { try { return JSON.parse(s.slice(a, b + 1)); } catch (e) {} }
  return null;
}

// 🧩 Junta números + análise da IA. Sai em 2 formatos:
//  • relatorio   = tudo, para a página (fica 6 h)
//  • diagnostico = só o que o fluxo "30 Dias de Posts" precisa para planejar o mês (fica 30 dias em ig:diagnostico)
const dados = $('Calcula métricas do perfil').first().json.dados;
const ia = parseJSON($input.first().json.output ?? '');
const txt = (s, max) => String(s ?? '').replace(/[<>]/g, '').trim().slice(0, max);
const lista = (arr, n, max) => (Array.isArray(arr) ? arr : []).map(x => txt(x, max)).filter(Boolean).slice(0, n);

// 🎞️ Mistura de formatos para 30 dias: a da IA; se faltar, calcula pelos números (formato que rende mais ganha mais dias)
const MAPA = { 'Foto': 'post', 'Carrossel': 'carrossel', 'Vídeo / Reels': 'reels' };
function normaliza(m) {
  const k = ['carrossel', 'post', 'reels'];
  const v = k.map(f => Math.max(4, Math.round(Number(m && m[f]) || 0)));
  let soma = v.reduce((a, b) => a + b, 0);
  if (soma <= 12) return { carrossel: 12, post: 10, reels: 8 };
  // nenhum formato passa de 16 dias (reels são só roteiro: o dono grava; o mês não pode virar só reels)
  const r = v.map(x => Math.min(16, Math.max(4, Math.round(x * 30 / soma))));
  let dif = 30 - r.reduce((a, b) => a + b, 0);
  const ordem = [0, 1, 2].sort((a, b) => r[b] - r[a]);
  for (let i = 0; dif !== 0 && i < 90; i++) { const j = ordem[i % 3]; if (dif > 0 && r[j] < 16) { r[j]++; dif--; } else if (dif < 0 && r[j] > 4) { r[j]--; dif++; } }
  return { carrossel: r[0], post: r[1], reels: r[2] };
}
let mix = ia && ia.mix_formatos ? normaliza(ia.mix_formatos) : null;
if (!mix) {
  const base = { carrossel: 12, post: 10, reels: 8 };
  const validos = (dados.porFormato || []).filter(f => f.posts >= 2 && MAPA[f.nome]);
  const geral = validos.length ? validos.reduce((s, f) => s + f.media, 0) / validos.length : 0;
  const m = { ...base };
  if (geral > 0) validos.forEach(f => { m[MAPA[f.nome]] = base[MAPA[f.nome]] * Math.max(0.5, Math.min(1.8, f.media / geral)); });
  mix = normaliza(m);
}
const hora = /^\d{2}:\d{2}$/.test(String(ia && ia.hora_sugerida || '')) ? ia.hora_sugerida : (dados.melhor_hora_exata || '');

const diagnostico = {
  versao: 1, geradoEm: dados.geradoEm, usuario: String(dados.perfil.username || '').toLowerCase(),
  seguidores: Number(dados.perfil.followers_count) || 0, posts_analisados: (dados.lista || []).length,
  engajamento_medio_percent: dados.resumo.engajamento_medio_percent, posts_ultimos_30_dias: dados.ult30,
  ia_ok: !!ia, nota_saude: ia ? Number(ia.nota_saude) || 0 : null, resumo: ia ? txt(ia.resumo, 400) : '',
  o_que_funciona: lista(ia && ia.o_que_funciona, 5, 200), o_que_melhorar: lista(ia && ia.o_que_melhorar, 5, 200),
  pilares_que_funcionam: lista(ia && ia.pilares_que_funcionam, 5, 60), evitar: lista(ia && ia.evitar, 5, 160),
  regras_para_legenda: lista(ia && ia.regras_para_legenda, 6, 200),
  ideias: (Array.isArray(ia && ia.ideias) ? ia.ideias : []).slice(0, 6).map(i => ({ formato: txt(i.formato, 20), titulo: txt(i.titulo, 100), gancho: txt(i.gancho, 160) })),
  melhor_dia: txt(ia && ia.melhor_dia, 60), melhor_horario: txt(ia && ia.melhor_horario, 60), frequencia: txt(ia && ia.frequencia_recomendada, 80),
  mix_formatos: mix, hora_sugerida: hora,
  numeros: { por_formato: dados.porFormato, por_horario: dados.porHorario, legendas: dados.legendas, calendario: dados.calendario,
    top5: (dados.top || []).map(p => ({ formato: p.formato, interacoes: p.interacoes, legenda: p.legenda })) },
};
return [{ json: { relatorio: JSON.stringify({ ...dados, ia: ia || null, plano: { mix_formatos: mix, hora_sugerida: hora } }), diagnostico: JSON.stringify(diagnostico) } }];
