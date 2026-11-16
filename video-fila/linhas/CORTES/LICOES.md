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
# Brief do melhorador central — Cortes (Shorts de parceiro) — 16/11 11:54

Vídeos nos últimos 7 dias: 805 | elegíveis (receberam o lote do feed): 330 | NÃO elegíveis: 14 | sem medida ainda: 461
% assistido mediano (só elegíveis): 49.5 | views 48 h mediana: 726.5 | QA com problema: 0 | saíram com parte faltando (IA caiu): 0

## Por canal
- DicasFinanceirasDaIA: n 51, elegíveis 27, % assistido 56.4, views48 1194.0
- inovaremanhwabr: n 40, elegíveis 28, % assistido 50.5, views48 1185.0
- Esporte Noturno: n 54, elegíveis 28, % assistido 63.7, views48 1146.5
- Inovare: n 93, elegíveis 27, % assistido 50.4, views48 1122.5
- Inovare Manhwa eng: n 3, elegíveis 3, % assistido 45.2, views48 1096
- CenaReact: n 51, elegíveis 22, % assistido 53.5, views48 1055
- HistoriasEmFrames: n 41, elegíveis 21, % assistido 56.7, views48 1019.5
- InventoReact: n 18, elegíveis 10, % assistido 47.2, views48 964
- Clínica Lucrativa IA: n 18, elegíveis 8, % assistido 49.3, views48 761.5
- Lei e Lucro: n 13, elegíveis 6, % assistido 51.0, views48 654.5
- Curiosidades Noturnas: n 33, elegíveis 7, % assistido 33.9, views48 474.0
- Imóvel em Foco: n 20, elegíveis 9, % assistido 37.6, views48 263
- @CodigoInteligente-n7j: n 28, elegíveis 19, % assistido 46, views48 214.0
- YouTube inovaremanhwaverseviet: n 7, elegíveis 6, % assistido 44.5, views48 137.0
- Empresário Inteligente IA: n 12, elegíveis 3, % assistido 25.7, views48 91.5
- Vendas que Escalam: n 17, elegíveis 8, % assistido 35.5, views48 55.0
- Filme Noturno: n 38, elegíveis 17, % assistido 45.0, views48 20.5
- Animescomia: n 43, elegíveis 17, % assistido 38.4, views48 9
- CartuchoReact: n 41, elegíveis 23, % assistido 29.4, views48 5
- AssistIA Investimentos: n 33, elegíveis 7, % assistido 54.7, views48 5
- Bicho Noturno: n 44, elegíveis 11, % assistido 58.4, views48 4.5
- Manhwa Noturno: n 12, elegíveis 10, % assistido 0.0, views48 3
- ManhwaReact-ia: n 19, elegíveis 10, % assistido 17.2, views48 3
- Dorama Noturno: n 28, elegíveis 0, % assistido None, views48 None
- ForjaReact: n 15, elegíveis 1, % assistido 0, views48 0.0
- Game Noturno: n 7, elegíveis 0, % assistido None, views48 None
- Inovaremanhwaversethai: n 7, elegíveis 2, % assistido 0.0, views48 0
- YouTube inovaremanhwaverseind: n 5, elegíveis 0, % assistido None, views48 0.0
- Anime Noturno: n 7, elegíveis 0, % assistido None, views48 None
- Bilionário Noturno: n 7, elegíveis 0, % assistido None, views48 None

## Os que mais renderam (copiar a estrutura, não o texto)
- Okv4q7oH9ZQ HistoriasEmFrames: views48 17766, % assistido 91.77, continuaram 81.48 — 
- -Fyd3kUwUXk DicasFinanceirasDaIA: views48 9957, % assistido 87.48, continuaram 68.78 — 
- P91i_8wDQ6w DicasFinanceirasDaIA: views48 5163, % assistido 100.17, continuaram 75.56 — 

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

## SEM NAVEGADOR (HTTP) — saúde em 11-16T11:31: youtube 24/38, tiktok 44/58, instagram 46/53, flow 27/233, fotos 0/4 | MORTOS: youtube assistiainvestimentos, youtube bichonoturno, youtube curiosidadesnoturnas, youtube esportenoturno, youtube filmenoturno, youtube fiodameada, youtube forjareact, youtube gamenoturno, youtube historiasemframes, youtube inovare_eng, youtube inovare_ita, youtube inovare_viet

## FILAS DE POSTAGEM BAIXAS/VAZIAS (produzir/encaminhar vídeo para elas antes de qualquer melhoria de formato)
Tiktok @jornalcomia (0), Tiktok @3dfabricadeautomacoesia (1), Tiktok @inovaremanhwaverseita (0), Tiktok @canalalucinaai (0), Instagram @videocassetadascom.ia (2), Instagram @iapro.mentoria (0), YouTube rede Mundo Que Nao Existe (0), Tiktok @fabricadeautomacoesia (7), Tiktok @canalhistoriacomia (0), Tiktok @entrevistacomia (0), Tiktok @emersonjosiel2026 (2), Tiktok @inovaremanhwaverse2 (5), Tiktok @emersonjosiel2031 (5), Tiktok @inovaremanhwaversehindi (0), Tiktok @inovaremanhwaverserussian (0), Tiktok @inovaremanhwaversethai (0), Tiktok @inovaremanhwaverse (0), Tiktok @inovaremanhwaversefrench (0), Tiktok @inovaremanhwaverseesp (0), Tiktok @gameoftroneskingsroadbrasil (0), Instagram @futebolcom.ia2 (0), Instagram @sintetizerisada (5), Tiktok @filmescomia1 (0), Tiktok @aulasrevolution (0), Tiktok @e4487017 (0), Tiktok @emersonjosielmrx1995 (0), Tiktok @en1653964 (0), Tiktok @murilodoctor192 (0), Tiktok @emersongencshin (0), Tiktok @solarmundo195 (0)

## PEDIDOS E OPINIÕES DA DONA (valem mais que o júri; atender antes de qualquer outra coisa)
- 30/10 00:20 | hipercool, longo | Hipercool está DESATIVADO de propósito (como o Historias em Frames, trocado pelo Claude Code Video); volta à produção na semana que vem, depois que terminar a postagem dos capítulos já feitos. Usar um projeto para melhorar o outro: o hipercool é o mais moderno — os personagens FALAM (ela pediu falas também nos longos) e tem muitos efeitos bons; os que não acrescentam muito tempo de render podem ir para os longos | aberto
<!-- central:fim -->
