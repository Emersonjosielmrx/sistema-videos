# Aprendizado com os parceiros — PARA IMPLEMENTAR (refeito a cada rodada; não editar à mão)

Atualizado 21/11/2026 03:43. Gerado por D:\video-fila\aprendizado.py.

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

### 1. [visual] Enquadramento em primeira pessoa/visão claustrofóbica em túnel curvo com perspectiva de afogamento e subida de nível de água
- visto em 1 vídeo(s) · nota máx. 8 · modelos: claude-sonnet
- como aplicar: Gerar no pipeline de 3D/animação sequências de 'cenário de risco em primeira/terceira pessoa próxima' (espaço confinado, água subindo) para shorts de sobrevivência e curiosidades médicas/extremas.
- por que é novo: Nosso acervo de hyperframes/fillers foca em batalhas cósmicas, cidades ou cenários abertos; não temos simulação 3D imersiva de perigo físico em espaço confinado com física de fluidos dinâmica.
- exemplos: https://www.youtube.com/watch?v=eulG1i95JPM seg 13.9 (trecho 66877685.mp4)
- ids: 66877685

### 2. [jeito_de_falar] Estrutura narrativa em loop perfeito ligando o desfecho exato à frase de gancho inicial ('quando tá preso num toboágua que tá enchendo...')
- visto em 1 vídeo(s) · nota máx. 9 · modelos: claude-sonnet
- como aplicar: Nos roteiros de curiosidades/shorts, fazer a última frase terminar com reticências conectando perfeitamente ao primeiro segundo, aumentando a taxa de retenção por repetição automática.
- por que é novo: Nossas intros_voz e bordões têm começos e finais estanques (.fim / .ini), sem script planejado para encaixar sintaticamente a última oração direto no gancho do segundo zero.
- exemplos: https://www.youtube.com/watch?v=eulG1i95JPM seg 26.2 (trecho 27c0b036.mp3)
- ids: 27c0b036

### 3. [visual] Título central em tipografia rústica texturizada em caixa branca com contorno irregular ('BOIS DO BRASIL')
- visto em 1 vídeo(s) · nota máx. 7 · modelos: claude-sonnet
- como aplicar: Criar templates de títulos estilizados no Photoshop/After Effects para a abertura dos primeiros 3 segundos de vídeos de curiosidades/rankings temáticos.
- por que é novo: Nosso banco de fontes só possui Bangers, LuckiestGuy, Montserrat e Impact limpas; não temos lettering temático rústico/carimbado com fundo recortado para introduzir o tema do Shorts.
- exemplos: https://www.youtube.com/watch?v=0ONNeIWYGr4 seg 0.0 (trecho 9963303a.mp4)
- ids: 9963303a

### 4. [visual] Alternância dinâmica entre tomadas de gado vivo em pasto e cortes da carne preparada (steak/churrasco)
- visto em 1 vídeo(s) · nota máx. 9 · modelos: gemini
- como aplicar: Nos vídeos de ranking, intercalar imagens de close-up de pratos prontos/carnes suculentas toda vez que mencionar o item avaliado.
- por que é novo: Associa diretamente o animal vivo à peça de carne correspondente no ponto de cozimento, gerando alto apelo visual e retenção.
- exemplos: https://www.youtube.com/watch?v=0ONNeIWYGr4 seg 3.1 (trecho 94bb7f3b.mp4)
- ids: 94bb7f3b

### 5. [visual] Transição direta mostrando o produto pronto e consumido logo no primeiro segundo
- visto em 1 vídeo(s) · nota máx. 9 · modelos: gemini
- como aplicar: Colocar o prato pronto ou o resultado final bem no frame 0 para prender a atenção nos primeiros segundos dos nossos vídeos de receita/pesca.
- por que é novo: Cria um gancho visual forte de 'resultado final' (food porn/pesca finalizada) antes de contar a história linear.
- exemplos: https://www.youtube.com/watch?v=TltsQH256W4 seg 1.4 (trecho 5fde70ac.mp4)
- ids: 5fde70ac

## B. Candidatos (sem resposta em 24 h): 483 grupo(s), os 40 mais fortes

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

### 21. [piada] Dica final anti-clímax que quebra a lógica do filme com conselho prático da vida real ('Arrume um emprego')
- visto em 1 vídeo(s) · nota máx. 8 · modelos: claude-sonnet
- como aplicar: Em vídeos de 'como sobreviver / como derrotar vilão de filme', fechar com dica realista/moral cômica acompanhada de meme ou homem de terno para gerar humor por quebra de expectativa.
- por que é novo: Estrutura de roteiro humorístico onde a última dica de sobrevivência em filme de assalto/invasão ignora o perigo imediato e ataca a causa raiz dos personagens serem ladrões.
- exemplos: https://www.youtube.com/watch?v=uEibbO00qvg seg 28.0 (trecho 19f17dea.mp3)
- ids: 19f17dea

### 22. [jeito_de_falar] Hook contra-intuitivo de quebra de objeção emocional ('E antes de você sentir raiva ou inveja, vou te mostrar o que isso significa para você')
- visto em 1 vídeo(s) · nota máx. 8 · modelos: claude-sonnet
- como aplicar: Em roteiros polêmicos sobre bilionários, riqueza ou privilégio, estruturar os primeiros 3 segundos desarmando o julgamento moral do espectador para focar na utilidade prática para a vida dele.
- por que é novo: Nossos scripts de intro focam em curiosidade direta ou choque; antecipar a emoção negativa do espectador (inveja/revolta) e redirecioná-la imediatamente para benefício próprio é uma técnica de retenção que ainda não aplicamos na copywriting.
- exemplos: https://www.youtube.com/watch?v=JGGdTT7rxdE seg 0.0 (trecho 746b7a80.mp3)
- ids: 746b7a80

### 23. [visual] Uso de imagens de arquivo reais de eventos e palestras reais (como a Nasdaq/SpaceX) como b-roll de fundo
- visto em 1 vídeo(s) · nota máx. 8 · modelos: gemini
- como aplicar: Integrar trechos curtos de vídeos públicos reais de anúncios ou eventos corporativos ao ilustrar notícias de grandes empresas.
- por que é novo: Dá autoridade e aspecto jornalístico/documental ao vídeo em vez de usar apenas memes ou imagens genéricas de banco.
- exemplos: https://www.youtube.com/watch?v=JGGdTT7rxdE seg 9.0 (trecho fa72b2fd.mp4)
- ids: fa72b2fd

### 24. [visual] Texto com contorno amarelo e fonte arredondada conversacional ('Jennie's skirt blew up...')
- visto em 1 vídeo(s) · nota máx. 8 · modelos: gemini
- como aplicar: Aplicar legenda central com fonte grossa (ex: LuckiestGuy ou Montserrat Black), contorno preto forte e cor amarela.
- por que é novo: Legenda centralizada chamativa típica de edits virais do TikTok com destaque em cor contrastante.
- exemplos: https://www.youtube.com/watch?v=kpOcL4dgh80 seg 2.6 (trecho e8cd84ff.mp4)
- ids: e8cd84ff

### 25. [visual] Texto cursor/destaque humorístico com asteriscos ('*Her shy smile*', '*notice* 👀')
- visto em 1 vídeo(s) · nota máx. 8 · modelos: gemini
- como aplicar: Inserir caixas de texto curtas no topo central com asteriscos para narrar o pensamento do editor ou o foco da cena.
- por que é novo: Adiciona comentário irônico em formato de pensamento/narração interna no topo da tela.
- exemplos: https://www.youtube.com/watch?v=kpOcL4dgh80 seg 7.7 (trecho 541173a5.mp4)
- ids: 541173a5

### 26. [visual] Uso de setas coloridas dinâmicas apontando para a boca/comida e círculos vermelhos enfatizando os exageros
- visto em 1 vídeo(s) · nota máx. 8 · modelos: gemini
- como aplicar: Inserir setas e círculos vermelhos/verdes pontuais para guiar o olhar do espectador para detalhes cômicos em vídeos de reação.
- por que é novo: Destaca com setas e círculos minimalistas de edição rápida a forma engraçada como os ídolos comem.
- exemplos: https://www.youtube.com/watch?v=kHe8oWuoU8o seg 1.6 (trecho 0c6db3cc.mp4)
- ids: 0c6db3cc

### 27. [visual] Infográfico minimalista estilo 2D vetorizado com escala de pH colorida (1 a 14) e ponteiro indicador ao lado do objeto
- visto em 1 vídeo(s) · nota máx. 8 · modelos: claude-sonnet
- como aplicar: Criar templates de infográficos dinâmicos (ex: termômetro, escala de nível, régua comparativa) em fundo com textura sutil e ponteiro animado para momentos explicativos/didáticos dos shorts.
- por que é novo: Temos recortes de memes e hyperframes com números grandes ou badges, mas não temos overlays infográficos verticais didáticos em estética vetor limpo/sketch para explicar métricas ou comparações técnicas de forma direta.
- exemplos: https://www.youtube.com/watch?v=MaL4mZoNZ5A seg 27.0 (trecho c10fb495.mp4)
- ids: c10fb495

### 28. [piada] Conselhos absurdos/literais de sobrevivência contra clichês de terror ('dormir na rua porque não tem porta pra bater', 'tacar fogo na casa')
- visto em 1 vídeo(s) · nota máx. 8 · modelos: claude-sonnet
- como aplicar: Roteirizar shorts com guias de sobrevivência zombando de clichês de animes ou filmes famosos que cobrimos
- por que é novo: Formato de lista satírica de 'como derrotar [filme/monstro] em 30 segundos' desconstruindo clichês clássicos do gênero com soluções burras/extremas
- exemplos: https://www.youtube.com/watch?v=p4F3hWc-VUQ seg 4.9 (trecho 25b636e0.mp3)
- ids: 25b636e0

### 29. [visual] HUD/Tela diegética militar sci-fi com tipografia pixelada, radar e log de sistema simulando visor quebrado
- visto em 1 vídeo(s) · nota máx. 8 · modelos: claude-sonnet
- como aplicar: Criar templates de overlay no Remotion/FFmpeg com máscara de CRT/scanlines, radar circular verde e texto em fonte monospace vermelha/verde para cortes de contexto tecnológico, IA ou batalha futurista.
- por que é novo: Nossos assets têm apenas dividers elétricos/fogo e hyperframes comuns; não temos overlays diegéticos de HUD sci-fi militar com texto de telemetria/radar dinâmico integrado ao storytelling.
- exemplos: https://www.youtube.com/watch?v=BcOEA3k2C-E seg 14.0 (trecho 07d6b4df.mp4)
- ids: 07d6b4df

### 30. [jeito_de_falar] Gancho trágico-narrativo com paradoxo humano/máquina ('Este homem está morto há centenas de anos, mas este bombardeiro continua voando')
- visto em 1 vídeo(s) · nota máx. 8 · modelos: claude-sonnet
- como aplicar: Adotar no primeiro segundo do roteiro frases de antítese radical ('[Sujeito] já morreu há séculos, mas [máquina/entidade] ainda executa a mesma ordem') para retenção imediata em resumos de filmes/jogos.
- por que é novo: Nossas intros em intros_voz focam em bordões e reações; falta essa fórmula de gancho com quebra conceitual dramática em histórias de ficção/resumos de animação.
- exemplos: https://www.youtube.com/watch?v=BcOEA3k2C-E seg 0.0 (trecho b9dbc82f.mp3)
- ids: b9dbc82f

### 31. [jeito_de_falar] Fechamento com síntese expressa antecedida de 'Resumo simples.' antes do CTA
- visto em 1 vídeo(s) · nota máx. 8 · modelos: claude-sonnet
- como aplicar: Adicionar nos templates de roteiro a fórmula de conclusão 'Resumo simples: [ponto 1, 2 e 3]' para recapitular vídeos informativos e aumentar o valor percebido antes da pergunta final
- por que é novo: Não temos nos roteiros o padrão de 'Resumo simples: [3 adjetivos/características chaves]', que ancora o aprendizado do espectador nos últimos 10 segundos
- exemplos: https://www.youtube.com/watch?v=8xu43xaiGX8 seg 50.0 (trecho b4252c14.mp3)
- ids: b4252c14

### 32. [visual] Uso de imagens B-roll em grande quantidade mostrando densidade extrema de peixes (tanques lotados de bagres em alta escala)
- visto em 1 vídeo(s) · nota máx. 8 · modelos: gemini
- como aplicar: Incluir clipes de arquivo de piscicultura em massa e tanques lotados ao falar sobre superpopulação ou crescimento rápido em vídeos sobre animais/pragas.
- por que é novo: Foca em imagens de escala massiva real (criação intensiva / tanques lotados) que ilustram superlotação de forma visualmente impactante, algo que não usamos com essa frequência.
- exemplos: https://www.youtube.com/watch?v=8xu43xaiGX8 seg 21.3 (trecho e731049b.mp4)
- ids: e731049b

### 33. [visual] Legendas centralizadas de uma palavra ou frase curta por vez com fundo contrastante (estilo Reels dinâmico)
- visto em 1 vídeo(s) · nota máx. 8 · modelos: gemini
- como aplicar: Aplicar o estilo de legendas centralizadas rápidas destacando palavras dinamicamente no meio da tela para aumentar o engajamento visual.
- por que é novo: Ritmo ultrarrápido de legendas centralizadas focando em verbos e substantivos principais (ex: 'DENTRO', 'CORRENTES', 'OBSERVAVAM')
- exemplos: https://www.youtube.com/watch?v=aWvfFbZOtgg seg 3.5 (trecho 6bd65996.mp4)
- ids: 6bd65996

### 34. [jeito_de_falar] Estrutura de desafio eliminatório como gancho inicial: 'Se você não consegue passar nesse teste, nunca pode...'
- visto em 1 vídeo(s) · nota máx. 8 · modelos: claude-sonnet
- como aplicar: Adaptar a primeira linha do roteiro nos vídeos de teste/capacidade humana usando a condicional 'Se você não consegue [ação], você nunca [consequência desafiadora]'.
- por que é novo: Nossos intros de voz focam em curiosidades ou reações de choque genéricas; falta essa fórmula de desafio direto que testa a autoimagem do espectador ('se você não passar, não é X').
- exemplos: https://www.youtube.com/watch?v=DfN8yuMyCCY seg 0.0 (trecho 4def4858.mp3)
- ids: 4def4858

### 35. [visual] Círculo vermelho grande e chamativo destacando o ponto central de interesse na cena inicial.
- visto em 1 vídeo(s) · nota máx. 8 · modelos: gemini
- como aplicar: Adicionar um círculo vermelho estático ou com leve pulso na abertura de vídeos de experimentos ou desafios para reter a atenção nos primeiros segundos.
- por que é novo: Destaca instantaneamente o objeto da pegadinha/experimento logo no primeiro segundo sem precisar de zoom excessivo.
- exemplos: https://www.youtube.com/watch?v=3Z4MIMtfymc seg 0.8 (trecho f27f4d0f.mp4)
- ids: f27f4d0f

### 36. [efeito] Lágrimas em cascata em estilo cartoon coladas direto no rosto da pessoa
- visto em 1 vídeo(s) · nota máx. 8 · modelos: claude-sonnet
- como aplicar: Aplicar o efeito de cachoeira de choro cômico cartoon nos olhos do mascote ou personagens de cortes em momentos de decepção exagerada ou birra.
- por que é novo: Temos emojis de choro estáticos, mas não o efeito visual de cachoeira de lágrimas estilo anime aplicado e rastreado sob os olhos.
- exemplos: https://www.youtube.com/watch?v=p9EE3Sam-Vo seg 10.3 (trecho 9b3d4845.mp4)
- ids: 9b3d4845

### 37. [outro] Narrativa visual de escalada extrema (de vara rústica de bambu pescando lambari para briga com peixe gigante na corredeira)
- visto em 1 vídeo(s) · nota máx. 8 · modelos: claude-sonnet
- como aplicar: Em roteiros sobre desafios ou ferramentas simples, abrir mostrando o uso mais básico/frágil possível e cortar direto para um resultado surpreendente/extremo usando o mesmo recurso
- por que é novo: Estrutura de contraste 'começa bobo/humilde e escala para proporções épicas' sem necessidade de meme inserido, prendendo a atenção por pura progressão de escala
- exemplos: https://www.youtube.com/watch?v=RjwS1Qbkx7I seg 3.1 (trecho 2f9d4b30.mp4)
- ids: 2f9d4b30

### 38. [visual] Efeito de raio/eletricidade animado sobreposto em cena da natureza (enguia elétrica)
- visto em 1 vídeo(s) · nota máx. 8 · modelos: gemini
- como aplicar: Aplicar overlays de raios (ex: pacotes tipo electric_00d1ff) com blend mode screen/add em cenas de alta tensão ou curiosidades científicas.
- por que é novo: Uso de raios estilizados dinâmicos para ilustrar descarga elétrica animal de forma dramática.
- exemplos: https://www.youtube.com/watch?v=jX1AyRy4U4E seg 16.4 (trecho 7cdae444.mp4)
- ids: 7cdae444

### 39. [visual] Transição de cena mostrando primeiro o produto em detalhes na mão e imediatamente após a tomada do produto sendo usado no cenário real (pescaria/água).
- visto em 1 vídeo(s) · nota máx. 8 · modelos: gemini
- como aplicar: Alternar cortes curtos entre o close do produto em estúdio/mesa e o uso prático no cenário real nos vídeos explicativos.
- por que é novo: Cria conexão direta entre a promessa/detalhe de bancada e a prova real de funcionamento.
- exemplos: https://www.youtube.com/watch?v=N8JyUT seg 6.7 (trecho c9432f7a.mp4)
- ids: c9432f7a

### 40. [visual] Perspectiva em primeira pessoa misturando visão aérea/subaquática de pesca com dicas estratégicas rápidas
- visto em 1 vídeo(s) · nota máx. 8 · modelos: gemini
- como aplicar: Usar takes em primeira pessoa e visão subaquática em vídeos de tutoriais ou curiosidades práticas de forma imersiva.
- por que é novo: Foca em tomadas de drone e underwater POV combinadas com narração de dica de pesca prática e direta ao ponto.
- exemplos: https://www.youtube.com/watch?v=ON seg 2.8 (trecho ae42b95e.mp4)
- ids: ae42b95e

(+ 443 grupo(s) mais fracos: vistos em 1 vídeo só; ficam no acervo.jsonl)
