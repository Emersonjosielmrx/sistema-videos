// 2ª passada: revisora de fatos (IA grátis, depois da espera de 31 s). Se falhar, segue com o roteiro como estava.
__TEXTO__
const rot = $('🧠 Escreve o roteiro').first().json.ok ? $('🧠 Escreve o roteiro').first().json
  : $('🧠 Escreve o roteiro (2ª tentativa)').first().json;
const sistema = `Você é REVISORA DE FATOS de roteiros de vídeos curtos em português do Brasil.
Recebe um JSON de roteiro${rot.referencia ? ' e um TEXTO DE REFERÊNCIA' : ''}. Confira cada "fala": toda afirmação falsa,
duvidosa, sem sentido, exagerada ou com número errado deve ser TROCADA por um fato verdadeiro${rot.referencia ? ' DO TEXTO DE REFERÊNCIA' : ''}
sobre o mesmo tema, com o mesmo tamanho (8 a 22 palavras). Corrija também português e acentos.
Mantenha o gancho na 1ª fala (pergunta ou fato surpreendente verdadeiro) e o convite a seguir na última.
Se trocar uma fala, troque também a "imagem" (em inglês) dela para mostrar o novo assunto.
Mantenha o mesmo número de cenas. Devolva SOMENTE o JSON completo corrigido, no mesmo formato, sem markdown.`;
const entrada = JSON.stringify({ titulo: rot.titulo, descricao: rot.descricao, hashtags: rot.hashtags, cenas: rot.cenas });
try {
  const r = await perguntaIA(this.helpers, [{ role: 'system', content: sistema },
    { role: 'user', content: entrada + (rot.referencia ? '\n\nTEXTO DE REFERÊNCIA (' + rot.fonte + '):\n' + rot.referencia : '') }], true);
  const novas = (Array.isArray(r.cenas) ? r.cenas : []).map((c, i) => ({
    fala: String(c.fala || '').replace(/\s+/g, ' ').trim(),
    imagem: String(c.imagem || (rot.cenas[i] || {}).imagem || '').replace(/\s+/g, ' ').trim() })).filter(c => c.fala.length > 3);
  if (novas.length < Math.min(3, rot.cenas.length)) throw new Error('revisão veio incompleta');
  return [{ json: { ...rot, ok: true, revisado: true, titulo: String(r.titulo || rot.titulo).slice(0, 100),
    descricao: String(r.descricao || rot.descricao).slice(0, 900), cenas: novas.slice(0, 12) } }];
} catch (e) {
  return [{ json: { ...rot, ok: true, revisado: false, aviso_revisao: String(e.message || e).slice(0, 150) } }];
}
