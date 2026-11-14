
## 27/10 00:44 [CERTEZA] Ajustar safe zone do gancho de abertura para evitar sobreposição facial (agy/gemini-3.8-flash-high)
- prova: No vídeo 6d2a o gancho 'NINGUÉM ESPERAVA ESSE PODER SURREAL' cobriu os olhos e testa do protagonista (legibilidade 5.5); no 5FDt o gancho 'O JOGO VIROU REALIDADE MORTAL' cobriu boca e queixo (legibilidade 4.0, retenção 4.5).
- onde: anime-pipeline.py / fx_clips.py (função de renderização da tarja/texto de gancho de abertura)
- como testar: Renderizar amostra dos primeiros 5 segundos de 6d2a e 5FDt e verificar se a margem superior do texto preserva integralmente o rosto do personagem.

## 27/10 00:44 [CERTEZA] Limitar sustentação de plano estático a 4s e forçar movimento contínuo no final (agy/gemini-3.8-flash-high)
- prova: No 6d2a o trecho 8 permaneceu 10s preso em imagem única com movimento de 6.2% e o encerramento mediu 6.1%; no 5FDt a cena entre 2339s e 2348s travou por >9s com 16.1% e o desfecho (2868s-2875s) marcou apenas 6.7% de movimento.
- onde: fx_clips.py / _movimento ou anime_segments.py (limite de permanência de plano estático a 4s e slow zoom/pan contínuo até o fade final)
- como testar: Gerar trecho de 30s nos pontos críticos (2339s-2348s e encerramento de 5FDt) e rodar juri_longo.py para validar movimento ≥ 20% e ausência de quadros parados.

## 27/10 00:44 [CERTEZA] Remover caixas de sistema e balões de diálogo em inglês da fonte via delogo/inpaint (agy/gemini-3.8-flash-high)
- prova: Em 6d2a caixas '[SYNTHESIZE DESIRED NUTRIENTS]' e balões 'HMM?'/'Y-YES' colidiram com a legenda; em 5FDt balões 'WHOA...' e manchetes 'ASTEROID...' apareceram sem tratamento, rebaixando a legibilidade para 4.0.
- onde: marca_site.py / anime_legenda_fonte.py (aplicação do filtro delogo do ffmpeg nas áreas de texto da scan gringa)
- como testar: Processar os quadros com caixas de sistema de 6d2a e 5FDt via delogo e certificar a remoção limpa do texto em inglês antes da gravação da legenda em português.

## 27/10 00:44 [CERTEZA] Corrigir separação de palavras no karaokê e desativar renderização da tag de narrador (agy/gemini-3.8-flash-high)
- prova: No 5FDt ocorreu fusão indevida de palavras ('atingiro' em vez de 'atingir o') e em ambos os vídeos etiquetas técnicas ('Kkvirjao', 'Omelhormanhwa') foram gravadas sobre a legenda, violando a regra fixa da dona e derrubando a retenção do 6d2a para 3.0.
- onde: anime_segments.py (bloco dono_rev e rotina de geração de estilos/tags no arquivo de legendas .ass)
- como testar: Gerar arquivo .ass do trecho de troca de narradores do 5FDt e verificar se os espaços delimitadores são preservados no highlight e se nenhuma tag de identificação é desenhada.

## 29/10 18:51 [CERTEZA] Corrigir truncamento da última palavra/frase e congelamento de ~7s no final do vídeo (gemini-4-argon)
- prova: gF-1j3NGxq8 cortou 'resumindo' para 'resumin.' no fechamento (q24); BTG0NRDWHB0 congelou o quadro final por ~7s (q29-q30) e cortou a oração em 'manda nessa,'; C6YGjXsJFTI ficou estático nos últimos 7s (q25-q27, movimento 8.1%).
- onde: anime_tts.py / montagem final de áudio-vídeo e alinhamento SRT/Whisper no encerramento
- como testar: Renderizar o trecho final de gF-1j3NGxq8 e BTG0NRDWHB0 conferindo que o áudio tem margem (padding/fade-out) após o último fonema, a legenda exibe a palavra inteira e o último painel mantém movimento (Ken Burns) até o fim.

## 29/10 18:51 [CERTEZA] Travar pan/crop 16:9 dentro de um único painel sem atravessar divisórias ou duplicar buffer (gemini-4-argon)
- prova: BTG0NRDWHB0 (movimento 4.0) parou sobre a costura horizontal entre dois painéis distintos; C6YGjXsJFTI (legibilidade 4.5 / movimento 5.0) teve split horizontal duplicando os mesmos personagens em cima e embaixo e trecho parado de 9.8s (movimento 8.9% em BTG0NRDWHB0).
- onde: fx_clips.py (_movimento / cálculo de clamping do crop e detecção de bordas/gutter de painel)
- como testar: Rodar o recorte nos quadros de falha de C6YGjXsJFTI e BTG0NRDWHB0 e verificar que o crop 16:9 nunca ultrapassa a borda do painel (sem wrap/tile de textura) nem estaciona em divisórias horizontais.

## 29/10 18:51 [CERTEZA] Limpar balões/letreiros em inglês com delogo/inpainting e corrigir cálculo da barra de progresso e espaço no gancho (gemini-4-argon)
- prova: BTG0NRDWHB0 (história 3.5) exibiu tela com 'SOME ENTER URNS.'; C6YGjXsJFTI (legibilidade 4.5) colidiu legenda com balão 'TOES! FRESH POTATOES...'; gF-1j3NGxq8 (legibilidade 6.0) juntou 'MAISFORTE' no gancho e teve barra de progresso em 37% aos 5310s/5340s (sumindo em q21).
- onde: marca_site / limpador de balões (inpainting/delogo), gerador do título de gancho e overlay da barra de progresso
- como testar: Inspecionar q01-q24 de gF-1j3NGxq8 e C6YGjXsJFTI garantindo espaço entre palavras no gancho, barra de progresso contínua proporcional à duração total consolidada e ausência de texto em inglês sob a legenda.

## 29/10 20:54 [CERTEZA] Bloquear 'patrick_estrela' e lista de narradores ruins no sorteio de vozes do longo (gemini-4-argon)
- prova: O vídeo OLYsz-zu7Rs (renderizado em 29/10 às 18:30) incluiu 'patrick_estrela' em vozes_lista ('moana,patrick_estrela,pica_pau...'), descumprindo a regra da dona de 28/10 ('Narradores ruins: Patrick Estrela').
- onde: bin/anime_tts.py e teste_narradores.json (filtrar chave 'ruins' ao montar vozes_lista)
- como testar: Rodar o sorteio de vozes para 20 vídeos em dry-run e verificar por assert que nenhuma voz da lista 'ruins' de teste_narradores.json entra em vozes_lista.

## 29/10 20:54 [CERTEZA] Priorizar topo/rostos no crop vertical 16:9 para evitar decapitação de personagens (gemini-4-argon)
- prova: O júri apontou erro grave de decapitação na borda superior em YZNYmnqVZWI (garota na grade com olhos/testa cortados) e 4 vezes em OLYsz-zu7Rs (legibilidade 5.5 e movimento 4.0: cabeças cortadas na altura do nariz/queixo).
- onde: bin/fx_clips.py / bin/panel_fx_auto.py (cálculo de offset Y / pan vertical no crop 16:9)
- como testar: Renderizar trecho de 60s de OLYsz-zu7Rs e YZNYmnqVZWI ancorando o offset Y inicial no terço superior (ou detecção de face/olhos) e inspecionar os quadros extraídos.

## 29/10 20:54 [CERTEZA] Remover desfoque gaussiano pesado no fundo durante overlay da mascote e limitar quadros estáticos a 3.5s (gemini-4-argon)
- prova: Em OLYsz-zu7Rs (nota 4.5), o júri apontou borrão fixo total na arte do manhwa atrás da mascote; além disso, KJ5FcMf85Zo (q13-q14, q16-q17, q26-q27), YZNYmnqVZWI (610.3s-619.3s, 9.6% mov) e OLYsz-zu7Rs (q11-q12) tiveram painéis 100% estáticos por 4.5s a 9s.
- onde: bin/mascote_overlay.py (overlay_mascote_deitado) e bin/fx_clips.py (_movimento)
- como testar: Gerar preview do início de capítulo com mascote mantendo o painel do manhwa nítido com zoom lento contínuo, e garantir que cenas com mais de 3.5s recebam push-in ou subdivisão de corte.

## 30/10 04:09 [CERTEZA] Fixar camada de legendas acima do overlay de memes e limitar duração de memes a 1.8s (gemini-4-argon)
- prova: Em CCJQvNP-23Y (q05-q06, 33s-42s, 9s de duração e 15.6% de movimento) e 2jtdp4vB1WQ (q04-q05, 33s-37.5s, 4.5s de duração), o meme encobriu totalmente a legenda da narração, apresentou pillarbox assimétrico (Wojak cortado com tarja preta à esquerda) e derrubou o ritmo inicial.
- onde: bin/fx_clips.py / pipeline de composição de overlays e legendas (ASS/subtitles filter)
- como testar: Renderizar trecho de 0s a 45s de CCJQvNP-23Y e 2jtdp4vB1WQ e verificar nos quadros q04-q06 se a legenda permanece visível no topo da pilha de vídeo, com meme centralizado em pillarbox simétrico e duração máxima de 1.8s.

## 30/10 04:09 [CERTEZA] Forçar cortes rápidos (máx 2.0s por painel) e zoom punch-in nos primeiros 7s do gancho (gemini-4-argon)
- prova: O movimento medido no 1º trecho foi de apenas 7.0% em CCJQvNP-23Y (lâmpada estática por ~7s), 7.3% em 2jtdp4vB1WQ (mesmo painel de 2.0s a 6.5s) e 16.8% em LAeiXj2Qmlg (painel estático por >5s), derrubando a nota de movimento logo nos segundos críticos de retenção.
- onde: bin/fx_clips.py (_movimento / montagem do gancho e resumo inicial)
- como testar: Rodar o medidor de movimento no trecho 0 de 2jtdp4vB1WQ e CCJQvNP-23Y após limitar a duração máxima de cada imagem do gancho a 2.0s, confirmando que o movimento inicial sobe para acima de 22%.

## 30/10 04:09 [CERTEZA] Bloquear hflip em painéis com texto detectado e corrigir erro de digitação/posição da tarja de hook (gemini-4-argon)
- prova: Em LAeiXj2Qmlg, o espelhamento horizontal automático inverteu painéis expositivos e marcas ('È ORIEMIRP', 'AWHNAM E2IIM'). Em CCJQvNP-23Y e 2jtdp4vB1WQ, o texto superior cortou na borda/testa do personagem e saiu com typo ('ELE QUASE MORREU NO VENOENO').
- onde: bin/fx_clips.py (filtro hflip) e gerador de texto da tarja de abertura (hook)
- como testar: Inspecionar quadros q01-q03 de CCJQvNP-23Y e 2jtdp4vB1WQ para confirmar safe area superior de 8% sem cortar cabeças/texto, e verificar em LAeiXj2Qmlg que quadros com OCR/balão não recebem hflip.

## 30/10 05:50 — Fable (engenharia reversa de 14 recaps, referencias\PADROES_COMUNS.md) — PRÓXIMO TESTE A/B quando o cta_inicio_frase_7 fechar
- **CTA fora dos primeiros 15 min**: os de 450k–2,1M views não pedem like/inscrição nos primeiros 10–15 min; os de 3–13k pedem antes do min 5. Variante B = `cta.depois_da_frase` ≈ 180 (15 min) e a pausa da mascote junto. Medir % assistido e views 48 h (régua D1).
- Já aplicados direto (não A/B): título na tríade humilhação→virada→vingança/riqueza (seo_generator, só longo pt); fala do clone +10% (longo.json CORTES_FALA_DELTA=10; o topo fala 200–230 palavras/min, o Pastor ~144); mini-ganchos a cada 15 min; capítulo 'Comente PARTE 2'.
- Ainda NÃO feito: 30+ cortes no 1º minuto (o resumo de abertura tem ~1 corte por frase); in media res (o resumo já abre no ápice).

## 06/11 14:36 [CERTEZA] Gravar a variante A/B no desempenho de cada vídeo (sem isso o experimento não decide) (ag-opus-5-5)
- prova: O experimento cta_inicio_frase_7 tem 63 pedidos enviados desde 29/10, mas os 15+ vídeos do DESEMPENHO estão todos com variante null. Vários também estão sem nota_juri e sem render_s (qSM3, actvN, KwdN, PFbu, RRrh). Assim não há como somar views e % assistido de cada lado.
- onde: Onde o pedido recebe a variante (gravar em render.json/ficha), no recolhimento do pronto (fila_dona.py e alimentador, que já copiam capitulos.json e roteiro.txt) e no coletor que monta o DESEMPENHO
- como testar: No próximo longo postado, o DESEMPENHO tem que mostrar variante 'A' ou 'B' e render_s preenchido. Depois, conferir se a contagem por lado bate com 'enviados'.

## 06/11 14:36 [CERTEZA] Letreiro 'COMENTE: PARTE 2' não pode dividir a faixa da legenda (ag-opus-5-5)
- prova: Júri de legibilidade do P-dj (2 achados graves): a legenda 'favorita até' ficou fundida com 'PARTE 2', e 'continuam à espreita.' ficou em cima de 'COMENTE:' no encerramento. O letreiro também aparece no fim, e não só perto dos 22 min.
- onde: Código da tarja do capitulos.parte2 (anime_tarja_capitulo / montagem dos capítulos) e o MarginV da legenda ASS
- como testar: Renderizar 2 min ao redor do card e o fim. Extrair um quadro por segundo com ffmpeg e conferir que o letreiro fica no terço de cima (ou que a legenda sobe enquanto ele aparece) e que ele não aparece no encerramento.

## 06/11 14:36 [CERTEZA] Cobrir de branco o texto em inglês dentro dos balões (mesmo jeito do delogo que a dona aprovou) (ag-opus-5-5)
- prova: Apareceu nos 3 relatórios: no u7tN em q08, q11, q14, q23, q26, q29 e q30, com a legenda em cima do balão 'IT'S INDEED'. No SNhb são 6 achados ('HURRAY FOR HIS HIGHNESS!' colidindo com a legenda e pedaços de balão na abertura, q01 a q03). No P-dj, 'THE RESULT WAS 8 CONSECUTIVE LOSSES.'. A LICOES de 26/10 já diz que o júri sempre acha isso.
- onde: Reaproveitar a detecção do marca_site (já acha caixas de texto no tempo, foram 77 detecções no u7tN). Para caixa com letras latinas e fundo claro, preencher com drawbox branco; se o fundo não for branco, usar delogo. Fica no pré-processamento dos trechos, antes do fx_clips.
- como testar: Rodar nos primeiros 3 min do SNhb e do u7tN. O júri de legibilidade da mesma amostra deve ficar com 0 ou 1 achado de balão em inglês, e não pode aparecer mancha ou tarja (a dona acha feio).

## 06/11 14:36 [CERTEZA] Trava de movimento na abertura e no miolo: no máximo 3 s na mesma imagem (ag-opus-5-5)
- prova: Movimento medido no SNhb: trecho 1 com 6,0% (resumo de abertura, 'conhecer Roland / virou príncipe', parado mais de 4,5 s) e trecho 3 com 6,9% (9 s na mesma silhueta, de 943 a 952 s). Abertura do P-dj com 14,4%. P-dj e u7tN ficaram parados de q17 a q18 (mais de 4,5 s). O contador 'parados: 0' não pegou nenhum desses casos, então o limite dele está alto demais.
- onde: fx_clips._movimento e a montagem do resumo (resumo.*): forçar corte ou zoom contínuo quando a mesma imagem passar de 3 s. Também baixar o limite de 'parado' no medidor de movimento para menos de 10%.
- como testar: Refazer só o trecho 1 do SNhb. O movimento medido tem que passar de 20%, e o júri de movimento não pode apontar 'painel estático no gancho'.

## 06/11 14:36 [CERTEZA] Painel de cabeça para baixo no P-dj: descobrir se vem do glitch ou da fonte (ag-opus-5-5)
- prova: Júri de legibilidade do P-dj (grave): painel girado 180°, com o queixo para cima.
- onde: fx_clips (ANIME_FX_GLITCH e transições) ou o recorte da fonte
- como testar: Achar o tempo pelo quadro do júri e extrair o mesmo instante da fonte original. Se lá estiver normal, o problema está no efeito; corrigir e refazer 10 s ao redor.

## 06/11 14:36 [CERTEZA] Tirar da rotação do longo os canais que não são de manhwa (ag-opus-5-5)
- prova: Assist-IA Investimentos: 2 views, 17 s assistidos (0,3%), mesmo com júri 5,5 e 5,4 h de render (19275 s). Pedido da dona em 27/10: postar só nos canais pt mais ligados a manhwa (Manhwa Noturno, inovare manhwa br, ForjaReact, ManhwaReact, Animescomia, CartuchoReact, InventoReact). Curiosidades Noturnas, Fio da Meada, Dorama Noturno, CenaReact e HistoriasEmFrames estão fora dessa lista.
- onde: Lista de canais do postador e da fila do longo
- como testar: Nos próximos 7 dias, todo longo deve sair só em canal da lista da dona. Comparar views_h por canal no DESEMPENHO.

## 06/11 14:36 [GOSTO] Próximo A/B deve ser título e thumbnail, que é onde as views travam (ag-opus-5-5)
- prova: Quem entra assiste 27 a 30 min (6d2a, 5FDt e KwdN com 33 a 36%), mas são só 3 a 24 views em mais de 100 h no ar. O gargalo é clique e impressão, não retenção. Hoje não existe alavanca de título nem de thumbnail.
- onde: Gerador de título e thumbnail do longo: criar alavanca, por exemplo 'titulo.estilo' (pergunta/choque x descritivo) e 'thumb.estilo' (rosto grande + 3 palavras x cena)
- como testar: Abrir como experimento quando o cta_inicio_frase_7 fechar, com 6 ou mais vídeos por lado, e comparar views_h e views em 48 h.

## 10/11 21:08 [CERTEZA] Bloquear sobreposição de cards, stickers e legendas sobre rostos/olhos dos personagens (safe zone facial) (antigravity/gemini-3.8-flash-tiered)
- prova: Em g-JGmhvi9uc (legibilidade 5.0), 'RAPAZIADA' e 'ESTAMOS' cobriram nariz, boca e bochecha, 'MOLECADA?' cobriu queixo, card 'IMAGIN' cobriu olho, nariz e boca, e card 'RASTREANDO...' cobriu testa/cabelo; em HZRTnl9uykk (legibilidade 3.5), o sticker 'TEM O GOLPE' cobriu diretamente testa, têmpora e olho do protagonista.
- onde: bin/fx_clips.py / rotina de overlay de cards/stickers e posicionamento de legendas dinâmicas do gancho
- como testar: Renderizar amostras de 30s dos pontos com stickers em g-JGmhvi9uc e HZRTnl9uykk e verificar visualmente que nenhum elemento gráfico ou texto sobrepõe o terço central superior onde rostos e expressões estão localizados.

## 10/11 21:08 [CERTEZA] Garantir persistência da legenda karaokê durante cards gráficos e cenas em letterbox (antigravity/gemini-3.8-flash-tiered)
- prova: Em HZRTnl9uykk (legibilidade 3.5), a legenda de narração sumiu completamente durante a exibição do sticker 'TEM O GOLPE' e durante o painel estreito horizontal ('efeito selo postal' com 70% de espaço morto); em g-JGmhvi9uc, durante o card 'IMAGINA SÓ', a legenda do rodapé também não foi renderizada.
- onde: bin/anime_segments.py e pipeline de renderização ASS no ffmpeg (camada de legenda sobreposta sem ocultação por overlays)
- como testar: Inspecionar os quadros com stickers e painéis panorâmicos de HZRTnl9uykk e validar que a legenda karaokê .ass continua presente e sincronizada com a fala em 100% dos frames.

## 10/11 21:08 [CERTEZA] Eliminar calhas brancas da fonte e travar safe area superior para evitar cabeças cortadas (antigravity/gemini-3.8-flash-tiered)
- prova: Em HZRTnl9uykk (legibilidade 3.5 e história 3.0), ~30% da lateral esquerda ficou ocupada por calha vazia não recortada, empurrando a imagem e reduzindo o painel a uma fita central com 70% de desfoque, além de decepar o protagonista no topo; no SNhb31ZuuFA (movimento 5.5), o pan cortou olhos e testa na fala 'coragem de subir'.
- onde: bin/panel_fx_auto.py / pré-processamento de corte de páginas de manhwa e cálculo de offset vertical no crop 16:9
- como testar: Processar as páginas de HZRTnl9uykk pelo detector de gutters para garantir corte rente das bordas vazias e verificar que o enquadramento 16:9 mantém a cabeça dos personagens dentro dos 90% superiores da tela.

## 10/11 21:08 [CERTEZA] Consertar congelamento de meio-frame na transição wipe diagonal (glitch visual) (antigravity/gemini-3.8-flash-tiered)
- prova: Em HZRTnl9uykk (legibilidade 3.5, achado grave), ocorreu corte diagonal rígido atravessando a tela com uma linha branca diagonal estática decorrente de transição wipe travada no meio.
- onde: bin/fx_clips.py (filtros de transição xfade / wipe / ANIME_FX_GLITCH no ffmpeg)
- como testar: Extrair os quadros ao redor da transição com falha em HZRTnl9uykk e verificar se a interpolação completa o ciclo sem deixar linha divisória ou frame intermediário congelado.

## 10/11 21:08 [CERTEZA] Expurgar gírias e saudações vazias ('RAPAZIADA', 'OS GURI') da abertura dos roteiros (antigravity/gemini-3.8-flash-tiered)
- prova: Em HZRTnl9uykk (história 3.0), o júri apontou que a abertura com vícios e saudações ('RAPAZIADA', 'OS GURI', 'MAIS ENROLAÇÃO') quebra a retenção e a imersão dramática; em g-JGmhvi9uc, as mesmas expressões geraram stickers gigantes no meio do quadro.
- onde: bin/anime-pipeline.py (_resumo_longo) e bin/anime_tts.py (revezar / prompt de adaptação de falas)
- como testar: Gerar os primeiros 60s de locução para 5 roteiros de teste e assegurar via filtro textual que nenhuma saudação genérica de canal seja inserida, abrindo direto na premissa dramática.

## 10/11 23:35 [CERTEZA] Implementar safe area facial para legendas dinâmicas e cards de reação (agy/gemini-3.8-flash-high)
- prova: Em g-JGmhvi9uc (legibilidade 5.0), as palavras flutuantes 'RAPAZIADA', 'MOLECADA?', 'ESTAMOS' e o card 'IMAGIN' cobriram nariz, boca e olhos; em HZRTnl9uykk (legibilidade 3.5), o card 'TEM O GOLPE' sobrepôs testa e olho; em lynfA6VwYPc (legibilidade 6.0), 'OS GURI?' colidiu com a cabeça do protagonista.
- onde: bin/fx_clips.py / mascote_overlay.py / anime_gancho.py
- como testar: Renderizar amostras dos trechos de abertura com detecção facial ativada e validar que nenhum card flutuante ou palavra em destaque sobreponha o terço central onde se concentram os rostos.

## 10/11 23:35 [CERTEZA] Dinamização obrigatória da imagem de abertura no gancho inicial (agy/gemini-3.8-flash-high)
- prova: O trecho 0 registrou movimento estático de apenas 6.4% em g-JGmhvi9uc (2.0s a 6.5s congelado), 10.0% em HZRTnl9uykk (>4s parado) e 7.2% em lynfA6VwYPc (>4.5s parado com apenas texto mudando), prejudicando a retenção nos primeiros segundos.
- onde: bin/fx_clips.py (_movimento / render_gancho)
- como testar: Aplicar zoom contínuo progressivo (push-in de no mínimo 15%) ou cortes rápidos a cada 1.5s sempre que a medição do trecho 0 for inferior a 20%, garantindo movimento medido final ≥ 25%.

## 10/11 23:35 [CERTEZA] Remover assets externos e memes de franquias terceiras fora de contexto (agy/gemini-3.8-flash-high)
- prova: Em lynfA6VwYPc (história 4.0), houve inserção aleatória de close-up da personagem Klee (Genshin Impact / 3D) em cena tensa de escritório e colagem de PNG avulso de personagem feminina em biquíni no encerramento, quebrando a imersão dramática.
- onde: bin/arsenal_memes.py / fx_clips.py
- como testar: Filtrar a biblioteca de memes e b-rolls para expurgar assets de jogos 3D externos e limitar inserções gráficas estritamente a elementos neutros ou painéis do próprio manhwa em produção.

## 10/11 23:35 [CERTEZA] Bloquear saudações genéricas e vícios de linguagem na geração do gancho (agy/gemini-3.8-flash-high)
- prova: Em HZRTnl9uykk (história 3.0), a abertura desperdiçou os primeiros segundos com 'RAPAZIADA', 'OS GURI' e 'MAIS ENROLAÇÃO'; em g-JGmhvi9uc, as telas iniciais exibiram 'RAPAZIADA' e 'MOLECADA?', atrasando a introdução do conflito principal.
- onde: bin/anime_roteiro.py (prompt de geração de resumo/gancho de abertura)
- como testar: Inserir regra e lista de bloqueio (blacklist) no validador de roteiro para barrar saudações de YouTuber no gancho inicial, forçando abertura direta no conflito dramático ou perigo iminente.

## 11/11 06:33 [CERTEZA] Inpainting e Delogo Automático para Balões de Scan em Inglês (gemini/gemini-3.5-flash)
- prova: Legibilidade nota 4.0 em L4mXm0XIEks por balões 'NOW WE CAN ENJOY...' e 'ONE OF THEM WAS KRAFT...' mantidos na tela, e nota 5.5 em 992lhmyh64g pelo balão 'HOLY B...'.
- onde: bin/delogo_scan.py e pipeline de limpeza de imagens de scan
- como testar: Executar o detector de balões/OCR nas páginas de entrada e validar se a área é preenchida via inpaint/delogo sem rasurar os personagens.

## 11/11 06:33 [CERTEZA] Filtro de Assets Exclusivos da Obra e Stop-Words em Cards RPG (gemini/gemini-3.5-flash)
- prova: História nota 4.0 em lynfA6VwYPc por inserção da Klee (Genshin Impact) e PNG avulso de waifu em rooftop, e nota 5.12 em 992lhmyh64g por card RPG gerado para a palavra 'NISSO' e sticker 'MAIS ENROLAÇÃO'.
- onde: bin/memes_overlay.py e bin/gerar_cards.py
- como testar: Simular seleção de memes e cards em trecho com a conjunção 'NISSO' e confirmar que stop-words são ignoradas e assets de outros jogos/animes são bloqueados.

## 11/11 06:33 [CERTEZA] Zoom/Corte Dinâmico nos Primeiro 5s e Correção de Lacuna em Legendas (gemini/gemini-3.5-flash)
- prova: Abertura estática com 6.7% de movimento em L4mXm0XIEks e 7.2% em lynfA6VwYPc (q01-q03), além de ausência total de legendas em q10 a q12 em L4mXm0XIEks.
- onde: bin/fx_clips.py e bin/legenda_burn.py
- como testar: Renderizar os primeiros 10s e a transição q10-q12 do longo e validar se o movimento medido pelo ffmpeg supera 20% com legendas contínuas.

## 11/11 12:39 [CERTEZA] Trava anti-sobreposição de badges e cards sobre rostos detectados (gemini/gemini-3.5-flash)
- prova: Em 8m6TEKqvxfY o badge 'MOLECADA?' cobriu o rosto do personagem e 'DESEJADO' tampou os olhos; em 992lhmyh64g o card 'IMPORTANTE / NISSO' cobriu a face do orc.
- onde: bin/fx_clips.py (função de posicionamento de overlays)
- como testar: Renderizar quadros de teste com detecção facial e verificar se os bboxes de badges e cards são deslocados para áreas neutras (terço superior/inferior livre).

## 11/11 12:39 [CERTEZA] Detecção e inpaint automático de balões de scan em inglês (gemini/gemini-3.5-flash)
- prova: Balões com texto em inglês originais da scan visíveis intactos em L4mXm0XIEks (q13/q14) e 992lhmyh64g ('HOLY B...').
- onde: bin/delogo.py (pipeline de inpainting de scans)
- como testar: Executar o delogo/inpaint em amostras de páginas com balões em inglês e checar se o texto fonte foi totalmente removido antes da edição.

## 11/11 12:39 [CERTEZA] Filtro de stop-words em cards de status e remoção de memes verticais descontextualizados (gemini/gemini-3.5-flash)
- prova: Geração indevida de card de status para a conjunção 'NISSO' em 992lhmyh64g e meme de gato em vídeo vertical em 8m6TEKqvxfY (33s).
- onde: bin/anime_tts.py (geração de overlays e seleção de mídia)
- como testar: Passar roteiro com conjunções gramaticais e confirmar ausência de cards; validar restrição de inserção de memes verticais descontextualizados.

## 11/11 12:46 [CERTEZA] Forçar movimento de câmera (Ken Burns/punch-in) e troca de planos no gancho de abertura (0s a 6.5s) (gemini-4-argon)
- prova: Em L4mXm0XIEks (movimento trecho 1 = 6.7%) e 8m6TEKqvxfY (movimento trecho 1 = 5.4%), os quadros q01 a q03 mantêm exatamente a mesma imagem estática por 4,5s a 6,5s mudando apenas adesivos/karaokê, além de exibir um meme de gato estático aos 33s em 8m6TEKqvxfY.
- onde: bin/fx_clips.py (_movimento / montagem do gancho e resumo inicial)
- como testar: Renderizar os primeiros 30s de 8m6TEKqvxfY garantindo zoom/pan contínuo (escala 1.0x -> 1.18x) e corte de plano a cada 1.5s-2.0s no gancho; verificar se o movimento medido no trecho 1 sobe de <7% para >20%.

## 11/11 12:46 [CERTEZA] Filtrar stop-words nos stickers/cards, reposicionar fora de rostos e corrigir tempo de descarte (TTL) (gemini-4-argon)
- prova: Em 992lhmyh64g o card de RPG foi gerado para a conjunção 'NISSO' ('IMPORTANTE / NISSO') cobrindo o focinho do orc e 'ESCOLTANDO' cobriu o centro; em 8m6TEKqvxfY o texto 'MOLECADA?' e a tarja 'DESEJADO' cobriram olhos/rosto dos personagens e o sticker 'DO QUE ELA DESEJADO' ficou travado por 3 cenas seguidas (q10 a q12, 1796s-1805s).
- onde: bin/fx_clips.py (gerador de stickers/cards de destaque e posicionamento de overlays)
- como testar: Adicionar lista de stop-words/conjunções ao filtro de gatilhos de cards, forçar âncora no terço superior/lateral longe da caixa facial (face/upper-body crop) e limitar o tempo de vida (enable=between) estritamente ao fim da frase atual.

## 11/11 12:46 [CERTEZA] Limpeza/inpaint ou crop de balões de diálogo em inglês antes da composição 16:9 e correção de falha de legenda no trecho 4 (gemini-4-argon)
- prova: Em L4mXm0XIEks (legibilidade 4.0) e 992lhmyh64g (legibilidade 5.5), balões grandes em inglês ('NOW WE CAN ENJOY...', 'ONE OF THEM WAS KRAFT...', 'HOLY B...') ocupam metade da tela ou surgem cortados nas bordas competindo com a legenda, além de ausência de legenda em q10-q12 de L4mXm0XIEks e linha amarela vazando na borda inferior (q04-q23).
- onde: bin/fx_clips.py (enquadramento 16:9 / limpeza de scan) e bin/anime_tts.py (sincronia de legendas por bloco)
- como testar: Aplicar detector de caixa de texto/balão branco nas bordas do painel para dar zoom/crop excluindo balões periféricos (ou aplicar delogo/inpaint) e inspecionar os quadros q10-q14 de L4mXm0XIEks para confirmar legenda ativa e ausência da linha amarela inferior.

## 11/11 19:40 [CERTEZA] Filtro de stop-words e posicionamento fora de rostos em cards/overlays (gemini/gemini-3.5-flash)
- prova: 992lhmyh64g gerou card RPG para 'NISSO' cobrindo o rosto do orc; 8m6TEKqvxfY cobriu rostos centrais com 'MOLECADA?' e 'DESEJADO'.
- onde: bin/fx_clips.py (geração e posicionamento de overlays/cards)
- como testar: Processar frases com conjunções e verificar que não geram cards de status, e que overlays fiquem fora das bounding boxes dos rostos.

## 11/11 19:40 [CERTEZA] Correção no pipeline de legendas para evitar apagão em trechos inteiros (gemini/gemini-3.5-flash)
- prova: L4mXm0XIEks ficou sem nenhuma legenda renderizada durante todo o trecho 4 (q10, q11 e q12).
- onde: bin/anime_tts.py (geração/sincronização do arquivo .ass de legendas)
- como testar: Renderizar um vídeo completo e checar se todos os blocos de áudio possuem eventos correspondentes na timeline do arquivo .ass.

## 11/11 19:40 [CERTEZA] Movimento e zoom dinâmico forçado nos primeiros 6 segundos de gancho (gemini/gemini-3.5-flash)
- prova: Medição de movimento de apenas 6.7% em L4mXm0XIEks e 5.4% em 8m6TEKqvxfY nos quadros q01 a q03.
- onde: bin/fx_clips.py (_movimento no gancho inicial)
- como testar: Gerar a abertura de 10s e verificar com medição de movimento se a variação fica acima de 20% com cortes/zooms dinâmicos.

## 11/11 19:40 [CERTEZA] Inpaint e crop automático de balões em inglês das scans originais (gemini/gemini-3.5-flash)
- prova: Balões em inglês não tratados em 992lhmyh64g ('HOLY B...') e L4mXm0XIEks ('NOW WE CAN ENJOY...', 'ONE OF THEM WAS KRAFT...').
- onde: bin/delogo_scan.py (etapa de inpainting/limpeza de texto original)
- como testar: Passar páginas de manhwa com texto em inglês pelo pré-processador e checar se os balões são removidos antes da montagem 16:9.

## 12/11 02:39 [CERTEZA] Filtro para evitar sobreposição de legendas e stickers sobre rostos de personagens (gemini/gemini-3.5-flash)
- prova: Em 8m6TEKqvxfY, o texto 'MOLECADA?' e a tarja 'DESEJADO' cobriram rosto e olhos. Em 992lhmyh64g, o card 'NISSO' cobriu a face do orc e a legenda 'toda.' ficou sobre a crista do galo.
- onde: bin/legenda_draw.py (posicionamento de legendas) e bin/fx_clips.py (overlay de stickers/cards)
- como testar: Processar trechos com detecção facial e validar se a caixa delimitadora (bounding box) de legendas, stickers e cards é reposicionada automaticamente nos terços neutros da tela.

## 12/11 02:39 [CERTEZA] Inpainting e remoção automática de balões e textos originais de scans em inglês (gemini/gemini-3.5-flash)
- prova: Em L4mXm0XIEks (legibilidade 4.0), os balões em inglês 'NOW WE CAN ENJOY...' e 'ONE OF THEM WAS KRAFT...' ocuparam o centro do quadro sem tratamento.
- onde: bin/inpaint_baloes.py (ou bin/pre_processa_quadros.py)
- como testar: Rodar OCR e remoção em lote nas imagens de entrada antes do corte 16:9 e verificar se balões em inglês foram apagados sem artefatos.

## 12/11 02:39 [CERTEZA] Bloqueio de stickers autodepreciativos e memes de imagens reais descontextualizados (gemini/gemini-3.5-flash)
- prova: Sticker 'MAIS ENROLAÇÃO' no gancho do 992lhmyh64g reduziu a nota de história para 4.0 e o meme de gato real aos 33s em 8m6TEKqvxfY quebrou a imersão visual da obra.
- onde: bin/stickers_gen.py e bin/selecao_memes.py
- como testar: Inserir lista de bloqueio para termos pejorativos em stickers e restringir inserção de memes apenas a painéis e reações da própria estética manhwa.

## 12/11 02:39 [CERTEZA] Validação da linha do tempo para evitar lacunas de legendas durante narração ativa (gemini/gemini-3.5-flash)
- prova: Ausência total de legendas durante todo o trecho 4 (quadros q10, q11 e q12) em L4mXm0XIEks durante a fala narrada.
- onde: bin/legenda_draw.py e bin/anime_tts.py
- como testar: Executar verificação automatizada pós-alinhamento de áudio/legenda para acusar e preencher qualquer lacuna sem legenda superior a 1,5s enquanto houver fala.

## 12/11 06:39 [CERTEZA] Filtro de stop-words e reposicionamento automático de overlays fora dos rostos (gemini/gemini-3.5-flash)
- prova: Overlays cobrindo rostos: 'MOLECADA?' e 'DESEJADO' sobre a face em 8m6TEKqvxfY (nota 5.5), e card RPG 'IMPORTANTE / NISSO' para conjunção sobre o orc em 992lhmyh64g (nota 5.12).
- onde: bin/mascote_overlay.py / bin/fx_clips.py
- como testar: Gerar overlays sobre amostras com conectivos gramaticais ('NISSO') e verificar via detecção facial se o texto é movido para os terços superior/inferior sem cobrir rostos.

## 12/11 06:39 [CERTEZA] Cortes dinâmicos e zoom contínuo para dinamizar ganchos estáticos (q01-q03) (gemini/gemini-3.5-flash)
- prova: Ganchos de abertura travados por >4,5s com movimento medido de apenas 5,4% em 8m6TEKqvxfY e 6,7% em L4mXm0XIEks.
- onde: bin/fx_clips.py (_movimento)
- como testar: Renderizar os primeiros 10s de um vídeo e verificar se o movimento medido no gancho fica acima de 20% com alternância de planos a cada 1,5s.

## 12/11 06:39 [CERTEZA] Inpainting e limpeza automática de balões e textos em inglês de scans originais (gemini/gemini-3.5-flash)
- prova: Balões em inglês das scans visíveis sem tratamento: 'HOLY B...' em 992lhmyh64g, e 'NOW WE CAN ENJOY...' e 'ONE OF THEM WAS KRAFT...' em L4mXm0XIEks (nota 4.62).
- onde: bin/delogo.py / pipeline.py
- como testar: Processar páginas de manhwa com balões em inglês no script de delogo/inpaint e checar se o texto original é totalmente removido antes do crop 16:9.

## 12/11 06:39 [CERTEZA] Correção de dessincronia na timeline de renderização de legendas (gemini/gemini-3.5-flash)
- prova: Ausência total de legendas durante todo o trecho 4 (q10, q11 e q12) no vídeo L4mXm0XIEks.
- onde: bin/anime_tts.py
- como testar: Gerar as legendas de um roteiro completo e inspecionar a timeline para garantir que não existam intervalos com áudio mas sem legendas.

## 12/11 13:10 [CERTEZA] Filtrar stop-words em cards de status e evitar sobreposição em rostos (gemini/gemini-3.5-flash)
- prova: Card 'IMPORTANTE / NISSO' cobriu o rosto do orc em 992lhmyh64g; 'MOLECADA?' e 'DESEJADO' cobriram a face e olhos em 8m6TEKqvxfY (q01 e q10).
- onde: bin/legenda_anime.py (função gerar_card_status / posicionar_overlay)
- como testar: Renderizar amostra com a conjunção 'nisso' e confirmar que a frase não gera card e que stickers ficam fora da área facial.

## 12/11 13:10 [CERTEZA] Inpaint / Delogo automático de balões de texto em inglês da scan fonte (gemini/gemini-3.5-flash)
- prova: Balões de diálogo em inglês mantidos sem limpeza em 992lhmyh64g ('HOLY B...') e L4mXm0XIEks ('NOW WE CAN ENJOY...', 'ONE OF THEM WAS KRAFT...'), derrubando legibilidade para 4.0.
- onde: bin/limpar_baloes.py (função detectar_e_limpar_baloes)
- como testar: Processar as imagens fontes de L4mXm0XIEks no pipeline de inpaint e checar remoção completa dos balões na composição 16:9.

## 12/11 13:10 [CERTEZA] Cortes dinâmicos de imagem e zoom contínuo nos 6s do gancho inicial (gemini/gemini-3.5-flash)
- prova: Ganchos de L4mXm0XIEks e 8m6TEKqvxfY marcaram 6.7% e 5.4% de movimento com a mesma imagem inerte por 4.5s (q01-q03), prejudicando a retenção inicial (PFbuZNbc6cA com 0.1%).
- onde: bin/fx_clips.py (função aplicar_movimento_gancho)
- como testar: Renderizar os primeiros 10s de um longo e verificar trocas de painéis a cada 1.5s e movimento medido >20%.

## 12/11 23:20 [CERTEZA] Trava de posicionamento vertical de legendas e tarjas fora da zona facial (gemini/gemini-3.5-flash)
- prova: GMuCrqDRe9A (legibilidade 4.0: tarjas 'RAPAZIADA', 'MAIS ENROLAÇÃO' e legenda 'MUNDO' cobrindo olhos/boca) e 8m6TEKqvxfY (legibilidade 6.0: 'MOLECADA?' e 'DESEJADO' no rosto).
- onde: bin/render_legenda.py / bin/fx_clips.py
- como testar: Rodar renderização de teste em quadros com detecção facial e confirmar que a legenda/tarja é deslocada automaticamente para a margem inferior segura sem interceptar a bounding box do rosto.

## 12/11 23:20 [CERTEZA] Movimento de câmera dinâmico obrigatório nos primeiros 6s do gancho (gemini/gemini-3.5-flash)
- prova: 8m6TEKqvxfY (gancho 0s-6.5s estático em 5.4% de movimento), GMuCrqDRe9A (gancho 0s-4s estático em 4.2%) e baixíssimo tempo médio assistido em PFbuZNbc6cA (4s) e gF-1j3NGxq8 (17s).
- onde: bin/fx_clips.py (_movimento / render_gancho)
- como testar: Renderizar os 10s iniciais aplicando zoom punch + pan contínuo e validar no ffmpeg se a medição de movimento do trecho inicial fica acima de 25%.

## 12/11 23:20 [CERTEZA] Descarte automático de overlays na transição de cena e filtro de memes externos (gemini/gemini-3.5-flash)
- prova: 8m6TEKqvxfY (sticker 'DO QUE ELA DESEJADO' travado nas cenas q10-q12 por 9s e meme de gato real dando joinha aos 33s quebrando imersão).
- onde: bin/mascote_overlay.py / bin/fx_clips.py
- como testar: Confirmar que o TTL dos overlays expira exatamente na transição do painel e que imagens de memes de terceiros fora da obra são descartadas.

## 12/11 23:20 [CERTEZA] Limpeza automática (delogo/inpainting) de balões com texto em inglês da fonte (gemini/gemini-3.5-flash)
- prova: PReloN5HWSI (legibilidade 5.0: balão em inglês 'BLACK MONEY' colidindo diretamente com a legenda PT 'puxavam as cordinhas').
- onde: bin/delogo_scan.py
- como testar: Rodar detecção de OCR/texto em inglês nos painéis de entrada e verificar a aplicação de inpainting limpo no balão antes da sobreposição da legenda narrada.

## 13/11 18:54 [CERTEZA] Trava de margem de segurança Y para legendas e tarjas fora da área facial (gemini/gemini-3.5-flash)
- prova: Em GMuCrqDRe9A, a palavra 'MUNDO' cobriu olhos/testa e a tarja 'MAIS ENROLAÇÃO' desfigurou o nariz/olho do personagem.
- onde: bin/fx_clips.py
- como testar: Renderizar trecho de teste com legendas longas e verificar se a coordenada vertical permanece fixa na margem inferior da tela 16:9.

## 13/11 18:54 [CERTEZA] Ocultação/Inpainting automático de balões com texto original em inglês (gemini/gemini-3.5-flash)
- prova: Em PReloN5HWSI e oLBasz5Hp16, textos em inglês ('BLACK MONEY', 'YOU WANT ME') mantiveram-se visíveis sob a legenda em português.
- onde: bin/delogo_scan.py
- como testar: Processar painéis contendo balões de fala estrangeiros e confirmar se a rotina de delogo/máscara limpa o balão antes do render da legenda.
