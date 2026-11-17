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
# Brief do melhorador central — Recap longo — 17/11 00:24

Vídeos nos últimos 7 dias: 40 | elegíveis (receberam o lote do feed): 34 | NÃO elegíveis: 0 | sem medida ainda: 6
% assistido mediano (só elegíveis): 0.6 | views 48 h mediana: 7 | QA com problema: 0 | saíram com parte faltando (IA caiu): 0

## Por canal
- @CodigoInteligente-n7j: n 16, elegíveis 13, % assistido 2.2, views48 34.5
- InventoReact: n 8, elegíveis 7, % assistido 3.0, views48 10
- inovaremanhwabr: n 3, elegíveis 3, % assistido 0.6, views48 6.5
- Curiosidades Noturnas: n 2, elegíveis 2, % assistido 0.4, views48 5.5
- HistoriasEmFrames: n 2, elegíveis 2, % assistido 0.0, views48 3.5
- CenaReact: n 2, elegíveis 2, % assistido 0.0, views48 2.0
- Dorama Noturno: n 2, elegíveis 2, % assistido 50.0, views48 1
- Animescomia: n 2, elegíveis 1, % assistido 0, views48 1
- ForjaReact: n 3, elegíveis 2, % assistido 0.1, views48 0.5

## Os que mais renderam (copiar a estrutura, não o texto)
- HomhRlIE72I InventoReact: views48 558, % assistido 3.02, continuaram 0 — 
- cIB4X-Q9MIk @CodigoInteligente-n7j: views48 220, % assistido 2.16, continuaram 0 — 
- AjgJG8HAfLk @CodigoInteligente-n7j: views48 192, % assistido 0.65, continuaram 0 — 

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

## SEM NAVEGADOR (HTTP) — saúde em 11-16T23:26: youtube 27/38, tiktok 44/58, instagram 46/53, flow 18/233, fotos 0/4 | MORTOS: youtube dicasfinanceirasdaia, youtube inovare_thai, youtube inovare_viet, youtube inovaremanhwabr, youtube inovaremanhwaverse, youtube inovareq8l, youtube inovareu8b, youtube inventoreact, youtube manhwareact, youtube leielucro, youtube bilionarionoturno, flow seebotsia

## FILAS DE POSTAGEM BAIXAS/VAZIAS (produzir/encaminhar vídeo para elas antes de qualquer melhoria de formato)
MS Energy - Instagram @msenergycap (4), Tiktok @jornalcomia (0), Tiktok @3dfabricadeautomacoesia (1), Tiktok @inovaremanhwaverseita (0), Tiktok @canalalucinaai (0), Instagram @videocassetadascom.ia (2), Instagram @iapro.mentoria (0), YouTube rede InventoReact (0), YouTube rede Mundo Que Nao Existe (0), Tiktok @canalhistoriacomia (0), Tiktok @entrevistacomia (0), Tiktok @emersonjosiel2026 (2), Tiktok @inovaremanhwaverse2 (6), Tiktok @emersonjosiel2031 (6), Tiktok @inovaremanhwaversehindi (0), Tiktok @inovaremanhwaverserussian (0), Tiktok @inovaremanhwaversethai (0), Tiktok @inovaremanhwaverse (0), Tiktok @inovaremanhwaversefrench (0), Tiktok @inovaremanhwaverseesp (0), Tiktok @gameoftroneskingsroadbrasil (0), Instagram @futebolcom.ia2 (0), Instagram @sintetizerisada (5), Tiktok @filmescomia1 (0), Tiktok @aulasrevolution (0), Tiktok @e4487017 (0), Tiktok @emersonjosielmrx1995 (0), Tiktok @en1653964 (0), Tiktok @murilodoctor192 (0), Tiktok @emersongencshin (0)

## PEDIDOS DA DONA QUE NÃO SAÍRAM NOS ÚLTIMOS LONGOS (conferido no log do render; corrigir a causa)
- X29n4fGbdXw_He_Entered_His_Favorite_Game: 12/13 ok — faltou: Falas de personagem com outra voz
- SjQHP-0GKJs_1_11__His_Girlfriend_Cheated: 12/13 ok — faltou: Falas de personagem com outra voz
- 0w1FjXmgX0w_They_Kicked_Him_To_Die_In_Th: 10/13 ok — faltou: Falas de personagem com outra voz, Capítulos, Mini-ganchos a cada 15 min
- SO-icNCOO3E_HE_WAS_REJECTED_BY_HIS_CHILD: 10/13 ok — faltou: Narradores por grupo, 1º = voz do resumo, Falas de personagem com outra voz, Mini-ganchos a cada 15 min
- 5DoGv3EXHgc_REENCARNOU_como_VILÃO____E_t: 12/13 ok — faltou: Falas de personagem com outra voz

## VARIANTES DOS LONGOS (views/h e % assistido por fator; só fixar com 4+ vídeos por variante)
| cortes_resumo | A | 34 | 0.03 | 1.1 |
| cortes_resumo | B | 40 | 0.05 | 1.1 |
| **cortes_resumo** | **vence B** (views/h) | | | |
| fala_rapida | A | 11 | 0.05 | 0.9 |
| fala_rapida | B | 18 | 0.03 | 0.5 |
| fala_rapida | C | 19 | 0.03 | 0.9 |
| fala_rapida | D | 12 | 0.04 | 3.1 |
| fala_rapida | E | 14 | 0.10 | 2.7 |
| **fala_rapida** | **vence E** (views/h) | | | |
| ganchos_15min | A | 21 | 0.07 | 0.9 |
| ganchos_15min | B | 19 | 0.03 | 2.6 |
| ganchos_15min | C | 34 | 0.03 | 1.1 |
| **ganchos_15min** | **vence A** (views/h) | | | |
| narradores_modo | com_terciarios | 5 | 0.01 | 1.3 |
| narradores_modo | dupla | 8 | 0.04 | 0.1 |
| narradores_modo | mistura_grande | 5 | 0.06 | 25.4 |
| narradores_modo | primarios_secundarios | 15 | 0.08 | 0.4 |
| narradores_modo | so_primarios | 25 | 0.03 | 1.5 |
| narradores_modo | solo | 16 | 0.04 | 0.9 |
| **narradores_modo** | **vence primarios_secundarios** (views/h) | | | |
| titulo_triade | A | 34 | 0.04 | 2.0 |
| titulo_triade | B | 40 | 0.04 | 0.7 |
| **titulo_triade** | **vence A** (views/h) | | | |

## OBRAS: CONTINUAR OU NÃO (48 h+, 20+ views, 30%+ assistido)
| Jujutsu Kaisen SEASON 1 RECAP    JJK Tim | Animescomia | 0 | — | 17 | pouco dado |
| Reincarnated With 999x LEGENDARY Power E | ForjaReact | 0 | — | 18 | pouco dado |
| Overpowered Boy Raised By Dragon Hides H | InventoReact | 1 | — | 19 | pouco dado |
| When a Mercenary Is Reborn as a Genius f | InovareManhwaVerse | 1 | — | 20 | pouco dado |
| He s the Only Genius Summoner with Creat | Fio da Meada | 2 | — | 25 | pouco dado |
| This Useless Loser Swallowed God s Finge | inovare manhwa br | 4 | 0.6 | 30 | pouco dado |
| He Can Make Any Weak Skill God Level by | InventoReact | 4 | 3.5 | 41 | pouco dado |
| When a Top Player Gets 6 Unique Traits R | Fio da Meada | 27 | 0.8 | 45 | pouco dado |
| He Can Upgrade Anything to Its Max Level | Manhwa Noturno | 1 | 99.9 | 49 | pouco dado |
| No Mana  No Skills  He Knows What Hard W | Dorama Noturno | 1 | 100.0 | 50 | pouco dado |
| While Everyone Else Can Have Only 1 Titl | Animescomia | 1 | — | 50 | pouco dado |
| 17  He got into the Medieval Age   bega | Fio da Meada | 21 | — | 51 | pouco dado |
| Orphan Reincarnated With God s Leveling | HistoriasEmFrames | 6 | — | 56 | pouco dado |
| 6 He got into the Medieval Age   began | Fio da Meada | 39 | 1.4 | 57 | parar (assistem pouco) |
| She Dumped Me for the  Hero  Now I Awake | InventoReact | 6 | 13.8 | 61 | pouco dado |
| 4 He got into the Medieval Age   began | Fio da Meada | 41 | 0.5 | 65 | parar (assistem pouco) |
| She Dumped Me Before  Reborn  I Want Her | InventoReact | 3 | 39.4 | 66 | pouco dado |
| Boy is Reincarnated As The Weakest F Ran | InovareManhwaVerse | 3 | 0.9 | 66 | pouco dado |
| He Accidentally Reincarnated As A Lv 1 S | InventoReact | 5 | 1.3 | 68 | pouco dado |
| 16  He got into the Medieval Age   bega | Fio da Meada | 8 | 0.2 | 76 | pouco dado |
| 10  He got into the Medieval Age   bega | Fio da Meada | 46 | 2.7 | 79 | parar (assistem pouco) |
| 15  He got into the Medieval Age   bega | Fio da Meada | 18 | 0.4 | 83 | pouco dado |
| POOR Guy Receives 90 BILLION To Get REVE | Manhwa Noturno | 12 | 0.3 | 85 | pouco dado |
| 14  He got into the Medieval Age   bega | Fio da Meada | 82 | 2.6 | 90 | parar (assistem pouco) |
| 13  He got into the Medieval Age   bega | Fio da Meada | 47 | 8.9 | 90 | parar (assistem pouco) |
| 8 He got into the Medieval Age   began | Fio da Meada | 196 | 0.7 | 91 | parar (assistem pouco) |
| No Mana Boy Becomes a Genius Alchemist i | InovareManhwaVerse | 6 | — | 93 | pouco dado |
| They Betrayed Him  Now He Solo Levels Up | Curiosidades Noturnas | 8 | — | 96 | pouco dado |

## PEDIDOS E OPINIÕES DA DONA (valem mais que o júri; atender antes de qualquer outra coisa)
- 30/10 00:20 | hipercool, longo | Hipercool está DESATIVADO de propósito (como o Historias em Frames, trocado pelo Claude Code Video); volta à produção na semana que vem, depois que terminar a postagem dos capítulos já feitos. Usar um projeto para melhorar o outro: o hipercool é o mais moderno — os personagens FALAM (ela pediu falas também nos longos) e tem muitos efeitos bons; os que não acrescentam muito tempo de render podem ir para os longos | aberto
<!-- central:fim -->
