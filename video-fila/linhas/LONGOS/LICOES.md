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
# Brief do melhorador central — Recap longo — 15/11 03:34

Vídeos nos últimos 7 dias: 33 | elegíveis (receberam o lote do feed): 22 | NÃO elegíveis: 0 | sem medida ainda: 11
% assistido mediano (só elegíveis): 0.6 | views 48 h mediana: 6.5 | QA com problema: 0 | saíram com parte faltando (IA caiu): 0

## Por canal
- InventoReact: n 6, elegíveis 3, % assistido 0.6, views48 123
- @CodigoInteligente-n7j: n 14, elegíveis 9, % assistido 2.7, views48 75.5
- inovaremanhwabr: n 2, elegíveis 2, % assistido 0.3, views48 6.5
- Curiosidades Noturnas: n 2, elegíveis 2, % assistido 0.4, views48 5
- HistoriasEmFrames: n 2, elegíveis 1, % assistido 0, views48 2
- CenaReact: n 2, elegíveis 2, % assistido 0.0, views48 2.0
- Dorama Noturno: n 2, elegíveis 1, % assistido 0, views48 1
- ForjaReact: n 2, elegíveis 2, % assistido 0.1, views48 0.5
- Animescomia: n 1, elegíveis 0, % assistido None, views48 None

## Os que mais renderam (copiar a estrutura, não o texto)
- HomhRlIE72I InventoReact: views48 558, % assistido 3.02, continuaram 0 — 
- cIB4X-Q9MIk @CodigoInteligente-n7j: views48 220, % assistido 2.16, continuaram 0 — 
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

## SEM NAVEGADOR (HTTP) — saúde em 11-15T03:26: youtube 29/36, tiktok 44/58, instagram 46/53, flow 35/232, fotos 0/4 | MORTOS: youtube dicasfinanceirasdaia, youtube historiasemframes, youtube inovare_viet, youtube inovareu8b, youtube manhwareact, youtube clinicalucrativaia, youtube imovelemfoco, flow seebotsia, flow emersonjosiel2032@pc2, flow aulacomia@x200ma, flow canalanimescomia@x200ma, flow canalhistoriacomia@x200ma

## FILAS DE POSTAGEM BAIXAS/VAZIAS (produzir/encaminhar vídeo para elas antes de qualquer melhoria de formato)
Tiktok @jornalcomia (0), Tiktok @3dfabricadeautomacoesia (1), Tiktok @inovaremanhwaverseita (0), Tiktok @canalalucinaai (0), Instagram @videocassetadascom.ia (2), Instagram @iapro.mentoria (0), YouTube rede Mundo Que Nao Existe (0), Tiktok @fabricadeautomacoesia (0), Tiktok @canalhistoriacomia (0), Tiktok @entrevistacomia (0), Tiktok @emersonjosiel2026 (1), Tiktok @emersonjosiel2030 (0), Tiktok @inovaremanhwaverse2 (0), Tiktok @curiosidadesnoturnas (1), Tiktok @emersonjosiel2032 (1), Tiktok @emersonjosiel2031 (0), Tiktok @inovaremanhwaversehindi (0), Tiktok @inovaremanhwaverserussian (0), Tiktok @inovaremanhwaversethai (0), Tiktok @inovaremanhwaverse (0), Tiktok @inovaremanhwaversefrench (0), Tiktok @inovaremanhwaverseesp (0), Tiktok @gameoftroneskingsroadbrasil (0), Instagram @futebolcom.ia2 (0), Instagram @sintetizerisada (3), Tiktok @filmescomia1 (0), Tiktok @aulasrevolution (0), Tiktok @e4487017 (0), Tiktok @emersonjosielmrx1995 (0), Tiktok @en1653964 (0)

## PEDIDOS DA DONA QUE NÃO SAÍRAM NOS ÚLTIMOS LONGOS (conferido no log do render; corrigir a causa)
- kh0Ejfzs4_4_Jujutsu_Kaisen_SEASON_1_RECA: 12/13 ok — faltou: Mini-ganchos a cada 15 min
- t-mnhLoSb18_Reincarnated_With_999x_LEGEN: 12/13 ok — faltou: Narradores por grupo, 1º = voz do resumo
- PvkF8Ut-mIM_He_Awakens_With_The_Power_Of: 12/13 ok — faltou: Mini-ganchos a cada 15 min
- y5Pm6ba-kIM_He_got_ban_from_using_MAGIC_: 12/13 ok — faltou: Falas de personagem com outra voz
- X29n4fGbdXw_He_Entered_His_Favorite_Game: 12/13 ok — faltou: Falas de personagem com outra voz

## VARIANTES DOS LONGOS (views/h e % assistido por fator; só fixar com 4+ vídeos por variante)
| cortes_resumo | A | 26 | 0.03 | 0.5 |
| cortes_resumo | B | 30 | 0.05 | 1.3 |
| **cortes_resumo** | **vence B** (views/h) | | | |
| fala_rapida | A | 8 | 0.04 | 0.4 |
| fala_rapida | B | 14 | 0.03 | 0.3 |
| fala_rapida | C | 17 | 0.03 | 1.6 |
| fala_rapida | D | 8 | 0.04 | 0.5 |
| fala_rapida | E | 9 | 0.06 | 3.9 |
| **fala_rapida** | **vence E** (views/h) | | | |
| ganchos_15min | A | 12 | 0.04 | 3.9 |
| ganchos_15min | B | 15 | 0.04 | 0.4 |
| ganchos_15min | C | 29 | 0.03 | 0.9 |
| **ganchos_15min** | **vence B** (views/h) | | | |
| narradores_modo | com_terciarios | 4 | 0.01 | 18.3 |
| narradores_modo | dupla | 6 | 0.03 | 0.1 |
| narradores_modo | mistura_grande | 4 | 0.16 | 11.4 |
| narradores_modo | primarios_secundarios | 10 | 0.06 | 0.4 |
| narradores_modo | so_primarios | 19 | 0.03 | 1.1 |
| narradores_modo | solo | 13 | 0.04 | 3.0 |
| **narradores_modo** | **vence mistura_grande** (views/h) | | | |
| titulo_triade | A | 23 | 0.03 | 0.8 |
| titulo_triade | B | 33 | 0.04 | 0.9 |
| **titulo_triade** | **vence B** (views/h) | | | |

## OBRAS: CONTINUAR OU NÃO (48 h+, 20+ views, 30%+ assistido)
| He Can Upgrade Anything to Its Max Level | Manhwa Noturno | 1 | — | 5 | pouco dado |
| No Mana  No Skills  He Knows What Hard W | Dorama Noturno | 0 | — | 5 | pouco dado |
| While Everyone Else Can Have Only 1 Titl | Animescomia | 0 | — | 6 | pouco dado |
| Orphan Reincarnated With God s Leveling | HistoriasEmFrames | 1 | — | 11 | pouco dado |
| 6 He got into the Medieval Age   began | Fio da Meada | 25 | — | 12 | pouco dado |
| 4 He got into the Medieval Age   began | Fio da Meada | 16 | — | 20 | pouco dado |
| She Dumped Me Before  Reborn  I Want Her | InventoReact | 3 | — | 21 | pouco dado |
| Boy is Reincarnated As The Weakest F Ran | InovareManhwaVerse | 1 | — | 22 | pouco dado |
| He Accidentally Reincarnated As A Lv 1 S | InventoReact | 3 | — | 23 | pouco dado |
| 16  He got into the Medieval Age   bega | Fio da Meada | 3 | — | 32 | pouco dado |
| 10  He got into the Medieval Age   bega | Fio da Meada | 23 | 2.7 | 35 | pouco dado |
| 15  He got into the Medieval Age   bega | Fio da Meada | 11 | — | 39 | pouco dado |
| POOR Guy Receives 90 BILLION To Get REVE | Manhwa Noturno | 11 | 0.3 | 40 | pouco dado |
| 14  He got into the Medieval Age   bega | Fio da Meada | 46 | 2.6 | 46 | pouco dado |
| 13  He got into the Medieval Age   bega | Fio da Meada | 20 | 8.9 | 46 | pouco dado |
| 8 He got into the Medieval Age   began | Fio da Meada | 192 | 0.7 | 46 | pouco dado |
| No Mana Boy Becomes a Genius Alchemist i | InovareManhwaVerse | 3 | — | 49 | pouco dado |
| They Betrayed Him  Now He Solo Levels Up | Curiosidades Noturnas | 4 | — | 51 | pouco dado |
| He Destroys the Hunter Exam So Easily Th | CenaReact | 3 | — | 53 | pouco dado |
| He Trains Hard After Ending Up in the Bo | ForjaReact | 0 | — | 54 | pouco dado |
| He Spent 3000 Years in a Loop  Now Even | Manhwa Noturno | 3 | 0.1 | 56 | pouco dado |
| He Acquires a New Skill Every Day    Man | Dorama Noturno | 1 | — | 62 | pouco dado |
| His Ex Girlfriend wanted to Return when | InventoReact | 580 | 3.0 | 68 | parar (assistem pouco) |
| He got into the Stone Age and Conquered | inovare manhwa br | 6 | — | 72 | pouco dado |
| His Party Left Him to Fight an Army For | InovareManhwaVerse | 3 | — | 73 | pouco dado |
| He Was Lvl 99 But Got Reincarnated So He | Manhwa Noturno | 1 | 0.3 | 76 | pouco dado |
| He Got Max Luck After a System Error and | Curiosidades Noturnas | 5 | 0.1 | 77 | pouco dado |
| Lost their parents on plane crash they w | CenaReact | 1 | — | 79 | pouco dado |

## PEDIDOS E OPINIÕES DA DONA (valem mais que o júri; atender antes de qualquer outra coisa)
- 30/10 00:20 | hipercool, longo | Hipercool está DESATIVADO de propósito (como o Historias em Frames, trocado pelo Claude Code Video); volta à produção na semana que vem, depois que terminar a postagem dos capítulos já feitos. Usar um projeto para melhorar o outro: o hipercool é o mais moderno — os personagens FALAM (ela pediu falas também nos longos) e tem muitos efeitos bons; os que não acrescentam muito tempo de render podem ir para os longos | aberto
<!-- central:fim -->
