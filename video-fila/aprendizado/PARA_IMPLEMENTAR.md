# Aprendizado com os parceiros — PARA IMPLEMENTAR (refeito a cada rodada; não editar à mão)

Atualizado 16/11/2026 22:37. Gerado por D:\video-fila\aprendizado.py.

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

## B. Candidatos (sem resposta em 24 h): 451 grupo(s), os 40 mais fortes

### 1. [visual] Uso de logos de marcas/entidades como elemento de cenário (diegetico)
- visto em 1 vídeo(s) · nota máx. 7 · modelos: gemini
- como aplicar: Ao inserir ícones ou logos, usar a ferramenta de perspectiva/distorção para que o objeto pareça estar deitado no chão do vídeo original.
- por que é novo: O logo do McDonald's aparece 'dentro' do campo, inclinado seguindo a perspectiva da grama, e não apenas como um adesivo por cima.
- exemplos: https://www.youtube.com/watch?v=Ag2D6QtuPWE seg 2.2 (trecho f519f8dd.mp4)
- ids: f519f8dd

### 2. [visual] Tela de comentário do TikTok no topo como gancho de abertura
- visto em 1 vídeo(s) · nota máx. 7 · modelos: claude-sonnet
- como aplicar: Começar vídeos com print de comentário/pergunta real sobre o tema, mostrando na tela por 2-3 segundos antes de responder, criando hook mais forte
- por que é novo: Usar screenshot de comentário real como elemento visual de abertura (não apenas ler comentário) estabelece contexto de forma mais autêntica e visual
- exemplos: https://www.youtube.com/watch?v=pIDoqR8f6RY seg 1.5 (trecho c434ec6d.mp4)
- ids: c434ec6d

### 3. [visual] Sobreposição de elementos históricos (jornais e fotos) na base da tela
- visto em 1 vídeo(s) · nota máx. 7 · modelos: gemini
- como aplicar: Usar ferramentas de IA para gerar 'flat lay' de evidências criminais que combinem com o bioma do vídeo (ex: papéis molhados na lama).
- por que é novo: Diferente de nossos overlays padrão, aqui os jornais parecem espalhados no chão da própria cena da floresta, integrando a 'evidência' ao ambiente.
- exemplos: https://www.youtube.com/watch?v=4ZqjVntf170 seg 34.4 (trecho 3f358079.mp4)
- ids: 3f358079

### 4. [visual] Texto 3D amarelo ouro com sombra (CR7) sobreposto ao campo
- visto em 1 vídeo(s) · nota máx. 7 · modelos: claude-sonnet
- como aplicar: Adicionar fonte 3D dourada para destacar nomes importantes, números, ou termos-chave em momentos de ênfase (apresentação de personagem, estatística impactante)
- por que é novo: Texto volumoso dourado com profundidade 3D que destaca nome/identificação de forma premium, diferente das legendas planas que vocês usam
- exemplos: https://www.youtube.com/watch?v=KBx0yQiExIg seg 5.3 (trecho 4ee4f25d.mp4)
- ids: 4ee4f25d

### 5. [visual] Seta indicativa curva com preenchimento sólido e borda
- visto em 1 vídeo(s) · nota máx. 7 · modelos: gemini
- como aplicar: Criar um asset de seta curva (PNG ou Shape Layer) e animar a escala/opacidade quando citar que o jogador estava 'livre'.
- por que é novo: Usamos emojis de seta, mas esta é uma forma gráfica personalizada que aponta com precisão para o jogador livre, guiando o olhar do espectador.
- exemplos: https://www.youtube.com/watch?v=KBx0yQiExIg seg 8.8 (trecho 2fe5ea37.mp4)
- ids: 2fe5ea37

### 6. [visual] Uso de clipes de arquivo/nostalgia com qualidade propositalmente baixa (VHS/档案)
- visto em 1 vídeo(s) · nota máx. 7 · modelos: claude-sonnet
- como aplicar: Para vídeos sobre nostalgia, rankings históricos ou 'você lembra', buscar e usar clipes de arquivo reais da época mencionada. Manter a qualidade baixa propositalmente (não tentar 'melhorar') para autenticidade. Pode ser aplicado em vídeos sobre cultura pop dos anos 90/2000, músicas antigas, etc
- por que é novo: Todo o vídeo usa footage de época (anos 90-2000) com qualidade de arquivo, granulado, cores saturadas. Não temos esse recurso visual de 'estética retrô' aplicada de forma consistente
- exemplos: https://www.youtube.com/watch?v=vw5vR0ca0ck seg 11.6 (trecho 64cfcf8a.mp4)
- ids: 64cfcf8a

### 7. [visual] Moldura/borda animada branca irregular (estilo recorte) ao redor do vídeo principal nos quadros 3-26s
- visto em 1 vídeo(s) · nota máx. 7 · modelos: claude-sonnet
- como aplicar: Criar mask overlay com borda irregular/orgânica (papel rasgado, tinta escorrida) para aplicar em momentos de close-up ou revelação. Adicionar aos overlays como 'fx_torn_frame' ou 'fx_cutout_border'
- por que é novo: Efeito de mask/frame orgânico que simula 'recorte físico' ou 'papel rasgado' ao redor do conteúdo principal. Diferente dos masks geométricos que vocês têm
- exemplos: https://www.youtube.com/watch?v=tdhEfw2nI8w seg 3 (trecho f58a05d0.mp4)
- ids: f58a05d0

### 8. [jeito_de_falar] Narração com tom de 'revelação' e suspense
- visto em 1 vídeo(s) · nota máx. 7 · modelos: gemini
- como aplicar: Inserir frases de 'validação do mestre' no roteiro, focando na habilidade do executor para gerar admiração no espectador.
- por que é novo: A fala 'foi só no final que eu entendi o que era ser um especialista' cria um pico de retenção emocional que não usamos em vídeos puramente informativos.
- exemplos: https://www.youtube.com/watch?v=tdhEfw2nI8w seg 15.0
- ids: 8872a94b

### 9. [visual] Perspectiva 3D do frame: quadro inclinado flutuando no espaço com fundo preto
- visto em 1 vídeo(s) · nota máx. 7 · modelos: claude-sonnet
- como aplicar: Usar para momentos de 'antes/depois' ou 'transformação' onde queremos destacar a mudança com profundidade visual
- por que é novo: Enquadramento com perspectiva 3D do vídeo flutuando em fundo preto, diferente do enquadramento plano padrão
- exemplos: https://www.youtube.com/watch?v=DXTDDO7dxhQ seg 1.2 (trecho 11277163.mp4)
- ids: 11277163

### 10. [jeito_de_falar] Minimização cômica de arma letal ('palito de dente' para projéteis que mataram Neji)
- visto em 1 vídeo(s) · nota máx. 7 · modelos: claude-sonnet
- como aplicar: Ao descrever mortes ou ferimentos em anime, usar termos cotidianos diminutivos ('palito', 'espetinho', 'furinho') para criar contraste cômico com gravidade da cena
- por que é novo: Técnica de contraste: chamar arma mortal de objeto inofensivo doméstico para destacar absurdo da situação. Não vejo pattern de diminutivos cômicos para armas/ataques nos sfx ou jeito_de_falar catalogados
- exemplos: https://www.youtube.com/watch?v=p1O7bPSuch0 seg 16.4 (trecho 98f5397c.mp3)
- ids: 98f5397c

### 11. [visual] Fotos reais integradas como evidência da história (foto de família)
- visto em 1 vídeo(s) · nota máx. 7 · modelos: claude-sonnet
- como aplicar: Quando personagem descobre algo ou investiga, mostrar 'evidências visuais' (fotos, documentos) como se fossem achados reais dele, usando overlay de foto polaroid ou porta-retrato
- por que é novo: Usa foto de família real/stock como prova visual dentro da narrativa, não como mero fundo decorativo
- exemplos: https://www.youtube.com/watch?v=IkSBYZApXUI seg 137.6 (trecho 403f817e.mp4)
- ids: 403f817e

### 12. [outro] Transição de 'zoom in' rápido em objetos de cena
- visto em 1 vídeo(s) · nota máx. 7 · modelos: gemini
- como aplicar: Adicionar keyframes de zoom rápido (0.5s) em momentos de revelação de objetos importantes na tela.
- por que é novo: O vídeo usa um zoom agressivo e rápido em detalhes (como o cartão da empresa) para manter o dinamismo, algo que não fazemos com tanta frequência.
- exemplos: https://www.youtube.com/watch?v=IkSBYZApXUI seg 21.7 (trecho 748ce4b2.mp4)
- ids: 748ce4b2

### 13. [jeito_de_falar] Narração em dupla com personalidades contrastantes (analítico vs entusiasmado)
- visto em 1 vídeo(s) · nota máx. 7 · modelos: claude-sonnet
- como aplicar: Testar formato de dois narradores com vozes IA distintas: um mais técnico/sério e outro irreverente fazendo piadas e comentários informais. Criar banter natural entre eles
- por que é novo: Nosso formato usa narração solo. Este vídeo alterna entre narrador sério (Whiz) e comentarista informal/engraçado (Boomstick) criando dinâmica cômica
- exemplos: https://www.youtube.com/watch?v=VhKtn3G5eM4 seg 73.1 (trecho 2a89f899.mp3)
- ids: 2a89f899

### 14. [efeito] Efeito de flash estroboscópico de energia com distorção rítmica e duplicação de personagem (After Image style)
- visto em 1 vídeo(s) · nota máx. 7 · modelos: gemini
- como aplicar: Aplicar o efeito de múltiplas cópias translúcidas com desfoque de movimento horizontal em cenas de ação rápida ou revelação de poder.
- por que é novo: Duplica e desfoca o personagem rapidamente em três instâncias para transmitir velocidade extrema sincronizada com a fala de combate.
- exemplos: https://www.youtube.com/watch?v=VhKtn3G5eM4 seg 658.3 (trecho 279c1e17.mp4)
- ids: 279c1e17

### 15. [jeito_de_falar] Ritmo de explicação rápido e denso: empilha fatos históricos cronológicos sem pausas dramáticas, estilo 'info dump' educacional
- visto em 1 vídeo(s) · nota máx. 7 · modelos: claude-sonnet
- como aplicar: Em vídeos de lore/explicação, testar abordagem mais acadêmica: 'Vamos explicar a linha do tempo completa', depois enumerar fatos cronologicamente sem pausas dramáticas. Priorizar densidade de informação sobre construção emocional
- por que é novo: Nossa narração tende a ser mais dramática/emocional. Este canal usa tom professoral objetivo, entregando timeline densa sem tentar criar suspense artificial - puro conteúdo informativo em alta velocidade
- exemplos: https://www.youtube.com/watch?v=8Hudk6XCDC4 seg 0 (trecho b6d6ae8b.mp3)
- ids: b6d6ae8b

### 16. [visual] Uso de legendas destacadas apenas em palavras-chave dentro da frase.
- visto em 1 vídeo(s) · nota máx. 7 · modelos: gemini
- como aplicar: Ao legendar, deixar a frase em branco e destacar apenas o termo técnico ou nome do personagem em uma cor vibrante (ex: amarelo ou ciano).
- por que é novo: Dá ênfase dinâmica ao que é importante sem poluir a tela com legendas completas, mantendo o foco no que é crucial.
- exemplos: https://www.youtube.com/watch?v=8Hudk6XCDC4 seg 493.3 (trecho f649c45b.mp4)
- ids: f649c45b

### 17. [visual] Texto amarelo com borda/sombra preta forte, sempre na parte inferior, com palavras-chave em caixa alta
- visto em 1 vídeo(s) · nota máx. 7 · modelos: claude-sonnet
- como aplicar: Padronizar legendas com cor amarela (#FFFF00 ou similar), stroke preto de 8-10px, sempre posicionadas no terço inferior. Usar para destacar palavras-chave da narração em momentos de tensão ou revelação
- por que é novo: Vocês usam legendas, mas essa combinação específica (amarelo vibrante + contorno preto grosso + posicionamento consistente embaixo) cria mais contraste e legibilidade que nossas legendas atuais
- exemplos: https://www.youtube.com/watch?v=D0TDFTzGQ9M seg 4.4 (trecho a5b0dbd0.mp4)
- ids: a5b0dbd0

### 18. [visual] Texto centralizado com destaque em palavra-chave
- visto em 1 vídeo(s) · nota máx. 7 · modelos: gemini
- como aplicar: Em frases longas, destacar a palavra principal com uma cor vibrante (ex: amarelo ou ciano) e um leve aumento de escala para criar ênfase visual.
- por que é novo: O uso de uma palavra destacada em cor diferente no centro da tela ajuda a manter o foco do espectador em pontos cruciais da história.
- exemplos: https://www.youtube.com/watch?v=PUNnTzYCEmc seg 66.9 (trecho f22e8af3.mp4)
- ids: f22e8af3

### 19. [visual] Zoom dinâmico no objeto específico (fita adesiva da caixa)
- visto em 1 vídeo(s) · nota máx. 7 · modelos: claude-sonnet
- como aplicar: Quando narrar ações com objetos específicos (pegar chave, abrir carta, cortar algo), fazer zoom fechado no objeto exato durante 0.5-1s antes da ação acontecer
- por que é novo: Fazemos zoom em personagens/cenas gerais. Este zoom fecha especificamente em um objeto pequeno e relevante da ação (a fita) sincronizado com a fala
- exemplos: https://www.youtube.com/watch?v=lyA- seg 38.2 (trecho 21cb7c3e.mp4)
- ids: 21cb7c3e

### 20. [visual] Uso de personagem/mascote integrado com expressão pensativa sobreposta no vídeo com borda/sombra estilizada.
- visto em 1 vídeo(s) · nota máx. 7 · modelos: gemini
- como aplicar: Inserir nossa pose de mascote correspondente ao sentimento da cena (ex: pose_shock ou pose_angry) centralizada na parte inferior com leve escala e sombra para reter a atenção.
- por que é novo: Apesar de termos poses de mascote, o uso dessa reação específica posicionada na parte inferior central combinada com o tema cria uma identidade visual forte nos Shorts estilo narrador.
- exemplos: https://www.youtube.com/watch?v=lyA- seg 2.9 (trecho 28ae2456.mp4)
- ids: 28ae2456

### 21. [visual] Efeito de brilho/luz rosa nos olhos do personagem durante momento romântico
- visto em 1 vídeo(s) · nota máx. 7 · modelos: claude-sonnet
- como aplicar: Adicionar overlay de brilho rosa suave nos olhos do personagem quando ele imagina cenários românticos ou fica encantado. Pode ser combinado com fx_hearts ou fx_blush existentes
- por que é novo: Não temos esse efeito de iluminação rosa nos olhos para destacar momentos de romantismo ou devaneio
- exemplos: https://www.youtube.com/watch?v=RD2C5FXSIYk seg 32.3 (trecho d8f1bb47.mp4)
- ids: d8f1bb47

### 22. [visual] Gradiente de cor suave no fundo (rosa/roxo) durante cenas românticas/imaginação
- visto em 1 vídeo(s) · nota máx. 7 · modelos: claude-sonnet
- como aplicar: Em vez de sempre usar backgrounds complexos, aplicar gradientes coloridos suaves (rosa, roxo, azul claro) durante devaneios românticos ou momentos emocionais para criar atmosfera
- por que é novo: Usamos backgrounds de anime gerados mas não esse tipo de gradiente suave e minimalista para destacar o mood romântico
- exemplos: https://www.youtube.com/watch?v=RD2C5FXSIYk seg 10.8 (trecho 214d8858.mp4)
- ids: 214d8858

### 23. [efeito] Zoom dramático lento (slow zoom-in) em expressões faciais de choque/vergonha
- visto em 1 vídeo(s) · nota máx. 7 · modelos: gemini
- como aplicar: Aplicar um keyframe de escala (100% para 110%) durante a fala de momentos de 'vergonha' do personagem.
- por que é novo: Nós usamos cortes rápidos; o zoom lento foca na emoção e cria uma pausa cômica mais efetiva.
- exemplos: https://www.youtube.com/watch?v=RD2C5FXSIYk seg 17.9 (trecho 209eed20.mp4)
- ids: 209eed20

### 24. [visual] Título fixo amarelo no topo durante todo o vídeo ('A ORIGEM DAQUELE MONSTRO MARINHO')
- visto em 1 vídeo(s) · nota máx. 7 · modelos: claude-sonnet
- como aplicar: Adicionar título de contexto fixo no topo em fonte amarela (impact/bangers) que permaneça visível durante toda a narrativa para ancorar o tema
- por que é novo: Mantém contexto visual permanente, funciona como branding/ancoragem narrativa ao longo de todo o vídeo, diferente de legendas que mudam
- exemplos: https://www.youtube.com/watch?v=jYETXAo06Fo seg 0 (trecho 9314f9f7.mp4)
- ids: 9314f9f7

### 25. [visual] Zoom dinâmico e cortes rápidos em momentos de ação
- visto em 1 vídeo(s) · nota máx. 7 · modelos: gemini
- como aplicar: Aplicar zooms graduais ou cortes secos (jump cuts) em momentos de tensão na narração, focando nas expressões faciais para aumentar o engajamento emocional.
- por que é novo: O vídeo alterna entre planos abertos e zooms fechados no rosto dos personagens ou na criatura, aumentando a sensação de urgência e perigo.
- exemplos: https://www.youtube.com/watch?v=jYETXAo06Fo seg 19.6 (trecho c5dabf36.mp4)
- ids: c5dabf36

### 26. [visual] Interface UI do jogo sobreposta (card da moto no segundo 11.5, tela de cadastro 21.4-28.0)
- visto em 1 vídeo(s) · nota máx. 7 · modelos: claude-sonnet
- como aplicar: Quando explicar funcionalidade de app/jogo, capturar e sobrepor a tela real da interface. Torna tutorial mais claro e confiável
- por que é novo: Mostramos texto na tela, mas não reproduzimos a UI real do sistema sendo explicado
- exemplos: https://www.youtube.com/watch?v=JSTy0fcFtNY seg 11.5 (trecho 73aa0a5d.mp4)
- ids: 73aa0a5d

### 27. [visual] Uso de 'cursor' simulado na tela
- visto em 1 vídeo(s) · nota máx. 7 · modelos: gemini
- como aplicar: Adicionar um elemento gráfico de cursor de mouse em vídeos de tutorial para indicar botões ou campos de preenchimento.
- por que é novo: O vídeo usa um cursor de mouse para guiar o olhar do espectador exatamente onde ele deve clicar.
- exemplos: https://www.youtube.com/watch?v=JSTy0fcFtNY seg 4.9 (trecho 43f9981e.mp4)
- ids: 43f9981e

### 28. [visual] Imagens de filmes/desenhos posicionadas como objetos 3D no mundo (não overlay 2D)
- visto em 1 vídeo(s) · nota máx. 7 · modelos: claude-sonnet
- como aplicar: No ambiente 3D proposto acima, renderizar as imagens referenciadas como texturas em planos 3D posicionados estrategicamente no percurso da câmera, com iluminação e sombras
- por que é novo: Vocês sobrepõem imagens/memes como layers 2D. Aqui as imagens dos filmes são objetos físicos dentro do mundo 3D (parecem quadros pendurados ou telas), com perspectiva e oclusão real
- exemplos: https://www.youtube.com/watch?v=Fxn73A7jwwU seg 2.9 (trecho 608d5105.mp4)
- ids: 608d5105

### 29. [visual] Efeito de linhas de tremor/vibração brancas ao redor da mão no momento da transformação
- visto em 1 vídeo(s) · nota máx. 7 · modelos: claude-sonnet
- como aplicar: Adicionar overlay de linhas de tremor em momentos de tensão física, transformação ou esforço extremo do personagem. Combina bem com narração de dor ou mudança corporal
- por que é novo: As linhas de tremor/impacto desenhadas manualmente não aparecem na lista de overlays. É diferente do fx_impact - são linhas de manga/anime indicando vibração
- exemplos: https://www.youtube.com/watch?v=Cab-g7KPPYg seg 50.2 (trecho 47f34660.mp4)
- ids: 47f34660

### 30. [visual] Elementos de desenho minimalista (ícones de controle, moedas, calendário) com traço fino e simples
- visto em 1 vídeo(s) · nota máx. 7 · modelos: claude-sonnet
- como aplicar: Criar biblioteca de ícones line-art simples para dados/comparações: calendário, dinheiro, objetos. Mais clean que emoji, mais humano que ícone vetorial padrão
- por que é novo: Vocês têm emojis elaborados e memes, mas não ícones minimalistas desenhados à mão no estilo infográfico limpo
- exemplos: https://www.youtube.com/watch?v=DcF6SJ seg 3.9 (trecho 28ed22f8.mp4)
- ids: 28ed22f8

### 31. [visual] Texto em aspas duplas para termo técnico/polêmico destacando que é citação ou jargão específico
- visto em 1 vídeo(s) · nota máx. 7 · modelos: claude-sonnet
- como aplicar: Ao introduzir termos técnicos, gírias ou palavras polêmicas relevantes para o tema, colocar o termo entre aspas visuais na tela para sinalizar que é um conceito importante ou controverso
- por que é novo: Usamos aspas ocasionalmente mas não como recurso visual consistente para destacar termos técnicos ou jargões que merecem atenção especial do espectador
- exemplos: https://www.youtube.com/watch?v=IC70RkNeKtI seg 21.2 (trecho 35ebb184.mp4)
- ids: 35ebb184

### 32. [visual] Onomatopeia visual 'Ah!~' integrada ao quadro (segundo 38.7)
- visto em 1 vídeo(s) · nota máx. 7 · modelos: claude-sonnet
- como aplicar: Criar overlays de texto estilizado com onomatopeias brasileiras ('Ah!', 'Uau!', 'Hã?!') com fonte manuscrita e posicionamento que pareça parte da ilustração. Combinar com fx_exclaim existente
- por que é novo: Temos emojis e overlays de reação, mas não texto de onomatopeia desenhado como parte da cena. Esse recurso adiciona expressividade
- exemplos: https://www.youtube.com/watch?v=Om6TMciwBaU seg 38.7 (trecho e7ef0d8b.mp4)
- ids: e7ef0d8b

### 33. [visual] Paleta de cor sépia/laranja intensa em cena de ação
- visto em 1 vídeo(s) · nota máx. 7 · modelos: claude-sonnet
- como aplicar: Aplicar grading sépia-laranja intenso em momentos de batalha épica ou apocalíptica, complementando os fillers de batalha que já têm. Cria atmosfera mais dramática que as cores neon
- por que é novo: Tratamento de cor extremamente saturado (laranja/amarelo queimado) para cena de combate - diferente das cores vibrantes elétricas que vocês já usam
- exemplos: https://www.youtube.com/watch?v=J seg 987.1 (trecho 78d3ffe5.mp4)
- ids: 78d3ffe5

### 34. [visual] Olhos brilhantes amarelo-dourado em close extremo de titã
- visto em 1 vídeo(s) · nota máx. 7 · modelos: claude-sonnet
- como aplicar: Criar overlay de olhos brilhantes amarelo-dourado para momentos de poder/ameaça em animes de ação. Aplicar em close-ups de antagonistas ou transformações.
- por que é novo: Não temos overlays de olhos brilhantes com essa intensidade e cor específica (amarelo-dourado). Nossos fx_anger e fx_impact são diferentes.
- exemplos: https://www.youtube.com/watch?v=cqoURVPgGPo seg 439 (trecho d886d76b.mp4)
- ids: d886d76b

### 35. [visual] Silhueta escura do personagem contra luz branca dramática com efeito de partículas/energia ao redor
- visto em 1 vídeo(s) · nota máx. 7 · modelos: claude-sonnet
- como aplicar: Usar nos momentos de revelação ou transformação do protagonista. Combinar com nossos fx_powerup ou fx_glitch mas adicionar layer de silhueta escura com backlight branco intenso
- por que é novo: Embora tenhamos efeitos de luz e bokeh, não temos essa composição específica de silhueta contra luz com dispersão de partículas que cria um momento épico/revelação
- exemplos: https://www.youtube.com/watch?v=Ex8wibsqnUo seg 52 (trecho 55e5a37d.mp4)
- ids: 55e5a37d

### 36. [visual] Gradiente rosa-vermelho intenso com silhueta de criatura demoníaca em primeiro plano
- visto em 1 vídeo(s) · nota máx. 7 · modelos: claude-sonnet
- como aplicar: Criar overlay de gradiente rosa-magenta-vermelho para momentos de terror/suspense/poder demoníaco. Combinar com silhuetas de monstros ou antagonistas
- por que é novo: Não temos paletas de cor tão saturadas em rosa/vermelho com silhuetas ameaçadoras. Nossos overlays tendem a cores mais elétricas (azul, verde, roxo)
- exemplos: https://www.youtube.com/watch?v=Ex8wibsqnUo seg 60 (trecho 5104c7b4.mp4)
- ids: 5104c7b4

### 37. [visual] Transição com fundo branco minimalista e linhas de velocidade (speed lines)
- visto em 1 vídeo(s) · nota máx. 7 · modelos: claude-sonnet
- como aplicar: Criar overlay de transição com speed lines em branco/preto para momentos de ação rápida ou mudança de contexto no vídeo. Usar entre blocos narrativos diferentes
- por que é novo: Vocês têm dividers coloridos e elétricos, mas não essa transição limpa com speed lines em fundo branco que dá sensação de movimento rápido entre cenas de anime
- exemplos: https://www.youtube.com/watch?v=Ep seg 4.7 (trecho e0428e20.mp4)
- ids: e0428e20

### 38. [efeito] Blur/desfoque intenso na parte superior e inferior da tela, criando foco no centro com efeito cinemático
- visto em 1 vídeo(s) · nota máx. 7 · modelos: claude-sonnet
- como aplicar: Criar overlay 'cinematic_blur_bars.png' com blur gaussiano nas faixas superior (20-25% altura) e inferior (20-25% altura), deixando centro cristalino. Aplicar em camada superior com opacidade 60-80% em vídeos dramáticos/tensos para dar sensação de 'filme de cinema'.
- por que é novo: Temos fx_blinds e fx_cap_blurin, mas não usamos blur nas bordas superior/inferior de forma consistente por todo o vídeo. Este efeito cria aspecto cinematográfico 2.35:1 (letterbox) e direciona atenção para o centro onde está a ação.
- exemplos: https://www.youtube.com/watch?v=GbSAYLY297Y seg 0 (trecho 18616ba9.mp4)
- ids: 18616ba9

### 39. [visual] Enquadramento com desfoque de fundo (bokeh artificial) no topo e base
- visto em 1 vídeo(s) · nota máx. 7 · modelos: gemini
- como aplicar: Adicionar uma camada de ajuste com desfoque gaussiano e uma máscara de gradiente nas extremidades do vídeo 9:16.
- por que é novo: O vídeo usa um efeito de profundidade de campo (blur) nas bordas superior e inferior para focar a atenção no centro da cena cinematográfica.
- exemplos: https://www.youtube.com/watch?v=GbSAYLY297Y seg 11.5 (trecho d6cd9bcc.mp4)
- ids: d6cd9bcc

### 40. [visual] Frame dentro do frame (letterbox criativo)
- visto em 1 vídeo(s) · nota máx. 7 · modelos: claude-sonnet
- como aplicar: Usar para cenas de flashback, memórias ou quando mostrar 'o que o personagem está vendo'. Adiciona camada de storytelling visual
- por que é novo: O vídeo de anime fica emoldurado dentro de um frame menor com bordas grossas, criando efeito de 'assistindo TV' ou 'vídeo dentro do vídeo'. Diferente dos overlays que vocês têm
- exemplos: https://www.youtube.com/watch?v=Ydnsx5cfeQA seg 0 (trecho 97dd777a.mp4)
- ids: 97dd777a

(+ 411 grupo(s) mais fracos: vistos em 1 vídeo só; ficam no acervo.jsonl)
