# Quadro de ideias - formatos que nos mesmos podemos produzir

Gerado automaticamente pelo vigia de formatos a partir dos videos reagidos. 67 replicaveis, 24 nao replicaveis.

## Replicaveis (ordenado por potencial)

### tour visual de produto/invenção com música ambiente  -  potencial 9/10, esforco baixo  -  canal: inventoreact

- **Visto em:** 2026-10-01 10-58-04.mp4 (2026-10-01)
- **O que e:** Vídeo mostra produto inovador (motorhome solar) em planos cinematográficos externos e internos, revelando funcionalidades progressivamente. Sem narração, só música de fundo e cortes dinâmicos que prendem pela descoberta visual.
- **Por que viraliza:** Desperta curiosidade pelo reveal progressivo e desejo aspiracional por produtos inovadores que resolvem problemas de forma elegante.
- **Como fazer:** 1) Coletar 8-12 imagens/vídeos de alta qualidade do produto (Pexels, Unsplash, geração IA via Veo 3 para produtos fictícios/futuristas). 2) Criar roteiro de 'descoberta progressiva': externa → funcionalidade 1 → funcionalidade 2 → detalhe surpresa. 3) Montar no ffmpeg com cortes de 2-3s por plano, zoom suave (ken burns) e transições rápidas. 4) Adicionar trilha instrumental épica/tech das 341 disponíveis. 5) Inserir legendas estilo Hormozi apontando cada funcionalidade ('PAINEL SOLAR ☀️', 'TETO RETRÁTIL 🌧️'). 6) Finalizar com SFX de transição e overlay de confete/raio nos momentos de reveal.
- **Ferramentas:** ffmpeg, geração de vídeo IA (Veo 3), Pollinations/Gemini (imagens), overlays animados, trilhas de música, SFX
- **Material:** Pexels/Unsplash para produtos reais; Veo 3 + Gemini para gerar produtos futuristas/inventos fictícios (ex: 'casa flutuante movida a energia solar', 'mochila que vira barraca'); Playwright para capturar sites de gadgets/Kickstarter
- **Exemplo de roteiro:**

```
FRAME 1: Motorhome amarelo comum na rua [legenda: 'PARECE NORMAL... 🤔'] → FRAME 2: Teto abre mostrando painéis solares [legenda: 'MAS TEM ISSO 😱☀️'] → FRAME 3: Interior com cama suspensa [legenda: 'CAMA RETRÁTIL 🛏️'] → FRAME 4: Banheiro compacto [legenda: 'ATÉ BANHEIRO COMPLETO 🚿'] → FRAME 5: Pessoa relaxando no teto aberto [legenda: 'LIBERDADE TOTAL 🌍✨']
```

- Tags: motorhome, energia_solar, vida_nomade, invencoes, minimalismo, tecnologia

### recap de cena de anime com legendas dramaticas sincronizadas  -  potencial 9/10, esforco baixo  -  canal: cenareact

- **Visto em:** 2026-10-01 11-23-15.mp4 (2026-10-01)
- **O que e:** Sequencia de frames de anime (4-6 cenas) com legendas curtas e impactantes sincronizadas com momentos-chave da cena, criando tensao narrativa. Sem narracao, so musica de fundo tensa.
- **Por que viraliza:** Suspense construido frame a frame + legendas que forcam o cerebro a completar a historia = loop de retencao ate o final + comentarios pedindo contexto
- **Como fazer:** 1) Extrair 4-6 frames de uma cena importante de anime (seu pipeline de recap ou capturas manuais); 2) Escrever legendas curtas e dramaticas para cada frame (ex: 'ROY', 'ACONTECENDO', 'NAO ERA', 'O HEROI'); 3) Montar no ffmpeg com transicoes rapidas (0.8-1.2s por frame) e fade entre frames; 4) Adicionar trilha tensa/epica da biblioteca (buildup); 5) Sobrepor legendas animadas estilo Hormozi (bold, branco com stroke preto, entrada com zoom); 6) Finalizar com gancho 'parte 2?' ou 'quer o contexto?'
- **Ferramentas:** ffmpeg, pipeline de recap de anime, overlays animados, trilhas de musica
- **Material:** frames extraidos de episodios de anime via pipeline de recap existente, ou capturas manuais de cenas virais/importantes
- **Exemplo de roteiro:**

```
Frame 1: [Subaru close, expressao chocada] - 'ELE PERCEBEU'
Frame 2: [Subaru e Ram lado a lado] - 'QUE ALGO ESTAVA ERRADO'
Frame 3: [Subaru olhos fechados] - 'MAS JA ERA TARDE'
Frame 4: [Luz brilhante envolvendo] - 'O TRANSPORTE COMECOU'
Frame 5: [tela branca] - 'E ELA ESQUECEU TUDO'
```

- Tags: rezero, anime recap, cena epica, subaru, plot twist, suspense

### recap de cena de anime com legendas palavra-chave sincronizadas  -  potencial 9/10, esforco baixo  -  canal: cenareact

- **Visto em:** 2026-10-01 11-35-45.mp4 (2026-10-01)
- **O que e:** Narração contando uma cena específica de anime (luta, momento emocional) com frames do episódio + legendas destacando palavras-chave em cada corte. Ritmo rápido, foco na reviravolta da cena.
- **Por que viraliza:** Nostalgia + spoiler controlado: quem viu relembra e comenta, quem não viu quer assistir o episódio completo.
- **Como fazer:** 1) Escolher cena marcante de anime popular (Re:Zero, JJK, Demon Slayer); 2) Extrair 4-6 frames-chave da cena via Playwright ou prints manuais; 3) Escrever roteiro de 30-50s narrando a cena com LLM (foco em reviravolta/momento épico); 4) Gerar áudio TTS (ElevenLabs ou Gemini TTS com voz dramática); 5) Sincronizar frames com ffmpeg, adicionando legendas palavra-chave (substantivos/verbos de ação) com timing preciso via overlays animados; 6) Adicionar trilha épica de fundo + SFX nos momentos de impacto.
- **Ferramentas:** ffmpeg, TTS, Playwright, overlays animados, trilhas de música, SFX
- **Material:** Screenshots de episódios de anime (uso educacional/comentário), prints via Playwright de streaming legal, ou painéis de manhwa adaptados
- **Exemplo de roteiro:**

```
O dragão Volcânica confunde Emilia com outra pessoa. [FRAME: Emilia séria] Ela corta na hora: 'Meu nome é EMILIA'. [FRAME: dragão atacando] Mas ele não aceita e parte pra luta. [FRAME: escama diferente] Emilia percebe UMA escama com cor diferente. [FRAME: magia de gelo] Ela lembra do PEKKA e concentra TODO o ataque de gelo naquele ponto. [FRAME: dragão voltando ao normal] FUNCIONOU.
```

- Tags: rezero, emilia, anime recap, cena épica, volcânica, shorts anime

### jogo de adivinhação interativo com pausas  -  potencial 9/10, esforco baixo  -  canal: manhwareact

- **Visto em:** 2026-10-01 16-15-50.mp4 (2026-10-01)
- **O que e:** Uma IA/personagem faz perguntas progressivas para adivinhar em quem você está pensando, com pausas para o espectador responder mentalmente. Ritmo de pergunta-pausa-resposta cria engajamento ativo.
- **Por que viraliza:** Engajamento ativo força o espectador a jogar mentalmente, criar apego à resposta dele e assistir até o fim pra ver se a IA acerta
- **Como fazer:** 1) Criar avatar IA (imagem gerada ou robô/personagem animado com overlays); 2) Escrever roteiro de 8-12 perguntas progressivas (começa genérico, afunila para resposta específica); 3) Gerar narração TTS com pausas de 2-3s após cada pergunta; 4) Montar no ffmpeg com texto animado das perguntas + avatar + música de suspense; 5) Revelar resposta no final com SFX de acerto
- **Ferramentas:** TTS, ffmpeg, geração de imagem IA, overlays animados, SFX, trilhas de música
- **Material:** Avatar gerado por IA (Gemini/Pollinations), perguntas escritas por LLM baseadas em categorias (personagens, países, objetos, filmes), overlays de texto animado
- **Exemplo de roteiro:**

```
Pense em um personagem de anime. Pronto? [pausa] Ele tem cabelo espetado? [pausa] Ele usa energia amarela? [pausa] Ele é um Sayajin? [pausa] Você pensou no GOKU! Acertei?
```

- Tags: jogo de adivinhação, interativo, personagens, IA, desafio mental, teste

### Animação de história cômica com narração dramatizada  -  potencial 9/10, esforco medio  -  canal: novo canal: RelatosBR

- **Visto em:** 2026-10-01 16-20-54.mp4 (2026-10-01)
- **O que e:** Vídeo animado estilo storytime contando situação cômica do dia-a-dia (marido fingindo que PlayStation é roteador). Narração dublada com múltiplas vozes, legendas dinâmicas, cortes rápidos nos momentos-chave e punchline no final.
- **Por que viraliza:** Identificação massiva com situações absurdas de relacionamento + punchline inesperada que gera compartilhamento ('manda pro crush', 'todo marido gamer').
- **Como fazer:** 1) Roteirizar história cômica viral (Reddit, Twitter, fóruns brasileiros) com setup + reviravolta. 2) Gerar frames da animação com IA (Gemini/Pollinations) - personagens simples, estilo cartoon/webtoon. 3) Dublar diálogo com TTS (ElevenLabs com vozes diferentes para cada personagem, ajustar tom para drama/comédia). 4) Editar no ffmpeg: cortar nos beats da piada, adicionar zoom dramático, som de tensão (SFX de suspense) antes da revelação, efeito de 'erro fatal' no final. 5) Legendas word-by-word estilo Hormozi nos momentos de punchline. 6) Trilha de fundo neutra que cresce no clímax.
- **Ferramentas:** Gemini/Pollinations, ElevenLabs TTS, ffmpeg, SFX, overlays de legenda
- **Material:** Histórias virais do Reddit (r/tifu, r/relationshipadvice), Twitter BR, fóruns de games, posts de Facebook/Instagram de confissões. Gerar frames de animação com prompts detalhados para IA.
- **Exemplo de roteiro:**

```
[Frame: esposa desconfiada] ESPOSA: 'O que é isso?' [zoom dramático] MARIDO: 'É o roteador novo, amor... Play Speed' [SFX de suor] ESPOSA: 'Play? Tipo... PlayStation?' [Frame: marido suando] MARIDO: 'Não não, é... Play... Fort?' [Frame: esposa percebendo] NARRADOR: 'Nesse momento, ele soube... que tinha acabado.' [SFX de game over]
```

- Tags: storytime, relacionamento, humor brasileiro, animação, marido gamer, viral

### notícia tech com legendas dinâmicas + fotos de produto  -  potencial 9/10, esforco baixo  -  canal: inventoreact

- **Visto em:** 2026-10-01 16-40-55.mp4 (2026-10-01)
- **O que e:** Explica uma notícia técnica (hardware, software, ciência) usando narração objetiva + legendas amarelas em palavras-chave + fotos/vídeos do produto em questão. Ritmo rápido, informativo, sem enrolação.
- **Por que viraliza:** Nostalgia + informação exclusiva + promessa de 'anota aí, vai ser importante' gera FOMO e autoridade
- **Como fazer:** 1. Escolher notícia tech recente (Reddit r/emulation, Hacker News, fóruns BR de tech). 2. Gerar roteiro informativo com LLM (Gemini) focado em impacto prático. 3. Narrar com TTS (ElevenLabs voz masculina confiante ou edge-tts pt-BR). 4. Buscar fotos do produto (Pexels, Unsplash, Wikipedia, geração IA se não existir foto boa). 5. Editar no ffmpeg: fotos em zoom lento + legendas amarelas estilo Hormozi nas palavras-chave + transições rápidas. 6. Adicionar trilha de suspense/tech (das 341 disponíveis) + SFX de 'whoosh' nas transições.
- **Ferramentas:** LLM, TTS, ffmpeg, Pexels/Unsplash, overlays animados
- **Material:** Notícias de Reddit (r/emulation, r/technology, r/brasil tech), fóruns (GBAtemp, ResetEra), sites tech BR (Adrenaline, Tecnoblog), fotos de produtos via Pexels/Unsplash ou geração IA
- **Exemplo de roteiro:**

```
Em setembro de 2026, hackers quebraram a criptografia do chip Mechacon do PS2. [FOTO: PS2 fat] Esse chip era o porteiro do console: checava se o disco era original, controlava trava de região. [FOTO: chip closeup] Agora? Mods modernos vão permitir SSD interno direto, sem depender de USB lento ou gambiarra de memory card. [FOTO: SSD] Salva esse vídeo. Daqui 2 anos você vai lembrar que eu avisei.
```

- Tags: PS2, tech, nostalgia, modding, hardware, mechacom

### paródia animada de anime com situação brasileira  -  potencial 9/10, esforco medio  -  canal: cenareact

- **Visto em:** 2026-10-01 16-49-02.mp4 (2026-10-01)
- **O que e:** Personagem de anime enfrenta problema cotidiano brasileiro (Receita Federal, taxas) em formato de animação caseira com diálogos dublados. Estrutura: setup → confronto → punchline absurda.
- **Por que viraliza:** Combina nostalgia de anime clássico com humor de raiva coletiva sobre burocracia brasileira - identificação instantânea + compartilhamento por revolta
- **Como fazer:** 1) Gerar frames estilo anime com IA (Gemini/Pollinations) - personagem principal + antagonista 'burocrata'. 2) Criar roteiro de paródia com situação brasileira viral (INSS, Detran, imposto). 3) Gerar vozes com TTS pt-br (edge-tts com vozes diferentes por personagem). 4) Adicionar legendas hardcoded estilo meme. 5) Inserir SFX de anime (explosão, whoosh) + trilha épica. 6) Montar no ffmpeg: frame → legenda → áudio → transição rápida.
- **Ferramentas:** Gemini/Pollinations, TTS edge-tts, ffmpeg, SFX anime, trilhas épicas
- **Material:** Geração de imagem IA para personagens estilo anime + fotos reais de contexto brasileiro (favela, Correios, filas) via domínio público/Pexels
- **Exemplo de roteiro:**

```
GOKU: 'Vim buscar minha encomenda dos EUA!'
ATENDENTE CORREIOS: 'Taxa de importação: R$ 500'
GOKU: 'QUE TAXA? NINGUÉM TAXA O SAYAJIN!'
[SFX: charge de ki]
ATENDENTE: 'Kamehameha não paga Receita Federal, não.'
[GOKU desiste e vai embora derrotado]
```

- Tags: anime brasileiro, goku receita federal, paródia dragon ball, meme anime, burocracia brasil, animação caseira

### edit rápido de anime com legendas provocativas  -  potencial 9/10, esforco baixo  -  canal: cenareact

- **Visto em:** 2026-10-01 17-47-36.mp4 (2026-10-02)
- **O que e:** Cortes rápidos de cenas de anime com legendas amarelas em português destacando falas/momentos provocativos ou engraçados, sem narração, só música de fundo. Ritmo acelerado, cada frame dura 1-2 segundos.
- **Por que viraliza:** Mistura nostalgia de anime + humor absurdo + legendas que criam narrativas inesperadas sobre personagens conhecidos
- **Como fazer:** 1) Extrair frames-chave de episódios de anime (Slime, outros isekai populares) via ffmpeg; 2) Criar legendas curtas e impactantes em português (TTS não necessário, só texto); 3) Aplicar overlay de texto amarelo estilo meme com bordas pretas via ffmpeg; 4) Adicionar trilha sonora viral (phonk, trap japonês); 5) Montar sequência de 3-5 frames com transições rápidas (0.8-1.5s cada); 6) Exportar em 9:16 com 15-30s totais.
- **Ferramentas:** ffmpeg, overlays animados, trilhas de musica, pipeline de recap de anime
- **Material:** episódios de anime disponíveis (Crunchyroll, torrents), frames extraídos do pipeline de recap, screenshots de cenas icônicas
- **Exemplo de roteiro:**

```
Frame 1: Shuna olhando Rimuru - legenda 'É'
Frame 2: Rimuru forma de slime - legenda 'EXISTE'
Frame 3: Close em peitos de personagem com glitch - legenda 'SOBREVIVA'
Frame 4: Shion sorrindo segurando Rimuru - legenda 'É'
Música: phonk agressivo com bass boost
```

- Tags: slime, anime edit, rimuru, isekai, react anime, tensei slime

### clipe viral legendado + narração IA reagindo  -  potencial 9/10, esforco baixo  -  canal: novo canal: ViralizouReact

- **Visto em:** 2026-10-01 17-49-09.mp4 (2026-10-02)
- **O que e:** Pega um clipe viral/polêmico (YouTube, TV, entrevista), corta as frases de impacto, adiciona legendas estilo meme com timing perfeito e narração IA comentando/reagindo de forma cômica ou explicativa.
- **Por que viraliza:** Combina polêmica real com humor de reação, legendas chamativas prendem atenção e o formato 'não acredito que ele disse isso' gera compartilhamento.
- **Como fazer:** 1) Buscar clipes virais/polêmicos no YouTube (domínio público, fair use educacional) ou gerar situações similares com Veo 3; 2) Extrair áudio e cortar as frases de impacto com ffmpeg; 3) Gerar legendas sincronizadas frame-a-frame (estilo meme, fonte impact/comic sans, cores vibrantes); 4) Criar narração IA (TTS ElevenLabs/Gemini) reagindo/explicando entre os cortes ('olha o que ele falou agora', 'espera, fica melhor'); 5) Adicionar SFX de meme (risada, suspense, erro do Windows) nos momentos-chave; 6) Overlay de zoom, slow-motion e efeitos (fogo, raio) nos punchlines com ffmpeg.
- **Ferramentas:** ffmpeg, TTS (ElevenLabs/Gemini), SFX de meme, overlays animados, Playwright (captura YouTube), LLM (roteiro da reação)
- **Material:** Clipes virais do YouTube (entrevistas, podcasts, programas de TV antigos), vídeos de domínio público, ou criar situações fictícias com Veo 3 + vozes TTS simulando entrevistas
- **Exemplo de roteiro:**

```
[Clipe: homem falando sobre casamento] 
LEGENDA: 'Claro! Eu casei com o Brasil!' 
NARRAÇÃO IA: 'Espera... isso vai ficar interessante' 
[SFX: suspense.mp3] 
LEGENDA: 'a ex-mulher e a amante' 
NARRAÇÃO IA: 'COMO ASSIM?' 
[Overlay: fogo + zoom] 
LEGENDA: 'um homem não pode ter várias mulheres?' 
NARRAÇÃO IA: 'Galera... não é assim que funciona' 
[SFX: erro_windows.mp3]
```

- Tags: clipes virais, reação IA, polêmica legendada, meme brasileiro, shorts comédia, fail legendado

### recap legendado de cena dramática de anime  -  potencial 9/10, esforco baixo  -  canal: manhwareact

- **Visto em:** 2026-10-01 17-53-35.mp4 (2026-10-02)
- **O que e:** Edição de cena de anime (Oshi no Ko) com legendas destacadas em palavras-chave emocionais (ARREPIADA, ESSENCIAL, PROPÓSITO) + cortes rápidos + trilha dramática. Foca em diálogo intenso sobre atuação/indústria.
- **Por que viraliza:** Diálogo dramático + palavras-chave visuais + cortes rápidos criam loop de atenção e identificação emocional com fãs de anime
- **Como fazer:** 1) Extrair cena do episódio via screencap ou usar frames do pipeline de recap; 2) Gerar legenda completa da cena com TTS (edge-tts ou ElevenLabs) + sincronizar com audio original ou narração IA; 3) Adicionar overlays de texto estilo Hormozi nas palavras emocionais (arrepiada, essencial, propósito); 4) Cortar em ritmo rápido (2-3s por frame) com ffmpeg; 5) Adicionar trilha dramática de fundo (das 341 disponíveis); 6) Finalizar com CTA ('deixa o like', 'parte 2 nos comentários')
- **Ferramentas:** ffmpeg, TTS, pipeline recap anime, overlays legendas Hormozi, trilhas música
- **Material:** frames extraídos do pipeline de recap de anime (episódios de Oshi no Ko, Frieren, etc.) + screencaps via Playwright de sites de streaming
- **Exemplo de roteiro:**

```
🎬 O que é essencial pra ser ator?
'Motivação e trabalho duro?'
ERRADO.
'Se a equipe não gostar de você, não recebe mais trampo'
💔 Oshi no Ko mostrando a REAL da indústria
👉 Já assistiu a 2ª temp?
```

- Tags: oshi no ko, anime recap, atuação, indústria do entretenimento, cena dramática, shorts anime

### recap de anime com memes de trader sobrepostos  -  potencial 9/10, esforco baixo  -  canal: manhwareact

- **Visto em:** 2026-10-01 17-54-53.mp4 (2026-10-02)
- **O que e:** Cenas de anime com legendas/memes de trading (stonks, gráficos, 'ACABA', lucro/prejuízo) sincronizados com a ação. Ritmo rápido, cortes secos, trilha neutra, memes visuais carregam a piada.
- **Por que viraliza:** Combina cultura otaku + fintwit/trader (crossover de nichos), memes reconhecíveis (stonks) + curiosidade sobre anime nichado = compartilhamento alto.
- **Como fazer:** 1) Baixar trailer/cenas oficiais do anime (YouTube, sites oficiais) ou usar frames do pipeline de recap. 2) Gerar memes de trader com IA (Pollinations: 'stonks meme', 'not stonks', 'gráfico vermelho caindo') ou buscar templates prontos. 3) Roteirizar: identificar momentos-chave (ganho, perda, tensão) e associar memes ('ela ganha 300k' = stonks; 'perde tudo' = not stonks). 4) ffmpeg: sobrepor memes/textos ('O LUCRO', 'ACABA', valores) com fade rápido, adicionar SFX de cash register/alarme de perda. 5) Legendas tipo meme (fonte Impact, borda preta) com edge-tts narrando 'Ela acabou de ganhar 300 mil... e perdeu tudo em 5 minutos'. 6) Trilha neutra/épica dos 341 tracks, cortar em 30-50s.
- **Ferramentas:** ffmpeg, edge-tts, Pollinations, pipeline recap anime, SFX (cash, alarme), overlays (legendas Impact)
- **Material:** trailers oficiais de anime no YouTube, frames do pipeline de recap, memes de trader gerados por IA (Pollinations: 'stonks', 'not stonks', 'gráfico bolsa'), templates de meme prontos (imgflip, domínio público)
- **Exemplo de roteiro:**

```
[Cena: personagem olha tela] NARRAÇÃO: 'Ela acabou de fazer 300 mil reais numa noite.' [Overlay: meme STONKS + SFX cash register] [Corte: gráfico vermelho] NARRAÇÃO: 'E perdeu TUDO em 5 minutos.' [Overlay: NOT STONKS + texto 'ACABA' + SFX alarme] [Fade: logo anime] NARRAÇÃO: 'Esse é o novo anime sobre traders. Vai bombar.'
```

- Tags: anime trader, stonks meme, recap anime, cultura otaku financeiro, anime nicho, meme fintwit

### recap dramatizado de manhwa com narração IA + painéis animados  -  potencial 9/10, esforco baixo  -  canal: manhwareact

- **Visto em:** 2026-10-02 08-03-48.mp4 (2026-10-02)
- **O que e:** Narração cinematográfica em português contando cena por cena de um manhwa (Prisão do Rei Demônio), com painéis do manhwa exibidos em sequência, zoom/pan dinâmico, efeitos sonoros de impacto, música épica de fundo e transições rápidas. Estrutura clássica de storytelling com tensão crescente.
- **Por que viraliza:** Storytelling épico com cliffhanger emocional prende até o fim; fãs de manhwa compartilham para recomendar a obra original.
- **Como fazer:** 1) Selecionar 40-60 painéis sequenciais de um manhwa do acervo (86 mil painéis); 2) Gerar roteiro dramático da cena usando LLM, com ganchos emocionais; 3) Sintetizar narração em PT-BR com edge-tts ou ElevenLabs (voz masculina grave/épica); 4) Montar no ffmpeg: painéis com zoom/pan (Ken Burns effect), duração sincronizada com narração; 5) Adicionar trilha épica (das 341 disponíveis) + SFX de impacto/explosão nos momentos chave (dos 650 sons de meme + 800 SFX); 6) Aplicar overlays animados (raio, fogo, confete) nos clímax da cena.
- **Ferramentas:** ffmpeg, TTS (edge-tts ou ElevenLabs), LLM para roteiro, painéis de manhwa do acervo, trilhas de música, SFX
- **Material:** 86 mil painéis de manhwa já disponíveis no acervo; roteiro gerado por LLM a partir de sinopses/capítulos públicos de manhwas populares
- **Exemplo de roteiro:**

```
O guerreiro ferido entrega a espada sagrada ao garoto... mas o Rei Demônio lança o ritual de possessão! A energia das sombras devora o menino, que grita em agonia. Part se arrasta desesperado: 'Eu não vou deixar a história se repetir!' Mas será tarde demais? CONTINUA... [link na bio]
```

- Tags: manhwa, recap, prisão do rei demônio, storytelling épico, narração IA, shorts dramatizados

### curiosidades de anime com painéis de mangá + narração IA  -  potencial 9/10, esforco baixo  -  canal: manhwareact

- **Visto em:** 2026-10-02 15-28-55.mp4 (2026-10-02)
- **O que e:** Vídeo curto revelando curiosidades ou fatos pouco conhecidos sobre animes/mangás populares, usando painéis estáticos com zoom dramático, narração direta e música de fundo tensa.
- **Por que viraliza:** Fãs de anime adoram descobrir detalhes obscuros que 'só quem leu a novel sabe' e compartilham para provar conhecimento
- **Como fazer:** 1) LLM pesquisa e gera roteiro de curiosidade específica sobre anime popular (ex.: 'personagem X quase morreu no capítulo Y'); 2) Seleciona 3-5 painéis de mangá relevantes do banco de 86k painéis; 3) TTS narra a curiosidade em tom revelador; 4) ffmpeg aplica zoom Ken Burns + transições nos painéis; 5) Adiciona trilha suspense/épica + SFX de impacto nos momentos-chave; 6) Overlay de legenda estilo Hormozi destaca palavras-chave
- **Ferramentas:** LLM, TTS, ffmpeg, painéis de mangá, trilhas, SFX, overlays de legenda
- **Material:** banco de 86k painéis de manhwa/mangá + pesquisa de curiosidades via LLM (wikis, fóruns, light novels)
- **Exemplo de roteiro:**

```
Você sabia que em Mushoku Tensei... [pausa dramática] ...a Silphy parou de falar por ANOS por causa do trauma com Rudeus? [painel dela calada] Ela só voltou a ter voz depois do reencontro na academia. [painel colorido] Quem leu a novel JÁ SABIA disso. [SFX de impacto]
```

- Tags: mushoku tensei, curiosidades anime, só quem leu sabe, silphy, anime facts, rudeus

### reaction fake a screenshot de anime com zoom dramático  -  potencial 9/10, esforco baixo  -  canal: manhwareact

- **Visto em:** 2026-10-02 15-38-02.mp4 (2026-10-02)
- **O que e:** Criador simula reagir a um frame estático de anime (Slime) com expressões exageradas e zoom no rosto, criando expectativa antes de revelar a imagem. Ritmo: setup emocional (3-4s) → reveal do frame (1-2s).
- **Por que viraliza:** Simula a experiência de assistir junto com alguém + gatilho de curiosidade (o que ele tá vendo?) + payoff emocional do reveal visual impactante
- **Como fazer:** 1) Gerar ou coletar frames de anime/manhwa de momentos icônicos (evoluções, revelações, plot twists). 2) Criar vídeo com foto do criador usando ffmpeg: começar em plano normal, aplicar zoom gradual (scale filter) + crop no rosto. 3) TTS gera narração tipo 'Olha isso!', 'Caramba!', 'Não acredito!' com timing dramático. 4) Inserir SFX de suspense (whoosh, riser) antes do reveal. 5) Cortar para o frame do anime em tela cheia com overlay animado (raio, fogo, confete). 6) Adicionar legenda estilo Hormozi destacando o momento ('A EVOLUÇÃO FINAL', 'ELE CONSEGUIU').
- **Ferramentas:** ffmpeg, TTS, fotos do criador, overlays animados, SFX, painéis de manhwa/anime, trilhas
- **Material:** 86 mil painéis de manhwa já disponíveis, screenshots de anime em domínio público ou fair use (frames únicos para comentário), fotos do criador em diferentes expressões
- **Exemplo de roteiro:**

```
[Zoom no rosto] 'Gente, olha isso aqui do Rimuru...' [SFX suspense] 'A evolução FINAL dele é absurda!' [Corta p/ frame do anime + raio] 'VIROU UM DEUS DRAGÃO!' [Legenda: 'CRONOA - FORMA SUPREMA']
```

- Tags: anime, slime, rimuru, evolução, reaction, plot twist

### diálogo legendado de anime/manhwa com texto enfatizado  -  potencial 9/10, esforco baixo  -  canal: manhwareact

- **Visto em:** 2026-10-02 15-43-00.mp4 (2026-10-02)
- **O que e:** Sequência de painéis estáticos de anime/manhwa mostrando diálogo emocional entre personagens, com legendas em português em fonte amarela chamativa sincronizadas com cada fala. Revela momento de tensão romântica.
- **Por que viraliza:** Plot twists românticos em anime/manhwa geram identificação instantânea e loops de rewatching para captar a emoção completa
- **Como fazer:** 1) Selecionar 4-6 painéis do acervo de 86 mil painéis de manhwa que formem uma cena com revelação/plot twist emocional; 2) Criar legendas em português estilo meme (fonte amarela com borda preta, palavras-chave em caps) para cada painel; 3) Adicionar zoom sutil e transições rápidas (0.8-1.2s por painel) com ffmpeg; 4) Sobrepor trilha emocional ou música viral nos momentos de tensão; 5) Opcional: adicionar SFX de impacto/suspense nos momentos de revelação; 6) Renderizar em 9:16 com ffmpeg.
- **Ferramentas:** ffmpeg, painéis de manhwa, trilhas musicais, SFX, overlays de texto
- **Material:** acervo próprio de 86 mil painéis de manhwa; selecionar cenas de romance/revelação/plot twist de obras populares
- **Exemplo de roteiro:**

```
Painel 1: 'ODIAVA??' (close na personagem chocada)
Painel 2: Olhar intenso da outra personagem
Painel 3: 'EXATAMENTE' (confirmação)
Painel 4: 'QUE' (reação final)
[Música emocional de fundo + corte abrupto]
```

- Tags: manhwa, romance, plot twist, anime, revelação, ships

### recap de cena de anime com legendas dinâmicas + classificação de raridade  -  potencial 9/10, esforco medio  -  canal: manhwareact

- **Visto em:** 2026-10-02 15-44-31.mp4 (2026-10-02)
- **O que e:** Mostra uma cena de ação de anime com legendas hardcoded que narram o que acontece ('FOI A SORTE', 'TARDE DEMAIS') + overlay de raridade ('RARO') estilo gacha/RPG. Ritmo frenético, cortes rápidos sincronizados com a ação.
- **Por que viraliza:** Combina nostalgia de gacha/RPG (raridade, sorte) com tensão de combate e legendas que antecipam o desfecho, gerando loop e comentários tipo 'eu dropei essa skin'
- **Como fazer:** 1) Selecionar cena de combate de anime (usar pipeline de recap ou screenshots dos 86k painéis de manhwa animados com Veo 3). 2) Gerar narração curta e impactante com LLM ('A habilidade era RARA demais!'). 3) Renderizar legendas com ffmpeg (estilo Hormozi: fonte bold, stroke grosso, zoom in/out). 4) Adicionar overlay de raridade (cristal brilhante + texto 'RARO'/'ÉPICO') com ffmpeg ou After Effects gratuito. 5) Música épica de fundo (das 341 trilhas) + SFX de impacto (dos 650 sons de meme). 6) Exportar em vertical 9:16.
- **Ferramentas:** ffmpeg, LLM, Veo 3, trilhas, SFX, overlays animados
- **Material:** 86 mil painéis de manhwa (animar com Veo 3) ou cenas de anime de domínio público/fair use educacional; gerar overlays de raridade com Gemini/Pollinations
- **Exemplo de roteiro:**

```
CENA 1: Personagem invoca cristal brilhante [OVERLAY: 'RARO'] [LEGENDA: 'ELE CONSEGUIU A HABILIDADE RARA'] / CENA 2: Inimigo ataca [LEGENDA: 'FOI A SORTE'] / CENA 3: Personagem contra-ataca com poder [LEGENDA: 'TARDE DEMAIS'] [SFX: explosão + música épica crescendo]
```

- Tags: anime, gacha, raridade, habilidade, sorte, recap

### recap dramático de cena icônica de anime com legendas e cortes rápidos  -  potencial 9/10, esforco baixo  -  canal: cenareact

- **Visto em:** 2026-10-02 15-47-23.mp4 (2026-10-02)
- **O que e:** Sequência de frames estáticos do anime com falas legendadas sincronizadas, cortes dinâmicos no ritmo da tensão, zoom em expressões faciais. Puro momento épico condensado em 30-60s.
- **Por que viraliza:** Nostalgia + tensão emocional de momento icônico que fãs querem reviver e compartilhar com quem não assistiu
- **Como fazer:** 1) Usar pipeline de recap de anime para extrair frames-chave de cenas icônicas (Torneio do Poder, Marineford, etc); 2) Gerar narração dramática com TTS (ElevenLabs com voz grave/épica); 3) Adicionar legendas hardcoded estilo Hormozi com palavras-chave destacadas (TRUNKS, BULMA); 4) Aplicar zoom/pan em rostos com ffmpeg (Ken Burns effect); 5) Inserir SFX de impacto nos momentos de tensão + trilha épica; 6) Overlay de raio/energia nos ataques
- **Ferramentas:** pipeline recap anime, TTS (ElevenLabs), ffmpeg, overlays (raio/energia), SFX impacto, trilhas épicas
- **Material:** frames extraídos via pipeline de recap de episódios específicos de anime (fair use educacional/comentário), screenshots da comunidade, fan art com crédito
- **Exemplo de roteiro:**

```
「Vegeta no momento mais INSANO do Torneio do Poder」
'Vamos sobreviver a todo custo!'
*zoom no rosto determinado*
'Adeus, Bulma... Trunks... Kakaroto...'
*explosão de energia roxa*
ELE REALMENTE FEZ ISSO? 😱
```

- Tags: dragon ball, vegeta, torneio do poder, anime épico, momento icônico, DBS

### comparação VS com narração educativa + imagens de fanart/anime  -  potencial 9/10, esforco baixo  -  canal: manhwareact

- **Visto em:** 2026-10-03 13-21-35.mp4 (2026-10-04)
- **O que e:** Compara dois elementos de anime (personagens, versões, equipamentos) usando narração explicativa, cortes rápidos de fanart/screenshots, legendas dinâmicas e efeitos visuais (zoom, brilho, onomatopeias).
- **Por que viraliza:** Gatilho de curiosidade + debate entre fãs ('qual é melhor?') + formato educativo que ensina lore sem parecer aula
- **Como fazer:** 1) Escolher tema de comparação popular (ex: poder X vs Y, versão jovem vs adulta); 2) Gerar script de comparação via LLM com fatos/curiosidades em formato VS; 3) Coletar 6-10 imagens (fanart IA via Pollinations/Gemini + screenshots de anime do banco de 86k paineis); 4) TTS narração em português (edge-tts ou ElevenLabs); 5) Montar no ffmpeg: zoom dramático nas imagens, legendas animadas estilo Hormozi com palavras-chave destacadas ('APESAR', 'OLDEUS', 'RUDEUS'), overlays de impacto (raio, brilho), SFX de tensão; 6) Música épica de fundo das 341 trilhas
- **Ferramentas:** ffmpeg, TTS, geração de imagem IA, overlays animados, SFX, trilhas de música, LLM para roteiro
- **Material:** Fanart gerada por IA (Pollinations/Gemini com prompts de personagens), screenshots do banco de 86k paineis de manhwa/anime, imagens de wikis de anime (domínio educativo/crítica)
- **Exemplo de roteiro:**

```
🔥 ARMADURA RUDEUS VS OLDEUS - QUAL VENCE?

Apesar de ser mago poderoso, Rudeus é FRACO fisicamente...
Mas a armadura MK1 tem 3 METROS de altura!

Já a do Oldeus? Ele desenvolveu SOZINHO.
Mesmo objetivo, visual TOTALMENTE diferente.

Qual você escolheria? 👇
```

- Tags: mushoku-tensei, anime-vs, curiosidades-anime, rudeus, comparacao-anime, anime-brasileiro

### recap de anime com legendas palavra-chave + trilha épica  -  potencial 9/10, esforco baixo  -  canal: cenareact

- **Visto em:** 2026-10-03 13-25-59.mp4 (2026-10-04)
- **O que e:** Narração rápida de cena/arco de anime com cortes dinâmicos do episódio, palavras-chave destacadas em legenda estilo Reels (MANA, PREPARADO, UMA HABILIDADE) e música épica de fundo. Ritmo acelerado, informação condensada, visual colorido.
- **Por que viraliza:** Entrega informação densa em segundos com estímulo visual constante (cores saturadas + legendas dinâmicas) e ganchos narrativos de plot twist que fazem otaku parar o scroll
- **Como fazer:** 1) Pegar 3-5 cenas importantes de um episódio de anime (screenshots ou clipes curtos via pipeline de recap); 2) Escrever roteiro de 30-40s com LLM focando em plot twist/momento épico, marcando palavras-chave; 3) Gerar narração com TTS PT-BR (ElevenLabs para qualidade); 4) Editar no ffmpeg: cortar cenas em 2-4s cada, inserir legendas animadas (palavras-chave em destaque com overlay de fogo/raio nos momentos chave); 5) Adicionar trilha épica das 341 disponíveis + SFX de impacto nos plot twists; 6) Exportar vertical 9:16
- **Ferramentas:** ffmpeg, TTS (ElevenLabs), pipeline de recap anime, overlays animados, trilhas épicas, SFX
- **Material:** screenshots/clipes de episódios de anime via pipeline de recap (fair use educacional/comentário), cenas públicas ou promocionais
- **Exemplo de roteiro:**

```
A ilha onde Fran quase MORREU... [cena ilha] No centro dela existe uma dungeon secreta cheia de MORTOS VIVOS... [overlay raio roxo] incluindo uma criatura de AMEAÇA CLASSE B [zoom no esqueleto] que já tinha obrigado até ELE a FUGIR no passado. [SFX suspense] Agora o Necromante queria voltar PREPARADO. [música épica sobe]
```

- Tags: anime recap, reincarnated as a sword, anime BR, momento épico anime, fran, explicação rápida

### história de golpe contada com legendas + imagens ilustrativas  -  potencial 9/10, esforco baixo  -  canal: novo canal: GolpesBR ou MalândriaBR

- **Visto em:** 2026-10-04 08-23-52.mp4 (2026-10-04)
- **O que e:** Narração de uma história real de golpe/malandragem brasileira, com cortes rápidos entre imagens ilustrativas (aeroporto, esteira de bagagem, documentos) e legendas destacadas. Ritmo dinâmico com revelação surpresa no final.
- **Por que viraliza:** Brasileiros adoram histórias de malandragem + indignação coletiva + twist inesperado que prende até o final
- **Como fazer:** 1) Pesquisar história real de golpe/fraude em notícias, fóruns ou processos públicos; 2) Escrever roteiro com LLM dividindo a história em 4-6 beats com gancho final; 3) Gerar narração com TTS brasileiro (edge-tts ou ElevenLabs); 4) Capturar com Playwright ou buscar imagens gratuitas de aeroportos, malas, documentos, hotéis; 5) Montar no ffmpeg com cortes a cada 2-3 segundos, legendas amarelas estilo meme, som de impacto no twist final; 6) Adicionar música de tensão das 341 trilhas
- **Ferramentas:** LLM, TTS, Playwright, Pollinations/Gemini, ffmpeg, SFX, música, legendas animadas
- **Material:** notícias de golpes, sites de notícias jurídicas, Reclame Aqui, processos públicos do TJ, imagens Pexels/Unsplash de aeroportos/viagens, geração IA para ilustrações específicas
- **Exemplo de roteiro:**

```
Três amigos viajaram juntos pra Orlando. Um deles despachou a mala... mas quando chegou na esteira, ele disse que a mala NUNCA CHEGOU. Processou a companhia aérea por extravio. O detalhe? Os outros dois amigos já estavam no hotel... COM AS TRÊS MALAS. Golpe perfeito. Até a empresa descobrir.
```

- Tags: golpes, malandragem brasileira, aeroporto, história real, indignação, twist

### recap de anime +18 com legendas de texto dinâmico  -  potencial 9/10, esforco baixo  -  canal: manhwareact

- **Visto em:** 2026-10-04 08-26-56.mp4 (2026-10-04)
- **O que e:** Mostra cenas de anime de harém/ecchi com legendas curtas e impactantes sincronizadas com momentos-chave (personagens, situações absurdas). Ritmo rápido, texto chamativo, sem narração verbal.
- **Por que viraliza:** Animes +18/harém são clickbait natural, o formato de 'exposição rápida' com texto polêmico gera curiosidade e compartilhamento por choque/humor
- **Como fazer:** 1) Usar pipeline de recap de anime para extrair frames de animes de harém/ecchi disponíveis ou usar imagens dos 86 mil painéis de manhwa similares; 2) Gerar roteiro com LLM identificando pontos polêmicos/engraçados (ex.: 'mãe e irmã querem o MC', 'harém no ep 2'); 3) Aplicar legendas animadas estilo Hormozi com ffmpeg + overlays de fogo/confete nos momentos de tensão; 4) Adicionar trilha de suspense/meme das 341 disponíveis + sons de meme (ex.: 'bruh', 'vine boom') nos reveals; 5) Exportar em 9:16 com cortes rápidos (3-5s por frame)
- **Ferramentas:** ffmpeg, pipeline recap anime, LLM narracao, overlays animados, trilhas musica, sons meme
- **Material:** Pipeline de recap de anime para frames de episódios recentes de harém/ecchi, ou 86 mil painéis de manhwa do mesmo gênero como alternativa visual
- **Exemplo de roteiro:**

```
Frame 1: [Garota loira] 'ELE SALVOU ELA'
Frame 2: [Mulher de cabelo roxo] 'ESSA É A MÃE DELE'
Frame 3: [Duas garotas] 'E AS DUAS QUEREM ELE'
Frame 4: [Cena de grupo] 'HARÉM NO EPISÓDIO 2'
Frame 5: 'ESSE ANIME NÃO TEM LIMITES 💀'
```

- Tags: anime polêmico, harém absurdo, ecchi, anime +18, wtf anime, recap anime

### recap de episódio com legendas sincronizadas + trilha épica  -  potencial 9/10, esforco baixo  -  canal: cenareact

- **Visto em:** 2026-10-04 08-32-52.mp4 (2026-10-04)
- **O que e:** Mostra cenas-chave de um episódio de anime com legendas brancas/vermelhas sincronizadas descrevendo o que acontece, editadas no ritmo da música. Sem narração, só texto + trilha dramática.
- **Por que viraliza:** Recaps visuais rápidos prendem fãs que perderam o episódio e curiosos que querem spoilers sem assistir tudo
- **Como fazer:** 1. Usar pipeline de recap de anime para gerar screenshots das cenas principais do episódio. 2. Escrever roteiro com LLM descrevendo os momentos (ex.: 'Uma união', 'Nem dava', 'Segundos', 'Justamente'). 3. Adicionar legendas animadas estilo Hormozi (fade in/zoom) sincronizadas com os beats da trilha. 4. Selecionar trilha épica das 341 disponíveis (tipo orquestral/trap). 5. Montar com ffmpeg: frame estático + legenda + fade entre cenas. 6. Adicionar overlays de fogo/raio nos momentos de impacto.
- **Ferramentas:** pipeline recap anime, LLM, ffmpeg, overlays animados, trilhas épicas
- **Material:** screenshots do episódio via pipeline de recap de anime; texto gerado por LLM; trilhas do acervo
- **Exemplo de roteiro:**

```
Frame 1: Asta aparece com armadura preta [LEGENDA: 'UMA UNIÃO ANSAKE'] / Frame 2: Yuno surge de costas [LEGENDA: 'NEM DAVA ANSAKE'] / Frame 3: Asta e Yuno lado a lado [LEGENDA: 'SEGUNDOS ANSAKE'] / Frame 4: Vilão sorrindo [LEGENDA: 'JUSTAMENTE ANSAKE'] / Música: trap orquestral épico, overlays de raio nos momentos de transformação.
```

- Tags: black clover, recap anime, asta armadura, yuno, anime 2026, spoiler

### recap de anime com legendas + música  -  potencial 9/10, esforco baixo  -  canal: cenareact

- **Visto em:** 2026-10-04 08-34-23.mp4 (2026-10-04)
- **O que e:** Montagem rápida de cenas-chave de anime com legendas curtas explicando a trama em ordem cronológica, sem narração, apenas música de fundo tensionante. Ritmo acelerado, foco em visuais impactantes.
- **Por que viraliza:** Storytelling visual comprimido em 15-30s gera curiosidade imediata sobre o anime completo, funciona como trailer viciante
- **Como fazer:** 1) Extrair 8-12 frames impactantes de episódios do anime (usar pipeline de recap existente ou prints manuais); 2) Escrever legendas curtas e diretas com LLM (ex: 'UM VÍRUS', 'PERSEGUIDAS', 'TRANSFORMAR'); 3) Montar no ffmpeg com transições rápidas (0.8-1.2s por frame); 4) Adicionar música tensionante das 341 trilhas (suspense/ação); 5) Overlay de legendas estilo Hormozi (bold, outline, posição inferior); 6) Exportar vertical 9:16
- **Ferramentas:** ffmpeg, LLM (roteiro), pipeline recap anime, overlays legendas, trilhas música
- **Material:** screenshots de episódios de anime via pipeline recap existente; anime de domínio público ou clips transformativos (fair use educacional); alternativamente usar os 86k painéis de manhwa se for adaptar mangá
- **Exemplo de roteiro:**

```
Frame 1: 'UM VÍRUS MISTERIOSO ATACA A CIDADE' [cena caótica vermelha]
Frame 2: 'DUAS GAROTAS PRECISAM FUGIR' [personagens correndo]
Frame 3: 'MAS UMA DELAS PODE SE TRANSFORMAR' [transformação]
Frame 4: 'ELA DISPARA... E TUDO MUDA' [ação climática]
Frame 5: 'ZENSHU - ASSISTA AGORA' [título do anime]
```

- Tags: anime, recap, zumbi, storytelling, viral, otaku

### recap de cena de anime com legendas destacadas e trilha dramática  -  potencial 9/10, esforco baixo  -  canal: cenareact

- **Visto em:** 2026-10-04 08-44-45.mp4 (2026-10-04)
- **O que e:** Apresenta uma cena completa de anime (diálogo entre personagens) com legendas em português, palavras-chave destacadas em amarelo/cores, e cortes rápidos entre frames. Usa música de fundo e foca em momentos de conflito/comédia/tensão que geram identificação.
- **Por que viraliza:** Diálogo inesperado + comédia situacional (princesa revoltada, casamento forçado) + legendas destacadas criam gancho de 'espera, o quê?' e loop de rewatch
- **Como fazer:** 1) Baixar episódio do anime ou usar pipeline de recap existente para extrair cena específica (30-60s); 2) Transcrever e traduzir diálogos, identificar palavras de impacto; 3) Gerar legendas com ffmpeg usando ass/srt com estilo Hormozi (palavras destacadas em amarelo, outline preto, fonte bold); 4) Selecionar trilha de música dramática/cômica das 341 disponíveis; 5) Adicionar overlay animado (raio/fogo) nos momentos de punch line; 6) Renderizar com ffmpeg: cena + legendas + música + overlays
- **Ferramentas:** ffmpeg, pipeline recap anime, overlays animados, trilhas de música
- **Material:** episódios de anime baixados, pipeline de recap já existente, ou captura via Playwright de players legais com subtítulo extraído
- **Exemplo de roteiro:**

```
🔥 QUANDO O REI TE CASA SEM AVISAR

[Princesa descobrindo que foi prometida]
'Como anunciou meu noivado sem me perguntar?'

[MC entra achando que é convidado]
'Esse cara não é boa pessoa'

[Plot twist: ele É o noivo E virou rei]
'Muito obrigada por USURPAR O TRONO' 💀

#anime #genjitsushugiyuusha #isekai
```

- Tags: anime, isekai, comédia, casamento arranjado, plot twist, recap

### recap de cena OP com legendas hard-coded e música épica  -  potencial 9/10, esforco baixo  -  canal: cenareact

- **Visto em:** 2026-10-04 10-47-36.mp4 (2026-10-04)
- **O que e:** Pega uma cena clássica de anime onde o protagonista OP revela seu poder, adiciona legendas em português estilo meme ('ELE ACHOU QUE ERA O ESPERTÃO... CASO / TUDO') sincronizadas com os momentos-chave, música épica de fundo, e narração TTS explicando o contexto. Estrutura: setup → subversão → payoff visual.
- **Por que viraliza:** Gatilho de satisfação + subversão de expectativa: todos amam ver o vilão confiante sendo humilhado pelo protagonista OP, especialmente com legendas meme que antecipam o plot twist.
- **Como fazer:** 1. Buscar no pipeline de recap de anime cenas icônicas de protagonistas OP (Maou Gakuin, Overlord, Misfit of Demon King Academy, etc.) ou usar os 86 mil painéis de manhwa para montar a sequência. 2. Gerar narração TTS em português explicando o setup ('Os inimigos acharam que tinham vencido o Rei Demônio com uma barreira anti-magia...'). 3. Adicionar legendas hard-coded via ffmpeg nos momentos-chave: 'ELE ACHOU QUE ERA O ESPERTÃO' → 'CASO' → 'TUDO' → reveal do poder. 4. Sincronizar música épica das 341 trilhas (tipo orquestral/trap épico) com o climax. 5. Overlays animados de fogo/raio no momento do poder revelado. 6. Renderizar com ffmpeg em formato vertical 9:16.
- **Ferramentas:** ffmpeg, TTS, pipeline de recap de anime, 86 mil painéis de manhwa, overlays animados, 341 trilhas de música
- **Material:** pipeline de recap de anime existente, 86 mil painéis de manhwa para sequências alternativas, clips de cenas OP de domínio público ou fair use educacional
- **Exemplo de roteiro:**

```
NARRAÇÃO: 'Os inimigos do Rei Demônio acharam que tinham vencido. Usaram a barreira Lyrid, que sela toda magia do clã Demonia...' [pausa dramática] 'Mas esqueceram de um detalhe.' [música sobe] LEGENDA: 'ELE ACHOU QUE ERA O ESPERTÃO...' → personagem quebra a barreira → 'CASO' → revela os olhos vermelhos → 'TUDO' → destrói todos. NARRAÇÃO: 'Anos de planejamento... destruídos em 3 segundos.'
```

- Tags: anime OP, rei demônio, plot twist, protagonista OP, maou gakuin, satisfação garantida

### recap narrado de dorama com legendas dinamicas  -  potencial 9/10, esforco medio  -  canal: novo canal: DramaResumosBR

- **Visto em:** 2026-10-04 10-51-21.mp4 (2026-10-04)
- **O que e:** Narração em português conta história dramática de dorama/filme asiático com cenas cortadas, legendas destacando palavras-chave (DÓLARES, MINHA) e ritmo acelerado. Estrutura: intro do conflito → reviravolta → desfecho satisfatório.
- **Por que viraliza:** Gatilho de justiça/vingança + reviravoltas constantes + satisfação do 'vilão se ferrando' mantém atenção até o final
- **Como fazer:** 1) Escolher dorama/filme asiático viral (domínio público ou fair use para recap); 2) Gerar roteiro de recap com LLM (foco em reviravoltas e vingança); 3) Criar cenas-chave com Veo 3 (personagens asiáticos, cenários dramáticos) ou usar painéis de manhwa estilizados; 4) Narração com TTS edge-tts (voz masculina brasileira, tom sério); 5) Adicionar legendas hardcoded com ffmpeg (palavras-chave em negrito/zoom, estilo Hormozi); 6) Música de suspense/drama das 341 trilhas + SFX de impacto nos plot twists
- **Ferramentas:** Veo 3, TTS edge-tts, LLM, ffmpeg, painéis manhwa, trilhas musicais, SFX
- **Material:** Doramas de domínio público ou recaps transformativos (fair use); painéis dos 86 mil manhwas estilizados como cenas live-action; geração de personagens asiáticos com Veo 3
- **Exemplo de roteiro:**

```
Ela descobriu que o marido estava TRAINDO ela com várias mulheres. Mas o que ele não sabia... é que ela tinha acesso ao COFRE SECRETO enterrado no quintal. Enquanto ele comemorava com a amante, ela cavou a terra e encontrou DEZENAS DE CAIXAS cheias de OURO. Nos dias seguintes, ela fez os papéis de óbito dele... e foi atrás das amantes pra RECUPERAR cada centavo gasto. No final? Ela e a sogra ficaram com MAIS DE 1 BILHÃO DE DÓLARES.
```

- Tags: dorama recap, vinganca satisfatoria, plot twist, historia real, justica servida, mulher forte

### recap de cena épica de manhwa com legendas palavra-por-palavra + trilha épica  -  potencial 9/10, esforco baixo  -  canal: manhwareact

- **Visto em:** 2026-10-04 10-55-59.mp4 (2026-10-04)
- **O que e:** Mostra uma sequência de ação/clímax de manhwa com legendas amarelas sincronizadas palavra por palavra, zoom dramático nos painéis-chave e trilha sonora épica. Ritmo rápido, cada palavra aparece no timing certo criando tensão.
- **Por que viraliza:** Legendas palavra-por-palavra criam tensão cinematográfica e loop perfeito, formato já validado no TikTok/Shorts de recap de mangá
- **Como fazer:** 1) Selecionar 4-8 painéis consecutivos de uma cena épica dos 86k painéis de manhwa; 2) Escrever legenda curta e impactante descrevendo a cena (ex: 'ele | cavaleiro | contra | o exército'); 3) Gerar vídeo com ffmpeg: cada painel dura 0.8-1.2s, aplicar zoom-in suave (scale + zoompan) nos momentos-chave; 4) Adicionar legendas amarelas com bordas pretas (drawtext) sincronizadas palavra por palavra usando timecodes precisos; 5) Mixar trilha épica (das 341 disponíveis) aumentando volume nos painéis de impacto; 6) Aplicar overlay de raio/energia nos frames de ataque
- **Ferramentas:** ffmpeg, painéis de manhwa, trilhas épicas, overlays animados
- **Material:** 86 mil painéis de manhwa já disponíveis no acervo, selecionar sequências de combate/momentos épicos
- **Exemplo de roteiro:**

```
Frame 1: 'ele' | Frame 2: 'cavaleiro' | Frame 3: 'contra' | Frame 4-5: pausa dramática com zoom + trilha crescendo | Frame 6: 'O IMPÉRIO INTEIRO' (caps lock, overlay de raio) | CTA final: 'Nome do manhwa nos comentários 👇'
```

- Tags: manhwa, recap, cena épica, ação, viral, storytelling

### recap de cena de manhwa com legendas de reação e zoom dramático  -  potencial 9/10, esforco baixo  -  canal: manhwareact

- **Visto em:** 2026-10-04 10-57-49.mp4 (2026-10-04)
- **O que e:** Mostra uma cena específica de anime/manhwa com legendas que narram o pensamento dos personagens, usando zooms, cortes rápidos e texto estilo meme para criar tensão cômica ou dramática.
- **Por que viraliza:** Mal-entendidos e reviravoltas em relacionamentos/poder geram identificação instantânea e vontade de comentar 'eu entendo ela'
- **Como fazer:** 1. Extrair 4-6 painéis sequenciais de um manhwa dos 86 mil disponíveis (escolher cena com mal-entendido ou tensão); 2. Gerar narração TTS em PT descrevendo a situação irônica/dramática ('Ela achou que ele era uma garota...'); 3. Adicionar legendas sincronizadas com palavras-chave (ACONTECER, RANKERS, PENSA) usando overlays animados; 4. Aplicar zoom gradual em ffmpeg (scale e crop) nos painéis-chave para criar tensão; 5. Adicionar trilha suspense/cômica dos 341 disponíveis + SFX de impacto nos momentos de revelação; 6. Renderizar em 9:16 com transições rápidas (0.3-0.5s por painel).
- **Ferramentas:** ffmpeg, TTS, paineis de manhwa, overlays animados, trilhas de musica, SFX
- **Material:** 86 mil painéis de manhwa já disponíveis, selecionando cenas com plot twist, mal-entendidos românticos oupower-up
- **Exemplo de roteiro:**

```
Título: 'ELA ACHOU QUE ELE ERA FRACO... 💀'
[Painel 1 - zoom no corpo] 'Ela pensou que ele era um garoto comum...'
[Painel 2 - close no rosto irritado] 'Mas aconteceu algo inesperado'
[Painel 3 - power-up vermelho] 'Ele era um RANKER nível S disfarçado'
[Painel 4 - zoom nos pés] 'E agora? Ela vai ter que lidar com as consequências...'
```

- Tags: manhwa, recap, plot-twist, ranker, romance, poder-oculto

### meme de anime com legenda irônica sobre vida adulta  -  potencial 9/10, esforco baixo  -  canal: manhwareact

- **Visto em:** 2026-10-06 10-17-10.mp4 (2026-10-06)
- **O que e:** Usa cenas icônicas de anime (Dragon Ball) com legendas que comparam situações épicas do anime com frustrações da vida real. Ritmo rápido, 2-4 frames, punchline no final.
- **Por que viraliza:** Nostalgia + identificação com frustração da vida adulta gera engajamento massivo e compartilhamento ('eu na vida real').
- **Como fazer:** 1) Escolher cena icônica de anime/manhwa dos 86 mil painéis. 2) Escrever roteiro com LLM: setup (promessa épica do anime) + punchline (realidade frustrante). 3) Adicionar legendas estilo meme com ffmpeg (fonte impact, stroke branco). 4) Inserir trilha nostálgica ou sons de meme no timing certo. 5) Exportar em 9:16 com cortes rápidos (3-5s por frame).
- **Ferramentas:** ffmpeg, LLM para roteiro, painéis de manhwa/anime, sons de meme, legendas animadas
- **Material:** 86 mil painéis de manhwa próprios, prints de anime clássicos (domain público ou fair use para crítica/paródia), geração IA para personagens genéricos se necessário
- **Exemplo de roteiro:**

```
Frame 1: Goku tenso - 'Mas pra virar Super Saiyajin você precisa ser um Saiyajin'
Frame 2: Goku reflexivo - 'Acho melhor só focarmos no treinamento normal mesmo'
Frame 3: Personagem genérico estressado - 'Quando te oferecem um curso pra virar líder'
Frame 4: Mesmo personagem aliviado - 'Mas você lembra que sua meta já é taxada'
```

- Tags: dragon ball meme, vida adulta anime, meme nostalgia, super saiyajin, anime brasileiro, realidade vs anime

### animação dublada com piada brasileira no final  -  potencial 9/10, esforco medio  -  canal: novo canal: BrasilToonMemes

- **Visto em:** 2026-10-06 10-15-59.mp4 (2026-10-06)
- **O que e:** Animação estilo motion comic de personagens conhecidos (Sonic/anime/games) com diálogo dublado construindo tensão, resolvida com piada ou referência brasileira no final. Legendas sincronizadas, cortes rápidos, SFX de ação.
- **Por que viraliza:** Nostalgia de personagem conhecido + reviravolta cômica brasileira inesperada gera rewatch e compartilhamento ('kkkkk Green Hill de Janeiro')
- **Como fazer:** 1. LLM gera roteiro curto (30-50s) com setup + punchline brasileira sobre personagem popular; 2. Gemini/Pollinations gera 4-8 painéis estilo animação (ou usa painéis de manhwa adaptados); 3. ElevenLabs/edge-tts dubla cada linha com vozes diferentes (Sonic=voz aguda, vilão=grave); 4. ffmpeg anima painéis com zoom/pan, adiciona legendas palavra-por-palavra estilo TikTok, insere SFX (corrida, explosão, 'ué') e trilha de tensão; 5. Overlay de efeitos (raio, confete) no punchline final; 6. Exporta 9:16 com hook nos primeiros 2s.
- **Ferramentas:** LLM (roteiro), Gemini/Pollinations (painéis), ElevenLabs/edge-tts, ffmpeg, overlays animados, SFX + trilhas, legendas Hormozi
- **Material:** Painéis gerados por IA imitando estilo de animação 2D ou adaptação dos 86 mil painéis de manhwa existentes; referências visuais de personagens icônicos (Sonic, Naruto, Mario) via prompts; piadas/memes brasileiros do cotidiano
- **Exemplo de roteiro:**

```
[SONIC correndo] 'Cara, precisa de um plano!' [TAILS] 'Eu sou imortal, posso me jogar neles!' [SFX: explosão] [SONIC pega esmeraldas] 'Deu certo!' [CORTA PRA CIDADE] 'Onde estamos?' [ESQUILO APARECE] 'Green Hill de Janeiro, parceiro!' [ZOOM + CONFETE + RISADA]
```

- Tags: sonic, animação dublada, meme brasileiro, personagens, comédia, nostalgia

### Recap de cena bizarra de anime com legendas motivacionais irônicas  -  potencial 9/10, esforco baixo  -  canal: cenareact

- **Visto em:** 2026-10-07 13-47-03.mp4 (2026-10-12)
- **O que e:** Pega uma cena absurda/over de anime (treino maluco, poder exagerado), recorta frames-chave, adiciona legendas curtas e impactantes em cada corte, com música épica de fundo. O contraste entre o absurdo visual e a narração séria/motivacional gera o humor.
- **Por que viraliza:** O absurdo visual dos animes de luta + legendas que amplificam o ridículo criam um loop de 'isso é sério?' que prende e gera compartilhamento por humor involuntário
- **Como fazer:** 1) Extrair 4-6 frames de cenas icônicas de Baki ou outros animes de luta via pipeline de recap. 2) Escrever legendas curtas e irônicas com LLM ('ENVOLVIA', 'OITO VEZES MAIOR', 'VER PRESO NO') que aumentam a tensão. 3) Montar no ffmpeg: cada frame 1-2s, transições rápidas, overlay de legenda estilo Hormozi (amarelo, bold, sombra). 4) Adicionar trilha épica/tensa do banco de 341 músicas. 5) Opcional: SFX de impacto nos cortes. 6) Exportar vertical 9:16.
- **Ferramentas:** ffmpeg, pipeline de recap anime, overlays de legenda Hormozi, banco de trilhas, LLM para roteiro
- **Material:** Frames extraídos de episódios de anime via pipeline de recap (Baki, Kengan Ashura, Hajime no Ippo, etc.) - uso transformativo educacional/comentário
- **Exemplo de roteiro:**

```
Frame 1: Baki olhando sério - 'ENVOLVIA'
Frame 2: Tigre gigante vs. grilo musculoso - 'OITO VEZES MAIOR'
Frame 3: Baki sofrendo - 'VER PRESO NO'
Frame 4: Close intenso - 'ATÉ ELE COMEÇOU A ALUCINAR'
[Música épica de tensão crescente]
```

- Tags: baki, anime absurdo, treino impossível, alucinação, motivação irônica, over the top

### teoria de anime com painéis + legendas word-by-word + música  -  potencial 9/10, esforco baixo  -  canal: manhwareact

- **Visto em:** 2026-10-07 13-48-56.mp4 (2026-10-12)
- **O que e:** Vídeo de teoria sobre poder/lore de personagem usando painéis sequenciais do anime/manhwa com legendas destacando palavras-chave em amarelo, sem narração, só música de tensão.
- **Por que viraliza:** Teorias geram engajamento nos comentários e o formato word-by-word com painéis impactantes prende até o final por curiosidade
- **Como fazer:** 1) Selecionar 4-6 painéis impactantes do manhwa (dos 86 mil disponíveis) que ilustrem a teoria; 2) Escrever roteiro da teoria em 3-5 frases curtas; 3) Gerar legendas com palavras-chave em amarelo usando overlays animados; 4) Adicionar zoom/movimento nos painéis com ffmpeg (ken burns effect); 5) Colocar trilha de suspense/épica das 341 disponíveis; 6) Renderizar em 9:16 com transições rápidas (2-3s por painel)
- **Ferramentas:** ffmpeg, overlays animados, painéis manhwa, trilhas musicais
- **Material:** 86 mil painéis de manhwa já disponíveis, seleção manual ou por LLM dos momentos-chave que sustentam a teoria
- **Exemplo de roteiro:**

```
ISSO MUDA TUDO SOBRE O YUJIRO...
MAS QUANDO OLHOU
OS SOLDADOS FICARAM
PARALISADOS DE MEDO
ELE VIU O DEMON BACK
DO AVÔ DELE TAMBÉM
```

- Tags: teoria anime, demon back, lore, mistério, plot twist, baki

### batalha de anime com legendas dinâmicas e musica épica  -  potencial 9/10, esforco baixo  -  canal: cenareact

- **Visto em:** 2026-10-07 13-50-45.mp4 (2026-10-12)
- **O que e:** Apresenta confronto entre personagens de anime/manga com título chamativo (X VS Y), painéis estáticos em sequência, legendas com palavras destacadas em cores, música de fundo tensa e branding constante (título da obra no rodapé).
- **Por que viraliza:** Gatilho de curiosidade mórbida (canibalismo/violência extrema) + nostalgia de anime clássico + formato VS que gera debate nos comentários
- **Como fazer:** 1) Selecionar confronto icônico de Baki/outro anime do banco de 86k painéis de manhwa/anime. 2) Criar título VS chamativo no topo com ffmpeg (texto vermelho bold). 3) Montar sequência de 4-8 painéis em slideshow (0.8-1.2s cada) com zoom sutil (ken burns). 4) Adicionar legendas fixas em português com palavras-chave destacadas em amarelo/verde (estilo do vídeo). 5) Inserir trilha épica/tensa do banco de 341 músicas. 6) Colocar branding no rodapé (nome da obra). 7) Exportar em 9:16 com ffmpeg.
- **Ferramentas:** ffmpeg, 86k painéis manhwa/anime, 341 trilhas música, overlays legendas
- **Material:** banco de 86 mil painéis de manhwa (extrair cenas de luta de Baki, Kengan Ashura, Hajime no Ippo, Record of Ragnarok)
- **Exemplo de roteiro:**

```
JACK HANMA VS PICKLE
[Painel 1: Pickle musculoso]
AS COSTAS E
[Painel 2: Tokugawa preocupado]
MAS ENQUANTO ELE
[Painel 3: Cidade]
O PICO TA
[Painel 4: Baki observando]
ESPERANDO...
```

- Tags: baki, anime, versus, luta, pickle, jackhanma

### legenda sincronizada com painéis de anime/manhwa + música dramática  -  potencial 9/10, esforco baixo  -  canal: manhwareact

- **Visto em:** 2026-10-07 13-54-53.mp4 (2026-10-12)
- **O que e:** Sequência de painéis estáticos de anime/manhwa com legendas sincronizadas contando uma história/curiosidade, sem narração, só música de fundo tensa. Cada painel aparece no timing exato da palavra-chave da legenda.
- **Por que viraliza:** Revela informação oculta/polêmica (censura) que o fã já conhece mas quer compartilhar + edição dinâmica prende até o final
- **Como fazer:** 1) Escolher curiosidade/lore de anime popular (ex.: censura, cena polêmica, backstory). 2) Escrever roteiro de 4-6 frases curtas e impactantes com LLM. 3) Selecionar 4-6 painéis do manhwa/anime dos 86 mil disponíveis que ilustrem cada frase. 4) Usar ffmpeg para montar vídeo: cada painel dura 2-3s, adicionar zoom sutil (scale + zoompan). 5) Sobrepor legendas amarelas estilo Hormozi (ass/srt) sincronizadas palavra por palavra. 6) Adicionar trilha tensa/épica das 341 disponíveis e SFX de tensão (whoosh, impacto) nos momentos-chave.
- **Ferramentas:** ffmpeg, 86mil painéis manhwa, legendas estilo Hormozi, 341 trilhas, 800 SFX
- **Material:** banco de 86 mil painéis de manhwa próprio + screenshots de anime de domínio público ou fair use educacional (análise/crítica)
- **Exemplo de roteiro:**

```
Kumi havia ENFRENTADO o monstro / Em VÁRIAS pequenas lutas / Desenvolvendo profundo RESPEITO por isso / Mas ninguém esperava o que viria / A cena foi CENSURADA em 12 países
```

- Tags: anime censurado, baki, curiosidade anime, cena proibida, lore anime, edit anime

### comparação power scaling com legendas dramaticas + cenas de luta  -  potencial 9/10, esforco baixo  -  canal: manhwareact

- **Visto em:** 2026-10-07 15-50-45.mp4 (2026-10-12)
- **O que e:** Video mostra confronto entre dois personagens/criaturas, com legendas destacando mecânicas de combate ("ao mesmo tempo", "do oponente", "escamas") em estilo kinetic typography. Ritmo rápido, cortes sincronizados com momentos de impacto visual.
- **Por que viraliza:** Power scaling e comparações "X vs Y" geram debate massivo nos comentários, e legendas kinetic prendem até o final por FOMO de perder a revelação
- **Como fazer:** 1) Extrair 4-6 painéis de manhwa de cenas de luta impactantes do seu acervo (86k painéis); 2) Gerar narração TTS dramatica explicando a comparação de poder/habilidades; 3) Adicionar legendas animadas estilo Hormozi com palavras-chave em amarelo nos momentos chave; 4) Aplicar overlays de fogo/raio nos impactos; 5) Adicionar SFX de explosão/impacto dos 800 SFX; 6) Montar com ffmpeg em ritmo acelerado (2-3s por painel)
- **Ferramentas:** ffmpeg, TTS, overlays animados, SFX, 86k painéis manhwa
- **Material:** painéis de manhwa do acervo (86 mil), especialmente cenas de batalha/confronto; geração IA para painéis adicionais se necessário
- **Exemplo de roteiro:**

```
"Serpente Gigante vs Cachorro Espiritual - QUEM VENCE?
[painel serpente] Invocação nível S, escamas impenetráveis
[painel cachorro] Mas o espírito canino tem ESTA habilidade secreta
[painel impacto] Velocidade de ataque 3x maior
[resultado] E o vencedor surpreende..."
```

- Tags: powerscaling, manhwa, comparação, versus, batalha, anime

### recap de cena de anime com legendas sincronizadas + música  -  potencial 9/10, esforco baixo  -  canal: cenareact

- **Visto em:** 2026-10-07 16-24-47.mp4 (2026-10-12)
- **O que e:** Mostra uma sequência de ação de anime (4-6 frames-chave) com legendas descritivas sincronizadas batendo com a ação, música de fundo intensa, sem narração falada. Ritmo rápido, cada legenda dura 0.8-1.2s.
- **Por que viraliza:** Revela uma sequência de ação surpreendente em câmera lenta narrativa, gerando curiosidade sobre qual anime é e vontade de compartilhar a cena épica.
- **Como fazer:** 1) Escolher cena icônica de anime usando pipeline de recap (extrair 4-6 frames da sequência). 2) Escrever legendas curtas e impactantes para cada momento ('E COLOCADA', 'POR DENTRO', 'DESMONTA', 'PEGA'). 3) Montar no ffmpeg: cada frame dura 1s, aplicar zoom sutil (scale e zoompan), adicionar legendas com drawtext em fonte bold/outline branco. 4) Adicionar trilha épica/tensa das 341 disponíveis. 5) Aplicar overlay de intensidade (raio/fogo) no momento climático. 6) Exportar 9:16, 10-15s.
- **Ferramentas:** ffmpeg, pipeline de recap de anime, overlays animados, 341 trilhas
- **Material:** frames extraídos de episódios de anime via pipeline de recap (cenas de domínio público ou fair use para análise), ou usar screencaps de anime de sites de fandom
- **Exemplo de roteiro:**

```
Frame 1 (0-1s): 'E COLOCADA' — espada de madeira surge
Frame 2 (1-2s): 'POR DENTRO' — close nos olhos determinados
Frame 3 (2-3.5s): 'DESMONTA' — espada corta outra espada ao meio
Frame 4 (3.5-5s): 'PEGA' — personagem vitoriosa, slow zoom out
[Trilha: épica crescente]
```

- Tags: anime, cena épica, espada, ação, recap

### meme narrativo com legendas progressivas + twist absurdo  -  potencial 9/10, esforco baixo  -  canal: novo canal: MemeDoAbsurdo

- **Visto em:** 2026-10-07 16-35-46.mp4 (2026-10-12)
- **O que e:** Sequência de frames com legendas curtas que constroem uma história absurda/nonsense, revelando um twist ridículo no final. Ritmo rápido, 3-5 segundos por frame, sem narração, só música de fundo e legendas sincronizadas.
- **Por que viraliza:** O setup cria expectativa de drama sério, mas o punchline absurdo (apagar fogo com xixi) quebra completamente e vira meme compartilhável
- **Como fazer:** 1) Gerar 4-6 imagens com IA (Gemini/Pollinations) seguindo roteiro absurdo; 2) Adicionar legendas brancas centralizadas em cada frame (ffmpeg drawtext); 3) Timing: 2-4s por frame com transições rápidas; 4) Música de suspense/comédia de fundo (das 341 trilhas); 5) SFX de impacto no twist final (dos 650 sons de meme); 6) Overlay de efeito (confete/raio) no punchline
- **Ferramentas:** Gemini/Pollinations, ffmpeg, sons de meme, trilhas de música, overlays animados
- **Material:** Geração de imagens por IA seguindo prompt de cenário absurdo + estética de filme/novela antiga
- **Exemplo de roteiro:**

```
Frame 1: 'HOMENS' (close dramático)
Frame 2: 'ATÉ' (pedra rolando)
Frame 3: 'ROLOU' (pedra gigante)
Frame 4: 'MIM' (personagem nu de costas)
Frame 5: [TWIST] 'E EU APAGUEI O FOGO ASSIM' (ação absurda + SFX + overlay de fogo)
```

- Tags: meme brasileiro, comedia absurda, plot twist, shitpost, zoeira, meme narrativo

### meme de anime com legenda word-by-word sincronizada  -  potencial 9/10, esforco baixo  -  canal: manhwareact

- **Visto em:** 2026-10-07 16-39-25.mp4 (2026-10-12)
- **O que e:** Pega cenas de anime/manhwa, adiciona legenda que aparece palavra por palavra (estilo karaokê) contando uma piada ou situação relatable. Ritmo rápido, punchline visual no final.
- **Por que viraliza:** Timing perfeito entre legenda e imagem cria dopamina; todo mundo se identifica com piadas de 'ficou rico' ou 'perdeu tudo'
- **Como fazer:** 1) Escolher 3-5 frames de anime/manhwa dos 86 mil painéis que combinem com a narrativa. 2) Escrever roteiro curto (15-20 palavras) com setup + punchline sobre dinheiro/relacionamento/escola. 3) Gerar legendas sincronizadas palavra por palavra no ffmpeg com efeito de surgimento (0.2s por palavra). 4) Adicionar trilha phonk/drill brasileira de fundo. 5) Overlay de dinheiro/efeitos no frame final (confete, brilho). 6) Exportar 9:16 com texto grande estilo impact branco com borda preta.
- **Ferramentas:** ffmpeg, paineis-manhwa, trilhas-musica, overlays-animados
- **Material:** 86 mil painéis de manhwa já disponíveis; selecionar expressões faciais que casem com a narrativa (surpresa, felicidade, dinheiro caindo)
- **Exemplo de roteiro:**

```
ELE É MILIONÁRIO AGORA... 😂
SEU / PAGAR / COMO
[Frame 1: gaveta de dinheiro]
[Frame 2: personagem pagando]
[Frame 3: personagem sorrindo]
[Frame 4: personagem deitado em pilha de dinheiro com efeito de confete]
```

- Tags: meme-anime, legenda-sincronizada, anime-brasileiro, manhwa-meme, rico-pobre, relatable

### unboxing silencioso + demo de produto tech com legendas  -  potencial 8/10, esforco baixo  -  canal: novo canal: TechReactBR

- **Visto em:** 2026-10-01 11-33-49.mp4 (2026-10-01)
- **O que e:** Vídeo mostra produto tech (projetor portátil) sendo desembalado, manuseado e testado em tempo real, com legendas descrevendo cada etapa. Sem narração, apenas música ambiente e texto na tela guiando o espectador pelos recursos do produto.
- **Por que viraliza:** Curiosidade sobre produto inovador + formato 'satisfying' de ver tecnologia funcionando + aspiração de compra
- **Como fazer:** 1. Gerar imagens IA do produto (projetor, gadget tech) em diferentes ângulos e cenários de uso. 2. Criar sequência: produto na caixa → mãos segurando → detalhes técnicos → tela projetada com conteúdo (Netflix, YouTube). 3. Adicionar legendas descritivas em cada frame ('mas até que dá pra levar numa bolsa grande', 'resolução máxima', 'caraca esse aqui é top do top hein'). 4. Trilha de fundo tech/moderna. 5. Montar com ffmpeg: transições rápidas (0.8-1.5s por frame), zoom sutil em detalhes importantes. 6. Overlay de ícones animados (Wi-Fi, resolução 4K, apps) nos momentos-chave.
- **Ferramentas:** ffmpeg, geracao-imagem-IA, overlays-animados, trilhas-musica
- **Material:** Imagens geradas por IA (Gemini/Pollinations) de produtos tech + screenshots de interfaces (Netflix, YouTube) via Playwright + overlays de ícones tech animados
- **Exemplo de roteiro:**

```
Frame 1: 'Testei esse PROJETOR PORTÁTIL que cabe na mochila 🎒'
Frame 2: 'Olha o tamanho dessa parada... cabe na palma da mão'
Frame 3: 'Conecta direto na Netflix, YouTube, Disney+'
Frame 4: 'Resolução MÁXIMA em 4K, parece cinema'
Frame 5: 'Preço? Bem mais barato que uma TV grande 💰'
```

- Tags: tech, unboxing, gadget, projetor, inovacao, aspiracional

### montagem de produto + legenda step-by-step com música ambiente  -  potencial 8/10, esforco baixo  -  canal: novo canal: 'InventoReact' (se focar em gadgets/invenções) ou criar 'IdeiasGeniais' (life hacks + produtos inteligentes)

- **Visto em:** 2026-10-01 11-44-04.mp4 (2026-10-01)
- **O que e:** Vídeo mostra a montagem/transformação de um produto (cama-cabine) em time-lapse com legendas em chinês narrando cada etapa. Sem narração falada, só música de fundo. Prende pela satisfação visual do antes/depois e utilidade prática.
- **Por que viraliza:** Satisfação visual de transformação + utilidade prática que faz o espectador pensar 'eu preciso disso' ou 'vou mostrar pra alguém'
- **Como fazer:** 1) Gerar sequência de imagens IA mostrando produto desmontado → etapas de montagem → produto final (ou usar fotos de produtos reais via Playwright/scraping); 2) Criar legendas em português para cada etapa (ex: 'Primeiro encaixe as laterais', 'Agora fixe a estrutura'); 3) Montar time-lapse com ffmpeg, acelerando transições; 4) Adicionar trilha musical ambiente (das 341 disponíveis); 5) Sobrepor legendas estilo Hormozi (amarelo com borda preta); 6) Opcional: SFX de 'clique' ou 'encaixe' nas transições.
- **Ferramentas:** ffmpeg, geração de imagem IA, overlays de legenda, trilhas musicais, Playwright
- **Material:** imagens de produtos via Pollinations/Gemini (móveis, gadgets, organização); fotos de e-commerce via Playwright; ou fotos próprias de produtos montáveis
- **Exemplo de roteiro:**

```
【Transforme seu quarto em 5 minutos】
→ Encaixe a estrutura principal
→ Fixe as laterais com travas
→ Monte a escada modular
→ Instale cortina de privacidade
→ Pronto: seu quarto privativo! 💡
```

- Tags: life hack, organização, produto genial, transformação, satisfying, útil

### slideshow de anime com trilha emotiva  -  potencial 8/10, esforco baixo  -  canal: cenareact

- **Visto em:** 2026-10-01 13-08-45.mp4 (2026-10-01)
- **O que e:** Sequência de frames estáticos de anime/manhwa com zoom lento, música de fundo emotiva/épica, sem narração. Ritmo contemplativo focado na expressão dos personagens.
- **Por que viraliza:** Nostalgia + trilha emotiva cria loop hipnótico; fãs de anime param para identificar personagens e reviver momentos marcantes
- **Como fazer:** 1) Selecionar 8-12 painéis de manhwa/anime do acervo (86k disponíveis) com expressões marcantes; 2) Aplicar efeito Ken Burns (zoom/pan suave) com ffmpeg; 3) Adicionar trilha emotiva/épica da biblioteca (341 disponíveis); 4) Sincronizar transições com beats da música; 5) Aplicar overlays sutis (brilho, partículas) nos momentos-chave; 6) Renderizar em 9:16 com ffmpeg
- **Ferramentas:** ffmpeg, painéis manhwa, trilhas musicais, overlays animados
- **Material:** acervo próprio de 86 mil painéis de manhwa + frames extraídos de anime (fair use para análise/comentário)
- **Exemplo de roteiro:**

```
🎭 Quando você percebe que ele SEMPRE soube...

[Frame 1: Subaru sério]
[Frame 2: Close no olhar]
[Frame 3: Personagem secundária]
[Frame 4: Revelação]

💔 Re:Zero me destruiu
```

- Tags: anime, rezero, momentos-marcantes, edit, amv, feels

### react a produto/técnica de construção com narração explicativa  -  potencial 8/10, esforco baixo  -  canal: novo canal: ConstruReact (foco em inovações de construção, materiais, técnicas)

- **Visto em:** 2026-10-01 16-19-51.mp4 (2026-10-01)
- **O que e:** Mostra um processo satisfatório (aplicação de granito líquido) com narração comentando benefícios, facilidade e resultado final. Retenção vem do oddly satisfying + promessa de 'futuro' + simplicidade.
- **Por que viraliza:** Oddly satisfying + promessa de inovação ('piso do futuro') + simplicidade aparente gera curiosidade e compartilhamento por quem reforma casa
- **Como fazer:** 1) Buscar vídeos de domínio público ou gerar com IA (Veo 3) mostrando processos satisfatórios: aplicação de resina, massa niveladora, pintura autonivelante, etc. 2) Criar roteiro com LLM destacando benefícios ('fácil aplicação', 'resistente', 'várias cores'). 3) Gerar narração com TTS (ElevenLabs ou edge-tts) em tom entusiasmado. 4) Adicionar legenda fixa no centro inferior com nome do produto/técnica. 5) Inserir overlay de marca d'água de produto fictício ou genérico. 6) Música de fundo neutra das 341 trilhas.
- **Ferramentas:** Veo 3, LLM, TTS, ffmpeg, overlays de legenda
- **Material:** vídeos de domínio público (Pexels, Pixabay) de construção/reforma, ou geração com Veo 3 de processos satisfatórios (líquido sendo espalhado, superfície ficando lisa)
- **Exemplo de roteiro:**

```
Você já ouviu falar no granito líquido? O piso do futuro! Olha que fácil de aplicar, é só espalhar. Alto nivelante, resistente, e ainda tem várias cores. Perfeito pra áreas internas. O que você acha? Eu acho que o futuro dos pisos é esse!
```

- Tags: granito líquido, construção, reforma, oddly satisfying, inovação, DIY

### timelapse de forja artesanal com narração IA comentando processo  -  potencial 8/10, esforco medio  -  canal: novo canal: ForjaLendária

- **Visto em:** 2026-10-01 17-51-13.mp4 (2026-10-02)
- **O que e:** Mostra o processo acelerado de forjar uma espada famosa (ex.: Senhor dos Anéis) a partir de material improvisado (mola de carro), com narração IA explicando cada etapa e curiosidades. Ritmo rápido, foco na transformação visual do metal bruto até peça final.
- **Por que viraliza:** Satisfação de ver transformação manual + nostalgia de armas icônicas + admiração por habilidade artesanal
- **Como fazer:** 1. Buscar vídeos CC0/domínio público de forja artesanal ou gerar clipes com Veo 3 simulando etapas (corte, aquecimento, martelagem, polimento). 2. Criar roteiro com LLM detalhando processo de forja de réplica icônica (espadas de anime/games/filmes). 3. Gerar narração com ElevenLabs PT-BR (voz masculina técnica/empolgada). 4. Editar com ffmpeg: timelapse acelerado (2-3x), overlays de fogo/faíscas nos momentos de forja, zoom dramático no resultado final. 5. Adicionar SFX de metal batendo, fogo, e trilha épica dos 341 disponíveis. 6. Legenda estilo Hormozi destacando materiais ('MOLA DE CARRO', 'FOGO 1200°C').
- **Ferramentas:** Veo 3, LLM, ElevenLabs, ffmpeg, overlays animados, SFX, trilhas
- **Material:** Vídeos CC0 de ferreiros/artesãos (Pexels, Pixabay), clipes gerados por Veo 3 simulando etapas de forja, imagens de referência das espadas icônicas (wikis, fan art domínio público)
- **Exemplo de roteiro:**

```
🔥 FORJANDO A ESPADA DO KRATOS COM MOLA DE CAMINHÃO
[Cena: mola sendo cortada] 'Pegamos 80kg de aço de mola...'
[Fogo intenso] '...aquecemos a 1200 graus no forno caseiro...'
[Martelagem] '...300 marteladas pra moldar a lâmina...'
[Polimento] '...e 6 horas de lixamento até o espelho.'
[Resultado final] 'Leviathan Axe feita em casa. Próxima: Excalibur?'
```

- Tags: forja, espadas, artesanato, DIY, satisfying, senhor dos anéis

### montagem nostálgica de console com trilha e legendas  -  potencial 8/10, esforco baixo  -  canal: novo canal: retrogamespt

- **Visto em:** 2026-10-02 15-32-43.mp4 (2026-10-02)
- **O que e:** Vídeo visual mostrando PlayStation 2, memory card, jogos e interface do console com legendas curtas e música ambiente. Ritmo rápido, cortes secos entre elementos icônicos, gatilho de nostalgia pura.
- **Por que viraliza:** Nostalgia instantânea + identificação geracional ('eu tinha isso') gera comentários e compartilhamentos massivos
- **Como fazer:** 1) Gerar imagens de PS2, memory cards, jogos clássicos via IA ou buscar fotos livres de direitos; 2) Capturar tela de interface PS2 via emulador (PCSX2) ou vídeos no YouTube; 3) Montar no ffmpeg com cortes rápidos (2-3s por elemento), adicionar legendas minimalistas ('modernos', números, nomes de jogos); 4) Sobrepor trilha nostálgica dos 341 tracks disponíveis; 5) Adicionar overlay de scan lines ou efeito CRT para reforçar nostalgia
- **Ferramentas:** ffmpeg, geração de imagem IA, Playwright, overlays animados
- **Material:** fotos de domínio público (Wikimedia Commons), prints de emulador PCSX2, geração IA de consoles/jogos, vídeos CC0 do Pexels
- **Exemplo de roteiro:**

```
Frame 1: [Interface PS2 com lista de jogos] 'Quem lembra disso?'
Frame 2: [Memory card sendo inserido] 'modernos'
Frame 3: [Capa de GTA San Andreas] 'Qual era o SEU jogo?'
Frame 4: [PS2 ligando] 'Coração acelerou agora'
Legenda: 'POV: você tem 28 anos 🎮💔'
```

- Tags: nostalgia, ps2, anos2000, memorycard, retrogaming, infancia

### experimento científico caseiro com teste prático passo a passo  -  potencial 8/10, esforco medio  -  canal: novo canal: ExperimentoBR

- **Visto em:** 2026-10-02 15-40-10.mp4 (2026-10-02)
- **O que e:** Mostra um experimento DIY (separar álcool de gasolina) com narração técnica explicando cada etapa, seguido de teste real pra provar se funciona. Estrutura: problema → solução técnica → momento da verdade.
- **Por que viraliza:** Curiosidade científica + payoff imediato ('será que funciona?') + valor prático que faz o espectador assistir até o fim.
- **Como fazer:** 1) LLM gera roteiro de experimento caseiro verificável (química, física, mecânica); 2) Gemini/Pollinations cria imagens dos materiais e etapas do processo; 3) Veo 3 gera clipes curtos de 'mãos realizando' (ou usa stock footage + zoom dramático); 4) TTS narra cada passo com tom didático; 5) Adiciona SFX de tensão no 'teste final' + overlay de fogo/raio no clímax; 6) ffmpeg monta com cortes rápidos (3-5s por etapa) e música de suspense.
- **Ferramentas:** LLM, Gemini/Pollinations, Veo 3, TTS, ffmpeg, SFX, overlays animados, trilhas
- **Material:** Imagens IA de objetos/processos, Pexels/Pixabay pra B-roll de materiais, Veo 3 pra 'mãos trabalhando', stock footage de testes (fogo, água, reações)
- **Exemplo de roteiro:**

```
NARRAÇÃO: 'Você sabia que dá pra separar o álcool da gasolina só com água? Vou provar. Passo 1: misture gasolina comum com água limpa numa garrafa. Passo 2: agite bem e deixe descansar 10 minutos. Repare: o álcool vai pro fundo com a água. Passo 3: retire a camada de cima — gasolina pura. Agora o teste: coloquei na minha moto. Será que pega? [SFX tensão] FUNCIONOU! Segue pra mais experimentos.'
```

- Tags: experimento caseiro, ciência DIY, gasolina pura, teste real, curiosidade científica, lifehack

### meme narrativo de anime com legenda e musica  -  potencial 8/10, esforco baixo  -  canal: manhwareact

- **Visto em:** 2026-10-02 15-49-05.mp4 (2026-10-02)
- **O que e:** História curta e cômica contada através de cenas de anime sequenciais com legendas em português, sem narração, apenas música de fundo. Estrutura de setup-punchline visual com timing de meme.
- **Por que viraliza:** Formato de meme já validado no TikTok/Shorts BR, relatável, rewatchable e altamente compartilhável por ser curto e ter punchline forte
- **Como fazer:** 1. Selecionar 3-5 frames de anime/manhwa do banco de 86 mil painéis que formem uma sequência cômica; 2. Escrever roteiro curto com LLM (setup + reviravolta engraçada) estilo meme brasileiro; 3. Adicionar legendas brancas com borda preta em cada frame usando ffmpeg; 4. Escolher trilha sonora adequada ao mood (suspense/comédia) das 341 disponíveis; 5. Montar sequência com ffmpeg ajustando timing (2-3s por frame, acelerar no punchline); 6. Adicionar SFX de impacto no momento da reviravolta
- **Ferramentas:** ffmpeg, LLM para roteiro, paineis de manhwa/anime, trilhas musicais, SFX
- **Material:** 86 mil painéis de manhwa já disponíveis + frames de anime de domínio público ou fair use para memes
- **Exemplo de roteiro:**

```
Frame 1: 'ELAS MEXERAM COM A GAROTA ERRADA...'
Frame 2: 'JOGOU A MENINA' [cena de bullying]
Frame 3: 'PRA ELAS' [garotas rindo]
Frame 4: 'AS GAROTAS' [zoom dramático]
Frame 5: 'MACHUCAR AS GAROTAS' [reviravolta - eram as vilãs] + SFX de impacto
```

- Tags: meme de anime, anime br, plot twist, anime engraçado, shorts de anime, relatável

### compilado de situações cotidianas frustrantes com narração e legendas  -  potencial 8/10, esforco baixo  -  canal: novo canal: FrustradoBR

- **Visto em:** 2026-10-02 15-51-00.mp4 (2026-10-02)
- **O que e:** Sequência rápida de vídeos mostrando situações do dia a dia que dão errado (produto enganoso, objeto quebrado, expectativa vs realidade), com narração relatando a frustração e legendas destacando o momento chave.
- **Por que viraliza:** Identificação imediata com frustrações universais do consumidor brasileiro (produto enganoso, coisa que quebra, expectativa vs realidade).
- **Como fazer:** 1. Coletar vídeos curtos de situações frustrantes (Pexels, Pixabay, ou gravar simulações simples com objetos do dia a dia). 2. Escrever roteiro com LLM narrando cada situação em tom de desabafo/comédia. 3. Gerar narração com TTS brasileiro (edge-tts ou ElevenLabs). 4. Adicionar legendas estilo Hormozi nos momentos de punchline ('olha isso', 'era só papel'). 5. Inserir sons de meme (suspense, decepção, 'au au au') e música de fundo cômica. 6. Montar sequência rápida no ffmpeg (3-4 clipes de 5-8s cada).
- **Ferramentas:** ffmpeg, TTS, sons de meme, overlays animados, LLM para roteiro
- **Material:** Vídeos de stock (Pexels, Pixabay), gravações próprias de objetos/situações simuladas, ou clipes de domínio público de situações cotidianas
- **Exemplo de roteiro:**

```
Comprei esse bife de 13 reais, achei que tava arrasando. Tirei o plástico... olha isso aqui, gente. Era só papel embaixo! Dois bifes minúsculos pelo preço de um churrasco. Brasil sendo Brasil. [corte] Peguei esse carrinho no mercado, parecia novinho. Fui empurrar e... a alça saiu na minha mão. Nem cheguei no caixa ainda!
```

- Tags: cotidiano brasileiro, expectativa vs realidade, produto enganoso, situações frustrantes, humor brasileiro, relatable

### Quiz visual de anime com legendas dinâmicas  -  potencial 8/10, esforco baixo  -  canal: cenareact

- **Visto em:** 2026-10-03 13-19-24.mp4 (2026-10-04)
- **O que e:** Vídeo em formato de pergunta-resposta visual sobre um anime específico. Mostra frames do anime com legendas amarelas em negrito revelando conceitos/elementos da trama em ritmo rápido. Estrutura: pergunta inicial → revelação progressiva de 3-5 elementos-chave com palavras isoladas.
- **Por que viraliza:** Loop de curiosidade: faz o espectador querer descobrir a resposta e testar conhecimento, ideal para fãs de anime competirem nos comentários
- **Como fazer:** 1) Escolher anime/manhwa do acervo de 86 mil painéis; 2) Gerar roteiro com LLM: 1 pergunta + 4-5 respostas curtas (conceitos, personagens, plot points); 3) Selecionar frames correspondentes ou gerar com IA; 4) Adicionar legendas amarelas estilo Hormozi com ffmpeg; 5) TTS em PT para narração da pergunta inicial; 6) Trilha épica de fundo + SFX de transição entre frames; 7) Render vertical 9:16 com ffmpeg.
- **Ferramentas:** ffmpeg, TTS, LLM, painéis de manhwa, overlays de legenda, trilhas, SFX
- **Material:** 86 mil painéis de manhwa do acervo; frames de anime de domínio público ou fair use educacional; geração IA para conceitos abstratos (ex.: 'universo costurado')
- **Exemplo de roteiro:**

```
🎬 PERGUNTA: Você sabe o que é Moshikoten-sei?
📌 Frame 1: ENTIDADE (personagem em luz)
📌 Frame 2: COSTUMAVA (porta dimensional)
📌 Frame 3: VIVER (silhueta no cosmos)
📌 Frame 4: NO UNIVERSO COSTURADO 🌌
💬 Comenta aí se acertou!
```

- Tags: anime quiz, moshikoten-sei, teste seu conhecimento, cultura otaku, anime explicado, curiosidades anime

### recap de cena de anime com legendas sincronizadas  -  potencial 8/10, esforco baixo  -  canal: cenareact

- **Visto em:** 2026-10-03 13-23-06.mp4 (2026-10-04)
- **O que e:** Cena curta de anime (15-30s) com legendas brancas sincronizadas ao diálogo, zoom dinâmico nos personagens e cortes rápidos entre frames. Ritmo ágil, sem narração extra, só o áudio original.
- **Por que viraliza:** Nostalgia + diálogo icônico + legendas que facilitam compartilhamento em grupos de fãs de anime.
- **Como fazer:** 1. Extrair cena curta de episódio com ffmpeg (15-30s, momento icônico/engraçado). 2. Gerar legendas em português com timing preciso (edge-tts para transcrever se necessário, ou escrever manualmente). 3. Aplicar zoom dinâmico e cortes entre frames com ffmpeg (filtros scale, crop, setpts para slow-motion em momentos-chave). 4. Sobrepor legendas estilo Hormozi (brancas, bold, outline preto) com ffmpeg drawtext. 5. Adicionar SFX nos momentos de impacto (boom, whoosh) e trilha de fundo sutil se necessário. 6. Renderizar vertical 9:16.
- **Ferramentas:** ffmpeg, edge-tts, SFX, trilhas, overlays legendas
- **Material:** episódios de anime (Dragon Ball Super, Naruto, One Piece) via pipeline de recap existente ou download de episódios para banco local
- **Exemplo de roteiro:**

```
🔥 Quando o Bills cansou da barulheira dos Saiyajins 😂

[Cena: Bills expulsando Goku e Vegeta]
Bills: 'Vou mandar vocês embora!'
Goku: 'Pra onde?!'
Bills: 'Pro inferno! 😡'

#DragonBallSuper #Bills #Goku
```

- Tags: dragon ball, anime recap, bills, goku, cena iconica, nostalgia

### história moral com legendas palavra-chave + clipe viral  -  potencial 8/10, esforco baixo  -  canal: novo canal: MoralReels (ou adaptar para cenareact se usar clipes de filmes/séries)

- **Visto em:** 2026-10-03 13-27-42.mp4 (2026-10-04)
- **O que e:** Pega um clipe viral (confusão, acidente, momento inesperado) e narra uma micro-história com legenda sincronizada destacando palavras-chave emocionais (PERCEBEU, ANTIGA, COMEÇOU, PERDIDO). Ritmo rápido, cortes a cada 2-3s, foco na reviravolta moral.
- **Por que viraliza:** Reviravolta emocional + lição moral em 20s = loop infinito e compartilhamento ('olha que história linda').
- **Como fazer:** 1) Buscar clipes virais curtos (15-40s) em subs do Reddit (r/HumansBeingBros, r/JusticeServed) ou Pexels. 2) Escrever roteiro de 4-6 frases com gancho moral (honestidade, karma, reviravolta). 3) Gerar narração TTS (ElevenLabs ou edge-tts, voz masculina séria). 4) Adicionar legendas estilo Hormozi com palavras-chave em caps + efeito de zoom/shake. 5) Inserir trilha dramática (suspense ou épica) dos 341 arquivos. 6) Cortar o clipe em jump cuts a cada mudança de frase (ffmpeg) para manter ritmo frenético.
- **Ferramentas:** ffmpeg, edge-tts ou ElevenLabs, overlays animados (legendas Hormozi), trilhas de música, SFX (whoosh, impact)
- **Material:** clipes virais de domínio público (Pexels, Pixabay), vídeos CC do YouTube, subs do Reddit (r/PublicFreakout, r/MadeMeSmile), IA generativa (Veo 3) para recriar cenas se necessário
- **Exemplo de roteiro:**

```
Um homem foi confundido com moto-táxi. PERCEBEU o erro quando já estava longe. A maioria guardaria o dinheiro. Mas ele VOLTOU. Honestidade ANTIGA que o mundo PERDEU. Esse é o cara que você quer por perto.
```

- Tags: histórias reais, honestidade, fé na humanidade, reviravolta, lição de vida, viral

### recap cinematográfico com legendas dinâmicas + música tensa  -  potencial 8/10, esforco medio  -  canal: novo canal: ThrillerzBR

- **Visto em:** 2026-10-04 08-29-30.mp4 (2026-10-04)
- **O que e:** Sequência de cenas de filme/série editadas com cortes rápidos, legendas sincronizadas contando a história, trilha sonora que amplifica tensão. Foco em momentos de plot twist, confronto ou revelação de personagem.
- **Por que viraliza:** Micro-narrativa com gancho imediato + estética de filme real + cliffhanger que força rewatch e comentários especulando o final
- **Como fazer:** 1) Gerar sequência de imagens cinematográficas com Veo 3 ou Pollinations (estética de thriller asiático: iluminação fria, personagem tenso, cenários urbanos noturnos). 2) Escrever roteiro de micro-história em 4-6 beats (ex.: assassino recebe ligação → sai de casa → persegue alvo → confronto → desfecho). 3) Gerar narração TTS Edge/ElevenLabs com tom dramático, ou usar só legendas + SFX de tensão. 4) Montar no ffmpeg: transições rápidas (0.8-1.2s por frame), legendas estilo Netflix (brancas com sombra preta), overlays de glitch/scanlines nos momentos de tensão. 5) Trilha de suspense das 341 disponíveis + SFX de passos, porta, respiração. 6) Thumbnail: close do rosto tenso + texto 'ELE VOLTOU'.
- **Ferramentas:** Veo 3, Pollinations, ffmpeg, TTS, overlays animados, trilhas de suspense, SFX
- **Material:** Veo 3 para gerar cenas originais estilo filme noir/thriller coreano; Pollinations para stills alternativos; fotos do criador editadas como 'ator' se quiser personalizar
- **Exemplo de roteiro:**

```
Frame 1: 'Ele saiu da cadeia depois de 10 anos' [homem magro, olhar vazio]
Frame 2: 'Mas alguém não queria que ele voltasse' [carro seguindo à noite]
Frame 3: 'A ligação mudou tudo' [celular vibrando, mão tremendo]
Frame 4: 'Agora ele vai terminar o que começou' [close nos olhos, música explode]
```

- Tags: thriller, suspense, história original, plot twist, cinematográfico, curta ficcional

### recap de anime com legendas sincronizadas + música  -  potencial 8/10, esforco baixo  -  canal: cenareact

- **Visto em:** 2026-10-04 08-35-58.mp4 (2026-10-04)
- **O que e:** Sequência rápida de cenas de anime (3-5 segundos cada) com legendas curtas sincronizadas contando a história ou destacando momentos-chave, música ambiente sem narração, ritmo acelerado tipo TikTok.
- **Por que viraliza:** Nostalgia + curiosidade sobre anime novo + legendas que criam suspense e fazem o espectador assistir até o fim pra entender a história
- **Como fazer:** 1) Baixar trailer/cenas do anime (YouTube, sites oficiais) ou usar frames do seu pipeline de recap. 2) Gerar roteiro curto com LLM (5-8 frases resumindo plot/momento viral). 3) Cortar cenas em 3-4s cada no ffmpeg, aplicar zoom/pan com filtros. 4) Adicionar legendas animadas (estilo Hormozi) com texto do roteiro sincronizado. 5) Mixar trilha épica/dramática das 341 disponíveis. 6) Exportar vertical 9:16.
- **Ferramentas:** ffmpeg, LLM para roteiro, overlays animados, trilhas musicais, pipeline recap anime
- **Material:** trailers oficiais YouTube, frames do pipeline de recap existente, cenas promocionais sem copyright
- **Exemplo de roteiro:**

```
MESMO // DA VIDA // SEU CORPO // UM DOS CRISTAIS // ELA SACRIFICOU TUDO // MAS O DESTINO TEM OUTROS PLANOS
```

- Tags: anime2025, recapanime, animerecomendacao, animenovo, otaku, animebr

### recap narrado de dorama curto chinês com legendas dinâmicas  -  potencial 8/10, esforco medio  -  canal: cenareact

- **Visto em:** 2026-10-04 10-49-08.mp4 (2026-10-04)
- **O que e:** Narração em português resume plot twist de minidrama asiático (isekai/reencarnação) em 30-60s, com legendas palavra-por-palavra sincronizadas, cortes rápidos nas viradas de cena e música dramática.
- **Por que viraliza:** Plot twists absurdos + narração acelerada + cliffhanger = loop infinito de 'o que acontece depois?' em nichos de dorama/isekai.
- **Como fazer:** 1) Escolher dorama curto chinês disponível no YouTube (domínio público ou creative commons) e baixar cenas-chave com yt-dlp; 2) Gerar roteiro de recap com LLM focando em plot twists e vingança/reencarnação; 3) TTS em português (ElevenLabs ou edge-tts voz feminina dramática) para narração; 4) ffmpeg para cortar cenas nos momentos de tensão (close-ups, revelações); 5) Adicionar legendas palavra-por-palavra estilo Hormozi com overlays animados (brilho dourado, fogo) nos picos dramáticos; 6) Trilha de suspense/drama + SFX de impacto nos plot twists.
- **Ferramentas:** ffmpeg, TTS, LLM, overlays animados, trilhas de música, SFX
- **Material:** minidramas chineses no YouTube (públicos ou CC), cenas de doramas curtos verticalizados, ou vídeos de recaps já existentes re-editados
- **Exemplo de roteiro:**

```
Ela escolheu o ovo dourado, mas nasceu um inseto feio. Todos riram. Mas ela cortou o próprio peito, derramou sangue no bicho... e ele virou um príncipe celestial! A irmã invejosa causou uma tragédia — mas as duas reencarnaram no MESMO DIA. Agora é a vingança.
```

- Tags: dorama, isekai, reencarnação, plot twist, vingança, recap

### recap dramatizado de filme curto asiático com legendas e narração  -  potencial 8/10, esforco medio  -  canal: cenareact

- **Visto em:** 2026-10-04 10-59-17.mp4 (2026-10-04)
- **O que e:** Narração em português de filme curto chinês de reencarnação, com legendas sincronizadas, cortes rápidos nas cenas-chave e música dramática de fundo. Estrutura: introdução do conflito → escalada de tensão → reviravolta → resolução satisfatória.
- **Por que viraliza:** Drama + reviravolta + resolução satisfatória em 60s ativa o loop de dopamina; público adora ver vilão se ferrando e protagonista vencendo.
- **Como fazer:** 1) Baixar filme curto asiático de reencarnação (YouTube, bilibili, domínio público chinês); 2) Extrair cenas-chave com ffmpeg (8-12 cortes de 2-4s cada); 3) Escrever roteiro de recap com LLM (foco em drama, reviravolta, satisfação); 4) Gerar narração TTS em português (ElevenLabs ou edge-tts com voz dramática); 5) Adicionar legendas estilo Hormozi sincronizadas com palavras-chave ("envenenada", "descoberto", "vingança"); 6) Camada de música dramática asiática (das 341 trilhas) + SFX de tensão nos momentos de pico; 7) Renderizar com ffmpeg (9:16, 40-60s).
- **Ferramentas:** ffmpeg, TTS, LLM, overlays legendas, trilhas musicais, SFX
- **Material:** filmes curtos asiáticos de plataformas chinesas (YouTube, bilibili, ReelShort, FlexTV) — maioria sem copyright rígido ou uso educacional/comentário
- **Exemplo de roteiro:**

```
🔥 ELA RENASCEU E DESCOBRIU QUE A MÃE ESTAVA SENDO ENVENENADA
🍼 Quando a mãe foi dar o leite, Emma derrubou tudo e começou a chorar
👴 O avô percebeu que algo estava errado e ordenou exames
⚡ A vilã tentou fugir, mas foi PEGA e expulsa da família
✨ Desta vez, Emma conseguiu MUDAR seu destino
```

- Tags: reencarnacao, drama-asiatico, filme-curto, vinganca, plot-twist, satisfacao-garantida

### história animada com legendas e música de fundo  -  potencial 8/10, esforco baixo  -  canal: novo canal: VidaCotidianaAnimada

- **Visto em:** 2026-10-06 10-14-11.mp4 (2026-10-06)
- **O que e:** Narrativa visual simples usando ilustrações estilo cartoon com legendas sincronizadas contando uma história cotidiana (criança chamando os pais). Ritmo rápido, cortes a cada 1-2 segundos, sem narração.
- **Por que viraliza:** Nostalgia + humor relatable de situações da infância que todo mundo viveu, formato digestível com punchline visual
- **Como fazer:** 1) Gerar 4-8 ilustrações estilo cartoon com Gemini/Pollinations (personagens simples, cenários minimalistas); 2) Criar legendas curtas e diretas para cada frame (ex: 'PAPAIÊÊÊ!', 'EM CIMA DA CAMA'); 3) Montar sequência no ffmpeg com cada imagem durando 1-2s; 4) Adicionar trilha de suspense/comédia das 341 disponíveis; 5) Sobrepor legendas com estilo bold/outline usando ffmpeg drawtext; 6) Opcional: adicionar SFX de passos, porta, etc.
- **Ferramentas:** Gemini/Pollinations, ffmpeg, biblioteca de músicas, SFX
- **Material:** geração de imagem por IA (prompts de personagens cartoon simples + cenários domésticos), legendas escritas manualmente ou por LLM
- **Exemplo de roteiro:**

```
[Frame 1: Criança gritando na cama] 'MAMÃEEE!' [Frame 2: Pai subindo escada] 'Que foi?' [Frame 3: Criança apontando] 'TEM UM MONSTRO EMBAIXO DA CAMA' [Frame 4: Pai olhando embaixo] 'Não tem nada aqui' [Frame 5: Sombra assustadora] 'Ou será que tem?'
```

- Tags: histórias animadas, relatable, infância, cartoon brasileiro, nostalgia, humor cotidiano

### sitcom animada com diálogo + legendas + timing cômico  -  potencial 8/10, esforco medio  -  canal: novo canal: VidaCotidianaAnimada ou ComedyCartoonBR

- **Visto em:** 2026-10-06 10-15-06.mp4 (2026-10-06)
- **O que e:** História curta em formato de sitcom com personagens animados simples, diálogo entre pai e filha, timing de comédia (criança dorme e esquece tudo), legendas integradas na animação. Estrutura: setup → pausa/sono → punchline.
- **Por que viraliza:** Situações relacionáveis de pais com filhos pequenos + timing cômico perfeito + formato visual limpo que segura até o punchline
- **Como fazer:** 1) Escrever roteiro curto (10-20s) de situação cômica familiar/cotidiana com LLM; 2) Gerar 4-6 frames de personagens animados (estilo cartoon simples) via Gemini/Pollinations com prompts consistentes (mesmos personagens, ângulos diferentes); 3) Adicionar legendas hardcoded nas imagens (ffmpeg drawtext ou overlay pré-renderizado); 4) Narrar diálogo com TTS (edge-tts ou ElevenLabs, vozes diferentes para pai/filha); 5) Montar sequência com ffmpeg: imagem estática para cada fala (2-4s), transições rápidas; 6) Adicionar SFX de sono (ronco, bocejo) e música de fundo suave de comédia
- **Ferramentas:** LLM, Gemini/Pollinations, ffmpeg, edge-tts ou ElevenLabs, SFX
- **Material:** Geração de imagem IA (personagens cartoon originais), roteiros criados por LLM baseados em situações do dia a dia, SFX da biblioteca de 650 sons de meme + 800 SFX
- **Exemplo de roteiro:**

```
[CARRO - PAI DIRIGINDO]
Pai: Júlia, olha ali! Tá escrito 'Rua 21 de Abril'.
[JÚLIA DORMINDO - 3 SEGUNDOS]
[JÚLIA ACORDA ASSUSTADA]
Pai: E agora, o que tá escrito?
Júlia: Ããhn... 7 de Setembro?
Pai: ...
[LEGENDA: 'A MEMÓRIA RAM DE CRIANÇA']
```

- Tags: sitcom, comedia familiar, animacao simples, cotidiano, meme de pais, relatable

### história cômica ilustrada com narração TTS  -  potencial 8/10, esforco medio  -  canal: novo canal: ComedyBR Comics

- **Visto em:** 2026-10-06 18-26-33.mp4 (2026-10-12)
- **O que e:** Narrativa curta e engraçada contada através de painéis estáticos de ilustração estilo webtoon/quadrinho, com narração em português, SFX e timing comedico. Estrutura: setup > escalada absurda > punchline visual.
- **Por que viraliza:** Identificação universal com situações cotidianas brasileiras + exagero absurdo que subverte expectativa + timing perfeito de comédia física
- **Como fazer:** 1) Escrever roteiro cômico de situação cotidiana brasileira com twist absurdo (30-45seg). 2) Gerar 4-6 painéis de ilustração via Gemini/Pollinations (estilo webtoon simplificado, personagens consistentes). 3) Narrar com TTS edge-tts (voz brasileira natural) + diálogos alternados (vozes masculina/feminina). 4) Adicionar SFX nos momentos-chave (susto, transformação, grito) + música de suspense/comédia de fundo. 5) Montar no ffmpeg: painéis com zoom/pan sutil + legendas grandes estilo meme + overlays (raio na transformação, confete no fail). 6) Cortar em 40-50seg, ritmo rápido.
- **Ferramentas:** Gemini/Pollinations, TTS (edge-tts), ffmpeg, SFX meme, trilhas comédia, overlays animados
- **Material:** Geração de imagem por IA (prompts detalhados para consistência visual dos personagens), biblioteca de SFX de meme/comédia, trilhas cômicas do acervo
- **Exemplo de roteiro:**

```
[Painel 1] 'Amor, tem uma barata aqui!' [SFX: grito feminino]
[Painel 2] 'Calma, eu vou matar' [música épica começa]
[Painel 3 - zoom] 'Mas primeiro... MODO COMBATE ATIVADO' [SFX: transformação] [overlay: raio]
[Painel 4] [personagem todo embrulhado tipo múmia] 'Cadê ela?'
[Painel 5] 'Tá subindo em você' [SFX: suspense]
[Painel 6] 'AAAAH!' [overlay: explosão] [música para]
```

- Tags: comédia brasileira, situações cotidianas, ilustração animada, relatable, humor absurdo, casal

### animação de personagem 2D clássico com plot twist brasileiro  -  potencial 8/10, esforco medio  -  canal: novo canal: BrasilMemeGames

- **Visto em:** 2026-10-06 18-27-41.mp4 (2026-10-12)
- **O que e:** Animação simples estilo retrô (Sonic 2D correndo) com diálogo legendado, setup de corrida e punchline com referência cultural brasileira (dois numa moto = assalto). Ritmo rápido, 15-30s, reviravolta no final.
- **Por que viraliza:** Plot twist cultural brasileiro pega desprevenido e gera identificação + compartilhamento ('é assim mesmo no Brasil'), nostalgia de jogos retrô amplifica alcance
- **Como fazer:** 1. Gerar sprites/animação 2D de personagem clássico correndo com IA (Veo 3 ou Pollinations para loops simples) ou usar sprites existentes; 2. Criar cenário de corrida estilo 16-bit com parallax; 3. Escrever roteiro com LLM: setup arrogante → corrida → reviravolta cultural brasileira; 4. TTS para narração dos diálogos; 5. Legendas estilo meme com fonte grossa branca/contorno preto; 6. ffmpeg para montar tudo + trilha retro/tensa + SFX de corrida
- **Ferramentas:** Veo 3, Pollinations, LLM, TTS, ffmpeg, overlays animados, SFX
- **Material:** Sprites de domínio público (OpenGameArt), gerar personagens 2D com IA, cenários pixel art gerados ou gratuitos, ou recriar estilo retrô com Veo 3
- **Exemplo de roteiro:**

```
SONIC: 'Preparado pra comer poeira? Essa é a corrida mais fácil da minha vida!'
PESSOA COMUM: 'Como você tá correndo tão rápido?'
SONIC: 'Olha o que tem atrás de você!'
[Aparecem dois numa moto]
PESSOA: 'EXATO! CORRE!'
[Legenda final: 'No Brasil é diferente 💀']
```

- Tags: sonic, meme brasileiro, animação retrô, plot twist, humor cultural, nostalgia

### sketch animado de comédia infantil com legendas  -  potencial 8/10, esforco medio  -  canal: novo canal: ComedinhaCurta

- **Visto em:** 2026-10-06 18-28-37.mp4 (2026-10-12)
- **O que e:** Diálogo curto e absurdo entre personagens animados 2D (criança vs vendedor), com legendas sincronizadas, transições de cena tipo sitcom e punchline final. Ritmo rápido com pausas cômicas.
- **Por que viraliza:** Absurdo infantil + timing de comédia criam loop de rewatching; legendas facilitam share sem áudio; formato universal de sketch curto
- **Como fazer:** 1) Escrever roteiro de sketch absurdo (30-45s) com LLM focado em lógica infantil/nonsense; 2) Gerar personagens 2D consistentes via Gemini (criança, adulto, cenário de loja colorido); 3) Criar 4-6 frames estáticos de cada cena com variação de expressão facial; 4) Sintetizar vozes com ElevenLabs (voz infantil feminina + voz adulta masculina) com timing de comédia; 5) Montar no ffmpeg: transições rápidas entre frames (0.5-1s cada), adicionar legendas brancas com borda preta estilo meme, inserir efeito de 'tela preta + texto' para punchline; 6) Adicionar trilha de fundo neutra + sons de meme (confusão, suspense) nos beats cômicos
- **Ferramentas:** Gemini, ElevenLabs, ffmpeg, overlays de legenda
- **Material:** geração IA de personagens 2D estilo cartoon infantil (Gemini com prompt de consistência visual) + roteiros criados por LLM baseados em lógica absurda infantil
- **Exemplo de roteiro:**

```
CENA 1: Criança na padaria - 'Moço, me dá um pão de ontem'
Padeiro confuso: 'Mas ontem já passou, só tenho pão fresco'
Criança: 'Então eu volto ontem pra buscar'
TELA PRETA: 'Ela nunca mais voltou...'
```

- Tags: humor infantil, sketch animado, comédia absurda, meme brasileiro, animação 2D, diálogo nonsense

### recap narrativo de anime com legendas dinâmicas  -  potencial 8/10, esforco medio  -  canal: cenareact

- **Visto em:** 2026-10-07 13-53-34.mp4 (2026-10-12)
- **O que e:** Narração contínua resumindo episódio/arco de anime, com frames estratégicos sincronizados e legendas amarelas destacando palavras-chave. Ritmo rápido, foco em plot twists e momentos de poder.
- **Por que viraliza:** Recap rápido de anime pouco conhecido desperta curiosidade, legendas dinâmicas prendem atenção, cliffhanger no final gera comentários perguntando o nome
- **Como fazer:** 1) LLM gera roteiro recap de 45-60s de anime isekai/sistema (usando sinopses públicas ou wikis); 2) TTS português (edge-tts ou ElevenLabs) narra o roteiro; 3) buscar frames do anime em repositórios públicos ou gerar cenas similares com Veo 3 (personagens genéricos, estilo anime); 4) ffmpeg sincroniza frames com narração, adiciona legendas com palavras-chave em amarelo (estilo do vídeo); 5) trilha épica de fundo (das 341 disponíveis); 6) overlay de fogo/raio nos momentos de clímax
- **Ferramentas:** LLM, TTS, Veo 3, ffmpeg, trilhas de música, overlays animados
- **Material:** frames de anime de domínio público/wikis, ou geração de cenas estilo anime com Veo 3, sinopses de MyAnimeList/AniList para roteiro
- **Exemplo de roteiro:**

```
Jack era o noob do servidor, mas descobriu uma skill QUEBRADA de farm de poções. Enquanto todos riam dele, ele treinava em segredo. Quando voltou pra cidade, os mesmos jogadores que zombavam IMPLORARAM pra comprar dele. Até o toxic do servidor teve que AJOELHAR. Quer saber o nome desse anime? Comenta 'NOME' aqui embaixo!
```

- Tags: anime recap, isekai, anime desconhecido, sistema de jogo, underdog, plot twist

### recap de anime legendado com música dramática  -  potencial 8/10, esforco baixo  -  canal: manhwareact

- **Visto em:** 2026-10-07 13-57-58.mp4 (2026-10-12)
- **O que e:** Sequência rápida de cenas-chave de anime com legendas em português descrevendo a trama (torneio, máfia, casamento). Música épica/tensa de fundo. Ritmo acelerado, cuts a cada 2-3 segundos.
- **Por que viraliza:** Mistura nostalgia de anime + storytelling acelerado + música épica cria loop de 'preciso saber o final'
- **Como fazer:** 1. Selecionar anime da base de 86k painéis de manhwa ou buscar frames no Pexels/domínio público de animes clássicos. 2. Montar storyline dramática (3-5 beats: apresentação→conflito→tensão→clímax). 3. Gerar legendas curtas e impactantes com LLM (estilo 'ELA O LARGOU', 'LIDERANDO', 'ISSO SIGNIFICA QUE SEGUIRÁ'). 4. Sincronizar frames com legendas usando ffmpeg, overlays animados (raio, fogo) nos momentos de tensão. 5. Adicionar trilha épica/dramática da biblioteca de 341 músicas. 6. Exportar em 9:16, 30-60 segundos.
- **Ferramentas:** ffmpeg, LLM (roteiro/legendas), overlays animados, biblioteca de músicas, 86k painéis manhwa
- **Material:** 86 mil painéis de manhwa próprios; frames de animes de domínio público; Pexels; ou geração IA (Veo 3) para cenas genéricas estilo anime
- **Exemplo de roteiro:**

```
Frame 1: 'ELE FOI DESAFIADO PELA MÁFIA' [homem de terno, fundo vermelho]
Frame 2: 'PARA GANHAR A MÃO DELA EM CASAMENTO' [garota chorando]
Frame 3: 'MAS O TORNEIO É MORTAL' [luta épica]
Frame 4: 'E ELE NÃO PODE PERDER' [close no rosto determinado]
Frame 5: 'O QUE ELE VAI FAZER?' [tela preta, suspense]
```

- Tags: anime recap, torneio anime, anime legendado, storytelling rápido, anime dramático, shorts anime

### recap de anime com legendas palavra-chave destacadas  -  potencial 8/10, esforco medio  -  canal: cenareact

- **Visto em:** 2026-10-07 13-59-31.mp4 (2026-10-12)
- **O que e:** Sequência de cenas do anime com legendas rápidas destacando palavras-chave em amarelo, contando a história do protagonista de forma acelerada e visual. Sem narração, só música de fundo.
- **Por que viraliza:** Formato de recap rápido cria curiosidade e urgência para assistir o anime completo, com legendas dinâmicas prendendo atenção
- **Como fazer:** 1. Extrair cenas do anime usando clipes curtos (3-5s cada) ou gerar frames com IA (Veo 3) baseados em sinopse; 2. Escrever roteiro resumido do enredo com LLM (3-8 frases curtas); 3. Adicionar legendas sincronizadas com ffmpeg, destacando palavras-chave em amarelo/neon com overlays animados; 4. Sobrepor trilha épica/tensa dos 341 recursos; 5. Acelerar ritmo com cortes rápidos (1-2s por cena) usando ffmpeg; 6. Exportar em formato vertical 9:16
- **Ferramentas:** ffmpeg, LLM para roteiro, Veo 3 (ou clipes fair use), overlays animados, trilhas de música
- **Material:** Clipes curtos do anime (fair use <10s total), ou gerar cenas similares com Veo 3 baseado em descrição da sinopse, ou usar painéis de manhwa se houver versão mangá
- **Exemplo de roteiro:**

```
Frame 1: [Personagem criança] 'Ele REENCARNADO de outro mundo'
Frame 2: [Personagem sorrindo] 'DEVERIA começar do ZERO'
Frame 3: [Cena de fazenda] 'Para ENFRENTAR qualquer ameaça'
Frame 4: [Luz brilhante] 'Mas herdou o poder INTEIRO de Jenny'
Frame 5: [Cena de batalha] 'E se tornou o PALADINO mais forte'
```

- Tags: anime recap, paladino, isekai, reencarnacao, power up, anime legendado

### recap narrado de anime com legendas destacadas  -  potencial 8/10, esforco baixo  -  canal: novo canal: AnimeRecapBR

- **Visto em:** 2026-10-07 15-48-37.mp4 (2026-10-12)
- **O que e:** Narração dramatica resumindo plot de anime (Kaiju/mecha/viagem no tempo), com cenas do anime + legendas amarelas destacando palavras-chave, ritmo rapido, gancho de suspense.
- **Por que viraliza:** Gancho de plot twist + legendas destacadas prendem atenção, nicho de anime tem engajamento alto e compartilhamento por curiosidade
- **Como fazer:** 1) Escolher anime de dominio publico ou usar trailer/cenas promocionais (ou gerar frames com IA se original). 2) Escrever roteiro de recap com LLM (Gemini/Claude) focado em plot twist. 3) Gerar narração TTS (ElevenLabs/edge-tts) com tom dramatico. 4) Cortar/editar cenas com ffmpeg, adicionar legendas amarelas (estilo Hormozi) em palavras-chave. 5) Adicionar trilha tensa (das 341) e SFX de impacto. 6) Exportar vertical 9:16.
- **Ferramentas:** ffmpeg, TTS, LLM (roteiro), overlays de legendas, trilhas, SFX
- **Material:** trailers oficiais de anime no YouTube, cenas promocionais, Veo 3 para gerar cenas originais de mecha/kaiju se necessario, ou usar paineis de manhwa adaptados
- **Exemplo de roteiro:**

```
Jack acordou achando que tudo foi um sonho... mas ao sair viu RUÍNAS por toda parte. Mechas DESTRUÍDOS espalhados pelo chão. Sua emoção DESPEDAÇOU... ele tinha VOLTADO NO TEMPO. O exército foi ANIQUILADO. O que aconteceu enquanto ele dormia?
```

- Tags: anime recap, kaiju, mecha, plot twist, viagem no tempo, suspense

### recap narrado de dramas curtos asiáticos com lição moral  -  potencial 8/10, esforco medio  -  canal: novo canal: DramaKarma

- **Visto em:** 2026-10-07 16-21-21.mp4 (2026-10-12)
- **O que e:** Narração contínua em português resumindo história curta asiática (drama/animação) com reviravolta e moral, legendas palavra-por-palavra sincronizadas, cortes rápidos entre cenas-chave.
- **Por que viraliza:** reviravolta inesperada + lição moral universal geram engajamento emocional e comentários debatendo a ética dos personagens
- **Como fazer:** 1) Gerar roteiro de história moral curta (3 atos, reviravolta, lição) com LLM. 2) Criar storyboard: 8-12 cenas-chave descritas. 3) Gerar cada cena com Veo 3 (personagens asiáticos, cenários modernos/tradicionais) ou Pollinations para frames estáticos + zoom/pan no ffmpeg. 4) Narrar roteiro com edge-tts (voz brasileira, ritmo 1.1x) ou ElevenLabs. 5) Sincronizar legendas palavra-por-palavra (ffmpeg + ass) estilo Hormozi. 6) Adicionar trilha emocional (suspense → drama) + SFX de impacto nas reviravoltas. 7) Overlay de emoji/símbolo nos momentos-chave (choque, ironia).
- **Ferramentas:** LLM, Veo 3, Pollinations, edge-tts, ffmpeg, overlays legendas Hormozi, trilhas, SFX
- **Material:** geração completa por IA: Veo 3 para clipes de drama (prompt detalhado de personagens/cenários asiáticos) ou Pollinations/Gemini para ilustrações estáticas animadas com ffmpeg (ken burns effect)
- **Exemplo de roteiro:**

```
Uma mãe rica bloqueia uma ambulância no trânsito, furiosa. Mas ela não sabia: a paciente crítica lá dentro era sua própria filha. Minutos depois, ao chegar no hospital, ela descobre a verdade. Enquanto isso, um homem arrogante também bloqueou a ambulância por orgulho. Agora os dois carregarão essa culpa para sempre. MORAL: Nunca sabemos quem estamos prejudicando com nossas atitudes.
```

- Tags: história moral, drama asiático, reviravolta, lição de vida, karma instantâneo, recap narrado

### recap rápido de cena de anime com legendas em caps lock  -  potencial 8/10, esforco baixo  -  canal: cenareact

- **Visto em:** 2026-10-07 16-40-19.mp4 (2026-10-12)
- **O que e:** Sequência acelerada de frames de anime de romance com legendas destacadas narrando a situação de forma direta e coloquial, criando tensão cômica.
- **Por que viraliza:** Combina nostalgia de clichês de anime de romance com humor de observação e ritmo acelerado que prende até o final.
- **Como fazer:** 1) Extrair 4-6 frames-chave de episódios de anime de romance da temporada (usar pipeline de recap existente); 2) Gerar roteiro com LLM descrevendo a cena em frases curtas e diretas ('É QUE...', 'DESMONTA', 'DE ACIDENTE', 'NERVOSA'); 3) Adicionar legendas em caps lock rosa/branco com ffmpeg + overlays animados; 4) TTS narrando as frases (voz masculina casual, estilo react) ou música de fundo tensa; 5) Cortar frames em 0.8-1.5s cada; 6) Finalizar com hook 'vai dar namoro' ou pergunta engajadora.
- **Ferramentas:** ffmpeg, TTS, pipeline de recap de anime, overlays animados, LLM para roteiro
- **Material:** Episódios de anime da temporada atual (captura via streaming legal ou database de frames), banco de 86k painéis de manhwa para complementar
- **Exemplo de roteiro:**

```
É QUE / DESMONTA / DE ACIDENTE / NERVOSA / [pausa dramática] VAI DAR NAMORO OU VAI ENROLAR 12 EPISÓDIOS? Comenta aí 👇
```

- Tags: anime, romance, react, temporada, clichê, shoujo

### screencast de ferramenta/processo com narração explicativa  -  potencial 8/10, esforco medio  -  canal: novo canal: negociosreact ou marketinghacks

- **Visto em:** 2026-10-09 17-22-24.mp4 (2026-10-12)
- **O que e:** Gravação de tela mostrando um dashboard ou ferramenta de branding (fases de criação de identidade visual) enquanto explica o processo de brand book para agências. Ritmo didático, foco em mostrar o 'como fazer'.
- **Por que viraliza:** Empreendedores e designers buscam processos prontos e dicas práticas que economizam tempo; o exemplo concreto ('farmácia nunca é preta') gera engajamento nos comentários.
- **Como fazer:** 1. Criar slides ou usar Canva/Figma para montar um dashboard visual de 'fases do brand book' (Agente 1: Estratégia, Agente 2: Branding, Agente 3: Identidade Visual). 2. Gerar narração com TTS ou LLM explicando cada fase (tom educativo, exemplos práticos tipo 'farmácia não usa preto/vermelho'). 3. Gravar tela com Playwright ou OBS simulando navegação pelo processo. 4. Adicionar overlays de texto destacando pontos-chave ('PALETA DE CORES', 'SEGMENTO', 'DIFERENCIAÇÃO'). 5. Trilha de fundo corporativa/motivacional. 6. Cortar em Shorts de 30-50s focando em 1 fase ou dica específica.
- **Ferramentas:** Playwright, TTS, Canva/Figma para mockup, ffmpeg, overlays de texto
- **Material:** Mockups de dashboards criados em Canva/Figma, prints de ferramentas de branding (Notion, Miro), ou geração de interface via IA (Gemini para criar layouts de 'sistema de brand book')
- **Exemplo de roteiro:**

```
❌ Você sabia que CORES ERRADAS matam negócios?
🏪 Já viu farmácia preta? NÃO. E barbearia verde? NUNCA.
🎨 O segredo? BRAND BOOK.
📊 Vou te mostrar as 3 fases que agências COBRAM R$5mil.
✅ Fase 1: Estratégia. Defina segmento, público, diferenciais...
```

- Tags: branding, identidade visual, empreendedorismo, marketing digital, brand book, dica de negócios

### meme estático com legenda fixa + áudio de fala  -  potencial 6/10, esforco baixo  -  canal: novo canal: OpiniãoQuente ou PolemicaBR

- **Visto em:** 2026-10-06_parte1_opiniao.mp4 (2026-10-06)
- **O que e:** Um único frame de meme (personagem com expressão) fica na tela com legenda fixa enquanto rola áudio de uma conversa/opinião polêmica. O meme funciona como reação visual ao que está sendo dito.
- **Por que viraliza:** Opinião polêmica + meme de reação criam identificação instantânea e vontade de comentar para discordar ou concordar.
- **Como fazer:** 1. Selecionar áudio polêmico/viral de política (extrair de podcast, entrevista, TikTok com Playwright ou usar TTS com roteiro de opinião controversa gerado por LLM). 2. Escolher meme de reação adequado ao tom (dos 650 sons de meme você pode pegar os PNGs associados, ou gerar com IA: 'personagem de desenho com expressão de descrença'). 3. Adicionar legenda fixa em caixa alta com fonte impact ('AÍ MEU DEUS, JU' ou frase-chave do áudio). 4. Montar no ffmpeg: imagem estática + áudio + legenda por 15-30seg. 5. Adicionar SFX sutil de tensão/suspense no fundo se necessário.
- **Ferramentas:** ffmpeg, Playwright, TTS, Gemini geração de imagem, SFX
- **Material:** Áudio: Playwright capturando cortes de podcast/entrevista no YouTube, ou TTS narrando thread polêmica do Twitter/Reddit. Meme: biblioteca de memes brasileiros (domínio público) ou geração IA com prompt de personagem cartoon com expressão específica.
- **Exemplo de roteiro:**

```
[ÁUDIO - TTS ou capturado]: 'Eu sinceramente acho que o Lula vai ganhar de novo em 2026, porque o povo brasileiro tem memória curta e esquece tudo que aconteceu.'
[MEME na tela]: Personagem de olhos arregalados com legenda 'PERAÍ, COMO ASSIM?'
[Corta antes de dar tempo de processar - 18 segundos]
```

- Tags: política, meme, reação, polêmica, debate, opinião

## Nao replicaveis (so para referencia)

- **resumo de filme com legendas + música tensa** (2026-10-07 16-44-43.mp4): Resumo visual de filme/série com cenas-chave legendadas em português, música de suspense, sem narração. Estrutura: 3-5 cenas impactantes + texto explicativo sobreposto + trilha que amplifica a tensão.
- **cenas de série dubladas com legendas clickbait** (2026-10-01 16-27-53.mp4): Pega cenas curtas e relacionáveis de séries/filmes (pai tirando filho da festa, mãe pegando no flagra, etc.), coloca legendas em destaque com palavras-chave exageradas ('BONITO', 'QUE ESTÁ', 'HACK PARA') e música dramática. O gancho é a situação universal + legendas chamativas.
- **transformação artesanal de objeto em réplica de item cult** (2026-10-01 16-37-51.mp4): Time-lapse de processo artesanal (cutelaria, marcenaria, metalurgia) transformando sucata/material comum em réplica de item icônico de filme/game/anime. Ritmo: mostrar etapas-chave com cortes rápidos, música épica, reveal dramático do resultado final.
- **cenas de série com reviravolta chocante + legendas** (2026-10-01 16-43-04.mp4): Pega uma cena curta de série/filme que escala de zero a cem (comédia inocente → violência/absurdo). Legendas em português destacando o diálogo, corte seco no clímax. Sem narração, só a cena original com legendas grandes estilo meme.
- **tutorial prático de hack/mod de console retro** (2026-10-01 16-24-50.mp4): Vídeo mostra passo a passo real de desbloqueio de Xbox 360 com HD externo, testando jogos clássicos e emuladores. Ritmo rápido com cortes entre plugar o HD, navegar menus e rodar jogos populares (Rock Band, Tony Hawk, arcade).
- **piada visual com legenda fixa + reações faciais exageradas** (2026-10-02 15-46-06.mp4): Setup em texto fixo no topo ('Como serão as discussões no futuro:') seguido de pessoa fazendo mímica/reação facial exagerada sem fala, criando a piada visual. Estrutura de meme clássico: texto + punchline visual.
- **legendagem de cenas de série com análise e zooms** (2026-10-03 13-31-46.mp4): Pega cenas de série/filme, adiciona legendas amarelas destacando falas-chave ou momentos irônicos, com cortes rápidos e zoom em expressões. Narração ou texto na tela comenta a cena (ex.: 'eles morrem', 'escadinha de traição').
- **cenas de série/filme com narração crítica sobre questões sociais** (2026-10-03 13-33-05.mp4): Exibe cenas icônicas de produções brasileiras (racismo, injustiça, desigualdade) com narração em off analisando o contexto, adicionando legendas dramatizadas e trilha tensa para amplificar o impacto emocional.
- **recap de cena cinematográfica com legendas contextuais** (2026-10-04 08-21-58.mp4): Sequência de frames de um filme/série com legendas curtas explicando a ação, sem narração, só música de fundo. Ritmo rápido, 3-5 segundos por frame, focando em reviravolta ou momento icônico.
- **resumo de clássico literário com cenas de adaptação + legendas dinâmicas** (2026-10-04 08-41-42.mp4): Narração em ritmo rápido contando a história de um livro/filme clássico com cenas visuais e palavras-chave em destaque na tela. Estrutura de storytelling com ganchos de drama/romance.
- **ranking de cenas tristes de anime com música emocional** (2026-10-07 12-03-29.mp4): Compilação de cenas impactantes de animes (morte, despedida, sofrimento) com música dramática de fundo, sem narração, apenas mostrando os momentos mais emocionais em sequência. O vídeo prende pela nostalgia e pelo gatilho emocional.
- **recap de cenas de filme/série com narração IA questionadora** (2026-10-07 16-17-32.mp4): Montagem de cenas-chave de um filme/série com narração IA fazendo perguntas retóricas e comentários que instigam o espectador a opinar ('você faria esse acordo?'). Ritmo: cena → provocação → próxima cena.
- **cenas de série/filme com narração e legendas dinâmicas** (2026-10-01 16-44-06.mp4): Pega cenas curtas de séries/filmes (aqui Malcolm in the Middle), adiciona narração dramatizada contando o contexto, legendas animadas estilo Hormozi sincronizadas com fala, e música de fundo. Ritmo: cortes rápidos entre cenas, zoom nos rostos, texto reforçando a piada.
- **clipe de série com legendas + reações via TTS** (2026-10-02 15-31-04.mp4): Cena dramática/cômica de série (família discutindo relacionamento) com legendas em português e comentários de reação em voice-over. Ritmo rápido, cortes na tensão, legendas sincronizadas.
- **recap de cenas icônicas de série com legendas e narração** (2026-10-03 13-30-21.mp4): Mostra cenas memoráveis/engraçadas de séries animadas, editadas em sequência rápida com legendas destacadas em palavras-chave (FURIOSA, VAI, RUPERT) e narração explicando o contexto. Ritmo acelerado, cortes dinâmicos, foco no absurdo/comédia.
- **cena de sitcom legendada com reações críticas por TTS** (2026-10-04 10-54-24.mp4): Pega uma cena icônica de série (aqui The Big Bang Theory), adiciona legendas em português com timing perfeito e uma narração TTS comentando/zuando a situação como se fosse um amigo assistindo junto. O gancho é a traição/barraco.
- **recap dramático de filme/série de época com legendas palavra-chave** (2026-10-04 10-42-55.mp4): Narração emotiva sobre cena dramática de obra clássica, com clipes da adaptação cinematográfica e legendas em palavras-chave sincronizadas (QUE, ARTIFÍCIO, MUDASSE). Ritmo lento, foco na tensão emocional.
- **screencast de plataforma com narração tutorial** (2026-10-06_parte2_financeiro.mp4): Demonstração de interface de bot/plataforma de investimento em cripto com IA, mostrando telas, métricas ao vivo, estratégias e explicação verbal técnica. Ritmo de tutorial educativo, retenção por dados reais e interface em movimento.
- **recap de cena cômica de anime com legendas dinâmicas** (2026-10-07 16-14-14.mp4): Mostra uma sequência curta de anime (15-30s) com legendas em português destacando falas/reações engraçadas, usando typografia chamativa e transições rápidas entre frames. O ritmo é ágil, sem narração, só música de fundo.
- **recap narrado de dorama/manhwa com clipes das cenas originais** (2026-10-07 16-41-59.mp4): Narração rápida resumindo enredo de dorama/manhwa coreano (confusão de identidade, romance, empresa) com cortes de cenas originais do dorama, legendas em português e trilha de fundo. Ritmo acelerado, cada cena dura 2-4 segundos.
- **demo de software/produto tech com tela compartilhada + explicação técnica** (2026-10-08 12-06-26.mp4): Apresentação de um bot de trading com IA mostrando interface, estratégias, código e resultados em tempo real. Conversa técnica entre desenvolvedores discutindo arquitetura, custos de API, performance e viabilidade.
- **comentário político falado direto na webcam** (2026-10-08 10-29-40_tema1.mp4): Criador dá opinião política direta olhando pra câmera, sem edição pesada, só ele falando. Formato vlog de opinião crua sobre eleições/política brasileira.
- **opinião política com reações faciais + música de fundo** (2026-10-08 10-29-40_tema2.mp4): Criador expressa opinião sobre política brasileira (PT, Lula) em estilo podcaster, com reações faciais genuínas e música ambiente. Ritmo: frases curtas, pausas dramáticas, construção de argumento informal.
- **meme legendado de série animada com cortes rápidos** (2026-10-04 10-46-07.mp4): Clipes curtos de Family Guy (ou similar) com legendas em português destacando piadas/situações absurdas. Cortes rápidos (3-7 segundos cada), sem narração, só a cena com legenda sincronizada.
