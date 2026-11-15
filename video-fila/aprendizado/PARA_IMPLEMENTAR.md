# Aprendizado com os parceiros — PARA IMPLEMENTAR (refeito a cada rodada; não editar à mão)

Atualizado 15/11/2026 02:45. Gerado por D:\video-fila\aprendizado.py.

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

## A. Aprovados (pela dona ou sozinho: os melhores de cada dia, nota >= 7) (1)

### 1. [outro] Sequência rápida de transição mostrando etapas extremas de preparo culinário (fritura na natureza, cozimento em caldeirão, montagem de prato rústico).
- visto em 1 vídeo(s) · nota máx. 9 · modelos: gemini
- como aplicar: Criar blocos de montagem rápida de 3 a 5 cortes secos mostrando o processo do início ao fim em menos de 5 segundos para aumentar a retenção.
- por que é novo: Montagem sequencial dinâmica focando puramente no aspecto visual e ASMR visual de receitas sem enrolação.
- exemplos: https://www.youtube.com/watch?v=hDG5QOEkaiI seg 8.0 (trecho f5babf5c.mp4)
- ids: f5babf5c

## B. Candidatos (sem resposta em 24 h): 527 grupo(s), os 40 mais fortes

### 1. [jeito_de_falar] Analogias caseiras e táteis para explicar geologia complexa ('massa de pizza', 'pasta de dente', 'porta')
- visto em 1 vídeo(s) · nota máx. 8 · modelos: claude-sonnet
- como aplicar: Nos roteiros de curiosidades científicas e históricas, substituir explicações técnicas por comparações táteis cotidianas com cartelas de texto destacadas.
- por que é novo: Geralmente usamos gírias ou memes para humor, mas não analogias sensoriais/culinárias estruturadas com texto colado na tela ('esticada como massa de pizza').
- exemplos: https://www.youtube.com/watch?v=53oBWf7c9DQ seg 24.3 (trecho ee775939.mp3)
- ids: ee775939

### 2. [jeito_de_falar] Metáfora didática em aforismo conciso: 'A água em si não mata bactéria nenhuma, só muda ela de endereço'
- visto em 1 vídeo(s) · nota máx. 8 · modelos: claude-sonnet
- como aplicar: Incluir no roteiro frases-síntese com analogias cotidianas simples para desmistificar mitos comuns no meio do vídeo.
- por que é novo: Frase de alto impacto cognitivo e fácil memorização ('muda de endereço') que resume instantaneamente a tese científica do vídeo sem termos técnicos maçantes.
- exemplos: https://www.youtube.com/watch?v=ZKJMDenC seg 16.3 (trecho 2a80d39c.mp3)
- ids: 2a80d39c

### 3. [piada] Plot twist cômico anti-clímax ('solução tecnológica ultra complexa vs jogar uma pedra')
- visto em 1 vídeo(s) · nota máx. 8 · modelos: claude-sonnet
- como aplicar: Usar essa estrutura de contraste/quebra de expectativa nos roteiros de animação e teorias: criar um problema hiperbólico e dar a solução mais boba e rústica no clímax final.
- por que é novo: Construção de roteiro que infla a complexidade de ficção científica (campo de atraso temporal, canhão de almas humanas) para resolver o problema com a ação mais primitiva e banal possível (atirar uma pedra).
- exemplos: https://www.youtube.com/watch?v=72NKj2CkiLI seg 47.0 (trecho 7c90c6fc.mp3)
- ids: 7c90c6fc

### 4. [jeito_de_falar] Gancho com quebra abrupta de narrativa no clímax final ('bem na hora em que...') sem call to action óbvia
- visto em 1 vídeo(s) · nota máx. 8 · modelos: claude-sonnet
- como aplicar: Encerrar scripts de episódios divididos interrompendo a frase na última conjunção da ação crucial, sem introduzir áudio de encerramento padrão
- por que é novo: Nossas intros/fins e CTAs costumam pedir inscrição/like ou fechar raciocínio; aqui há um corte seco no ápice da ação ('bem na hora em que...') gerando retenção pura para parte 2
- exemplos: https://www.youtube.com/watch?v=W7o0hzjbZ60 seg 85.0 (trecho 590791d3.mp3)
- ids: 590791d3

### 5. [jeito_de_falar] Call To Action com engajamento geográfico específico ('comenta o nome da sua cidade')
- visto em 1 vídeo(s) · nota máx. 8 · modelos: claude-sonnet
- como aplicar: Adicionar script/hyperframe de finalização convidando os espectadores a comentar sua cidade/estado para pedir a continuação.
- por que é novo: Nosso repertório de CTAs (cta_question, watch_to_end) usa perguntas genéricas ou pedidos de like/inscrição. Pedir a cidade de origem gera alta taxa de comentários espontâneos e sem atrito cognitivo.
- exemplos: https://www.youtube.com/watch?v=cTMg2GTXHwY seg 63.0 (trecho a760cd16.mp3)
- ids: a760cd16

### 6. [jeito_de_falar] Loop narrativo em gancho com pergunta reflexiva de retorno ao início
- visto em 1 vídeo(s) · nota máx. 8 · modelos: claude-sonnet
- como aplicar: Adicionar essa frase ou estrutura de recapitulação circular no final do roteiro de shorts/reels que contam histórias lineares, incentivando a repetição do vídeo
- por que é novo: Usa a fórmula '...só que cê lembra como tudo isso começou?' no clímax final para criar um seamless loop perfeito de volta aos primeiros segundos sem parecer corte seco de fim de vídeo
- exemplos: https://www.youtube.com/watch?v=BOWCeZuogKI seg 81.0 (trecho 63df3f3a.mp3)
- ids: 63df3f3a

### 7. [jeito_de_falar] Gancho reflexivo de encerramento ('Pode ser o registro silencioso de... / A mesma força que destrói... cria')
- visto em 1 vídeo(s) · nota máx. 8 · modelos: claude-sonnet
- como aplicar: Inserir nos últimos 15s de roteiros de curiosidades uma antítese poética (destruição vs criação, micro vs macro) para elevar o valor percebido do conteúdo antes do CTA de inscrição.
- por que é novo: Nosso roteiro costuma finalizar com CTA direto ou resumo factual simples; aqui ele usa uma antítese poética e filosófica ('destruição na superfície gerando riqueza no subterrâneo') que conecta destruição e criação antes da pergunta de retenção.
- exemplos: https://www.youtube.com/watch?v=kirdD3zdWw0 seg 135.6 (trecho eeae67d2.mp3)
- ids: eeae67d2

### 8. [jeito_de_falar] Gancho condicional imersivo 'Imagina que un día...'
- visto em 1 vídeo(s) · nota máx. 8 · modelos: claude-sonnet
- como aplicar: Abrir o Short/TikTok nos primeiros 3 segundos dizendo: 'Imagina se um dia você abre uma porta no seu quarto e vai parar direto num mundo de RPG com status apelão...'.
- por que é novo: Nossas intros focam em bordoes ou falas diretas do mascote, mas não usam a estrutura de convite mental 'Imagina se um dia você...', que retém a audiência colocando-a na pele do protagonista.
- exemplos: https://www.youtube.com/watch?v=r77umNwvRKU seg 0.0 (trecho 7373216f.mp3)
- ids: 7373216f

### 9. [visual] Transição de foto histórica real para recriação 3D cinematográfica no mesmo ângulo relativo
- visto em 1 vídeo(s) · nota máx. 8 · modelos: claude-sonnet
- como aplicar: Quando falarmos de armamentos ou veículos históricos, parear fotos de museu/arquivo com clipes renderizados em CGI/jogos com câmera dinâmica simulando o disparo.
- por que é novo: Não temos esse contraste de alternar foto de arquivo B&W/colorizada para cena de render 3D/game engine (estilo War Thunder/cinematics) para dar dinamismo visual à narrativa técnica.
- exemplos: https://www.youtube.com/watch?v=CCji3f6Cgj8 seg 14.6 (trecho 20af9c21.mp4)
- ids: 20af9c21

### 10. [visual] Uso de fotografias históricas reais em preto e branco combinadas com colorizações de época e filmagens de arquivo sobrepostas com cortes dinâmicos de zoom sutil.
- visto em 1 vídeo(s) · nota máx. 8 · modelos: gemini
- como aplicar: Incorporar mais fotos e vídeos de arquivo reais e históricos (história militar/engenharia) com tratamento de cor sépia ou PB com zoom digital lento para dar dinamismo a conteúdos informativos.
- por que é novo: Foca em imagens arquivísticas históricas reais de grande escala com acabamento documental de época que não utilizamos com tanta frequência em nossos vídeos cotidianos.
- exemplos: https://www.youtube.com/watch?v=CCji3f6Cgj8 seg 0 (trecho acd8b7ef.mp4)
- ids: acd8b7ef

### 11. [visual] Pig icon with surprised eyes overlay at top-left corner
- visto em 1 vídeo(s) · nota máx. 8 · modelos: gemini
- como aplicar: Adicionar um PNG fixo da mascote com expressão de surpresa no canto superior esquerdo em vídeos de suspense ou bizarrice.
- por que é novo: Usa um ícone de animal temático (porquinho) com expressão de espanto no canto superior fixo durante todo o vídeo, reforçando a identidade visual e o tom de humor.
- exemplos: https://www.youtube.com/watch?v=Z7wrutt3G90 seg 0.0 (trecho d50b51ca.mp4)
- ids: d50b51ca

### 12. [jeito_de_falar] Hook com curiosidade pop linkada à ciência prática ('Já reparou que James Bond pede batida e não mexida?')
- visto em 1 vídeo(s) · nota máx. 8 · modelos: claude-sonnet
- como aplicar: Adotar ganchos que questionam hábitos clássicos de ficção (animes, filmes, games) prometendo uma explicação lógica/científica do mundo real para prender o público nos primeiros 3s.
- por que é novo: Costumamos abrir direto no tema factual ou com piadas/bordões de choque; não usamos perguntas retóricas sobre detalhes de filmes/cultura pop com explicação científica imediata.
- exemplos: https://www.youtube.com/watch?v=d-QU seg 0.0 (trecho 5016bf0d.mp3)
- ids: 5016bf0d

### 13. [efeito] Clímax visual dramático com fogo/maçarico no topo da solução para comprovar o argumento
- visto em 1 vídeo(s) · nota máx. 8 · modelos: claude-sonnet
- como aplicar: Inserir no terço final um elemento de choque/teste de estresse visual (ex: fogo, teste de resistência, explosão curta ou efeito visual radical) para reter até o último segundo.
- por que é novo: Não temos desfecho de retenção baseado em teste extremo ou combustão real como punchline visual antes da CTA.
- exemplos: https://www.youtube.com/watch?v=d-QU seg 54.0 (trecho 5b5a6707.mp4)
- ids: 5b5a6707

### 14. [visual] Teste prático final com maçarico acendendo fogo na camada de álcool da bebida
- visto em 1 vídeo(s) · nota máx. 8 · modelos: gemini
- como aplicar: Incorporar pequenos experimentos controlados com fogo ou reações visuais marcantes no encerramento de vídeos de ciência ou curiosidades.
- por que é novo: Não temos o recurso visual de demonstração com fogo/maçarico para provar dramaticamente a concentração de álcool em um experimento.
- exemplos: https://www.youtube.com/watch?v=d-QU seg 54 (trecho 15763a22.mp4)
- ids: 15763a22

### 15. [visual] Stack progressivo vertical de linhas com bandeira + rage comic + fórmula matemática correspondente
- visto em 1 vídeo(s) · nota máx. 8 · modelos: claude-sonnet
- como aplicar: Em Shorts comparativos entre países ou línguas, montar um layout vertical onde cada linha nova entra abaixo com bandeira, equação lógica simplificada e reação cômica crescente.
- por que é novo: Apresenta comparações linguísticas empilhando visualmente fórmulas aritméticas com expressões de Rage Comics que evoluem de calmo para desespero/raiva extrema.
- exemplos: https://www.youtube.com/watch?v=p-s330V6IDU seg 3.0 (trecho 397a79ca.mp4)
- ids: 397a79ca

### 16. [visual] Contagem regressiva estilizada em 3D com números volumétricos (como o '2' gigante no segundo 21)
- visto em 1 vídeo(s) · nota máx. 8 · modelos: gemini
- como aplicar: Importar assets de números 3D estilizados em formato de vídeo/overlay com canal alpha para transições de contagem ou tópicos.
- por que é novo: Usa um número 3D com chanfro dourado/metálico muito limpo e chamativo, diferente dos nossos números padrão.
- exemplos: https://www.youtube.com/watch?v=M5esBi7xSMc seg 21.1 (trecho 9538f259.mp4)
- ids: 9538f259

### 17. [outro] Uso de cenas geradas por IA com estilo visual consistente de fantasia mecânica/vintage para recontar uma história dramática/cinemática
- visto em 1 vídeo(s) · nota máx. 8 · modelos: gemini
- como aplicar: Integrar prompts de IA estilo dark steampunk/fantasy nos vídeos de histórias misteriosas e de fuga.
- por que é novo: A narrativa visual lembra clássicos adaptados por IA com temática steampunk/fantasia escura (como O Mágico de Oz sombrio) mantendo engajamento alto.
- exemplos: https://www.youtube.com/watch?v=wYsrT7sLWPo seg 3.6 (trecho 05ac530e.mp4)
- ids: 05ac530e

### 18. [visual] Uso de faixa amarela superior com texto em caixa alta destacando a premissa isekai/cultigao do protagonista
- visto em 1 vídeo(s) · nota máx. 8 · modelos: gemini
- como aplicar: Implementar uma tarja superior permanente ou semi-permanente em vídeos de recapitulação de mangá/manhua resumindo o conflito principal do protagonista.
- por que é novo: Manter uma barra de texto fixa no topo com um resumo chamativo da premissa ("Ele caiu no corpo de um líder fracassado...") durante todo o vídeo prende a atenção de quem entra no meio.
- exemplos: https://www.youtube.com/watch?v=YDaBWskB seg 1.6 (trecho 8482f31a.mp4)
- ids: 8482f31a

### 19. [jeito_de_falar] Estrutura de hook cumulativo rápido ('Esse peixe aguenta água ruim, come praticamente de tudo, se reproduz rápido e ainda quase não tem predador...')
- visto em 1 vídeo(s) · nota máx. 8 · modelos: claude-sonnet
- como aplicar: Adotar roteiro com lista rápida de 3 a 4 fatos inacreditáveis/características extremas antes de revelar o elemento principal nos primeiros 10 segundos para reter curiosidade
- por que é novo: Nossas intros em intros_voz focam em frases de abertura diretas ou bordões gravados; essa técnica usa empilhamento acelerado de atributos extremos antes de revelar o nome do sujeito aos 13s
- exemplos: https://www.youtube.com/watch?v=VyUBk3VVPyo seg 1.9 (trecho a465aa05.mp3)
- ids: a465aa05

### 20. [visual] Vetores/setas bidirecionais de forças opostas com fissuras de tensão na superfície do astro
- visto em 1 vídeo(s) · nota máx. 8 · modelos: claude-sonnet
- como aplicar: Criar preset de animação para conceitos de física/destruição onde setas de tração aparecem enquanto rachaduras surgem sobre a imagem do elemento central.
- por que é novo: Mostra visualmente o 'limite de Roche' e forças diferenciais usando setas opostas e rachaduras sincronizadas na geometria do corpo celeste.
- exemplos: https://www.youtube.com/watch?v=r244g1U6-bc seg 16.3 (trecho 9ff5f93c.mp4)
- ids: 9ff5f93c

### 21. [efeito] Anel de detritos/fragmentos orbitando o planeta após destruição
- visto em 1 vídeo(s) · nota máx. 8 · modelos: claude-sonnet
- como aplicar: Adicionar preset de loop/camada de partículas 'debris_orbit' para representar impactos cósmicos, fragmentação de luas ou satélites.
- por que é novo: Nosso acervo de fx tem cortes e fumaça, mas não partículas/escombros volumétricos orbitando em anel tipo Saturno ao redor do objeto.
- exemplos: https://www.youtube.com/watch?v=r244g1U6-bc seg 19.9 (trecho 50738594.mp4)
- ids: 50738594

### 22. [jeito_de_falar] Gancho de 'ponto fraco curioso' com reviravolta explicativa e teste prático
- visto em 1 vídeo(s) · nota máx. 8 · modelos: claude-sonnet
- como aplicar: Em roteiros sobre materiais, invenções ou curiosidades científicas, incluir sempre a seção do 'calcanhar de Aquiles' ou contraindicação bizarra aos 75% do vídeo para renovar a retenção antes do CTA.
- por que é novo: Apresenta um 'super-material' incrível, mas no clímax do vídeo introduz intencionalmente o seu ponto fraco/defeito ('Mas o produto tem um ponto fraco muito curioso: basta jogar sal...') demonstrando a dissolução imediata e finalizando com a implicação lógica ('não funciona na água do mar'). Nosso formato foca muito em fatos lineares sem essa quebra de expectativa no terço final.
- exemplos: https://www.youtube.com/watch?v=xSzOJAgDVD8 seg 25.5 (trecho 265b8868.mp3)
- ids: 265b8868

### 23. [visual] Zoom dramático com distorção de foco na reação de pânico da protagonista
- visto em 1 vídeo(s) · nota máx. 8 · modelos: gemini
- como aplicar: Aplicar zoom in rápido combinado com leve desfoque nas bordas (radial blur) nos momentos de revelação ou choque dos personagens.
- por que é novo: Foca na expressão de choque de forma muito intensa e cinematográfica, ideal para o início de reviravoltas em vídeos de drama.
- exemplos: https://www.youtube.com/watch?v=FrdfvS-hFWM seg 25.8 (trecho df8ba7c1.mp4)
- ids: df8ba7c1

### 24. [jeito_de_falar] Uso de 'bicho escroto' e 'tecnologia doida' para qualificar maquinário técnico/avançado de forma ultra-coloquial
- visto em 1 vídeo(s) · nota máx. 8 · modelos: claude-sonnet
- como aplicar: Flexibilizar o tom dos roteiros sobre ferramentas/ciência adotando hipérboles informais de admiração ('é um bicho muito escroto', 'tecnologia doida')
- por que é novo: Nosso acervo de roteiros e dublagens tende a usar explicações científicas ou termos neutros; o canal parceiro vulgariza positivamente a eficiência tecnológica ('um bicho muito escroto')
- exemplos: https://www.youtube.com/watch?v=JpXFH7 seg 7.0 (trecho 8f640022.mp3)
- ids: 8f640022

### 25. [visual] Uso de personagem animado 2D integrado na lateral inferior do vídeo reagindo e apontando para as cenas
- visto em 1 vídeo(s) · nota máx. 8 · modelos: gemini
- como aplicar: Criar variações de posicionamento do nosso avatar mascote fixo no canto inferior esquerdo/direito com animações de corpo inteiro gesticulando durante explicações técnicas.
- por que é novo: Apesar de termos mascotes, a nossa integração e posicionamento estático dinâmico no canto com falas explicativas no estilo narrador-personagem com avatar humanóide cartoon próprio difere do nosso padrão atual de uso de mascotes reativas.
- exemplos: https://www.youtube.com/watch?v=JpXFH7 seg 2.5 (trecho 565c9d17.mp4)
- ids: 565c9d17

### 26. [gíria] Uso de termos coloquiais fortes e expressivos ('um bicho muito escroto', 'zero bala')
- visto em 1 vídeo(s) · nota máx. 8 · modelos: gemini
- como aplicar: Temperar os roteiros descritivos com expressões populares brasileiras de forte contraste com alta tecnologia.
- por que é novo: Vocabulário técnico misturado com gírias de forte apelo popular e regional brasileiro para descrever tecnologia de ponta.
- exemplos: https://www.youtube.com/watch?v=JpXFH7 seg 7.4 (trecho 75521d89.mp3)
- ids: 75521d89

### 27. [jeito_de_falar] Hook com paradoxo de escala extrema ('um simples X podia destruir uma fábrica inteira')
- visto em 1 vídeo(s) · nota máx. 8 · modelos: claude-sonnet
- como aplicar: Estruturar aberturas de curiosidades usando a fórmula: 'Sabia que um simples [objeto insignificante] quase destruiu [algo gigantesco] nos anos [década]?'
- por que é novo: Contraste narrativo imediato entre um detalhe minúsculo/banal (um número escrito à mão) e uma catástrofe monumental (destruição de uma fábrica de milhares de dólares), gerando curiosidade instantânea antes de revelar o tema.
- exemplos: https://www.youtube.com/watch?v=lbNZaiGpGvo seg 0.0 (trecho 967295b7.mp3)
- ids: 967295b7

### 28. [visual] Sequência de imagens macro/zoom estáticas evoluindo para tomada aberta em vídeo mostrando o bando no habitat
- visto em 1 vídeo(s) · nota máx. 8 · modelos: gemini
- como aplicar: Inserir fotos estáticas com zoom in dramático nos primeiros segundos de vídeos de animais antes de soltar a cena principal em movimento.
- por que é novo: Começamos direto com vídeos em movimento sem explorar close-ups extremos iniciais dos detalhes do animal para gerar curiosidade antes da revelação do bando.
- exemplos: https://www.youtube.com/watch?v=Kisv0-FWSho seg 1.0 (trecho 95403218.mp4)
- ids: 95403218

### 29. [piada] Metáfora cômica e culturalmente identificável ('Brasília amarela com hélice voando baixo por Guarulhos')
- visto em 1 vídeo(s) · nota máx. 8 · modelos: claude-sonnet
- como aplicar: Inserir comparações absurdas do imaginário pop brasileiro no roteiro de curiosidades sobre veículos estranhos ou engenhocas
- por que é novo: Usa referências populares brasileiras muito específicas (Mamonas Assassinas / Brasília Amarela / Guarulhos) para criar contraste humorístico com uma geringonça tecnológica
- exemplos: https://www.youtube.com/watch?v=wVRZu9dsskA seg 45.0 (trecho 5669445d.mp3)
- ids: 5669445d

### 30. [jeito_de_falar] Gancho com negação imediata de suposições intuitivas ('Este homem não está cavando neve ou areia...')
- visto em 1 vídeo(s) · nota máx. 8 · modelos: claude-sonnet
- como aplicar: Em roteiros com cenas visuais enganosas ou surpreendentes, abrir a narração com 'Você pode achar que [X], mas na verdade é [Y]' ou 'Isso não é [suposição óbvia]'.
- por que é novo: Em vez de abrir com pergunta genérica ou afirmação descritiva padrão, abre desmentindo o que os olhos do espectador imediatamente assumem ao ver a imagem (neve), gerando quebra imediata de expectativa.
- exemplos: https://www.youtube.com/watch?v=gE3Bl0FoW8o seg 0.0 (trecho 188d7ff0.mp3)
- ids: 188d7ff0

### 31. [outro] Hook com objeto misterioso/transformável em POV close-up gerando curiosidade ('isso não é X')
- visto em 1 vídeo(s) · nota máx. 8 · modelos: claude-sonnet
- como aplicar: Usar em intros de review ou curiosidades sobre itens inusitados: começar mostrando o item fechado com frase de quebra de expectativa ('Isso não é um chaveiro...') antes da transformação.
- por que é novo: Abertura puramente visual e tátil com negação no gancho ('isso não é 1 caneta') focada em produto curioso/gadget miniaturizado, sem necessidade de narrador em tela.
- exemplos: https://www.youtube.com/watch?v=cfmOF7QyXH0 seg 1.7 (trecho eb355338.mp4)
- ids: eb355338

### 32. [visual] Uso de imagens de arquivo estáticas e surreais de memes antigos (como o Fofão deformado/bochechudo) para ilustrar piadas visuais rápidas
- visto em 1 vídeo(s) · nota máx. 8 · modelos: gemini
- como aplicar: Inserir imagens estáticas de baixa resolução de memes clássicos brasileiros com zoom súbito durante citações cômicas.
- por que é novo: Apesar de termos memes_img, a escolha de imagens de susto/bizzarras de baixa qualidade sincronizadas com narração acelerada gera um efeito de shitpost dinâmico.
- exemplos: https://www.youtube.com/watch?v=eHFIPHvZ7qQ seg 5.3 (trecho 1b25d180.mp4)
- ids: 1b25d180

### 33. [visual] Borda de foto polaroid/analógica escura com vinheta granulada sobre cenas de terror/creepypasta
- visto em 1 vídeo(s) · nota máx. 8 · modelos: claude-sonnet
- como aplicar: Criar um overlay PNG de moldura polaroid escura/vintage para vídeos de contos de terror e mistério no pipeline de geração
- por que é novo: Nosso acervo de hyperframes/dividers usa estilos gráficos coloridos/elétricos, sem moldura fotográfica analógica 'found footage/polaroid' com bordas brancas sutis e revelação escura
- exemplos: https://www.youtube.com/watch?v=V217m seg 3.6 (trecho 45355603.mp4)
- ids: 45355603

### 34. [visual] Tomada aérea cenográfica direta (top-down view) de uma cratera de água azul intensa cercada por vegetação densa.
- visto em 1 vídeo(s) · nota máx. 8 · modelos: gemini
- como aplicar: Empregar imagens de satélite ou drone em perspectiva estritamente vertical (top-down) para introduzir locais misteriosos ou abismos naturais.
- por que é novo: Gera um forte impacto visual de escala e isolamento geográfico que prende a atenção do espectador instantaneamente nos primeiros segundos de um tópico.
- exemplos: https://www.youtube.com/watch?v=5zUdresZmKY seg 18.3 (trecho c768aaf6.mp4)
- ids: c768aaf6

### 35. [visual] Composição em camadas no mesmo ambiente subaquático mostrando escala e comparação entre os espécimes citados
- visto em 1 vídeo(s) · nota máx. 8 · modelos: claude-sonnet
- como aplicar: Nos segundos finais de vídeos comparativos/listas, gerar um quadro síntese reunindo todos os elementos citados no vídeo para ancorar a conclusão e prender o espectador no loop
- por que é novo: Não temos b-roll de síntese comparativa onde todos os sujeitos do roteiro (baleia, tubarão e concha) coexistem num mesmo plano final submerso para recapitulação
- exemplos: https://www.youtube.com/watch?v=n5G0JHa seg 72.1 (trecho b5f59e29.mp4)
- ids: b5f59e29

### 36. [visual] Enquadramento de baixo para cima mostrando a enorme pata ou traseiro de um monstro cobrindo o horizonte da vila
- visto em 1 vídeo(s) · nota máx. 8 · modelos: gemini
- como aplicar: Usar clipes de monstros gigantes ou animais oversized com ângulo contra-plongée extremo e legenda centralizada chamativa
- por que é novo: Perspectiva exagerada de proporção que enfatiza a comédia do tamanho absurdo do monstro comparado ao protagonista
- exemplos: https://www.youtube.com/watch?v=7vVwf4hlUnI seg 0.8 (trecho 97b5bd3e.mp4)
- ids: 97b5bd3e

### 37. [visual] Uso de imagens subaquáticas reais e ilustrativas intercaladas com cenas reais de pesca em tom informativo/documental de alerta
- visto em 1 vídeo(s) · nota máx. 8 · modelos: gemini
- como aplicar: Utilizar B-roll subaquático de alta qualidade combinado com imagens reais de manuseio de grandes peixes em vídeos de alerta de leis ambientais.
- por que é novo: Foca em imagens de arquivo subaquáticas bem cinematográficas aliadas a avisos legais de pesca que agregam autoridade e clareza visual imediata.
- exemplos: https://www.youtube.com/watch?v=wqJvHYqpit4 seg 3.0 (trecho b139e441.mp4)
- ids: b139e441

### 38. [som] Efeito sonoro exagerado de osso quebrando/estalando sincronizado com o susto do apresentador
- visto em 1 vídeo(s) · nota máx. 8 · modelos: gemini
- como aplicar: Adicionar efeito de som de 'crack' seco em momentos de ações corporais exageradas nos nossos vídeos
- por que é novo: Foco em som de impacto corporal cômico sincronizado com reação dramática em close
- exemplos: https://www.youtube.com/watch?v=OMHvhSt0UmE seg 15.0 (trecho 7721a080.mp3)
- ids: 7721a080

### 39. [visual] Menu estilo interface de rede social/comentários com cabeçalho 'SORTED BY COMMENTS' e setas de ordenação no topo do vídeo
- visto em 1 vídeo(s) · nota máx. 8 · modelos: gemini
- como aplicar: Criar um componente overlay em formato de caixa de comentários com título estilizado no topo para introduzir premissas ou dilemas de mangás/manhwas.
- por que é novo: Apresenta uma UI simulando um fórum ou seção de comentários de forma limpa e destacada, gerando contexto narrativo imediato sem uso de legenda comum.
- exemplos: https://www.youtube.com/watch?v=Tv4TcuPT9JI seg 225.5 (trecho df074136.mp4)
- ids: df074136

### 40. [visual] Seta verde grande apontando para a ação do segurança no início do vídeo
- visto em 1 vídeo(s) · nota máx. 8 · modelos: gemini
- como aplicar: Adicionar setas indicativas verdes ou vermelhas dinâmicas nos primeiros segundos de vídeos de fofoca/flagras para destacar detalhes sutis.
- por que é novo: Uso de setas verdes grossas com contorno escuro bem chamativas para guiar o olhar do espectador para o ponto exato de conflito antes da revelação.
- exemplos: https://www.youtube.com/watch?v=CGfcAnwEtD0 seg 1.4 (trecho 62eba2f2.mp4)
- ids: 62eba2f2

(+ 487 grupo(s) mais fracos: vistos em 1 vídeo só; ficam no acervo.jsonl)
