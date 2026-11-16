# Aprendizado com os parceiros — PARA IMPLEMENTAR (refeito a cada rodada; não editar à mão)

Atualizado 16/11/2026 15:41. Gerado por D:\video-fila\aprendizado.py.

OBRIGATÓRIO (dona 01/11): ninguém implanta isto sozinho — o chat que for melhorar vídeo analisa estes itens
ANTES de editar e marca cada um. Passo a passo: D:\video-fila\aprendizado\LEIA_ANTES_DE_MELHORAR.md

REGRA (dono 22/10): toda sessão que for mexer na produção dos vídeos LÊ isto antes, avalia e decide. Quem avalia
é a sessão (modelo forte), nunca o vigia nem a IA do painel. Para cada grupo: aplicar (testando num vídeo real,
com backup) ou descartar com motivo. Depois:
    python D:\video-fila\aprendizado.py marcar <ids do grupo> aplicado --motivo "onde/como"
    python D:\video-fila\aprendizado.py marcar <ids do grupo> reprovado --motivo "por que não serve"
(aplicado/reprovado entram no ja_temos.json: o estudo não sugere parecido de novo).
Candidato = o dono não respondeu em 24 h e a nota era >= 7: é sugestão, não ordem. Cuidado com o que já existe
na produção, com humor/visual que derruba monetização e com marca do parceiro (não copiar marca).

## A. Aprovados (pela dona ou sozinho: os melhores de cada dia, nota >= 7) (0)

(nenhum)

## B. Candidatos (sem resposta em 24 h): 522 grupo(s), os 40 mais fortes

### 1. [outro] Gancho final de engajamento deixando propositalmente o próprio país (Brasil) para os comentários responderem
- visto em 1 vídeo(s) · nota máx. 9 · modelos: claude-sonnet
- como aplicar: Em vídeos comparativos por países/categorias, omitir a resposta do Brasil no final e fechar com: 'E do Brasil, qual é a nossa? Responde aí nos comentários'.
- por que é novo: Nossos hyperframes de CTA fazem perguntas genéricas (cta_question), enquanto aqui o mistério de 'quem representa o Brasil' força comentários e debate entre os espectadores.
- exemplos: https://www.youtube.com/watch?v=TMQnSR26bK0 seg 54.0 (trecho 32716b92.mp4)
- ids: 32716b92

### 2. [visual] B-roll em split screen mostrando um processo prático manual (torno de madeira) enquanto o palestrante fala
- visto em 1 vídeo(s) · nota máx. 9 · modelos: gemini
- como aplicar: Adicionar vídeos de processos satisfatórios ou trabalhos manuais na parte inferior dos nossos vídeos informativos.
- por que é novo: Usa um vídeo B-roll contínuo de artesanato/trabalho manual na metade inferior da tela durante toda a explicação, mantendo alta retenção visual.
- exemplos: https://www.youtube.com/watch?v=266QAGdQ3SI seg 0.0 (trecho c7683c5d.mp4)
- ids: c7683c5d

### 3. [visual] Uso de moldura/polaroid emoldurada e pinada com corda vermelha simulando investigação policial (quadro 3)
- visto em 1 vídeo(s) · nota máx. 9 · modelos: gemini
- como aplicar: Criar template de overlay em After Effects/CapCut com fundo de cortiça, foto central emoldurada com borda branca, grampo ou alfinete vermelho no topo e fio/corda vermelha cruzando a imagem.
- por que é novo: Apresenta fotos antigas com um visual de 'mural de investigação' (conspiração/true crime) fixadas com alfinete e corda vermelha sobre fundo de cortiça, que ainda não utilizamos no nosso acervo.
- exemplos: https://www.youtube.com/watch?v= seg 30.0 (trecho 8f0adb2b.mp4)
- ids: 8f0adb2b

### 4. [visual] Infográfico com silhuetas vetoriais escuras no rodapé e estatísticas com setas de queda/preço
- visto em 1 vídeo(s) · nota máx. 8.5 · modelos: claude-sonnet
- como aplicar: Usar em momentos de perda de audiência/prejuízo financeiro: posicionar silhuetas minimalistas nas bordas inferiores e animar big numbers com setas descendentes vermelhas no centro.
- por que é novo: Combina silhuetas pretas estilizadas de pessoas no primeiro plano inferior com números brancos em caixas outline e grande seta vermelha de queda animada por trás, transmitindo impacto financeiro e perda de público.
- exemplos: https://www.youtube.com/watch?v=rJyqYxeQtY0 seg 67.3 (trecho 602dff0b.mp4)
- ids: 602dff0b

### 5. [jeito_de_falar] Analogias caseiras e táteis para explicar geologia complexa ('massa de pizza', 'pasta de dente', 'porta')
- visto em 1 vídeo(s) · nota máx. 8 · modelos: claude-sonnet
- como aplicar: Nos roteiros de curiosidades científicas e históricas, substituir explicações técnicas por comparações táteis cotidianas com cartelas de texto destacadas.
- por que é novo: Geralmente usamos gírias ou memes para humor, mas não analogias sensoriais/culinárias estruturadas com texto colado na tela ('esticada como massa de pizza').
- exemplos: https://www.youtube.com/watch?v=53oBWf7c9DQ seg 24.3 (trecho ee775939.mp3)
- ids: ee775939

### 6. [jeito_de_falar] Metáfora didática em aforismo conciso: 'A água em si não mata bactéria nenhuma, só muda ela de endereço'
- visto em 1 vídeo(s) · nota máx. 8 · modelos: claude-sonnet
- como aplicar: Incluir no roteiro frases-síntese com analogias cotidianas simples para desmistificar mitos comuns no meio do vídeo.
- por que é novo: Frase de alto impacto cognitivo e fácil memorização ('muda de endereço') que resume instantaneamente a tese científica do vídeo sem termos técnicos maçantes.
- exemplos: https://www.youtube.com/watch?v=ZKJMDenC seg 16.3 (trecho 2a80d39c.mp3)
- ids: 2a80d39c

### 7. [piada] Plot twist cômico anti-clímax ('solução tecnológica ultra complexa vs jogar uma pedra')
- visto em 1 vídeo(s) · nota máx. 8 · modelos: claude-sonnet
- como aplicar: Usar essa estrutura de contraste/quebra de expectativa nos roteiros de animação e teorias: criar um problema hiperbólico e dar a solução mais boba e rústica no clímax final.
- por que é novo: Construção de roteiro que infla a complexidade de ficção científica (campo de atraso temporal, canhão de almas humanas) para resolver o problema com a ação mais primitiva e banal possível (atirar uma pedra).
- exemplos: https://www.youtube.com/watch?v=72NKj2CkiLI seg 47.0 (trecho 7c90c6fc.mp3)
- ids: 7c90c6fc

### 8. [jeito_de_falar] Gancho com quebra abrupta de narrativa no clímax final ('bem na hora em que...') sem call to action óbvia
- visto em 1 vídeo(s) · nota máx. 8 · modelos: claude-sonnet
- como aplicar: Encerrar scripts de episódios divididos interrompendo a frase na última conjunção da ação crucial, sem introduzir áudio de encerramento padrão
- por que é novo: Nossas intros/fins e CTAs costumam pedir inscrição/like ou fechar raciocínio; aqui há um corte seco no ápice da ação ('bem na hora em que...') gerando retenção pura para parte 2
- exemplos: https://www.youtube.com/watch?v=W7o0hzjbZ60 seg 85.0 (trecho 590791d3.mp3)
- ids: 590791d3

### 9. [jeito_de_falar] Call To Action com engajamento geográfico específico ('comenta o nome da sua cidade')
- visto em 1 vídeo(s) · nota máx. 8 · modelos: claude-sonnet
- como aplicar: Adicionar script/hyperframe de finalização convidando os espectadores a comentar sua cidade/estado para pedir a continuação.
- por que é novo: Nosso repertório de CTAs (cta_question, watch_to_end) usa perguntas genéricas ou pedidos de like/inscrição. Pedir a cidade de origem gera alta taxa de comentários espontâneos e sem atrito cognitivo.
- exemplos: https://www.youtube.com/watch?v=cTMg2GTXHwY seg 63.0 (trecho a760cd16.mp3)
- ids: a760cd16

### 10. [jeito_de_falar] Loop narrativo em gancho com pergunta reflexiva de retorno ao início
- visto em 1 vídeo(s) · nota máx. 8 · modelos: claude-sonnet
- como aplicar: Adicionar essa frase ou estrutura de recapitulação circular no final do roteiro de shorts/reels que contam histórias lineares, incentivando a repetição do vídeo
- por que é novo: Usa a fórmula '...só que cê lembra como tudo isso começou?' no clímax final para criar um seamless loop perfeito de volta aos primeiros segundos sem parecer corte seco de fim de vídeo
- exemplos: https://www.youtube.com/watch?v=BOWCeZuogKI seg 81.0 (trecho 63df3f3a.mp3)
- ids: 63df3f3a

### 11. [jeito_de_falar] Gancho reflexivo de encerramento ('Pode ser o registro silencioso de... / A mesma força que destrói... cria')
- visto em 1 vídeo(s) · nota máx. 8 · modelos: claude-sonnet
- como aplicar: Inserir nos últimos 15s de roteiros de curiosidades uma antítese poética (destruição vs criação, micro vs macro) para elevar o valor percebido do conteúdo antes do CTA de inscrição.
- por que é novo: Nosso roteiro costuma finalizar com CTA direto ou resumo factual simples; aqui ele usa uma antítese poética e filosófica ('destruição na superfície gerando riqueza no subterrâneo') que conecta destruição e criação antes da pergunta de retenção.
- exemplos: https://www.youtube.com/watch?v=kirdD3zdWw0 seg 135.6 (trecho eeae67d2.mp3)
- ids: eeae67d2

### 12. [jeito_de_falar] Gancho condicional imersivo 'Imagina que un día...'
- visto em 1 vídeo(s) · nota máx. 8 · modelos: claude-sonnet
- como aplicar: Abrir o Short/TikTok nos primeiros 3 segundos dizendo: 'Imagina se um dia você abre uma porta no seu quarto e vai parar direto num mundo de RPG com status apelão...'.
- por que é novo: Nossas intros focam em bordoes ou falas diretas do mascote, mas não usam a estrutura de convite mental 'Imagina se um dia você...', que retém a audiência colocando-a na pele do protagonista.
- exemplos: https://www.youtube.com/watch?v=r77umNwvRKU seg 0.0 (trecho 7373216f.mp3)
- ids: 7373216f

### 13. [jeito_de_falar] Hook com curiosidade pop linkada à ciência prática ('Já reparou que James Bond pede batida e não mexida?')
- visto em 1 vídeo(s) · nota máx. 8 · modelos: claude-sonnet
- como aplicar: Adotar ganchos que questionam hábitos clássicos de ficção (animes, filmes, games) prometendo uma explicação lógica/científica do mundo real para prender o público nos primeiros 3s.
- por que é novo: Costumamos abrir direto no tema factual ou com piadas/bordões de choque; não usamos perguntas retóricas sobre detalhes de filmes/cultura pop com explicação científica imediata.
- exemplos: https://www.youtube.com/watch?v=d-QU seg 0.0 (trecho 5016bf0d.mp3)
- ids: 5016bf0d

### 14. [outro] Uso de cenas geradas por IA com estilo visual consistente de fantasia mecânica/vintage para recontar uma história dramática/cinemática
- visto em 1 vídeo(s) · nota máx. 8 · modelos: gemini
- como aplicar: Integrar prompts de IA estilo dark steampunk/fantasy nos vídeos de histórias misteriosas e de fuga.
- por que é novo: A narrativa visual lembra clássicos adaptados por IA com temática steampunk/fantasia escura (como O Mágico de Oz sombrio) mantendo engajamento alto.
- exemplos: https://www.youtube.com/watch?v=wYsrT7sLWPo seg 3.6 (trecho 05ac530e.mp4)
- ids: 05ac530e

### 15. [jeito_de_falar] Estrutura de hook cumulativo rápido ('Esse peixe aguenta água ruim, come praticamente de tudo, se reproduz rápido e ainda quase não tem predador...')
- visto em 1 vídeo(s) · nota máx. 8 · modelos: claude-sonnet
- como aplicar: Adotar roteiro com lista rápida de 3 a 4 fatos inacreditáveis/características extremas antes de revelar o elemento principal nos primeiros 10 segundos para reter curiosidade
- por que é novo: Nossas intros em intros_voz focam em frases de abertura diretas ou bordões gravados; essa técnica usa empilhamento acelerado de atributos extremos antes de revelar o nome do sujeito aos 13s
- exemplos: https://www.youtube.com/watch?v=VyUBk3VVPyo seg 1.9 (trecho a465aa05.mp3)
- ids: a465aa05

### 16. [jeito_de_falar] Gancho de 'ponto fraco curioso' com reviravolta explicativa e teste prático
- visto em 1 vídeo(s) · nota máx. 8 · modelos: claude-sonnet
- como aplicar: Em roteiros sobre materiais, invenções ou curiosidades científicas, incluir sempre a seção do 'calcanhar de Aquiles' ou contraindicação bizarra aos 75% do vídeo para renovar a retenção antes do CTA.
- por que é novo: Apresenta um 'super-material' incrível, mas no clímax do vídeo introduz intencionalmente o seu ponto fraco/defeito ('Mas o produto tem um ponto fraco muito curioso: basta jogar sal...') demonstrando a dissolução imediata e finalizando com a implicação lógica ('não funciona na água do mar'). Nosso formato foca muito em fatos lineares sem essa quebra de expectativa no terço final.
- exemplos: https://www.youtube.com/watch?v=xSzOJAgDVD8 seg 25.5 (trecho 265b8868.mp3)
- ids: 265b8868

### 17. [jeito_de_falar] Hook com paradoxo de escala extrema ('um simples X podia destruir uma fábrica inteira')
- visto em 1 vídeo(s) · nota máx. 8 · modelos: claude-sonnet
- como aplicar: Estruturar aberturas de curiosidades usando a fórmula: 'Sabia que um simples [objeto insignificante] quase destruiu [algo gigantesco] nos anos [década]?'
- por que é novo: Contraste narrativo imediato entre um detalhe minúsculo/banal (um número escrito à mão) e uma catástrofe monumental (destruição de uma fábrica de milhares de dólares), gerando curiosidade instantânea antes de revelar o tema.
- exemplos: https://www.youtube.com/watch?v=lbNZaiGpGvo seg 0.0 (trecho 967295b7.mp3)
- ids: 967295b7

### 18. [piada] Metáfora cômica e culturalmente identificável ('Brasília amarela com hélice voando baixo por Guarulhos')
- visto em 1 vídeo(s) · nota máx. 8 · modelos: claude-sonnet
- como aplicar: Inserir comparações absurdas do imaginário pop brasileiro no roteiro de curiosidades sobre veículos estranhos ou engenhocas
- por que é novo: Usa referências populares brasileiras muito específicas (Mamonas Assassinas / Brasília Amarela / Guarulhos) para criar contraste humorístico com uma geringonça tecnológica
- exemplos: https://www.youtube.com/watch?v=wVRZu9dsskA seg 45.0 (trecho 5669445d.mp3)
- ids: 5669445d

### 19. [jeito_de_falar] Gancho com negação imediata de suposições intuitivas ('Este homem não está cavando neve ou areia...')
- visto em 1 vídeo(s) · nota máx. 8 · modelos: claude-sonnet
- como aplicar: Em roteiros com cenas visuais enganosas ou surpreendentes, abrir a narração com 'Você pode achar que [X], mas na verdade é [Y]' ou 'Isso não é [suposição óbvia]'.
- por que é novo: Em vez de abrir com pergunta genérica ou afirmação descritiva padrão, abre desmentindo o que os olhos do espectador imediatamente assumem ao ver a imagem (neve), gerando quebra imediata de expectativa.
- exemplos: https://www.youtube.com/watch?v=gE3Bl0FoW8o seg 0.0 (trecho 188d7ff0.mp3)
- ids: 188d7ff0

### 20. [outro] Hook com objeto misterioso/transformável em POV close-up gerando curiosidade ('isso não é X')
- visto em 1 vídeo(s) · nota máx. 8 · modelos: claude-sonnet
- como aplicar: Usar em intros de review ou curiosidades sobre itens inusitados: começar mostrando o item fechado com frase de quebra de expectativa ('Isso não é um chaveiro...') antes da transformação.
- por que é novo: Abertura puramente visual e tátil com negação no gancho ('isso não é 1 caneta') focada em produto curioso/gadget miniaturizado, sem necessidade de narrador em tela.
- exemplos: https://www.youtube.com/watch?v=cfmOF7QyXH0 seg 1.7 (trecho eb355338.mp4)
- ids: eb355338

### 21. [som] Efeito sonoro exagerado de osso quebrando/estalando sincronizado com o susto do apresentador
- visto em 1 vídeo(s) · nota máx. 8 · modelos: gemini
- como aplicar: Adicionar efeito de som de 'crack' seco em momentos de ações corporais exageradas nos nossos vídeos
- por que é novo: Foco em som de impacto corporal cômico sincronizado com reação dramática em close
- exemplos: https://www.youtube.com/watch?v=OMHvhSt0UmE seg 15.0 (trecho 7721a080.mp3)
- ids: 7721a080

### 22. [jeito_de_falar] Estrutura narrativa de fábula mística com virada trágica inevitável ('mesmo evitando rios, morre no riacho')
- visto em 1 vídeo(s) · nota máx. 8 · modelos: claude-sonnet
- como aplicar: Adotar essa estrutura de 'ironia do destino/maldição inevitável' na redação dos resumos de animes de mistério/sobrenatural, pausando o ritmo para enfatizar a profecia que se cumpre.
- por que é novo: Nossos scripts de animes/recap costumam focar em shonen de ação/poder ou comédia; a estrutura de paradoxo trágico/folclórico estilo Mushishi mantém alta retenção sem precisar de piadas ou bordões.
- exemplos: https://www.youtube.com/watch?v=mR9L0KVgrvU seg 43.9 (trecho 88e8cc1c.mp3)
- ids: 88e8cc1c

### 23. [outro] Uso de imagens de Google Street View estáticas intercaladas com filmagens aéreas de drone para contextualizar geograficamente o local da notícia
- visto em 1 vídeo(s) · nota máx. 8 · modelos: gemini
- como aplicar: Inserir gravacoes curtas de navegação em zoom out do Google Maps seguido de drone na abertura de vídeos de denúncia urbana.
- por que é novo: Transição direta de print/gravação de tela do Google Maps/Street View para vídeo real de drone local.
- exemplos: https://www.youtube.com/watch?v=FkN5oG-1b6U seg 4.5 (trecho 06a6abe7.mp4)
- ids: 06a6abe7

### 24. [jeito_de_falar] Roteiro de ranking em contagem regressiva linear (5º ao 1º lugar) com fechamento em clímax no predador mais agressivo
- visto em 1 vídeo(s) · nota máx. 8 · modelos: claude-sonnet
- como aplicar: Padronizar roteiros de curiosidades em Top 5 ordenado, alocando ~10s por item com ênfase visual imediata na característica bizarra de cada elemento.
- por que é novo: Costumamos usar ganchos com mascoetes e cortes dinâmicos de memes/reações sem a estrutura clássica e altamente retentiva de top 5 decrescente com justificativa curta (aparência + mecânica biológica) por item.
- exemplos: https://www.youtube.com/watch?v=y0hIM8OSRZM seg 0.0 (trecho 62e0845c.mp3)
- ids: 62e0845c

### 25. [outro] Inserção de filmagem real de arquivo em baixa resolução (gravação de show/celular antigo) sem moldura
- visto em 1 vídeo(s) · nota máx. 8 · modelos: claude-sonnet
- como aplicar: Inserir trechos reais de arquivo/noticiário (3 a 5s) sem tratamento excessivo no miolo dos vídeos de curiosidades históricas ou crimes reais antes de voltar ao apresentador.
- por que é novo: Uso de filmagens cruas de arquivo do evento/fato discutido diretamente no fluxo do vídeo curto, rompendo a estética polida do estúdio e gerando imersão de reconstituição documental.
- exemplos: https://www.youtube.com/watch?v=XJIwmtAiHgc seg 20.7 (trecho 79609dba.mp4)
- ids: 79609dba

### 26. [jeito_de_falar] Abertura direta anunciando o produto/parceria ('Foi a convite de...') de forma orgânica e imediata
- visto em 1 vídeo(s) · nota máx. 8 · modelos: gemini
- como aplicar: Começar os vídeos de indicação de produtos/séries direto com a justificativa de quem convidou ou enviou, gerando autoridade instantânea.
- por que é novo: Estrutura de gancho comercial transparente e direta, mantendo a credibilidade sem parecer comercial chato.
- exemplos: https://www.youtube.com/watch?v=XJIwmtAiHgc seg 3.0 (trecho 2c8bb2fc.mp3)
- ids: 2c8bb2fc

### 27. [visual] Caixa de destaque vermelha com borda branca e texto em negrito para valores monetários (ex: R$ 600, R$ 1.200)
- visto em 1 vídeo(s) · nota máx. 8 · modelos: gemini
- como aplicar: Criar um componente de texto com fundo vermelho escuro e borda branca para destacar números grandes ou preços mencionados na narração.
- por que é novo: Apresenta uma caixa translúcida/sólida vermelha elegante com contraste forte para destacar rapidamente o custo de forma impactante na tela.
- exemplos: https://www.youtube.com/watch?v=qSxpCilPM9c seg 28.8 (trecho afc9fa42.mp4)
- ids: afc9fa42

### 28. [jeito_de_falar] Gancho inicial apelativo usando a expressão hiperbólica 'chegam a ser covardia'
- visto em 1 vídeo(s) · nota máx. 8 · modelos: claude-sonnet
- como aplicar: Usar a fórmula '[X] é tão apelão/forte que chega a ser covardia' para introduções de curiosidades, dicas, truques e listas nos primeiros 2 segundos dos Shorts.
- por que é novo: Não temos esse padrão de hook hiperbólico ('tão bom que chega a ser covardia / trapaça') cadastrado no nosso acervo de ganchos de abertura.
- exemplos: https://www.youtube.com/watch?v=fpecvHeh06g seg 0.0 (trecho 3b4137de.mp3)
- ids: 3b4137de

### 29. [visual] Legenda destacada em dois tons (branco com fundo verde vibrante estilo TikTok/Reels de pesca)
- visto em 1 vídeo(s) · nota máx. 8 · modelos: gemini
- como aplicar: Adotar fontes grossas estilo Montserrat-Black/Impact com palavras-chave destacadas em verde limão ou amarelo vivo no centro inferior da tela para manter alta retenção.
- por que é novo: Embora usemos legendas, o contraste forte com letras grossas preenchidas e contorno/fundo sombreado focado em vídeos de nicho de pesca outdoor cria uma identidade visual muito marcante que podemos refinar.
- exemplos: https://www.youtube.com/watch?v=fpecvHeh06g seg 2.5 (trecho 0cb4dc34.mp4)
- ids: 0cb4dc34

### 30. [visual] Gravação de tela de cálculo/checkout ao vivo com recorte de fundo do apresentador sobreposto (talking head picture-in-picture)
- visto em 1 vídeo(s) · nota máx. 8 · modelos: claude-sonnet
- como aplicar: Colocar a gravação de tela de tutorias/ferramentas ocupando o topo/fundo e o apresentador ou mascote recortado na parte inferior apontando e reagindo diretamente aos elementos numéricos da tela.
- por que é novo: Apresentador recortado ou em primeiro plano enquanto a tela do software/site roda atrás demonstrando valores e campos preenchidos em tempo real, integrando a reação com a tela.
- exemplos: https://www.youtube.com/watch?v=9tOU5xjejVE seg 39.8 (trecho 335d2588.mp4)
- ids: 335d2588

### 31. [visual] Exibição de tela de checkout detalhada com quebra de custos aduaneiros e impostos (ICMS, PIS/COFINS)
- visto em 1 vídeo(s) · nota máx. 8 · modelos: gemini
- como aplicar: Inserir screen recordings detalhados com zoom nas linhas de impostos e taxas ao explicar custos logísticos ou financeiros complexos.
- por que é novo: Mostra o painel real de custos e taxas discriminadas de importação passo a passo com marcação visual na tela.
- exemplos: https://www.youtube.com/watch?v=9tOU5xjejVE seg 47.0 (trecho 17edb0f2.mp4)
- ids: 17edb0f2

### 32. [visual] Cronômetro/selo temático animado no canto superior com ponteiro marcando a duração do quadro (MEI Minuto)
- visto em 1 vídeo(s) · nota máx. 8 · modelos: claude-sonnet
- como aplicar: Criar um overlay de relógio/timer com ponteiro que avança conforme a duração do vídeo no canto superior para quadros de curiosidades ou dicas rápidas.
- por que é novo: Não temos nos hyperframes ou overlays um widget dinâmico de cronômetro temático que gira e reforça a promessa do formato curto (ex: 'dica em 30s').
- exemplos: https://www.youtube.com/watch?v=tEN7LosaLf4 seg 10.2 (trecho 643ec075.mp4)
- ids: 643ec075

### 33. [efeito] Animação de mão simulando anotação/marcação real com caneta (whiteboard marker)
- visto em 1 vídeo(s) · nota máx. 8 · modelos: claude-sonnet
- como aplicar: Implementar overlay PNG/WebM de mão segurando marcador desenhando círculos, sublinhados e letras de gabarito sobre os termos-chave.
- por que é novo: Nossa biblioteca possui animações e recortes de memes/mascotes, mas não temos o efeito visual de mão desenhando/grifando palavras-chave e preenchendo gabarito na tela.
- exemplos: https://www.youtube.com/watch?v=Asg5Q6iN-AA seg 14.8 (trecho d7ba588e.mp4)
- ids: d7ba588e

### 34. [visual] Recorte de papel rasgado (torned paper/mask tear) segurando títulos e tópicos históricos em cima de estátuas ou fundos antigos.
- visto em 1 vídeo(s) · nota máx. 8 · modelos: gemini
- como aplicar: Criar templates de png com bordas de papel rasgado coladas na horizontal central e aplicar textos curtos e marcantes da nossa editoria por cima.
- por que é novo: Usa fita/papel rasgado colado na tela para destacar palavras-chave textuais e nomes próprios (ex: 'Caduceu', 'Índia') em vez de legenda comum.
- exemplos: https://www.youtube.com/watch?v=o3ZwCkv-2rI seg 3.0 (trecho dc62d4a5.mp4)
- ids: dc62d4a5

### 35. [visual] Número de episódio minimalista e elegante flutuando com ícone de guarda-chuva e partículas de neve
- visto em 1 vídeo(s) · nota máx. 8 · modelos: gemini
- como aplicar: Criar template de numeração de episódio estilo minimalista com fonte fina e animação de neve/partículas ao fundo.
- por que é novo: Nosso sistema usa badges pesados (part_badge), enquanto este estilo anime usa tipografia limpa com numeração serial finita e elemento atmosférico.
- exemplos: https://www.youtube.com/watch?v=mKdnQ66SIZM seg 367.4 (trecho 4e52b69b.mp4)
- ids: 4e52b69b

### 36. [visual] Uso de zoom extremo dinâmico acompanhando a tensão da linha da vara de pesca flexionando até a fisgada final.
- visto em 1 vídeo(s) · nota máx. 8 · modelos: gemini
- como aplicar: Aplicar zooms progressivos keyframados em tomadas de suspense/ação rápida nos nossos vídeos.
- por que é novo: Foca nos detalhes físicos da ação (vara curvando) alternando com o ponto de impacto na água com corte rápido.
- exemplos: https://www.youtube.com/watch?v=RC4pe6ms450 seg 10.8
- ids: 517a2d37

### 37. [piada] Plot twist surreal/bizarro no final ao revelar alguém coberto de molho dentro da geladeira
- visto em 1 vídeo(s) · nota máx. 8 · modelos: claude-sonnet
- como aplicar: Em roteiros curtos de situações cotidianas, criar uma quebra de expectativa onde o elemento recusado/guardado encontra seu 'consumidor bizarro' escondido em armários, geladeiras ou gavetas.
- por que é novo: A estrutura de piada constrói uma narrativa comum em primeira pessoa (oferecer ketchup a um amigo, ser recusado e ir guardar na geladeira) para entregar um anticlímax bizarro e absurdo (um cara lambuzado de ketchup agachado lá dentro). Nossos memes e gags atuais são reações pontuais/cortes clássicos, não esquetes de 'punchline física absurda'.
- exemplos: https://www.youtube.com/watch?v=VXl1s5gqFhM seg 9.1 (trecho 2222e332.mp3)
- ids: 2222e332

### 38. [visual] Texto de título com fonte arredondada amarela com borda escura e sombra preta com emoji integrado no texto (segundos 0.8 e 2.4).
- visto em 1 vídeo(s) · nota máx. 8 · modelos: gemini
- como aplicar: Usar fonte bold estilo LuckiestGuy amarela com contorno preto grosso e fundo/sombra para introduzir a situação no topo.
- por que é novo: Apresenta a premissa/narrativa de forma limpa, legível e altamente chamativa para Shorts.
- exemplos: https://www.youtube.com/watch?v=aLNh2kQyT4A seg 0.8 (trecho e9da310e.mp4)
- ids: e9da310e

### 39. [piada] Uso de meme clássico de reação (Risadas de El Risitas) na metade da lista para subverter a expectativa
- visto em 1 vídeo(s) · nota máx. 8 · modelos: gemini
- como aplicar: Inserir memes visuais clássicos (como El Risitas ou similares) entre itens de listas absurdas para aumentar retenção e humor.
- por que é novo: Usa um meme icônico de vídeo externo integrado diretamente ao ritmo da lista numerada para quebra de expectativa humorística.
- exemplos: https://www.youtube.com/watch?v=OP0MtkovhT8 seg 9.3 (trecho 8cc188af.mp3)
- ids: 8cc188af

### 40. [jeito_de_falar] Dilema moral/religioso para forçar engajamento ('Dinheiro vs Jesus')
- visto em 1 vídeo(s) · nota máx. 8 · modelos: claude-sonnet
- como aplicar: Inserir em roteiros de curiosidades/rankings logo após a introdução rápida uma chamada de retenção baseada em escolha moral/polarizadora para inflar a taxa de comentários e inscrições.
- por que é novo: Não temos esse formato de CTA contrastivo ('Se prefere R$ 1 milhão comente Dinheiro, mas se ama Jesus comente um coração e se inscreva') no nosso banco de hooks/intros.
- exemplos: https://www.youtube.com/watch?v=y9zScmqflfQ seg 7.0 (trecho 213c841b.mp3)
- ids: 213c841b

(+ 482 grupo(s) mais fracos: vistos em 1 vídeo só; ficam no acervo.jsonl)
