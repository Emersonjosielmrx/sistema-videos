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
# Brief do melhorador central — Cortes (Shorts de parceiro) — 13/11 13:14

Vídeos nos últimos 7 dias: 742 | elegíveis (receberam o lote do feed): 283 | NÃO elegíveis: 12 | sem medida ainda: 447
% assistido mediano (só elegíveis): 49.7 | views 48 h mediana: 146 | QA com problema: 0 | saíram com parte faltando (IA caiu): 0

## Por canal
- Esporte Noturno: n 47, elegíveis 32, % assistido 70.0, views48 1362.0
- InventoReact: n 22, elegíveis 19, % assistido 53.5, views48 1185.5
- DicasFinanceirasDaIA: n 44, elegíveis 26, % assistido 65.9, views48 1022
- CenaReact: n 50, elegíveis 29, % assistido 48.0, views48 983
- inovaremanhwabr: n 47, elegíveis 23, % assistido 41.6, views48 952.5
- HistoriasEmFrames: n 41, elegíveis 21, % assistido 52.0, views48 510
- YouTube inovaremanhwaverseviet: n 7, elegíveis 3, % assistido 42.6, views48 205
- @CodigoInteligente-n7j: n 34, elegíveis 22, % assistido 49.2, views48 106
- Curiosidades Noturnas: n 33, elegíveis 12, % assistido 56.2, views48 77.5
- Filme Noturno: n 37, elegíveis 7, % assistido 63.0, views48 34
- Bicho Noturno: n 48, elegíveis 14, % assistido 44.7, views48 33.0
- CartuchoReact: n 37, elegíveis 11, % assistido 28.7, views48 7.5
- ManhwaReact-ia: n 16, elegíveis 13, % assistido 37.9, views48 7.0
- Animescomia: n 40, elegíveis 9, % assistido 63.1, views48 6.0
- ForjaReact: n 11, elegíveis 1, % assistido 46.7, views48 1
- AssistIA Investimentos: n 39, elegíveis 5, % assistido 57.2, views48 1.0
- Inovare: n 95, elegíveis 27, % assistido 0, views48 0.0
- Manhwa Noturno: n 11, elegíveis 9, % assistido 0, views48 0.0
- Dorama Noturno: n 28, elegíveis 0, % assistido None, views48 None
- Game Noturno: n 7, elegíveis 0, % assistido None, views48 None
- YouTube inovaremanhwaverseind: n 10, elegíveis 0, % assistido None, views48 0.0
- Inovaremanhwaversethai: n 7, elegíveis 0, % assistido None, views48 0.0
- Inovare Manhwa eng: n 3, elegíveis 0, % assistido None, views48 None
- Imóvel em Foco: n 6, elegíveis 0, % assistido None, views48 None
- Empresário Inteligente IA: n 7, elegíveis 0, % assistido None, views48 None
- Clínica Lucrativa IA: n 7, elegíveis 0, % assistido None, views48 None
- Vendas que Escalam: n 6, elegíveis 0, % assistido None, views48 None
- Lei e Lucro: n 2, elegíveis 0, % assistido None, views48 None

## Os que mais renderam (copiar a estrutura, não o texto)
- yB18hIQOGKw HistoriasEmFrames: views48 8075, % assistido 76.6, continuaram 73.6 — 
- OIWMMph1vqM DicasFinanceirasDaIA: views48 5662, % assistido 91.9, continuaram 75.6 — 
- UHR8LFR9hOI Esporte Noturno: views48 4100, % assistido 72.8, continuaram 60.5 — 

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

## SEM NAVEGADOR (HTTP) — saúde em 11-13T12:20: youtube 22/36, tiktok 44/58, instagram 46/53, flow 82/230, fotos 0/4 | MORTOS: youtube animescomia, youtube assistiainvestimentos, youtube bichonoturno, youtube cartuchoreact, youtube curiosidadesnoturnas, youtube dicasfinanceirasdaia, youtube filmenoturno, youtube forjareact, youtube gamenoturno, youtube historiasemframes, youtube inovare_thai, youtube inovaremanhwabr

## FILAS DE POSTAGEM BAIXAS/VAZIAS (produzir/encaminhar vídeo para elas antes de qualquer melhoria de formato)
MS Energy - Instagram @msenergycap (5), Tiktok @jornalcomia (0), Tiktok @3dfabricadeautomacoesia (1), Tiktok @inovaremanhwaverseita (0), Tiktok @canalalucinaai (0), Instagram @videocassetadascom.ia (2), Instagram @iapro.mentoria (0), YouTube rede Mundo Que Nao Existe (0), Tiktok @fabricadeautomacoesia (0), Tiktok @canalhistoriacomia (0), Tiktok @entrevistacomia (0), Tiktok @emersonjosiel2026 (0), Tiktok @emersonjosiel2030 (3), Tiktok @inovaremanhwaverse2 (0), Tiktok @curiosidadesnoturnas (3), Tiktok @emersonjosiel2032 (0), Tiktok @emersonjosiel2031 (0), Tiktok @inovaremanhwaversehindi (0), Tiktok @inovaremanhwaverserussian (0), Tiktok @inovaremanhwaversethai (0), Tiktok @inovaremanhwaverse (0), Tiktok @inovaremanhwaversefrench (0), Tiktok @inovaremanhwaverseesp (0), Tiktok @gameoftroneskingsroadbrasil (0), Instagram @futebolcom.ia2 (0), Instagram @sintetizerisada (0), Tiktok @filmescomia1 (0), Tiktok @aulasrevolution (0), Tiktok @e4487017 (0), Tiktok @emersonjosielmrx1995 (0)

## PEDIDOS E OPINIÕES DA DONA (valem mais que o júri; atender antes de qualquer outra coisa)
- 30/10 00:20 | hipercool, longo | Hipercool está DESATIVADO de propósito (como o Historias em Frames, trocado pelo Claude Code Video); volta à produção na semana que vem, depois que terminar a postagem dos capítulos já feitos. Usar um projeto para melhorar o outro: o hipercool é o mais moderno — os personagens FALAM (ela pediu falas também nos longos) e tem muitos efeitos bons; os que não acrescentam muito tempo de render podem ir para os longos | aberto
<!-- central:fim -->
