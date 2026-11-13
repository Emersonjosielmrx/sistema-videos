// Lê o que a IA diretora devolveu. Se a IA falhar, segue com o básico (título no topo, sem tópicos).
function parseJSON(txt) {
  const s = String(txt || '').replace(/^\s*```(?:json)?\s*/i, '').replace(/```\s*$/i, '').trim();
  try { return JSON.parse(s); } catch (e) {}
  const a = s.indexOf('{'), b = s.lastIndexOf('}');
  if (a > -1 && b > a) { try { return JSON.parse(s.slice(a, b + 1)); } catch (e) {} }
  return null;
}
const v = $('🧩 Pega o vídeo').first().json;
let r = null;
try { const x = $input.first().json; r = parseJSON(x.choices ? x.choices[0].message.content : ''); } catch (e) {}
r = r || {};
const limpa = (s, m) => String(s || '').replace(/[<>{}\\]/g, '').trim().slice(0, m);
const TRILHAS = ['elegante', 'animado', 'urgente', 'emocional', 'calmo', 'tropical', 'latino', 'chill'];
return [{ json: {
  ia: !!r.gancho,
  gancho: limpa(r.gancho, 40) || limpa(v.dados.titulo, 40),
  topicos: (Array.isArray(r.topicos) ? r.topicos : []).map(t => ({ palavra: Math.max(0, parseInt(t.palavra, 10) || 0), texto: limpa(t.texto, 26) }))
    .filter(t => t.texto).sort((a, b) => a.palavra - b.palavra).slice(0, 4),
  cartao: limpa(r.cartao, 28) || 'Chame no direct',
  cor: /^#[0-9a-fA-F]{6}$/.test(r.cor || '') ? String(r.cor).toUpperCase() : '',
  trilha: v.op.trilha !== 'auto' ? v.op.trilha : (TRILHAS.includes(r.trilha) ? r.trilha : 'elegante'),
  legenda_post: limpa(r.legenda_post, 2200),
} }];
