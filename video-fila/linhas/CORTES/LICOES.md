# Lições da linha CORTES (o que deu certo/errado — o melhorador lê antes de decidir)

- 26/10: "sem legenda = sem tarja" — a visão chutava faixa; só vale com texto LIDO e DIFERENTE em >= 2 de 6 quadros.
  Com 3 quadros perdia legenda que só aparece quando alguém fala (Galaxy Express 999). Prova sempre com folha de quadros
  e um controle negativo (vídeo sem legenda) antes de ligar.
- 26/10: a checagem "texto fixo" dos pixels derrubava legenda real parada 3-4 s em painel parado de manhwa.
- 26/10: a legenda no TOPO quase nunca é a legenda: o GTA pôs a tarja no título do topo e deixou a legenda real à mostra.
- 27/10: a faixa da visão vem folgada (15% da altura): medir a caixa das letras em resolução >= 720 px; em 360 px a
  legenda pequena de vídeo deitado vira ruído.
- 26/10: dorama/filme saíam com bordões do narrador-personagem (Chiquinha) e em 3ª pessoa: a instrução do narrador
  "vale por cima" das regras gerais — regra de nicho tem de entrar DENTRO do bloco do narrador também.
- 26/10: voz clonada lenta: ~60 vozes sem legenda medida herdavam -7% — piso de velocidade +5%.
- 26/10: a voz clonada na hora da POSTAGEM travou >10 min (Applio carregando no PC1 cheio): coisa pesada só na produção.
- 26/10: o PC2 usava yt-dlp por conta própria e bloqueou o IP da casa: máquina remota NUNCA usa yt-dlp.
- 26/10: a IA de título colava a palavra buscada no meio ("ELE DESCOBRIU ovos BICHOS"): conferir título antes de usar.
- 28/10: trocar o MODELO de texto (Argon, que "pensa") quebrou os pedidos curtos: gancho com max_tokens=40 voltava
  "[EMPTY RESPONSE]" ou o raciocínio em inglês ("LANGUAGE:", "WINDOW") e foi QUEIMADO no topo de 13 de 49 Shorts.
  Trocou modelo = conferir TODO pedido curto (max_tokens < 200) e a validação da resposta; 1 palavra latina = lixo.
- 28/10: o júri viu o defeito 9 vezes em 13 h e ninguém agiu (júri só anotava). Defeito de CERTEZA visto pelo júri
  (texto de erro na tela) = segurar o Short na hora (cortes_juri._trava_texto_erro), não esperar o lote.
- 28/10: o júri vê 1 em 4. Achou defeito de texto = folha do TOPO no 1,5 s de TODOS os Shorts do dia (barato, 1 imagem;
  D:\tmp\folha_topo.py) pra medir o tamanho real antes de decidir.
- 28/10: nota baixa do júri NÃO é prova: conferir no roteiro.txt antes de mexer. O júri via quadros soltos, juntava
  pedaços da legenda e punia o loop e a 1ª pessoa; o aprendiz virou isso regra contra a dona. Toda regra do APRENDIDO
  passa pelas DECISOES_DONO (cortes_juri) antes de virar mudança no pipeline.
- 27/10: dono não gostou da barra preta com a frase: só pra uso muito específico; prefere legenda com palavras de
  impacto maiores, de lado, fontes e cores por personagem.

<!-- central:inicio -->
# Brief do melhorador central — Cortes (Shorts de parceiro) — 19/11 15:54

Vídeos nos últimos 7 dias: 702 | elegíveis (receberam o lote do feed): 154 | NÃO elegíveis: 3 | sem medida ainda: 545
% assistido mediano (só elegíveis): 53.4 | views 48 h mediana: 657 | QA com problema: 1 | saíram com parte faltando (IA caiu): 0

## Por canal
- CenaReact: n 54, elegíveis 13, % assistido 58.5, views48 1374
- DicasFinanceirasDaIA: n 41, elegíveis 13, % assistido 46.2, views48 1278
- Esporte Noturno: n 40, elegíveis 21, % assistido 64.9, views48 1062.5
- Manhwa Noturno: n 7, elegíveis 7, % assistido 43.2, views48 1054.0
- AssistIA Investimentos: n 17, elegíveis 4, % assistido 50.9, views48 1047.0
- Inovare: n 68, elegíveis 4, % assistido 73.6, views48 995.5
- HistoriasEmFrames: n 43, elegíveis 15, % assistido 61.5, views48 829.0
- InventoReact: n 11, elegíveis 3, % assistido 60.4, views48 697.0
- inovaremanhwabr: n 39, elegíveis 6, % assistido 62.3, views48 648.5
- Imóvel em Foco: n 36, elegíveis 6, % assistido 37.6, views48 534
- @CodigoInteligente-n7j: n 21, elegíveis 7, % assistido 51.2, views48 469
- Filme Noturno: n 31, elegíveis 8, % assistido 36.5, views48 201.5
- Clínica Lucrativa IA: n 31, elegíveis 7, % assistido 55.9, views48 127
- Lei e Lucro: n 25, elegíveis 8, % assistido 42.4, views48 94
- Anime Noturno: n 18, elegíveis 3, % assistido 47.8, views48 80
- Vendas que Escalam: n 25, elegíveis 6, % assistido 33.0, views48 30
- ManhwaReact-ia: n 15, elegíveis 6, % assistido 42.4, views48 11.5
- CartuchoReact: n 25, elegíveis 5, % assistido 0, views48 6
- Empresário Inteligente IA: n 22, elegíveis 4, % assistido 33.5, views48 3.0
- Bilionário Noturno: n 17, elegíveis 2, % assistido 22.1, views48 1.0
- YouTube inovaremanhwaverseviet: n 1, elegíveis 0, % assistido None, views48 None
- Animescomia: n 25, elegíveis 6, % assistido 21.2, views48 None
- Dorama Noturno: n 20, elegíveis 0, % assistido None, views48 None
- ForjaReact: n 13, elegíveis 0, % assistido None, views48 0.0
- Bicho Noturno: n 23, elegíveis 0, % assistido None, views48 None
- Curiosidades Noturnas: n 29, elegíveis 0, % assistido None, views48 None
- Game Noturno: n 5, elegíveis 0, % assistido None, views48 None

## Os que mais renderam (copiar a estrutura, não o texto)
- WYgbuhD5K8E HistoriasEmFrames: views48 20792, % assistido 105.76, continuaram 75.75 — 
- 8oCAjppKOlg HistoriasEmFrames: views48 8227, % assistido 97.98, continuaram 55.36 — 
- hAfj7LGBetA CenaReact: views48 7975, % assistido 58.55, continuaram 75.58 — 

## QA (defeito objetivo, sem IA)
- 8rIMC2GRC3g: ffprobe não leu a duração

## O QUE DECIDE VIEWS (dado medido em 29/10 — FABLE_DECISOES.md D1; vale mais que gosto e que nota de júri)
- 60% dos Shorts NÃO entram no lote de teste do feed ("continuaram" 100% com < 10 views = o YouTube mostrou a 2–5
  pessoas e parou). Gancho/efeito/mascote não mudam isso: esses vídeos não são vistos. Não aprenda regra com eles.
- Quem entra no lote para em 1.000–1.500 views. O que leva ao 2º lote é ASSISTIR INTEIRO (% assistido ≥ 65%):
  os 5 que passaram de 2.000 têm 13–24 s e 64–89% assistido; os do platô, 50–75 s e 44%. "Continuaram" (deslizou)
  é igual nos dois grupos — não é a alavanca.
- Logo: priorize duração curta (15–25 s), final que emenda no início (loop), 1 acontecimento por vídeo. Qualquer
  mudança que ALONGUE o vídeo começa com peso negativo.
- Para comparar A/B: só vídeos elegíveis (views_periodo ≥ 20); métrica primária pct_media, depois log(views/mediana
  do canal). Nunca promover por nota de júri sozinha.

## SEM NAVEGADOR (HTTP) — saúde em 11-19T15:24: youtube 33/41, tiktok 41/58, instagram 46/53, flow 9/234, fotos 0/4 | MORTOS: youtube assistiainvestimentos, youtube fiodameada, youtube manhwareact, youtube clinicalucrativaia, youtube animenoturno, youtube dentrodascoisas3d, youtube fatochocante, youtube pordentro, tiktok inovaremanhwaverseita, tiktok inovaremanhwaverseviet, tiktok jogoscomia, tiktok vendeafiliados3

## FILAS DE POSTAGEM BAIXAS/VAZIAS (produzir/encaminhar vídeo para elas antes de qualquer melhoria de formato)
Tiktok @jornalcomia (0), Tiktok @3dfabricadeautomacoesia (1), Tiktok @inovaremanhwaverseita (0), Tiktok @canalalucinaai (0), Instagram @videocassetadascom.ia (2), Instagram @iapro.mentoria (0), Tiktok @canalhistoriacomia (0), Tiktok @entrevistacomia (0), Tiktok @emersonjosiel2026 (0), Tiktok @inovaremanhwaverse2 (6), Tiktok @inovaremanhwaversehindi (0), Tiktok @inovaremanhwaverserussian (0), Tiktok @inovaremanhwaversethai (0), Tiktok @inovaremanhwaverse (0), Tiktok @inovaremanhwaversefrench (0), Tiktok @inovaremanhwaverseesp (0), Tiktok @gameoftroneskingsroadbrasil (0), Instagram @futebolcom.ia2 (0), Tiktok @filmescomia1 (0), Tiktok @aulasrevolution (0), Tiktok @e4487017 (0), Tiktok @emersonjosielmrx1995 (0), Tiktok @en1653964 (0), Tiktok @murilodoctor192 (0), Tiktok @emersongencshin (0), Tiktok @solarmundo195 (0), Tiktok @empressinovare (0), Tiktok @filmescomia00 (0), Tiktok @inovaremultiatendimento (0), Tiktok @emersonjosiel1995 (0)

## PEDIDOS E OPINIÕES DA DONA (valem mais que o júri; atender antes de qualquer outra coisa)
- 30/10 00:20 | hipercool, longo | Hipercool está DESATIVADO de propósito (como o Historias em Frames, trocado pelo Claude Code Video); volta à produção na semana que vem, depois que terminar a postagem dos capítulos já feitos. Usar um projeto para melhorar o outro: o hipercool é o mais moderno — os personagens FALAM (ela pediu falas também nos longos) e tem muitos efeitos bons; os que não acrescentam muito tempo de render podem ir para os longos | aberto
<!-- central:fim -->
