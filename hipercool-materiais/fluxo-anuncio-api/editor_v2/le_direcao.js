// Lê o que a IA diretora devolveu. Se a IA falhar, segue com o básico (título no topo, sem tópicos nem destaques).
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
// emojis que existem como imagem no Google (fonts.gstatic.com/s/e/notoemoji/latest/<código>/512.png) — conferidos 01/11
const EMOJI = { '💡': '1f4a1', '☀': '2600', '⚡': '26a1', '🔋': '1f50b', '💰': '1f4b0', '💸': '1f4b8', '🏠': '1f3e0', '✅': '2705',
  '🔥': '1f525', '👉': '1f449', '📉': '1f4c9', '📈': '1f4c8', '🤝': '1f91d', '😍': '1f60d', '🚀': '1f680', '🛠': '1f6e0',
  '👷': '1f477', '📍': '1f4cd', '⭐': '2b50', '🎉': '1f389', '💪': '1f4aa', '❤': '2764', '🌱': '1f331', '🕒': '1f552',
  '📞': '1f4de', '🍔': '1f354', '🚗': '1f697', '🏡': '1f3e1', '💎': '1f48e', '👀': '1f440', '🤑': '1f911', '🆕': '1f195',
  '🔑': '1f511', '📦': '1f4e6', '🌞': '1f31e', '💯': '1f4af', '👏': '1f44f', '😎': '1f60e', '🧾': '1f9fe', '📲': '1f4f2' };
const destaques = (Array.isArray(r.destaques) ? r.destaques : [])
  .map(t => ({ palavra: parseInt(t.palavra, 10), emoji: EMOJI[String(t.emoji || '').replace(/[️‍]/g, '').trim()] || '' }))
  .filter(t => t.palavra >= 0).sort((a, b) => a.palavra - b.palavra)
  .filter((t, i, l) => i === 0 || t.palavra - l[i - 1].palavra > 2).slice(0, 6);
return [{ json: {
  ia: !!r.gancho,
  abertura: limpa(r.abertura, 44) || limpa(r.gancho, 40) || limpa(v.dados.titulo, 40),
  gancho: limpa(r.gancho, 40) || limpa(v.dados.titulo, 40),
  rosto: Array.isArray(r.rosto) && r.rosto.length === 2 && r.rosto.every(x => Number(x) >= 0 && Number(x) <= 1) &&
    Number(r.rosto[1]) - Number(r.rosto[0]) > 0.03 ? r.rosto.map(Number) : null,
  rosto_x: r.rosto_x !== null && r.rosto_x !== '' && Number(r.rosto_x) >= 0 && Number(r.rosto_x) <= 1 ? Number(r.rosto_x) : null,
  oferta: limpa(r.oferta, 40),
  servicos: limpa(r.servicos, 70),
  topicos: (Array.isArray(r.topicos) ? r.topicos : []).map(t => ({ palavra: Math.max(0, parseInt(t.palavra, 10) || 0), texto: limpa(t.texto, 26) }))
    .filter(t => t.texto).sort((a, b) => a.palavra - b.palavra).slice(0, 4),
  destaques,
  cartao: limpa(r.cartao, 28) || 'Chame no direct',
  cor: /^#[0-9a-fA-F]{6}$/.test(r.cor || '') ? String(r.cor).toUpperCase() : '',
  trilha: v.op.trilha !== 'auto' ? v.op.trilha : (TRILHAS.includes(r.trilha) ? r.trilha : 'elegante'),
  legenda_post: limpa(r.legenda_post, 2200),
} }];
