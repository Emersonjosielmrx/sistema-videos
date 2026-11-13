# Aprendizado com os parceiros — PARA IMPLEMENTAR (refeito a cada rodada; não editar à mão)

Atualizado 13/11/2026 08:39. Gerado por D:\video-fila\aprendizado.py.

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

## B. Candidatos (sem resposta em 24 h): 635 grupo(s), os 40 mais fortes

### 1. [visual] Texto centralizado em caixa preta/amarela com borda preta ('Original step:' e 'Jennie doing it in encore:')
- visto em 1 vídeo(s) · nota máx. 9 · modelos: gemini
- como aplicar: Usar padrão de fonte grossa (ex: Montserrat-ExtraBold ou LuckiestGuy) com borda preta grossa e fundo contrastante para títulos comparativos.
- por que é novo: Usa legendas em destaque com contraste forte para contextualizar a mudança de comportamento entre a cena original e a repetição.
- exemplos: https://www.youtube.com/watch?v=cO20RvgiMYk seg 0.8 (trecho 0dc54ad2.mp4)
- ids: 0dc54ad2

### 2. [outro] Narrativa focada em 'micro-detalhes' visuais (escovar dentes, mexer açúcar, chaves voando).
- visto em 1 vídeo(s) · nota máx. 8 · modelos: gemini
- como aplicar: Em roteiros de suspense, inserir inserts de 1 a 2 segundos focados apenas no objeto que prova a mudança de comportamento do personagem.
- por que é novo: Nós costumamos focar na ação principal; o parceiro usa o close-up em objetos para criar tensão antes da revelação.
- exemplos: https://www.youtube.com/watch?v=53kBEy2GiV4 seg 3.5 (trecho d4fd28f7.mp4)
- ids: d4fd28f7

### 3. [jeito_de_falar] Gancho de continuação cortado 'e aí cê me pergunta, será que é possível que...'
- visto em 1 vídeo(s) · nota máx. 8 · modelos: claude-sonnet
- como aplicar: Usar como padrão de CTA no fim: começar pergunta retórica relacionada ao tema e cortar antes da resposta para gerar curiosidade e retenção
- por que é novo: Encerramento que cria antecipação através de pergunta retórica inacabada, forçando continuação. Diferente dos nossos CTAs diretos
- exemplos: https://www.youtube.com/watch?v=GkTetcMLBZI seg 19.4
- ids: f68dacd4

### 4. [jeito_de_falar] Uso de analogias regionais/humorísticas ("cavalo manco", "lei na Rota 66")
- visto em 1 vídeo(s) · nota máx. 8 · modelos: gemini
- como aplicar: Incluir expressões coloquiais e comparações inusitadas no roteiro para quebrar a formalidade de tutoriais técnicos.
- por que é novo: Cria uma personalidade marcante e um tom de voz mais autêntico e menos robótico.
- exemplos: https://www.youtube.com/watch?v=lgbIkIG4ea0 seg 1.9 (trecho bbe6d3fa.mp3)
- ids: bbe6d3fa

### 5. [gíria] Uso de gírias brasileiras coloquiais específicas: Zé ruela, tapado, pachorra, desabou a chorar
- visto em 1 vídeo(s) · nota máx. 8 · modelos: claude-sonnet
- como aplicar: Criar glossário de 20-30 expressões brasileiras coloquiais e distribuir 2-3 por script: termos para personagens ruins (Zé ruela, mala, pivete), intensificadores (pra caramba, à beça, do caramba), expressões de emoção (desabar a chorar, dar chilique). Priorizar em momentos de climax emocional.
- por que é novo: Vocabulário super brasileiro e coloquial ('Zé ruela', 'pachorra', 'desabou a chorar', 'pra caramba') que vocês não usam sistematicamente. Torna a narração mais próxima e autêntica.
- exemplos: https://www.youtube.com/watch?v=StMteOasMNk seg 7.7 (trecho 159111fd.mp3)
- ids: 159111fd

### 6. [visual] Etiqueta de contexto temporal/local fixa
- visto em 1 vídeo(s) · nota máx. 8 · modelos: gemini
- como aplicar: Criar um preset de retângulo arredondado amarelo com texto em preto para inserir informações secundárias de local ou data.
- por que é novo: Usa uma 'tag' amarela (ex: EA, 21 DE OUTUBRO) que flutua sobre a imagem para situar o espectador sem precisar narrar a data.
- exemplos: https://www.youtube.com/watch?v=fF5E1jL7skY seg 5.5
- ids: 11c05d82

### 7. [outro] Uso de 'Papo Reto' e 'Minha Tropa'
- visto em 1 vídeo(s) · nota máx. 8 · modelos: gemini
- como aplicar: Substituir introduções genéricas por chamadas de comunidade e usar expressões de afirmação urbana no meio da explicação.
- por que é novo: Linguagem mais informal e tribal que gera conexão imediata com o público jovem/gamer brasileiro.
- exemplos: https://www.youtube.com/watch?v=fF5E1jL7skY seg 1.1
- ids: a146f209

### 8. [jeito_de_falar] Narração com sotaque francês estilizado ('mon ami', 'voilà') misturado ao português
- visto em 1 vídeo(s) · nota máx. 8 · modelos: claude-sonnet
- como aplicar: Adicionar persona de narrador com sotaque característico (francês, russo, italiano) usando expressões típicas do idioma. Criar variações de intro_voz com essa caracterização
- por que é novo: Não temos narrações com sotaque ou expressões em outras línguas integradas ao português de forma cômica
- exemplos: https://www.youtube.com/watch?v=42rmCSvnsvI seg 0 (trecho ee30d195.mp3)
- ids: ee30d195

### 9. [visual] Legenda com sombra projetada e borda colorida (estilo 'impact')
- visto em 1 vídeo(s) · nota máx. 8 · modelos: gemini
- como aplicar: Adotar o padrão de texto com sombra pesada e destacar verbos ou substantivos importantes com cores contrastantes.
- por que é novo: A legibilidade é muito superior à nossa, com destaque para palavras-chave em cores vibrantes (vermelho/ciano) que guiam o olhar.
- exemplos: https://www.youtube.com/watch?v=Js46aiJVP-o seg 708.9 (trecho acda9256.mp4)
- ids: acda9256

### 10. [visual] Animação 2D flat minimalista estilo infográfico educativo
- visto em 1 vídeo(s) · nota máx. 8 · modelos: claude-sonnet
- como aplicar: Criar versões flat/vetoriais de personagens históricos ou conceitos para vídeos educativos. Pode ser usado em stories explicativos sobre anime/mangá, história de estúdios, etc.
- por que é novo: Vocês não têm esse estilo de animação vetorial simplificada e limpa para conteúdo histórico/educativo. É diferente dos overlays e mascotes que já possuem.
- exemplos: https://www.youtube.com/watch?v=yxaegqvl4aE seg 13.5 (trecho c07ed087.mp4)
- ids: c07ed087

### 11. [visual] CTA visual no frame final com URL completa (www.patreon.com/simplehistory no segundo 257.3)
- visto em 1 vídeo(s) · nota máx. 8 · modelos: claude-sonnet
- como aplicar: No último frame, manter o personagem/cena com URL do Patreon/Instagram sobreposta de forma natural. Mais orgânico que um overlay separado. Aumenta memorização do link.
- por que é novo: Vocês têm 'cta_question' mas não CTA com URL completa integrada no último frame da animação de forma orgânica. É mais direto que overlay genérico.
- exemplos: https://www.youtube.com/watch?v=yxaegqvl4aE seg 257.3 (trecho 5fd732ee.mp4)
- ids: 5fd732ee

### 12. [visual] Uso de mapas estilizados com setas animadas para explicar movimentação militar
- visto em 1 vídeo(s) · nota máx. 8 · modelos: gemini
- como aplicar: Criar templates de mapas minimalistas com setas de movimento (vetores) para ilustrar conflitos ou rotas em vídeos de curiosidades históricas ou geográficas.
- por que é novo: Nossas produções atuais focam muito em personagens e memes, mas carecem de elementos visuais de apoio para explicar contextos geográficos ou estratégicos complexos.
- exemplos: https://www.youtube.com/watch?v=yxaegqvl4aE seg 121.9 (trecho d3843de2.mp4)
- ids: d3843de2

### 13. [visual] Interface de tela de ligação com ícones de câmera/mic/desligar sobreposta no quadro
- visto em 1 vídeo(s) · nota máx. 8 · modelos: claude-sonnet
- como aplicar: Criar overlay de interface de app de chamada (WhatsApp/FaceTime style) para cenas onde protagonista está ao telefone ou videochamada. Aplicar quando narração mencionar ligação/contato.
- por que é novo: Simula interface real de chamada de vídeo com botões funcionais, não apenas legenda. Cria imersão visual que não temos em nossos overlays.
- exemplos: https://www.youtube.com/watch?v=IJuMT0agIiE seg 5.4 (trecho b8559b93.mp4)
- ids: b8559b93

### 14. [visual] Uso de elementos gráficos de anime (ícones de exclamação/surpresa) para enfatizar reações.
- visto em 1 vídeo(s) · nota máx. 8 · modelos: gemini
- como aplicar: Adicionar sobreposições de ícones de '!' ou '?' estilo anime sobre os personagens quando houver uma revelação ou surpresa.
- por que é novo: Nós usamos mascotes, mas não usamos elementos visuais típicos de linguagem de anime para pontuar reações dos personagens.
- exemplos: https://www.youtube.com/watch?v=YI5av9lamHQ seg 1568.6 (trecho cecf35c6.mp4)
- ids: cecf35c6

### 15. [visual] Palavras-chave animadas em 3D com borda preta grossa, cores neon variadas (verde limão, ciano, verde escuro) sincronizadas com palavras-chave da narração
- visto em 1 vídeo(s) · nota máx. 8 · modelos: claude-sonnet
- como aplicar: Criar overlays de texto 3D com outline preto grosso para palavras-chave emocionais ou técnicas (ex: 'CHOQUE', 'DESCARGA', 'SISTEMA NERVOSO'). Usar cores neon do nosso palette electric_ mas aplicar em texto 3D maior e mais destacado que as legendas normais
- por que é novo: Vocês têm legendas e texto na tela, mas essas palavras-chave 3D com borda preta grossa e cores neon vibrantes (especialmente o verde limão elétrico) aparecem de forma mais destacada e isolada do que legendas corridas. Cada palavra aparece sozinha enfatizando momentos específicos da narração
- exemplos: https://www.youtube.com/watch?v=B7fObanfoZM seg 2.3 (trecho cf66e5ce.mp4)
- ids: cf66e5ce

### 16. [visual] Legenda com palavras destacadas em cor verde brilhante de alto contraste com borda preta grossa estilo TikTok
- visto em 1 vídeo(s) · nota máx. 8 · modelos: gemini
- como aplicar: Adotar o estilo de destaque de palavras-chave individuais em verde vibrante (#22c55e) com contorno preto grosso na edição de legendas.
- por que é novo: Estilo de destaque dinâmico por palavra-chave em verde neon altamente legível em fundos variados.
- exemplos: https://www.youtube.com/watch?v=B7fObanfoZM seg 2.3 (trecho 0dc2032b.mp4)
- ids: 0dc2032b

### 17. [visual] Transição entre diferentes shows/apresentações da Adele como prova visual
- visto em 1 vídeo(s) · nota máx. 8 · modelos: claude-sonnet
- como aplicar: Quando falar sobre comportamento recorrente de alguém, mostrar 3-4 exemplos visuais diferentes da mesma pessoa fazendo aquilo. Reforça credibilidade e prende atenção com variedade.
- por que é novo: Uso de múltiplos clipes reais da artista em diferentes contextos (dia/noite, diferentes ângulos, diferentes vestidos) como evidência visual do argumento. Não é B-roll genérico, são provas específicas.
- exemplos: https://www.youtube.com/watch?v=HBOvZcSE1os seg 3.2 (trecho 5f327fa9.mp4)
- ids: 5f327fa9

### 18. [visual] Bordas desfocadas coloridas (rosa, azul, laranja) emoldurando o vídeo vertical
- visto em 1 vídeo(s) · nota máx. 8 · modelos: claude-sonnet
- como aplicar: Criar overlay de borda desfocada que muda de cor conforme o mood da cena (rosa para romance, azul para ação, vermelho para tensão). Aplicar como camada de fundo em vídeos verticais
- por que é novo: Não temos esse tratamento de borda colorida desfocada que cria profundidade e destaque para o conteúdo central durante todo o vídeo
- exemplos: https://www.youtube.com/watch?v=Pd98vMXL seg 0 (trecho c70b87b4.mp4)
- ids: c70b87b4

### 19. [visual] Interface de sistema de segurança com texto 'Remote Command: Door Locked' em tela digital tech
- visto em 1 vídeo(s) · nota máx. 8 · modelos: claude-sonnet
- como aplicar: Criar overlays de interface tech (estilo monitor de segurança, sistema de computador, HUD) para introduzir situações ou revelar informações importantes na narrativa. Usar fonte monoespaçada com fundo de tela digital.
- por que é novo: Vocês não têm esse tipo de UI/interface de sistema tecnológico para contextualizar cenários. É diferente de texto simples na tela.
- exemplos: https://www.youtube.com/watch?v=76SYvCtml4k seg 415.5 (trecho b8729832.mp4)
- ids: b8729832

### 20. [visual] Silhueta voadora em contra-luz com efeitos de lens flare dramáticos
- visto em 1 vídeo(s) · nota máx. 8 · modelos: gemini
- como aplicar: Usar imagens de fundo panorâmicas com sobreposição de lens flare e silhuetas misteriosas em cenas de perigo.
- por que é novo: Composição de cena de fundo apocalíptico com criatura flutuando contra forte luz solar e destroços.
- exemplos: https://www.youtube.com/watch?v=76SYvCtml4k seg 2908.0 (trecho 030456b3.mp4)
- ids: 030456b3

### 21. [visual] Texto em caixa alta com stroke verde neon grosso e sombra
- visto em 1 vídeo(s) · nota máx. 8 · modelos: claude-sonnet
- como aplicar: Usar fonte impact ou similar com stroke verde #00FF88 de 8-10px e sombra preta. Aplicar em palavras-chave da narrativa para criar hierarquia visual forte
- por que é novo: Vocês têm legendas com outline mas não esse estilo de stroke verde neon super espesso que vibra contra o fundo escurecido
- exemplos: https://www.youtube.com/watch?v=bh3Ad2MApcc seg 3.8 (trecho 2c8ff716.mp4)
- ids: 2c8ff716

### 22. [visual] Setas vermelhas apontando elementos específicos nos quadros
- visto em 1 vídeo(s) · nota máx. 8 · modelos: claude-sonnet
- como aplicar: Criar overlay de seta vermelha animada (bounce in) para momentos onde precisamos apontar algo específico na imagem/vídeo. Útil em análises de cenas, easter eggs, detalhes que passam despercebidos.
- por que é novo: Usa setas vermelhas grossas para direcionar atenção a detalhes específicos (ex: placa, personagem, objeto na mão). Diferente dos nossos overlays de exclamação/impacto que são mais genéricos.
- exemplos: https://www.youtube.com/watch?v=sMEkq5bruXw seg 2.9 (trecho fc603998.mp4)
- ids: fc603998

### 23. [visual] Uso de seta vermelha animada para apontar elementos específicos na tela.
- visto em 1 vídeo(s) · nota máx. 8 · modelos: gemini
- como aplicar: Criar um asset de seta vermelha com animação de entrada (bounce) para destacar personagens ou objetos mencionados na narração.
- por que é novo: Nós usamos overlays de destaque, mas não temos uma seta dinâmica que 'aponta' para o objeto de interesse, o que ajuda a guiar o olhar do espectador.
- exemplos: https://www.youtube.com/watch?v=sMEkq5bruXw seg 2.9 (trecho 0711aa4e.mp4)
- ids: 0711aa4e

### 24. [efeito] Sobreposição de personagem com transparência (Ghost Overlay)
- visto em 1 vídeo(s) · nota máx. 8 · modelos: gemini
- como aplicar: Recortar o personagem secundário, aumentar a escala, reduzir a opacidade para ~40% e posicionar atrás da camada do personagem principal em momentos de reflexão.
- por que é novo: Um personagem do passado ou memória aparece em tamanho maior e com opacidade reduzida atrás do protagonista para dar contexto emocional.
- exemplos: https://www.youtube.com/watch?v=XNKCOSdfMrU seg 2126.8 (trecho f2fa4e5e.mp4)
- ids: f2fa4e5e

### 25. [visual] Gradiente de cor de fundo animado (amarelo→laranja→roxo)
- visto em 1 vídeo(s) · nota máx. 8 · modelos: claude-sonnet
- como aplicar: Criar presets de gradientes animados que mudem conforme o tom da narrativa (alegre→tenso, calmo→intenso). Aplicar como camada de fundo em momentos de transição emocional
- por que é novo: Nossos dividers são estáticos. Esse vídeo usa transição de cor no próprio fundo que acompanha a progressão da cena (tons quentes→frios para mudança de mood)
- exemplos: https://www.youtube.com/watch?v=ZIGA4roGbmQ seg 222.2 (trecho 8590efc8.mp4)
- ids: 8590efc8

### 26. [visual] Pose dinâmica de ação congelada emângulo lateral (s. 16.8)
- visto em 1 vídeo(s) · nota máx. 8 · modelos: claude-sonnet
- como aplicar: Em cenas de ação ou momento climático, usar enquadramento lateral low-angle com personagem em pose de combate congelada para criar impacto visual
- por que é novo: Enquadramento lateral com personagem em movimento de chute/soco congelado, criando silhueta dinâmica contra o céu - não usamos esse ângulo dramático
- exemplos: https://www.youtube.com/watch?v=4L7SOEY8UW4 seg 16.8 (trecho 96d29293.mp4)
- ids: 96d29293

### 27. [visual] Uso de máscara circular (vinheta) para focar em detalhes da ação
- visto em 1 vídeo(s) · nota máx. 8 · modelos: gemini
- como aplicar: Aplicar uma máscara de opacidade circular com bordas suaves (feather) em momentos de ação específica ou detalhes que precisam de destaque imediato.
- por que é novo: Cria um efeito de 'lupa' ou foco narrativo que isola o elemento principal da cena, diferente dos nossos cortes secos ou zooms simples.
- exemplos: https://www.youtube.com/watch?v=4L7SOEY8UW4 seg 57.0 (trecho 855479cc.mp4)
- ids: 855479cc

### 28. [visual] Clipes do filme original (Lyle, Lyle, Crocodile) com legenda em português sobreposta
- visto em 1 vídeo(s) · nota máx. 8 · modelos: claude-sonnet
- como aplicar: Licenciar ou usar clipes de animes/filmes populares relacionados ao tema do vídeo, adicionar nossa legenda em Montserrat-Black por cima para contar a história. Funciona especialmente para resumos de enredo.
- por que é novo: Não temos no acervo uso de clipes de filmes/séries reais com legenda própria sobreposta. Sempre criamos visuais do zero ou usamos memes estáticos.
- exemplos: https://www.youtube.com/watch?v=tObDsrj73Kw seg 5.7 (trecho 98b43052.mp4)
- ids: 98b43052

### 29. [visual] Placa de protesto 'LET LYLE SING' levantada na multidão do tribunal
- visto em 1 vídeo(s) · nota máx. 8 · modelos: gemini
- como aplicar: Inserir em cenas de julgamento ou apelo popular memes de cartazes customizados com texto em inglês/português estilo manifestação.
- por que é novo: Uso de cartaz físico/protesto em cena dramática/comédia que gera senso de movimento de massa e engajamento que não temos nos nossos recursos estáticos atuais.
- exemplos: https://www.youtube.com/watch?v=tObDsrj73Kw seg 109.1 (trecho 44e89c48.mp4)
- ids: 44e89c48

### 30. [visual] Zoom extremo em olho com detalhe da íris brilhando (quadro 222.7)
- visto em 1 vídeo(s) · nota máx. 8 · modelos: claude-sonnet
- como aplicar: Usar em momentos de revelação ou tensão dramática - criar overlay de zoom em olho com brilho/reflexo destacado para enfatizar emoção ou momento decisivo na história
- por que é novo: Não temos esse tipo de close dramático em olho com brilho destacado no nosso arsenal de overlays ou enquadramentos
- exemplos: https://www.youtube.com/watch?v=MjLIGOeds14 seg 222.7 (trecho 8334026b.mp4)
- ids: 8334026b

### 31. [visual] Filtro de cor verde (overlay de alerta)
- visto em 1 vídeo(s) · nota máx. 8 · modelos: gemini
- como aplicar: Aplicar um sólido verde ou vermelho com 30-50% de opacidade em momentos de 'ideia de jegue' ou erro.
- por que é novo: Usa uma cor sólida semitransparente para mudar o 'mood' da cena instantaneamente quando fala de algo errado/proibido.
- exemplos: https://www.youtube.com/watch?v=V9c9vVkjguk seg 9.4 (trecho 87a3197b.mp4)
- ids: 87a3197b

### 32. [visual] Efeito de 'aura' ou 'linhas de desespero' no fundo
- visto em 1 vídeo(s) · nota máx. 8 · modelos: gemini
- como aplicar: Criar um pack de overlays de 'estados emocionais' (linhas de depressão, fundo de fogo, fundo de flores) para aplicar atrás do personagem em momentos de piada.
- por que é novo: Usamos overlays de impacto, mas não temos esse estilo de 'fundo dramático' que isola o personagem e enfatiza o estado emocional (ex: linhas verticais azuis de tristeza/depressão).
- exemplos: https://www.youtube.com/watch?v=Y-1wrEyMgF8 seg 682.3 (trecho 035d0eef.mp4)
- ids: 035d0eef

### 33. [visual] Texto descritivo de objeto aparece sobre o próprio objeto (ex: 'UMA MARCA' sobre o pingente aos 20s)
- visto em 1 vídeo(s) · nota máx. 8 · modelos: claude-sonnet
- como aplicar: Quando mencionar itens importantes (armas, joias, artefatos), posicionar a legenda amarela apontando diretamente para o objeto na imagem, criando conexão visual imediata
- por que é novo: Normalmente colocamos legendas na parte inferior/superior, não diretamente sobre os objetos relevantes da cena
- exemplos: https://www.youtube.com/watch?v=GOAVvJ3TnIY seg 20 (trecho 255f94d5.mp4)
- ids: 255f94d5

### 34. [visual] Título fixo no topo ('PS6 POR MIL DÓLARES?') + legendas contextuais em faixa amarela abaixo
- visto em 1 vídeo(s) · nota máx. 8 · modelos: claude-sonnet
- como aplicar: Em vídeos com pergunta-gancho ou tema principal, fixar título provocativo no topo enquanto legendas dinâmicas rolam embaixo para dados/contexto
- por que é novo: Estrutura dupla: título-gancho permanente + legenda de apoio rotativa. Nossas legendas geralmente não mantêm título fixo simultâneo
- exemplos: https://www.youtube.com/watch?v=9vaDPVT1MGo seg 1.2 (trecho 8851a88a.mp4)
- ids: 8851a88a

### 35. [visual] Carimbo de texto 'ESTIMATIVA' sobreposto à imagem
- visto em 1 vídeo(s) · nota máx. 8 · modelos: gemini
- como aplicar: Criar um overlay de texto com fundo vermelho (estilo carimbo) para marcar dados que são apenas estimativas ou rumores em nossos vídeos.
- por que é novo: Reforça a credibilidade da informação de forma visual e rápida, diferenciando fato de especulação sem precisar de locução extra.
- exemplos: https://www.youtube.com/watch?v=9vaDPVT1MGo seg 20.5 (trecho ac7cd714.mp4)
- ids: ac7cd714

### 36. [visual] Uso de interface de menu do jogo (UI) como elemento narrativo
- visto em 1 vídeo(s) · nota máx. 8 · modelos: gemini
- como aplicar: Gravar a tela do menu do servidor com zoom focado na recompensa específica que está sendo mencionada na locução, criando uma imersão maior.
- por que é novo: O vídeo não apenas fala, ele mostra o menu do servidor (Battle Pass/Recompensas) como se o espectador estivesse navegando nele.
- exemplos: https://www.youtube.com/watch?v=wv0E2W3ZYqc seg 7.0 (trecho c8d36f8b.mp4)
- ids: c8d36f8b

### 37. [visual] Inserção de fórmulas químicas/elementos técnicos flutuantes
- visto em 1 vídeo(s) · nota máx. 8 · modelos: gemini
- como aplicar: Quando o roteiro citar algum conceito científico ou técnico, inserir uma sobreposição (overlay) estática ou levemente animada de uma fórmula ou esquema técnico ao lado do personagem.
- por que é novo: Adiciona uma camada de 'autoridade' e curiosidade visual que quebra a monotonia da narração.
- exemplos: https://www.youtube.com/watch?v=fSx50o67HB4 seg 3062.9 (trecho 28fc46f8.mp4)
- ids: 28fc46f8

### 38. [visual] Meme em sticker recortado (Willem Dafoe olhando pra cima apavorado) sobreposto diretamente no cenário
- visto em 1 vídeo(s) · nota máx. 8 · modelos: claude-sonnet
- como aplicar: Adicionar o recorte PNG do Willem Dafoe olhando pra cima na pasta memes_png e disparar como sticker sobreposto na tela quando o narrador descrever uma ameaça colossal ou piora repentina da situação.
- por que é novo: Embora tenhamos memes_img, usar o recorte transparente do Dafoe olhando pro céu sobreposto diretamente sobre a cena dramática pontua o choque/medo do personagem sem cortar o fluxo da animação com tela cheia.
- exemplos: https://www.youtube.com/watch?v=q3ixE2vr8aA seg 27.0 (trecho 8f34797b.mp4)
- ids: 8f34797b

### 39. [efeito] Efeito de 'tremor' (shake) nos personagens
- visto em 1 vídeo(s) · nota máx. 8 · modelos: gemini
- como aplicar: Aplicar um leve efeito de vibração (shake) em camadas de personagens quando estiverem em situações de perigo ou susto.
- por que é novo: Dá uma sensação de medo ou tensão que nossos efeitos estáticos não transmitem.
- exemplos: https://www.youtube.com/watch?v=5-vQopGwQ8Y seg 1028.0 (trecho 888f8cff.mp4)
- ids: 888f8cff

### 40. [efeito] Efeito de impacto com linhas de velocidade e brilho intenso
- visto em 1 vídeo(s) · nota máx. 8 · modelos: gemini
- como aplicar: Usar overlays de impacto com linhas radiais e brilho roxo/neon em momentos de ataque ou poder.
- por que é novo: Nossos impactos são mais simples; este efeito de 'energia' é mais dinâmico para cenas de ação.
- exemplos: https://www.youtube.com/watch?v=5-vQopGwQ8Y seg 1850.5 (trecho 1b9593b5.mp4)
- ids: 1b9593b5

(+ 595 grupo(s) mais fracos: vistos em 1 vídeo só; ficam no acervo.jsonl)
