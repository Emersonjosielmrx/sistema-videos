function parseJSON(txt) {
  const s = String(txt || '').replace(/^\s*```(?:json)?\s*/i, '').replace(/```\s*$/i, '').trim();
  try { return JSON.parse(s); } catch (e) {}
  const a = s.indexOf('{'), b = s.lastIndexOf('}');
  if (a > -1 && b > a) { try { return JSON.parse(s.slice(a, b + 1)); } catch (e) {} }
  return null;
}

// Transforma o plano da IA em 30 dias com data. Se a IA falhar, monta um plano padrão (para não travar).
// Com diagnóstico: guarda o resumo no calendário (a página mostra), usa o melhor horário e a mistura de formatos dele.
const v = $('🧩 Confere o pedido').first().json;
const dg = $('🧩 Prepara o diagnóstico').first().json;
const cal = JSON.parse(v.cal);
let ia = null;
try { ia = parseJSON($('🤖 Estrategista').first().json.output); } catch (e) {}
const FORMATOS = ['post', 'carrossel', 'reels'];
const txt = (s, max) => String(s ?? '').replace(/[<>]/g, '').trim().slice(0, max);
let dias = Array.isArray(ia && ia.dias) ? ia.dias : [];
// plano padrão: segue a mistura do diagnóstico se tiver (ex.: mais reels quando reels rende mais)
let padrao = ['carrossel', 'post', 'reels', 'carrossel', 'post', 'carrossel', 'reels'];
if (dg.usado && dg.resumo && dg.resumo.mix_formatos) {
  const m = { ...dg.resumo.mix_formatos }, seq = [];
  for (let i = 0; i < 30; i++) {
    const opc = FORMATOS.filter(f => m[f] > 0 && !(seq.length >= 2 && seq[seq.length - 1] === f && seq[seq.length - 2] === f));
    const f = (opc.length ? opc : FORMATOS.filter(f => m[f] > 0)).sort((a, b) => m[b] - m[a])[0] || 'post';
    seq.push(f); m[f]--;
  }
  padrao = seq;
}
const pilares = (Array.isArray(ia && ia.pilares) ? ia.pilares : []).map(p => txt(p, 30)).filter(Boolean).slice(0, 5);
if (!pilares.length) pilares.push('Dicas', 'Bastidores', 'Produtos', 'Clientes', 'Ofertas');
const dataDe = n => { const d = new Date(cal.inicio + 'T12:00:00Z'); d.setUTCDate(d.getUTCDate() + n); return d.toISOString().slice(0, 10); };
cal.dias = Array.from({ length: 30 }, (_, i) => {
  const d = dias.find(x => Number(x.dia) === i + 1) || dias[i] || {};
  return {
    dia: i + 1, data: dataDe(i), formato: FORMATOS.includes(d.formato) ? d.formato : padrao[i % padrao.length],
    pilar: txt(d.pilar, 30) || pilares[i % pilares.length], tema: txt(d.tema, 140) || `${pilares[i % pilares.length]} da ${cal.negocio.nome}`,
    objetivo: txt(d.objetivo, 20) || 'engajar', motivo: txt(d.motivo, 160), titulo: '', subtitulo: '', slides: [], roteiro: [], legenda: '', hashtags: [],
    estado: 'planejado', v: 1, link: '', erro: '',
  };
});
// 🔀 Nunca 3 formatos iguais seguidos: troca o dia inteiro (formato + tema) com o próximo de formato diferente
const CAMPOS = ['formato', 'pilar', 'tema', 'objetivo', 'motivo'];
for (let i = 2; i < cal.dias.length; i++) {
  const f = cal.dias[i].formato;
  if (f !== cal.dias[i - 1].formato || f !== cal.dias[i - 2].formato) continue;
  const j = cal.dias.findIndex((x, k) => k > i && x.formato !== f);
  if (j < 0) break;
  for (const c of CAMPOS) [cal.dias[i][c], cal.dias[j][c]] = [cal.dias[j][c], cal.dias[i][c]];
}
cal.pilares = pilares;
cal.plano_ia = !!(ia && Array.isArray(ia.dias) && ia.dias.length >= 20);
// 🔎 Diagnóstico
if (dg.usado) {
  cal.diagnostico = dg.resumo;
  if (v.hora_diag && /^\d{2}:\d{2}$/.test(dg.resumo.hora_sugerida || '')) { cal.hora_pedida = cal.hora; cal.hora = dg.resumo.hora_sugerida; }
} else if (v.usar_diag) {
  cal.diagnostico = { status: 'sem', aviso: dg.aviso || 'Não deu para ler o diagnóstico; o mês foi planejado só com os dados do negócio.' };
} else {
  cal.diagnostico = null;
}
cal.status = 'escrevendo';
// 5 lotes de 6 dias: a IA redatora escreve um lote por vez e o calendário vai enchendo na tela
const lotes = [0, 1, 2, 3, 4].map(l => ({ json: { lote: l + 1, dias: cal.dias.slice(l * 6, l * 6 + 6).map(d => ({ dia: d.dia, data: d.data, formato: d.formato, pilar: d.pilar, tema: d.tema, objetivo: d.objetivo, motivo: d.motivo })) } }));
return [{ json: { id: cal.id, cal: JSON.stringify(cal), lotes } }];
