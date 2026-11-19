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
# Brief do melhorador central — Recap longo — 19/11 03:54

Vídeos nos últimos 7 dias: 31 | elegíveis (receberam o lote do feed): 25 | NÃO elegíveis: 0 | sem medida ainda: 6
% assistido mediano (só elegíveis): 0.7 | views 48 h mediana: 6.0 | QA com problema: 0 | saíram com parte faltando (IA caiu): 0

## Por canal
- @CodigoInteligente-n7j: n 12, elegíveis 11, % assistido 0.8, views48 34
- Curiosidades Noturnas: n 1, elegíveis 1, % assistido 0, views48 6
- InventoReact: n 7, elegíveis 5, % assistido 3.5, views48 5.5
- HistoriasEmFrames: n 2, elegíveis 1, % assistido 0, views48 5
- inovaremanhwabr: n 2, elegíveis 1, % assistido 0.6, views48 4
- CenaReact: n 1, elegíveis 1, % assistido 0, views48 3
- Dorama Noturno: n 2, elegíveis 2, % assistido 50.0, views48 1.0
- Animescomia: n 2, elegíveis 2, % assistido 0.0, views48 1
- ForjaReact: n 2, elegíveis 1, % assistido 0, views48 0.0

## Os que mais renderam (copiar a estrutura, não o texto)
- HomhRlIE72I InventoReact: views48 558, % assistido 3.02, continuaram 0 — 
- AjgJG8HAfLk @CodigoInteligente-n7j: views48 192, % assistido 0.65, continuaram 0 — 
- SPThI7oMKGw @CodigoInteligente-n7j: views48 139, % assistido 2.23, continuaram 0 — 

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

## SEM NAVEGADOR (HTTP) — saúde em 11-19T03:21: youtube 36/41, tiktok 43/58, instagram 46/53, flow 15/234, fotos 0/4 | MORTOS: youtube filmenoturno, youtube fiodameada, youtube manhwareact, youtube dentrodascoisas3d, youtube fatochocante, tiktok gameoftroneskingsroadbrasil, flow seebotsia, flow emersonjosiel2032@pc2, flow aulacomia@x200ma, flow canalanimescomia@x200ma, flow canalhistoriacomia@x200ma, flow comoseriasecomia@x200ma

## FILAS DE POSTAGEM BAIXAS/VAZIAS (produzir/encaminhar vídeo para elas antes de qualquer melhoria de formato)
MS Energy - Instagram @msenergycap (4), Tiktok @jornalcomia (0), Tiktok @3dfabricadeautomacoesia (1), Tiktok @inovaremanhwaverseita (0), Tiktok @canalalucinaai (0), Instagram @videocassetadascom.ia (2), Instagram @iapro.mentoria (0), Tiktok @canalhistoriacomia (0), Tiktok @entrevistacomia (0), Tiktok @emersonjosiel2026 (0), Tiktok @inovaremanhwaverse2 (6), Tiktok @emersonjosiel2031 (9), Tiktok @inovaremanhwaversehindi (0), Tiktok @inovaremanhwaverserussian (0), Tiktok @inovaremanhwaversethai (0), Tiktok @inovaremanhwaverse (0), Tiktok @inovaremanhwaversefrench (0), Tiktok @inovaremanhwaverseesp (0), Tiktok @gameoftroneskingsroadbrasil (0), Instagram @futebolcom.ia2 (0), Tiktok @filmescomia1 (0), Tiktok @aulasrevolution (0), Tiktok @e4487017 (0), Tiktok @emersonjosielmrx1995 (0), Tiktok @en1653964 (0), Tiktok @murilodoctor192 (0), Tiktok @emersongencshin (0), Tiktok @solarmundo195 (0), Tiktok @empressinovare (0), Tiktok @filmescomia00 (0)

## PEDIDOS DA DONA QUE NÃO SAÍRAM NOS ÚLTIMOS LONGOS (conferido no log do render; corrigir a causa)
- 5DoGv3EXHgc_REENCARNOU_como_VILÃO____E_t: 12/13 ok — faltou: Falas de personagem com outra voz
- 97bBeHddKJI_When_The_Strongest_Mage_Of_A: 10/13 ok — faltou: Falas de personagem com outra voz, Capítulos, Mini-ganchos a cada 15 min
- zZGctp8j_QU_Beating_Up_the_Arrogant_Bull: 11/13 ok — faltou: Falas de personagem com outra voz, Mini-ganchos a cada 15 min
- ZZ7LeUws7-c_Reborn_to_Reject_My_Cheating: 12/13 ok — faltou: Falas de personagem com outra voz
- keBJ_bd5oVw_My_Ex_Begged_Me_Back_When_I_: 13/13 ok — faltou: nada

## VARIANTES DOS LONGOS (views/h e % assistido por fator; só fixar com 4+ vídeos por variante)
| cortes_resumo | A | 22 | 0.05 | 2.2 |
| cortes_resumo | B | 26 | 0.19 | 0.7 |
| **cortes_resumo** | **vence B** (views/h) | | | |
| fala_rapida | A | 9 | 0.06 | 0.6 |
| fala_rapida | B | 13 | 0.03 | 0.9 |
| fala_rapida | C | 10 | 0.03 | 2.2 |
| fala_rapida | D | 8 | 0.09 | 0.5 |
| fala_rapida | E | 8 | 0.36 | 2.7 |
| **fala_rapida** | **vence E** (views/h) | | | |
| ganchos_15min | A | 13 | 0.23 | 0.6 |
| ganchos_15min | B | 13 | 0.38 | 2.6 |
| ganchos_15min | C | 22 | 0.03 | 0.8 |
| **ganchos_15min** | **vence B** (views/h) | | | |
| narradores_modo | com_terciarios | 4 | 0.01 | 36.4 |
| narradores_modo | dupla | 9 | 0.06 | 0.6 |
| narradores_modo | mistura_grande | 3 | 0.23 | 11.4 |
| narradores_modo | primarios_secundarios | 11 | 0.12 | 0.5 |
| narradores_modo | so_primarios | 11 | 0.40 | 2.0 |
| narradores_modo | solo | 10 | 0.12 | 0.7 |
| titulo_triade | A | 21 | 0.09 | 0.6 |
| titulo_triade | B | 27 | 0.07 | 1.9 |
| **titulo_triade** | **vence A** (views/h) | | | |

## OBRAS: CONTINUAR OU NÃO (48 h+, 20+ views, 30%+ assistido)
| They Kicked Him To Die In The Apocalypse | HistoriasEmFrames | 12 | — | 44 | pouco dado |
| He Awakens With The Power Of The STRONGE | inovare manhwa br | 2 | — | 50 | pouco dado |
| Reincarnated With 999x LEGENDARY Power E | ForjaReact | 0 | — | 70 | pouco dado |
| Pharmacologist Reincarnated Into Isekai | Fio da Meada | 43 | — | 72 | pouco dado |
| He s the Only Genius Summoner with Creat | Fio da Meada | 143 | 2.2 | 77 | parar (assistem pouco) |
| This Useless Loser Swallowed God s Finge | inovare manhwa br | 5 | 0.6 | 82 | pouco dado |
| When a Top Player Gets 6 Unique Traits R | Fio da Meada | 38 | 0.8 | 97 | parar (assistem pouco) |
| 17  He got into the Medieval Age   bega | Fio da Meada | 44 | 0.6 | 103 | parar (assistem pouco) |
| Orphan Reincarnated With God s Leveling | HistoriasEmFrames | 8 | — | 108 | pouco dado |
| 6 He got into the Medieval Age   began | Fio da Meada | 44 | 1.4 | 109 | parar (assistem pouco) |
| 4 He got into the Medieval Age   began | Fio da Meada | 48 | 0.5 | 117 | parar (assistem pouco) |
| 16  He got into the Medieval Age   bega | Fio da Meada | 15 | 0.2 | 128 | pouco dado |
| 10  He got into the Medieval Age   bega | Fio da Meada | 50 | 2.7 | 131 | parar (assistem pouco) |
| 15  He got into the Medieval Age   bega | Fio da Meada | 36 | 0.4 | 135 | parar (assistem pouco) |
| 14  He got into the Medieval Age   bega | Fio da Meada | 114 | 2.6 | 142 | parar (assistem pouco) |
| 13  He got into the Medieval Age   bega | Fio da Meada | 57 | 8.9 | 142 | parar (assistem pouco) |
| 8 He got into the Medieval Age   began | Fio da Meada | 202 | 0.7 | 143 | parar (assistem pouco) |
| They Betrayed Him  Now He Solo Levels Up | Curiosidades Noturnas | 8 | — | 148 | pouco dado |
| He Destroys the Hunter Exam So Easily Th | CenaReact | 10 | — | 149 | pouco dado |
| He Trains Hard After Ending Up in the Bo | ForjaReact | 0 | — | 150 | pouco dado |
| He got into the Stone Age and Conquered | inovare manhwa br | 15 | — | 168 | pouco dado |
| He Got Max Luck After a System Error and | Curiosidades Noturnas | 5 | 0.1 | 174 | pouco dado |
| Lost their parents on plane crash they w | CenaReact | 2 | — | 175 | pouco dado |
| Bullied Boy Levels Up 300 Times Using Ch | ForjaReact | 1 | 0.1 | 177 | pouco dado |
| Depressed Hero Hated by Humanity Is Love | HistoriasEmFrames | 4 | — | 178 | pouco dado |
| 12  He got into the Medieval Age   bega | Fio da Meada | 74 | 11.4 | 178 | parar (assistem pouco) |
| 11  He got into the Medieval Age   bega | Fio da Meada | 27 | 5.5 | 183 | parar (assistem pouco) |
| 9 He got into the Medieval Age   began | Fio da Meada | 267 | 2.2 | 185 | parar (assistem pouco) |

## PEDIDOS E OPINIÕES DA DONA (valem mais que o júri; atender antes de qualquer outra coisa)
- 30/10 00:20 | hipercool, longo | Hipercool está DESATIVADO de propósito (como o Historias em Frames, trocado pelo Claude Code Video); volta à produção na semana que vem, depois que terminar a postagem dos capítulos já feitos. Usar um projeto para melhorar o outro: o hipercool é o mais moderno — os personagens FALAM (ela pediu falas também nos longos) e tem muitos efeitos bons; os que não acrescentam muito tempo de render podem ir para os longos | aberto
<!-- central:fim -->
