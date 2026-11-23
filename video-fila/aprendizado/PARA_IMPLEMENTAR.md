# Aprendizado com os parceiros — PARA IMPLEMENTAR (refeito a cada rodada; não editar à mão)

Atualizado 23/11/2026 15:41. Gerado por D:\video-fila\aprendizado.py.

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

## A. Aprovados (pela dona ou sozinho: os melhores de cada dia, nota >= 7) (5)

### 1. [jeito_de_falar] Estrutura de guia rápido estilo 'checklist binário' (Entidade X -> Requisito A + Requisito B)
- visto em 1 vídeo(s) · nota máx. 7 · modelos: claude-sonnet
- como aplicar: Adotar o formato 'Qual [item] usar pra cada [situação]?' em roteiros tutoriais rápidos (ex: qual software/configuração/estratégia pra cada objetivo).
- por que é novo: Nossos roteiros costumam focar em narrativa ou curiosidades soltas; essa fórmula de pareamento direto e prático (Qual X para cada Y: 'Pra X, vara A e isca B') gera alto salvamento/compartilhamento.
- exemplos: https://www.youtube.com/watch?v=GTUW7cbj9rI seg 0.0 (trecho 3b2e209d.mp3)
- ids: 3b2e209d

### 2. [visual] Split-screen temático 50/50 com cena de entrevista na sauna em cima e foto/contexto do jogador embaixo
- visto em 1 vídeo(s) · nota máx. 7 · modelos: claude-sonnet
- como aplicar: Quando narrar bastidores de atletas ou criadores, dividir a tela exatamente ao meio: topo com a gravação do podcast/entrevista e base com imagem de arquivo em alta da notícia/lance
- por que é novo: Nossos cortes utilizam layouts verticais cheios ou recortes de mascote/memes sobrepostos, sem essa divisão simétrica 50/50 separando o bate-papo informal da matéria/jogada em questão
- exemplos: https://www.youtube.com/watch?v=TaBrCh6Je4o seg 2.5 (trecho 159b89de.mp4)
- ids: 159b89de

### 3. [visual] Popup PiP centralizado/inferior com bordas bem arredondadas (squircle) e contorno branco grosso
- visto em 1 vídeo(s) · nota máx. 8 · modelos: claude-sonnet
- como aplicar: Criar template de moldura squircle com stroke branco de 6-8px para fazer fade/pop-in no centro-inferior da tela ao introduzir rostos citados pelo narrador sem cobrir todo o vídeo
- por que é novo: Nosso acervo de hyperframes e memes não tem esse card flutuante arredondado com borda sólida branca para ilustrar personagens citados (como o técnico/dirigente)
- exemplos: https://www.youtube.com/watch?v=TaBrCh6Je4o seg 7.4 (trecho 188e2265.mp4)
- ids: 188e2265

### 4. [visual] Miniaturas flutuantes redondas com borda branca mostrando fotos dos jogadores/técnicos citados (ex: Nuno Espírito Santo, escalação em campo)
- visto em 1 vídeo(s) · nota máx. 9 · modelos: gemini
- como aplicar: Adicionar assets de fotos de jogadores/clubes dentro de um container circular com borda branca grossa e sombra projetada (drop shadow) flutuando dinamicamente na tela quando forem mencionados.
- por que é novo: Uso de imagens recortadas em círculos com borda branca e sombra suave flutuando para ilustrar o contexto da história sem ocupar a tela inteira.
- exemplos: https://www.youtube.com/watch?v=TaBrCh6Je4o seg 2.5
- ids: 4dd92ea1

### 5. [visual] Uso de painel de controle industrial (botão de acionamento) em close-up para marcar o início de uma ação mecânica pesada.
- visto em 1 vídeo(s) · nota máx. 8 · modelos: gemini
- como aplicar: Inserir shots de close-up operando botões, alavancas ou telas touch em vídeos de processos industriais ou tecnologia antes de uma reviravolta ou corte dinâmico.
- por que é novo: Mostra a interação física humana direta com o comando da máquina de forma imersiva e tátil, o que gera expectativa para a ação.
- exemplos: https://www.youtube.com/watch?v=sVORL2G36OM seg 21.2 (trecho 16bdb1eb.mp4)
- ids: 16bdb1eb

## B. Candidatos (sem resposta em 24 h): 534 grupo(s), os 40 mais fortes

### 1. [visual] Gráfico de escala de pH com garrafa e indicador de nível (seta preta apontando para o 7).
- visto em 1 vídeo(s) · nota máx. 9 · modelos: gemini
- como aplicar: Criar templates de infográficos verticais para escalas numéricas (temperatura, pH, níveis de energia) usando um estilo visual de ícone minimalista e seta indicadora animada.
- por que é novo: Ilustração esquemática limpa em vetor/ícone para explicar conceitos científicos (pH neutro) diretamente na tela sem stock genérico.
- exemplos: https://www.youtube.com/watch?v=MaL4mZoNZ5A seg 15 (trecho d8ea025e.mp4)
- ids: d8ea025e

### 2. [visual] Inclusão de foto de arquivo antiga / anúncio publicitário retrô (Anúncio Arisco com Rubens Barrichello jovem) para ilustrar a história contada.
- visto em 1 vídeo(s) · nota máx. 9 · modelos: gemini
- como aplicar: Quando narrarmos histórias antigas ou curiosidades de famosos/marcas no início dos vídeos, buscar imagens reais da época (anúncios antigos, fotos de infância) e aplicar com efeito de zoom lento (Ken Burns) e legenda flutuante sobreposta.
- por que é novo: Usa uma foto de arquivo/propaganda real da época para dar contexto visual imediato e humorístico à narrativa de fofoca/história passada.
- exemplos: https://www.youtube.com/watch?v=vwkbpcDU seg 3.0 (trecho 8f832f20.mp4)
- ids: 8f832f20

### 3. [visual] Uso de meme clássico da menina sorrindo na frente do incêndio contextualizado na dica 'taca fogo na casa'
- visto em 1 vídeo(s) · nota máx. 9 · modelos: gemini
- como aplicar: Usar imagens de memes clássicos conhecidos (como a Disaster Girl) sincronizados com ações absurdas citadas na narração dos nossos vídeos.
- por que é novo: Integração direta de imagem de meme reativa com legenda numerada em cima em vídeos de lista rápida, gerando humor absurdo imediato.
- exemplos: https://www.youtube.com/watch?v=p4F3hWc-VUQ seg 4.9 (trecho a877c61b.mp4)
- ids: a877c61b

### 4. [visual] Texto estilo interface de terminal militar em vermelho brilhante sobre fundo escuro tecnológico
- visto em 1 vídeo(s) · nota máx. 9 · modelos: gemini
- como aplicar: Gerar overlay de texto em caixa preta com fonte monoespaçada vermelha forte ('TERMINAL OPERATIONS / SENDING REPORT') para cenas de tecnologia/futuro.
- por que é novo: Ainda não usamos telas de terminal com texto vermelho em blocos grandes simulando sistema embarcado de IA militar.
- exemplos: https://www.youtube.com/watch?v=BcOEA3k2C-E seg 14.0 (trecho 84a0c76b.mp4)
- ids: 84a0c76b

### 5. [visual] Interface de radar tático verde estilizado com linhas de varredura e falhas/glitches simulando tela antiga danificada
- visto em 1 vídeo(s) · nota máx. 9 · modelos: gemini
- como aplicar: Criar template de radar verde com ruído de varredura estilo terminal militar antigo para momentos de alerta ou busca de alvos.
- por que é novo: Não temos em nosso acervo overlays de radar verde militar com efeito CRT de varredura e falhas analógicas.
- exemplos: https://www.youtube.com/watch?v=BcOEA3k2C-E seg 23.0 (trecho fff7c109.mp4)
- ids: fff7c109

### 6. [visual] Texto verde destacado com contraste no topo em caixa alta (ex: 'COLOCARAM A MULHER EM UM TANQUE E ENCHERAM DE AGUA!')
- visto em 1 vídeo(s) · nota máx. 9 · modelos: gemini
- como aplicar: Nos nossos vídeos de narração de histórias, destacar termos de impacto (como 'TANQUE', 'ÁGUA') em verde brilhante enquanto o resto do texto fica branco no topo.
- por que é novo: Uso de destaque de palavras-chave em cor verde limão dentro de uma frase de gancho contínua no topo para prender a retenção imediata.
- exemplos: https://www.youtube.com/watch?v=aWvfFbZOtgg seg 3.5 (trecho efb045f2.mp4)
- ids: efb045f2

### 7. [visual] Uso de estilo visual de IA consistente/cinematográfico com rostos misturados a animais (cabeça de galinha/galo em humanos)
- visto em 1 vídeo(s) · nota máx. 9 · modelos: gemini
- como aplicar: Gerar imagens/cenas com IA combinando corpos humanos realistas com cabeças de animais em situações cotidianas para vídeos de comédia ou teorias absurdas.
- por que é novo: Cria um conceito surreal e bizarro de invasão ou substituição por animais de forma integrada ao live-action realista que ainda não exploramos com essa estética específica de personagens híbridos.
- exemplos: https://www.youtube.com/watch?v=udgzx8T seg 36.1 (trecho a9b9fdb7.mp4)
- ids: a9b9fdb7

### 8. [visual] Filtros de expressão facial animados com overlay de choro/lágrimas e fumaça saindo da orelha (estilo cartoon sobre vídeo real)
- visto em 1 vídeo(s) · nota máx. 9 · modelos: gemini
- como aplicar: Sobrepor stickers PNG transparentes de lágrimas ou vapor nas têmporas sincronizados com as trocas de expressão facial dos personagens em vídeos de reação.
- por que é novo: Uso de stickers estáticos/animados expressivos integrados diretamente sobre o rosto em momentos de drama cômico para exagerar a reação.
- exemplos: https://www.youtube.com/watch?v=p9EE3Sam-Vo seg 4.0 (trecho 87526937.mp4)
- ids: 87526937

### 9. [visual] Uso de vara de bambu rudimentar contrastando com a captura de peixes gigantes em corredeiras intensas
- visto em 1 vídeo(s) · nota máx. 9 · modelos: gemini
- como aplicar: Criar vídeos focados em desafios extremos usando ferramentas minimalistas ou improvisadas em nichos de aventura/curiosidades.
- por que é novo: Mostra uma situação extrema de pesca rústica vs grande porte que gera alto engajamento pelo fator surpresa e contraste visual.
- exemplos: https://www.youtube.com/watch?v=RjwS1Qbkx7I seg 33.8 (trecho 382e8307.mp4)
- ids: 382e8307

### 10. [visual] Inserção de imagem circular recortada de um animal terrestre (javali) contrastando com imagens aéreas de peixes para fazer analogia inusitada.
- visto em 1 vídeo(s) · nota máx. 9 · modelos: gemini
- como aplicar: Adicionar um círculo com borda suave ou preta contendo o animal de referência com zoom leve ao fazer comparações de tamanho ou comportamento.
- por que é novo: Ainda não utilizamos esse tipo de recorte circular flutuante com zoom in sobre um animal de comparação logo no início do vídeo para fazer analogias visuais diretas.
- exemplos: https://www.youtube.com/watch?v=sDij68PwvZ4 seg 2.4 (trecho 42734310.mp4)
- ids: 42734310

### 11. [visual] Sequência rápida de demonstração física do produto logo no início (apertando a isca maleável com os dedos para mostrar realismo).
- visto em 1 vídeo(s) · nota máx. 9 · modelos: gemini
- como aplicar: Começar vídeos de review ou demonstração apertando, flexionando ou testando o material do produto nos primeiros 2 segundos.
- por que é novo: Gera curiosidade tátil imediata antes de mostrar a isca na água ou com os anzóis.
- exemplos: https://www.youtube.com/watch?v=N8JyUT seg 1.3 (trecho 988a126c.mp4)
- ids: 988a126c

### 12. [jeito_de_falar] Narrativa empática abordando frustração do cotidiano ('trabalho em dois empregos pra não jogar dinheiro fora') aplicada a um hobby
- visto em 1 vídeo(s) · nota máx. 9 · modelos: gemini
- como aplicar: Inserir ganchos com piadas relacionáveis sobre esforço x desperdício financeiro no início dos tutoriais.
- por que é novo: Conecta um problema cotidiano/relatable (trabalhar em dois empregos) com uma situação específica de lazer.
- exemplos: https://www.youtube.com/watch?v=ON seg 14.1 (trecho a575d012.mp3)
- ids: a575d012

### 13. [visual] Fundo verde quadriculado tipo papel milimetrado com título grande em destaque no topo
- visto em 1 vídeo(s) · nota máx. 9 · modelos: gemini
- como aplicar: Adotar plano de fundo com textura de grade verde/papel milimetrado em vídeos de curiosidades financeiras ou biográficas.
- por que é novo: Padronização estética estilo lousa/quadro escolar moderno com grade e fontes grossas de alto impacto que não utilizamos na mesma composição.
- exemplos: https://www.youtube.com/watch?v=MKTdnCetDRo seg 0.0 (trecho 41be904a.mp4)
- ids: 41be904a

### 14. [visual] Cheque bancário gigante com valor impresso de 30 bilhões de dólares sobreposto ao fundo
- visto em 1 vídeo(s) · nota máx. 9 · modelos: gemini
- como aplicar: Gerar gráficos de cheques gigantes ou notas fiscais com valores absurdos para enfatizar piadas sobre quantias de dinheiro.
- por que é novo: Ilustração literal e exagerada de um documento financeiro (cheque) para tangibilizar valores astronômicos citados no roteiro.
- exemplos: https://www.youtube.com/watch?v=MKTdnCetDRo seg 56.0 (trecho e28d0e8b.mp4)
- ids: e28d0e8b

### 15. [visual] Demonstração prática em macro close-up na boca do peixe mostrando o encaixe da ferramenta
- visto em 1 vídeo(s) · nota máx. 9 · modelos: gemini
- como aplicar: Iniciar vídeos de utilidades/gadgets mostrando imediatamente o problema crítico em close bem fechado antes da introdução
- por que é novo: Foco extremo na dor do nicho (anzol preso) logo no primeiro segundo em formato POV direto
- exemplos: https://www.youtube.com/watch?v=hMwyBouB seg 1.0 (trecho 6d4172d8.mp4)
- ids: 6d4172d8

### 16. [visual] Uso de objeto inusitado (chave de boca/ferramenta) como isca de pesca artesanal
- visto em 1 vídeo(s) · nota máx. 9 · modelos: gemini
- como aplicar: Em vídeos de testes ou hacks, usar objetos absurdos do cotidiano (ex: usar um garfo, uma escova de dentes ou uma chave inglesa) para resolver problemas simples no gancho inicial.
- por que é novo: Foca em um item completamente bizarro adaptado para uma função comum, gerando curiosidade imediata e prendendo o espectador no início (hook).
- exemplos: https://www.youtube.com/watch?v=8pZEDGHCZOo seg 0.0 (trecho 3b1891bb.mp4)
- ids: 3b1891bb

### 17. [visual] Alternância dinâmica entre filmagem real de pesca de barco com captura e imagens subaquáticas conceituais/ilustrativas do habitat do peixe.
- visto em 1 vídeo(s) · nota máx. 9 · modelos: gemini
- como aplicar: Inserir vídeos B-roll ou imagens subaquáticas ilustrativas que correspondam ao áudio/narração para enriquecer visualmente e prender a atenção do espectador.
- por que é novo: Mistura cenas de ação real (pesca) com imagens imersivas de arquivo do fundo do rio, criando um storytelling visual mais rico do que apenas manter a câmera no barco.
- exemplos: https://www.youtube.com/watch?v=CM1bpSz-0zc seg 3.6 (trecho a67b7c81.mp4)
- ids: a67b7c81

### 18. [visual] Notificação flutuante estilo SMS/Banco na parte superior com texto de transferência em moeda estrangeira ou valor exagerado
- visto em 1 vídeo(s) · nota máx. 9 · modelos: gemini
- como aplicar: Criar um componente visual customizado estilo banner de notificação de celular (estilo iOS/Android) no topo do vídeo simulando depósitos absurdos para vídeos de reviravolta financeira.
- por que é novo: Mostra uma interface realista de notificação bancária/sistema simulando dinheiro entrando na conta, o que não temos em nossos hyperframes ou overlays atuais.
- exemplos: https://www.youtube.com/watch?v=cdBMCwsz-Wo seg 273.1 (trecho 384a860f.mp4)
- ids: 384a860f

### 19. [visual] Cronômetro regressivo fixo no topo com ícone de relógio
- visto em 1 vídeo(s) · nota máx. 9 · modelos: gemini
- como aplicar: Adicionar um widget de relógio com contagem regressiva decrescente no topo central dos vídeos de desafios ou rotinas rápidas.
- por que é novo: Cria um senso de urgência contínuo e contagem regressiva para prender a retenção do espectador ao longo de todo o vídeo, simulando um desafio de tempo.
- exemplos: https://www.youtube.com/watch?v=JnF6H seg 1.1 (trecho d53a4909.mp4)
- ids: d53a4909

### 20. [visual] Tomada aberta horizontal/vertical do peixe capturado exibido próximo à câmera com o pescador ao fundo
- visto em 1 vídeo(s) · nota máx. 9 · modelos: gemini
- como aplicar: Empregar o formato de 'revelação do resultado' erguendo o item/prêmio principal na altura da lente no desfecho.
- por que é novo: Grande contraste de escala entre a isca minúscula inicial e o peixe grande final em close de revelação.
- exemplos: https://www.youtube.com/watch?v=gFztA2XkdVg seg 31.1 (trecho 19c478f8.mp4)
- ids: 19c478f8

### 21. [visual] Caixa de texto vermelha arredondada em destaque chamativa cobrindo a parte central com título em caixa alta branco
- visto em 1 vídeo(s) · nota máx. 9 · modelos: gemini
- como aplicar: Criar um componente de banner inferior com fundo vermelho sólido e bordas arredondadas para destacar a manchete do vídeo durante falas densas de finanças.
- por que é novo: Usa um bloco vermelho grande e fixo na tela com contraste forte para prender a atenção no assunto principal sem sumir rapidamente.
- exemplos: https://www.youtube.com/watch?v=RH8r6JEDg04 seg 7.3 (trecho 6a4321f9.mp4)
- ids: 6a4321f9

### 22. [jeito_de_falar] Loop narrativo conectando a frase de desfecho diretamente com o início do vídeo ('...porque tudo isso começa quando muita gente jura que...')
- visto em 1 vídeo(s) · nota máx. 9 · modelos: claude-sonnet
- como aplicar: Estruturar o roteiro finalizando com uma conjunção ou frase incompleta ('porque tudo isso começa quando...') que encaixa com a primeira frase do vídeo, aumentando a taxa de retenção/replay nos Shorts.
- por que é novo: Nossos roteiros geralmente terminam com chamada para ação (CTA) ou encerramento tradicional, sem amarrar a última oração sintaticamente com a primeira palavra do vídeo para loop infinito.
- exemplos: https://www.youtube.com/watch?v=dtlUNhLB1AU seg 70.0 (trecho fc5b8e6e.mp3)
- ids: fc5b8e6e

### 23. [visual] Sobreposição de gráfico financeiro/dados com números negativos e linhas vermelhas sobre paisagem urbana cinzenta e brumosa.
- visto em 1 vídeo(s) · nota máx. 9 · modelos: gemini
- como aplicar: Adicionar uma camada de gráfico de ações em queda vermelha com números flutuantes e opacidade ajustada sobre clipes B-roll de grandes centros urbanos em pautas de economia.
- por que é novo: Não utilizamos gráficos de candlestick/financeiros transparentes sobrepostos a imagens de cidades reais em tom sombrio para contextualizar crises econômicas.
- exemplos: https://www.youtube.com/watch?v=tm seg 50.3 (trecho 4bce5ec2.mp4)
- ids: 4bce5ec2

### 24. [visual] Card de pergunta com borda vermelha e sombra no estilo 'pergunta de seguidor'
- visto em 1 vídeo(s) · nota máx. 9 · modelos: gemini
- como aplicar: Criar um template de card flutuante com borda colorida simulando um comentário ou pergunta enviada pelo usuário.
- por que é novo: Apresenta a dúvida do espectador em formato de post de rede social estilizado no início do vídeo para engajamento.
- exemplos: https://www.youtube.com/watch?v=8fHmCH50wPI seg 0.0 (trecho 89ab42b0.mp4)
- ids: 89ab42b0

### 25. [visual] Corte em perfil geológico mostrando as camadas subterrâneas da terra e raízes de plantas
- visto em 1 vídeo(s) · nota máx. 9 · modelos: gemini
- como aplicar: Usar animações em 3D de seções transversais do solo para explicar conceitos de agricultura ou geologia
- por que é novo: Demonstração visual do subsolo em 3D explicativo cortado ao meio que não utilizamos em nossos vídeos
- exemplos: https://www.youtube.com/watch?v=e2H-sIWaqbU seg 22.6 (trecho 38398e53.mp4)
- ids: 38398e53

### 26. [outro] Transição cômica de POV estressante/extremo em alto mar direto para o marinheiro fazendo flexão em ambiente interno calmo
- visto em 1 vídeo(s) · nota máx. 9 · modelos: gemini
- como aplicar: Criar cortes secos imprevistos conectando uma situação caótica ou perigosa a uma ação mundana e descontraída.
- por que é novo: Contraste extremo entre perigo mortal em alto mar e calmaria/exercício casual dentro da cabine do navio.
- exemplos: https://www.youtube.com/watch?v=Z65nztXTT3Q seg 23.5 (trecho fe5fd7d3.mp4)
- ids: fe5fd7d3

### 27. [jeito_de_falar] Estrutura narrativa em cadeia de causas/escalada com encerramento em loop infinito
- visto em 1 vídeo(s) · nota máx. 9 · modelos: claude-sonnet
- como aplicar: Adotar no gerador de roteiros uma fórmula de 'efeito dominó' em histórias de sobrevivência/crafting onde a última frase fica sintaticamente incompleta e encaixa no primeiro segundo do vídeo para loop perfeito.
- por que é novo: A narração encadeia cada item como degrau para o próximo ('item A vira B que pega C que atrai D') e termina a frase final conectando perfeitamente de volta ao início ('e tudo isso começou quando ele pegou uma simples mola de lanterna e... [volta para: Ele tira a mola da lanterna]'), criando retenção máxima e repetição infinita que não temos automatizada nos roteiros.
- exemplos: https://www.youtube.com/watch?v=G-RYguL5Ig4 seg 1.7 (trecho 1bcaa805.mp3)
- ids: 1bcaa805

### 28. [visual] Zoom com lupa/esfera macro mostrando os detalhes internos da mandíbula da formiga e esporos do fungo
- visto em 1 vídeo(s) · nota máx. 9 · modelos: gemini
- como aplicar: Criar sobreposições circulares em 3D simulando lente de aumento/microscópio com elementos internos destacados para explicar conceitos anatômicos ou científicos nos nossos vídeos
- por que é novo: Usa gráficos 3D explicativos em estilo lupa microscópica flutuante sobre filmagem real/macro para explicar biologia de forma lúdica
- exemplos: https://www.youtube.com/watch?v=wyR18FmRm84 seg 7.6 (trecho fd2ed735.mp4)
- ids: fd2ed735

### 29. [efeito] Zoom in rápido com impacto de velocidade (speed lines/anime action lines) em cenas de comédia/surpresa
- visto em 1 vídeo(s) · nota máx. 9 · modelos: gemini
- como aplicar: Aplicar camada de efeito de linhas de velocidade radiais (anime speed lines) combinada com um zoom repentino de 110% na keyframe inicial.
- por que é novo: Foco em linhas de velocidade estilo mangá/anime enfatizando o salto da personagem com alta saturação
- exemplos: https://www.youtube.com/watch?v=fyQTRywBafk seg 26.2 (trecho 184b416b.mp4)
- ids: 184b416b

### 30. [outro] Revelação progressiva de um objeto escondido/anômalo dentro da natureza (pedra com entalhes dentro de uma árvore oca).
- visto em 1 vídeo(s) · nota máx. 9 · modelos: gemini
- como aplicar: Criar conteúdos focados em 'achados impossíveis' ou mistérios naturais com zoom progressivo para gerar curiosidade.
- por que é novo: Ganha alto engajamento pelo formato de 'enigma arqueológico ou mistério na floresta' que força o usuário a assistir até o fim.
- exemplos: https://www.youtube.com/watch?v=S1B9qKMdNy0 seg 1.6 (trecho c14a696b.mp4)
- ids: c14a696b

### 31. [visual] Corte dinâmico combinando filmagem real subaquática com animação em 3D dos peixes no mesmo habitat
- visto em 1 vídeo(s) · nota máx. 9 · modelos: gemini
- como aplicar: Utilizar cenas de stock subaquáticas intercaladas com closes de iscas e peixes para ilustrar comportamentos de pesca.
- por que é novo: Mistura imagens reais de pescaria com renders subaquáticos detalhados dos personagens apresentados.
- exemplos: https://www.youtube.com/watch?v=SDvVwZbXoPU seg 3.1 (trecho e1be19b4.mp4)
- ids: e1be19b4

### 32. [jeito_de_falar] Narração esportiva empolgada estilo Galvão Bueno aplicada a tema financeiro sério
- visto em 1 vídeo(s) · nota máx. 8.5 · modelos: claude-sonnet
- como aplicar: Roteirizar tópicos densos de finanças/negócios com locução e vocabulário de narração esportiva de clássico de futebol nos primeiros 30-40 segundos.
- por que é novo: Usa metáforas de futebol ('Haja coração', 'avançando no campo', 'tabela rápida', 'pressão total na área', 'golaço tá armando') para explicar uma operação técnica de M&A entre FIIs, criando contraste cômico e retenção alta sem parecer aula chata.
- exemplos: https://www.youtube.com/watch?v=GKjI-xCZJx8 seg 2.6 (trecho dbc46ca0.mp3)
- ids: dbc46ca0

### 33. [piada] Dica final anti-clímax que quebra a lógica do filme com conselho prático da vida real ('Arrume um emprego')
- visto em 1 vídeo(s) · nota máx. 8 · modelos: claude-sonnet
- como aplicar: Em vídeos de 'como sobreviver / como derrotar vilão de filme', fechar com dica realista/moral cômica acompanhada de meme ou homem de terno para gerar humor por quebra de expectativa.
- por que é novo: Estrutura de roteiro humorístico onde a última dica de sobrevivência em filme de assalto/invasão ignora o perigo imediato e ataca a causa raiz dos personagens serem ladrões.
- exemplos: https://www.youtube.com/watch?v=uEibbO00qvg seg 28.0 (trecho 19f17dea.mp3)
- ids: 19f17dea

### 34. [jeito_de_falar] Hook contra-intuitivo de quebra de objeção emocional ('E antes de você sentir raiva ou inveja, vou te mostrar o que isso significa para você')
- visto em 1 vídeo(s) · nota máx. 8 · modelos: claude-sonnet
- como aplicar: Em roteiros polêmicos sobre bilionários, riqueza ou privilégio, estruturar os primeiros 3 segundos desarmando o julgamento moral do espectador para focar na utilidade prática para a vida dele.
- por que é novo: Nossos scripts de intro focam em curiosidade direta ou choque; antecipar a emoção negativa do espectador (inveja/revolta) e redirecioná-la imediatamente para benefício próprio é uma técnica de retenção que ainda não aplicamos na copywriting.
- exemplos: https://www.youtube.com/watch?v=JGGdTT7rxdE seg 0.0 (trecho 746b7a80.mp3)
- ids: 746b7a80

### 35. [visual] Uso de imagens de arquivo reais de eventos e palestras reais (como a Nasdaq/SpaceX) como b-roll de fundo
- visto em 1 vídeo(s) · nota máx. 8 · modelos: gemini
- como aplicar: Integrar trechos curtos de vídeos públicos reais de anúncios ou eventos corporativos ao ilustrar notícias de grandes empresas.
- por que é novo: Dá autoridade e aspecto jornalístico/documental ao vídeo em vez de usar apenas memes ou imagens genéricas de banco.
- exemplos: https://www.youtube.com/watch?v=JGGdTT7rxdE seg 9.0 (trecho fa72b2fd.mp4)
- ids: fa72b2fd

### 36. [visual] Texto com contorno amarelo e fonte arredondada conversacional ('Jennie's skirt blew up...')
- visto em 1 vídeo(s) · nota máx. 8 · modelos: gemini
- como aplicar: Aplicar legenda central com fonte grossa (ex: LuckiestGuy ou Montserrat Black), contorno preto forte e cor amarela.
- por que é novo: Legenda centralizada chamativa típica de edits virais do TikTok com destaque em cor contrastante.
- exemplos: https://www.youtube.com/watch?v=kpOcL4dgh80 seg 2.6 (trecho e8cd84ff.mp4)
- ids: e8cd84ff

### 37. [visual] Texto cursor/destaque humorístico com asteriscos ('*Her shy smile*', '*notice* 👀')
- visto em 1 vídeo(s) · nota máx. 8 · modelos: gemini
- como aplicar: Inserir caixas de texto curtas no topo central com asteriscos para narrar o pensamento do editor ou o foco da cena.
- por que é novo: Adiciona comentário irônico em formato de pensamento/narração interna no topo da tela.
- exemplos: https://www.youtube.com/watch?v=kpOcL4dgh80 seg 7.7 (trecho 541173a5.mp4)
- ids: 541173a5

### 38. [visual] Uso de setas coloridas dinâmicas apontando para a boca/comida e círculos vermelhos enfatizando os exageros
- visto em 1 vídeo(s) · nota máx. 8 · modelos: gemini
- como aplicar: Inserir setas e círculos vermelhos/verdes pontuais para guiar o olhar do espectador para detalhes cômicos em vídeos de reação.
- por que é novo: Destaca com setas e círculos minimalistas de edição rápida a forma engraçada como os ídolos comem.
- exemplos: https://www.youtube.com/watch?v=kHe8oWuoU8o seg 1.6 (trecho 0c6db3cc.mp4)
- ids: 0c6db3cc

### 39. [visual] Infográfico minimalista estilo 2D vetorizado com escala de pH colorida (1 a 14) e ponteiro indicador ao lado do objeto
- visto em 1 vídeo(s) · nota máx. 8 · modelos: claude-sonnet
- como aplicar: Criar templates de infográficos dinâmicos (ex: termômetro, escala de nível, régua comparativa) em fundo com textura sutil e ponteiro animado para momentos explicativos/didáticos dos shorts.
- por que é novo: Temos recortes de memes e hyperframes com números grandes ou badges, mas não temos overlays infográficos verticais didáticos em estética vetor limpo/sketch para explicar métricas ou comparações técnicas de forma direta.
- exemplos: https://www.youtube.com/watch?v=MaL4mZoNZ5A seg 27.0 (trecho c10fb495.mp4)
- ids: c10fb495

### 40. [piada] Conselhos absurdos/literais de sobrevivência contra clichês de terror ('dormir na rua porque não tem porta pra bater', 'tacar fogo na casa')
- visto em 1 vídeo(s) · nota máx. 8 · modelos: claude-sonnet
- como aplicar: Roteirizar shorts com guias de sobrevivência zombando de clichês de animes ou filmes famosos que cobrimos
- por que é novo: Formato de lista satírica de 'como derrotar [filme/monstro] em 30 segundos' desconstruindo clichês clássicos do gênero com soluções burras/extremas
- exemplos: https://www.youtube.com/watch?v=p4F3hWc-VUQ seg 4.9 (trecho 25b636e0.mp3)
- ids: 25b636e0

(+ 494 grupo(s) mais fracos: vistos em 1 vídeo só; ficam no acervo.jsonl)
