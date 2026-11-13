// Monta o pedido para a IA diretora: o que a pessoa falou (com o número de cada palavra), um quadro do vídeo e os dados
// do negócio. A IA devolve o gancho do topo, os tópicos numerados (em que palavra cada um começa), a chamada do
// cartão final, a cor, a trilha e os textos do post.
const v = $('🧩 Pega o vídeo').first().json;
const ex = $('🧩 Lê a extração').first().json;
const dg = $('🎧 Deepgram: transcreve').first().json;
const VICIOS = /^(n[ée]|é+|eh+|ãh+|ah+|hum+|hm+|tipo|então|assim|uh+|ahn|aham|mm+)$/i;
const alt = (((dg.results || {}).channels || [])[0] || {}).alternatives || [];
const palavras = ((alt[0] || {}).words || []).map(w => String(w.punctuated_word || w.word));
// numeração igual à do montador (que tira os vícios antes de numerar)
const ficam = v.op.cortar_vicios ? palavras.filter(w => !VICIOS.test(w.replace(/[.,!?;:]/g, ''))) : palavras;
const numerado = ficam.map((w, i) => `[${i}]${w}`).join(' ');
const d = v.dados;
const texto = `O QUE É: ${d.tipo_txt} — ${d.titulo}
NEGÓCIO: ${d.marca || '-'} · Instagram: ${d.instagram ? '@' + d.instagram : '-'}
DETALHES DO DONO: ${d.detalhes || '-'}

FALA DO VÍDEO (cada palavra com o número dela):
${numerado || '(o vídeo não tem fala)'}

Você é EDITOR DE REELS para pequenos negócios. Com base na fala e no quadro do vídeo, devolva:
- gancho: frase curta para o topo (até 32 letras), que prende quem rola o feed; use SÓ o que foi falado/mostrado
- topicos: 2 a 4 tópicos curtos (até 22 letras) na ordem da fala, cada um com "palavra" = o número da palavra em que
  o assunto começa (use os números entre colchetes). Sem fala: lista vazia.
- cartao: chamada do cartão final (até 24 letras), ex.: "Agende sua visita", "Peça pelo direct"
- cor: cor da marca em hexadecimal que combine com o vídeo (ex.: "#C9A227")
- trilha: uma de elegante, animado, urgente, emocional, calmo, tropical, latino, chill
- legenda_post: legenda para o Instagram (até 600 letras, com 3 a 6 hashtags no fim)
REGRAS: não invente preço, número, prazo nem promessa que não foi dita. Português do Brasil com acentos.
RETORNE SOMENTE JSON: {"gancho":"","topicos":[{"palavra":0,"texto":""}],"cartao":"","cor":"#000000","trilha":"","legenda_post":""}`;
return [{ json: { corpo: JSON.stringify({ model: 'antigravity/gemini-3-flash', max_tokens: 2000, temperature: 0.5,
  messages: [{ role: 'user', content: [{ type: 'text', text: texto }, { type: 'image_url', image_url: { url: 'data:image/jpeg;base64,' + ex.b64 } }] }] }) } }];
