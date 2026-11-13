// Monta o pedido para a IA diretora: o que a pessoa falou (com o número de cada palavra), um quadro do vídeo e os dados
// do negócio. A IA devolve a frase de abertura, o gancho do topo, os tópicos numerados (em que palavra cada um começa),
// as PALAVRAS-CHAVE (destacadas na legenda, com som e emoji), a chamada do cartão final, a cor, a trilha e o post.
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
const EMOJIS = '💡 ☀ ⚡ 🔋 💰 💸 🏠 ✅ 🔥 👉 📉 📈 🤝 😍 🚀 🛠 👷 📍 ⭐ 🎉 💪 ❤ 🌱 🕒 📞 🍔 🚗 🏡 💎 👀 🤑 🆕 🔑 📦 🌞 💯 👏 😎 🧾 📲';
const texto = `O QUE É: ${d.tipo_txt} — ${d.titulo}
NEGÓCIO: ${d.marca || '-'} · Instagram: ${d.instagram ? '@' + d.instagram : '-'}
DETALHES DO DONO: ${d.detalhes || '-'}

FALA DO VÍDEO (cada palavra com o número dela):
${numerado || '(o vídeo não tem fala)'}

Você é EDITOR DE REELS para pequenos negócios (estilo dos melhores criadores do Instagram). Com base na fala e no
quadro do vídeo, devolva:
- abertura: frase forte que aparece GRANDE no meio da tela nos 2 primeiros segundos (até 34 letras), curiosidade ou
  benefício; pode ser a PERGUNTA que o público costuma fazer (termine com "?"); use SÓ o que foi falado/mostrado
- rosto: onde está o ROSTO da pessoa principal no quadro, como [topo, base] em fração da ALTURA da imagem (0 = topo,
  1 = base; ex.: [0.18, 0.36]); null se não houver rosto
- rosto_x: onde está o CENTRO do rosto na LARGURA da imagem (0 = esquerda, 1 = direita; ex.: 0.62); null se não houver
- oferta: frase curta para o cartão final (até 34 letras) com o que a empresa oferece, tirada da fala ou dos detalhes
- servicos: até 3 serviços/produtos curtos separados por " • " (só os que aparecem na fala ou nos detalhes)
- gancho: frase curta que fica fixa no topo (até 30 letras)
- topicos: 2 a 4 tópicos curtos (até 22 letras) na ordem da fala, cada um com "palavra" = o número da palavra em que
  o assunto começa (use os números entre colchetes). Sem fala: lista vazia.
- destaques: 3 a 6 PALAVRAS-CHAVE da fala (benefício, número, lugar, produto, resultado), cada uma com "palavra" = o
  número dela e "emoji" = UM destes: ${EMOJIS}. Espalhe ao longo do vídeo (não duas seguidas).
- cartao: chamada do cartão final (até 24 letras), ex.: "Agende sua visita", "Peça pelo direct"
- cor: cor da marca em hexadecimal que combine com o vídeo (ex.: "#C9A227")
- trilha: uma de elegante, animado, urgente, emocional, calmo, tropical, latino, chill
- legenda_post: legenda para o Instagram (até 600 letras, com 3 a 6 hashtags no fim)
REGRAS: não invente preço, número, prazo nem promessa que não foi dita. Português do Brasil com acentos.
RETORNE SOMENTE JSON: {"rosto":[0,0],"rosto_x":0.5,"abertura":"","oferta":"","servicos":"","gancho":"","topicos":[{"palavra":0,"texto":""}],"destaques":[{"palavra":0,"emoji":""}],"cartao":"","cor":"#000000","trilha":"","legenda_post":""}`;
return [{ json: { corpo: JSON.stringify({ model: 'antigravity/gemini-3-flash', max_tokens: 2500, temperature: 0.5,
  messages: [{ role: 'user', content: [{ type: 'text', text: texto }, { type: 'image_url', image_url: { url: 'data:image/jpeg;base64,' + ex.b64 } }] }] }) } }];
