// ── Fatos de verdade, grátis e sem chave: API pública da Wikipédia em português ──
// A IA grátis inventa números e fatos; com o texto da Wikipédia no pedido ela só usa o que está lá.
async function fatosWikipedia(helpers, tema) {
  const PARE = /\b(curiosidades?|sobre|que|quase|ningu[eé]m|sabe|sabia|voc[eê]|os|as|o|a|um|uma|de|do|da|dos|das|e|em|no|na|nos|nas|para|por|com|fatos?|incr[ií]veis|segredos?|coisas?|explica[cç][aã]o|not[ií]cia|dicas?|como|porque|por que|\d+)\b/gi;
  const busca = tema.replace(PARE, ' ').replace(/[^\p{L}\p{N} -]/gu, ' ').replace(/\s+/g, ' ').trim() || tema;
  const cab = { 'User-Agent': 'n8n-fluxos-gratis/1.0 (biblioteca de fluxos sem chave)' };
  const s = await helpers.httpRequest({ json: true, timeout: 15000, headers: cab,
    url: 'https://pt.wikipedia.org/w/api.php?action=query&list=search&format=json&srlimit=1&srsearch=' + encodeURIComponent(busca) });
  const titulo = (((s || {}).query || {}).search || []).map(x => x.title)[0];
  if (!titulo) return { fonte: '', texto: '' };
  const e = await helpers.httpRequest({ json: true, timeout: 15000, headers: cab,
    url: 'https://pt.wikipedia.org/w/api.php?action=query&prop=extracts&explaintext=1&exsectionformat=plain&format=json&exchars=3500&titles=' +
      encodeURIComponent(titulo) });
  const pag = Object.values(((e || {}).query || {}).pages || {})[0] || {};
  const texto = String(pag.extract || '').replace(/\n{2,}/g, '\n').trim().slice(0, 3500);
  return { fonte: texto ? 'Wikipédia: ' + titulo : '', texto };
}
