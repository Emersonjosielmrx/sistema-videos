// Escreve o roteiro com a IA grátis (Pollinations). Uma chamada só: o limite sem chave é 1 resposta a cada 30 s.
// Curiosidades, notícia e dicas vêm ancoradas no texto da Wikipédia (a IA grátis inventa fatos sem isso).
__TEXTO__
__WIKI__
const v = $('🧩 Confere o pedido').first().json;
const nCenas = Math.max(5, Math.min(10, Math.round(v.duracao / 6)));
const palavras = Math.round(v.duracao * 2.5);
let ref = { fonte: '', texto: '' };
if (['curiosidades', 'noticia', 'dicas'].includes(v.tipo)) {
  try { ref = await fatosWikipedia(this.helpers, v.tema); } catch (e) { ref = { fonte: '', texto: '' }; }
}
const sistema = `Você é roteirista de vídeos curtos em português do Brasil para YouTube Shorts, Reels e TikTok.
Responda SOMENTE um JSON válido, sem markdown, neste formato:
{"titulo":"","descricao":"","hashtags":["#..."],"cenas":[{"fala":"","imagem":""}]}
Regras:
- Exatamente ${nCenas} cenas. A 1ª fala é o GANCHO: prende nos primeiros 3 segundos (pergunta ou fato surpreendente VERDADEIRO).
- "fala": o que o narrador diz na cena, 8 a 22 palavras, frase natural para ouvir, com acentos, sem emojis, sem listas,
  sem parênteses. Somando todas as falas, cerca de ${palavras} palavras. A última fala fecha a ideia e convida a seguir para
  mais vídeos, sem citar nome de canal.
- "imagem": descrição EM INGLÊS da imagem da cena (máx. 45 palavras), mostrando exatamente o assunto da fala, composição
  ${v.formato === '9:16' ? 'vertical (portrait)' : 'horizontal (landscape)'}, estilo: ${v.estilo_img}. Sem texto, letras,
  números escritos, logotipos ou marcas d'água na imagem. Sem pessoas famosas reais. Mesmos personagens com a mesma aparência
  em todas as cenas quando houver personagem. A imagem da última cena também mostra o assunto do vídeo (nada de pessoa
  posando, colagem ou grade de fotos).
- ${ref.texto ? 'Use SOMENTE fatos que estão no TEXTO DE REFERÊNCIA. Não invente números nem fatos fora dele.'
    : 'Fatos verdadeiros e conferíveis. Se não tiver certeza de um número, não use número.'}
- Nada de frase sem sentido ou exagero falso.
- "titulo": até 90 caracteres, 2 a 4 palavras-chave em MAIÚSCULAS, no máximo 1 emoji, desperta curiosidade, sem "#shorts".
- "descricao": 2 ou 3 frases sobre o vídeo e uma pergunta para o público comentar.
- "hashtags": 3 a 6 hashtags específicas do assunto (nada genérico como #shorts #viral #ia #fyp).`;
const pedido = `Tema: ${v.tema}\nTipo: ${v.tipo_txt}\nDuração alvo: ${v.duracao} segundos.` +
  (ref.texto ? `\n\nTEXTO DE REFERÊNCIA (${ref.fonte}):\n${ref.texto}` : '');
try {
  const r = await perguntaIA(this.helpers, [{ role: 'system', content: sistema }, { role: 'user', content: pedido }], true);
  const cenas = (Array.isArray(r.cenas) ? r.cenas : [])
    .map(c => ({ fala: String(c.fala || '').replace(/\s+/g, ' ').trim(), imagem: String(c.imagem || '').replace(/\s+/g, ' ').trim() }))
    .filter(c => c.fala.length > 3);
  if (cenas.length < 3) throw new Error('roteiro veio com poucas cenas');
  for (const c of cenas) if (!c.imagem) c.imagem = v.tema + ', ' + v.estilo_img;
  return [{ json: { ok: true, titulo: String(r.titulo || v.tema).slice(0, 100), descricao: String(r.descricao || '').slice(0, 900),
    hashtags: limpaHashtags(r.hashtags), cenas: cenas.slice(0, 12), fonte: ref.fonte, referencia: ref.texto } }];
} catch (e) {
  return [{ json: { ok: false, erro: String(e.message || e).slice(0, 250), fonte: ref.fonte, referencia: ref.texto } }];
}

function limpaHashtags(h) {
  return (Array.isArray(h) ? h : String(h || '').split(/\s+/))
    .map(t => '#' + String(t).replace(/^#+/, '').replace(/[^\p{L}\p{N}_]/gu, '')).filter(t => t.length > 2)
    .filter(t => !/^#(shorts|viral|ia|fyp|foryou|parati)$/i.test(t)).slice(0, 6);
}
