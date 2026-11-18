# Aprendizado com os parceiros — PARA IMPLEMENTAR (refeito a cada rodada; não editar à mão)

Atualizado 17/11/2026 19:40. Gerado por D:\video-fila\aprendizado.py.

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

## B. Candidatos (sem resposta em 24 h): 394 grupo(s), os 40 mais fortes

### 1. [efeito] Zoom rápido (punch-in) acompanhado de efeito de brilho (glitter/sparkle) no canto superior
- visto em 1 vídeo(s) · nota máx. 7 · modelos: gemini
- como aplicar: Adicionar o overlay 'magic_sparkle' exatamente no frame onde ocorre o zoom de impacto em momentos de descoberta ou truques.
- por que é novo: Usamos zooms, mas não combinamos com o elemento visual de 'brilho' para enfatizar momentos de revelação ou 'sacadas' inteligentes.
- exemplos: https://www.youtube.com/watch?v=MfAQkNeypDQ seg 3.7 (trecho ef9b9ddc.mp4)
- ids: ef9b9ddc

### 2. [visual] Palavras-chave isoladas em cards (IMPROVISARAM 9.9s, JANGADA 9.9s, ÁGUA 23s, PRÉDIO 36.2s)
- visto em 1 vídeo(s) · nota máx. 7 · modelos: claude-sonnet
- como aplicar: Em momentos-chave da narrativa, pausar a legenda corrida e mostrar um card com a palavra central (substantivo ou verbo importante) em destaque, como flash card. Reforça conceitos e adiciona ritmo visual
- por que é novo: Vocês destacam palavras na legenda corrida, mas não vejo cards isolados com uma palavra-chave sozinha ocupando destaque
- exemplos: https://www.youtube.com/watch?v=l9EneN3osGs seg 9.9 (trecho 9299b2bd.mp4)
- ids: 9299b2bd

### 3. [visual] Zoom dramático em personagem chibi isolada em fundo escuro/vazio aos 20.7s
- visto em 1 vídeo(s) · nota máx. 7 · modelos: claude-sonnet
- como aplicar: Quando narrar momento de reflexão/pensamento do personagem, fazer cut para fundo preto ou escuro com apenas o personagem em destaque. Usar mascote_mov em fundo escuro quando adequado ao contexto emocional
- por que é novo: Não temos transição para fundo completamente escuro com personagem isolada. Nossos fundos são sempre cenários de anime ou fillers gerados
- exemplos: https://www.youtube.com/watch?v=njMk9HkANtA seg 20.7 (trecho a7534b68.mp4)
- ids: a7534b68

### 4. [visual] Gradiente de cor cinematográfico aplicado sobre toda a imagem (amarelo-esverdeado para prisão, azul para advogado)
- visto em 1 vídeo(s) · nota máx. 7 · modelos: claude-sonnet
- como aplicar: Adicionar layer de ajuste de cor com overlay de gradiente sutil ou LUT cinematográfico. Para tensão: tons quentes dessaturados. Para alívio/esperança: tons frios. Para suspense: verde-azulado. Aplicar em 20-40% de opacidade.
- por que é novo: Vocês têm overlays e efeitos, mas não aplicam correção de cor/grading consistente para criar mood. Este vídeo usa tons quentes/sufocantes (amarelo-verde) na prisão e azul frio para cenas externas/autoridade.
- exemplos: https://www.youtube.com/watch?v=3m51S-mqsvI seg 0 (trecho b4b3f17c.mp4)
- ids: b4b3f17c

### 5. [visual] Texto em chinês com estilo neon/holográfico em tela de tablet
- visto em 1 vídeo(s) · nota máx. 7 · modelos: claude-sonnet
- como aplicar: Criar overlay de tablet/celular holográfico com texto que brilha em ciano/azul neon para momentos de revelação ou informação importante
- por que é novo: Usamos texto na tela mas não com efeito holográfico/neon em dispositivos dentro da cena anime
- exemplos: https://www.youtube.com/watch?v=A72DXdSi0cY seg 1576.1 (trecho 1a1977ac.mp4)
- ids: 1a1977ac

### 6. [visual] Efeito de 'câmera de segurança' (scanlines e leve distorção)
- visto em 1 vídeo(s) · nota máx. 7 · modelos: gemini
- como aplicar: Aplicar um filtro de 'CCTV' ou 'Security Camera' sobre cenas de ação ou momentos de revelação para dar um tom de mistério.
- por que é novo: Adiciona uma camada de realismo e tensão à narrativa, simulando um ponto de vista externo, o que ajuda a variar a estética visual do vídeo.
- exemplos: https://www.youtube.com/watch?v=A72DXdSi0cY seg 1333.6 (trecho bf4ec878.mp4)
- ids: bf4ec878

### 7. [visual] Close-up macro detalhado em elemento de arma com raios/energia elétrica sobreposta
- visto em 1 vídeo(s) · nota máx. 7 · modelos: gemini
- como aplicar: Usar clipes B-roll macro de armas ou itens mágicos com efeitos de raio elétrico customizados nas cenas de ação intensa.
- por que é novo: Foca em detalhes técnicos/armamento com efeito visual de energia que não temos integrado nos clipes padrão.
- exemplos: https://www.youtube.com/watch?v=fjYFUZwwYiE seg 353.6 (trecho f943ba00.mp4)
- ids: f943ba00

### 8. [visual] Bordas desfocadas laterais (vignette escurecido) mantidas durante todo o vídeo
- visto em 1 vídeo(s) · nota máx. 7 · modelos: claude-sonnet
- como aplicar: Adicionar como overlay fixo em todos os vídeos, escurecendo/desfocando as laterais em 20-30% para dar profundidade ao conteúdo central do manhwa/webtoon.
- por que é novo: Vocês têm vários overlays e efeitos, mas não vi um vignette lateral permanente na lista de overlays. Isso cria profundidade e foco no centro mantendo o formato vertical.
- exemplos: https://www.youtube.com/watch?v=97bBeHddKJI seg 0 (trecho f6ab53e1.mp4)
- ids: f6ab53e1

### 9. [visual] Símbolos de onomatopeia flutuantes grandes (ドォ no frame 8458.4)
- visto em 1 vídeo(s) · nota máx. 7 · modelos: claude-sonnet
- como aplicar: Criar pack de onomatopeias em estilo asiático (ドォ, バン, etc) para usar em momentos de impacto, surpresa ou ação em vídeos de manhwa/webtoon.
- por que é novo: Vocês têm texto na tela e emojis, mas não vi onomatopeias estilizadas orientais (katakana/kanji) como elemento visual. É característico de manhwa/manga.
- exemplos: https://www.youtube.com/watch?v=97bBeHddKJI seg 8458.4 (trecho e1260b68.mp4)
- ids: e1260b68

### 10. [visual] Uso de estilo webtoon cômico com enquadramentos dinâmicos alternando reações exageradas e cenas de ação pastelão.
- visto em 1 vídeo(s) · nota máx. 7 · modelos: gemini
- como aplicar: Importar imagens/quadros no estilo webtoon coreano com traços cômicos e coloridos para momentos de alívio cômico nas edições.
- por que é novo: Foca em quadros de estilo manwha/webtoon fofos e cômicos intercalados rapidamente, o que difere dos recortes de animes tradicionais que usamos.
- exemplos: https://www.youtube.com/watch?v=97bBeHddKJI seg 497.6 (trecho 7730c909.mp4)
- ids: 7730c909

### 11. [visual] Legenda posicionada na parte inferior do quadro de vídeo (não no rodapé da tela)
- visto em 1 vídeo(s) · nota máx. 7 · modelos: claude-sonnet
- como aplicar: Reposicionar legendas para ficarem sobrepondo a parte inferior do vídeo (cerca de 20-25% da altura) em vez de ocupar a barra preta inferior. Ajustar templates de legenda
- por que é novo: As legendas ficam dentro da área de conteúdo visual, não no rodapé preto. Cria composição mais integrada entre vídeo e texto
- exemplos: https://www.youtube.com/watch?v=4-0RCWGjj2g seg 2.9 (trecho 886a8ef1.mp4)
- ids: 886a8ef1

### 12. [visual] Transição para quadro completamente preto com objeto isolado (tubarão pendurado iluminado, ~24-29s)
- visto em 1 vídeo(s) · nota máx. 7 · modelos: claude-sonnet
- como aplicar: Adicionar template de 'spotlight dramático': fundo preto + feixe de luz no objeto importante + silêncio ou som ambiente baixo. Usar em momentos de tensão, revelação ou quando o objeto é a chave da cena seguinte
- por que é novo: Vocês têm dividers e máscaras, mas não usam corte dramático pra fundo 100% preto com spotlight no objeto. Aqui isola o tubarão pendurado criando suspense visual
- exemplos: https://www.youtube.com/watch?v=4I3-q4FFNp4 seg 24 (trecho 5cf36614.mp4)
- ids: 5cf36614

### 13. [efeito] Tilt-shift (miniaturização) em cena de vila
- visto em 1 vídeo(s) · nota máx. 7 · modelos: claude-sonnet
- como aplicar: Aplicar blur gradual nas bordas superior/inferior em cenas de mundo aberto ou cenários amplos para dar escala épica ou humor. Pode criar overlay 'fx_tiltshift'
- por que é novo: Não temos efeito de tilt-shift na lista de overlays. Cria sensação de maquete/miniatura, diferente dos nossos efeitos de câmera
- exemplos: https://www.youtube.com/watch?v=sC0fy3NBl6g seg 862.3 (trecho fced140c.mp4)
- ids: fced140c

### 14. [visual] Legendas curtas de uma palavra sincronizadas com fala
- visto em 1 vídeo(s) · nota máx. 7 · modelos: claude-sonnet
- como aplicar: Trocar legendas de frase completa por palavras-chave isoladas que aparecem no ritmo da fala. Usar palavras de impacto ou transição da narração
- por que é novo: Legendas extremamente sintéticas (EM, RAPIDAMENTE, QUE, LOGO, CONCLUÍRAM, TRATAVA, MARINADA, RECOLHIDAS, HAVIA) aparecem isoladas no centro inferior, não frases completas
- exemplos: https://www.youtube.com/watch?v=WLC0xm4R3lY seg 9.4
- ids: 3fcb8603

### 15. [jeito_de_falar] Uso de termos coloquiais e irônicos ('anjo sofrido', 'infeliz cozinhado', 'resumo da ópera')
- visto em 1 vídeo(s) · nota máx. 7 · modelos: gemini
- como aplicar: Adotar um roteiro com mais personalidade, usando adjetivos irônicos para descrever as situações e personagens.
- por que é novo: Dá um tom de crônica/fofoca ao conteúdo de crime, tornando o vídeo mais leve e menos 'robótico' do que uma narração puramente informativa.
- exemplos: https://www.youtube.com/watch?v=WLC0xm4R3lY seg 9.4
- ids: 788c0527

### 16. [transição] Mudança de paleta de cor por cena/mood (tons quentes→frios→neutros)
- visto em 1 vídeo(s) · nota máx. 7 · modelos: claude-sonnet
- como aplicar: Aplicar correção de cor ou LUT por segmento narrativo para reforçar atmosfera (tensão=verde escuro, romance=rosa, ação=laranja intenso)
- por que é novo: Usamos overlays e dividers, mas não mudamos a paleta base do vídeo. Aqui cada cena tem tonalidade própria: laranja (291.9), sépia (875.6), rosa dramático (1459.3), verde escuro (2043.0)
- exemplos: https://www.youtube.com/watch?v=ssMbrCz0fhE seg 0 (trecho 187c4870.mp4)
- ids: 187c4870

### 17. [efeito] Arco de energia/magia animado com texto sobreposto
- visto em 1 vídeo(s) · nota máx. 7 · modelos: claude-sonnet
- como aplicar: Criar overlay de arco animado (curva laranja com trail) para momentos de habilidade especial ou revelação dramática, com texto integrado ao traço luminoso
- por que é novo: Temos fx_powerup e fx_magic_sparkle, mas não esse tipo de arco luminoso laranja/vermelho que atravessa a tela com texto integrado ('I REGRET THE CLEVEN HYMIRREL PROMOTION')
- exemplos: https://www.youtube.com/watch?v=ssMbrCz0fhE seg 3794.1 (trecho 7daa1f9d.mp4)
- ids: 7daa1f9d

### 18. [visual] Barra de progresso laranja horizontal abaixo do título
- visto em 1 vídeo(s) · nota máx. 7 · modelos: claude-sonnet
- como aplicar: Implementar barra de progresso horizontal fina (2-3px) abaixo do título fixo, cor laranja/vermelha da nossa paleta, animada para preencher conforme duração do vídeo
- por que é novo: Usa barra de progresso horizontal laranja/vermelha que avança durante o vídeo, não temos esse tipo de indicador de progresso
- exemplos: https://www.youtube.com/watch?v=DQ6WM3LBeDY seg 0 (trecho 5c355a42.mp4)
- ids: 5c355a42

### 19. [jeito_de_falar] Uso de expressões coloquiais e bem-humoradas ('Minha nossa senhora da rosquinha recheada')
- visto em 1 vídeo(s) · nota máx. 7 · modelos: gemini
- como aplicar: Inserir 'exclamações de personagem' ou gírias específicas que fujam do padrão técnico, humanizando o narrador.
- por que é novo: Nosso tom é mais direto. O uso de frases criativas e engraçadas cria uma conexão mais forte e autêntica com o público.
- exemplos: https://www.youtube.com/watch?v=DQ6WM3LBeDY seg 31.9 (trecho 0ff17673.mp3)
- ids: 0ff17673

### 20. [piada] Quebra de expectativa com interjeição ('hihihi, levei vantagem!')
- visto em 1 vídeo(s) · nota máx. 7 · modelos: gemini
- como aplicar: Adicionar comentários curtos em primeira pessoa que zombam da situação descrita, como se o narrador estivesse assistindo ao evento.
- por que é novo: O narrador assume uma persona sarcástica que comenta o erro da empresa, tornando o conteúdo educativo em entretenimento.
- exemplos: https://www.youtube.com/watch?v=DQ6WM3LBeDY seg 10.6 (trecho 64f0f7ac.mp3)
- ids: 64f0f7ac

### 21. [visual] Legendas minimalistas: uma palavra por cena (cidade, garoto, eliminado, soldados, segurou, correr, pro, apertaram, virou, mas)
- visto em 1 vídeo(s) · nota máx. 7 · modelos: claude-sonnet
- como aplicar: Em vídeos de ação/tensão, usar legenda de palavra única como marcador de beat narrativo ao invés de frase explicativa. Mantém ritmo rápido e força atenção visual
- por que é novo: Nossas legendas costumam ter frases completas ou palavras com destaque colorido. Aqui é só substantivo/verbo isolado em branco, deixando a imagem contar
- exemplos: https://www.youtube.com/watch?v=-eob8rfFRAk seg 6.4 (trecho 902e1698.mp4)
- ids: 902e1698

### 22. [visual] Paleta de cores dessaturada e sombria para atmosfera de terror
- visto em 1 vídeo(s) · nota máx. 7 · modelos: claude-sonnet
- como aplicar: Criar preset de correção de cor com dessaturação e tons frios/escuros para aplicar em cenas de suspense e terror, especialmente em narrativas mais sérias.
- por que é novo: Uso consistente de tons escuros, azulados e cinzentos para criar mood de terror psicológico. Nossos overlays têm cores vibrantes (electric, fire), não tons sombrios narrativos.
- exemplos: https://www.youtube.com/watch?v=PxPZcsHTgAE seg 1532.7 (trecho 5e73a180.mp4)
- ids: 5e73a180

### 23. [visual] Personagem creepy com design perturbador como antagonista visual
- visto em 1 vídeo(s) · nota máx. 7 · modelos: claude-sonnet
- como aplicar: Criar versão 'horror' do mascote ou personagens antagonistas assustadores para usar em narrativas de terror, como reveal final ou jump scare visual.
- por que é novo: Design de personagem assustador (rosto pálido, sorriso perturbador, olhos grandes) como payoff visual. Nosso mascote tem poses emocionais mas não tem versão genuinamente assustadora/perturbadora.
- exemplos: https://www.youtube.com/watch?v=PxPZcsHTgAE seg 9707.4 (trecho ae7a7955.mp4)
- ids: ae7a7955

### 24. [visual] Uso de elementos gráficos de ambiente (ex: chuva) integrados à animação.
- visto em 1 vídeo(s) · nota máx. 7 · modelos: gemini
- como aplicar: Usar overlays de partículas (chuva, neve, poeira) em cenas de transição ou ambientação.
- por que é novo: Nossas animações são estáticas; adicionar efeitos climáticos dinâmicos aumenta a imersão.
- exemplos: https://www.youtube.com/watch?v=PxPZcsHTgAE seg 7663.7 (trecho 71f82141.mp4)
- ids: 71f82141

### 25. [efeito] Objeto 3D com energia/fogo roxo envolvendo (377s)
- visto em 1 vídeo(s) · nota máx. 7 · modelos: claude-sonnet
- como aplicar: Para momentos de poder mágico, itens importantes sendo revelados, ou objetos místicos. Combinar partículas de fogo roxo com glow intenso
- por que é novo: Temos fx_fire genérico, mas não temos efeito de energia/chamas coloridas (roxo/magenta) envolvendo objeto específico como um selo ou item místico
- exemplos: https://www.youtube.com/watch?v=5uemizbPJtM seg 377 (trecho a86e030f.mp4)
- ids: a86e030f

### 26. [efeito] Aura dourada/amarela envolvendo personagens (494s)
- visto em 1 vídeo(s) · nota máx. 7 · modelos: claude-sonnet
- como aplicar: Para power-ups, transformações, momentos épicos. Overlay de partículas douradas + glow amarelo intenso ao redor do sujeito
- por que é novo: Temos fx_anger, fx_blush, mas não temos aura de poder/energia dourada envolvendo personagem inteiro com partículas
- exemplos: https://www.youtube.com/watch?v=5uemizbPJtM seg 494 (trecho 26af6c71.mp4)
- ids: 26af6c71

### 27. [visual] Bordas desfocadas (vinheta escura) em cenas dramáticas
- visto em 1 vídeo(s) · nota máx. 7 · modelos: claude-sonnet
- como aplicar: Adicionar overlay de vinheta escura (bordas desfocadas) em momentos de tensão, revelação ou cenas emocionais pesadas. Pode ser um preset 'anime_drama' que aplica automaticamente em histórias de suspense/drama
- por que é novo: Vocês têm overlays diversos mas não vi vinheta/borda escurecida sendo usada sistematicamente para criar tensão visual. Aqui está presente em praticamente todos os quadros, criando um efeito cinematográfico de 'anime dramático'
- exemplos: https://www.youtube.com/watch?v=PsNqKB seg 115.3 (trecho 40a28bc2.mp4)
- ids: 40a28bc2

### 28. [visual] Padrões gráficos repetidos como papel de parede (hexágonos vermelhos com texto)
- visto em 1 vídeo(s) · nota máx. 7 · modelos: claude-sonnet
- como aplicar: Criar backgrounds com padrões temáticos repetidos para dar identidade visual forte em segmentos específicos. Útil para enfatizar marca/canal ou criar atmosfera específica.
- por que é novo: Background preenchido com pattern repetitivo estilizado (hexágonos com texto japonês). Nossos fundos são mais sólidos ou com overlays pontuais.
- exemplos: https://www.youtube.com/watch?v=n29SjmSm8k4 seg 413.5 (trecho 20f3e515.mp4)
- ids: 20f3e515

### 29. [visual] Uso de elementos gráficos de sinalização (placas de aviso)
- visto em 1 vídeo(s) · nota máx. 7 · modelos: gemini
- como aplicar: Criar overlays de placas de aviso ou sinalização industrial para destacar pontos importantes ou avisos no vídeo.
- por que é novo: Cria um ambiente visualmente rico e temático, funcionando como um 'cenário' para o texto.
- exemplos: https://www.youtube.com/watch?v=n29SjmSm8k4 seg 413.5 (trecho 166c3038.mp4)
- ids: 166c3038

### 30. [visual] Blur desfocado nas bordas simulando folhagem em primeiro plano
- visto em 1 vídeo(s) · nota máx. 7 · modelos: claude-sonnet
- como aplicar: Adicionar overlay de blur verde/orgânico nas bordas em cenas de exploração ou revelação para criar profundidade cinematográfica
- por que é novo: Não temos esse efeito de profundidade de campo com blur orgânico nas bordas para simular perspectiva através de vegetação/objetos
- exemplos: https://www.youtube.com/watch?v=Tp2S7yqX9uU seg 188.4 (trecho c8de7901.mp4)
- ids: c8de7901

### 31. [visual] Efeito de glitch/aberração cromática em transições
- visto em 1 vídeo(s) · nota máx. 7 · modelos: gemini
- como aplicar: Aplicar o efeito de glitch em momentos de 'perigo' ou 'falha' na narrativa do vídeo, focando em objetos específicos da cena.
- por que é novo: Embora tenhamos 'glitch', o uso aqui é aplicado de forma sutil em elementos específicos da cena para simular falha de sinal, não apenas como transição de corte.
- exemplos: https://www.youtube.com/watch?v=FvSo6xIUrW8 seg 6020.7 (trecho 5869b455.mp4)
- ids: 5869b455

### 32. [visual] Mistura de cenas de anime clássico (Inuyasha) com filtros/tratamento nostálgico
- visto em 1 vídeo(s) · nota máx. 7 · modelos: claude-sonnet
- como aplicar: Incorporar clipes de animes clássicos/nostálgicos dos anos 90-2000 para narrativas que explorem temas retrô ou comparações. Manter estética original para efeito nostálgico
- por que é novo: Usam footage de anime antigo com aparência preservada (grão, cores vintage). Não é AI-generated nem editado pesadamente
- exemplos: https://www.youtube.com/watch?v=-QscVCm77-E seg 182.8 (trecho 2b3dac4d.mp4)
- ids: 2b3dac4d

### 33. [efeito] Filtro de dessaturação seletiva (Preto e Branco) para flashbacks ou contexto histórico
- visto em 1 vídeo(s) · nota máx. 7 · modelos: gemini
- como aplicar: Aplicar filtro P&B em cenas de flashback (como no segundo 182.8 e 2741.7) para criar contraste narrativo.
- por que é novo: Diferencia visualmente o que é narração de fatos passados vs. a cena atual do vídeo sem precisar de avisos em texto.
- exemplos: https://www.youtube.com/watch?v=-QscVCm77-E seg 182.8 (trecho ff2af51f.mp4)
- ids: ff2af51f

### 34. [visual] Legendas em coreano com formatação bold amarela/vermelha integradas à cena
- visto em 1 vídeo(s) · nota máx. 7 · modelos: claude-sonnet
- como aplicar: Adicionar variações de legendas bold em amarelo (#FFD700) e vermelho (#FF0000) para momentos de tensão/drama. Posicionar estrategicamente na tela como elemento de composição, não só na parte inferior
- por que é novo: Vocês têm legendas em português, mas esse estilo de legenda colorida em bold (amarelo e vermelho intenso) com posicionamento integrado à composição visual não está na lista de recursos
- exemplos: https://www.youtube.com/watch?v=A seg 419.5 (trecho f057c2b1.mp4)
- ids: f057c2b1

### 35. [efeito] Filtro de hachura/desenho (sketch) em momentos de tensão
- visto em 1 vídeo(s) · nota máx. 7 · modelos: gemini
- como aplicar: Aplicar um overlay de textura de hachura (sketch) com opacidade reduzida em cenas de impacto ou revelação dramática.
- por que é novo: O vídeo aplica uma textura de linhas cruzadas sobre a imagem para enfatizar a seriedade ou vilania do personagem, algo que não usamos.
- exemplos: https://www.youtube.com/watch?v=A seg 587.3 (trecho 51ba4f54.mp4)
- ids: 51ba4f54

### 36. [jeito_de_falar] Uso de 'meu amor' como interjeição no meio da narração
- visto em 1 vídeo(s) · nota máx. 7 · modelos: claude-sonnet
- como aplicar: Inserir 'meu amor', 'meu bem', 'meu anjo' em momentos de contraste ou ironia na narração, especialmente quando contando algo surpreendente ou absurdo
- por que é novo: Não temos esse tipo de tratamento carinhoso/irônico inserido naturalmente na narração. É diferente de gírias - é um jeito mais pessoal e próximo de falar
- exemplos: https://www.youtube.com/watch?v=hWvBvihSBBI seg 13.0 (trecho 45ba1f30.mp3)
- ids: 45ba1f30

### 37. [som] Uso de trilha sonora que muda conforme o tom da história
- visto em 1 vídeo(s) · nota máx. 7 · modelos: gemini
- como aplicar: Sincronizar a trilha sonora com as viradas do roteiro, usando cortes secos na música para enfatizar momentos de impacto.
- por que é novo: A trilha acompanha a mudança de humor (do engraçado ao emocionante), reforçando a mensagem de cada cena.
- exemplos: https://www.youtube.com/watch?v=hWvBvihSBBI seg 1.9 (trecho fb5c7241.mp3)
- ids: fb5c7241

### 38. [som] Inserção de áudios de memes clássicos brasileiros (Poeira, Poeira)
- visto em 1 vídeo(s) · nota máx. 7 · modelos: gemini
- como aplicar: Identificar momentos de clímax ou ironia no roteiro e inserir trechos curtos (1-2 segundos) de músicas ou memes brasileiros icônicos para pontuar a piada.
- por que é novo: O vídeo insere um áudio de música popular brasileira (Ivete Sangalo) como efeito sonoro cômico no meio da narração, algo que não fazemos.
- exemplos: https://www.youtube.com/watch?v=ZPe6hDe seg 37.9 (trecho 175ea6b1.mp3)
- ids: 175ea6b1

### 39. [outro] Narrativa totalmente visual sem narração, construída apenas com cortes rápidos e legendas de palavra única
- visto em 1 vídeo(s) · nota máx. 7 · modelos: claude-sonnet
- como aplicar: Criar compilações de momentos de anime sem narração, usando legendas de palavra única para pontuar emoções, reações ou comparações. Funciona para formato 'wait for it' ou 'spot the difference'
- por que é novo: Nossos vídeos dependem muito de narração. Este formato conta história inteira (comparação/piada) só com imagens e palavras-chave estratégicas
- exemplos: https://www.youtube.com/watch?v=3RQesG8rf seg 0 (trecho 96b1305f.mp4)
- ids: 96b1305f

### 40. [visual] Cor amarela/verde limão vibrante no texto em tela
- visto em 1 vídeo(s) · nota máx. 7 · modelos: claude-sonnet
- como aplicar: Testar essa cor #DFFF00 ou similar nas palavras-chave das legendas em vídeos outdoor/pesca/aventura pra criar contraste máximo com céu/água
- por que é novo: Usamos legendas mas não essa paleta amarelo-limão neon que contrasta forte com fundo natural/azul. É diferente do nosso padrão de cores elétricas (00d1ff, 22c55e, etc).
- exemplos: https://www.youtube.com/watch?v=5xMXse-MLnQ seg 2.0 (trecho 96e2096c.mp4)
- ids: 96e2096c

(+ 354 grupo(s) mais fracos: vistos em 1 vídeo só; ficam no acervo.jsonl)
