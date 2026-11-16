
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

## 14/11 05:30 [CERTEZA] Impedir sobreposição de stickers e legendas sobre o rosto de personagens (gemini/gemini-3.5-flash)
- prova: Júri de legibilidade indicou que stickers como 'E DEIXA' e 'MAS QUERIAM' (AP_c0bbMmRI), 'PASSANDO' (8fM6Ay7OJho) e 'OS GURI?' (KQMPGyt6PxA) cobriram olhos e rostos em close-ups dramáticos.
- onde: bin/fx_clips.py (função de cálculo de posição de stickers e legendas)
- como testar: Renderizar amostragem de 5 minutos dos vídeos com erro e rodar o júri de legibilidade para confirmar que nenhum elemento gráfico colide com a face.

## 14/11 05:30 [CERTEZA] Corrigir enquadramento focal vertical para evitar decapitação e emendas de fundo (gemini/gemini-3.5-flash)
- prova: Relatórios de movimento e legibilidade apontam cortes severos no topo da cabeça (8fM6Ay7OJho e KQMPGyt6PxA) e emenda vertical dura dividindo o céu azul ao meio no pan (8fM6Ay7OJho q30 e KQMPGyt6PxA).
- onde: bin/fx_clips.py (ancoragem de crop 16:9 e geração de pans)
- como testar: Gerar trechos de pan nos segmentos afetados e verificar visualmente se a cabeça do personagem é preservada no terço superior sem divisões de textura no cenário.

## 14/11 08:18 [CERTEZA] Trava anti-colisão de stickers e textos sobre rostos de personagens (gemini/gemini-3.5-flash)
- prova: Nos vídeos LUQDew946Ps (legibilidade 3.5) e KQMPGyt6PxA (legibilidade 4.5), stickers como 'BOTANDO', 'o MALUCO' e 'OS GURI?' foram estampados diretamente sobre olhos e rostos dos personagens.
- onde: bin/mascote_overlay.py e bin/fx_clips.py na função de posicionamento de overlays/stickers
- como testar: Gerar render de amostragem com detecção facial ativa e verificar se o bounding box do sticker é deslocado para o terço inferior quando detecta área focal de rosto.

## 14/11 08:18 [CERTEZA] Limpeza automatizada de legendas originais espelhadas na fonte (gemini/gemini-3.5-flash)
- prova: No vídeo LUQDew946Ps (legibilidade 3.5, q06), a legenda oficial em português colidiu visualmente com o texto espelhado da fonte original em inglês ('tuov tlust e'mraG ton e'tI').
- onde: bin/delogo.py ou bin/anime_legendas.py antes da etapa de queimado da legenda final
- como testar: Processar trechos que contenham texto queimado no material bruto e confirmar a aplicação do delogo/máscara antes da sobreposição da legenda em português.

## 14/11 13:47 [CERTEZA] Trava de posicionamento de stickers e balões fora da área facial (gemini/gemini-3.5-flash)
- prova: Em LUQDew946Ps (legibilidade 3.5), a tarja 'BOTANDO' cobriu o rosto da personagem; em KQMPGyt6PxA (legibilidade 4.5), stickers 'OS GURI?' e 'UMA ALMA' ficaram sobre os olhos do protagonista e a face do idoso.
- onde: bin/mascote_overlay.py / bin/fx_clips.py
- como testar: Gerar clipe com stickers de gancho ativados e verificar se as caixas de texto permanecem restritas ao terço inferior ou áreas negativas sem sobreposição com rostos detectados.

## 14/11 13:47 [CERTEZA] Ajuste na âncora do crop vertical para evitar decapitação em zooms e pans (gemini/gemini-3.5-flash)
- prova: Em KQMPGyt6PxA (movimento 6.0), a câmera aplicou zoom/pan cortando o topo da cabeça do personagem e enquadrando peito e manga durante a fala 'chega esbaforido'.
- onde: bin/fx_clips.py
- como testar: Executar a função de renderização de movimento vertical em quadros com personagens e confirmar visualmente que os olhos e o topo da cabeça permanecem visíveis no terço superior.

## 14/11 18:30 [CERTEZA] Corrigir distorção de malha 2.5D e eliminar fenda de costura (seam tear) vertical (gemini/gemini-3.5-flash)
- prova: S6LISaC7K6A apresentou rosto com 3 olhos e feições duplicadas em q01 (nota 4.12); KAA_csRv7NU apresentou rosto partido verticalmente com duplicação de olho/sobrancelha em cena central.
- onde: bin/fx_clips.py:aplicar_efeito_25d / animar_crop_vertical
- como testar: Executar render de amostragem em quadros de close-up facial com parallax 2.5D habilitado e validar visualmente ausência de duplicação de feições ou desalinhamento de emenda vertical.

## 14/11 18:30 [CERTEZA] Reforçar inpainting/limpeza automática de balões de fala e marcas em inglês (gemini/gemini-3.5-flash)
- prova: KAA_csRv7NU q02, q03 e q07-q09 exibiram balões em inglês visíveis ('EN-THUNDERSCANS.COM' e 'SUCH A GROWN MAN...'), derrubando retenção para 4.0 e história para 5.0.
- onde: bin/limpa_baloes.py:remover_texto_ingles
- como testar: Rodar rotina de detecção de OCR e inpaint em lote de quadros com balões em inglês e verificar se 100% das caixas de texto estrangeiro foram limpas.

## 14/11 18:30 [CERTEZA] Ajustar colisão e margem de segurança de legendas/stickers sobre a boca de personagens (gemini/gemini-3.5-flash)
- prova: S6LISaC7K6A teve a legenda 'você ficar' e o sticker 'DESFALQUE' posicionados diretamente sobre a boca e queixo dos personagens nos close-ups de reação.
- onde: bin/mascote_overlay.py e bin/fx_clips.py:posicionar_elementos_texto
- como testar: Gerar render de teste em sequências com stickers/legendas em close-ups faciais e verificar se a região da boca e olhos permanece 100% desobstruída.

## 14/11 22:46 [CERTEZA] Limitar duração de stickers a 2s e bloquear sobreposição em rostos/bocas (gemini-4-argon)
- prova: Em S6LISaC7K6A ('DESFALQUE' sobre a boca em choro; 'QUE DIABOS' congelado por >9s de q07 a q09), KAA_csRv7NU ('SE INSCREVE!' fixo por >4s cobrindo rosto em q16) e t-mnhLoSb18 ('ESTÃO?' nos olhos e 'A FORTALEZA' na boca), stickers estáticos obstruíram expressões faciais e poluíram o gancho.
- onde: bin/fx_clips.py e bin/mascote_overlay.py
- como testar: Renderizar trecho de 60s com stickers/CTAs e verificar no júri se nenhum overlay ultrapassa 2.0s, se é encerrado no corte de cena e se respeita a bounding box facial.

## 14/11 22:46 [CERTEZA] Corrigir wrap/costura vertical no pan/crop, artefato de wipe diagonal e deformação 2.5D em rostos (gemini-4-argon)
- prova: Em S6LISaC7K6A o efeito 2.5D gerou três olhos e corte triangular no braço; em KAA_csRv7NU houve seam tear vertical partindo o rosto; em t-mnhLoSb18 o pan vertical sem clamp duplicou o topo da cabeça e uma linha diagonal de wipe ficou travada sobre o salão.
- onde: bin/fx_clips.py (funções de _movimento, pan/crop 16:9, wipe e parallax 2.5D)
- como testar: Aplicar clamp nas bordas do pan/zoom para impedir repetição de pixels (wrap), desativar distorção de malha 2.5D sobre faces detectadas e validar keyframes de transição wipe em trechos de teste.

## 14/11 22:46 [CERTEZA] Detectar marca d'água antes de espelhar quadro e cobrir balões em inglês na base (gemini-4-argon)
- prova: Em t-mnhLoSb18 a marca 'AniPrestige' passou batida porque o quadro foi espelhado horizontalmente ('pit2e19inA'); em KAA_csRv7NU o selo roxo 'EN-THUNDERSCANS.COM' e balões em inglês (q02, q03, q07–q09) ficaram totalmente expostos.
- onde: bin/marca_site.py e pipeline de limpeza/crop de painéis
- como testar: Executar OCR/detecção de marca d'água também na versão espelhada do frame antes de aplicar hflip + delogo, e aplicar inpaint/crop nos balões de diálogo em inglês na base dos quadros.

## 14/11 23:26 [CERTEZA] Clamp de bordas no pan vertical para evitar duplicação e wrap de quadros (gemini/gemini-3.5-flash)
- prova: t-mnhLoSb18 (legibilidade 4.0 / movimento 5.0): pan vertical sem clamp causou wrap horizontal e duplicou o topo da cabeça do personagem no limite da tela.
- onde: bin/fx_clips.py
- como testar: Executar animação de pan vertical no limite do enquadramento e confirmar que as bordas aplicam clamp sem duplicação de quadros.

## 14/11 23:26 [CERTEZA] Offset de margem de segurança para legendas e stickers longe do rosto (gemini/gemini-3.5-flash)
- prova: S6LISaC7K6A (legibilidade 5.0) com sticker 'DESFALQUE' e legendas sobre a boca; t-mnhLoSb18 (legibilidade 4.0) com sticker 'ESTÃO?' cobrindo os olhos do personagem.
- onde: bin/legenda.py e bin/mascote_overlay.py
- como testar: Renderizar cenas de close-up facial e verificar se legendas/stickers são reposicionados automaticamente na margem neutra.

## 14/11 23:26 [CERTEZA] Limpeza automática (inpaint/delogo) de balões em inglês e marcas de scan (gemini/gemini-3.5-flash)
- prova: KAA_csRv7NU (historia 5.0): balões com texto em inglês 'SUCH A GROWN MAN...' e marca 'EN-THUNDERSCANS.COM' visíveis no render.
- onde: bin/limpa_balao.py e bin/delogo.py
- como testar: Processar imagem com balões em inglês e verificar se o OCR/inpaint remove o texto mantendo a textura original do painel.

## 14/11 23:26 [CERTEZA] Fallback do efeito 2.5D/parallax para pan/zoom 2D em segmentações complexas (gemini/gemini-3.5-flash)
- prova: S6LISaC7K6A (legibilidade 5.0): deformação no efeito 2.5D gerou rosto com três olhos e feições duplicadas.
- onde: bin/fx_clips.py
- como testar: Simular mapa de profundidade de baixa confiança e verificar se o sistema comuta para zoom 2D suave em vez de aplicar distorção de malha.

## 15/11 02:17 [CERTEZA] Limpeza automática de balões de texto em inglês e marcas de scan (gemini/gemini-3.5-flash)
- prova: KAA_csRv7NU (história 5.0) exibe balões em inglês ('SUCH A GROWN MAN...', 'IS THE SUPREME RULER...') nos quadros q02, q03, q07, q08, q09 e marca d'água EN-THUNDERSCANS.COM.
- onde: bin/scan_cleaner.py
- como testar: Executar a rotina de limpeza/inpaint na imagem fonte de KAA_csRv7NU e conferir a remoção total do texto em inglês e das marcas de scan.

## 15/11 02:17 [CERTEZA] Margem de segurança para legendas e stickers desviarem do rosto dos personagens (gemini/gemini-3.5-flash)
- prova: S6LISaC7K6A (legibilidade 5.0) teve o sticker 'DESFALQUE' e legenda 'você ficar' sobre a boca do personagem; t-mnhLoSb18 (legibilidade 4.0) teve o sticker 'ESTÃO?' sobre os olhos.
- onde: bin/legenda.py e bin/mascote_overlay.py
- como testar: Processar os takes com sobreposição ajustando a posição Y dos elementos para manter a expressão facial desobstruída.

## 15/11 02:17 [CERTEZA] Clamp nas bordas do movimento de câmera e travamento do efeito 2.5D instável (gemini/gemini-3.5-flash)
- prova: t-mnhLoSb18 (movimento 5.0) apresentou topo da cabeça duplicado/cortado em pan vertical; S6LISaC7K6A (legibilidade 5.0) sofreu deformação severa de malha no rosto em 2.5D.
- onde: bin/fx_clips.py (_movimento)
- como testar: Renderizar clipe com pan vertical checando se o clamp impede duplicação visual e fallback para pan/zoom 2D suave em recortes faciais complexos.

## 15/11 04:54 [CERTEZA] Impedir sobreposição de stickers e textos decorativos sobre rostos (gemini/gemini-3.5-flash)
- prova: SjQHP-0GKJs (legibilidade 5.0: 'MOLECADA?' e 'TRAÍRA' cobrindo boca e queixo) e t-mnhLoSb18 (legibilidade 4.0: 'ESTÃO?' sobre os olhos do protagonista)
- onde: bin/mascote_overlay.py e bin/fx_clips.py
- como testar: Renderizar trechos de teste com stickers de apoio e confirmar que a caixa delimitadora dos rostos é duramente respeitada como área proibida

## 15/11 04:54 [CERTEZA] Corrigir wrap horizontal/seam tear em pans e zooms verticais (gemini/gemini-3.5-flash)
- prova: t-mnhLoSb18 (legibilidade 4.0 e movimento 5.0: rasgo horizontal no terço superior e duplicação da cabeça) e KAA_csRv7NU (historia 5.0: rosto partido verticalmente por seam tear)
- onde: bin/fx_clips.py (_movimento / clamp de bordas)
- como testar: Executar fx_clips.py em imagem vertical com movimento de pan e checar ausência de repetição de pixels ou emendas visíveis nas margens superiores

## 15/11 04:54 [CERTEZA] Forçar limpeza/inpaint de balões de texto em inglês e marcas de scanlation (gemini/gemini-3.5-flash)
- prova: KAA_csRv7NU (historia 5.0: marca 'EN-THUNDERSCANS.COM' e balões não limpos 'SUCH A GROWN MAN...' e 'IS THE SUPREME RULER...')
- onde: bin/limpar_baloes.py
- como testar: Submeter os quadros brutos de KAA_csRv7NU ao pipeline de limpeza e verificar eliminação total dos balões em inglês antes do ajuste de legenda

## 15/11 22:53 [CERTEZA] Garantir painel de fundo até o último segundo e eliminar tela preta/congelamento no encerramento (gemini-4-argon)
- prova: Em SO-icNCOO3E (legibilidade 4.0, movimento 5.0), q25.jpg (5855.25s) a q27.jpg ficam com 70% a 100% da tela em preto sólido vazio atrás da legenda e do avatar, derrubando o movimento do trecho 9 para 6.6%; em NatfJn-eQp0 o trecho final caiu para 9.2% com a mascote congelada; em 0w1FjXmgX0w o encerramento cortou a fala na legenda 'de casa!'.
- onde: bin/anime_tts.py e bin/mascote_overlay.py (overlay_mascote_deitado / montagem da trilha visual de fechamento e CTA final)
- como testar: Renderizar os últimos 20s de SO-icNCOO3E e 0w1FjXmgX0w garantindo que o último painel do manhwa (com pan/zoom ativo) se estenda até o fim do áudio do CTA + 0.5s de padding, verificar com ffprobe se a duração de vídeo cobre 100% do áudio e checar se o movimento do último trecho fica acima de 18% sem frames pretos.

## 15/11 22:53 [CERTEZA] Bloquear sobreposição de pop-ups de texto, stickers e HUDs sobre rostos no centro do frame (gemini-4-argon)
- prova: Em NatfJn-eQp0 (legibilidade 5.0), os pop-ups 'GAROTO', 'O FEITICEIRO' e 'MAIS ENROLAÇÃO' cobriram os olhos de Yuji, a face de Geto e a boca de Sukuna; em 0w1FjXmgX0w (legibilidade 4.0), 'OS GURI?' e 'QUE CORTADO' cobriram o rosto e a cabeça dos personagens; em SO-icNCOO3E (legibilidade 4.0), o HUD 'RASTREANDO...' tampou a cabeça do personagem e metade do balão.
- onde: bin/fx_clips.py (posicionamento de stickers/pop-ups de impacto e HUDs sobre o vídeo 16:9)
- como testar: Restringir o ancoramento de pop-ups e HUDs às margens laterais (zonas de blur 16:9) ou ao terço inferior fora da caixa central de rosto, gerar os primeiros 60s de NatfJn-eQp0 e 0w1FjXmgX0w e inspecionar q01-q10 confirmando zero obstrução facial.

## 15/11 22:53 [CERTEZA] Forçar troca de quadros ou recorte multi-foco a cada 1.5s-2s no gancho de abertura (0s a 6.5s) (gemini-4-argon)
- prova: Mesmo após o ajuste de câmera em 12/11, q01, q02 e q03 (0s a 6.5s) seguem presos no mesmo quadro estático nos 3 vídeos: Sukuna parado em NatfJn-eQp0 (movimento 18.3%, retenção 4.0), mesma imagem de 'RAPAZIADA!' a 'UMA QUE EU TÔ' em 0w1FjXmgX0w (movimento 19.9%) e página inteira sem corte em SO-icNCOO3E.
- onde: bin/fx_clips.py (_movimento / montagem dos primeiros 6.5s do gancho)
- como testar: Subdividir páginas ou alternar entre 3 recortes/quadros distintos nos primeiros 6.5s (1 corte a cada frase curta ou 2s) com zoom-in forte, renderizar o início de 0w1FjXmgX0w e confirmar que q01, q02 e q03 exibem enquadramentos diferentes e movimento > 28%.

## 15/11 23:21 [CERTEZA] Safe area e evasão facial obrigatória para overlays de texto e adesivos flutuantes (antigravity/gemini-3.8-flash-tiered)
- prova: Em NatfJn-eQp0 o pop-up 'GAROTO' cobriu o olho de Yuji, 'O FEITICEIRO' cobriu o rosto de Geto e 'MAIS ENROLAÇÃO' cobriu a boca de Sukuna; em 0w1FjXmgX0w o selo 'OS GURI?' tampou olhos/nariz/boca e 'QUE CORTADO' cobriu a cabeça; em SO-icNCOO3E o HUD cobriu o rosto do personagem e balões de diálogo.
- onde: bin/mascote_overlay.py / bin/fx_clips.py (rotina de posicionamento de pop-ups, adesivos e tags gráficas)
- como testar: Renderizar trechos de 5s nos momentos com pop-ups em NatfJn-eQp0 e 0w1FjXmgX0w com detecção facial ativa e verificar se todos os elementos foram deslocados para áreas neutras, mantendo o rosto dos personagens 100% desobstruído.

## 15/11 23:21 [CERTEZA] Forçar alternância de painéis ou zoom punch-in real na imagem durante os 6s do gancho (antigravity/gemini-3.8-flash-tiered)
- prova: NatfJn-eQp0 travou no mesmo quadro do Sukuna de 0s a 4.5s (q01-q03) com movimento medido de apenas 18.3% e retenção 4.0; em 0w1FjXmgX0w a mesma imagem estática perdurou por três falas (2.0s a 6.5s, 19.9% de movimento), comprovando que apenas alternar stickers de texto não produz dinamismo visual real na abertura.
- onde: bin/fx_clips.py (_movimento e montagem do gancho inicial nos primeiros 7s)
- como testar: Renderizar os primeiros 7 segundos de NatfJn-eQp0 e 0w1FjXmgX0w forçando divisão de cortes (máx 2.0s por imagem) ou push-in contínuo na camada de imagem do manhwa, validando se o movimento medido do trecho 0 supera 25%.

## 15/11 23:21 [CERTEZA] Eliminar tela preta no encerramento e garantir animação/fundo contínuo com fade suave (antigravity/gemini-3.8-flash-tiered)
- prova: SO-icNCOO3E finalizou em tela preta total nos quadros q25 a q27 com movimento de 6.6%; NatfJn-eQp0 congelou a mascote e o fundo estáticos no trecho final com 9.2% de movimento; 0w1FjXmgX0w cortou o áudio abruptamente na frase incompleta ('de' casa!').
- onde: bin/anime_tts.py / bin/mascote_overlay.py / pipeline de montagem e finalização de áudio/vídeo
- como testar: Renderizar os últimos 20s de SO-icNCOO3E e NatfJn-eQp0 conferindo a presença de background ativo (partículas/pan suave) sem tela preta e verificando se o áudio e a legenda completam a frase com fade out adequado.

## 15/11 23:21 [CERTEZA] Bloquear inserção de clipes live-action em recaps de mangá/manhwa (antigravity/gemini-3.8-flash-tiered)
- prova: Em SO-icNCOO3E a nota de história caiu para 4.0 devido à quebra de imersão provocada pela inclusão de um vídeo live-action de escritório em baixa resolução para ilustrar 'O Salto Final Para A Queda' em meio a uma história escolar em preto e branco.
- onde: bin/arsenal_memes.py / bin/fx_clips.py (filtro de estilo visual para seleção de mídias de apoio e memes)
- como testar: Executar o seletor de memes em lote para histórias de mangá/manhwa e verificar por asserção que nenhum vídeo live-action com atores reais seja selecionado, priorizando painéis da própria obra ou animações estilizadas.
