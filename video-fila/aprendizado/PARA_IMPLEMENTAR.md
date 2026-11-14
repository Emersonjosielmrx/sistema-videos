# Aprendizado com os parceiros — PARA IMPLEMENTAR (refeito a cada rodada; não editar à mão)

Atualizado 14/11/2026 10:26. Gerado por D:\video-fila\aprendizado.py.

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

## A. Aprovados (pela dona ou sozinho: os melhores de cada dia, nota >= 7) (3)

### 1. [visual] Banner de impacto em faixa amarela full-width cobrindo o centro do quadro
- visto em 1 vídeo(s) · nota máx. 7 · modelos: claude-sonnet
- como aplicar: Inserir uma tarja horizontal amarela de ponta a ponta (com tipografia preta pesada) nos primeiros 2-3 segundos do Shorts para destacar a frase mais chocante da premissa.
- por que é novo: Nosso layout usa caixas menores ou legendas pontuais; aqui há uma faixa sólida amarela de ponta a ponta que entra nos primeiros segundos com texto em caixa alta e fonte pesada ('AGORA QUER SER O LÍDER.') para reter atenção imediata no gancho.
- exemplos: https://www.youtube.com/watch?v=GxkhmEX5wL0 seg 1.3 (trecho 64bf6d99.mp4)
- ids: 64bf6d99

### 2. [visual] Enquadramento vertical com bordas/letterbox superior e inferior escuras destacando o mangá centralizado.
- visto em 1 vídeo(s) · nota máx. 8 · modelos: gemini
- como aplicar: Aplicar barras pretas estilizadas ou desfoque de fundo (blur background) nas extremidades superior e inferior do painel central do mangá para focar o olhar.
- por que é novo: Cria um aspecto cinematográfico (letterbox) em vídeos verticais (tipo 9:16), separando claramente a área do conteúdo da área de legendas e tarjas.
- exemplos: https://www.youtube.com/watch?v=GxkhmEX5wL0 seg 1.3 (trecho 724cdc5a.mp4)
- ids: 724cdc5a

### 3. [efeito] Efeito de glitch/fita com fatiamento horizontal dessincronizado revelando camadas
- visto em 1 vídeo(s) · nota máx. 8 · modelos: claude-sonnet
- como aplicar: Aplicar displacement map horizontal ou fatiamento em blocos com leve offset quando o roteiro falar de ilusão, fantasmas ou realidade distorcida.
- por que é novo: Nosso banco de cortes_fx tem cortes rápidos, mas não temos transição de glitch slice/tear horizontal revelando rostos divididos.
- exemplos: https://www.youtube.com/watch?v=xnDpE5LIBh0 seg 1.7 (trecho 7e900bc0.mp4)
- ids: 7e900bc0

## B. Candidatos (sem resposta em 24 h): 646 grupo(s), os 40 mais fortes

### 1. [visual] Demonstração prática em close-up das mãos cortando e preparando a isca natural na tábua de corte
- visto em 1 vídeo(s) · nota máx. 9 · modelos: gemini
- como aplicar: Começar nossos tutoriais e vídeos de dicas com um shot POV em close-up das mãos manipulando o objeto/isca de forma satisfatória nos primeiros 3 segundos.
- por que é novo: Inicia o vídeo diretamente com a ação manual detalhada (POV do pescador preparando o coquinho/fruta), gerando curiosidade imediata antes de mostrar o peixe.
- exemplos: https://www.youtube.com/watch?v=fpecvHeh06g seg 2.5 (trecho a8ba5a0a.mp4)
- ids: a8ba5a0a

### 2. [visual] Perspectiva submarina macro hiper-realista com animais da fauna silvestre brasileira nativa (peixes de cardume, dourado, capivara, cervo-do-pantanal) interagindo próximo a lixo/poluição humana submersa.
- visto em 1 vídeo(s) · nota máx. 9 · modelos: gemini
- como aplicar: Utilizar prompts de IA ou banco de imagens focados em macrofotografia subaquática de rios brasileiros de água doce limpa contrastando com elementos poluentes detalhados (chumbadas de pesca), mantendo alta imersão.
- por que é novo: Uso consistente de filmagens hiper-realistas subaquáticas de ecossistemas fluviais brasileiros (Pantanal/Rios de água cristalina) mostrando animais reais (dourado, piava, capivara) convivendo diretamente com resíduos metálicos no fundo.
- exemplos: https://www.youtube.com/watch?v=YxABYyjo3IU seg 0.0 (trecho af755ec0.mp4)
- ids: af755ec0

### 3. [visual] Transição de tela gravada (gravação de tela de resultados de busca do Google) com a apresentadora sobreposta no canto inferior direito.
- visto em 1 vídeo(s) · nota máx. 9 · modelos: gemini
- como aplicar: Inserir screen recordings reais de portais oficiais (gov.br) com o avatar/apresentador em Picture-in-Picture (PIP) comentando e apontando para os pontos de atenção.
- por que é novo: Mostra o site real do governo/busca de forma fluida com recorte chroma/PIP da pessoa guiando com o dedo/apontando para os resultados patrocinados.
- exemplos: https://www.youtube.com/watch?v=tEN7LosaLf4 seg 18.4 (trecho c1a13d2f.mp4)
- ids: c1a13d2f

### 4. [visual] Mnemônico visual colorido com acrônimo 'Hi.Po / Di.Vi.Di.Re' segurado por mascote ilustrada para memorização de poderes administrativos.
- visto em 1 vídeo(s) · nota máx. 9 · modelos: gemini
- como aplicar: Criar arte gráfica vetorial dividindo conceitos complexos em sílabas coloridas (ex: mnemônicos de direito ou biologia) para fixar na introdução de vídeos de questões.
- por que é novo: Apresenta um método mnemônico completo dividido por cores e sílabas direto em um cartaz físico segurado por uma personagem animada antes de resolver cada item da questão.
- exemplos: https://www.youtube.com/watch?v=Asg5Q6iN-AA seg 3 (trecho bd1f7b9b.mp4)
- ids: bd1f7b9b

### 5. [visual] Inserção de fórmulas químicas/elementos técnicos flutuantes
- visto em 1 vídeo(s) · nota máx. 8 · modelos: gemini
- como aplicar: Quando o roteiro citar algum conceito científico ou técnico, inserir uma sobreposição (overlay) estática ou levemente animada de uma fórmula ou esquema técnico ao lado do personagem.
- por que é novo: Adiciona uma camada de 'autoridade' e curiosidade visual que quebra a monotonia da narração.
- exemplos: https://www.youtube.com/watch?v=fSx50o67HB4 seg 3062.9 (trecho 28fc46f8.mp4)
- ids: 28fc46f8

### 6. [visual] Meme em sticker recortado (Willem Dafoe olhando pra cima apavorado) sobreposto diretamente no cenário
- visto em 1 vídeo(s) · nota máx. 8 · modelos: claude-sonnet
- como aplicar: Adicionar o recorte PNG do Willem Dafoe olhando pra cima na pasta memes_png e disparar como sticker sobreposto na tela quando o narrador descrever uma ameaça colossal ou piora repentina da situação.
- por que é novo: Embora tenhamos memes_img, usar o recorte transparente do Dafoe olhando pro céu sobreposto diretamente sobre a cena dramática pontua o choque/medo do personagem sem cortar o fluxo da animação com tela cheia.
- exemplos: https://www.youtube.com/watch?v=q3ixE2vr8aA seg 27.0 (trecho 8f34797b.mp4)
- ids: 8f34797b

### 7. [efeito] Efeito de 'tremor' (shake) nos personagens
- visto em 1 vídeo(s) · nota máx. 8 · modelos: gemini
- como aplicar: Aplicar um leve efeito de vibração (shake) em camadas de personagens quando estiverem em situações de perigo ou susto.
- por que é novo: Dá uma sensação de medo ou tensão que nossos efeitos estáticos não transmitem.
- exemplos: https://www.youtube.com/watch?v=5-vQopGwQ8Y seg 1028.0 (trecho 888f8cff.mp4)
- ids: 888f8cff

### 8. [efeito] Efeito de impacto com linhas de velocidade e brilho intenso
- visto em 1 vídeo(s) · nota máx. 8 · modelos: gemini
- como aplicar: Usar overlays de impacto com linhas radiais e brilho roxo/neon em momentos de ataque ou poder.
- por que é novo: Nossos impactos são mais simples; este efeito de 'energia' é mais dinâmico para cenas de ação.
- exemplos: https://www.youtube.com/watch?v=5-vQopGwQ8Y seg 1850.5 (trecho 1b9593b5.mp4)
- ids: 1b9593b5

### 9. [visual] Gradiente de cor dominante por personagem/mood
- visto em 1 vídeo(s) · nota máx. 8 · modelos: claude-sonnet
- como aplicar: Aplicar gradiente overlay consistente em blocos de cena para criar identidade visual por personagem ou momento emocional, não só correção de cor
- por que é novo: Cada corte tem gradiente overlay forte (azul-verde, verde natural, amarelo, vermelho-laranja, rosa) sincronizado com personagem/emoção, não apenas como filtro mas como identidade visual do momento
- exemplos: https://www.youtube.com/watch?v=r6wFByKK0Q4 seg 191.3 (trecho 676c7c06.mp4)
- ids: 676c7c06

### 10. [visual] Uso de cortinas de teatro como moldura (frame) inicial
- visto em 1 vídeo(s) · nota máx. 8 · modelos: gemini
- como aplicar: Adicionar uma sobreposição (overlay) de cortinas vermelhas abrindo nos primeiros 1-2 segundos de vídeos que contam histórias ou curiosidades.
- por que é novo: Cria um efeito de 'abertura de espetáculo' que dá um ar mais premium e narrativo ao início do vídeo.
- exemplos: https://www.youtube.com/watch?v=r6wFByKK0Q4 seg 191.3 (trecho 53fbef0c.mp4)
- ids: 53fbef0c

### 11. [visual] Inversão de cor/flash dramático de choque no rosto do protagonista humano ao perceber que virou formiga
- visto em 1 vídeo(s) · nota máx. 8 · modelos: gemini
- como aplicar: Aplicar filtro de tom avermelhado forte com vinheta escura e zoom rápido no momento de surpresa/desespero do personagem.
- por que é novo: Usamos reações genéricas, mas o close com distorção e tom avermelhado/magenta de choque absurdo intensifica a comédia da situação.
- exemplos: https://www.youtube.com/watch?v=nV2aNVwUL-A seg 159.1 (trecho e896297c.mp4)
- ids: e896297c

### 12. [efeito] Linhas de tremor (Shake Lines) em objetos estáticos
- visto em 1 vídeo(s) · nota máx. 8 · modelos: gemini
- como aplicar: Adicionar overlays de 'Electric/Shock lines' ou usar o pincel de animação quadro a quadro para criar contornos vibrantes em pontos específicos de ação.
- por que é novo: O vídeo adiciona linhas brancas trêmulas desenhadas ao redor do punho para simular força/tensão, transformando uma imagem estática em algo dinâmico sem mover o quadro todo.
- exemplos: https://www.youtube.com/watch?v=5FDtWi2JmuE seg 2083.5
- ids: 9f2c1527

### 13. [visual] Uso de 'freeze frame' com filtro de contorno/desenho
- visto em 1 vídeo(s) · nota máx. 8 · modelos: gemini
- como aplicar: Ao narrar momentos de choque ou estranheza, pausar o vídeo e aplicar um filtro de 'posterize' ou 'sketch' com bordas pretas fortes para enfatizar a expressão do personagem.
- por que é novo: O vídeo congela a imagem e aplica um filtro que parece um desenho ou pintura, destacando a ação bizarra do personagem.
- exemplos: https://www.youtube.com/watch?v=yDSdS0yAatM seg 20.2 (trecho 2d868b48.mp4)
- ids: 2d868b48

### 14. [jeito_de_falar] Estrutura narrativa 'in media res' com cliffhanger causal: revela o crime/sabotagem no presente e faz flashback para a motivação
- visto em 1 vídeo(s) · nota máx. 8 · modelos: claude-sonnet
- como aplicar: Adaptar o gerador de roteiros para Shorts de suspense/drama: iniciar com a ação de vingança/clímax nos primeiros 10s e em seguida rebobinar ('Tudo começou quando...') para prender retenção imediata.
- por que é novo: Geralmente nossas narrações seguem ordem cronológica ou apresentação direta de fatos. Aqui o protagonista abre confessando um ato extremo em andamento ('Eu solto de propósito o trinco...') e no meio transiciona para 'Tudo começa minutos antes quando...'.
- exemplos: https://www.youtube.com/watch?v=IlGnmNGHHII seg 0.0 (trecho a6e4234e.mp3)
- ids: a6e4234e

### 15. [visual] Cortes rápidos e fechados (close-ups) em detalhes da arte
- visto em 1 vídeo(s) · nota máx. 8 · modelos: gemini
- como aplicar: Programar cortes que acompanhem a narração, dando zoom no detalhe que está sendo descrito (ex: o olho do personagem ao falar de poder), em vez de apenas mostrar a cena estática.
- por que é novo: O vídeo alterna entre planos gerais e zooms extremos em olhos ou mãos, aumentando a intensidade dramática da cena.
- exemplos: https://www.youtube.com/watch?v=zuDwpO6AokY seg 15.0 (trecho 2b08f9fc.mp4)
- ids: 2b08f9fc

### 16. [visual] Censura em pixel art (mosaico) para itens cômicos ou 'proibidos'
- visto em 1 vídeo(s) · nota máx. 8 · modelos: gemini
- como aplicar: Aplicar o efeito 'Mosaic' ou 'Pixelate' apenas sobre o objeto mencionado na fala absurda para gerar curiosidade/humor.
- por que é novo: Nós não usamos censura visual estilizada para reforçar piadas (como o chapéu sendo comido).
- exemplos: https://www.youtube.com/watch?v=39kzEATJ044 seg 3.8 (trecho 15b68abd.mp4)
- ids: 15b68abd

### 17. [visual] Uso de balão de pensamento (thought bubble) com imagem interna
- visto em 1 vídeo(s) · nota máx. 8 · modelos: gemini
- como aplicar: Criar um overlay de balão de pensamento que permita inserir uma imagem ou vídeo pequeno dentro dele para representar o que o personagem está pensando.
- por que é novo: Nós usamos apenas legendas ou memes estáticos; o balão de pensamento integra a narrativa visual de forma mais orgânica e cômica.
- exemplos: https://www.youtube.com/watch?v=QW0lnOD seg 8770.9 (trecho a7f9fc71.mp4)
- ids: a7f9fc71

### 18. [visual] Menu interativo estilizado do jogo (FiveM/GTA) mostrando a seleção de origem ('Onde nos encontrou?') com opções flutuantes customizadas
- visto em 1 vídeo(s) · nota máx. 8 · modelos: gemini
- como aplicar: Simular telas de carregamento, menus de contexto ou caixas de diálogo estilizadas do jogo como elemento overlay nos vídeos.
- por que é novo: Foca em interações de UI/UX personalizadas de servidores de RP que geram identificação imediata do nicho.
- exemplos: https://www.youtube.com/watch?v=unSSHjDlge8 seg 9.3 (trecho f7a93d1e.mp4)
- ids: f7a93d1e

### 19. [visual] Mini-mapa do jogo com marcação de rota em roxo/magenta com ícone personalizado destacando o destino exato
- visto em 1 vídeo(s) · nota máx. 8 · modelos: gemini
- como aplicar: Incluir clipes rápidos do GPS do jogo traçando rotas para locais específicos mencionados no roteiro.
- por que é novo: Uso dinâmico do mapa do GTA/FiveM como storytelling visual para mostrar localização de forma imersiva.
- exemplos: https://www.youtube.com/watch?v=unSSHjDlge8 seg 13.0 (trecho 5a53abff.mp4)
- ids: 5a53abff

### 20. [gíria] Uso de eufemismos da internet como 'desviver' e 'suco de tomate' para sangue/morte
- visto em 1 vídeo(s) · nota máx. 8 · modelos: claude-sonnet
- como aplicar: Padronizar nos roteiros de histórias fictícias o uso proposital de 'desviver' e 'suco de tomate' (sangue) para retenção da linguagem algorítmica e tom cômico/jovem.
- por que é novo: Nosso vocabulário/roteiros muitas vezes evitam o assunto ou usam linguagem direta, arriscando filtro de conteúdo do TikTok/Shorts.
- exemplos: https://www.youtube.com/watch?v=B-2QuiaoBcE seg 100.8 (trecho ce6e8d81.mp3)
- ids: ce6e8d81

### 21. [visual] Simulação de interface de tablet/sistema
- visto em 1 vídeo(s) · nota máx. 8 · modelos: gemini
- como aplicar: Criar um frame de sobreposição que simule uma tela de dispositivo (tablet/celular) com bordas tecnológicas para mostrar o que o personagem está vendo.
- por que é novo: O vídeo mostra a mão do personagem interagindo com um tablet que exibe o mundo pixelado, criando uma imersão de 'POV' (ponto de vista).
- exemplos: https://www.youtube.com/watch?v=B-2QuiaoBcE seg 87.4 (trecho 95f5b551.mp4)
- ids: 95f5b551

### 22. [visual] Escrita secreta na perna/coxa
- visto em 1 vídeo(s) · nota máx. 8 · modelos: gemini
- como aplicar: Simular escrita à caneta na pele com efeito de zoom em dramatizações de suspense.
- por que é novo: Uso de partes do corpo como suporte de mensagem oculta de socorro em close-up.
- exemplos: https://www.youtube.com/watch?v=LiMdjEzZxpQ seg 4.9 (trecho 118eadba.mp4)
- ids: 118eadba

### 23. [jeito_de_falar] Uso de analogias cotidianas e informais
- visto em 1 vídeo(s) · nota máx. 8 · modelos: gemini
- como aplicar: Incorporar analogias do dia a dia para explicar comportamentos complexos de animais ou produtos, fugindo da linguagem puramente descritiva.
- por que é novo: O roteiro usa comparações como 'vigia de baú de brinquedos' e 'xerife', que tornam o conteúdo técnico mais acessível e engraçado.
- exemplos: https://www.youtube.com/watch?v=gFg-PP seg 27.9 (trecho 024b0bd9.mp3)
- ids: 024b0bd9

### 24. [visual] Card retangular escuro semi-transparente com borda/acento amarelo lateral agrupando especificações técnicas (ex: '1 máquina ASIC • 200 TH/s • 3.500 W')
- visto em 1 vídeo(s) · nota máx. 8 · modelos: claude-sonnet
- como aplicar: Criar um componente de overlay estilo 'infocard' para exibir dados técnicos, atributos ou métricas com linha vertical amarela em vídeos informativos ou comparativos
- por que é novo: Nosso acervo tem overlays pontuais e big numbers, mas não possui esse formato de mini-ficha técnica/hud retangular com marcador de borda vertical amarelo para resumir stats ou dados analíticos
- exemplos: https://www.youtube.com/watch?v=F1Vr2Uq7oeA seg 4.0 (trecho a8baabde.mp4)
- ids: a8baabde

### 25. [piada] Dublagem paródia inserindo bordões clássicos do Chaves ('Cale-se, cale-se...', 'Isso, isso, isso!', 'Não se misture com essa gentalha!') em dorama dramático chinês
- visto em 1 vídeo(s) · nota máx. 8 · modelos: claude-sonnet
- como aplicar: Usar roteiros/dublagens cômicas que remixam falas icônicas da TV brasileira (Chaves, novelas da Globo) sobre trechos de conflito dramático de doramas curtos para gerar contraste cômico e retenção.
- por que é novo: Não temos esse formato de paródia de voz com referências e bordões de humor nostálgico brasileiro sobrepostas a novelas asiáticas sérias.
- exemplos: https://www.youtube.com/watch?v=kFdlOyUMkxw seg 9.0 (trecho 370d009d.mp3)
- ids: 370d009d

### 26. [jeito_de_falar] Roteiro em 1ª pessoa adotando a persona egocêntrica/narcisista ('minha gloriosa propriedade', 'mente brilhante', 'dentadura majestosa', 'seus desocupados')
- visto em 1 vídeo(s) · nota máx. 8 · modelos: claude-sonnet
- como aplicar: Inserir adjetivos grandiosos satíricos ('meu intelecto incomparável', 'minha nobre presença') e chamar o espectador de apelidos provocativos amigáveis nos roteiros de recap/POV
- por que é novo: Geralmente usamos narração em 3ª pessoa ou primeira pessoa neutra/séria; o vídeo usa um tom cômico arrogante/teatral que xinga o público ('seus desocupados') e romantiza situações trágicas para reter a atenção
- exemplos: https://www.youtube.com/watch?v=qzI seg 0.0 (trecho b7a1d6cb.mp3)
- ids: b7a1d6cb

### 27. [visual] Legenda centralizada com quebra de linha dinâmica que acompanha o ritmo da fala.
- visto em 1 vídeo(s) · nota máx. 8 · modelos: gemini
- como aplicar: Configurar o editor de legendas para priorizar frases curtas centralizadas, alternando o peso visual entre as linhas para destacar o tom dramático da narrativa.
- por que é novo: Nossas legendas atuais costumam ser estáticas ou seguir padrões de leitura linear; o uso de quebras de linha que enfatizam palavras-chave no centro da tela aumenta a retenção.
- exemplos: https://www.youtube.com/watch?v=qzI seg 3.4 (trecho 09f58ab0.mp4)
- ids: 09f58ab0

### 28. [visual] Uso de acessórios físicos na personagem (tiara de sapo)
- visto em 1 vídeo(s) · nota máx. 8 · modelos: gemini
- como aplicar: Incluir acessórios simples e temáticos no figurino do apresentador/mascote que combinem com o tema da história (ex: tiaras, óculos, adereços de cabeça).
- por que é novo: Adiciona uma camada de personalidade e humor visual que não temos, criando uma identificação imediata com o personagem sem depender só de edição.
- exemplos: https://www.youtube.com/watch?v=zmN5gHkCaG8 seg 111.2 (trecho c4276cd2.mp4)
- ids: c4276cd2

### 29. [visual] Legenda dinâmica com troca de cor por palavra
- visto em 1 vídeo(s) · nota máx. 8 · modelos: gemini
- como aplicar: Implementar um estilo de legenda onde a palavra falada no momento ganha uma cor de destaque (ex: amarelo ou ciano) enquanto as outras permanecem brancas.
- por que é novo: Nossas legendas costumam ser estáticas ou simples; o parceiro usa cores vibrantes que mudam conforme a ênfase da fala, mantendo o foco visual.
- exemplos: https://www.youtube.com/watch?v=UYwA-hJjMnw seg 1.4 (trecho 1ff5c0fd.mp4)
- ids: 1ff5c0fd

### 30. [visual] Lista vertical de locais com ícones
- visto em 1 vídeo(s) · nota máx. 8 · modelos: gemini
- como aplicar: Criar uma lista animada (overlay) que surge lateralmente para listar comandos ou locais importantes em vez de falar tudo.
- por que é novo: Apresenta informações densas de forma organizada e visualmente limpa, facilitando a leitura rápida.
- exemplos: https://www.youtube.com/watch?v=fQsSb-qUZHU seg 34.1 (trecho edcf7e13.mp4)
- ids: edcf7e13

### 31. [visual] Uso de partículas de energia/faíscas (overlay) para enfatizar impacto ou tensão
- visto em 1 vídeo(s) · nota máx. 8 · modelos: gemini
- como aplicar: Adicionar overlays de faíscas ou partículas em momentos de impacto ou transições rápidas, sincronizando com um sfx de impacto.
- por que é novo: Embora tenhamos overlays, não usamos partículas dinâmicas que 'nascem' de um ponto de impacto específico para dar peso visual a uma cena de ação.
- exemplos: https://www.youtube.com/watch?v=MlgXYIqjzno seg 1424.5 (trecho c25b9d2d.mp4)
- ids: c25b9d2d

### 32. [jeito_de_falar] Uso de regionalismos informais ('uai', 'dureza danada', 'cês')
- visto em 1 vídeo(s) · nota máx. 8 · modelos: gemini
- como aplicar: Incorporar expressões regionais leves no roteiro para humanizar a narração, mantendo a clareza.
- por que é novo: Nossa comunicação atual é muito neutra/padrão; o uso de gírias regionais cria proximidade e autenticidade.
- exemplos: https://www.youtube.com/watch?v=C5hzxEfLlf4 seg 0 (trecho ee8bf678.mp3)
- ids: ee8bf678

### 33. [som] Efeitos sonoros onomatopaicos (SNIFF, PLUM)
- visto em 1 vídeo(s) · nota máx. 8 · modelos: gemini
- como aplicar: Adicionar sfx de foley curtos e pontuais que reforcem ações físicas dos personagens, sincronizados exatamente com o movimento na tela.
- por que é novo: O vídeo usa sons que acompanham ações específicas dos personagens (como o 'sniff' ao cheirar energia), criando uma camada de imersão cômica.
- exemplos: https://www.youtube.com/watch?v=WAv-3WVeAu0 seg 3.7
- ids: 4fda937a

### 34. [outro] Narrativa com tom de 'contação de história' (storytelling)
- visto em 1 vídeo(s) · nota máx. 8 · modelos: gemini
- como aplicar: Começar nossos vídeos com uma frase de ambientação que convide o espectador para dentro da história, criando um clima de 'fofoca' ou 'conto'.
- por que é novo: O vídeo não apenas descreve a cena, ele cria um ambiente ('Senta aqui perto do fogo'), humanizando a narração.
- exemplos: https://www.youtube.com/watch?v=2Lq7KkHt-6Q seg 3.9 (trecho 043159cd.mp4)
- ids: 043159cd

### 35. [piada] Analogia cômica do cotidiano: 'É tipo almoço de domingo na casa da sogra, só que...'
- visto em 1 vídeo(s) · nota máx. 8 · modelos: claude-sonnet
- como aplicar: Orientar os roteiristas a incluírem punchlines usando hipérboles de situações familiares brasileiras para quebrar o tom expositivo do resumo.
- por que é novo: Compara a premissa fantástica/absurda do manhwa (vilão conhecendo heróis) com uma situação comum brasileira (tensão na casa da sogra), gerando identificação imediata.
- exemplos: https://www.youtube.com/watch?v=DXqqnQP3omE seg 48.0 (trecho 2cccc77e.mp3)
- ids: 2cccc77e

### 36. [jeito_de_falar] Narração em 1ª pessoa assumindo o monólogo interno do monstro/personagem bizarro ('Eu fiz mais de oitocentas cirurgias...', 'Arrancaram meus braços...') com deboche ao ouvinte ('seu pançudo')
- visto em 1 vídeo(s) · nota máx. 8 · modelos: claude-sonnet
- como aplicar: Em cortes de monstros, vilões ou transformações bizarras de animes/séries, redigir o roteiro na primeira pessoa do próprio personagem contando sua loucura e insultando o espectador com humor ácido.
- por que é novo: Costumamos narrar fatos em 3ª pessoa ou fazer resumos analíticos/descritivos. Incorporar a 'persona' do vilão/criatura de forma visceral e informal gera identificação e choque imediatos.
- exemplos: https://www.youtube.com/watch?v=Da2OEqetod4 seg 0.0 (trecho f909ea2f.mp3)
- ids: f909ea2f

### 37. [visual] Uso de caligrafia chinesa vertical para identificar personagens
- visto em 1 vídeo(s) · nota máx. 8 · modelos: gemini
- como aplicar: Criar overlays de texto com fontes estilo 'brush' ou caligráficas, posicionadas verticalmente na lateral da tela ao introduzir um novo personagem.
- por que é novo: Identifica personagens com um estilo visual mais sofisticado e dramático do que apenas nomes simples na tela.
- exemplos: https://www.youtube.com/watch?v=OAoFU2VUrMY seg 63.0 (trecho 6b38ae6f.mp4)
- ids: 6b38ae6f

### 38. [efeito] Uso de 'zoom' dramático em momentos de comédia física
- visto em 1 vídeo(s) · nota máx. 8 · modelos: gemini
- como aplicar: Aplicar zooms rápidos (keyframe de escala) em momentos de 'punchline' ou situações bizarras, sincronizado com o efeito sonoro de impacto.
- por que é novo: O vídeo usa zooms rápidos e fechados para enfatizar o absurdo da situação (pés/mãos trocados), o que potencializa o humor visual.
- exemplos: https://www.youtube.com/watch?v=DCAAna2CkV0 seg 11.3 (trecho 649262d8.mp4)
- ids: 649262d8

### 39. [outro] Narrativa baseada em 'causa e efeito' absurdo
- visto em 1 vídeo(s) · nota máx. 8 · modelos: gemini
- como aplicar: Estruturar roteiros onde o clímax da bizarrice acontece primeiro e a explicação (mesmo que absurda) é revelada apenas no final do vídeo.
- por que é novo: O vídeo constrói uma história surrealista que justifica o absurdo inicial apenas no final, mantendo a curiosidade até o último segundo.
- exemplos: https://www.youtube.com/watch?v=DCAAna2CkV0 seg 64.0 (trecho 3587853c.mp4)
- ids: 3587853c

### 40. [visual] Header fixo com perfil simulado de rede social (Twitter/X)
- visto em 1 vídeo(s) · nota máx. 8 · modelos: gemini
- como aplicar: Fixar um elemento gráfico no topo com foto de perfil, nome e @ do canal durante todo o vídeo.
- por que é novo: Cria uma identidade visual constante e autoridade de marca sem poluir o centro da tela, diferente dos nossos overlays genéricos.
- exemplos: https://www.youtube.com/watch?v=l6IqakMpVaQ seg 2.5 (trecho 92c32386.mp4)
- ids: 92c32386

(+ 606 grupo(s) mais fracos: vistos em 1 vídeo só; ficam no acervo.jsonl)
