# Lições da linha LONGOS (a sessão Claude escreve; o melhorador lê em toda decisão) — mais nova em cima

- 30/10: "fim cortado no meio da frase" no u7tN era falso alarme do júri (ele vê quadros soltos): a gravação da
  mascote no fim fala inteira até 5,8 s de 8 s (conferido com Whisper). O defeito real era a FALA FORA DE HORA: o fim
  dizia "qual foi a sua parte favorita ATÉ AGORA?" e a abertura (1 min) "Se você chegou até aqui". Antes de consertar
  "frase cortada", transcrever o trecho final. Veo põe som de fundo: silencedetect não acha o fim da fala.
- 30/10: pedidos da fila_dona.py chegavam sem capitulos.json/roteiro na ficha (o limpar() apagava a pasta da fila
  antes de copiar) — Pastor e P-dj sem capítulos na descrição. Todo caminho que recolhe pronto tem que copiar
  capitulos.json e roteiro.txt da fila, como o alimentador.

- 28/10: fonte do YouTube em AV1 = +46% de CPU na montagem dos trechos (decodificar AV1 é caro); em H.264 cai 31%.
  Converter depois de baixar NÃO paga (40 s CPU/min do original x 22 s/min economizados); só baixar já em H.264.
- 28/10: medir render com relógio de parede no PC1 não serve (CPU em 100% por outros); usar `ffmpeg -benchmark`
  (utime+stime) — e com `-v error` a linha "bench:" nem sai.
- 28/10: o resumo de abertura precisa de trava no código: a IA usou o desfecho (frase 521/556) mesmo proibido, e o
  Gemini 3 padrão do claude_client copiava frases do roteiro (usar Gemini 3.8).
- 28/10: o MOV da mascote termina transparente — segurar o último quadro deixa ela apagada.
- 27/10: o Gemini 3 soltou "caralho"/"merda"/"mijada" nas passagens MESMO com "sem palavrão" no prompt; o Dragon
  (KwdN) foi ao ar assim. Agora: anti_ban em todo texto do revezamento + trava no postador (pipeline.log). Prompt
  sozinho não segura regra — sempre trava em código.
- 27/10: Argon em tudo no vídeo longo = +1 h por vídeo (blocos de 40 linhas levam 1–5 min); Argon só na passagem
  (17–83 s cada) + Gemini 3.8 no resto = +10–15 min e texto limpo.
- 27/10: Argon antes de 10:10 vinha Flash-Lite calado e 7+ chamadas juntas travam as contas — Argon 1 por vez.
- 27/10: karaokê deitado com a Impact tinha vão de 0 px entre palavras ("atingiro"); 2 espaços = 9 px.
- 27/10: voz clonada sai mais baixa que o edge (-26 contra -18,5 LUFS) e a trilha calibrada no edge sobrava.
- 27/10: alimentador reenviava o vídeo que acabou de chegar (feitos lidos antes de recolher) — RA4H/PFbu feitos 2x.
- 27/10: Kaggle = 30 h de GPU por semana por conta; conta sem cota termina o kernel sem dar sinal de vida.
- 27/10: canal recebe vídeo de vários projetos — o limite diário de envios do YouTube acaba antes da nossa vez;
  postar cedo no dia.
- 27/10: a dona ADOROU o `delogo` do ffmpeg pra esconder texto/marca fixa (some sem mancha). Borrão/tarja = feio.
- 26/10: nome do narrador na legenda = retenção 3,0 no júri e reprovado pela dona. Nunca nome na legenda.
- 26/10: narrador PARCEIRO não pode ser chamado pelo nome na troca; personagem (Kratos, Naruto) pode.
- 26/10: a passagem de quem entra não pode recontar o fato da frase seguinte (sai repetido no áudio).
- 26/10: a dona quer a voz IGUAL à dos Cortes (rodízio + base kokoro/francisca/misto); nunca simplificar.
- 26/10: o júri por amostra acha sempre: balões do manhwa em inglês, gancho fraco nos 2 primeiros s, final parado
  e cortado no meio da frase, legenda/gancho em cima do rosto, vídeo vertical estreito com laterais borradas.
- 26/10: < 1 s por frase = render quebrado (edge bloqueado, clone desligado). Trava já existe.
- 26/10: vídeo de 1 h: música dinâmica leva ~30 min pra mixar; timeout tem que ser proporcional à duração.

<!-- central:inicio -->
# Brief do melhorador central — Recap longo — 13/11 08:44

Vídeos nos últimos 7 dias: 25 | elegíveis (receberam o lote do feed): 14 | NÃO elegíveis: 0 | sem medida ainda: 11
% assistido mediano (só elegíveis): 0.7 | views 48 h mediana: 10 | QA com problema: 0 | saíram com parte faltando (IA caiu): 0

## Por canal
- @CodigoInteligente-n7j: n 9, elegíveis 6, % assistido 2.9, views48 161
- InventoReact: n 3, elegíveis 3, % assistido 0.6, views48 66.5
- inovaremanhwabr: n 4, elegíveis 0, % assistido None, views48 4
- ManhwaReact-ia: n 1, elegíveis 1, % assistido 16.9, views48 1
- HistoriasEmFrames: n 1, elegíveis 0, % assistido None, views48 None
- ForjaReact: n 2, elegíveis 1, % assistido 0.1, views48 None
- CenaReact: n 2, elegíveis 1, % assistido 0, views48 None
- Curiosidades Noturnas: n 2, elegíveis 2, % assistido 0.4, views48 None
- Dorama Noturno: n 1, elegíveis 0, % assistido None, views48 None

## Os que mais renderam (copiar a estrutura, não o texto)
- nd67FAr0h14 @CodigoInteligente-n7j: views48 209, % assistido 0, continuaram 0 — 
- updrdJlgTEM @CodigoInteligente-n7j: views48 161, % assistido 0, continuaram 0 — 
- gUsq9g6aUOo InventoReact: views48 123, % assistido 0.6, continuaram 0 — 

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

## SEM NAVEGADOR (HTTP) — saúde em 11-13T08:20: youtube 21/36, tiktok 44/58, instagram 46/53, flow 87/229, fotos 0/4 | MORTOS: youtube animescomia, youtube assistiainvestimentos, youtube bichonoturno, youtube cartuchoreact, youtube dicasfinanceirasdaia, youtube filmenoturno, youtube fiodameada, youtube forjareact, youtube gamenoturno, youtube historiasemframes, youtube inovare_thai, youtube inovaremanhwabr

## FILAS DE POSTAGEM BAIXAS/VAZIAS (produzir/encaminhar vídeo para elas antes de qualquer melhoria de formato)
Tiktok @jornalcomia (0), Tiktok @3dfabricadeautomacoesia (1), Tiktok @inovaremanhwaverseita (0), Tiktok @canalalucinaai (0), Instagram @videocassetadascom.ia (2), Instagram @iapro.mentoria (0), YouTube rede Mundo Que Nao Existe (0), Tiktok @fabricadeautomacoesia (0), Tiktok @canalhistoriacomia (0), Tiktok @entrevistacomia (0), Tiktok @emersonjosiel2026 (0), Tiktok @emersonjosiel2030 (3), Tiktok @inovaremanhwaverse2 (0), Tiktok @curiosidadesnoturnas (3), Tiktok @emersonjosiel2032 (0), Tiktok @emersonjosiel2031 (0), Tiktok @inovaremanhwaversehindi (0), Tiktok @inovaremanhwaverserussian (0), Tiktok @inovaremanhwaversethai (0), Tiktok @inovaremanhwaverse (0), Tiktok @inovaremanhwaversefrench (0), Tiktok @inovaremanhwaverseesp (0), Tiktok @gameoftroneskingsroadbrasil (0), Instagram @futebolcom.ia2 (0), Instagram @sintetizerisada (0), Tiktok @filmescomia1 (0), Tiktok @aulasrevolution (0), Tiktok @e4487017 (0), Tiktok @emersonjosielmrx1995 (0), Tiktok @en1653964 (0)

## PEDIDOS DA DONA QUE NÃO SAÍRAM NOS ÚLTIMOS LONGOS (conferido no log do render; corrigir a causa)
- GMuCrqDRe9A_No_Mana_Boy_Becomes_a_Genius: 12/13 ok — faltou: Mini-ganchos a cada 15 min
- PReloN5HWSI_13__He_got_into_the_Medieval: 12/13 ok — faltou: Narradores por grupo, 1º = voz do resumo
- oLBasz5H1-4_15__He_got_into_the_Medieval: 11/13 ok — faltou: Falas de personagem com outra voz, Mini-ganchos a cada 15 min
- pnX8RlSn7Yk_14__He_got_into_the_Medieval: 12/13 ok — faltou: Falas de personagem com outra voz
- e2nIzNGXvmA_POOR_Guy_Receives_90_BILLION: 11/13 ok — faltou: Narradores por grupo, 1º = voz do resumo, Falas de personagem com outra voz

## VARIANTES DOS LONGOS (views/h e % assistido por fator; só fixar com 4+ vídeos por variante)
| cortes_resumo | A | 19 | 0.04 | 0.6 |
| cortes_resumo | B | 19 | 0.04 | 1.3 |
| **cortes_resumo** | **vence B** (views/h) | | | |
| fala_rapida | A | 6 | 0.03 | 0.1 |
| fala_rapida | B | 9 | 0.03 | 0.4 |
| fala_rapida | C | 11 | 0.04 | 10.4 |
| fala_rapida | D | 7 | 0.04 | 0.6 |
| fala_rapida | E | 5 | 1.31 | 8.2 |
| **fala_rapida** | **vence E** (views/h) | | | |
| ganchos_15min | A | 4 | 0.04 | 20.2 |
| ganchos_15min | B | 11 | 0.05 | 0.4 |
| ganchos_15min | C | 23 | 0.03 | 1.5 |
| **ganchos_15min** | **vence B** (views/h) | | | |
| narradores_modo | com_terciarios | 2 | 0.01 | 36.4 |
| narradores_modo | dupla | 2 | 0.01 | — |
| narradores_modo | mistura_grande | 2 | 0.14 | — |
| narradores_modo | primarios_secundarios | 7 | 0.04 | 0.3 |
| narradores_modo | so_primarios | 16 | 0.03 | 1.1 |
| narradores_modo | solo | 9 | 0.06 | 12.4 |
| titulo_triade | A | 18 | 0.04 | 1.9 |
| titulo_triade | B | 20 | 0.04 | 1.1 |
| **titulo_triade** | **vence B** (views/h) | | | |

## OBRAS: CONTINUAR OU NÃO (48 h+, 20+ views, 30%+ assistido)
| 14  He got into the Medieval Age   bega | Fio da Meada | 3 | — | 3 | pouco dado |
| 13  He got into the Medieval Age   bega | Fio da Meada | 4 | — | 3 | pouco dado |
| 8 He got into the Medieval Age   began | Fio da Meada | 4 | — | 4 | pouco dado |
| No Mana Boy Becomes a Genius Alchemist i | InovareManhwaVerse | 0 | — | 6 | pouco dado |
| They Betrayed Him  Now He Solo Levels Up | Curiosidades Noturnas | 0 | — | 9 | pouco dado |
| He Destroys the Hunter Exam So Easily Th | CenaReact | 0 | — | 10 | pouco dado |
| He Trains Hard After Ending Up in the Bo | ForjaReact | 0 | — | 12 | pouco dado |
| He Spent 3000 Years in a Loop  Now Even | Manhwa Noturno | 2 | 0.1 | 13 | pouco dado |
| He Acquires a New Skill Every Day    Man | Dorama Noturno | 1 | — | 19 | pouco dado |
| His Ex Girlfriend wanted to Return when | InventoReact | 538 | 3.0 | 25 | pouco dado |
| He got into the Stone Age and Conquered | inovare manhwa br | 6 | — | 29 | pouco dado |
| His Party Left Him to Fight an Army For | InovareManhwaVerse | 3 | — | 30 | pouco dado |
| He Was Lvl 99 But Got Reincarnated So He | Manhwa Noturno | 1 | 0.3 | 34 | pouco dado |
| He Got Max Luck After a System Error and | Curiosidades Noturnas | 5 | 0.7 | 34 | pouco dado |
| Lost their parents on plane crash they w | CenaReact | 0 | — | 36 | pouco dado |
| Bullied Boy Levels Up 300 Times Using Ch | ForjaReact | 1 | 0.1 | 38 | pouco dado |
| Depressed Hero Hated by Humanity Is Love | HistoriasEmFrames | 1 | — | 39 | pouco dado |
| 12  He got into the Medieval Age   bega | Fio da Meada | 44 | 11.4 | 39 | pouco dado |
| Bullied Orphan Dated His Master After Be | InovareManhwaVerse | 4 | — | 40 | pouco dado |
| 11  He got into the Medieval Age   bega | Fio da Meada | 25 | 5.5 | 44 | pouco dado |
| 9 He got into the Medieval Age   began | Fio da Meada | 220 | 2.2 | 46 | pouco dado |
| He Devours Viruses to Become the Stronge | inovare manhwa br | 7 | — | 52 | pouco dado |
| 2  The Little Orc everyone Mocked accid | InventoReact | 123 | 0.6 | 55 | parar (assistem pouco) |
| When the Slave Becomes the  1 Mage and E | InovareManhwaVerse | 3 | 0.1 | 57 | pouco dado |
| He Eats Monster Cores and Receives Their | InventoReact | 12 | 0.3 | 61 | pouco dado |
| He Opens Loot Boxes in his Safe Hideout | Fio da Meada | 116 | 3.9 | 77 | parar (assistem pouco) |
| He Farms Monsters in His Own Dungeon and | inovare manhwa br | 5 | — | 149 | pouco dado |
| 7 He got into the Medieval Age   began | inovare manhwa br | 6 | 8.0 | 152 | pouco dado |

## PEDIDOS E OPINIÕES DA DONA (valem mais que o júri; atender antes de qualquer outra coisa)
- 30/10 00:20 | hipercool, longo | Hipercool está DESATIVADO de propósito (como o Historias em Frames, trocado pelo Claude Code Video); volta à produção na semana que vem, depois que terminar a postagem dos capítulos já feitos. Usar um projeto para melhorar o outro: o hipercool é o mais moderno — os personagens FALAM (ela pediu falas também nos longos) e tem muitos efeitos bons; os que não acrescentam muito tempo de render podem ir para os longos | aberto
<!-- central:fim -->
