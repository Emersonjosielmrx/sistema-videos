# Aprendizado com os parceiros — PARA IMPLEMENTAR (refeito a cada rodada; não editar à mão)

Atualizado 19/11/2026 03:57. Gerado por D:\video-fila\aprendizado.py.

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

### 1. [visual] Split-screen em grade 2x2 com mini-vídeos simultâneos de bastidores de e-commerce e produtos
- visto em 1 vídeo(s) · nota máx. 8 · modelos: claude-sonnet
- como aplicar: Criar template de grade 2x2 no ffmpeg/editor para exibir 4 takes curtos de ação rápida ou provas visuais nos primeiros 3 segundos de gancho.
- por que é novo: Nossos dividers e cortes mostram no máximo 2 planos ou reações; uma montagem em mosaico/grid 4x4 dinâmico simultâneo gera retenção visual rápida e sobrecarga positiva de contexto no gancho inicial.
- exemplos: https://www.youtube.com/watch?v=fj1EaCM4k3c seg 2.7 (trecho fb06c4f9.mp4)
- ids: fb06c4f9

### 2. [efeito] Flash/dimming escuro na tela inteira para enfatizar palavra séria/investimento
- visto em 1 vídeo(s) · nota máx. 7 · modelos: claude-sonnet
- como aplicar: Aplicar keyframe de brilho/exposição reduzindo 50-70% durante 1 a 1.5s sincronizado com palavras de alerta ou peso financeiro.
- por que é novo: Ao invés de apenas dar zoom ou aplicar meme, o vídeo escurece a iluminação geral/exposição da cena no exato momento da palavra-chave 'um investimento', trazendo peso dramático imediato.
- exemplos: https://www.youtube.com/watch?v=fj1EaCM4k3c seg 40.5 (trecho fda42c0c.mp4)
- ids: fda42c0c

### 3. [visual] Uso de split-screen com múltiplos vídeos de B-roll na introdução
- visto em 1 vídeo(s) · nota máx. 8 · modelos: gemini
- como aplicar: Criar templates de grade (grid 2x2 ou 3 colunas) com clipes curtos de produtos acelerados nos primeiros segundos dos nossos vídeos.
- por que é novo: Mostra vários nichos/produtos diferentes simultaneamente em uma grade na tela dividida para capturar atenção rápida antes de focar na apresentadora.
- exemplos: https://www.youtube.com/watch?v=fj1EaCM4k3c seg 0.0 (trecho 06a19fb0.mp4)
- ids: 06a19fb0

### 4. [visual] Uso de títulos regionais estilizados com fontes serifadas elegantes em destaque no topo dos quadros (ex: NORDEST, PANTANAL, AMA, ROÇA MINEIRA)
- visto em 1 vídeo(s) · nota máx. 8 · modelos: gemini
- como aplicar: Adicionar um bloco superior com fundo semi-transparente ou texto serifado elegante em caixa alta para categorizar tópicos ou regiões dos vídeos.
- por que é novo: Apresenta uma identidade visual limpa e elegante de títulos por região que diferencia categorias geográficas sem poluir.
- exemplos: https://www.youtube.com/watch?v=u6 seg 0.0 (trecho b76a25c4.mp4)
- ids: b76a25c4

### 5. [visual] Alternância fluida entre cenas geradas por IA de casais típicos locais e vídeos reais em close-up de preparação de pratos e cortes de carne
- visto em 1 vídeo(s) · nota máx. 9 · modelos: gemini
- como aplicar: Criar sequências combinando gerador de imagens de rostos/cenários temáticos com clipes b-roll reais de comidas tipicas e preparos culinários.
- por que é novo: Mistura perfeitamente personas ilustrativas humanizadas (geradas por IA) com texturas e close-ups reais de gastronomia para dar alta retenção e apetite appeal.
- exemplos: https://www.youtube.com/watch?v=u6 seg 3.4 (trecho 432ec224.mp4)
- ids: 432ec224

## B. Candidatos (sem resposta em 24 h): 423 grupo(s), os 40 mais fortes

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

### 6. [piada] Dica final anti-clímax que quebra a lógica do filme com conselho prático da vida real ('Arrume um emprego')
- visto em 1 vídeo(s) · nota máx. 8 · modelos: claude-sonnet
- como aplicar: Em vídeos de 'como sobreviver / como derrotar vilão de filme', fechar com dica realista/moral cômica acompanhada de meme ou homem de terno para gerar humor por quebra de expectativa.
- por que é novo: Estrutura de roteiro humorístico onde a última dica de sobrevivência em filme de assalto/invasão ignora o perigo imediato e ataca a causa raiz dos personagens serem ladrões.
- exemplos: https://www.youtube.com/watch?v=uEibbO00qvg seg 28.0 (trecho 19f17dea.mp3)
- ids: 19f17dea

### 7. [jeito_de_falar] Hook contra-intuitivo de quebra de objeção emocional ('E antes de você sentir raiva ou inveja, vou te mostrar o que isso significa para você')
- visto em 1 vídeo(s) · nota máx. 8 · modelos: claude-sonnet
- como aplicar: Em roteiros polêmicos sobre bilionários, riqueza ou privilégio, estruturar os primeiros 3 segundos desarmando o julgamento moral do espectador para focar na utilidade prática para a vida dele.
- por que é novo: Nossos scripts de intro focam em curiosidade direta ou choque; antecipar a emoção negativa do espectador (inveja/revolta) e redirecioná-la imediatamente para benefício próprio é uma técnica de retenção que ainda não aplicamos na copywriting.
- exemplos: https://www.youtube.com/watch?v=JGGdTT7rxdE seg 0.0 (trecho 746b7a80.mp3)
- ids: 746b7a80

### 8. [visual] Uso de imagens de arquivo reais de eventos e palestras reais (como a Nasdaq/SpaceX) como b-roll de fundo
- visto em 1 vídeo(s) · nota máx. 8 · modelos: gemini
- como aplicar: Integrar trechos curtos de vídeos públicos reais de anúncios ou eventos corporativos ao ilustrar notícias de grandes empresas.
- por que é novo: Dá autoridade e aspecto jornalístico/documental ao vídeo em vez de usar apenas memes ou imagens genéricas de banco.
- exemplos: https://www.youtube.com/watch?v=JGGdTT7rxdE seg 9.0 (trecho fa72b2fd.mp4)
- ids: fa72b2fd

### 9. [visual] Texto com contorno amarelo e fonte arredondada conversacional ('Jennie's skirt blew up...')
- visto em 1 vídeo(s) · nota máx. 8 · modelos: gemini
- como aplicar: Aplicar legenda central com fonte grossa (ex: LuckiestGuy ou Montserrat Black), contorno preto forte e cor amarela.
- por que é novo: Legenda centralizada chamativa típica de edits virais do TikTok com destaque em cor contrastante.
- exemplos: https://www.youtube.com/watch?v=kpOcL4dgh80 seg 2.6 (trecho e8cd84ff.mp4)
- ids: e8cd84ff

### 10. [visual] Texto cursor/destaque humorístico com asteriscos ('*Her shy smile*', '*notice* 👀')
- visto em 1 vídeo(s) · nota máx. 8 · modelos: gemini
- como aplicar: Inserir caixas de texto curtas no topo central com asteriscos para narrar o pensamento do editor ou o foco da cena.
- por que é novo: Adiciona comentário irônico em formato de pensamento/narração interna no topo da tela.
- exemplos: https://www.youtube.com/watch?v=kpOcL4dgh80 seg 7.7 (trecho 541173a5.mp4)
- ids: 541173a5

### 11. [visual] Uso de setas coloridas dinâmicas apontando para a boca/comida e círculos vermelhos enfatizando os exageros
- visto em 1 vídeo(s) · nota máx. 8 · modelos: gemini
- como aplicar: Inserir setas e círculos vermelhos/verdes pontuais para guiar o olhar do espectador para detalhes cômicos em vídeos de reação.
- por que é novo: Destaca com setas e círculos minimalistas de edição rápida a forma engraçada como os ídolos comem.
- exemplos: https://www.youtube.com/watch?v=kHe8oWuoU8o seg 1.6 (trecho 0c6db3cc.mp4)
- ids: 0c6db3cc

### 12. [visual] Infográfico minimalista estilo 2D vetorizado com escala de pH colorida (1 a 14) e ponteiro indicador ao lado do objeto
- visto em 1 vídeo(s) · nota máx. 8 · modelos: claude-sonnet
- como aplicar: Criar templates de infográficos dinâmicos (ex: termômetro, escala de nível, régua comparativa) em fundo com textura sutil e ponteiro animado para momentos explicativos/didáticos dos shorts.
- por que é novo: Temos recortes de memes e hyperframes com números grandes ou badges, mas não temos overlays infográficos verticais didáticos em estética vetor limpo/sketch para explicar métricas ou comparações técnicas de forma direta.
- exemplos: https://www.youtube.com/watch?v=MaL4mZoNZ5A seg 27.0 (trecho c10fb495.mp4)
- ids: c10fb495

### 13. [piada] Conselhos absurdos/literais de sobrevivência contra clichês de terror ('dormir na rua porque não tem porta pra bater', 'tacar fogo na casa')
- visto em 1 vídeo(s) · nota máx. 8 · modelos: claude-sonnet
- como aplicar: Roteirizar shorts com guias de sobrevivência zombando de clichês de animes ou filmes famosos que cobrimos
- por que é novo: Formato de lista satírica de 'como derrotar [filme/monstro] em 30 segundos' desconstruindo clichês clássicos do gênero com soluções burras/extremas
- exemplos: https://www.youtube.com/watch?v=p4F3hWc-VUQ seg 4.9 (trecho 25b636e0.mp3)
- ids: 25b636e0

### 14. [visual] HUD/Tela diegética militar sci-fi com tipografia pixelada, radar e log de sistema simulando visor quebrado
- visto em 1 vídeo(s) · nota máx. 8 · modelos: claude-sonnet
- como aplicar: Criar templates de overlay no Remotion/FFmpeg com máscara de CRT/scanlines, radar circular verde e texto em fonte monospace vermelha/verde para cortes de contexto tecnológico, IA ou batalha futurista.
- por que é novo: Nossos assets têm apenas dividers elétricos/fogo e hyperframes comuns; não temos overlays diegéticos de HUD sci-fi militar com texto de telemetria/radar dinâmico integrado ao storytelling.
- exemplos: https://www.youtube.com/watch?v=BcOEA3k2C-E seg 14.0 (trecho 07d6b4df.mp4)
- ids: 07d6b4df

### 15. [jeito_de_falar] Gancho trágico-narrativo com paradoxo humano/máquina ('Este homem está morto há centenas de anos, mas este bombardeiro continua voando')
- visto em 1 vídeo(s) · nota máx. 8 · modelos: claude-sonnet
- como aplicar: Adotar no primeiro segundo do roteiro frases de antítese radical ('[Sujeito] já morreu há séculos, mas [máquina/entidade] ainda executa a mesma ordem') para retenção imediata em resumos de filmes/jogos.
- por que é novo: Nossas intros em intros_voz focam em bordões e reações; falta essa fórmula de gancho com quebra conceitual dramática em histórias de ficção/resumos de animação.
- exemplos: https://www.youtube.com/watch?v=BcOEA3k2C-E seg 0.0 (trecho b9dbc82f.mp3)
- ids: b9dbc82f

### 16. [efeito] Ícone gráfico de raiva/fogo colado na cabeça do personagem (anime style)
- visto em 1 vídeo(s) · nota máx. 7.5 · modelos: claude-sonnet
- como aplicar: Criar overlays gráficos estilo mangá/anime (veia saltada, fogo de raiva, gota de suor na cabeça) e aplicar em reações dos personagens em momentos de choque ou tensão.
- por que é novo: Usa um sticker 2D animado de fogo e veia de raiva rastreado sutilmente no cabelo da personagem para pontuar irritação cômica/dramática, recurso comum em doramas/animes que não temos catalogado.
- exemplos: https://www.youtube.com/watch?v=d2apjZs70bA seg 115.0 (trecho d3eb4fbd.mp4)
- ids: d3eb4fbd

### 17. [efeito] Zoom rápido (punch-in) acompanhado de efeito de brilho (glitter/sparkle) no canto superior
- visto em 1 vídeo(s) · nota máx. 7 · modelos: gemini
- como aplicar: Adicionar o overlay 'magic_sparkle' exatamente no frame onde ocorre o zoom de impacto em momentos de descoberta ou truques.
- por que é novo: Usamos zooms, mas não combinamos com o elemento visual de 'brilho' para enfatizar momentos de revelação ou 'sacadas' inteligentes.
- exemplos: https://www.youtube.com/watch?v=MfAQkNeypDQ seg 3.7 (trecho ef9b9ddc.mp4)
- ids: ef9b9ddc

### 18. [visual] Palavras-chave isoladas em cards (IMPROVISARAM 9.9s, JANGADA 9.9s, ÁGUA 23s, PRÉDIO 36.2s)
- visto em 1 vídeo(s) · nota máx. 7 · modelos: claude-sonnet
- como aplicar: Em momentos-chave da narrativa, pausar a legenda corrida e mostrar um card com a palavra central (substantivo ou verbo importante) em destaque, como flash card. Reforça conceitos e adiciona ritmo visual
- por que é novo: Vocês destacam palavras na legenda corrida, mas não vejo cards isolados com uma palavra-chave sozinha ocupando destaque
- exemplos: https://www.youtube.com/watch?v=l9EneN3osGs seg 9.9 (trecho 9299b2bd.mp4)
- ids: 9299b2bd

### 19. [visual] Zoom dramático em personagem chibi isolada em fundo escuro/vazio aos 20.7s
- visto em 1 vídeo(s) · nota máx. 7 · modelos: claude-sonnet
- como aplicar: Quando narrar momento de reflexão/pensamento do personagem, fazer cut para fundo preto ou escuro com apenas o personagem em destaque. Usar mascote_mov em fundo escuro quando adequado ao contexto emocional
- por que é novo: Não temos transição para fundo completamente escuro com personagem isolada. Nossos fundos são sempre cenários de anime ou fillers gerados
- exemplos: https://www.youtube.com/watch?v=njMk9HkANtA seg 20.7 (trecho a7534b68.mp4)
- ids: a7534b68

### 20. [visual] Gradiente de cor cinematográfico aplicado sobre toda a imagem (amarelo-esverdeado para prisão, azul para advogado)
- visto em 1 vídeo(s) · nota máx. 7 · modelos: claude-sonnet
- como aplicar: Adicionar layer de ajuste de cor com overlay de gradiente sutil ou LUT cinematográfico. Para tensão: tons quentes dessaturados. Para alívio/esperança: tons frios. Para suspense: verde-azulado. Aplicar em 20-40% de opacidade.
- por que é novo: Vocês têm overlays e efeitos, mas não aplicam correção de cor/grading consistente para criar mood. Este vídeo usa tons quentes/sufocantes (amarelo-verde) na prisão e azul frio para cenas externas/autoridade.
- exemplos: https://www.youtube.com/watch?v=3m51S-mqsvI seg 0 (trecho b4b3f17c.mp4)
- ids: b4b3f17c

### 21. [visual] Texto em chinês com estilo neon/holográfico em tela de tablet
- visto em 1 vídeo(s) · nota máx. 7 · modelos: claude-sonnet
- como aplicar: Criar overlay de tablet/celular holográfico com texto que brilha em ciano/azul neon para momentos de revelação ou informação importante
- por que é novo: Usamos texto na tela mas não com efeito holográfico/neon em dispositivos dentro da cena anime
- exemplos: https://www.youtube.com/watch?v=A72DXdSi0cY seg 1576.1 (trecho 1a1977ac.mp4)
- ids: 1a1977ac

### 22. [visual] Efeito de 'câmera de segurança' (scanlines e leve distorção)
- visto em 1 vídeo(s) · nota máx. 7 · modelos: gemini
- como aplicar: Aplicar um filtro de 'CCTV' ou 'Security Camera' sobre cenas de ação ou momentos de revelação para dar um tom de mistério.
- por que é novo: Adiciona uma camada de realismo e tensão à narrativa, simulando um ponto de vista externo, o que ajuda a variar a estética visual do vídeo.
- exemplos: https://www.youtube.com/watch?v=A72DXdSi0cY seg 1333.6 (trecho bf4ec878.mp4)
- ids: bf4ec878

### 23. [visual] Close-up macro detalhado em elemento de arma com raios/energia elétrica sobreposta
- visto em 1 vídeo(s) · nota máx. 7 · modelos: gemini
- como aplicar: Usar clipes B-roll macro de armas ou itens mágicos com efeitos de raio elétrico customizados nas cenas de ação intensa.
- por que é novo: Foca em detalhes técnicos/armamento com efeito visual de energia que não temos integrado nos clipes padrão.
- exemplos: https://www.youtube.com/watch?v=fjYFUZwwYiE seg 353.6 (trecho f943ba00.mp4)
- ids: f943ba00

### 24. [visual] Bordas desfocadas laterais (vignette escurecido) mantidas durante todo o vídeo
- visto em 1 vídeo(s) · nota máx. 7 · modelos: claude-sonnet
- como aplicar: Adicionar como overlay fixo em todos os vídeos, escurecendo/desfocando as laterais em 20-30% para dar profundidade ao conteúdo central do manhwa/webtoon.
- por que é novo: Vocês têm vários overlays e efeitos, mas não vi um vignette lateral permanente na lista de overlays. Isso cria profundidade e foco no centro mantendo o formato vertical.
- exemplos: https://www.youtube.com/watch?v=97bBeHddKJI seg 0 (trecho f6ab53e1.mp4)
- ids: f6ab53e1

### 25. [visual] Símbolos de onomatopeia flutuantes grandes (ドォ no frame 8458.4)
- visto em 1 vídeo(s) · nota máx. 7 · modelos: claude-sonnet
- como aplicar: Criar pack de onomatopeias em estilo asiático (ドォ, バン, etc) para usar em momentos de impacto, surpresa ou ação em vídeos de manhwa/webtoon.
- por que é novo: Vocês têm texto na tela e emojis, mas não vi onomatopeias estilizadas orientais (katakana/kanji) como elemento visual. É característico de manhwa/manga.
- exemplos: https://www.youtube.com/watch?v=97bBeHddKJI seg 8458.4 (trecho e1260b68.mp4)
- ids: e1260b68

### 26. [visual] Uso de estilo webtoon cômico com enquadramentos dinâmicos alternando reações exageradas e cenas de ação pastelão.
- visto em 1 vídeo(s) · nota máx. 7 · modelos: gemini
- como aplicar: Importar imagens/quadros no estilo webtoon coreano com traços cômicos e coloridos para momentos de alívio cômico nas edições.
- por que é novo: Foca em quadros de estilo manwha/webtoon fofos e cômicos intercalados rapidamente, o que difere dos recortes de animes tradicionais que usamos.
- exemplos: https://www.youtube.com/watch?v=97bBeHddKJI seg 497.6 (trecho 7730c909.mp4)
- ids: 7730c909

### 27. [visual] Legenda posicionada na parte inferior do quadro de vídeo (não no rodapé da tela)
- visto em 1 vídeo(s) · nota máx. 7 · modelos: claude-sonnet
- como aplicar: Reposicionar legendas para ficarem sobrepondo a parte inferior do vídeo (cerca de 20-25% da altura) em vez de ocupar a barra preta inferior. Ajustar templates de legenda
- por que é novo: As legendas ficam dentro da área de conteúdo visual, não no rodapé preto. Cria composição mais integrada entre vídeo e texto
- exemplos: https://www.youtube.com/watch?v=4-0RCWGjj2g seg 2.9 (trecho 886a8ef1.mp4)
- ids: 886a8ef1

### 28. [visual] Transição para quadro completamente preto com objeto isolado (tubarão pendurado iluminado, ~24-29s)
- visto em 1 vídeo(s) · nota máx. 7 · modelos: claude-sonnet
- como aplicar: Adicionar template de 'spotlight dramático': fundo preto + feixe de luz no objeto importante + silêncio ou som ambiente baixo. Usar em momentos de tensão, revelação ou quando o objeto é a chave da cena seguinte
- por que é novo: Vocês têm dividers e máscaras, mas não usam corte dramático pra fundo 100% preto com spotlight no objeto. Aqui isola o tubarão pendurado criando suspense visual
- exemplos: https://www.youtube.com/watch?v=4I3-q4FFNp4 seg 24 (trecho 5cf36614.mp4)
- ids: 5cf36614

### 29. [efeito] Tilt-shift (miniaturização) em cena de vila
- visto em 1 vídeo(s) · nota máx. 7 · modelos: claude-sonnet
- como aplicar: Aplicar blur gradual nas bordas superior/inferior em cenas de mundo aberto ou cenários amplos para dar escala épica ou humor. Pode criar overlay 'fx_tiltshift'
- por que é novo: Não temos efeito de tilt-shift na lista de overlays. Cria sensação de maquete/miniatura, diferente dos nossos efeitos de câmera
- exemplos: https://www.youtube.com/watch?v=sC0fy3NBl6g seg 862.3 (trecho fced140c.mp4)
- ids: fced140c

### 30. [visual] Legendas curtas de uma palavra sincronizadas com fala
- visto em 1 vídeo(s) · nota máx. 7 · modelos: claude-sonnet
- como aplicar: Trocar legendas de frase completa por palavras-chave isoladas que aparecem no ritmo da fala. Usar palavras de impacto ou transição da narração
- por que é novo: Legendas extremamente sintéticas (EM, RAPIDAMENTE, QUE, LOGO, CONCLUÍRAM, TRATAVA, MARINADA, RECOLHIDAS, HAVIA) aparecem isoladas no centro inferior, não frases completas
- exemplos: https://www.youtube.com/watch?v=WLC0xm4R3lY seg 9.4
- ids: 3fcb8603

### 31. [jeito_de_falar] Uso de termos coloquiais e irônicos ('anjo sofrido', 'infeliz cozinhado', 'resumo da ópera')
- visto em 1 vídeo(s) · nota máx. 7 · modelos: gemini
- como aplicar: Adotar um roteiro com mais personalidade, usando adjetivos irônicos para descrever as situações e personagens.
- por que é novo: Dá um tom de crônica/fofoca ao conteúdo de crime, tornando o vídeo mais leve e menos 'robótico' do que uma narração puramente informativa.
- exemplos: https://www.youtube.com/watch?v=WLC0xm4R3lY seg 9.4
- ids: 788c0527

### 32. [transição] Mudança de paleta de cor por cena/mood (tons quentes→frios→neutros)
- visto em 1 vídeo(s) · nota máx. 7 · modelos: claude-sonnet
- como aplicar: Aplicar correção de cor ou LUT por segmento narrativo para reforçar atmosfera (tensão=verde escuro, romance=rosa, ação=laranja intenso)
- por que é novo: Usamos overlays e dividers, mas não mudamos a paleta base do vídeo. Aqui cada cena tem tonalidade própria: laranja (291.9), sépia (875.6), rosa dramático (1459.3), verde escuro (2043.0)
- exemplos: https://www.youtube.com/watch?v=ssMbrCz0fhE seg 0 (trecho 187c4870.mp4)
- ids: 187c4870

### 33. [efeito] Arco de energia/magia animado com texto sobreposto
- visto em 1 vídeo(s) · nota máx. 7 · modelos: claude-sonnet
- como aplicar: Criar overlay de arco animado (curva laranja com trail) para momentos de habilidade especial ou revelação dramática, com texto integrado ao traço luminoso
- por que é novo: Temos fx_powerup e fx_magic_sparkle, mas não esse tipo de arco luminoso laranja/vermelho que atravessa a tela com texto integrado ('I REGRET THE CLEVEN HYMIRREL PROMOTION')
- exemplos: https://www.youtube.com/watch?v=ssMbrCz0fhE seg 3794.1 (trecho 7daa1f9d.mp4)
- ids: 7daa1f9d

### 34. [visual] Barra de progresso laranja horizontal abaixo do título
- visto em 1 vídeo(s) · nota máx. 7 · modelos: claude-sonnet
- como aplicar: Implementar barra de progresso horizontal fina (2-3px) abaixo do título fixo, cor laranja/vermelha da nossa paleta, animada para preencher conforme duração do vídeo
- por que é novo: Usa barra de progresso horizontal laranja/vermelha que avança durante o vídeo, não temos esse tipo de indicador de progresso
- exemplos: https://www.youtube.com/watch?v=DQ6WM3LBeDY seg 0 (trecho 5c355a42.mp4)
- ids: 5c355a42

### 35. [jeito_de_falar] Uso de expressões coloquiais e bem-humoradas ('Minha nossa senhora da rosquinha recheada')
- visto em 1 vídeo(s) · nota máx. 7 · modelos: gemini
- como aplicar: Inserir 'exclamações de personagem' ou gírias específicas que fujam do padrão técnico, humanizando o narrador.
- por que é novo: Nosso tom é mais direto. O uso de frases criativas e engraçadas cria uma conexão mais forte e autêntica com o público.
- exemplos: https://www.youtube.com/watch?v=DQ6WM3LBeDY seg 31.9 (trecho 0ff17673.mp3)
- ids: 0ff17673

### 36. [piada] Quebra de expectativa com interjeição ('hihihi, levei vantagem!')
- visto em 1 vídeo(s) · nota máx. 7 · modelos: gemini
- como aplicar: Adicionar comentários curtos em primeira pessoa que zombam da situação descrita, como se o narrador estivesse assistindo ao evento.
- por que é novo: O narrador assume uma persona sarcástica que comenta o erro da empresa, tornando o conteúdo educativo em entretenimento.
- exemplos: https://www.youtube.com/watch?v=DQ6WM3LBeDY seg 10.6 (trecho 64f0f7ac.mp3)
- ids: 64f0f7ac

### 37. [visual] Legendas minimalistas: uma palavra por cena (cidade, garoto, eliminado, soldados, segurou, correr, pro, apertaram, virou, mas)
- visto em 1 vídeo(s) · nota máx. 7 · modelos: claude-sonnet
- como aplicar: Em vídeos de ação/tensão, usar legenda de palavra única como marcador de beat narrativo ao invés de frase explicativa. Mantém ritmo rápido e força atenção visual
- por que é novo: Nossas legendas costumam ter frases completas ou palavras com destaque colorido. Aqui é só substantivo/verbo isolado em branco, deixando a imagem contar
- exemplos: https://www.youtube.com/watch?v=-eob8rfFRAk seg 6.4 (trecho 902e1698.mp4)
- ids: 902e1698

### 38. [visual] Paleta de cores dessaturada e sombria para atmosfera de terror
- visto em 1 vídeo(s) · nota máx. 7 · modelos: claude-sonnet
- como aplicar: Criar preset de correção de cor com dessaturação e tons frios/escuros para aplicar em cenas de suspense e terror, especialmente em narrativas mais sérias.
- por que é novo: Uso consistente de tons escuros, azulados e cinzentos para criar mood de terror psicológico. Nossos overlays têm cores vibrantes (electric, fire), não tons sombrios narrativos.
- exemplos: https://www.youtube.com/watch?v=PxPZcsHTgAE seg 1532.7 (trecho 5e73a180.mp4)
- ids: 5e73a180

### 39. [visual] Personagem creepy com design perturbador como antagonista visual
- visto em 1 vídeo(s) · nota máx. 7 · modelos: claude-sonnet
- como aplicar: Criar versão 'horror' do mascote ou personagens antagonistas assustadores para usar em narrativas de terror, como reveal final ou jump scare visual.
- por que é novo: Design de personagem assustador (rosto pálido, sorriso perturbador, olhos grandes) como payoff visual. Nosso mascote tem poses emocionais mas não tem versão genuinamente assustadora/perturbadora.
- exemplos: https://www.youtube.com/watch?v=PxPZcsHTgAE seg 9707.4 (trecho ae7a7955.mp4)
- ids: ae7a7955

### 40. [visual] Uso de elementos gráficos de ambiente (ex: chuva) integrados à animação.
- visto em 1 vídeo(s) · nota máx. 7 · modelos: gemini
- como aplicar: Usar overlays de partículas (chuva, neve, poeira) em cenas de transição ou ambientação.
- por que é novo: Nossas animações são estáticas; adicionar efeitos climáticos dinâmicos aumenta a imersão.
- exemplos: https://www.youtube.com/watch?v=PxPZcsHTgAE seg 7663.7 (trecho 71f82141.mp4)
- ids: 71f82141

(+ 383 grupo(s) mais fracos: vistos em 1 vídeo só; ficam no acervo.jsonl)
