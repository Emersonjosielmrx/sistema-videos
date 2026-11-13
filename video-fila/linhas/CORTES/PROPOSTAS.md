
## 29/10 18:15 PROPOSTA [CERTEZA] Fixar card de topo/marca d'água abaixo de y=150, manter título visível e usar regras_titulo no gancho visual (gweb/gemini-3.1-pro)
- prova: 3 Shorts com elementos de topo acima de y=150 (sem-obra-6dd484 q01.jpg, sem-obra-b0c0f3 q01.jpg em y≈25-145, sem-obra-990199 q01.jpg em y≈100-140); 2 Shorts com gancho de topo dando spoiler do final ('O DESVIO que fez nascer o Brasil' em sem-obra-6dd484 q01.jpg e 'ELE JÁ DESTRUIU O INIMIGO' em bleach_cap1 q01.jpg) e sumindo em q03.jpg (~3.5s) deixando faixa morta no topo (sem-obra-b0c0f3 q03.jpg e bleach_cap1 q03.jpg).
- onde: Renderizador de layout/overlay de topo (template Remotion / script de montagem de vídeo da linha CORTES) e gerador de texto do gancho superior.
- como testar: Renderizar 2 Shorts de teste e rodar D:\tmp\folha_topo.py em 1.5s e 5.0s verificando que nenhum texto/watermark fica em y < 150, que o gancho não some deixando tarja vazia após 3.5s e que o texto do topo reutiliza o título sem spoiler.

## 29/10 19:27 PROPOSTA [CERTEZA] Confinar sticker de gancho do topo em y>=160 sem sobrepor marca d'água e aplicar regras_titulo nele (gweb/gemini-3.1-pro)
- prova: sem-obra-990199_cap1_20261029 q01 e dr-stone_cap1_20261029 q01 sobrepõem '@animescomia'; the-bald-guy-who-stole-hair_cap1_20261029 q01 fica em y=90-120; bleach_cap1_20261029 q01 exibe 'ELE JÁ DESTRUIU O INIMIGO' (spoiler) e some em q03 (3.76s).
- onde: Gerador/renderizador do gancho de topo (Remotion / script de composição do hook superior e geração da frase de gancho)
- como testar: Gerar folha do topo em 1.5s e 4.5s (D:\tmp\folha_topo.py) nos 4 Shorts e validar que o hook fica entre y=160 e y=320 por >=4s, sem tocar na marca d'água e sem entregar o resultado final.

## 29/10 19:27 PROPOSTA [CERTEZA] Auditar detecção de hardsub/letreiro em bleach e dr-stone e cortar barrigas estáticas >3s no alinhamento (gweb/gemini-3.1-pro)
- prova: bleach_cap1_20261029 (q01-q04, q07, q15, q18) ficou com a legenda original no centro/baixo totalmente sem cobertura sobrepondo a nossa; dr-stone_cap1_20261029 (q01-q07) manteve letreiro da fonte vazando nas bordas; sem-obra-990199 q09, dr-stone q16-q17 (8.4% mov) e the-bald-guy q16-q17 (18.2% mov) seguraram quadros parados/vazios por 3 a 6s.
- onde: Detector de hardsub (amostragem de quadros/OCR para delogo/tarja) e seletor de cortes/cenas do vídeo base
- como testar: Rodar detecção de hardsub em bleach_cap1_20261029 verificando quantos quadros leram texto no log [hardsub] e impor limite máximo de 3.0s por tomada parada sem ação.

## 29/10 20:35 PROPOSTA [CERTEZA] Travar coordenadas verticais entre gancho superior e legenda dinâmica na Cena 1 (gweb/gemini-3.1-pro)
- prova: Em sem-obra-c4fa8c_cap1_20261029 (q01, q02) e sem-obra-30f403_cap1_20261029 (q01 a q03), o título de gancho ('ISSO NÃO DEVERIA SER REAL' / 'ESSE LAGO NÃO DEVERIA EXISTIR') foi renderizado na mesma faixa vertical (y) da legenda dinâmica da narração, tornando ambos ilegíveis.
- onde: Módulo de composição de legendas/gancho (Remotion / gerador de ASS/drawtext em cortes)
- como testar: Renderizar 2 Shorts com gancho ativo na Cena 1 e extrair folha de quadros em 1.0s e 2.5s (q01-q03) verificando que o gancho permanece isolado no topo (y=160..320) e a legenda dinâmica fica fixa no terço inferior (y=1250..1450) sem intersecção de bounding boxes.

## 29/10 20:35 PROPOSTA [CERTEZA] Substituir filtro delogo/pixel-stretch por tarja sólida exata sobre hardsub detectado (gweb/gemini-3.1-pro)
- prova: Em sem-obra-7dbdbc_cap1_20261029 (q06, q16) o filtro de cobertura criou uma faixa central de estiramento vertical (smear) que rasgou as mãos do pesquisador e o carro ao meio; em q08 e em sem-obra-c4fa8c_cap1_20261029 (q01) o borrão ainda deixou vazar texto original.
- onde: Função de aplicação de cobertura de hardsub no pipeline de vídeo (alavanca cobertura_legenda / filtro ffmpeg delogo)
- como testar: Rodar o corte de sem-obra-7dbdbc_cap1_20261029 trocando o filtro delogo por caixa opaca do tamanho exato do bbox medido em >=720p (apenas nos timestamps com texto confirmado) e inspecionar q06, q08 e q16.

## 29/10 21:46 PROPOSTA [CERTEZA] Travar limite vertical inferior da legenda dinâmica em y<=1500 e margem do @canal fora de rostos/topo (gemini-4-argon)
- prova: Em sem-obra-76fab9_cap1_20261029 (q01.jpg) a legenda desce até y=1630 e em sem-obra-bb6977_cap1_20261029 (q02.jpg) atinge y=1640, invadindo a interface inferior (y>1580). A marca d'água (@canal) também colide com título/texto do topo em 8bac11 (q01.jpg) e 76fab9 (q01.jpg) ou cobre a testa do personagem em 5369b9 (q09/q13.jpg) e 76fab9 (q16.jpg).
- onde: Renderizador de legendas ASS/Remotion e posicionamento de overlay/@canal no pipeline de cortes
- como testar: Renderizar sem-obra-76fab9_cap1_20261029 e sem-obra-bb6977_cap1_20261029 e medir o bounding box da legenda em q01/q02 garantindo y_max <= 1500 e @canal sem colisão com a tarja/título do topo.

## 29/10 21:46 PROPOSTA [CERTEZA] Sincronizar troca de tomada com o timestamp da fala e bloquear repetição do mesmo subclip no Short (gemini-4-argon)
- prova: Em sem-obra-5369b9_cap1_20261029 (q11, q13, q14, q15.jpg) o vídeo repete os mesmos takes de Cristiano Ronaldo (q09=q13, q10=q14) e Benzema (q11=q15) enquanto a locução fala de Messi ('o argentino', 'faturou sua oitava', 'levou a Copa'); em sem-obra-8bac11_cap1_20261029 (q05-q07.jpg) e sem-obra-76fab9_cap1_20261029 (q08, q11.jpg) os cortes entram atrasados ou adiantados em relação à frase narrada.
- onde: Alinhamento de cenas/timestamps com o áudio da locução e seletor de subclips do montador de vídeo
- como testar: Rodar o montador em sem-obra-5369b9_cap1_20261029 verificando que nenhum segmento de vídeo (mesmo intervalo de timestamps da fonte) seja reutilizado e que a troca de cena ocorra dentro de <=0.3s do gatilho no áudio.

## 30/10 01:12 PROPOSTA [CERTEZA] Travar Short cujo roteiro/narração contém meta-instrução de prompt (cw/claude-sonnet-5-5)
- prova: sem-obra-54b88d q10 a q18: legenda e áudio dizem 'envie a transcrição para que criar o roteiro completo no estilo do Luiz Carlos Persy, seguindo e garantindo perfeita para o loop'. Nota 2.5.
- onde: geração do roteiro (validação da resposta da IA) e cortes_juri._trava_texto_erro
- como testar: Rodar o roteiro.txt do sem-obra-54b88d na validação: deve ser rejeitado e regenerado. Criar lista de padrões ('envie a', 'transcrição', 'estilo do', 'garantindo', 'prompt') e conferir que 0 dos 49 Shorts do dia dão falso positivo.

## 30/10 01:12 PROPOSTA [CERTEZA] Mover a marca d'água @canal para posição que não cubra rosto e dar contorno (cw/claude-sonnet-5-5)
- prova: sem-obra-54b88d q04 e q13, sem-obra-62e3fc q06: @esportenoturno sobre rosto/boca/cabeça; q02: baixo contraste sobre placa branca. Também @filmenoturno colidindo com texto central em gta-6 q03.
- onde: módulo de render da marca d'água (overlay @canal) no pipeline CORTES
- como testar: Fixar a marca no canto inferior-esquerdo (y entre 1250 e 1500, fora do rosto) com traçado preto >= 3 px; rodar folha de quadros de 10 Shorts de esporte e conferir 0 sobreposições em rosto.

## 30/10 01:12 PROPOSTA [CERTEZA] Título superior e palavra de impacto fora do rosto e dentro da zona segura (cw/claude-sonnet-5-5)
- prova: sem-obra-e91dc2 q01 (título acima de y=150 cobrindo a cabeça) e q12 ('TRÊS' sobre o rosto caído); gta-6 q03 (texto central colide com @filmenoturno).
- onde: componentes Remotion do título/gancho e legenda_impacto (clamp y>=150, evitar bbox de rosto)
- como testar: Renderizar os 3 Shorts citados e medir a caixa do título: y>=150, margem lateral >= 60 px, sem interseção com rosto detectado.

## 30/10 01:12 PROPOSTA [CERTEZA] Quebra de linha da legenda empurrando palavra abaixo de y=1580 (cw/claude-sonnet-5-5)
- prova: sem-obra-e91dc2 q17: 'garotos' caiu para a 2ª linha quase na borda inferior; sem-obra-62e3fc q15-q18: marca de terceiro abaixo de y=1580.
- onde: render da legenda palavra a palavra (limite de largura/linhas e âncora de base)
- como testar: Forçar frase de 4 palavras longas e conferir que a base nunca passa de y=1500; para marca de terceiro, avaliar delogo/tarja do tamanho exato dela.

## 30/10 01:12 PROPOSTA [CERTEZA] Artefato de dissolução com dither duplicando cabeçalho e tela final de canal terceiro (cw/claude-sonnet-5-5)
- prova: gta-6 q09 (cabeçalho duplicado com ruído e 'REAJUSTETE') e q17-q18 (tela preta com 'GRANA NERD / VÍDEO COMPLETO NO CANAL' enquanto a narração segue).
- onde: transição entre cenas no render (xfade/dissolve) e corte do trecho final da fonte
- como testar: Trocar a transição por corte seco nas cenas 3→4 do gta-6 e cortar a fonte antes do cartão final; checar que não há frame preto com a locução ativa.

## 30/10 01:12 PROPOSTA [GOSTO] Troca de cena adiantada/atrasada em relação à locução e clipes repetidos (cw/claude-sonnet-5-5)
- prova: sem-obra-e91dc2 q04 (cena 2 entra ~1 s antes da fala) e q08/q11/q13 (mesmo take 3 vezes); sem-obra-62e3fc q04-q06 (nome falado 2,5 s antes da imagem). Só vale se confirmado no cenas.json.
- onde: seleção/sincronia de cenas (tempos por cena a partir do áudio) e deduplicação de clipes
- como testar: Comparar início de cada cena com o timestamp da primeira palavra no roteiro e proibir reuso do mesmo trecho da fonte em um Short.

## 30/10 02:15 PROPOSTA [CERTEZA] Travar ordem cronológica dos takes e sincronizar corte de cena com o timestamp da palavra-gatilho na locução (gemini-4-argon)
- prova: Em sem-obra-cb8d24_cap1_20261029 (q11–q15) há efeito ping-pong entre Shakhtar e Bielorrússia e troca de cena desconectada da fala ('no meio de pedido de gandula' em q14 mostra jogador do Shakhtar chorando); em meu-irmão-é-mais-velho_cap1_20261029 (q08, q10–q12) há inserção fora de lugar (xícara no escuro em q08 no meio da sala de aula) e o diretor aparece em q10 (40.27s) enquanto a locução só o menciona em q12 (47.82s); em sem-obra-206d3a_cap1_20261029 (q06–q07, q10) o corte de cena trunca a frase no meio e reutiliza o enquadramento de q03.
- onde: Pipeline de montagem/alinhamento de cenas com timestamps do TTS (módulo de seleção e corte de cenas / alinhamento word-level)
- como testar: Reprocessar sem-obra-cb8d24_cap1_20261029 e meu-irmão-é-mais-velho_cap1_20261029 garantindo que cada cena só mude na fronteira de frase do TTS correspondente ao novo evento e sem reutilizar intervalos de tempo anteriores da fonte.

## 30/10 02:15 PROPOSTA [CERTEZA] Auditar detecção de hardsub/delogo e sanitização do gancho do topo (espaçamento, spoiler e persistência) (gemini-4-argon)
- prova: Em sem-obra-b7cafb_cap1_20261029 (q01 'a prisão', q13 'in') e sem-obra-206d3a_cap1_20261029 (q03/q07 '1+1>1 A CHANCE DE SOBREVIVER', q13 'TER VOLTA!') legendas queimadas da fonte ficaram sem cobertura, enquanto em meu-irmão-é-mais-velho_cap1_20261029 (q02–q18) o delogo vertical borrou a boca e o queixo dos personagens. Além disso, o gancho do topo sumiu após q01 em meu-irmão-é-mais-velho_cap1_20261029 (q02) e sem-obra-206d3a_cap1_20261029 (q03), entregou spoiler em sem-obra-206d3a_cap1_20261029 (q01 'ELE VENCEU COM UM COGUMELO') e colou palavras em sem-obra-cb8d24_cap1_20261029 (q01 'UMERRO').
- onde: Módulo de detecção de hardsub/delogo e gerador do texto de gancho superior (gancho_remotion / título queimado no topo)
- como testar: Rodar folha de quadros nos 4 Shorts do lote verificando: (1) bounding box do delogo restrito exatamente à caixa das letras da legenda original sem atingir rostos acima, (2) regex no texto do topo para separar palavras coladas em MAIÚSCULAS e aplicar as regras de não-spoiler de regras_titulo, e (3) duração constante do gancho superior.

## 30/10 03:26 PROPOSTA [CERTEZA] Cortar ou mascarar bordas extremas e remover telas finais (outro/CTA) do vídeo-fonte (gemini-4-argon)
- prova: Em sem-obra-7c9658_cap1_20261029 (q01.jpg, q02.jpg, q07.jpg, q11.jpg), sobrou texto residual ('purposes only.') no topo extremo (y < 100) e barra de progresso amarela na borda inferior; em sem-obra-5991e3_cap1_20261029 (q17.jpg, q18.jpg), os últimos 3s mantiveram a tela preta de inscrição ('GRANA NERD - SE INSCREVE') da fonte original enquanto a locução ainda falava.
- onde: cortes_pipeline.py / função de recorte de vídeo-fonte (crop perimétrico de 2-5% e detecção/corte de tela estática de encerramento nos últimos segundos)
- como testar: Rodar o pré-processamento de vídeo em sem-obra-7c9658_cap1_20261029 e sem-obra-5991e3_cap1_20261029 e verificar nos quadros extraídos que o topo/base extremos foram limpos e que o B-roll útil substitui a tela final estática até o fim do áudio.

## 30/10 03:26 PROPOSTA [CERTEZA] Garantir margem lateral mínima e zona segura nos overlays de texto/tarja superior (gemini-4-argon)
- prova: Em sem-obra-e4043b_cap1_20261029 (q06.jpg, q09.jpg, q10.jpg), o texto da tarja superior vazou nas duas bordas laterais ('IÃO TEM CORAGEM DE AJUDAR EL'); em amnesiac-nanny-was-the-ceos-true-love_cap1_20261029 (q01.jpg), o texto de gancho ficou acima de y=150 colidindo com '@doramanoturno' e em q17.jpg um sticker 'DNA' cobriu o rosto/queixo da personagem.
- onde: cortes_render.py / posicionamento e quebra de linha automática da tarja superior, gancho e stickers
- como testar: Renderizar q01 e q10 de sem-obra-e4043b_cap1_20261029 e q01/q17 de amnesiac-nanny-was-the-ceos-true-love_cap1_20261029 conferindo margem lateral >= 60px e y >= 150 sem colisão com a marca d'água.

## 30/10 04:44 PROPOSTA [CERTEZA] Travar zona segura superior (y >= 150) e corrigir mapeamento do @ do canal e persistência do gancho (gemini-4-argon)
- prova: Em sem-obra-6b31a0 (q01, q02) o gancho e o @ (@historiasemframes-emerson) ficaram em y ≈ 65–110 (cortados pela UI do Shorts); em sem-obra-e1173f (q01, q17) saiu o @ de outro canal ('@cenareact-f3j' em vez de 'novo_universo_ia_d6s') sobre os olhos do protagonista, e o gancho sumiu após q01/q02 em ambos.
- onde: Renderizador de overlay/Remotion e gerador de filtro FFmpeg de marca d'água/gancho (cortes_pipeline / cortes_render)
- como testar: Gerar folha de topo (D:\tmp\folha_topo.py) em 1,5 s e 5,0 s de 4 Shorts e verificar que o @ corresponde ao canal do projeto, fica fixo em y >= 150 sem cobrir rostos e o gancho mantém duração e posição seguras.

## 30/10 04:44 PROPOSTA [CERTEZA] Sincronizar pontos de corte de vídeo estritamente com os timestamps de início/fim de frase do TTS (gemini-4-argon)
- prova: Quatro Shorts do lote tiveram cortes desconectados da fala: sem-obra-e1173f (q07 mostra abraço romântico durante fuga do leão; q15 entra áudio da cena 6 aos 28.72s ainda na imagem da cena 5), sem-obra-6b31a0 (q03 corta para o rapaz enquanto narra insolação da protagonista), sem-obra-ae7564 (q16 corta para o antagonista enquanto ainda repete 'O piazinho é brabo') e sem-obra-4c9116 (q06 faz corte 'ioiô' de 1s para Zeus/Ares no meio da fala de Darkseid).
- onde: Montador de cenas / alinhamento de timestamps de áudio e corte de vídeo (cortes_montagem / cortes_sincronia)
- como testar: Rodar re-render de sem-obra-e1173f e sem-obra-4c9116 garantindo que a duração de cada clipe de cena case com o intervalo exato do segmento de áudio correspondente e proibir sub-cortes menores que 1,5 s fora de contexto.

## 30/10 06:01 PROPOSTA [CERTEZA] Cortes de cena atrasados ou adiantados em relação à voz (cw/claude-sonnet-5-5)
- prova: his-divine q03 (4.44s: troca para o monstro enquanto a voz ainda fala dos professores), q04 (6.66s: forma final aparece em 'ninguém esperava'), q08 (13.88s: a besta só aparece em q10, 4s depois de 'invoca'); mushroom q09/q10 (voz 'pássaro' e 'elimina' sobre golem e janela de missão, pássaro só em q11); 29eb81 q08.
- onde: Seleção/ordem de tomadas por trecho do roteiro (sincronia cena x palavra do roteiro com o tempo da voz) no pipeline de cortes.
- como testar: Conferir no roteiro.txt e nos tempos da voz do his-divine e do mushroom se a cena escolhida é a da frase falada naquele instante. Se o desvio for medido (> 0.3s), reprocessar os dois e comparar a nota de movimento antes e depois.

## 30/10 06:01 PROPOSTA [CERTEZA] Legenda palavra a palavra sobre o @ do canal e abaixo de y=1580 (cw/claude-sonnet-5-5)
- prova: his-divine q03/q04 (legenda 'o tratam' e 'Só que' na mesma Y do @inovaremanhwabr, sobrando só '@ino' e 'wabr'); mushroom q01, q02, q04 a q18 (legenda em y≈1680-1775, sob a interface do Shorts).
- onde: Posição Y da legenda e do @ no compositor de legenda e overlay. O @ pode ir para a faixa y=160-240 e a legenda para y=1250-1450, desde que isso não contradiga a decisão da dona sobre o estilo da legenda (DECISOES_DONO).
- como testar: Renderizar 3 Shorts com os novos Y, abrir a folha de quadros e conferir que legenda e @ não compartilham a coordenada e que a legenda fica acima de y=1580. Checar nas DECISOES_DONO se a Y atual da legenda é escolha dela.

## 30/10 06:01 PROPOSTA [CERTEZA] Título de gancho acima de y=150 e que some no q02 (cw/claude-sonnet-5-5)
- prova: his-divine q01 (y≈110, some em q03); 3f331d q01 (y~110, 'pisca e some no q02'); 29eb81 q01 (título só no q01, sem tarja branca, some no q02).
- onde: Overlay do título de gancho no topo: posição Y e duração. O título deve ficar na Cena 1 inteira.
- como testar: Rodar a folha do TOPO (D:\tmp\folha_topo.py) em todos os Shorts do dia para medir a Y real do título e a duração, antes de mudar o tempo de exibição.

## 30/10 06:01 PROPOSTA [CERTEZA] Blur central em 29eb81: provar se existe legenda queimada embaixo (cw/claude-sonnet-5-5)
- prova: 29eb81 q03/q08/q11/q14: faixa de blur em y≈950-1050 sobre boca, nariz e queixo em todos os quadros, mais um patch marrom ou vermelho sobre o olho em q14. Falta o log do Short para saber se a visão leu legenda.
- onde: Log '[hardsub]' do Short sem-obra-29eb81 e a decisão de tarja/delogo que posicionou a faixa na altura do rosto.
- como testar: Ler o log. Se for '[hardsub] só 0/6' (ou o texto lido não bater com o do quadro), o blur é indevido: reprocessar sem tarja. Se leu legenda, reprocessar medindo a altura real das letras (resolução >= 720 px) para que o blur não passe do tamanho exato da legenda.

## 30/10 06:01 PROPOSTA [GOSTO] Stickers da mascote cobrindo @ ou rosto (sem alavanca segura) (cw/claude-sonnet-5-5)
- prova: mushroom q13 (sticker sobre o 'r' do @ e acima de y=150); 29eb81 q11/q14 (sticker feminino sobre a arte e sobre o @). Não sei o que são os modos A e B de 'mascote', então trocar 'ab' seria chute.
- onde: Módulo da mascote: posição, margem do topo e z-order em relação ao @. Ver o que A e B fazem.
- como testar: Se a mascote é identidade da dona, só reposicioná-la (fora de y<150, sem cobrir o @ ou rosto) em vez de bani-la, e medir nos próximos lotes. Não adotar a regra 6 do APRENDIDO sem passar pelas DECISOES_DONO.

## 30/10 10:04 PROPOSTA [CERTEZA] Fixar posições de marca do canal, título de gancho e stickers fora da zona morta superior e sem colisão (gemini-4-argon)
- prova: Colisão direta e invasão de y < 150 em 3 Shorts do lote: sem-obra-899c4e (q01: título colide e cobre @bichonoturnobr), sem-obra-3214b2 (q01: título acima de y=150 sobrepõe @bichonoturnobr; q02: sticker no canto superior esquerdo), sem-obra-0fdade (q01: @manhwareact-ia em y=90-110 com fonte <34px e sem contraste em q09; q03/q15: sticker em y=50 cobrindo '@m' da marca do canal).
- onde: Template Remotion / gerador de overlay de topo e mascote (posicionamento Y da marca em y=160..200 com corpo >=34px e contorno escuro >=3px, título abaixo sem sobrepor, e trava para stickers não cobrirem a marca).
- como testar: Renderizar 1 quadro em t=1.5s (folha_topo.py) de 4 Shorts com gancho e mascote ativos e verificar que @canal e título têm bounding boxes disjuntas dentro de y=150..300.

## 30/10 10:04 PROPOSTA [CERTEZA] Cortar planos mortos sem sujeito (>1.5s de baixa variação/ausência de foco) e clipes residuais de CTA no fim das tomadas (gemini-4-argon)
- prova: Repetido em todos os 4 Shorts: sem-obra-899c4e (q12 aos 29.64s fica quase 3s em vegetação cinza vazia após o animal sair em q11), sem-obra-3214b2 (q03 aos 10.1s mantém chão vazio e névoa após o personagem afundar na areia), sem-obra-0fdade (q06 parede bege vazia com 11.4% de movimento; q18 caminho de pedras vazio no fecho), e sem-obra-320d34 (q17/q18 aos 15.86s entra clipe desconexo de bebê com CTA 'deixa' e '@DelsitoShorts').
- onde: Pipeline de seleção/corte de cenas e detecção de fim de tomada (trimmer de B-roll / detector de movimento por sub-trecho).
- como testar: Rodar o extrator de cenas nos 4 Shorts do lote exigindo corte antecipado quando a taxa de movimento cair abaixo de 15% por >1.2s ou houver troca brusca de histograma nos últimos 2s da fonte (CTA final).

## 30/10 15:26 PROPOSTA [CERTEZA] Fixar coordenadas e contorno da marca do canal e do título no topo sem colisão (gemini-4-argon)
- prova: Em sem-obra-899c4e_cap1_20261029 (q01) e sem-obra-3214b2_cap1_20261029 (q01), o título inicia acima de y=150 e sobrepõe diretamente a marca '@bichonoturnobr'. Em sem-obra-0fdade_cap1_20261029 (q01, q09, q15), '@manhwareact-ia' fica em y=90-110 (<34px) sem contraste contra clarões e colide com elementos do canto superior.
- onde: Renderizador de overlay/topo do pipeline de cortes (posicionamento de @canal e título de gancho)
- como testar: Gerar folha do topo em 1,5s (D:\tmp\folha_topo.py) e verificar que @canal fica fixo em y=160..200 (>=34px com borda escura >=3px) e o título logo abaixo (y=210..280) sem sobreposição.

## 30/10 15:26 PROPOSTA [CERTEZA] Detectar e cortar stickers de canto, marcas d'água e caudas de CTA da fonte parceira (gemini-4-argon)
- prova: Em sem-obra-3214b2_cap1_20261029 (q01, q02) e sem-obra-0fdade_cap1_20261029 (q01, q03, q15), stickers de anime no canto superior esquerdo e marcas d'água ('Ultravox Filmes', 'levisaosensei') ficaram visíveis. Em sem-obra-320d34_cap1_20261029 (q17, q18) e sem-obra-899c4e_cap1_20261029 (q12), entraram sobras de vídeo com CTA '@DelsitoShorts' e 3s de tela térmica vazia.
- onde: Módulo de seleção de cenas / crop de bordas do vídeo fonte no pipeline de cortes
- como testar: Rodar reprocessamento nos 4 Shorts do lote e inspecionar q01..q18 garantindo crop perimétrico (5% a 15%) sobre stickers de canto e corte de fim de cena antes de CTAs ou planos vazios (<15% movimento).

## 30/10 16:34 PROPOSTA [CERTEZA] Ajustar enquadramento (crop vertical) para preservar sujeito ativo e menus completos e limpar zona morta superior (gemini-4-argon)
- prova: Em sem-obra-0fdade_cap1_20261029 (q06, q12) o crop foca em parede vazia na fala 'ele abre' e corta o tronco/rosto do personagem em 'ficou fortão'; em gta-rp_cap1_20261029 (q03, q04, q05, q11) o crop corta a coluna esquerda do menu de configurações ('Muito alta', 'Normal'), reduz a caixa de cupom a miniatura ilegível e deixa o logo 'Maresia' fatiado no topo (y < 150).
- onde: Módulo de crop vertical / reenquadramento inteligente e posicionamento de marca d'água no pipeline de vídeo
- como testar: Rodar o reenquadramento nos vídeos fonte de sem-obra-0fdade_cap1_20261029 e gta-rp_cap1_20261029 e inspecionar q05, q06, q11 e q12 garantindo texto de UI legível (>= 32 px), sujeito centralizado e marca d'água dentro de y=150..1580.

## 30/10 16:34 PROPOSTA [CERTEZA] Evitar repetição de takes estáticos e alinhar corte de cena exatamente ao gatilho verbal da locução (gemini-4-argon)
- prova: Em sem-obra-615719_cap1_20261029 (q12, q16, q17) o take do corredor alagado de q14 se repete em q16 e o corte para a escadaria atrasa em relação à fala 'escadaria do navio'; em gta-rp_cap1_20261029 (q06, q08, q15) a mesma pose estática em preto e branco repete 4 vezes e a fala diz 'normal' enquanto o cursor seleciona 'Desligado'; em sem-obra-b04e32_cap1_20261030 (q09, q11, q15) há flash cut de 1s e cena parada (8.2% de movimento) com sticker 'EXPLODE' durante narração de explosão.
- onde: Seletor de cenas / alinhamento de B-roll com timestamps do roteiro e filtro de deduplicação de takes
- como testar: Reprocessar a montagem de sem-obra-615719_cap1_20261029 e sem-obra-b04e32_cap1_20261030 verificando ausência de takes duplicados, movimento > 15% no clímax e corte sincronizado com substantivos/conectivos da fala.

## 30/10 17:44 PROPOSTA [CERTEZA] Fixar duração e zona segura (y=180..260) do banner de gancho na Cena 1 (gemini-4-argon)
- prova: Em sem-obra-82e3a7_cap1_20261030 (q01, q03) o banner 'O DESASTRADO TINHA UM DOM RARO' colide com '@manhwareact-ia' e some abruptamente em q03 ainda na Cena 1; em danmachi_cap1_20261030 (q01, q02, q03) o gancho 'ELE REJEITOU A GAROTA ERRADA' sai no centro da tela (y~600-750) cobrindo o rosto da personagem Freya e também desaparece em q03 antes do fim da cena inicial.
- onde: Renderizador de overlay/título de gancho da Cena 1 (cálculo de coordenada Y e duração do filtro drawtext/overlay no FFmpeg)
- como testar: Renderizar sem-obra-82e3a7_cap1_20261030 e danmachi_cap1_20261030 e extrair q01, q02 e q03 conferindo se o banner permanece entre y=180 e y=260 sem cobrir rosto/identificador do canal e se sustenta 100% de opacidade durante toda a Cena 1.

## 30/10 17:44 PROPOSTA [CERTEZA] Detecção de marca d'água fixa nos cantos e texto queimado fora da faixa padrão (gemini-4-argon)
- prova: Três Shorts saíram com grafismos ou legendas da fonte parceira expostos: sem-obra-82e3a7_cap1_20261030 (q01-q18 texto fixo no topo e q11 legendas 'EXPLICARAM'/'DERRETIDO' no meio da tela sem cobertura), tensei-shitara-slime-datta-ken_cap1_20261030 (q14 mascote fixa da fonte no canto inferior esquerdo até y=1880) e danmachi_cap1_20261030 (q01/q05 marca 'TOP ANIME / INSCREVA-SE' no canto superior esquerdo).
- onde: Módulo de detecção de hardsub/marca d'água e recorte (crop/delogo) do pipeline de vídeo
- como testar: Rodar o detector nos vídeos-fonte desses 3 Shorts e validar em folha de quadros se os cantos com marca d'água estática são recortados pelo pan & scan e se legendas dinâmicas no terço médio recebem delogo exato na caixa das letras.

## 30/10 18:56 PROPOSTA [CERTEZA] Desativar palavras gigantes no centro da tela e stickers/avatares fora da zona segura (gemini-4-argon)
- prova: Letreiros gigantes no centro obstruem a cena principal em sem-obra-3744ee (q16 'PERDEU' cobrindo a prensa em y~700-950) e cherish (q16 'VIROU' cobrindo o rosto dos pais); stickers invadem margens proibidas em sem-obra-ffeedb (q05, q11 acima de y=150) e pirarucu (q15 abaixo de y=1580).
- onde: gerador de legenda / compositor de overlays de vídeo (modo legenda_impacto='lateral' e camada de stickers)
- como testar: Renderizar sem-obra-3744ee, cherish e pirarucu garantindo que toda ênfase fique restrita à legenda inferior e sem stickers avulsos fora de y=150..1580.

## 30/10 18:56 PROPOSTA [CERTEZA] Restringir delogo/smear de legenda à metade inferior e bloquear em áreas de rosto/corpo central (gemini-4-argon)
- prova: Faixa de distorção/smear deformando elementos principais no meio da tela em pirarucu (q03 e q05 entre y~870 e y~1140 fatiando o peixe e a cabeça do pescador) e cherish (q13 sobre os rostos e olhos dos músicos no split screen).
- onde: detector de hardsub / filtro delogo no pipeline de vídeo
- como testar: Rodar detecção de hardsub nos quadros de pirarucu e cherish e validar que caixas no terço médio (y < 1150) ou sobre rostos não recebam filtro delogo.

## 30/10 19:04 PROPOSTA [CERTEZA] Desativar overlays de palavra gigante no centro, stickers de anime avulsos e barras de áudio (gemini-4-argon)
- prova: Letreiros gigantes no centro da tela cobrem a ação e rostos no clímax em sem-obra-3744ee_cap1_20261030 (q16.jpg, texto 'PERDEU' em y~700-950 sobre a prensa) e cherish_cap1_20261030 (q16.jpg, texto 'VIROU' sobre o rosto dos pais). Além disso, stickers de anime desconexos e barras pretas de áudio invadem zonas proibidas (< y=150 e > y=1580) ou piscam com glitch em sem-obra-ffeedb_cap1_20261030 (q05.jpg, q07.jpg, q11.jpg) e pirarucu_cap1_20261030 (q15.jpg, sticker até y=1845).
- onde: Pipeline de composição de vídeo / gerador de legendas ASS e camadas de overlay (funções de word-impact central, inserção de stickers PNG e audio visualizer)
- como testar: Renderizar novamente sem-obra-3744ee e pirarucu verificando nos quadros q05, q07, q15 e q16 que nenhuma palavra gigante central, barra de espectro ou sticker PNG avulso foi desenhado e que todo elemento gráfico respeita a margem y=150..1580 e x=60..1020.

## 30/10 19:04 PROPOSTA [CERTEZA] Travar duração máxima de plano estático com zoom/pan contínuo (Ken Burns) e sincronizar corte por timestamp da locução (gemini-4-argon)
- prova: Planos congelados ou parados derrubaram o movimento nos 4 Shorts do lote: sem-obra-3744ee_cap1_20261030 (q09-q14, >6s congelado e atraso de ~2s na troca em q13), sem-obra-ffeedb_cap1_20261030 (q06-q17, >16s no mesmo plano aberto com 5.6% de movimento), pirarucu_cap1_20261030 (q09-q13, quase 20s de corredeira estática) e cherish_cap1_20261030 (q14-q17, imagem estática de IA congelada por ~5s e cortes atrasados em q04 e q13).
- onde: Montador de cenas / corte de vídeo no FFmpeg (aplicação de filtro zoompan em imagens estáticas ou takes com movimento medido < 15% e alinhamento do corte ao timestamp inicial da frase no TTS)
- como testar: Rodar o medidor de movimento por cena nos 4 Shorts após reprocessar e confirmar que nenhuma cena fica com movimento < 15% ou freeze frame > 1.0s, e que a troca de take ocorre em até 0.2s do início da frase correspondente.

## 30/10 19:04 PROPOSTA [CERTEZA] Restringir delogo/smear de legenda queimada à faixa da legenda original sem atingir o terço médio (gemini-4-argon)
- prova: O filtro de cobertura/delogo está criando faixas de distorção por estiramento vertical de pixels no meio da imagem, deformando o pirarucu e a cabeça do pescador em pirarucu_cap1_20261030 (q03.jpg e q05.jpg, entre y=870 e y=1140) e borrando os rostos e olhos dos músicos no split screen de cherish_cap1_20261030 (q13.jpg).
- onde: Detector de hardsub / gerador de caixa de delogo (cálculo de bounding box y/h especialmente quando há reenquadramento vertical ou split screen)
- como testar: Inspecionar q03 e q05 de pirarucu_cap1_20261030 e q13 de cherish_cap1_20261030 garantindo que o delogo só seja aplicado onde há texto confirmado em >= 2 quadros e nunca sobre a faixa central de rosto/sujeito (y=700..1150) sem legenda.

## 30/10 20:14 PROPOSTA [CERTEZA] Remover letreiros gigantes centrais, stickers avulsos e travar elementos na zona segura (y=150..1580) (gemini-4-argon)
- prova: Letreiro gigante no centro cobrindo a ação/rostos em sem-obra-3744ee_cap1_20261030 (q16 'PERDEU') e cherish_cap1_20261030 (q16 'VIROU'); stickers/avatares e barras de áudio invadindo bordas ou área de botões em sem-obra-ffeedb_cap1_20261030 (q05, q07, q11) e pirarucu_cap1_20261030 (q15); título fora de y=150 ou colidindo com @Inovare-q8l em sem-obra-3744ee (q03, q09 'o' residual), pirarucu (q01) e cherish (q01).
- onde: Pipeline de composição/overlay de vídeo e legendas (geração de ASS/FFmpeg drawtext/overlays em D:\video-fila\linhas\CORTES)
- como testar: Renderizar novamente sem-obra-3744ee e cherish e inspecionar folha de quadros verificando ausência de texto central gigante, ausência de stickers/barras de áudio avulsos e confinamento de títulos/marcas em y=150..1580 com margem lateral >= 60px.

## 30/10 20:14 PROPOSTA [CERTEZA] Quebrar planos estáticos/congelados (>3s) com zoom/pan dinâmico e sincronizar corte de cena com a locução (gemini-4-argon)
- prova: Planos congelados ou parados por 5s a 16s em todos os 4 Shorts: sem-obra-3744ee_cap1_20261030 (q09-q14 congelado >6s e atraso de corte em q13), sem-obra-ffeedb_cap1_20261030 (q06-q17 parado 16s no mesmo plano com 5-7% de movimento e pan final para cadeira vazia em q18), pirarucu_cap1_20261030 (q09-q13 corredeira por ~20s e q05-q06 costas do pescador por 8s) e cherish_cap1_20261030 (q14-q17 imagem estática por ~5s e cortes atrasados em q04 e q13).
- onde: Módulo de corte/montagem de cenas e aplicação de Ken Burns / pan & scan (D:\video-fila\linhas\CORTES)
- como testar: Medir taxa de movimento por cena nos Shorts reprocessados garantindo movimento > 15%, zero freeze frames > 1.0s e alinhamento dos cortes com os timestamps de troca de cena da locução (tolerância < 0.2s).

## 30/10 21:24 PROPOSTA [CERTEZA] Remover palavras de impacto no centro da tela e confinar stickers/títulos à zona segura sem colidir com marca d'água (gemini-4-argon)
- prova: Letreiro central gigante obstruindo o clímax/rostos em sem-obra-3744ee (q16.jpg 'PERDEU' em y~700-950) e cherish (q16.jpg 'VIROU' sobre o rosto dos pais). Stickers fora de contexto e elementos fora da zona segura (y=150..1580, margem 60px) em sem-obra-3744ee (q03.jpg título em y=50-80, q05.jpg seta a <60px da borda), sem-obra-ffeedb (q05.jpg e q11.jpg avatar cortado na margem direita e em y=75) e pirarucu (q15.jpg sticker anime até y=1845; q01.jpg título colidindo com '@Inovare-q8l' em y~540).
- onde: Gerador de ASS / compositor FFmpeg de camadas gráficas (função de legenda_impacto='lateral', overlay de stickers/setas e posicionamento do título do gancho)
- como testar: Renderizar novamente sem-obra-3744ee, pirarucu e cherish verificando nos quadros q01, q03, q05, q15 e q16 que nenhuma palavra de destaque cai na faixa central (y=400..1300), que stickers/avatares avulsos estão desativados e que todo texto/seta respeita x in [60, 1020] e y in [150, 1580] sem sobrepor a marca d'água.

## 30/10 21:24 PROPOSTA [CERTEZA] Aplicar zoom/pan dinâmico (Ken Burns) ou sub-cortes em tomadas estáticas longas e travar delogo fora da faixa central de rostos (gemini-4-argon)
- prova: Imagens congeladas ou planos estáticos longos derrubando movimento em todos os 4 Shorts: sem-obra-3744ee (q09-q14, >6s congelado), sem-obra-ffeedb (q06-q17, >16s no mesmo plano aberto com 5.6% de movimento), pirarucu (q09-q13, ~20s de corredeira; q05-q06, 8s estático) e cherish (q14-q17, ~5s de foto estática sem zoom/pan). Além disso, faixa de delogo/smear no meio do quadro (y~870-1140) deformando rostos e o sujeito em pirarucu (q03.jpg, q05.jpg) e cherish (q13.jpg).
- onde: Montador de vídeo / filtro de movimento e detector de caixa de hardsub (cortes_pipeline / aplicação do delogo e pan & scan)
- como testar: Checar no montador que tomadas ou fotos com duração > 3.0s ou movimento medido < 10% recebem zoom-in/pan contínuo ou corte de escala, e bloquear a aplicação de delogo quando a caixa detectada cair na faixa central do corpo/rosto (y entre 600 e 1250 em frame 1920p) sem confirmação de texto válido.

## 30/10 22:38 PROPOSTA [CERTEZA] Fixar título de gancho na zona segura superior (y=160..280) sem cobrir rostos e manter opacidade 100% até o fim da Cena 1 (gemini-4-argon)
- prova: O bloco de título inicial cobriu o rosto/olhos do personagem principal em cherish_cap1_20261030 (q01, q02), lamine-yamal_cap1_20261030 (q01, q02) e the-sword-chose-the-boy_cap1_20261030 (q01), colidiu com '@Inovare-q8l' em pirarucu_cap1_20261030 (q01) e sumiu ou ficou com opacidade fantasma antes do corte da Cena 1 em pirarucu (q02), cherish (q03) e lamine-yamal (q03).
- onde: anime_gancho.py / parceiro_marca.py (cálculo de GANCHO_Y em relação ao bbox de rosto/@canal e duração/fade do overlay na Cena 1)
- como testar: Renderizar a Cena 1 dos 4 Shorts do lote e gerar folha do topo em 1.5s e 3.8s (D:\tmp\folha_topo.py), validando que o título permanece entre y=160 e y=280 sem interseção com rostos ou @canal e com 100% de opacidade até o corte para a Cena 2.

## 30/10 22:38 PROPOSTA [CERTEZA] Restringir filtro delogo/smear à caixa exata de letras confirmadas pela visão e bloquear aplicação sobre o terço médio/rostos (gemini-4-argon)
- prova: Faixa de distorção vertical (delogo/smear) no centro da imagem deformou elementos principais e rostos em 3 Shorts: pirarucu_cap1_20261030 (q03 fatia o peixe e q05/q06 deforma a cabeça do pescador entre y≈870 e y≈1140), cherish_cap1_20261030 (q13 sobre os olhos dos músicos) e the-sword-chose-the-boy_cap1_20261030 (q07, q13, q16 no centro das cenas), além de blur pélvico em lamine-yamal_cap1_20261030 (q07, q08, q10).
- onde: anime_hardsub_detect.py / parceiro_marca.py (validação vertical da caixa de hardsub e aplicação de delogo)
- como testar: Conferir o log [hardsub] e reprocessar pirarucu_cap1_20261030, cherish_cap1_20261030 e the-sword-chose-the-boy_cap1_20261030 garantindo que caixas com y < 1150 ou sem texto variável confirmado em >= 2/6 quadros não recebam delogo.

## 30/10 22:38 PROPOSTA [CERTEZA] Eliminar buracos > 1.5s sem legenda dinâmica e limitar planos estáticos aplicando zoompan e corte sincronizado ao áudio (gemini-4-argon)
- prova: Vácuo total de legendas durante o vídeo em 3 Shorts: pirarucu_cap1_20261030 (q15), lamine-yamal_cap1_20261030 (q06 a q08 entre 7s-10s e q11) e the-sword-chose-the-boy_cap1_20261030 (q11 e q12, quase 5s sem texto aos 27s-30s). Planos parados longos ou cortes atrasados em pirarucu (q09-q13, ~20s de corredeira; q05-q06, 8s parado), cherish (q04 e q13 com corte atrasado; q14-q17 foto congelada por ~5s) e lamine-yamal (q16-q18 com 5.0% de movimento).
- onde: fx_subtitles.py / anime_segments.py (continuidade dos timestamps de cartões de legenda e corte/zoompan em tomadas com movimento < 15% ou duração > 3.5s)
- como testar: Reprocessar the-sword-chose-the-boy_cap1_20261030, lamine-yamal_cap1_20261030 e cherish_cap1_20261030 verificando que nenhum intervalo > 1.0s com fala fique sem legenda renderizada, que as trocas de cena ocorram em <= 0.2s do início da frase e que tomadas estáticas recebam zoompan ou corte.

## 30/10 23:44 PROPOSTA [CERTEZA] Corrigir centralização do sujeito no reenquadramento vertical (pan & scan 9:16) e margem de 60px (gemini-4-argon)
- prova: Em 3 de 4 Shorts o crop vertical cortou cabeças/protagonistas ou deixou >60% de cenário vazio: sem-obra-065b5d (q06 cabeça de Ramos abaixo de y=1580 com 70% de gramado; q12 cabeça de Kroos decepada no topo; q09 Benzema cortado), sem-obra-43e95b (q12 protagonista cortado na lateral direita; q15 paraquedas cortado no topo com 60% de céu vazio) e sem-obra-d41062 (q02, q08, q10 tags 'MODRIC'/'KOVACIC'/'BERNARDO' cortadas na borda direita e câmera fora do gol).
- onde: Módulo de reenquadramento vertical / crop 9:16 e detecção de rosto/sujeito no pipeline de vídeo
- como testar: Rodar o crop 9:16 nos vídeos-fonte de sem-obra-065b5d e sem-obra-43e95b e gerar folha de quadros verificando se o rosto/corpo do sujeito citado fica entre y=300 e y=1400 e a mais de 60px das bordas laterais.

## 30/10 23:44 PROPOSTA [CERTEZA] Fixar duração (4s-5s), posição (y=160 a y=260) e anti-spoiler no texto de gancho do topo (gemini-4-argon)
- prova: Em 2 Shorts o texto de gancho no topo deu spoiler do final no primeiro segundo e sumiu abruptamente em q02: sem-obra-43e95b (q01 'ELE SALVOU UM ELEFANTE EM QUEDA LIVRE' some logo após q02) e sem-obra-a3e127 (q01 'ELE SE TORNOU UMA LENDA' invadindo y=95-110 acima de y=150 e sumindo em q02).
- onde: Geração e renderização do hook/headline superior (overlay de texto inicial do Short)
- como testar: Gerar o gancho de sem-obra-43e95b e sem-obra-a3e127 e checar com D:\tmp\folha_topo.py e quadros q01-q05 se o texto fica entre y=160 e y=260, permanece estável até o fim da 1ª cena (4-5s) e não usa verbo no passado entregando o desfecho.

## 30/10 23:44 PROPOSTA [CERTEZA] Alinhar corte de cena e correspondência visual com o sujeito citado na locução (gemini-4-argon)
- prova: Em 4 de 4 Shorts a imagem contradiz o sujeito ou ação narrada: sem-obra-065b5d (q14 fala 'Carlo Ancelotti' e mostra Carvajal; q15 fala 'Lucas Vázquez' e mostra Alexander-Arnold), sem-obra-d41062 (q04 fala de euforia e mostra Guardiola desolado; q14 narra o chute após a bola já ter entrado em q12), sem-obra-43e95b (q14 insere take sentado no avião durante a queda livre) e sem-obra-a3e127 (q08 galão amarelo em árvores na deixa 'Porém um dia'; q10 fala 'puxei o travesseiro' sem cachorro em cena).
- onde: Alinhamento roteiro-cena / seleção de takes e timestamps no montador de cortes
- como testar: Conferir os timestamps das falas contra os quadros extraídos nos 4 Shorts garantindo que o corte visual ocorra junto à mudança de sujeito (<0.2s) e exiba o personagem citado.

## 30/10 23:44 PROPOSTA [CERTEZA] Filtrar fontes com stickers de anime intrusivos e remover palavra isolada gigante no centro (gemini-4-argon)
- prova: Em 2 Shorts (sem-obra-065b5d q04/q13 e sem-obra-43e95b q09) há stickers de anime sobrepostos ao vídeo original; e em sem-obra-a3e127 (q18) a palavra gigante 'COMEÇOU' no centro da tela cobre o cachorro e duplica a legenda inferior.
- onde: Filtro de qualidade da fonte / limpeza de overlays periféricos e gerador de ênfase de legenda
- como testar: Verificar nos quadros q04/q13 de sem-obra-065b5d, q09 de sem-obra-43e95b e q18 de sem-obra-a3e127 se nenhuma palavra gigante é renderizada no centro da tela e se stickers de borda são detectados/recortados.

## 31/10 01:05 PROPOSTA [CERTEZA] Recuo lateral mínimo (>= 60 px) e proteção de rosto nas palavras de impacto laterais e título de topo (gemini-4-argon)
- prova: sem-obra-23bf3f_cap1_20261030 (q17.jpg 'DEMITIU' colado a < 60 px da borda esquerda e sobre a cabeça; q02.jpg título no topo sobre a testa) e sem-obra-5a03df_cap1_20261030 (q14.jpg 'GRITOU' e q18.jpg 'GOSTOU' a < 60 px das bordas laterais e cobrindo o rosto dos personagens).
- onde: Módulo de renderização de legendas/palavras de impacto (ex.: função de layout ASS/drawtext para legenda_impacto='lateral' e headline do topo)
- como testar: Renderizar novamente sem-obra-23bf3f e sem-obra-5a03df garantindo clamp de X entre [60, 1020] px e deslocamento vertical fora da bounding box de rosto detectado; inspecionar q02, q14, q17 e q18.

## 31/10 01:05 PROPOSTA [CERTEZA] Desativar stickers/avatares PNG de canto e ajustar crop vertical para preservar rostos sem stretch blur invasivo (gemini-4-argon)
- prova: Stickers invadindo margem/rosto/marca d'água em sem-obra-23bf3f_cap1_20261030 (q06.jpg, q15.jpg) e she-fell-in-love-with-her-teacher_cap1_20261030 (q07.jpg); rostos decepados no topo ou na boca pelo crop/stretch blur em she-fell-in-love-with-her-teacher_cap1_20261030 (q01.jpg, q03.jpg, q07.jpg) e sem-obra-5a03df_cap1_20261030 (q07.jpg, q09.jpg).
- onde: Pipeline de composição de vídeo / overlay de stickers e função de auto-crop/enquadramento vertical 9:16
- como testar: Desligar a inserção de stickers PNG avulsos e ancorar o centro do crop Y no topo da bounding box facial (garantindo olhos e boca dentro da área ativa do vídeo antes do fundo desfocado) nos Shorts she-fell-in-love-with-her-teacher e sem-obra-5a03df.

## 31/10 01:05 PROPOSTA [CERTEZA] Travar corte de cena nos timestamps exatos da locução e proibir reciclagem de tomada incompatível no clímax (gemini-4-argon)
- prova: sem-obra-223ebb_cap1_20261030 (q05.jpg, q07.jpg, q16.jpg com cortes de cards atrasados/adiantados em relação ao nome falado e q14.jpg com painel vazio) e sem-obra-5a03df_cap1_20261030 (q16.jpg, q17.jpg repetindo cena ensolarada da entrada da escola enquanto a narração descreve confusão com taco e desmaio no chão).
- onde: Montador de cenas / alinhamento de timestamps de áudio-vídeo (corte de cenas por frase do TTS)
- como testar: Validar no montador que cada transição de cena use o timestamp de início da frase correspondente no TTS (tolerância < 0.2s) e impedir reuso de clipes de cenas anteriores no clímax.

## 31/10 02:16 PROPOSTA [CERTEZA] Respeitar margem de segurança (>= 60px laterais, y >= 150) e evitar rostos em stickers e palavras de impacto (gemini-4-argon)
- prova: Em sem-obra-23bf3f (q06, q15, q17), she-fell-in-love-with-her-teacher (q07) e sem-obra-5a03df (q14, q18), stickers de personagem e textos de impacto ('DEMITIU', 'GRITOU', 'GOSTOU') invadem a margem lateral (< 60 px) ou superior (y < 150) e cobrem diretamente o rosto dos personagens.
- onde: Módulo de renderização de overlays/stickers e legenda de impacto lateral
- como testar: Renderizar novamente os 3 Shorts afetados aplicando clamp de coordenadas (x entre 60 e largura-60, y >= 150) e checagem de bounding box de rosto antes de posicionar o sticker ou texto lateral.

## 31/10 02:16 PROPOSTA [CERTEZA] Sincronizar cortes de cena com os timestamps da locução e bloquear reaproveitamento de takes fora de ordem (gemini-4-argon)
- prova: Em she-fell-in-love-with-her-teacher (q06, q15), sem-obra-5a03df (q16, q17) e sem-obra-223ebb (q07, q14, q16), os cortes visuais adiantam/atrasam em relação à frase narrada ou reciclam cenas anteriores que contradizem a ação descrita.
- onde: Módulo de alinhamento de cenas/montagem de vídeo (seleção e corte de takes por trecho de áudio)
- como testar: Conferir nos quadros de transição se a mudança de plano ocorre dentro de 0.2s do início da frase correspondente e impedir reutilização de timestamp já exibido em cenas anteriores.

## 31/10 03:24 PROPOSTA [CERTEZA] Travar margem lateral mínima (>= 60 px) e zona superior (y >= 150) para stickers e palavras de impacto lateral (gemini-4-argon)
- prova: sem-obra-23bf3f_cap1_20261030 (q06, q15, q17: sticker acima de y=150 sobrepondo @doramanoturno/cabeça e texto 'DEMITIU' a < 60 px da borda esquerda), she-fell-in-love-with-her-teacher_cap1_20261030 (q01, q07: destaque sobre rosto e sticker a < 60 px da borda) e sem-obra-5a03df_cap1_20261030 (q14 'GRITOU' e q18 'GOSTOU' sobre o rosto e a < 60 px das bordas laterais).
- onde: Módulo de renderização de overlays/legenda de impacto lateral e stickers no compositor de vídeo (pipeline CORTES)
- como testar: Renderizar novamente q14/q18 de sem-obra-5a03df e q15/q17 de sem-obra-23bf3f verificando bounding box de todos os overlays dentro de x in [60, 1020] e y >= 150, sem colisão com caixas de rosto detectadas.

## 31/10 03:24 PROPOSTA [CERTEZA] Ancorar crop vertical pela detecção facial para não decepar olhos ou boca nem invadir a faixa de stretch blur (gemini-4-argon)
- prova: she-fell-in-love-with-her-teacher_cap1_20261030 (q01, q03, q07: enquadramento corta olhos e testa dos personagens pela borda superior) e sem-obra-5a03df_cap1_20261030 (q07, q09: corte do quadro principal na altura da boca, deformando queixo e lábios no stretch blur inferior).
- onde: Função de auto-crop / reenquadramento 9:16 e cálculo da borda do fundo blur/stretch no pipeline de vídeo
- como testar: Rodar o crop nos trechos de q03 de she-fell-in-love e q07/q09 de sem-obra-5a03df e validar que o bbox completo da face permanece 100% dentro da janela ativa do vídeo antes da transição para o blur.

## 31/10 04:34 PROPOSTA [CERTEZA] Travar a camada da tarja/título fora do zoom/pan da cena e respeitar zona segura (x>=60, y>=150) (gemini-4-argon)
- prova: Em sem-obra-e4043b (q03, q04, q08), o título na tarja branca oscilou com a câmera e teve letras cortadas nas margens ('LES VÃO...', 'AGUENTAR ESS', 'NA ESCOL.'). Em sem-obra-0f7fe7 (q01), o título subiu para y=115 e cobriu os olhos do protagonista e o @ do canal.
- onde: Renderização de overlay/tarja no FFmpeg (aplicar drawtext/overlay da tarja após o crop/zoompan da cena, travado em trilha estática com margem lateral >= 60px e y entre 160 e 260)
- como testar: Reprocessar sem-obra-e4043b_cap1_20261030 e sem-obra-0f7fe7_cap1_20261030 e gerar folha de topo (1.5s e 10s) verificando que 100% das letras ficam dentro de x=[60, 1020] e y>=150 sem oscilar nos cortes.

## 31/10 04:34 PROPOSTA [CERTEZA] Antecipar corte de cena para o início da frase do novo sujeito e aplicar zoom dinâmico em tomadas > 3s (gemini-4-argon)
- prova: Atraso visual de 2 a 4s entre a fala e a imagem em 4 Shorts: betinha q07 (fala do protagonista na imagem da garota), one-piece q15 (fala do Zoro na imagem da Robin), sem-obra-e4043b q08 (fala do pássaro ainda no pátio) e sem-obra-0f7fe7 q15 (fala de ex-amigo na cena do pano). Além disso, planos estáticos >4s derrubaram o movimento em betinha (q05, q14), one-piece (q11, q15) e sem-obra-0f7fe7 (q17).
- onde: Alinhamento de timestamps de cortes (sincronia TTS/cena) e filtro de movimento/zoompan em tomadas com duração > 3.0s
- como testar: Comparar os timestamps de início de cada frase do TTS com os pontos de corte do vídeo em one-piece_cap1_20261030 e sem-obra-e4043b_cap1_20261030 (tolerância < 0.2s) e medir se o movimento por cena fica acima de 15%.

## 31/10 04:34 PROPOSTA [CERTEZA] Detectar e recortar/mascarar avatares PNG fixos nos cantos da fonte parceira (gemini-4-argon)
- prova: Avatares/stickers PNG fixos do vídeo original vazaram nos cantos em betinha_cap1_20261030 (q05, q12 no canto inferior esquerdo) e one-piece_cap1_20261030 (q08, q09 no canto superior esquerdo).
- onde: Pré-processamento de vídeo / detecção de elementos estáticos de borda nos vídeos de canais parceiros de anime
- como testar: Rodar detecção de máscara estática nos cantos em betinha_cap1_20261030 e one-piece_cap1_20261030 e conferir nos quadros q05, q08 e q12 se o sticker do parceiro foi removido por crop leve ou blur.

## 31/10 05:45 PROPOSTA [CERTEZA] Corrigir glitches de renderização da legenda (quebra de sílabas, sobreposição de linhas e efeito esticado) e posição sobre rostos (gemini-4-argon)
- prova: sem-obra-2a4dba_cap1_20261030 (q14 quebra 'M' e 'mão', q11 cobre olhos), jujutsu-kaisen_cap1_20261030 (q13 texto esticado em código de barras, q11 'SETE' sobre olho) e eu-perdi-minha-memória_cap1_20261030 (q04 'cara.' sobre 'ABRAÇOU', q05 arco flutuante, q06 'PRO JETOR').
- onde: Gerador de legendas ASS / estilo `legenda_impacto: lateral` no pipeline de legendagem.
- como testar: Renderizar os trechos q04-q06 de eu-perdi-minha-memória_cap1_20261030 e q11-q14 de jujutsu-kaisen_cap1_20261030 e sem-obra-2a4dba_cap1_20261030 garantindo palavras inteiras sem quebra no meio, espaçamento vertical fixo entre linhas e posicionamento fora da zona central de rostos (y=600 a y=1100).

## 31/10 05:45 PROPOSTA [CERTEZA] Remover stickers/mascotes com fundo opaco ou desconexos em cenas dramáticas e corrigir crop de marcas d'água de terceiros (gemini-4-argon)
- prova: Stickers com falha de transparência/contexto em eu-perdi-minha-memória_cap1_20261030 (q06, q13, q14 caixa preta/cinza opaca) e attack-on-titan_cap1_20261030 (q04 cobrindo @cartuchoreact, q10); marcas d'água de terceiros visíveis em attack-on-titan_cap1_20261030 (q01-q03 'NERD DAY'), sem-obra-2a4dba_cap1_20261030 (q01-q18 'NEXHWA OFICIAL') e jujutsu-kaisen_cap1_20261030 (q02-q18 '@animescomia').
- onde: Módulo de composição de vídeo / overlay de assets do canal e filtro de crop/delogo de bordas.
- como testar: Desativar a sobreposição de stickers/mascotes PNG ou validar canal alpha antes do overlay, e aplicar crop perimétrico de 6% a 10% na base/topo para eliminar 'NERD DAY', 'NEXHWA OFICIAL' e '@animescomia' conferindo folha de quadros q01 e q06.

## 31/10 06:55 PROPOSTA [CERTEZA] Desativar stickers/cursores PNG e travar margem mínima de 60 px nas palavras de impacto laterais (gemini-4-argon)
- prova: Stickers e cursores sobrepondo texto ou cortados na borda em sem-obra-a6ac68 (q01, q02), sem-obra-01ce63 (q13, q14), sem-obra-6f5f81 (q14) e sem-obra-ceafe2 (q14); palavras de destaque 'DESCOBRE' (sem-obra-a6ac68 q18) e 'NINGUÉM' (sem-obra-ceafe2 q14) a menos de 30–60 px da borda esquerda.
- onde: Renderizador de legendas/overlays de CORTES (geração do ASS/FFmpeg para legenda_impacto='lateral' e camada de stickers/marca d'água)
- como testar: Re-renderizar sem-obra-a6ac68 e sem-obra-ceafe2 sem camada de stickers e com clamp de x >= 60 e x <= 1020 no texto de impacto lateral, conferindo nos quadros q02, q14 e q18 se não há corte nem colisão com @marca.

## 31/10 06:55 PROPOSTA [CERTEZA] Evitar reciclagem de takes (efeito ping-pong) e inversão cronológica na montagem das cenas (gemini-4-argon)
- prova: Repetição de planos anteriores quebrando a continuidade física da ação em 4 Shorts: sem-obra-6f5f81 (q04 repete q01), sem-obra-a6ac68 (q04 repete q03 antes da massa crua em q05), sem-obra-01ce63 (q08/q09 e q14 voltam no tempo após creme já espalhado em q13) e sem-obra-ceafe2 (q07/q08 repetem a fuga de q02/q03 quando a voz diz 'vai encarar').
- onde: Seletor/montador de cortes de vídeo da linha CORTES (alinhamento de timestamps da fonte sem voltar atrás na timeline original)
- como testar: Exigir progressão monotônica de timestamps dos cortes da fonte (ou bloquear reuso de segmento já exibido) e validar nos vídeos gerados que nenhum take se repete.

## 31/10 08:19 PROPOSTA [CERTEZA] Corrigir detecção e cobertura de hardsub no rodapé e centro (evitar delogo estriado ou falha de caixa) (gemini-4-argon)
- prova: the-greatest-estate-developer_cap1_20261030 (q01, q03, q04, q08), sem-obra-d45121_cap1_20261030 (q01, q08, q09, q13, q14) e sem-obra-554315_cap1_20261030 (q01, q04, q07) apresentam legenda original vazando abaixo de y=1580 ou no centro sob a nossa legenda, além de faixas de esticamento vertical (smear/delogo) deformando personagens.
- onde: Módulo de detecção/máscara de hardsub no pipeline de vídeo (cálculo de bounding box da visão e filtro de cobertura sobre a caixa exata das letras)
- como testar: Rodar a detecção de hardsub nos frames q01, q03 e q08 dos 3 Shorts afetados e gerar folha de quadros confirmando cobertura exata do texto original sem vazamento lateral/inferior e sem faixa de distorção no centro.

## 31/10 08:19 PROPOSTA [CERTEZA] Remover marca d'água '@inventoreact' e stickers de reação no terço superior (gemini-4-argon)
- prova: the-greatest-estate-developer_cap1_20261030 (q05, q06, q12, q13) e sem-obra-d45121_cap1_20261030 (q03 a q18) exibem '@inventoreact' e avatares de terceiros visíveis no vídeo final, violando a regra fixa de zero @ na tela.
- onde: Etapa de limpeza/crop perimétrico da fonte ou máscara de watermark do parceiro antes da composição final
- como testar: Processar um corte de fonte com '@inventoreact' no topo e inspecionar q03–q12 garantindo remoção completa do @ e do sticker sem cortar cabeças (headroom >= 60 px).

## 31/10 08:19 PROPOSTA [CERTEZA] Desativar ou deslocar palavras de impacto centralizadas para não cobrir rostos nem duplicar legenda (gemini-4-argon)
- prova: sem-obra-226fd4_cap1_20261030 (q06 'NINGUÉM') e sem-obra-554315_cap1_20261030 (q17 'IMPLORARAM') exibem palavras gigantes no centro da tela cobrindo o rosto/foco principal e repetindo a legenda inferior simultaneamente.
- onde: Renderizador de legenda/palavras de impacto (configuração de 'legenda_impacto: lateral')
- como testar: Renderizar trechos com palavras de impacto de sem-obra-554315_cap1_20261030 (q17) e verificar se a palavra sai integrada ou lateralizada na zona segura sem sobrepor o centro do quadro nem duplicar a legenda base.

## 31/10 09:25 PROPOSTA [CERTEZA] Fixar posição da marca d'água (@canal) no topo seguro com contorno preto forte desde o frame 0.0 (gemini-4-argon)
- prova: Em sem-obra-1a38bf_cap1_20261030 (q13.jpg a q18.jpg) a marca '@inovaremanhwabr' colide exatamente com a coordenada da legenda da narração e cobre o queixo em q05.jpg; em sem-obra-41129c_cap1_20261030 (q18.jpg) e sem-obra-282924_cap1_20261030 (q06.jpg, q15.jpg) '@gamenoturnobr' fica ilegível sobre fundos/clarões brancos e está ausente em q01-q02.
- onde: Pipeline de renderização/overlay de vídeo (função que desenha o drawtext/ASS da marca d'água @canal)
- como testar: Renderizar novamente sem-obra-1a38bf_cap1_20261030 e sem-obra-282924_cap1_20261030 e verificar em q01, q06 e q13-q18 se o @canal permanece fixo no topo seguro (y=160..220), visível desde 0.0s, com borda/sombra preta >= 3px legível sobre fundo branco e longe da faixa de legenda.

## 31/10 09:25 PROPOSTA [CERTEZA] Detectar ou descartar tomadas finais com cursor de mouse / artefatos de gravação de tela na fonte (gemini-4-argon)
- prova: Em sem-obra-41129c_cap1_20261030 (q18.jpg) e sem-obra-282924_cap1_20261030 (q18.jpg), um ícone de mãozinha/ponteiro de clique do sistema operacional aparece bem no centro da tela sobre o objeto em destaque no último quadro.
- onde: Extração de vídeo da fonte / seleção de frames da última cena (cortes_pipeline / extrator da fonte)
- como testar: Inspecionar o vídeo-fonte de sem-obra-41129c e sem-obra-282924 nos segundos finais para confirmar se o cursor vem de overlay de end-screen/player capturado ou da fonte, cortando 0.5s antes do aparecimento do cursor ou filtrando na seleção de cenas.

## 31/10 09:25 PROPOSTA [GOSTO] Sustentar a headline de gancho no topo até o fim completo da Cena 1 / primeira oração (gemini-4-argon)
- prova: Em sem-obra-1a38bf_cap1_20261030 (q03.jpg, 3.87s) o texto 'O CIÚME QUASE DESTRUIU ELA' desaparece antes do fim da Cena 1; em sem-obra-282924_cap1_20261030 (q03.jpg, 3.96s) 'ESSE OBJETO DESAFIA A GRAVIDADE' some abruptamente antes do fim da oração falada.
- onde: Cálculo de duração do overlay de título/gancho de topo na Cena 1
- como testar: Vincular o tempo de fim do texto de gancho ao timestamp real de término da primeira frase/Cena 1 (em vez de duração fixa curta) e checar q03.jpg em ambos os Shorts.

## 31/10 10:41 PROPOSTA [CERTEZA] Travar stickers e letreiros soltos de template (anime, 'REVELA', 'NOSSO') fora de canais de manhwa (cw/claude-sonnet-5-5)
- prova: 3db133 (pesca real) q04/q05/q14/q15: sticker de personagem anime e 'REVELA' sobre a isca e a mão, cortado na borda. dfdc16 (dorama histórico) q07/q15: 'NOSSO' sobre o rosto do menino e sticker de garota de anime. Os dois Shorts não são manhwa, e o sticker ainda cobre o objeto central da narração.
- onde: Função que sorteia/aplica overlays PNG e letreiros de impacto no render da linha CORTES (procurar por 'sticker', 'impacto' ou 'legenda_impacto' no módulo de render); provável condicionar ao nicho da obra.
- como testar: Gerar 1 Short de pesca/curiosidade e 1 dorama com o mesmo lote e conferir na folha de quadros que nenhum sticker ou letreiro solto aparece fora de manhwa; controle positivo: um manhwa continua com os stickers.

## 31/10 10:41 PROPOSTA [CERTEZA] Confinar marca d'água, sticker e letreiro na zona segura e longe do rosto (cw/claude-sonnet-5-5)
- prova: c19f00 q07-q12: @inovaremanhwabr em y=1600 a 1700 (abaixo de y=1580) e q06 sobre a legenda. onmyou q04 etc.: @manhwareact-ia em y≈520 na testa dos personagens. 3db133 q04/q05/q14: sticker acima de y=150 e a menos de 60 px da lateral. Padrão em 4 de 4 Shorts.
- onde: Função que calcula a posição da marca d'água e dos overlays no render (constantes de y e margem lateral); validar contra a regra 11 do APRENDIDO (y de 150 a 1580, margem de 60 px).
- como testar: Renderizar 4 Shorts de nichos diferentes e medir por script a caixa da marca d'água em q01, q07 e q12: deve ficar em y entre 160 e 220 e x entre 60 e 1020.

## 31/10 10:41 PROPOSTA [GOSTO] Legenda palavra a palavra no centro vertical cobre o rosto (cw/claude-sonnet-5-5)
- prova: onmyou q01-q13 e q18: legenda em y≈960 cobrindo nariz e boca em todos os closes. Só 1 Short do lote, então vale como observação; as regras da dona preferem legenda de impacto de lado.
- onde: Posição vertical da legenda palavra a palavra no render (parâmetro de y da legenda em cortes_legenda ou equivalente).
- como testar: Subir a legenda para o terço inferior só em planos de close e comparar a nota do júri em 5 Shorts; medir 1 mudança por vez.

## 31/10 10:41 PROPOSTA [GOSTO] Cena 1 sem planos vazios e topo contínuo; verificar sincronia dos cortes (cw/claude-sonnet-5-5)
- prova: c19f00 q01-q02: pan em escadaria vazia por 3,6 s enquanto a voz já chama o protagonista; 3db133 q14/q15: corte para a isca entra com atraso em relação a 'o anzol'; título/tarja do topo some no q02 em dfdc16 e onmyou.
- onde: Seleção do trecho inicial da cena 1 e o tempo de exibição da tarja do topo no render; função de alinhamento cena-fala.
- como testar: Comparar o tempo de aparição do protagonista contra a primeira palavra da narração em 5 Shorts e checar se a tarja dura até o corte para a cena 2.

## 31/10 11:47 PROPOSTA [CERTEZA] Desativar ou recortar fundo opaco de stickers PNG e impedir colisão com marca d'água (@canal) (gemini-4-argon)
- prova: Em sem-obra-843743 (q06 e q13) e sem-obra-bab5ba (q10), stickers de anime surgem com fundo retangular preto/cinza opaco no topo esquerdo (y < 150), tampando a marca d'água oficial (@assistinvestimentos / @esportenoturno) e a cabeça dos personagens.
- onde: Pipeline de composição de vídeo / filtro de inserção de stickers e overlays
- como testar: Rodar renderização de teste nos Shorts sem-obra-843743 e sem-obra-bab5ba verificando nos quadros q06, q10 e q13 se a marca d'água e os rostos permanecem 100% livres e sem stickers fora de nicho ou com fundo opaco.

## 31/10 11:47 PROPOSTA [CERTEZA] Respeitar margem lateral mínima de 60px e evitar duplicação na legenda de impacto lateral (gemini-4-argon)
- prova: Após ativar legenda_impacto='lateral', o texto estilizado ficou colado ou cortado na borda esquerda (x < 60px) em sem-obra-a4b64b (q18, letra 'T' de 'TRAÍRA' cortada) e em sem-obra-bab5ba (q13, palavra 'ATACAM' duplicada e com margem < 60px).
- onde: Gerador de legenda ASS / posicionamento de legenda_impacto lateral
- como testar: Renderizar legendas com palavras de impacto longas e inspecionar o frame para garantir x >= 60px e x <= 1020px sem sobreposição ou duplicação.

## 31/10 12:55 PROPOSTA [CERTEZA] Travar safe zone (y >= 150, margem x >= 60 px), camada única de texto e banir stickers opacos/finais (gemini-4-argon)
- prova: sem-obra-23f414 (q01.jpg dois títulos sobrepostos no topo acima de y=150; q07.jpg e q13.jpg colisão de camadas na legenda; q14.jpg sticker com fundo branco opaco), sem-obra-1fd34f (q01.jpg/q02.jpg título em y≈115; q17.jpg destaque a 40 px da borda; q18.jpg sticker de like no centro) e sem-obra-bd075c (q17.jpg 'VIROU' a 25-30 px da borda).
- onde: Renderizador de legendas/títulos e compositor de overlays do pipeline CORTES
- como testar: Renderizar novamente sem-obra-23f414, sem-obra-1fd34f e sem-obra-bd075c e inspecionar q01, q07, q13, q14, q17 e q18 garantindo bounding boxes dentro de x=[60, 1020] e y=[150, 1580], sem colisão de linhas nem PNGs sem alfa.

## 31/10 12:55 PROPOSTA [CERTEZA] Bloquear buracos pretos, canvas vazio no pan, repetição de takes e planos parados > 4s (gemini-4-argon)
- prova: sem-obra-bd075c (q10.jpg tela preta sem vídeo por gap de mídia; q08.jpg plano fixo por > 6s com 6,2% de movimento), sem-obra-f28742 (q09.jpg pan vertical expôs 35% de canvas branco; q10.jpg repetição de q07; q16.jpg plano congelado por ~6s) e sem-obra-1fd34f (q08-q11 repetem exatamente q04-q07; q16.jpg repete q07 pela 3ª vez).
- onde: Montador de cortes / seleção de B-roll e cálculo de crop/pan 9:16 do pipeline CORTES
- como testar: Validar no montador que nenhum clip seja reutilizado no mesmo Short, que o pan/crop mantenha 100% do quadro 1080x1920 preenchido com luma > 0 em todas as cenas e que tomadas com movimento baixo > 4s recebam corte ou zoom dinâmico.

## 11/11 10:31 PROPOSTA [CERTEZA] Sticker/card de palavra não pode cobrir rosto nem a legenda embaixo (cw/claude-sonnet-5-5)
- prova: Repete em 4 Shorts: nen-2 q01 (queixo), q05 (testa), q12 (rosto inteiro, com camada 'CINCO' duplicada); fbe400 q03 ('MICHAEL' nos olhos), q08 (selo no rosto), q10 ('IMAGINA' sobre a cabeça); f741be q03 ('TIAGO' nos olhos), q08 (sticker sobre a linha da legenda); 111e6f q14 ('CARNE' sobre o olho do peixe).
- onde: Módulo que posiciona stickers e cards da legenda palavra a palavra em cortes (posição vertical/lateral e camadas ativas). Função provável: a que calcula y/x do sticker.
- como testar: Rodar detecção de rosto nos quadros de 5 Shorts, calcular a sobreposição com a caixa do sticker e, se passar de ~10%, deslocar para a área livre. Conferir também que só 1 camada de palavra fica ativa por vez (nen-2 q08 e q12 mostram duplicadas). Comparar na folha de quadros antes e depois.

## 11/11 10:31 PROPOSTA [GOSTO] Card do topo cobrindo a marca d'água do parceiro (cw/claude-sonnet-5-5)
- prova: fbe400 q03 e q04: 'IMPORTANTE MICHAEL' esconde quase toda a '@historiasemframes-emerson'. f741be q03: o card 'TIAGO' encavala na mesma marca.
- onde: Posição do card de topo (y) no layout do título e do card.
- como testar: Medir a faixa onde a marca costuma aparecer nos canais parceiros (topo esquerdo) e subir ou descer o card para fora dela. Medir em 10 Shorts e checar que a marca fica legível.

## 11/11 10:31 PROPOSTA [CERTEZA] Imagem fora do tempo ou errada para o que a voz fala (cw/claude-sonnet-5-5)
- prova: nen-2 q16-q18: a máscara só cai depois da frase 'minha máscara caiu', e q11 mostra uma caneta enquanto a voz fala do computador. f741be q16-q17: prato parado por ~8 s e a janela do quintal só entra em q18, depois da fala. fbe400 q07-q08: o cadáver aparece antes da queda narrada; q09 corta para o GTA RP antes de a frase acabar. 111e6f q02/q05: aparece cascudo e cuiú-cuiú em vez de abrótea e dourado.
- onde: Mapeamento cena→trecho de fala e escolha de cortes (seleção de cena por palavra-chave e a margem de corte no fim de cada cena).
- como testar: Para 5 Shorts, comparar o timestamp da palavra-chave de cada frase (já medido na voz) com o início da cena escolhida. Se a cena começar mais de 0,5 s depois ou antes, ajustar o corte. Rodar o júri de movimento no mesmo lote.

## 11/11 10:31 PROPOSTA [CERTEZA] Confirmar pelo log o caso da tarja ausente em sem-obra-111e6f (cw/claude-sonnet-5-5)
- prova: O júri diz que a fonte tem legenda queimada no centro ('A MOQUECA', 'GIGANTE PIRARUCU') sem cobertura, gerando duas camadas de texto. Pela lição de 26/10, isso só vale se o log do Short disser que a visão NÃO leu legenda.
- onde: Log do Short 111e6f_cap1_20261107, linha '[hardsub]', e a etapa de detecção de legenda queimada.
- como testar: Ler o log. Se mostrar 'só 0/6', rodar a folha de quadros em resolução >= 720 px, como no controle negativo de 26/10, para ver se a legenda do centro foi perdida. Se o log mostrar texto lido, o júri errou e não há defeito.

## 11/11 11:47 PROPOSTA [CERTEZA] Impedir que adesivos/legenda de destaque cubram rosto ou focinho (cw/claude-sonnet-5-5)
- prova: 9d0daf q01 ('ESSE PANACA' sobre o rosto do Andy) e q03 ('DEPOIS' sobre os olhos da Fuuko); nen-3 q06 ('CEM' sobre a cabeça e o focinho do dragão); think q05 (QUATRO sobre peito e queixo). 3 Shorts de 4 do lote.
- onde: módulo de legenda palavra a palavra / posicionamento das palavras de impacto (cortes_legenda, função que escolhe x,y do destaque) e a visão que detecta rosto
- como testar: Rodar os 3 Shorts acima de novo e conferir em folha de quadros que nenhum destaque encosta em rosto/focinho; incluir um Short sem personagens como controle negativo.

## 11/11 11:47 PROPOSTA [CERTEZA] Contraste mínimo das palavras de destaque (cores escuras sobre fundo escuro) (cw/claude-sonnet-5-5)
- prova: think q06 (cinza-oliva sobre paletó escuro), q13 (amarelo-oliva sobre blazer preto), q14 (vermelho apagado, corpo < 34 px); 6ec270 q10 e q02 (branco/ciano sem contorno sobre aço e surimi); nen-3 q03 e q06 (verde e laranja escuros sobre o animal). 3 Shorts.
- onde: paleta de cores por personagem e contorno das palavras (cortes_legenda): forçar traçado escuro grosso e restringir à paleta amarelo/branco quando a luminância do fundo for parecida
- como testar: Calcular razão de contraste entre cor da palavra e a região do quadro atrás dela; rejeitar < 4,5 e trocar cor; reprocessar think e nen-3.

## 11/11 11:47 PROPOSTA [CERTEZA] Palavras e cards cortados na borda da tela / sobrepostos à marca d'água (cw/claude-sonnet-5-5)
- prova: 6ec270 q15 ('PEPPER' cortado na lateral direita, margem 0 px); 9d0daf q12 ('mpurra' cortado à esquerda) e q02 (HUD 'IMPORTANTE ANDY' sobre @cenareact); nen-3 q04 (card 'ALERTA ATACA' sobre @bichonoturnobr).
- onde: cálculo da caixa da palavra e dos cards (largura máxima com margem de 60 px) e z-order da marca d'água
- como testar: Teste automático que mede a caixa de cada palavra/card renderizado e falha se x < 60 ou x+w > 1020 ou se intersecta a região da marca.

## 11/11 11:47 PROPOSTA [GOSTO] Cards de HUD com atributos fictícios (IMPORTANTE, ALERTA, PODER) com texto errado (cw/claude-sonnet-5-5)
- prova: nen-3 q04 ('ALERTA ATACA') e 9d0daf q02/q17 ('IMPORTANTE ANDY', 'PROTAGONISTA FUUKO' com personagem trocado). A dona prefere palavras de impacto maiores, não cards de atributo.
- onde: gerador de cards/HUD; considerar desligar ou checar o nome do personagem contra o quadro
- como testar: Desligar os cards num lote pequeno e comparar nota do júri e % assistido contra o lote com cards.

## 11/11 12:59 PROPOSTA [CERTEZA] Corrigir detecção de hardsub para legendas estilizadas/coloridas e em múltiplos pontos do vídeo (gemini-4-argon)
- prova: Nos 4 Shorts do lote (sem-obra-66969c q09/q10, sem-obra-5fbaab q01/q10, damascus-steel q08, questões-questionáveis-8 q13/q14/q16), a legenda queimada da fonte ficou visível e colidiu com a nossa legenda sem ser coberta pelo delogo/apagado.
- onde: Pipeline de detecção de hardsub / cálculo de caixa de delogo em cortes
- como testar: Rodar a detecção de hardsub nos 4 vídeos-fonte deste lote e gerar folha de quadros verificando se 100% das legendas originais foram detectadas e cobertas na faixa exata.

## 11/11 12:59 PROPOSTA [CERTEZA] Travar camada única de legenda sem inclinação 3D e respeitar margem lateral de 60px e zona da marca d'água (gemini-4-argon)
- prova: Duas legendas simultâneas/sobrepostas em sem-obra-66969c (q10), sem-obra-5fbaab (q09) e questões-questionáveis-8 (q07); texto cortado na borda em damascus-steel (q03 'MOANA', q06 'MEDIEVAL'); colisão com marca d'água em questões-questionáveis-8 (q03, q07, q10) e sem-obra-5fbaab (q10).
- onde: Renderizador de legendas ASS/FFmpeg e posicionador de stickers/HUD da linha CORTES
- como testar: Renderizar sem-obra-5fbaab e damascus-steel conferindo nos quadros q03, q06, q07, q09 e q10 ausência de sobreposição dupla, margem lateral >= 60px e separação da marca d'água.

## 11/11 14:08 PROPOSTA [CERTEZA] Ignorar topo (y < 30% da altura) na detecção de hardsub para não ancorar cobertura no título da fonte (gemini-4-argon)
- prova: gta_cap1_20261107 (q01-q16: cobertura foi para o topo enquanto a legenda 'O GTA 6 CUSTA / PADRÃO' ficou exposta no rodapé) e sem-obra-bb3ddb_cap1_20261107 (q01-q16: título 'O Limite da Mente Humana' no topo acima de y=150 e legenda 'Vamos imaginar tentar ensinar' exposta embaixo).
- onde: Detector de legenda queimada (hardsub) / cálculo de bounding box da cobertura (delogo/tarja) no pipeline de vídeo
- como testar: Rodar a detecção de hardsub nos fontes de gta_cap1_20261107 e sem-obra-bb3ddb_cap1_20261107 restringindo candidatos de legenda à metade/terço inferior (y >= 0.45*H) e verificar na folha de quadros se o delogo/cobertura recai exatamente sobre a legenda do rodapé.

## 11/11 14:08 PROPOSTA [CERTEZA] Remover cor azul-escuro/tons escuros da paleta de palavras de destaque e travar zona segura (x: 60..1020, y: 150..1580) com camada única (gemini-4-argon)
- prova: Contraste ilegível em azul-escuro sobre fundo escuro em 3 Shorts: gta_cap1_20261107 (q02 'TÔ', q05 '90', q07 'FALTAR'), sem-obra-bb3ddb_cap1_20261107 (q10 'NESSA') e and_cap1_20261107 (q02 'SETENTA'). Vazamento de margem e dupla camada em sem-obra-1b054f_cap1_20261107 (q01-q03 'QUASE'/'RORAIMA' cortado em x<60) e and_cap1_20261107 (q01 y>1750, q04 'poss' cortado na borda esquerda).
- onde: Renderizador de legenda/stickers dinâmicos (definição de paleta de cores de destaque e clamp de bounding box na composição)
- como testar: Restringir a paleta de preenchimento de destaques a cores claras de alto contraste (#FFFF00, #FFDD00, #FFFFFF, #00FFFF) com contorno preto >= 8px, desativar sobreposição simultânea de sticker+legenda no mesmo timestamp e aplicar clamp de coordenadas dentro de x=[60, 1020] e y=[150, 1580]; re-renderizar and_cap1_20261107 e sem-obra-1b054f_cap1_20261107 e inspecionar q01-q05.

## 11/11 14:08 PROPOSTA [CERTEZA] Cortar quadros finais escuros (luminância média < limiar) ou com tela de encerramento ('Se inscreve') nos últimos 3s da fonte (gemini-4-argon)
- prova: gta_cap1_20261107 (q18 exibe tela final escura do canal de origem 'GRANA NERD / VÍDEO COMPLETO NO CANAL / SE INSCREVE'), sem-obra-bb3ddb_cap1_20261107 (q18 severamente subexposto/quase preto antes do loop) e and_cap1_20261107 (q17 janela do player preta vazia com sobra de recorte).
- onde: Seleção/trim de cenas do vídeo-fonte (corte do trecho final antes da montagem das cenas)
- como testar: No pré-processamento dos cortes da fonte, inspecionar os últimos 3s procurando queda brusca de luminância (quadro quase preto) ou OCR de termos de outro ('inscreva', 'inscreve', 'vídeo completo') e antecipar o ponto de saída (trim out) da cena final; testar em gta_cap1_20261107 e and_cap1_20261107.

## 11/11 15:15 PROPOSTA [CERTEZA] Corrigir auto-fit lateral, remoção de camada anterior e trava de y<=1450 na legenda palavra-a-palavra (gemini-4-argon)
- prova: Em what-the-popemobile-looks-like-inside_cap1_20261107 (q04, q05, q07) a palavra 'DIFICILMENTE' ultrapassa a borda direita cortando 'TE' e sobrepõe a palavra anterior ('VÃO'/'POR'); em sem-obra-9e94d9_cap1_20261107 (q16, q17, q18) 'mpletamente perdi' e 'ontato com homer' saem decepadas nas duas bordas e posicionadas abaixo de y=1580.
- onde: gerador de legenda ASS / renderizador de legendas do pipeline CORTES (cálculo de bounding box, quebra/auto-fit para x entre 60 e 1020, y entre 1000 e 1450 e limpeza do evento anterior)
- como testar: Re-renderizar a legenda de what-the-popemobile-looks-like-inside_cap1_20261107 e sem-obra-9e94d9_cap1_20261107 e inspecionar q04, q07, q16, q17 e q18 verificando margem mínima de 60px, ausência de sobreposição e y <= 1450.

## 11/11 15:15 PROPOSTA [CERTEZA] Revisar detecção de hardsub colorido/borda inferior na visão para não perder cobertura de legenda queimada (gemini-4-argon)
- prova: Em what-the-popemobile-looks-like-inside_cap1_20261107 (q04, q10, q14) e sem-obra-ba2e1d_cap1_20261107 (q01, q03, q05, q06), a legenda queimada colorida da fonte ficou 100% descoberta colidindo com a nossa legenda.
- onde: módulo de detecção de hardsub / visão do pipeline CORTES (amostragem de quadros e filtro de caixa de texto queimado)
- como testar: Rodar o detector de hardsub nos vídeos-fonte de what-the-popemobile-looks-like-inside_cap1_20261107 e sem-obra-ba2e1d_cap1_20261107 com folha de 6 quadros e confirmar que a coordenada da legenda original é detectada e coberta com delogo no tamanho exato.

## 11/11 16:30 PROPOSTA [CERTEZA] Auto-fit lateral da legenda: palavra nunca sai da margem de 60 px (cw/claude-sonnet-5-5)
- prova: Letra inicial ou final cortada em 4 Shorts do lote: a68f1e q16 ('PROVOQUEI' vira 'ROVOQUEI' em x=0), nen q18 ('oção do perrengu' cortado nas duas laterais), 1ed8b7 q01 ('MAGNATA' com M fora da margem) e pepesi q13/q15 (mascote cobrindo o 'C', caixa a menos de 60 px da borda direita).
- onde: função que renderiza a legenda palavra a palavra e calcula o tamanho da fonte (módulo de legenda/ASS do pipeline CORTES). Procurar onde a palavra de destaque é aumentada.
- como testar: Gerar a legenda de 3 Shorts com palavras longas (PROVOQUEI, MAGNATA, CURTINDO), medir a caixa de cada palavra e exigir x_min ≥ 60 e x_max ≤ 1020. Se estourar, reduzir a fonte da palavra até caber. Passar pela folha de quadros antes de ligar.

## 11/11 16:30 PROPOSTA [GOSTO] Palavra de destaque fora do rosto e das mãos (cw/claude-sonnet-5-5)
- prova: Legenda sobre boca, queixo ou rosto em a68f1e q10 ('ME CERCOU' no rosto do Motoqueiro Fantasma), q12 ('DIRETO' no queixo do policial), nen q07 ('ANEL' em boca e nariz) e 1ed8b7 q06 ('MINHA' na boca da personagem).
- onde: posicionamento vertical da legenda e do destaque. Usar a detecção de rosto que já existe no pipeline, se houver, para deslocar a palavra para a faixa do peito, sem mudar a fonte.
- como testar: Aplicar só nos Shorts com close, comparar a nota de legibilidade do júri e conferir à mão que a palavra não saiu da faixa segura. É questão de gosto, então testar uma coisa por vez.

## 11/11 16:30 PROPOSTA [GOSTO] Texto da fonte vazando pelo delogo em parte dos quadros (cw/claude-sonnet-5-5)
- prova: a68f1e q06/q16 mostram a legenda amarela da fonte visível ao lado do desfoque. nen q01/q03/q06-q16 mostram 'A NOIVA QUE SE TRANSFORMOU EM ZUMBI' e 'ELE PEGA UM PREGO DO CHÃO E TENTA' legíveis, com o desfoque cortando o texto ao meio. A prova é só do júri; falta o log do Short para confirmar que a visão leu a legenda ali.
- onde: caixa de cobertura calculada pela visão (cortes_ajustes tarja/delogo) e a medição da caixa das letras. Nos dois Shorts, comparar a altura medida com a altura real da legenda.
- como testar: Abrir o log do nen_cap1 e do a68f1e, ver se há '[hardsub]' com leitura OK e qual caixa foi usada, e rodar a folha de quadros em resolução ≥720 px. Se a caixa estiver menor que a legenda, corrigir a medição. Não propor tarja grande (regra fixa da dona).

## 11/11 16:30 PROPOSTA [CERTEZA] Quadros escuros e faixas pretas quando o clipe 16:9 entra no vertical (cw/claude-sonnet-5-5)
- prova: a68f1e q13 (filme espremido no rodapé com mais de 60% de preto), q14 (fundo de nebulosa sem relação com a cena) e q15 (plano turvo); nen q16 (quase preto); 1ed8b7 q16 (clipe 16:9 com faixas amplas no topo e na base). O pepesi q12 tem whiteout no flash de transição.
- onde: montagem de cena (preenchimento vertical do clipe horizontal), escolha de imagem de reserva quando falta tomada, e o efeito de flash de transição.
- como testar: Calcular o brilho médio por quadro na saída e segurar o Short se algum quadro ficar abaixo de ~15 ou acima de ~240 por mais de 0,5 s, ou se o clipe ocupar menos de 80% da altura. Revisar no log o que gerou a imagem de nebulosa.

## 11/11 17:40 PROPOSTA [CERTEZA] Card 'LOCAL MUNDO' disparado pela palavra 'mundo' e cobrindo o título do topo (cw/claude-sonnet-5-5)
- prova: e42902 q07-q09 (card com pin no topo após 'todo mundo sumiu') e a57656 q08, q10 e q11 (card cobre o título fixo, sobra só 'LU', texto truncado 'MUN').
- onde: Gerador de stickers/cards por palavra-chave (módulo de overlays do pipeline CORTES). Provável gatilho 'local/mundo' sem checar contexto, e posição do card sem evitar a zona do título (y=150 a 300).
- como testar: Rodar o gerador nos roteiros dos dois Shorts. Esperado: 'mundo' como gíria não gera card de localização, e nenhum card se sobrepõe ao título do topo. Conferir com a folha do topo (D:\tmp\folha_topo.py) em todos os Shorts do dia.

## 11/11 17:40 PROPOSTA [CERTEZA] Legenda/sticker sobre boca e rosto em close (cw/claude-sonnet-5-5)
- prova: e42902 q02 ('UM GRITO' na cabeça) e q03 ('QUEM VAI' e megafone na boca); 1ed8b7 q06 ('MINHA' sobre boca e queixo); a57656 q04 ('SUPER' e sticker 'TÁ' no queixo do Luffy).
- onde: Posicionamento da legenda palavra a palavra e dos stickers (função que calcula o y/x da legenda). Falta desvio quando há rosto na faixa da legenda.
- como testar: Detectar rosto por quadro (ou usar a posição já medida pela visão). Quando o rosto cair na faixa, deslocar a legenda para o peito ou para a área neutra. Reprocessar e1/e42902 q02-q03 e 1ed8b7 q06 e conferir que boca e queixo ficam livres.

## 11/11 17:40 PROPOSTA [CERTEZA] Contraste mínimo das palavras de impacto e cores por personagem (cw/claude-sonnet-5-5)
- prova: 1ed8b7 q08 ('MANSÃO' verde-escuro com contorno verde sobre paletó azul-marinho) e e42902 q05 ('MILHÕES!' marrom/âmbar sem traço sobre roupa vermelha).
- onde: Paleta de cores/contorno das palavras de destaque (função que escolhe cor por personagem ou palavra).
- como testar: Calcular o contraste da cor de preenchimento contra a cor média do quadro e forçar contorno preto ou clarear o preenchimento abaixo de um limite. Reprocessar os dois quadros e conferir a leitura.

## 11/11 17:40 PROPOSTA [GOSTO] Abertura passiva nos 2 primeiros segundos (rosto e conflito só depois de 2 s) (cw/claude-sonnet-5-5)
- prova: 1ed8b7 q01 (sala vazia e quadro distante enquanto o título promete 'chacota da família') e e42902 q01 e q02 (garota deitada; a mulher do megafone só aparece em 2.27 s, apesar da narração já falar dos 10 milhões).
- onde: Seleção da cena de abertura / escolha do primeiro corte (corte de cena do pipeline).
- como testar: Medir em mais lotes se a abertura sem rosto ou conflito correlaciona com % assistido menor. Se sim, preferir como primeira tomada a cena com rosto e movimento mais próxima da fala do gancho. Testar em 1 canal e comparar a retenção.

## 11/11 17:40 PROPOSTA [CERTEZA] Trechos escuros, desfocados ou com faixas pretas amplas (cw/claude-sonnet-5-5)
- prova: e42902 q15 (chão desfocado e escuro durante 'TUDO'), 1ed8b7 q16 (clipe 16:9 com faixas pretas no meio do 9:16) e 4f3192 q14 (arquibancada quase preta).
- onde: Seleção/recorte de tomadas (filtro de luminância mínima por cena e preenchimento vertical de clipes 16:9).
- como testar: Descartar ou encurtar tomadas com luminância média abaixo de um limite e fazer reenquadramento com preenchimento em clipes horizontais. Reprocessar os 3 Shorts e conferir os quadros apontados.

## 11/11 19:31 PROPOSTA [CERTEZA] Travar paleta de cores claras, opacidade 100% e corte seco na legenda de impacto (gemini-4-argon)
- prova: Em sem-obra-36a60f (q07.jpg 'MINHA' em vermelho escuro, q10.jpg 'ALGO' em cinza/vinho, q11.jpg 'E AÍ' semi-transparente), sem-obra-4667a3 (q03.jpg 'LIGADO' transparente, q05.jpg 'GENTE' azul-marinho, q07.jpg 'CINCO' vinho com ghosting em q08.jpg, q13.jpg 'DIZEM' marrom) e never-touch-these-animals (q09.jpg 'RÃ-DARDO-DOURADA' vinho <32px, q16.jpg 'NENHUMA' laranja opaco), os stickers/palavras saíram escuros ou translúcidos.
- onde: D:\recapd-ambientes\producao\bin\fx_subtitles.py
- como testar: Renderizar trecho de sem-obra-36a60f e sem-obra-4667a3 e extrair folha de quadros confirmando preenchimento 100% opaco em amarelo/branco com contorno preto espesso, corpo >= 36 px e remoção imediata da palavra anterior sem ghosting.

## 11/11 19:31 PROPOSTA [CERTEZA] Corrigir detecção e caixa vertical da legenda queimada no rodapé abaixo de y=1580 (gemini-4-argon)
- prova: Legenda original da fonte ficou visível ou cortada ao meio no rodapé (y=1580 a 1800) em 3 Shorts do lote: sem-obra-36a60f (q01.jpg, q09.jpg, q10.jpg), sem-obra-4667a3 (q02.jpg, q05.jpg a q18.jpg) e never-touch-these-animals (q01.jpg, q04.jpg, q07.jpg, q09.jpg com delogo desalinhado, q14.jpg, q15.jpg).
- onde: D:\recapd-ambientes\producao\bin\anime_hardsub_detect.py e parceiro_marca.py
- como testar: Rodar detecção de hardsub nas fontes desses 3 Shorts, verificar nos logs se a faixa y inferior até 1800 px é capturada em >= 2 de 6 quadros e checar na folha de quadros se o apagado/tarja cobre 100% da altura exata das letras sem cortar ao meio.

## 11/11 19:31 PROPOSTA [CERTEZA] Remover cards de transição/alerta truncados e sincronizar troca de cena com timestamps da fala (gemini-4-argon)
- prova: Overlays gráficos invadiram ou truncaram texto e atrasaram cortes em 2 Shorts: never-touch-these-animals (q03.jpg resquício 'DE', q06.jpg 'ALERTA DRAGÃO' entrando aos 8.7s sobre o card 3 antes do fim da fala do polvo, q12.jpg quadrado '[0]' solto) e sem-obra-36a60f (q16.jpg legenda duplicada no rodapé y>1580 e q17.jpg caixa cortada 'ALERTA PERI').
- onde: D:\recapd-ambientes\producao\bin\anime_segments.py e fx_subtitles.py
- como testar: Gerar novamente os Shorts sem-obra-36a60f e never-touch-these-animals e inspecionar q03, q06, q12, q16 e q17 garantindo ausência de tags truncadas/residuais, legenda sempre acima de y=1580 e corte de cena cravado no fim do áudio de cada frase.

## 11/11 22:05 PROPOSTA [CERTEZA] Eliminar ghosting/sobreposição de palavras, cores escuras e cobertura de rosto no gerador ASS (gemini-4-argon)
- prova: Texto fantasma e colisão de palavras simultâneas em sem-obra-4d4db7 (q06 'APRESENTAÇÃO' sob 'SOLO'), sem-obra-66b167 (q02 'COLOSSAL' sobre 'COM O PROTA', q03 'DESCOBRINDO', q04 'PRÊMIO' sobre 'COLOSSAL') e sem-obra-8d5a76 (q04); cores translúcidas/escuras sem leitura em sem-obra-4d4db7 (q10 'JURO' marrom) e sem-obra-0e3c03 (q07 verde claro, q08 invisível, q13 vermelho escuro); legenda sobre olhos/boca em sem-obra-66b167 (q02), sem-obra-0e3c03 (q05, q13) e sem-obra-8d5a76 (q02, q04).
- onde: Módulo de geração de legendas (.ass) do pipeline de cortes (ex.: cortes_legenda.py / função de montagem de eventos dialogue ASS)
- como testar: Forçar corte seco (End do evento anterior <= Start do próximo, sem fade/alpha residual), travar paleta em branco (#FFFFFF) e amarelo (#FFFF00/#FFDD00) com opacidade 100% e contorno preto 8-14px, ancorar Y na faixa 1000-1450 (margem X >= 60px) e re-renderizar sem-obra-66b167 e sem-obra-0e3c03 conferindo q02-q13.

## 11/11 22:05 PROPOSTA [CERTEZA] Corrigir falha de detecção/aplicação de cobertura sobre hardsub e títulos queimados da fonte (gemini-4-argon)
- prova: Texto queimado original visível e colidindo com a nossa legenda em sem-obra-4d4db7 (q01 'IDOLS DE K POP...'), sem-obra-0e3c03 (q01 legendas centrais sem tarja) e sem-obra-8d5a76 (q01 'É MESMO?' no centro e spoiler 'O IRMÃO GÊMEO DO BIL' cortado no topo).
- onde: Detector de hardsub e filtro de cobertura de legenda em cortes_pipeline.py / detector de OCR dos quadros
- como testar: Rodar o detector nos vídeos-fonte de sem-obra-4d4db7, sem-obra-0e3c03 e sem-obra-8d5a76, verificar por que os quadros q01 não geraram máscara/tarja nas bandas superior (y=150-300) e inferior (y=1400-1750) e validar com folha de quadros.

## 11/11 22:05 PROPOSTA [CERTEZA] Ajustar corte de cena ao fim da frase falada para eliminar atraso de reação e corte ping-pong (gemini-4-argon)
- prova: Troca de cena atrasada ou no meio da frase emtodos os 4 Shorts: sem-obra-4d4db7 (q08/q09 e q13/q14 cortando antes de terminar de levantar), sem-obra-66b167 (q10 reação atrasada, q16 sobra de plano aberto), sem-obra-0e3c03 (q06 atraso no corte para Hestia, q13 close parado de 2s durante narração de ataque) e sem-obra-8d5a76 (q03 atraso na entrada de Champa, q08/q15 flash-cuts de 0.6s).
- onde: Alinhador de cortes de vídeo com timestamps do áudio (TTS/forced alignment) no montador de cenas
- como testar: Travar duração mínima de tomada em >= 1.2s (proibindo flash-cuts de 0.6s) e alinhar o timestamp de corte de vídeo exatamente ao início do timestamp da frase no alinhamento forçado; testar em sem-obra-8d5a76.

## 11/11 23:15 PROPOSTA [CERTEZA] Eliminar ghosting/sobreposição de legendas entre cenas, cores escuras/translúcidas e posicionar em faixa segura longe de rostos (gemini-4-argon)
- prova: Ghosting/sobreposição de palavras em 3/4 Shorts: 4d4db7 q06 ('APRESENTAÇÃO' fantasma atrás de 'SOLO'), 66b167 q02-q04 ('COLOSSAL' e 'DESCOBRINDO' sobrepostas a 'COM O PROTA' e 'PRÊMIO'), 8d5a76 q04 ('TODO MUNDO A' translúcido sobre os olhos de Goku). Baixo contraste/opacidade nula em 2/4 Shorts: 4d4db7 q10 ('JURO' marrom escuro translúcido), 0e3c03 q07/q08/q13 ('DISFARCE' invisível, 'PENSA' verde claro sem contraste, 'TODO' vermelho escuro). Cobertura de rosto e corte de margem em todos os 4 Shorts: 66b167 q02, 0e3c03 q05/q13, 8d5a76 q01/q02/q04 e 4d4db7 q03/q06/q10.
- onde: Gerador de legendas ASS/FFmpeg do pipeline de cortes (função de estilo/eventos de palavra-a-palavra e cálculo de bounding box/margem)
- como testar: Forçar encerramento estrito do timestamp de cada evento ASS antes do início da próxima palavra/cena (opacidade 100% ou 0%, sem fade/trilha duplicada), travar paleta em branco (#FFFFFF) ou amarelo (#FFFF00/#FFDD00) com borda preta de 8-14px, restringir x entre 60 e 1020 e posicionar y na faixa 1000-1450 desviando de rostos detectados; re-renderizar 66b167 e 0e3c03 e checar q02-q08 e q13.

## 11/11 23:15 PROPOSTA [CERTEZA] Garantir cobertura de hardsub/headers da fonte pela tarja branca e ocultar marcas d'água de terceiros (gemini-4-argon)
- prova: Em 3/4 Shorts o texto queimado ou marca d'água da fonte vazou sem cobertura: 4d4db7 q01 ('IDOLS DE K POP QUE CAÍRAM...' competindo com 'CÊ NÃO TEM'), 0e3c03 q01/q07 (ausência da tarja branca sobre a legenda central e botão 'INSCREVA-SE TOP ANIME' exposto) e 8d5a76 q01 (cabeçalho 'O IRMÃO GÊMEO DO BILLS APARECEU!' dando spoiler do mistério, legenda 'É MESMO?' sob 'FIGURA' e marca '@ANIMAX_97').
- onde: Detector de hardsub/tarja e filtro de crop/cobertura do vídeo-fonte no pipeline de cortes
- como testar: Rodar a detecção de texto queimado em resolução >= 720p nas faixas superior (y=150-300) e inferior/central (y=1300-1750) aplicando tarja branca sólida de ponta a ponta (1080px) quando houver texto da fonte, e ajustar o crop 9:16 para cortar banners/marcas d'água de canto; testar nos fontes de 4d4db7, 0e3c03 e 8d5a76.

## 11/11 23:15 PROPOSTA [CERTEZA] Alinhar cortes de cena aos limites de frase da locução e evitar planos estáticos longos ou perda de sujeito no pan/crop (gemini-4-argon)
- prova: Nos 4 Shorts há atraso na troca de cena ou congelamento em momentos de ação: 4d4db7 q08/q14/q16 (2,5s de palco escuro e janela letterbox com 9.9% de movimento), 66b167 q10/q13/q16 (corte atrasado para o guerreiro e pan em q13-q14 mostrando só gramado/céu vazio sem o personagem), 0e3c03 q06/q13/q18 (close estático da Freya por 2s enquanto narra ataque e frame congelado no fim) e 8d5a76 q03/q11/q15 (atraso na entrada de Champa, 3s estáticos em Vados e flash-cut de 0.6s).
- onde: Módulo de montagem/alinhamento de cenas por timestamps do áudio e crop dinâmico (tracking de sujeito)
- como testar: Sincronizar os pontos de corte exatamente com o início de cada frase do alinhamento forçado (evitando sobras < 0.8s ou planos parados > 2.0s) e ancorar o crop 9:16 na detecção de cabeça/tronco (y=300-1100); validar gerando folhas de quadros de 66b167 e 8d5a76.

## 12/11 00:27 PROPOSTA [CERTEZA] Detectar legendas estilo karaokê pop-in no meio da tela e forçar cobertura opaca quando delogo vazar (gemini-4-argon)
- prova: Nos 4 Shorts (sem-obra-4d4db7 q01-q03/q15, sem-obra-66b167 q02-q08/q15-q17, sem-obra-0e3c03 q01/q07-q11 e sem-obra-8d5a76 q01/q05/q11-q13/q17), a legenda queimada do vídeo parceiro ficou visível atrás da nossa legenda dinâmica, criando duas camadas de texto simultâneas e ilegíveis.
- onde: D:\recapd-ambientes\producao\bin\anime_hardsub_detect.py e parceiro_marca.py
- como testar: Rodar anime_hardsub_detect nas fontes dos 4 Shorts com amostragem densa na faixa central (y=800..1600) e verificar nos quadros gerados se a caixa cobre 100% da legenda original sem deixar palavras fantasmas.

## 12/11 00:27 PROPOSTA [CERTEZA] Travar posição vertical da legenda dinâmica abaixo dos rostos (y=1150 a 1450) e remover blur/perspectiva 3D (gemini-4-argon)
- prova: Em sem-obra-66b167 (q02, q10, q11, q17), sem-obra-0e3c03 (q05, q09, q10, q13) e sem-obra-8d5a76 (q02, q04, q08, q13, q14, q15), as palavras da legenda foram renderizadas exatamente sobre os olhos, nariz e boca dos personagens, além de 'CARACA' (8d5a76 q14) sair borrada por efeito 3D/motion blur e 'PENSA'/'DISFARCE' (0e3c03 q07/q08) saírem translúcidas.
- onde: D:\recapd-ambientes\producao\bin\fx_subtitles.py
- como testar: Gerar legendas ASS para sem-obra-8d5a76 e sem-obra-0e3c03 garantindo MarginV na faixa segura inferior (peito/tronco, y=1150..1450), opacidade 100% sólida e sem tags de blur/rotação 3D que degradem a leitura.

## 12/11 00:27 PROPOSTA [CERTEZA] Reenquadrar cenas em letterbox 16:9 e limpar cabeçalhos/stickers de terceiros nas bordas (gemini-4-argon)
- prova: Em sem-obra-4d4db7 (q16-q18) a cena 6 entrou em letterbox horizontal com >60% da tela preta, botões falsos de INSCREVER-SE e sticker cobrindo a legenda ('...HOU', '...SSO!'); em sem-obra-8d5a76 (q01) o cabeçalho '@animax_97 / O IRMÃO GÊMEO DO BILLS APARECEU!' ficou exposto dando spoiler; em sem-obra-0e3c03 (q06-q09) vazou botão 'INSCREVA-SE TOP ANIME' e card 'LOCAL: MUNDO'.
- onde: D:\recapd-ambientes\producao\bin\anime_segments.py e parceiro_marca.py
- como testar: Detectar barras pretas superiores/inferiores e overlays fixos de terceiros no crop vertical de anime_segments.py, aplicando zoom/crop 9:16 limpo nos trechos afetados.

## 12/11 01:40 PROPOSTA [CERTEZA] Corrigir detecção e cobertura de hardsub para ocultar 100% da legenda queimada da fonte antes de sobrepor a legenda dinâmica (gemini-4-argon)
- prova: Nas folhas de quadros dos 4 Shorts — sem-obra-4d4db7 (q01-q03, q15), sem-obra-66b167 (q03 'DESCOBRINDO', q08 'ASSUSTAR', q17 'CONCORDARAM'), sem-obra-0e3c03 (q01-q02, q09) e sem-obra-8d5a76 (q01, q05-q06, q11-q13, q17-q18) — a legenda original da fonte permaneceu visível sem tarja nem delogo eficaz, causando sobreposição direta de duas legendas.
- onde: D:\recapd-ambientes\producao\bin\anime_hardsub_detect.py e parceiro_marca.py
- como testar: Rodar anime_hardsub_detect.py e parceiro_marca.py nas fontes de sem-obra-8d5a76, sem-obra-66b167 e sem-obra-4d4db7, gerar folha.jpg e confirmar que nenhum caractere da legenda original vaza sob a legenda da narração.

## 12/11 01:40 PROPOSTA [CERTEZA] Reposicionar a legenda palavra-a-palavra na faixa inferior do peito/tronco (fora do rosto) e garantir opacidade 100% com alto contraste (gemini-4-argon)
- prova: Nas folhas de sem-obra-0e3c03 (q05 'TODO', q10 'E EXIGE', q13 'ATACA'), sem-obra-8d5a76 (q02 'MISTERIOSA', q08 'PERSONAGEM', q15 'ISSO?') e sem-obra-66b167 (q10 'CHOCADO', q11 'TENTANDO', q17 'ESSA BAGUN'), as caixas de texto cobrem diretamente olhos, nariz e boca dos personagens; além disso, palavras saíram translúcidas ou escuras sem contraste em 0e3c03 (q07 'PENSA', q08 'DISFARCE', q15 'GAROTO'), 4d4db7 (q10 'JURO') e 8d5a76 (q16 'PROTA').
- onde: D:\recapd-ambientes\producao\bin\fx_subtitles.py
- como testar: Renderizar fx_subtitles.py nos Shorts sem-obra-0e3c03 e sem-obra-8d5a76 e inspecionar os quadros q02, q05, q07, q08, q13, q15 e q16 para validar que os rostos ficam livres e todas as palavras têm preenchimento opaco claro com contorno preto espesso.

## 12/11 02:48 PROPOSTA [CERTEZA] Reforçar detecção e cobertura de hardsub estilizado/central (anime_hardsub_detect / parceiro_marca) (gemini-4-argon)
- prova: Nos 4 Shorts do lote (sem-obra-4d4db7 q01-q03/q15, sem-obra-66b167 q02/q03/q08/q17, sem-obra-0e3c03 q01/q07/q09/q11/q16 e sem-obra-8d5a76 q01/q05/q11/q17), a legenda queimada original da fonte ficou exposta sob a nossa legenda dinâmica (causando efeito de 'texto fantasma' e colisão direta de palavras), além de cabeçalhos com spoiler/arrobas de terceiros no topo em sem-obra-8d5a76 (q01 'O IRMÃO GÊMEO DO BILLS APARECEU!' / '@animax_97') e sem-obra-0e3c03 (q07 botão 'INSCREVA-SE TOP ANIME'). As alavancas tarja_largura_max (0.8) e tarja_letra (0.62) já atingiram o teto.
- onde: D:\recapd-ambientes\producao\bin\anime_hardsub_detect.py e D:\recapd-ambientes\producao\bin\parceiro_marca.py
- como testar: Rodar detecção de hardsub nas fontes de sem-obra-66b167, sem-obra-0e3c03 e sem-obra-8d5a76; ajustar detecção para capturar legendas estilizadas no centro/meio-inferior e substituir delogo insuficiente por tarja sólida quando houver alto contraste residual; gerar folha.jpg e validar ausência de colisão de texto.

## 12/11 02:48 PROPOSTA [CERTEZA] Travar zona Y da legenda dinâmica na faixa inferior segura (y=1150 a 1450) e garantir opacidade 100% (fx_subtitles) (gemini-4-argon)
- prova: Em 3 Shorts do lote a nossa legenda palavra-a-palavra foi renderizada no centro da tela cobrindo olhos, nariz e boca dos personagens: sem-obra-66b167 (q02, q10, q11, q17), sem-obra-0e3c03 (q03, q05, q09, q10, q13, além de palavras com baixa opacidade/contraste em q07 'PENSA', q08 'DISFARCE' e q15 'GAROTO') e sem-obra-8d5a76 (q02 'MISTERIOSA' no olho de Goku, q04, q08 'PERSONAGEM', q13, q15 'ISSO?' no rosto da Vados e q14 'CARACA' com blur excessivo).
- onde: D:\recapd-ambientes\producao\bin\fx_subtitles.py
- como testar: Renderizar legendas de teste em sem-obra-0e3c03 e sem-obra-8d5a76 fixando o alinhamento vertical na faixa y=1150..1450 (abaixo do rosto em closes médios), removendo cores escuras/translúcidas e desfoque de perspectiva; extrair folha.jpg para confirmar rostos limpos e contraste 100%.

## 12/11 04:00 PROPOSTA [CERTEZA] Conferir por que 3 Shorts saíram sem tarja com legenda queimada da fonte visível (cw/claude-sonnet-5-5)
- prova: 4d4db7 q01 (texto 'IDOLS DE K POP...' competindo com a nossa legenda), 0e3c03 q01/q02 (legenda da fonte exposta) e 8d5a76 q01 ('É MESMO?' sob 'FIGURA'). O júri não vê o log, então isto só vale se o log disser que a visão NÃO leu legenda ('[hardsub] só 0/6'). Se o log mostrar texto lido e diferente em ≥2 de 6 quadros e a tarja não foi aplicada, é bug. Se o log mostrar 0/6, o júri está certo e a detecção falhou.
- onde: log dos 3 Shorts do lote de 08/11; checagem hardsub da visão e função que decide aplicar a tarja
- como testar: Abrir o log de cada Short e ler a linha [hardsub]. Para os que tiverem 0/6, rodar a folha de quadros em resolução ≥720 px e medir a caixa das letras. Usar um vídeo sem legenda como controle negativo antes de mudar o limiar.

## 12/11 04:00 PROPOSTA [CERTEZA] Legenda palavra a palavra cobrindo o rosto e com opacidade/contraste quase nulo (cw/claude-sonnet-5-5)
- prova: Rosto coberto: 66b167 q02, 0e3c03 q05/q13, 8d5a76 q02/q04. Opacidade ou contraste ruim: 4d4db7 q10 ('JURO' marrom), 0e3c03 q07/q08 ('PENSA' e 'DISFARCE' translúcidos). Aparece em 3 Shorts com notas entre 3.62 e 4.25.
- onde: Renderização da legenda: cor/estilo por personagem, posição da caixa e fade de opacidade; talvez um deslocamento quando houver rosto na zona da palavra
- como testar: Renderizar os 4 Shorts citados e conferir, nos mesmos quadros, que a palavra ativa tem opacidade 100%, traçado escuro e não toca olhos, nariz ou boca. Preservar a regra da dona de legenda com palavras de impacto maiores, de lado, com fontes e cores por personagem.

## 12/11 04:00 PROPOSTA [CERTEZA] Palavras da frase seguinte ou anterior aparecendo por baixo da palavra ativa (cw/claude-sonnet-5-5)
- prova: 66b167 q02/q03/q04 ('COLOSSAL' antecipada sobre 'COM O PROTA', 'DESCOBRINDO' sob 'QUE ANIQUILA') e 4d4db7 q06 ('APRESENTAÇÃO' fantasma sob 'SOLO'). Repete em 2 Shorts.
- onde: Montagem das legendas na timeline: tempo de fim das palavras e limpeza entre cenas
- como testar: Extrair os quadros q02–q04 de 66b167 e q06 de 4d4db7 com o tempo exato e verificar que só uma palavra ou par fica ativo por instante.

## 12/11 04:00 PROPOSTA [CERTEZA] Marca d'água e botão de canal terceiro exposto (TOP ANIME, Animax) (cw/claude-sonnet-5-5)
- prova: 0e3c03 q07 (botão 'INSCREVA-SE TOP ANIME' e logotipo) e 8d5a76 q01 (avatar, '@animax_97' e marca d'água grande). Aparece em 2 Shorts de anime.
- onde: Etapa de cobertura (cobertura_legenda=delogo) e detecção de marca d'água por quadro
- como testar: Rodar delogo nas regiões detectadas desses 2 vídeos e conferir se o resultado não deixa borrão. Cuidar para a cobertura não virar faixa grande, o que contraria a regra da dona de tarja só do tamanho exato.

## 12/11 05:11 PROPOSTA [CERTEZA] Legenda palavra a palavra com mais de uma palavra ativa ao mesmo tempo (ghosting) (cw/claude-sonnet-5-5)
- prova: 66b167 q02 ('COLOSSAL' antecipada sobre 'COM O PROTA'), q03 ('DESCOBRINDO' sob 'QUE ANIQUILA'), q04 ('PRÊMIO' sobre 'COLOSSAL'); 4d4db7 q06 ('APRESENTAÇÃO' fantasma atrás de 'SOLO'); 8d5a76 q04 (resíduo 'TODO MUNDO A' sobre os olhos do Goku). Repete em 3 Shorts.
- onde: Renderizador da legenda (geração do ASS/eventos de legenda): fim de cada palavra e o início da próxima, mais a troca de cena. Provável erro de fim/início sobreposto ou camada de cena anterior que não é limpa.
- como testar: Gerar o ASS do 66b167 e contar, por instante, os eventos ativos (esperado: no máximo 1 palavra ou par). Rerrenderizar e conferir q02-q04 numa folha de quadros.

## 12/11 05:11 PROPOSTA [CERTEZA] Legenda ilegível ou cobrindo o rosto: opacidade, contraste e margem lateral (cw/claude-sonnet-5-5)
- prova: 0e3c03 q07 e q08 ('PENSA' e 'DISFARCE' quase transparentes), q05 e q13 (bloco sobre nariz e boca da Freya); 4d4db7 q10 ('JURO' marrom translúcido, 'GRITINHO' a menos de 20 px da borda), q03 (palavra a menos de 20 px da borda); 8d5a76 q02 e q04 (palavra sobre o rosto do Goku e do Vegeta). Repete em 3 Shorts.
- onde: Paleta de cor por personagem e posicionamento no renderizador da legenda: piso de opacidade 100% e de contraste contra o fundo, limite de x entre 60 e 1020 px, e deslocar a palavra para o lado ou para baixo quando houver rosto detectado.
- como testar: Rodar nos 3 Shorts, medir o contraste de cada palavra e a distância da borda. Manter as cores por personagem que a dona prefere, só impedindo tons escuros ou translúcidos. Conferir 6 quadros por Short.

## 12/11 05:11 PROPOSTA [CERTEZA] Legenda queimada da fonte exposta sem tarja: investigar se a detecção falhou (cw/claude-sonnet-5-5)
- prova: 4d4db7 q01 (texto 'IDOLS DE K POP...' visível), 0e3c03 q01 (legenda central exposta e 'INSCREVA-SE TOP ANIME' em q07), 8d5a76 q01 (texto da fonte atrás de 'FIGURA'). Falta a prova obrigatória: o log '[hardsub] só X/6' de cada Short. Sem ele, não dá para dizer se a visão não leu ou se a tarja foi lida e não aplicada.
- onde: Detecção de hardsub e aplicação da tarja (etapa que decide tarja/apagado). Primeiro ler o log dos 3 Shorts.
- como testar: Ler '[hardsub]' do log dos 3 Shorts. Se a visão leu e a tarja não foi aplicada, é bug de aplicação. Se leu 0/6, montar folha de 6 quadros em resolução >= 720 px com um controle negativo (vídeo sem legenda) antes de mexer no limiar. A tarja continua do tamanho exato da legenda.

## 12/11 05:11 PROPOSTA [CERTEZA] Marca d'água, avatar e botão 'inscreva-se' do canal de origem expostos (cw/claude-sonnet-5-5)
- prova: 0e3c03 q07 (botão 'INSCREVA-SE TOP ANIME' com sino e logotipo na lateral); 8d5a76 q01 (avatar, 'Animax', '@animax_97' e marca d'água grande). Repete em 2 Shorts. A única alavanca de cobertura permitida é 'delogo', já ativa.
- onde: Etapa de cobertura (delogo): o brief não diz se ela detecta marca d'água fora da faixa da legenda.
- como testar: Verificar nos 2 Shorts se a região foi enviada ao delogo. Se não foi, testar delogo nas regiões de canto e lateral com o mesmo teste de folha de quadros. Cuidado com marca d'água em movimento, que pode deixar rastro.

## 12/11 06:18 PROPOSTA [CERTEZA] Legenda palavra a palavra cobrindo olhos, nariz e boca (cw/claude-sonnet-5-5)
- prova: 0e3c03 q05 (bloco rosa 'TODO' sobre nariz e boca da Freya) e q13 ('ATACA' gigante sobre olhos e testa); 8d5a76 q02 ('MISTERIOSA' sobre o olho e o nariz do Goku) e q04 ('ACHA' no queixo do Vegeta); 66b167 q02 ('PROTA' sobre queixo e boca). Repete em 3 Shorts.
- onde: Função que posiciona a legenda no render final (módulo de legenda/ASS da linha CORTES). Provável: y fixo da palavra ativa e o fator de escala por palavra de impacto.
- como testar: Rodar os 3 Shorts de novo com a palavra ativa limitada a uma faixa y mais baixa (peito/tronco) e tamanho máximo por palavra. Conferir em folha de quadros se algum rosto ainda fica coberto. Controle: um Short sem rosto no quadro não pode mudar.

## 12/11 06:18 PROPOSTA [CERTEZA] Resíduo (ghosting) de palavra da cena anterior na legenda (cw/claude-sonnet-5-5)
- prova: 4d4db7 q06 ('APRESENTAÇÃO' fantasma atrás de 'SOLO'); 66b167 q03 ('DESCOBRINDO' sob 'QUE ANIQUILA') e q04 ('PRÊMIO' sobre 'COLOSSAL'); 8d5a76 q04 ('TODO MUNDO A' sobre os olhos do Goku). Repete em 3 Shorts.
- onde: Geração dos eventos de legenda a partir do alinhamento (fim de cada palavra vs. início da próxima, e sobreposição de camadas/estilos). Procurar eventos com tempo de fim maior que o início do evento seguinte.
- como testar: Para um Short afetado (ex.: 66b167), listar os eventos e checar sobreposição temporal entre palavras. Corrigir cortando o fim de cada palavra no início da próxima e re-renderizar. Conferir os quadros q03 e q04.

## 12/11 06:18 PROPOSTA [CERTEZA] Opacidade/contraste de palavras de destaque (cor escura, translúcida ou contorno fino) (cw/claude-sonnet-5-5)
- prova: 4d4db7 q10 ('JURO' marrom escuro translúcido); 0e3c03 q08 ('DISFARCE' com opacidade quase nula), q07 ('PENSA' com contorno verde fino sobre roupa clara) e q13 ('TODO' vermelho escuro sobre manto azul escuro). Repete em 2 Shorts.
- onde: Paleta de cores por personagem/palavra de impacto e fade de opacidade no estilo da legenda.
- como testar: Aplicar piso de luminância e contorno preto mínimo em toda palavra, e opacidade 100% imediata. Renderizar 0e3c03 e 4d4db7 e conferir as palavras citadas. Isso não deve contrariar a preferência da dona por cores por personagem: mexer só no piso de contraste, não na cor.

## 12/11 06:18 PROPOSTA [CERTEZA] Conferir o log de hardsub dos Shorts que o júri disse estarem sem tarja (cw/claude-sonnet-5-5)
- prova: 4d4db7 q01, 0e3c03 q01/q02 e 8d5a76 q01 mostram texto queimado da fonte competindo com a nossa legenda. Pela lição, o júri não vê debaixo da tarja, então isto só vale com o log '[hardsub] só 0/6'. Não tenho o log neste lote.
- onde: Log de produção de cada um dos 3 Shorts (linha [hardsub]) e a decisão tarja/delogo no pipeline.
- como testar: Abrir os logs dos 3 Shorts. Se disserem que a visão NÃO leu legenda, não há defeito (o júri viu a legenda da fonte, mas a regra é sem tarja). Se leu legenda e mesmo assim saiu sem tarja, é bug de CERTEZA no passo de cobertura.

## 12/11 06:18 PROPOSTA [GOSTO] Troca de cena adiantada/atrasada em relação à frase narrada (cw/claude-sonnet-5-5)
- prova: 0e3c03 q06 (a narração já fala 'ENQUANTO' e o vídeo segue na Freya) e q13 (close sereno da Freya durante 'ataca todo mundo'); 8d5a76 q03 (a figura só entra em q05) e q15 (ping-pong de 0,6 s); 66b167 q10 e q16 (cena repete o plano anterior). Repete em 3 Shorts, mas o júri já errou antes sobre cortes.
- onde: Seleção/corte de cena por beat da narração (função que mapeia frase para trecho do vídeo).
- como testar: Antes de mexer, conferir no roteiro.txt e no mapa de cenas se o atraso é real (mais de 0,5 s entre o início da frase e a troca). Se for, testar o corte da cena alinhado ao início da frase em 1 Short e comparar.

## 12/11 07:33 PROPOSTA [CERTEZA] Palavras da legenda palavra a palavra sobrepostas/fantasma entre cenas (cw/claude-sonnet-5-5)
- prova: 66b167 q03 ('DESCOBRINDO' sob 'QUE ANIQUILA') e q04 ('PRÊMIO' sobre 'COLOSSAL'); 8d5a76 q04 (resíduo 'TODO MUNDO A' sobre o rosto do Goku); 4d4db7 q06 ('APRESENTAÇÃO' fantasma atrás de 'SOLO'). Aparece em 3 de 5 Shorts.
- onde: Renderizador da legenda (ASS/drawtext): onde cada palavra recebe início/fim. Provável: função que gera os eventos de legenda a partir do alinhamento forçado.
- como testar: Gerar os 3 Shorts de novo e extrair quadros em cada troca de frase (±0,2 s). Verificar que só uma palavra/par está ativa por vez (fim da palavra N <= início da N+1) e que não há layers duplicadas no .ass.

## 12/11 07:33 PROPOSTA [CERTEZA] Legenda com baixo contraste ou translúcida (cores por personagem) (cw/claude-sonnet-5-5)
- prova: 4d4db7 q10 ('JURO' marrom escuro translúcido); 0e3c03 q07 ('PENSA' translúcido, contorno fino), q08 ('DISFARCE' quase invisível), q13 ('TODO' vermelho escuro sobre manto azul escuro).
- onde: Paleta de cores por personagem e opacidade/contorno no gerador da legenda.
- como testar: Calcular contraste (cor do texto vs. contorno) e impor mínimo de contorno grosso e opacidade 100%; excluir tons escuros da paleta; rodar nos 2 Shorts e conferir os quadros q07/q08/q10/q13.

## 12/11 07:33 PROPOSTA [CERTEZA] Legenda cobrindo rosto e colada na margem lateral (cw/claude-sonnet-5-5)
- prova: 0e3c03 q05/q13 (cobre nariz/olhos da Freya); 8d5a76 q02/q04 (cobre olho do Goku e boca do Vegeta); 66b167 q02 (queixo/boca); 4d4db7 q03/q10 (<20 px da borda).
- onde: Posicionamento vertical/horizontal e tamanho máximo da palavra de impacto na legenda.
- como testar: Limitar largura a x=60..1020 com redução automática do corpo; testar deslocar a legenda para o tronco quando houver rosto detectado na faixa; rodar nos mesmos 4 Shorts.

## 12/11 07:33 PROPOSTA [CERTEZA] Marca d'água/avatar de canal terceiro exposto (TOP ANIME, @animax_97) (cw/claude-sonnet-5-5)
- prova: 0e3c03 q07 (botão 'INSCREVA-SE TOP ANIME'); 8d5a76 q01 (avatar, '@animax_97' e marca d'água grande). A regra fixa proíbe @/link na tela.
- onde: Etapa de crop/cobertura da fonte (delogo/enquadramento) e checagem de QA de texto na tela.
- como testar: Detectar @ e botão de inscrição nos primeiros quadros (OCR) e ampliar o crop ou aplicar delogo na área; conferir com os 2 Shorts.

## 12/11 07:33 PROPOSTA [GOSTO] Cortes de cena fora do beat da narração (cw/claude-sonnet-5-5)
- prova: 0e3c03 q06 (narração já em 'ENQUANTO', vídeo ainda na Freya); 8d5a76 q03/q05 (revelação atrasada); 66b167 q10/q16 (cena repete o plano anterior).
- onde: Função que alinha cortes de cena aos tempos das frases (sincronia voz x cena).
- como testar: Mover o início de cada cena para o início da frase correspondente; comparar nota de movimento antes/depois em 5 Shorts. É gosto, então mede antes de ligar.

## 12/11 07:33 PROPOSTA [CERTEZA] Enquadramento perde o sujeito (gramado/céu vazio) e letterbox com 70% estático (cw/claude-sonnet-5-5)
- prova: 66b167 q13/q14 (personagem fora de quadro por ~2 s); 4d4db7 q16 (movimento 9,9%, janela minúscula com topo preto).
- onde: Cálculo do crop vertical 9:16 (ancoragem no sujeito) e layout do quadro.
- como testar: Reprocessar os 2 Shorts ancorando o crop na cabeça/tronco; verificar nos quadros indicados que o sujeito aparece e não há faixa preta.

## 12/11 08:42 PROPOSTA [CERTEZA] Legenda palavra a palavra cobrindo rosto (olhos/nariz/boca) e palavra ativa grande demais (cw/claude-sonnet-5-5)
- prova: 0e3c03 q05 (bloco 'TODO' sobre nariz e boca da Freya) e q13 ('ATACA' desproporcional sobre olhos/testa); 8d5a76 q02 ('MISTERIOSA' sobre o olho e nariz de Goku) e q04 ('ACHA' no queixo de Vegeta). Repete em 2 Shorts. Observação: tarja_letra está em 0.62 desde 00:27, então a mudança pode estar agravando o tamanho; medir antes de concluir.
- onde: Renderização da legenda (posição Y e escala da palavra ativa), ver função de composição da legenda ASS/overlay no pipeline CORTES; comparar com a posição das caixas de rosto da visão
- como testar: Renderizar os mesmos 2 Shorts com a legenda ancorada no terço inferior/tronco (fora da caixa do rosto detectado) e limite de escala por palavra; conferir quadros q05/q13 (0e3c03) e q02/q04 (8d5a76).

## 12/11 08:42 PROPOSTA [CERTEZA] Palavras com opacidade/contraste quase nulo ('ghost') e resíduo de palavra anterior (cw/claude-sonnet-5-5)
- prova: 0e3c03 q07 ('PENSA', preenchimento translúcido) e q08 ('DISFARCE' opacidade ~0); 4d4db7 q10 ('JURO' marrom escuro translúcido) e q06 (resíduo 'APRESENTAÇÃO' sob 'SOLO'); 66b167 q03 ('DESCOBRINDO') e q04 ('PRÊMIO' sobre 'COLOSSAL'). Repete em 3 Shorts.
- onde: Geração/paleta de cores por palavra e limpeza de eventos anteriores na legenda (fim do evento da palavra inativa; paleta que permite cor escura/translúcida)
- como testar: Forçar preenchimento opaco claro com contorno escuro em toda palavra e encerrar o evento anterior no início do próximo; renderizar 66b167 e 4d4db7 e checar q03/q04 e q06/q10 sem sobreposição.

## 12/11 08:42 PROPOSTA [CERTEZA] Margem lateral: texto do título/legenda a menos de 60 px da borda (cw/claude-sonnet-5-5)
- prova: 8d5a76 q01 (título cortado 'O IRMÃO GÊMEO DO BIL'), 4d4db7 q03 ('POSSÍVEL' a < 20 px) e q10 ('GRITINHO' a < 20 px). Repete em 2 Shorts. Cuidado: o texto de q01 do 8d5a76 e o de 4d4db7 q01 parecem ser texto queimado da fonte, não nosso; confirmar a origem antes de agir.
- onde: Quebra de linha e largura máxima do título/legenda no render (quebrar por largura de pixel medida, com margem de 60 px)
- como testar: Medir a largura renderizada de títulos longos e palavras grandes; forçar quebra/redução de corpo quando exceder 960 px; reconferir os 3 quadros citados.

## 12/11 08:42 PROPOSTA [GOSTO] Cortes de cena atrasados em relação à frase narrada (sujeito da frase aparece depois) (cw/claude-sonnet-5-5)
- prova: 0e3c03 q06 (narração já fala de Hestia, imagem segue em Freya) e q13 (narra o ataque da família, imagem em close sereno de Freya por ~2 s); 8d5a76 q03 ('aparece' dito, figura só entra em q05) e q15; 66b167 q10 e q16. Repete em 3 Shorts, mas é corte de cena (fora das alavancas) e tem componente de gosto.
- onde: Seleção/alinhamento de cenas com a narração (função que casa cena × frase e define o ponto de corte)
- como testar: Antecipar o início de cada cena em ~0,3–0,5 s em relação ao início da frase e comparar a retenção média e a nota do júri em um lote de 10 Shorts.

## 12/11 10:16 PROPOSTA [CERTEZA] Cor/contraste da legenda palavra a palavra: banir cores escuras e translúcidas (cw/claude-sonnet-5-5)
- prova: Em 3 Shorts: sem-obra-0e3c03 q07 ('PENSA' translúcida, contorno fino) e q08 ('DISFARCE' opacidade quase nula); sem-obra-afc76d q06 ('DURANTE' marrom fosco), q07 ('CLASSE' azul-escuro sobre cabelo preto), q12 ('BEM' azul-marinho sobre fundo ciano). O júri classificou como grave; casa com a regra 3 do APRENDIDO (só amarelo/branco, 100% opaco, traço preto). Antes de aplicar, conferir contra DECISOES_DONO, já que a dona prefere cores por personagem (lição 27/10): então restringir a paleta de cores por personagem a tons com contraste mínimo, em vez de impor só amarelo/branco.
- onde: módulo de renderização da legenda (gerador ASS/overlay palavra a palavra) e a tabela de cores por personagem/destaque
- como testar: Renderizar 10 Shorts antigos com a paleta filtrada (razão de contraste mínima ~4.5:1 contra o quadro, opacidade 100%) e rodar o júri; checar que não há mais 'baixo contraste' em legibilidade e que a diferenciação por personagem continua.

## 12/11 10:16 PROPOSTA [CERTEZA] Evitar que a palavra em destaque cubra o rosto (olhos/nariz/boca) (cw/claude-sonnet-5-5)
- prova: 3 Shorts: 0e3c03 q05 ('TODO' sobre nariz/boca da Freya) e q13 ('ATACA' sobre olhos/testa); 8d5a76 q02 ('MISTERIOSA' sobre olho e nariz de Goku) e q04 ('ACHA' no queixo/boca de Vegeta); afc76d q06 e q07 (rosto do protagonista). Em 66b167 q02 'PROTA' no queixo/boca.
- onde: função que posiciona a legenda/destaque (âncora vertical) e, se existir, a detecção de rosto por quadro
- como testar: Rodar detecção de rosto no quadro de cada palavra; se a caixa da palavra intersectar o rosto, mover para a faixa livre (tronco/peito) ou reduzir o corpo. Medir a taxa de interseções em 20 Shorts antes e depois.

## 12/11 10:16 PROPOSTA [CERTEZA] Camadas de legenda fantasma/sobrepostas e card residual de template (cw/claude-sonnet-5-5)
- prova: 66b167 q02 ('COLOSSAL' antecipada sobre 'COM O PROTA'), q03 ('DESCOBRINDO' fantasma abaixo de 'QUE ANIQUILA'), q04 ('PRÊMIO' sobre 'COLOSSAL'); 8d5a76 q04 (resíduo 'TODO MUNDO A' sobre Goku); afc76d q10–q12 (card 'ANTES/AGORA' persistente, texto desconexo da narração, corpo minúsculo) e q13 ('VIU?' residual). Pontua com a regra 5 do APRENDIDO. Verificar primeiro no .ass/timeline do Short se há eventos com intervalos sobrepostos antes de culpar o júri.
- onde: geração de eventos da legenda (fim de cada palavra deve ser <= início da próxima) e o ciclo de vida do card de template (remover quando a cena termina)
- como testar: Script que lê a timeline de um Short e reporta sobreposições de intervalo e cards com duração maior que a cena; rodar nos Shorts do lote 08/11 e confirmar zero sobreposições após a correção.

## 12/11 10:16 PROPOSTA [CERTEZA] Marca d'água/avatar/botão de inscrição do canal de origem ficam à mostra (cw/claude-sonnet-5-5)
- prova: 0e3c03 q07 (botão 'INSCREVA-SE TOP ANIME' e logotipo), 8d5a76 q01 (avatar, 'Animax', '@animax_97' e marca d'água grande), afc76d q02 (marca d'água 'richan'). Atenção: as regras fixas proíbem '@' na tela; a marca d'água do parceiro traz '@' visível. O corte 'tarja do tamanho exato da legenda' não se aplica a marca d'água, então este item é separado da tarja e exige decisão da dona.
- onde: etapa de crop/enquadramento do vídeo fonte (cortes) e/ou detecção de marca d'água; avaliar crop com zoom leve ou delogo na região detectada (delogo já é o valor da alavanca cobertura_legenda, mas hoje não atua sobre marca d'água)
- como testar: Detectar texto/logo nos cantos em 3 quadros por Short; aplicar delogo ou crop só nessa região em 5 Shorts e conferir com folha de quadros, mais um controle negativo (vídeo sem marca d'água).

## 12/11 10:16 PROPOSTA [CERTEZA] Conferir no log se a tarja sumiu de verdade em sem-obra-0e3c03 (antes de qualquer mudança) (cw/claude-sonnet-5-5)
- prova: O júri disse 'ausência da tarja' e 'legenda queimada exposta' em q01/q02 de 0e3c03. Pelas lições, isso só vale se o log do Short registrar que a visão NÃO leu a legenda ('[hardsub] só 0/6'). Sem esse log não é defeito comprovado e não se mexe.
- onde: log do Short sem-obra-0e3c03_cap1_20261108 (linha [hardsub]) e a decisão de tarja do pipeline
- como testar: Ler o log; se mostrar 'só 0/6', abrir a folha de quadros do início do vídeo para ver se havia legenda queimada de fato e tratar como falha de detecção de legenda curta/inicial.

## 12/11 10:16 PROPOSTA [CERTEZA] Auditar por que 'prota' continua saindo mesmo com a regra de roteiro (cw/claude-sonnet-5-5)
- prova: 'COM O PROTA' em 66b167 q02 e 'O prota' em afc76d q13 (2 Shorts), apesar da regra 'Nunca use a gíria prota' estar em regras_roteiro (reintroduzida em 11/11 22:05, ainda 'vigiando'). Pode ser que estes Shorts (08/11) tenham sido gerados ANTES da regra; checar a data de geração do roteiro.txt.
- onde: roteiro.txt dos dois Shorts e o prompt do narrador (regra de nicho tem de entrar também dentro do bloco do narrador, lição 26/10); considerar filtro pós-roteiro que reescreve 'prota' em vez de confiar só no prompt
- como testar: Grep por 'prota' nos roteiros gerados depois de 11/11 22:05; se ainda ocorrer, adicionar validação determinística (regex) que recusa/reescreve o roteiro.

## 12/11 11:50 PROPOSTA [CERTEZA] Legenda palavra a palavra cobrindo olhos, nariz e boca (cw/claude-sonnet-5-5)
- prova: Aparece nos 4 Shorts: 66b167 q02 (PROTA no queixo e boca), 0e3c03 q05/q13 (TODO e ATACA sobre o rosto da Freya), 8d5a76 q02/q04 (MISTERIOSA sobre o olho e nariz do Goku, ACHA no queixo do Vegeta), afc76d q06/q07 (DURANTE e CLASSE sobre o rosto).
- onde: Renderizador da legenda (ASS/Pillow) no pipeline do CORTES, posição vertical da palavra ativa
- como testar: Detectar rosto no quadro (OpenCV/MediaPipe) e deslocar a palavra para fora da caixa do rosto, ou fixar a legenda no terço inferior seguro. Rodar nos 4 Shorts de 08/11 e conferir q02, q05, q13 e q06 com a folha de quadros.

## 12/11 11:50 PROPOSTA [CERTEZA] Cor, opacidade e contorno da legenda sem contraste (cw/claude-sonnet-5-5)
- prova: 0e3c03 q07 (PENSA translúcido), q08 (DISFARCE quase invisível) e q13 (TODO vermelho escuro sobre manto azul escuro). afc76d q06 (marrom fosco), q07 (azul escuro sobre cabelo preto) e q12 (azul-marinho sobre fundo ciano).
- onde: Função que escolhe a paleta por personagem/palavra (cor de preenchimento e contorno)
- como testar: Calcular o contraste (razão WCAG) entre o preenchimento e o contorno; se for menor que 4.5, forçar branco ou amarelo com contorno preto. Manter as cores por personagem só quando o contraste passar. Conferir os quadros q07, q08 e q12.

## 12/11 11:50 PROPOSTA [CERTEZA] Legenda ou card fantasma de cena anterior ainda ativos (cw/claude-sonnet-5-5)
- prova: 66b167 q03/q04 (DESCOBRINDO e COLOSSAL sobrepostos à legenda atual, barra amarela residual até q18). 8d5a76 q04 (resíduo 'TODO MUNDO A' sobre o Goku). afc76d q10-q12 (card 'ANTES/AGORA' residual, texto desconexo em corpo pequeno) e q13 (resíduo de 'VIU?').
- onde: Montagem da timeline: fim de cada evento de legenda/card na troca de cena
- como testar: Gerar o vídeo e extrair o quadro nos primeiros 100 ms de cada cena; garantir no máximo 1 palavra ativa e nenhum card antigo. Se sobrar ghosting, é erro de fim de evento.

## 12/11 11:50 PROPOSTA [CERTEZA] Marca d'água e botão do canal de origem à mostra (cw/claude-sonnet-5-5)
- prova: 0e3c03 q07 (botão 'INSCREVA-SE TOP ANIME' e logo). 8d5a76 q01 (avatar, 'Animax' e '@animax_97'). afc76d q02 (marca 'richan').
- onde: Etapa de cobertura/crop do vídeo fonte (cobertura_legenda=delogo) e escolha do enquadramento
- como testar: Detectar texto @ ou logo estático nos cantos pelo OCR dos quadros iniciais e aplicar delogo ou crop. Regra da dona: sem @ na tela. Validar nos 3 Shorts citados.

## 12/11 11:50 PROPOSTA [GOSTO] Cortes de cena atrasados em relação à fala (cw/claude-sonnet-5-5)
- prova: 0e3c03 q06 (a fala vai para 'ENQUANTO' e a imagem segue na Freya) e q13 (Freya sorrindo durante 'ataca todo mundo'). 8d5a76 q03 ('aparece' com o plano de reação ainda no ar). 66b167 q10 (fala 'guerreiro chocado' sobre o close do xamã).
- onde: Seleção e corte de cenas por frase (alinhamento cena e narração)
- como testar: Antecipar o corte em cerca de 0,3 s para a primeira palavra da frase e medir se a nota de 'movimento' do júri sobe. Testar uma mudança por vez.

## 12/11 13:13 PROPOSTA [CERTEZA] Confinar legenda dinâmica na faixa segura (y=1000 a y=1450, x entre 60 e 1020 px) e fora da área facial (agy/gemini-3.8-flash-high)
- prova: Em sem-obra-8d5a76_cap1_20261108 (q02.jpg e q04.jpg) a legenda cobriu olhos e nariz de Goku e Vegeta; em sem-obra-afc76d_cap1_20261108 (q06.jpg e q07.jpg) as palavras cobriram os olhos e testa do protagonista; em sem-obra-7c3aa7_cap1_20261108 (q15.jpg e q16.jpg) a legenda desceu abaixo de y=1580 e teve palavras cortadas nas laterais.
- onde: Renderizador de legendas ASS/Remotion (cálculo de coordenadas verticais y e margem lateral mínima no pipeline de montagem)
- como testar: Renderizar trechos com closes faciais em sem-obra-8d5a76 e sem-obra-afc76d e verificar se a bounding box das palavras mantém respiro mínimo de 40 px abaixo dos rostos detectados e permanece contida em x=[60, 1020] e y=[1000, 1450].

## 12/11 13:13 PROPOSTA [CERTEZA] Expandir bounding box da cobertura delogo e sanar falha de detecção sobre legendas queimadas (agy/gemini-3.8-flash-high)
- prova: Em sem-obra-520bad_cap1_20261108 (q01.jpg e q06.jpg) a máscara de desfoque vazou texto da fonte acima ('EXISTEM COMIDAS'), abaixo ('COMUNS') e nas bordas laterais ('QUA', 'BRA') ao longo de todo o vídeo; em sem-obra-7c3aa7_cap1_20261108 (q01.jpg e q17.jpg) e sem-obra-8d5a76_cap1_20261108 (q01.jpg) a legenda queimada da fonte ficou sem cobertura, gerando sobreposição com a legenda da narração.
- onde: Detector de hardsub e filtro de aplicação de cobertura delogo (módulo de detecção e mascaramento de legendas da fonte no pipeline CORTES)
- como testar: Executar a detecção em sem-obra-520bad e sem-obra-7c3aa7 e verificar se a máscara de cobertura abrange 100% da área da legenda original sem vazamento residual em nenhum quadro com texto.

## 12/11 13:14 PROPOSTA [CERTEZA] Corrigir falha de detecção de hardsub e vazamento lateral/vertical do delogo (gemini-4-argon)
- prova: Legenda original da fonte exposta em todos os 4 Shorts do lote: sem-obra-520bad (q01 e q06 vazando acima, abaixo e nas laterais do desfoque), sem-obra-7c3aa7 (q01 a q17 com legenda inferior visível sob a nossa legenda), sem-obra-e867e6 (q02, q03, q06, q08 com legendas originais expostas) e sem-obra-c11b82 (q01 e q05 com stickers e legendas originais na tela).
- onde: Pipeline de detecção de hardsub e aplicação de máscara/tarja (módulo de visão / cortes_pipeline)
- como testar: Rodar a detecção de hardsub nos vídeos-fonte de sem-obra-520bad, sem-obra-7c3aa7, sem-obra-e867e6 e sem-obra-c11b82 em resolução >= 720p e verificar na folha de quadros se a caixa cobre 100% das letras queimadas.

## 12/11 13:14 PROPOSTA [CERTEZA] Travar margem lateral mínima (60 px) e zona segura vertical (y=150 a 1450) na renderização de legendas e títulos (gemini-4-argon)
- prova: Textos cortados pelas bordas ou fora da zona segura em 3 Shorts: sem-obra-520bad (q01 topo 'COMIDAS ESQUECI█' cortado acima de y=150), sem-obra-7c3aa7 (q15 'penas/quebra' e q16 'destrui' cortados nas laterais e abaixo de y=1580; q11 card cortado à esquerda) e sem-obra-c11b82 (q05 'BRAÇO' vazando à direita e q11 'BOX, BOX' cortado no topo).
- onde: Renderizador de legendas/títulos ASS ou filtro drawtext/overlay no pipeline de vídeo
- como testar: Renderizar sem-obra-7c3aa7 e sem-obra-520bad conferindo se todas as palavras da legenda ficam entre x=60..1020 e y=1000..1450 e o título do topo abaixo de y=150 sem truncamento.

## 12/11 14:27 PROPOSTA [CERTEZA] Corrigir detecção de hardsub e dimensionamento da cobertura da legenda da fonte (gemini-4-argon)
- prova: Nos 4 Shorts do lote a legenda queimada da fonte ficou visível: em sem-obra-520bad (q01, q06) o delogo é estreito/baixo demais e vaza 'EXISTEM COMIDAS' acima, 'COMUNS' abaixo e 'QUA'/'BRA' nas laterais; em sem-obra-7c3aa7 (q01-q17, 'A SEGURANÇA PÚBLICA NÃO'), sem-obra-e867e6 (q02-q17, 'FILHA', 'RESTAVA', 'SALVAR MINHA') e sem-obra-c11b82 (q01-q18, 'SEU MANÉ', 'ESSA MULHER') a legenda queimada ficou exposta sem cobertura eficaz.
- onde: Módulo de detecção de hardsub e aplicação de cobertura/delogo no pipeline de vídeo (D:\video-fila\linhas\CORTES)
- como testar: Rodar a detecção e cobertura nos vídeos-fonte de sem-obra-520bad, sem-obra-7c3aa7, sem-obra-e867e6 e sem-obra-c11b82 e extrair folha de quadros (q01, q06, q15) confirmando que 100% da caixa de texto original é coberta com folga sem vazar letras no topo, base ou laterais.

## 12/11 14:27 PROPOSTA [CERTEZA] Travar bounding box da legenda dinâmica e overlays dentro das margens seguras (x=60..1020, y=1000..1450) e topo (y>=150) (gemini-4-argon)
- prova: Em sem-obra-7c3aa7 (q15, q16, q17) a legenda foi renderizada abaixo de y=1580 sobre a legenda original e cortada nas bordas laterais ('penas pra quebra', 'destrui'); em sem-obra-e867e6 (q03, q04) o sticker 'DECIDI' cobriu o rosto do bebê e 'ACALMAR' colou na borda esquerda (x < 60 px); em sem-obra-520bad (q01) e sem-obra-c11b82 (q05, q11) o título do topo ('COMIDAS ESQUECI█', 'BOX, BOX') cortou acima de y=150 e o banner 'BRAÇO' vazou a margem direita.
- onde: Gerador de legendas ASS/renderizador de overlays e título do topo no pipeline CORTES
- como testar: Renderizar sem-obra-7c3aa7, sem-obra-e867e6 e sem-obra-520bad validando que nenhum glifo ultrapasse x < 60, x > 1020, y < 150 (topo) ou y > 1450 (legenda), com quebra de linha automática antes de atingir a margem.

## 12/11 15:34 PROPOSTA [CERTEZA] Ajustar detecção de hardsub e margem de cobertura (delogo/tarja) (gemini-4-argon)
- prova: Legenda queimada da fonte visível sem cobertura em sem-obra-7c3aa7_cap1_20261108 (q01, q17: 'A SEGURANÇA PÚBLICA NÃO', 'VOCÊ NÃO COMEÇA TIRANDO'), sem-obra-e867e6_cap1_20261108 (q02, q03, q08: 'FILHA', 'RESTAVA', 'SALVAR MINHA') e sem-obra-c11b82_cap1_20261108 (q01, q05: 'ESSA MULHER', 'O BRAÇO'), e vazando pelas bordas do delogo em sem-obra-520bad_cap1_20261108 (q01, q06: 'EXISTEM COMIDAS', 'QUA', 'BRA').
- onde: Detector de hardsub (visão em >= 720p) e cálculo da bounding box do filtro de cobertura da legenda original
- como testar: Rodar a detecção de hardsub nos 4 vídeos-fonte do lote, gerar folha de quadros e confirmar que 100% dos caracteres queimados nos 4 casos são detectados e cobertos sem vazar nas bordas (e que um vídeo controle sem legenda continua sem tarja).

## 12/11 15:34 PROPOSTA [CERTEZA] Travar margens seguras (x in [60, 1020], y in [1000, 1450]) e presença contínua da legenda dinâmica (gemini-4-argon)
- prova: Legenda cortada nas bordas laterais e abaixo de y=1580 em sem-obra-7c3aa7_cap1_20261108 (q15 'penas... quebra', q16 'destrui', q17 sobreposta no rodapé), colada na borda esquerda/sobre rosto em sem-obra-e867e6_cap1_20261108 (q03 sobre o rosto do bebê, q04 'ACALMAR' em x < 60 px) e ausente de q01 a q12 em sem-obra-e867e6_cap1_20261108.
- onde: Renderizador de legenda dinâmica (.ass / filtro de legendas do FFmpeg) e validação pós-alinhamento de áudio
- como testar: Re-renderizar sem-obra-7c3aa7_cap1_20261108 e sem-obra-e867e6_cap1_20261108 verificando que todas as palavras respeitam MarginL/MarginR >= 60 px, y entre 1000 e 1450 e que q01–q12 de e867e6 exibem legenda sincronizada com a locução.

## 12/11 21:09 PROPOSTA [CERTEZA] Remover bordões fixos de personagem ('Pelos poderes de Bright Moon') do prompt do narrador em anime_script.py / anime_gancho.py (gemini-4-argon)
- prova: Em sem-obra-72412c_cap1_20261109 (q01.jpg) e how-does-a-snake-rattle-make-sound_cap1_20261109 (q01.jpg), ambos do canal @codigointeligente-n7j, a locução abre com 'Pelos poderes de Bright Moon'. Conforme a lição de 26/10, a instrução do bloco do narrador-personagem vale por cima das regras gerais se não for limpa diretamente no template do narrador.
- onde: D:\recapd-ambientes\producao\bin\anime_script.py e D:\recapd-ambientes\producao\bin\anime_gancho.py (bloco de persona/bordão do narrador)
- como testar: Buscar 'Bright Moon' ou instruções de bordão de persona nos prompts de roteiro/gancho, remover a exigência de bordão de abertura e gerar 2 roteiros de teste para @codigointeligente-n7j conferindo que abrem direto no fato da cena.

## 12/11 21:09 PROPOSTA [CERTEZA] Eliminar sobreposição/ghosting de palavras, cores translúcidas/escuras e colisão com rosto/mascote na legenda dinâmica (gemini-4-argon)
- prova: Repetido nos 4 Shorts: (1) Ghosting/duplicação: sem-obra-7dbc42 q06 ('CARTÓRIO' borrado atrás de 'AO IR') e q18 ('COMENTÁRIOS' + 'NOS MENTÁRIOS!'), sem-obra-54cfff q17 ('MUNDO!' vermelho sob 'EMBAIXO'), sem-obra-72412c q12 ('CONGELADOS' sob 'SAEM') e q18 (duplo 'EMBAIXO'), how-does-a-snake-rattle-make-sound q13/q14 ('BARULHO' duplicado sob 'AQUELE' e 'GOSTOU?'); (2) Baixo contraste/transparência: 7dbc42 q02/q06, 54cfff q03/q08 ('IMPEDE')/q15, 72412c q03/q05 ('COREANA!' translúcido)/q11/q13, snake-rattle q09 ('UMAS')/q12 ('PEÇAS' verde s/ borda); (3) Cobertura de rosto/colisão com sticker no CTA: 7dbc42 q12/q15/q18, 54cfff q16/q17, 72412c q18.
- onde: D:\recapd-ambientes\producao\bin\fx_subtitles.py (geração de eventos ASS, paleta por personagem e posicionamento de CTA/mascote)
- como testar: Garantir que cada evento ASS encerre estritamente no timestamp inicial do próximo (sem camada residual entre cenas ou duplicação no CTA), travar opacidade em 100% com contorno preto >= 8px e luminância alta nas cores de personagem, e posicionar a legenda na faixa inferior (y=1150..1450) sem colidir com o sticker da mascote; validar re-renderizando os 4 Shorts e checando as folhas de quadros.

## 12/11 21:09 PROPOSTA [CERTEZA] Alargar cobertura sobre a caixa exata da legenda queimada da fonte quando exceder 80% da largura ou falhar na detecção (gemini-4-argon)
- prova: As alavancas tarja_largura_max (0.8) e tarja_letra (0.62) já estão no limite máximo permitido, mas a legenda original da fonte continuou vazando nas laterais do delogo em 3 Shorts — sem-obra-7dbc42 (q04 'd...n', q05 'im...ar'), sem-obra-72412c (q06 'TRA...ORES', q08 'HI...NDO', q15 'PI...ADA') e how-does-a-snake-rattle-make-sound (q04 'da...as', q05 'que...em', q10 'qu...ão', q17/q18 'a co...exe') — e ficou 100% descoberta em sem-obra-54cfff (q02/q03 'ESSE TRABALHADOR COLOCANDO FAIXA PRETA').
- onde: D:\recapd-ambientes\producao\bin\anime_hardsub_detect.py e D:\recapd-ambientes\producao\bin\parceiro_marca.py
- como testar: Conferir o log [hardsub] de sem-obra-54cfff para verificar por que a legenda azul não foi coberta e permitir que a largura da caixa medida em >=720px cubra 100% da extensão horizontal das letras detectadas (com margem lateral de segurança nas sílabas extremas), testando nos 4 Shorts e em um controle negativo sem legenda.

## 12/11 21:09 PROPOSTA [CERTEZA] Sincronizar corte de cena com a locução, remover planos mortos/repetidos e evitar micro-cortes desconexos (gemini-4-argon)
- prova: Repetido nos 4 Shorts: sem-obra-7dbc42 (q05 e q08 inserem flashes de <1s de afogamento na piscina enquanto narra espera no cartório; q14/q15 mostram outra mulher na escada enquanto narra busca no jardim em 1ª pessoa), sem-obra-54cfff (q01 flash branco estourado; q07 sobra de 0,6s da cena anterior; q08-q12 foto estática da parede por >2s com 11.3% de movimento), sem-obra-72412c (q10/q11 mostram dutos e chapa vazia enquanto narra 'ossos de porco congelados saem da câmara fria', que só aparecem em q13 repetindo o take de q01) e how-does-a-snake-rattle-make-sound (q01-q05 3s estáticos com 7.2% de movimento; q13 corte escuro de 0,7s; q15-q18 repete plano estático inicial).
- onde: D:\recapd-ambientes\producao\bin\anime_segments.py (seleção, deduplicação e alinhamento de cenas com o áudio)
- como testar: Bloquear reutilização do mesmo intervalo de vídeo da fonte no mesmo Short, proibir sub-cortes < 1.2s fora de contexto, aplicar zoompan (Ken Burns) quando o movimento medido do trecho for < 15% e alinhar a troca de tomada ao início da frase correspondente no TTS; reprocessar sem-obra-72412c e sem-obra-7dbc42 e comparar as folhas de quadros.

## 12/11 22:14 PROPOSTA [CERTEZA] Aumentar margem horizontal do delogo e detectar hardsub centralizado (gemini-4-argon)
- prova: how-does-a-snake-rattle-make-sound_cap1_20261109 (q04, q05, q08) e think_cap1_20261109 (q15, q17) vazam palavras nas extremidades do delogo mesmo com tarja_largura_max=0.8 e tarja_letra=0.62 no limite; sem-obra-2b292a_cap1_20261109 (q01-q18) e sem-obra-70f464_cap1_20261109 (q04) ficaram com a legenda original inteira exposta no centro/base.
- onde: cortes_pipeline.py / função de detecção de hardsub e cálculo da bounding box do delogo
- como testar: Rodar a detecção de hardsub nos 4 vídeos acima e gerar folha de quadros verificando que a caixa cobre 100% da largura das legendas inferiores e também captura legendas posicionadas no terço central.

## 12/11 22:14 PROPOSTA [CERTEZA] Travar opacidade 100% sólida e desativar rotação 3D/duplicação na legenda dinâmica (gemini-4-argon)
- prova: sem-obra-2b292a_cap1_20261109 (q11 'CARNE', q13 'VEZES') renderizou palavras com opacidade quase nula sem preenchimento e duplicou 'CHOCADO' em q17; think_cap1_20261109 (q05 'LÁ' sobre 'CÉU', q06 'INSTANTE' achatado em linha horizontal) apresentou sobreposição de palavras ativas e distorção 3D ilegível.
- onde: Gerador de legendas ASS/renderizador de legendas palavra a palavra do pipeline de Cortes
- como testar: Renderizar novamente os trechos q05-q06 de think_cap1_20261109 e q11-q17 de sem-obra-2b292a_cap1_20261109 e inspecionar os quadros garantindo preenchimento sólido (#FFFF00 ou #FFFFFF) com borda preta e apenas um grupo ativo por vez.

## 12/11 22:14 PROPOSTA [CERTEZA] Validar ordem temporal dos recortes de vídeo contra os timestamps originais (gemini-4-argon)
- prova: think_cap1_20261109 inverteu a reação do amigo (q09) com a explosão do pássaro (q10-q12); sem-obra-2b292a_cap1_20261109 mostra o peixe já aberto em q05-q06 e volta para o peixe fechado em q07; sem-obra-70f464_cap1_20261109 mostra gameplay de Miles Morales (q13-q15) durante a fala sobre o jogo de PS4.
- onde: Módulo de montagem/seleção de cenas por timestamp no pipeline de Cortes
- como testar: Conferir no log de montagem dos 3 Shorts se os intervalos de tempo extraídos do vídeo-fonte estão em ordem estritamente crescente e alinhados aos trechos da transcrição original.

## 12/11 23:45 PROPOSTA [CERTEZA] Travar detecção de hardsub no terço inferior e cobrir com caixa exata em vez de delogo furado (gemini-4-argon)
- prova: Nos 4 Shorts do lote a legenda original vazou no rodapé: em sem-obra-dc6f15_cap1_20261109 (q01, q03) a tarja foi parar no topo enquanto 'VILAREJO'/'ESQUECIDO' ficaram expostos embaixo; em this-boy-saved-his-father-animation_cap1_20261109 (q01, q05, q06, q10) o delogo borrou a boca do personagem e vazou 'DESESPERO'; em sem-obra-8991d3_cap1_20261109 (q06) vazou 'LE... DO'; e em top-5-deadliest-animals-in-brazil_cap1_20261109 (q01) as legendas verdes ('ABELHA', 'JARARACA') ficaram sem cobertura.
- onde: Pipeline de detecção e cobertura de hardsub (cortes_pipeline.py / módulo de visão e filtro delogo/drawbox)
- como testar: Rodar a detecção de legenda queimada nos 4 vídeos-fonte do lote restringindo a busca de hardsub ao terço inferior (y > 60%) e validar na folha de quadros se a cobertura cobre 100% da caixa das letras sem subir para o rosto ou topo.

## 12/11 23:45 PROPOSTA [CERTEZA] Corrigir preset de legenda ASS/renderizador para limpar frame anterior, fixar cor clara com borda preta e respeitar safe zone fora de rostos (gemini-4-argon)
- prova: Em top-5-deadliest-animals-in-brazil_cap1_20261109 (q12 'AVISAR', q14 'PICADA', q16 'TRATAMENTO' colidindo com 'E NA QUARTA', q17 'POSIÇÃO') e sem-obra-8991d3_cap1_20261109 (q08 'TIGELA' fantasma com 'LEITE' cinza, q10 'DELA' marrom sem contorno, q17 'UMA MULHER' no focinho do tigre) e this-boy-saved-his-father-animation_cap1_20261109 (q01 'BEM' no olho, q02 'TEMPESTADE' na boca), as legendas saíram em cores escuras translúcidas sem contorno, acumularam palavras fantasmas na troca de corte e cobriram rostos.
- onde: Gerador de legendas palavra a palavra (.ass / filtro subtitles no pipeline de renderização de CORTES)
- como testar: Gerar 2 Shorts de teste e inspecionar q08, q10, q12 e q16 garantindo out-point estrito antes do próximo token, preenchimento 100% opaco amarelo/branco com outline preto >= 8px e posição abaixo do centro facial.

## 13/11 01:00 PROPOSTA [CERTEZA] Barrar sticker/placeholder de template e de CTA fora de contexto (LOCAL: MUNDO, CURTIR, waifu/personagem de anime) em vídeos reais (cw/claude-sonnet-5-5)
- prova: d3c366 q13-q16 ('LOCAL MUNDO' em vídeo de pescaria) e q15 (adesivo 'PACUS' sobre carpa-espelho); robô q18 ('CURTIR' +1 e personagem no trono sobre 'DISSO!'); nen q18 (anime em espartilho sobre churrasqueira, também risco de nudez/revisão). 3 Shorts do lote.
- onde: Módulo que insere stickers/adesivos e cards no render (função de overlay do cortes; provável cortes_stickers ou o passo 'palavras de impacto'). Verificar também o template de recap de manhwa vazando para nichos reais.
- como testar: Renderizar 5 Shorts de pesca, culinária e pets com stickers desligados para nichos reais e conferir por folha de quadros que não sobra 'LOCAL', 'CURTIR' nem personagem; depois comparar a nota de legibilidade do júri.

## 13/11 01:00 PROPOSTA [CERTEZA] Limitar a legenda nossa à zona segura (y <= 1580) e impedir 3 linhas e quebra para a base (cw/claude-sonnet-5-5)
- prova: nen q04, q06, q08-q10, q13, q15-q17 (y~1620-1730; 'EXTREMAMENTE' a menos de 60 px da borda em q10); d3c366 q06 ('nunca' em y~1720).
- onde: Função que monta o ASS/layout da legenda palavra a palavra (margem inferior, MarginV, regra de quebra de linha e largura máxima).
- como testar: Gerar o nen_cap1 e o d3c366_cap1 com MarginV fixo e máximo de 2 linhas, medir a caixa das letras em 1080x1920 e conferir y_max <= 1580 e x entre 60 e 1020 em todos os quadros.

## 13/11 01:00 PROPOSTA [CERTEZA] Sincronia cena x fala: o corte de cena segue o tempo da frase narrada, não a duração fixa da cena de origem (cw/claude-sonnet-5-5)
- prova: cf5541 q11 e q17 (a imagem mostra a 2ª e a 3ª isca enquanto a voz ainda explica a 1ª e a 2ª, cerca de 10 s adiantada); d3c366 q04 e q10 (cena presa mais de 3,5 s, corte tardio); robô q04 (corte a 2,70 s com a voz no meio da frase 1).
- onde: Função que casa o início/fim de cada tomada com os timestamps da voz (alinhamento por palavra) no cortes principal; provável ponto de ajuste: duração acumulada por cena versus tempo da primeira e última palavra da frase.
- como testar: Reprocessar o cf5541_cap1 com o corte ancorado na palavra-chave de cada frase (tolerância 0.3 s) e checar na folha de quadros que 'milho', 'massa' e 'larva' aparecem na imagem junto da fala.

## 13/11 01:00 PROPOSTA [CERTEZA] Fonte com legenda queimada sem cobertura: diagnosticar por que a detecção não cobriu (nen) ou cobriu estreito (cf5541) (cw/claude-sonnet-5-5)
- prova: nen q01 (legenda da fonte visível e nítida durante o vídeo todo, sem cobertura); cf5541 q06, q15, q16, q18 (letras vazando acima, abaixo e nas laterais do desfoque). tarja_largura_max já está em 0.8, o máximo permitido, então a largura não é o que dá pra mexer.
- onde: Passo de detecção de legenda queimada (visão: log '[hardsub] só N/6') e cálculo da caixa de cobertura (margem lateral e vertical do delogo). Conferir o log desses dois Shorts antes de qualquer decisão.
- como testar: Ler o log '[hardsub]' de nen e cf5541: se leu legenda e a caixa ficou curta, ampliar a margem da caixa do delogo sem passar do tamanho exato das letras; se NÃO leu, tratar como falso negativo da visão e rodar a folha de quadros com controle negativo.

## 13/11 02:11 PROPOSTA [CERTEZA] Legenda queimada da fonte ficou sem tarja/delogo em 4 de 4 Shorts do lote (cw/claude-sonnet-5-5)
- prova: q01 e q05 de sem-obra-36914e, q05/q09/q10/q16 de sem-obra-2be4ef, q01/q02 de he-finally-bought-his-first-sword e q01 de sem-obra-f2bd55 mostram a legenda da fonte visível. É o caso inverso da lição de 26/10 ('sem legenda = sem tarja'): aqui a fonte TEM legenda e a tarja não cobriu. Pode ser a visão que decidiu 'sem legenda' por engano (3 de 6 quadros perdem legenda que só aparece quando alguém fala), ou a tarja que não foi aplicada, ou a que foi aplicada fora do lugar. O log ainda não foi conferido: falta o '[hardsub] N/6' desses 4 Shorts.
- onde: detecção de hardsub da linha CORTES (função da visão que mede a faixa da legenda) e a etapa que aplica tarja/delogo
- como testar: Ler o log dos 4 Shorts e ver se saiu '[hardsub] só 0/6' ou '1/6'. Se sim, repetir a visão com folha de quadros em resolução >= 720 px, em quadros espaçados pelos momentos de fala, e conferir se passa a ler a legenda, com um controle negativo (vídeo sem legenda). Se o log disser que a visão leu legenda e a tarja não foi aplicada, o bug está na etapa de aplicação, não na detecção.

## 13/11 02:11 PROPOSTA [CERTEZA] Marca d'água da fonte (@inventoreact) aparece no centro do quadro e falta a marca do canal (cw/claude-sonnet-5-5)
- prova: he-finally-bought-his-first-sword q02 e sem-obra-f2bd55 q01 mostram '@inventoreact' no peito/centro, e o júri não vê '@novo_ia_agora_h3n'.
- onde: etapa de marca d'água/overlay do render final e a cobertura (delogo) da marca da fonte
- como testar: Renderizar 2 Shorts de fonte InventoReact e conferir em 3 quadros (início, meio, fim) que a marca da fonte sumiu e a nossa aparece. Se a regra for não mostrar marca nenhuma, só confirmar o delogo.

## 13/11 02:11 PROPOSTA [CERTEZA] Legenda palavra a palavra cai sobre rosto, sai pela borda e sobrepõe a palavra anterior (cw/claude-sonnet-5-5)
- prova: sem-obra-2be4ef q02, q08, q09 e q11: 'FORMATO', 'FECHADOS', 'REVELAM' e 'INTENSO' esticadas na horizontal, cortadas na margem, azul escuro sobre fundo escuro, sobre os olhos e com a palavra anterior ainda na tela. sem-obra-f2bd55 q11, q12 e q13: card cortado na borda esquerda e palavra sobre o rosto ou sobre o tweet. Os dois Shorts mostram deformação, camada que não limpa e posição fixa que ignora o conteúdo.
- onde: gerador da legenda (ASS/drawtext): escala horizontal (ScaleX), cor por personagem, limpeza da palavra anterior (tempo de fim) e checagem de margem x entre 60 e 1020
- como testar: Renderizar esses 2 roteiros de novo com um teste automático que acusa: texto fora de x 60–1020, mais de 1 palavra ativa no mesmo instante, escala horizontal fora de 100%, luminância da cor baixa sobre o fundo. Conferir q02, q08 e q11 do 2be4ef. Atenção: a dona prefere cores por personagem, então o piso de contraste deve corrigir só cores escuras demais, sem uniformizar.

## 13/11 02:11 PROPOSTA [GOSTO] Repetição de B-roll do mesmo take em menos de 10 s (cw/claude-sonnet-5-5)
- prova: sem-obra-2be4ef q01 repetido em q06 e q04 repetido em q09; sem-obra-f2bd55 repete o take da idol sorrindo da cena 1 no começo da cena 4. Se aparecer em mais lotes, vira regra de seleção de tomada; por ora é 2 Shorts.
- onde: seleção de tomadas por cena (escolha do trecho da fonte para cada frase do roteiro)
- como testar: Penalizar ou impedir o reuso do mesmo trecho dentro de uma janela de 10 s (ou exigir novo intervalo da fonte), rodar 5 Shorts e comparar a nota de retenção do júri.

## 13/11 03:20 PROPOSTA [CERTEZA] Conferir por que a tarja/apagado não foi aplicado em Shorts cuja fonte tem legenda queimada (cw/claude-sonnet-5-5)
- prova: 3f73ef, 08c410 e b3c748: o júri vê a legenda da fonte exposta de q01 até o fim, sem tarja. Só vale como defeito se o log disser que a visão LEU legenda (ex.: '[hardsub] 2/6' ou mais). Se o log disser '0/6', o júri errou e nada muda.
- onde: Passo de detecção de hardsub e aplicação da tarja no pipeline CORTES (função que decide tarja/delogo depois da visão; log do Short).
- como testar: Rodar o grep '[hardsub]' nos logs desses 3 Shorts. Se a visão leu legenda e a tarja não saiu, achar o ramo que descartou a tarja e reprocessar um deles. Controle negativo: um vídeo sem legenda continua sem tarja.

## 13/11 03:20 PROPOSTA [CERTEZA] O delogo/blur na legenda da fonte cobre só o centro e deixa as laterais legíveis (cw/claude-sonnet-5-5)
- prova: 354b36 q13: 'Eletro' (esquerda) e 'ético' (direita) nítidos fora do desfoque. 354b36 q01: letra 'B' e ')' visíveis sob o blur.
- onde: Cálculo da caixa de cobertura da legenda (largura/margens da faixa do delogo). tarja_largura_max já está em 0.8, o teto da faixa.
- como testar: Medir a caixa real das letras em resolução >= 720 px (lição de 27/10) e conferir que a cobertura vai de ponta a ponta da legenda, sem virar faixa grande. Rodar em 354b36 e checar q01 e q13.

## 13/11 03:20 PROPOSTA [CERTEZA] Manter a nossa legenda dentro da zona segura e sem colisão de linhas (cw/claude-sonnet-5-5)
- prova: 3f73ef q06 (legenda em y≈1620–1710), 08c410 q12 ('encanamento.' abaixo de y=1580), 3f73ef q11 ('DE PEIXES E' sobre 'NÃO TER LEVADO'), b3c748 q16 (sticker colado em x=0).
- onde: Renderizador da legenda palavra a palavra (posição vertical, margem lateral, fila de linhas ativas).
- como testar: Renderizar 3f73ef e 08c410 e medir o bbox da legenda em todos os quadros: y <= 1580, x entre 60 e 1020, uma linha ativa por vez.

## 13/11 03:20 PROPOSTA [CERTEZA] Destaques e stickers cobrindo a marca d'água, o rosto ou o objeto da ação (cw/claude-sonnet-5-5)
- prova: 354b36 q04, q05 e q10 (rosto coberto); 3f73ef q09 (peixe coberto); 08c410 q02, b3c748 q15 e q16 (@esportenoturno coberto).
- onde: Posicionamento dos stickers/palavras de impacto (zona proibida: marca d'água e rosto detectado).
- como testar: Detectar rosto e a região da marca d'água, mover o sticker para fora dessas áreas e conferir 354b36, 3f73ef e b3c748. Mantém o pedido da dona de palavras de impacto maiores e de lado.

## 13/11 03:20 PROPOSTA [GOSTO] A troca de cena está atrasada em relação ao início das frases (cw/claude-sonnet-5-5)
- prova: 354b36 q06, q09, q11 e q13 (frase 5 inteira dentro da cena 4, atraso acumulado) e b3c748 q04 e q06 (visual atrasado em relação ao roteiro).
- onde: Ajuste dos cortes de cena pelos tempos das frases (sincronia voz/cena).
- como testar: Comparar o instante de início de cada frase com o corte da cena em 354b36 e b3c748, tolerância de 0.3 s. Só vale se o atraso se repetir em mais Shorts do lote; fora do código de sincronia é proposta, não alavanca.

## 13/11 04:31 PROPOSTA [CERTEZA] Impedir CTA, sticker de curtir/inscrever e tela promocional no começo e no fim dos Shorts (cw/claude-sonnet-5-5)
- prova: Aparece em 3 Shorts do lote. Em sem-obra-6e3cfc, q16–q18 (~6 s finais) mostram a tela 'CAPÍTULO NOVO JÁ NA CINEFY'. Em sem-obra-e97798, q02 (~6 s) e q09 (~34 s) trazem o sticker de anime com CURTIR/INSCRITO, que também cobre a legenda. Em sem-obra-956252, q16 (19–21 s) traz o CTA gigante sobre o clímax. A regra fixa diz que produto nosso só entra no meio e só nas cópias TikTok/Insta, e o loop exige ação até o último frame.
- onde: Função que insere stickers/CTA na timeline (provável módulo de stickers do renderizador da linha CORTES). Também o corte do final do vídeo-fonte, para remover o cartão promocional do parceiro (Cinefy).
- como testar: Gerar 5 Shorts de fontes diferentes e conferir q01, q02 e os 3 últimos quadros de cada um, sem sticker de CURTIR/INSCRITO e sem cartela promocional. Depois comparar a retenção dos Shorts novos com os do lote atual.

## 13/11 04:31 PROPOSTA [CERTEZA] Medir e travar texto cortado nas bordas (cabeçalho e legenda fora da margem lateral) (cw/claude-sonnet-5-5)
- prova: Em sem-obra-6e3cfc, o cabeçalho 'SUA MORTE FOI PATETICA, MAS UM SISTEM' perde o 'A' na borda direita (q05, q06, q13) e perde o 'S' na borda esquerda (q07, q11). A legenda aparece cortada em q06 ('Venerável Hyohyo... com') e q08 ('Mestre Taoísta Hor'). O problema aparece só nesse Short e ainda não é padrão.
- onde: Função que desenha o cabeçalho e a legenda palavra a palavra (cálculo de largura do texto versus largura útil, quebra de linha automática).
- como testar: Seguir a lição de 28/10: montar a folha do TOPO no 1,5 s de todos os Shorts do dia (D:\tmp\folha_topo.py) e contar quantos têm texto cortado. Se for ≥2, aplicar auto-redução da fonte ou quebra de linha para manter margem de 60 px. Conferir com um título longo de teste.

## 13/11 04:31 PROPOSTA [CERTEZA] Evitar camadas de legenda duplicadas ou sobrepostas na mesma palavra (cw/claude-sonnet-5-5)
- prova: Só em sem-obra-ed1f07: q12 mostra 'FINALMENTE' em amarelo empilhada sobre 'ATÉ QUE FINALMENTE', e q08 mostra 'TREMENDO' em tarja vermelha sobre 'HORA'. Ainda é 1 Short; precisa repetir em outro para virar padrão.
- onde: Renderizador da legenda palavra a palavra: o destaque da palavra ativa deve substituir a linha em vez de adicionar uma camada nova.
- como testar: Renderizar 3 Shorts com palavras de destaque coloridas e conferir quadro a quadro, nos cortes de palavra, que só existe uma camada ativa.

## 13/11 05:40 PROPOSTA [CERTEZA] Camada de legenda palavra a palavra: nunca duas palavras ao mesmo tempo (cw/claude-sonnet-5-5)
- prova: fda53b q14: ENGRAVIDOU em dois estilos ao mesmo tempo. 719ae1 q13: SEM amarelo sobre o bloco MAR. 719ae1 q09: ACHA ficou na tela depois de CARRETILHA. fda53b q05: MEU vazando atrás de BICHINHO.
- onde: Renderizador de legenda palavra a palavra (ASS/ffmpeg drawtext, função que gera os eventos por palavra). Procurar eventos com intervalos sobrepostos e estilos alternados (adesivo amarelo e caixa rosa).
- como testar: Gerar o Short 719ae1 e o fda53b de novo e listar os eventos da legenda. Garantir que end(i) <= start(i+1) e que há uma só camada ativa por instante. Conferir os quadros q09, q13 e q14.

## 13/11 05:40 PROPOSTA [CERTEZA] Margem lateral e zona segura vertical da legenda (cortada nas bordas, y > 1580) (cw/claude-sonnet-5-5)
- prova: e0545c q16: 'conheceu' e 'vesti' cortadas nas duas bordas e no rodapé. 719ae1 q03: caixa vermelha com x <= 0. cfe227 q01: legenda em y ≈ 1650-1710 em quase todos os quadros. O e0545c q16 também mudou para texto minúsculo, então vale checar o fallback de fonte e de tamanho.
- onde: Cálculo de largura e posição do bloco de palavra (auto-ajuste de fonte). Falta limitar a palavra à caixa x=60..1020 e y<=1580. Palavras longas ('profissionais', 'CARRETILHA') devem reduzir a fonte em vez de vazar.
- como testar: Rodar uma lista de palavras longas e frases com 3 palavras e medir a caixa renderizada. Falhar o teste se algum pixel de texto ficar fora da área segura. Reproduzir o cfe227 e o e0545c.

## 13/11 05:40 PROPOSTA [CERTEZA] Contraste das cores de destaque por personagem (cw/claude-sonnet-5-5)
- prova: cfe227 q12: REAÇÃO em vermelho escuro sobre camiseta preta. cfe227 q01: JOGADORES em vermelho escuro sobre cinza. fda53b q12: ACABADO só em contorno fino sobre papel claro. e0545c q05: amarelo sobre pele clara e camisa branca. cfe227 q03: ciano fino sobre monitor estourado.
- onde: Paleta de cores por personagem e estilo da palavra (preenchimento, contorno). Exigir contorno preto >= 6 px e preenchimento opaco. Rejeitar tons escuros ou sem contorno na paleta.
- como testar: Rodar as paletas atuais por um verificador de contraste (luminância do preenchimento contra o contorno) e checar se alguma combinação falha. Reproduzir os quadros q12 e q03 do cfe227.

## 13/11 05:40 PROPOSTA [GOSTO] Evitar legenda sobre boca e queixo (posição adaptativa) (cw/claude-sonnet-5-5)
- prova: e0545c q06 (adesivo LOGO tapando a boca), q03 e q05; fda53b q12 e q13. Preferência registrada em 27/10: palavras de impacto maiores, de lado.
- onde: Posicionamento vertical da legenda. Usar a detecção de rosto que o pipeline já tem para deslocar a palavra para baixo ou para o lado do rosto, dentro da zona segura.
- como testar: Medir em 20 Shorts a fração de quadros com sobreposição entre a caixa da palavra e a caixa do rosto, antes e depois. Mudar uma coisa só e comparar a nota de legibilidade.

## 13/11 05:40 PROPOSTA [CERTEZA] Verificar a tarja em cfe227 (fonte com legenda queimada visível sem tarja) (cw/claude-sonnet-5-5)
- prova: Só 1 Short: o júri diz que a legenda da fonte aparece em quase todos os quadros sem tarja. Falta o log do Short ([hardsub] n/6) para saber se a visão leu ou não a legenda. Sem esse log, não é padrão nem defeito provado.
- onde: Log de produção do cfe227 e a função de detecção de legenda queimada (hardsub). Se a visão leu 0/6 numa fonte com legenda real, é falso negativo.
- como testar: Abrir a folha de 6 quadros do cfe227 e o log. Se houver legenda real e a visão não leu, repetir a detecção com quadros >= 720 px. Se aparecer em outro Short, vira padrão.

## 13/11 05:40 PROPOSTA [GOSTO] Ritmo: cenas paradas e final vazio (movimento) (cw/claude-sonnet-5-5)
- prova: 719ae1 q07/q08 e q16-q18 (>10 s parados, 10,1% de movimento). fda53b q04 (13 s no mesmo ambiente) e q18 (80% do quadro é parede). cfe227 q11-q12 (plano parado >2 s). Padrão de 3 Shorts, mas é corte de cena, então não há alavanca.
- onde: Seleção e duração de cenas (corte por movimento medido) e enquadramento do crop vertical, que não segue o foco (fda53b q06 e q16, cfe227 q16).
- como testar: Impor duração máxima por cena sem movimento (ex.: 4 s) e centralizar o crop no sujeito. Comparar o movimento medido e a nota de movimento antes e depois em 10 Shorts.

## 13/11 06:50 PROPOSTA [CERTEZA] Legenda/sticker nunca sobre rosto, olhos ou bico (cw/claude-sonnet-5-5)
- prova: eb6c7b q05, q06 e q11 (legenda sobre olhos e bico da coruja); a96e79 q03 (sobre o rosto do apresentador). Repete em 2 Shorts.
- onde: Função que posiciona a legenda palavra a palavra e os stickers (render da legenda, cortes_legenda ou equivalente).
- como testar: Rodar o render nesses 2 Shorts e conferir os quadros citados: a legenda deve ficar fora da caixa do rosto (detecção de rosto/animal) ou ir para o terço inferior seguro.

## 13/11 06:50 PROPOSTA [CERTEZA] Limpar camadas de texto e stickers residuais ao trocar de palavra (cw/claude-sonnet-5-5)
- prova: a96e79 q14/q15 (VENCEU, VENCE, VITÓRIA!, MILAGROSAS empilhados e fantasma 'VOCÊ'); eb6c7b q07 (fantasma '250º' sob 'MAIS DE'); 7f259b q13 ('A GALERA' sobre 'NISSO'); f0b6a1 q11/q12 (sticker cobrindo a legenda).
- onde: Render de overlays: o tempo de saída (fade-out) de cada palavra/sticker e a colisão entre camadas.
- como testar: Gerar um Short com palavras seguidas e frases com stickers; verificar nos quadros que só há uma palavra ativa por vez e que o sticker não cobre a legenda.

## 13/11 06:50 PROPOSTA [CERTEZA] Contraste mínimo da legenda (palavras quase invisíveis) (cw/claude-sonnet-5-5)
- prova: 7f259b q04 ('TÃO' marrom no escuro) e q13 ('NISSO' rosa apagado); a96e79 q11 ('QUASE' verde translúcido) e q01 ('PEÇA' prateada em fundo claro); f0b6a1 q04 (opacidade ~0). Repete em 3 Shorts.
- onde: Paleta de cores por palavra/personagem e opacidade da animação de entrada, no módulo de legenda.
- como testar: Checar a razão de contraste de cada cor contra o fundo; impor cor mínima clara com contorno escuro e opacidade 100% após a entrada.

## 13/11 06:50 PROPOSTA [CERTEZA] Verificar se a tarja deixou de ser aplicada (antes de culpar) (cw/claude-sonnet-5-5)
- prova: 7f259b q01 e f0b6a1 q01/q02 dizem 'tarja ausente com legenda da fonte exposta'. Falta o log '[hardsub]' deles para provar. Os 'pixel smear' no eb6c7b são na faixa inferior, ligados ao delogo.
- onde: Log de produção desses 3 Shorts ('[hardsub] só 0/6') e o filtro de cobertura (delogo) no eb6c7b.
- como testar: Ler os logs: se a visão leu legenda e a tarja não entrou, é bug do pipeline; se não leu, descartar. No eb6c7b, comparar o quadro antes/depois do delogo para ver o estiramento de pixels.

## 13/11 08:07 PROPOSTA [CERTEZA] Legenda palavra a palavra sobrepondo a palavra anterior ou um sticker (cw/claude-sonnet-5-5)
- prova: d7f768 q12 ('E A' sobre 'NOSSA' vira 'NEASA'), 22bb27 q10 ('ATÉ OS' sobre 'MESMOS' vira 'M ATÉ OS MOS'), 22bb27 q13 ('LONDRES' congelada em cima de 'DE LONDRES'), 69b7d1 q02 (sticker sobre 'PORQUE'). São 3 Shorts com palavras ou camadas desenhadas ao mesmo tempo na mesma posição.
- onde: Renderizador da legenda palavra a palavra (ASS/drawtext) e camada de stickers/cards. Provável: onde o fim de cada palavra é calculado. Quando o tempo de uma palavra é encurtado, a anterior ainda não saiu.
- como testar: Renderizar os 3 Shorts, extrair quadros nos instantes citados (25 s no d7f768, 19 a 23 s no 22bb27) e conferir que só uma palavra está ativa por quadro. Para cada palavra, forçar o fim em no máximo o início da seguinte. Conferir também que stickers e cards não ficam na mesma caixa da legenda.

## 13/11 08:07 PROPOSTA [CERTEZA] Legenda com preenchimento translúcido ou escuro, ilegível no celular (cw/claude-sonnet-5-5)
- prova: d7f768 q07 ('LÍNGUA', miolo vazado com contorno roxo) e q14 ('RENDER', preenchimento escuro sobre feijoada). 461215 q06 ('IGNOREI' avermelhado translúcido) e q07 (letras apagadas sobre o rosto). Em 2 Shorts, estilos de cor ou personagem saem sem contraste.
- onde: Paleta de cores/estilos por personagem ou por palavra de impacto na geração da legenda. Provável: o estilo 'destaque' usa alfa menor que 100% ou cor escura.
- como testar: Listar as cores e o alfa de todos os estilos. Impor preenchimento opaco claro ou amarelo, com contorno preto grosso, a todos. Se quiser manter cores por personagem, escolher só entre as claras. Renderizar os dois Shorts e conferir os quadros citados.

## 13/11 08:07 PROPOSTA [CERTEZA] Legenda ou badge sobre rosto/boca do personagem (cw/claude-sonnet-5-5)
- prova: 22bb27 q08 (badge 'A PIADA' sobre boca e queixo), q16 ('SEU' sobre os lábios), q13 (palavra fixa sobre o queixo); 461215 q03 e q07; 69b7d1 q04 (sticker sobre olhos e nariz). Em 3 Shorts, a posição vertical fixa da legenda cobre o rosto em planos próximos.
- onde: Posicionamento vertical da legenda e dos stickers. Provável: a altura é fixa e não considera a cena. Pode usar detecção de rosto por cena, já que a visão existe no pipeline, e descer ou subir a legenda dentro da zona segura.
- como testar: Em 10 cortes com talking head, comparar a caixa da legenda com a caixa do rosto (detecção de rosto). Medir quantos quadros colidem antes e depois do deslocamento. Alvo: zero colisão com boca e olhos.

## 13/11 08:07 PROPOSTA [CERTEZA] Reuso de B-roll e imagem fora da fala (adiantada ou atrasada) (cw/claude-sonnet-5-5)
- prova: d7f768: o take da concha de q01 volta em q12 e q13, e a feijoada aparece em 'E A NOSSA'. 69b7d1: o pênalti de q03 volta em q07, e Neymar chorando de q06 volta em q08 e q10, enquanto a fala já cita o Mbappé em q09 e q10. 461215: 'NUM SKATE' cai sobre um borrão verde em q16, e o skate já tinha aparecido em q14. É um padrão de seleção e ordem de clipes em 3 Shorts.
- onde: Seleção e ordenação de takes por cena (função que casa trecho do roteiro com o clipe da fonte). Provável: falta uma lista de takes já usados e uma checagem da distância entre o tempo da palavra-chave e a troca de plano.
- como testar: Marcar o hash perceptual de cada take usado no Short e vetar o reuso dentro do mesmo Short. Medir o atraso entre a palavra-chave da fala e a troca de imagem, com tolerância de 0,3 s. Rodar nos 3 Shorts e conferir os quadros citados. Descartar quadros sem sujeito (borrão) como candidatos.

## 13/11 09:41 PROPOSTA [CERTEZA] Legenda palavra a palavra tampando rosto e boca (cw/claude-sonnet-5-5)
- prova: 22bb27 q08 e q16 (legenda sobre a boca e o queixo); 461215 q03 e q07 (sobre a testa e o rosto); ed2afc q05 e q11 (sobre a bochecha e os olhos). Defeito em 3 Shorts do lote.
- onde: Função que posiciona a legenda no render (y da legenda palavra a palavra). Provavelmente no módulo de legenda da linha CORTES; o arquivo exato precisa ser conferido.
- como testar: Detectar o rosto na janela de cada palavra (por exemplo, o rosto já medido na cena) e descer a legenda para o terço inferior (y entre 1200 e 1450) quando houver sobreposição. Rodar nos 3 Shorts acima e conferir os quadros q08, q16, q03, q07, q05 e q11.

## 13/11 09:41 PROPOSTA [CERTEZA] Texto, card e sticker cortados na margem lateral (< 60 px) (cw/claude-sonnet-5-5)
- prova: 461215 q01 ('QUERENDO' com o Q fora da tela); ed2afc q17 (card 'CONVERSA' exibido como 'NVERSA').
- onde: Render de cards e stickers e cálculo de x da legenda. Falta clamp de x entre 60 e 1020.
- como testar: Aplicar clamp horizontal (x entre 60 e 1020) a todo overlay e re-renderizar 461215 e ed2afc. Conferir que nenhum texto toca a borda.

## 13/11 09:41 PROPOSTA [CERTEZA] Card comparativo com fonte minúscula e frase truncada (cw/claude-sonnet-5-5)
- prova: 88b8f9 q09 a q11 (rótulos < 24 px, 'EM SEGUNDOS E' e 'O BANQUETE DOS' cortados); ed2afc q16 e q17 (mensagens do chat < 34 px e sticker cobrindo a linha 3 do card).
- onde: Template do card comparativo e do card de conversa.
- como testar: Impor corpo mínimo de 34 px e quebra de frase completa ou omissão do card se não couber. Re-renderizar os 2 Shorts. Antes, confirmar no log se o 'EM SEGUNDOS E' é o card nosso ou a legenda queimada da fonte, pois 88b8f9 q10 sugere legenda da fonte à mostra.

## 13/11 09:41 PROPOSTA [CERTEZA] Legenda com cor translúcida ou baixo contraste (cw/claude-sonnet-5-5)
- prova: 461215 q06 (vermelho escuro translúcido) e q07 (letras apagadas); 88b8f9 q13, q15 e q17 (magenta e azul finos sobre a garrafa); ed2afc q05 (amarelo-esverdeado apagado).
- onde: Paleta de destaque por personagem ou palavra de impacto. Provável bug de opacidade ou contorno na cor por personagem.
- como testar: Forçar opacidade 100%, contorno preto >= 6 px e luminância mínima nas cores por personagem. Medir o contraste nos quadros citados. Isso preserva a preferência da dona por cores por personagem, só corrige as que ficam invisíveis.

## 13/11 09:41 PROPOSTA [GOSTO] Cortes ping-pong entre dois planos do mesmo sujeito (cw/claude-sonnet-5-5)
- prova: 22bb27 q16 a q18 (perfil, frente, perfil em menos de 4 s); 461215 q05 a q07 (parque, close, parque); ed2afc q15 a q18 (rei, protagonista, rei, protagonista).
- onde: Seleção e ordem de tomadas por cena (corte de cena). Hoje parece alternar fontes de B-roll sem conferir a continuidade.
- como testar: Medir quantos retornos A-B-A existem por Short em 10 Shorts antes e depois. Testar com a regra de não voltar ao plano anterior em menos de 5 s. Comparar a retenção e a nota do júri. Uma mudança por vez.

## 13/11 09:41 PROPOSTA [CERTEZA] Legenda duplicada ou sobreposta na mesma posição (cw/claude-sonnet-5-5)
- prova: 22bb27 q10 ('M ATÉ OS MOS', 'MESMOS' sob 'ATÉ OS') e q13 ('LONDRES' congelada sob 'DE LONDRES'); 461215 q06 (duas camadas em estilos diferentes).
- onde: Camada de legenda e destaque: o destaque de palavra de impacto não é desligado quando a palavra seguinte entra.
- como testar: Garantir que há uma única camada ativa por instante (fim da anterior = início da próxima). Re-renderizar 22bb27 e 461215 e checar q10, q13 e q06.

## 13/11 10:50 PROPOSTA [CERTEZA] Legenda palavra a palavra fora do rosto e dentro da zona segura (cw/claude-sonnet-5-5)
- prova: Legenda ou sticker sobre boca, olhos ou queixo em 22bb27 q08 e q16, 461215 q03 e q07, ed2afc q05 e q11. Texto encostado ou cortado na margem esquerda em 461215 q01 e ed2afc q17.
- onde: Módulo que renderiza a legenda ASS/karaokê (posição Y e margens, provavelmente a função de montagem do ASS em cortes_*). Verificar também os cards de conversa e comparativos.
- como testar: Rodar 5 Shorts de talking head, extrair a folha de quadros e medir: nenhuma caixa de texto com x<60 ou x>1020. Com detecção de rosto, nenhuma sobreposição da legenda com a região da boca. Comparar a nota de legibilidade antes e depois.

## 13/11 10:50 PROPOSTA [CERTEZA] Uma única camada de legenda ativa por vez (sem palavra congelada) (cw/claude-sonnet-5-5)
- prova: 22bb27 q10: 'ATÉ OS' desenhado em cima de 'MESMOS', resultando em 'M ATÉ OS MOS'. 22bb27 q13: 'LONDRES' congelada em cima enquanto 'DE LONDRES' aparece embaixo. ed2afc q16: sticker em cima do texto do card.
- onde: Geração dos eventos de legenda (fim de cada palavra vs início da seguinte, estilos de destaque/adesivo). Provável: o evento de destaque não é encerrado quando a próxima palavra entra.
- como testar: Gerar o ASS desses 2 Shorts e checar por script que nenhum par de eventos se sobrepõe no tempo na mesma região. Depois renderizar e conferir q10 e q13 do 22bb27.

## 13/11 10:50 PROPOSTA [CERTEZA] Piso de contraste e opacidade nas cores de destaque da legenda (cw/claude-sonnet-5-5)
- prova: Legenda translúcida ou de cor tênue (magenta, azul fino, avermelhado, amarelo-esverdeado) em 461215 q06 e q07, ed2afc q05, 88b8f9 q13, q15 e q17. O júri as descreve como praticamente invisíveis no celular.
- onde: Paleta de cores por personagem/destaque (função que sorteia a cor do destaque). Impor opacidade 100%, traço preto e luminância mínima.
- como testar: Calcular o contraste do preenchimento contra o traço e contra o fundo do quadro nos mesmos 3 Shorts, e rejeitar cores abaixo do limite. Reconferir as notas de legibilidade.

## 13/11 10:50 PROPOSTA [GOSTO] Corte de cena adiantado ou atrasado em relação à palavra falada (cw/claude-sonnet-5-5)
- prova: 461215 q14/q16 (skate mostrado antes do 'NUM SKATE'), ed2afc q12 (fala 'NUM CALABOUÇO' sobre a floresta), 88b8f9 q06 ('SÓ QUE DO NADA' com a cobra aparecendo 5 s depois), 22bb27 q03. Também há ping-pong de planos em 22bb27 q16-q18, 461215 q05-q07 e ed2afc q13-q18.
- onde: Função que associa cena à frase (alinhamento tempo da voz × cena) e o seletor de cortes. Pode ser tolerância de alinhamento ou um atraso fixo.
- como testar: Medir em 10 Shorts o desvio entre o início da frase e o início da cena que a ilustra (meta <=0,3 s). Testar um deslocamento de cena -0,3 s num lote controlado e comparar a retenção.

## 13/11 10:50 PROPOSTA [CERTEZA] Verificar se a fonte tinha legenda queimada nos Shorts com texto da fonte à mostra (cw/claude-sonnet-5-5)
- prova: 88b8f9 q09-q11 mostra 'ANTES EM SEGUNDOS E' e 'AGORA O BANQUETE DOS' à vista. ed2afc q01 mostra a marca d'água '@cenareact-f3j' no centro durante quase todo o vídeo. Ainda não sei se é legenda queimada, card nosso ou marca d'água, e não há log '[hardsub]' para provar.
- onde: Log do Short 88b8f9 (linha '[hardsub] ... lido/N') e o módulo de cobertura (delogo). Para a marca d'água, o delogo ou recorte da região central.
- como testar: Abrir os logs desses 2 Shorts. Se a visão leu legenda e não cobriu, é falha de tarja. Se a visão não leu, não é defeito. Para a marca d'água, aplicar o delogo na região e conferir a folha de quadros.

## 13/11 12:00 PROPOSTA [CERTEZA] Remover/cobrir o @ do canal de origem no topo (e conferir qual @ deveria aparecer) (cw/claude-sonnet-5-5)
- prova: ed2afc q01 e 23473f q01 a q18 mostram '@cenareact-f3j' no topo, centrado, durante quase todo o vídeo. O canal da postagem é @novo_universo_ia_d6s. A regra fixa da dona proíbe @ na tela, e esse é o @ de outra linha.
- onde: etapa de render/overlay do topo (onde a marca do canal é desenhada) e a função que escolhe o handle por canal; checar também se o @ vem queimado na fonte e precisa de delogo no topo
- como testar: Rodar o Short sem-obra-23473f e o sem-obra-ed2afc, tirar uma folha do TOPO no 1,5 s e no meio (D:\tmp\folha_topo.py) e confirmar que o @ é o do canal certo, ou que não há @. Depois varrer os Shorts do dia com a mesma folha para medir quantos saíram com o @ errado.

## 13/11 12:00 PROPOSTA [CERTEZA] Prender a legenda palavra a palavra à zona segura lateral (x entre 60 e 1020), reduzindo o corpo em vez de cortar (cw/claude-sonnet-5-5)
- prova: 461215 q01 ('Q' de QUERENDO fora da borda), ed2afc q17 (início de CONVERSA cortado, aparece 'NVERSA') e 23473f q17 (ARREMESSA com glow a menos de 60 px da borda). O defeito é objetivo e se repete em 3 dos 4 Shorts.
- onde: função que calcula a posição e a largura de cada palavra da legenda (render ASS/karaokê); aplicar clamp de x e, se a palavra for larga, escala automática do corpo. Os cards ('CONVERSA') têm o mesmo problema: conferir o mesmo clamp.
- como testar: Renderizar palavras longas (ARREMESSA, QUERENDO, CONVERSA) com o efeito de brilho/glow e medir a caixa com a largura real do texto: x_min >= 60 e x_max <= 1020 em 1080 px. Rodar nos 3 Shorts acima.

## 13/11 12:00 PROPOSTA [CERTEZA] Piso de contraste e opacidade da legenda (preenchimento opaco, contorno grosso) e posição fora do rosto (cw/claude-sonnet-5-5)
- prova: Palavras translúcidas ou apagadas em 461215 q06 e q07 ('IGNOREI' avermelhado, 'SÓ PRA NÃO SAIR'), 88b8f9 q15 e q17 ('SEM' magenta tênue, 'RESOLVEU' azul fino) e 23473f q11 e q15 (cinza-esverdeado sobre verde). Legenda sobre o rosto em 461215 q07, ed2afc q11 e q05, e sobre a ação em 88b8f9 q13 e 23473f q18.
- onde: paleta/estilo da legenda por personagem (cores e fontes) e o posicionador da legenda; restringir as cores sorteadas a um conjunto com contraste mínimo sobre a cena e evitar o centro do rosto detectado
- como testar: Calcular o contraste entre o preenchimento e o fundo atrás da caixa em cada quadro dos 4 Shorts. Reprovar abaixo de 4.5:1 ou opacidade menor que 100%. Reprovar também se a caixa cobrir a região do rosto detectada no mesmo quadro. Comparar a nota de legibilidade no lote seguinte.

## 13/11 12:00 PROPOSTA [GOSTO] Sincronia da imagem com o sujeito narrado (personagem/ação adiantada ou atrasada) (cw/claude-sonnet-5-5)
- prova: ed2afc q01 ('O VELHO VIROU' sobre o jovem), 88b8f9 q06 e q14 (a fala 'DO NADA' antecipa uma cena que só vem 5 s depois e 'PREDADOR' aparece quando o animal já saiu) e 461215 q14 e q16 ('NUM SKATE' aparece sobre um borrão, o plano de skate já tinha passado). Aparece em 3 Shorts, mas o júri só vê quadros soltos. Antes de mexer, conferir no roteiro.txt e nos tempos da voz.
- onde: etapa que casa a cena com a palavra falada (alinhamento de cena por tempo da voz) e o filtro que descarta tomadas desfocadas ou escuras (461215 q16, 23473f q17)
- como testar: Para 3 Shorts, comparar o tempo da palavra-chave na voz com o início da cena correspondente (tolerância de 0,5 s). Medir antes e depois a nota de movimento e história, em um lote de pelo menos 8 Shorts. Mexer em uma coisa só por vez.

## 13/11 13:11 PROPOSTA [CERTEZA] Cor/contorno da legenda palavra a palavra: preenchimento escuro e translúcido some no fundo (cw/claude-sonnet-5-5)
- prova: Em 4 de 4 Shorts: parasyte q14 ('CACHORRO' transparente sobre focinho preto), b36464 q03/q08/q02/q16 ('MOLEZA' azul-escuro, 'GALHADAS' verde-oliva), d79377 q06/q12 ('NISSO' e 'ASSISTIR' cinza/verde-escuro), 421860 q11 ('MANCHA' verde-escuro). Todas são cores escuras por personagem/palavra de impacto sem contorno claro.
- onde: Renderizador da legenda palavra a palavra (a função que escolhe a cor da palavra e o traçado; procurar a paleta de cores por personagem/impacto no módulo de legenda da linha CORTES).
- como testar: Forçar piso de luminância no preenchimento (ou contorno claro/preto de 6–10 px quando o fundo for escuro), regerar os 4 Shorts e conferir os quadros citados com a folha de quadros. Respeita a preferência da dona por palavras de impacto maiores e cores por personagem, só impedindo cores ilegíveis.

## 13/11 13:11 PROPOSTA [CERTEZA] Legenda sai pela borda esquerda da tela (palavra cortada) (cw/claude-sonnet-5-5)
- prova: 421860 q06: 'COLHER/ESCOLHER' com o início fora da tela. Visto em 1 Short, então só proposta de verificação, não padrão.
- onde: Posicionamento horizontal da palavra na legenda (clamp de x ao calcular a largura do texto), módulo de legenda.
- como testar: Medir a largura da palavra maior e aplicar clamp com margem de 60 px; procurar nos próximos lotes se repete em >= 2 Shorts.

## 13/11 13:11 PROPOSTA [CERTEZA] Duas camadas de legenda ativas ao mesmo tempo / resíduo fantasma (cw/claude-sonnet-5-5)
- prova: parasyte q11 ('REVELOU' duplicado), d79377 q14/q16/q17 (resíduo de 'BRAÇO' e 'VERDADE' sobrepostos), 421860 q01 ('OLHA' vazando). Repete em 3 Shorts.
- onde: Renderização das camadas de legenda (ASS/overlay): conferir se um evento termina exatamente no início do próximo e se o estilo de 'impacto' não é desenhado junto com o estilo normal.
- como testar: Extrair o frame do instante exato de cada troca de palavra nos Shorts citados e contar eventos ativos; deve haver no máximo 1 por tempo.

## 13/11 13:11 PROPOSTA [CERTEZA] Marca do canal coberta por seta/card e marca de outro canal visível (cw/claude-sonnet-5-5)
- prova: parasyte q15 (card 'ALERTA MONSTRO' sobre @manhwareact-ia), d79377 q07 (seta sobre @historiasemframes), 421860 q01 (@inventoreact da fonte visível, canal oficial diferente). Dois Shorts com sobreposição de grafismo sobre a marca própria.
- onde: Posição dos cards/setas versus a posição da marca d'água do canal (módulo de overlays); e cobertura da marca da fonte.
- como testar: Proibir overlays na faixa y=160–220 e conferir os quadros citados. A marca da fonte precisa de checagem à parte, pois não sei se o júri leu o canal certo.

## 13/11 13:11 PROPOSTA [GOSTO] Cortes de cena em desacordo com a fala (equipamento/objeto trocado) (cw/claude-sonnet-5-5)
- prova: b36464 q04/q06/q09 (carretilha x molinete) e 421860 q10 (fala 'a molecada' sobre caneta mágica). Repete em 2 Shorts, mas depende da sincronia entre fala e cena, não do texto.
- onde: Alinhamento de cena com as palavras-chave do roteiro (seleção/corte de cena e sincronia fala-imagem).
- como testar: Para cada substantivo-chave do roteiro, checar se a cena exibida no instante da fala corresponde; começar pelos dois Shorts citados.
