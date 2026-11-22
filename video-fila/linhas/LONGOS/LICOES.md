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
# Brief do melhorador central — Recap longo — 22/11 07:54

Vídeos nos últimos 7 dias: 18 | elegíveis (receberam o lote do feed): 3 | NÃO elegíveis: 0 | sem medida ainda: 15
% assistido mediano (só elegíveis): 0.6 | views 48 h mediana: 4 | QA com problema: 0 | saíram com parte faltando (IA caiu): 0

## Por canal
- HistoriasEmFrames: n 2, elegíveis 0, % assistido None, views48 6.5
- inovaremanhwabr: n 2, elegíveis 1, % assistido 0.6, views48 5.5
- CenaReact: n 1, elegíveis 0, % assistido None, views48 5
- @CodigoInteligente-n7j: n 8, elegíveis 1, % assistido 2.2, views48 1
- InventoReact: n 2, elegíveis 0, % assistido None, views48 None
- ForjaReact: n 1, elegíveis 0, % assistido None, views48 0
- Animescomia: n 1, elegíveis 1, % assistido 0, views48 None
- Curiosidades Noturnas: n 1, elegíveis 0, % assistido None, views48 None

## Os que mais renderam (copiar a estrutura, não o texto)
- SPThI7oMKGw @CodigoInteligente-n7j: views48 139, % assistido 2.23, continuaram 0 — 
- Vqzd9oirlC0 inovaremanhwabr: views48 4, % assistido 0.57, continuaram 0 — 
- cW8uNubxSD4 Animescomia: views48 None, % assistido 0, continuaram 0 — 

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

## SEM NAVEGADOR (HTTP) — saúde em 11-22T07:20: youtube 33/42, tiktok 41/58, instagram 43/53, flow 9/239, fotos 0/4 | MORTOS: youtube esportenoturno, youtube fiodameada, youtube inovareq8l, youtube manhwareact, youtube clinicalucrativaia, youtube empresariointeligenteia, youtube dentrodascoisas3d, youtube fatochocante, youtube pordentro, tiktok solarmundo195, tiktok vendeafiliados3, instagram emerson20332.ia

## FILAS DE POSTAGEM BAIXAS/VAZIAS (produzir/encaminhar vídeo para elas antes de qualquer melhoria de formato)
Tiktok @jornalcomia (0), Tiktok @3dfabricadeautomacoesia (1), Tiktok @inovaremanhwaverseita (0), Tiktok @canalalucinaai (0), Instagram @videocassetadascom.ia (2), Instagram @iapro.mentoria (0), Tiktok @canalhistoriacomia (4), Tiktok @entrevistacomia (0), Tiktok @emersonjosiel2026 (0), Tiktok @inovaremanhwaverse2 (6), Tiktok @doramanoturno (3), Tiktok @curiosidadesnoturnas (5), Tiktok @inovaremanhwaversehindi (0), Tiktok @inovaremanhwaverserussian (0), Tiktok @inovaremanhwaversethai (0), Tiktok @inovaremanhwaverse (0), Tiktok @inovaremanhwaversefrench (0), Tiktok @inovaremanhwaverseesp (0), Tiktok @gameoftroneskingsroadbrasil (0), Instagram @futebolcom.ia2 (0), Tiktok @filmescomia1 (0), Tiktok @aulasrevolution (0), Tiktok @e4487017 (0), Tiktok @emersonjosielmrx1995 (0), Tiktok @en1653964 (0), Tiktok @murilodoctor192 (0), Tiktok @emersongencshin (0), Tiktok @solarmundo195 (0), Tiktok @empressinovare (0), Tiktok @filmescomia00 (0)

## PEDIDOS DA DONA QUE NÃO SAÍRAM NOS ÚLTIMOS LONGOS (conferido no log do render; corrigir a causa)
- gJve_WjefZs_I_Tried_to_Start_Over__But_M: 12/13 ok — faltou: Narradores por grupo, 1º = voz do resumo
- 8fM6Ay7OJho_She_Dumped_Me_Before__Reborn: 10/13 ok — faltou: Narradores por grupo, 1º = voz do resumo, Falas de personagem com outra voz, Mini-ganchos a cada 15 min
- e2nIzNGXvmA_xtts_momo: 12/13 ok — faltou: Narradores por grupo, 1º = voz do resumo
- 82ge1YYkUyA_qwen3_momo: 12/13 ok — faltou: Narradores por grupo, 1º = voz do resumo
- 82ge1YYkUyA_s2pro_momo: 12/13 ok — faltou: Narradores por grupo, 1º = voz do resumo

## VARIANTES DOS LONGOS (views/h e % assistido por fator; só fixar com 4+ vídeos por variante)
| cortes_resumo | A | 24 | 0.04 | 2.2 |
| cortes_resumo | B | 31 | 0.07 | 0.7 |
| **cortes_resumo** | **vence B** (views/h) | | | |
| fala_rapida | A | 9 | 0.04 | 0.6 |
| fala_rapida | B | 13 | 0.02 | 0.9 |
| fala_rapida | C | 12 | 0.02 | 2.2 |
| fala_rapida | D | 11 | 0.07 | 0.5 |
| fala_rapida | E | 10 | 0.15 | 2.7 |
| **fala_rapida** | **vence E** (views/h) | | | |
| ganchos_15min | A | 15 | 0.12 | 0.6 |
| ganchos_15min | B | 15 | 0.08 | 2.6 |
| ganchos_15min | C | 25 | 0.02 | 0.8 |
| **ganchos_15min** | **vence A** (views/h) | | | |
| narradores_modo | com_terciarios | 6 | 0.01 | 36.4 |
| narradores_modo | dupla | 9 | 0.03 | 0.6 |
| narradores_modo | mistura_grande | 4 | 0.10 | 11.4 |
| narradores_modo | primarios_secundarios | 14 | 0.06 | 0.5 |
| narradores_modo | so_primarios | 12 | 0.18 | 2.0 |
| narradores_modo | solo | 10 | 0.09 | 0.7 |
| **narradores_modo** | **vence so_primarios** (views/h) | | | |
| titulo_triade | A | 25 | 0.08 | 0.6 |
| titulo_triade | B | 30 | 0.03 | 1.9 |
| **titulo_triade** | **vence A** (views/h) | | | |

## OBRAS: CONTINUAR OU NÃO (48 h+, 20+ views, 30%+ assistido)
| She Cheated On Him With 3 Other Guys But | Fio da Meada | 1 | — | 16 | pouco dado |
| She Dumped Me Before  Reborn XTTS | Fio da Meada | 2 | — | 19 | pouco dado |
| Every RUMOR Became True  So My Cheating | Fio da Meada | 14 | — | 47 | pouco dado |
| She Betrayed Him for a Servant Now He s | Fio da Meada | 1 | — | 52 | pouco dado |
| My Girlfriend Was a Demon And When I Tri | Fio da Meada | 0 | — | 54 | pouco dado |
| I Was Reborn To Give My Cheating Wife Th | Curiosidades Noturnas | 1 | — | 70 | pouco dado |
| My Ex Begged Me Back When I Started Dati | HistoriasEmFrames | 1 | — | 63 | pouco dado |
| Reborn to Reject My Cheating Fiancee and | CenaReact | 5 | — | 64 | pouco dado |
| I Was Reborn To Give My Cheating Wife Th | Fio da Meada | 1 | — | 70 | pouco dado |
| They Kicked Him To Die In The Apocalypse | HistoriasEmFrames | 14 | — | 120 | pouco dado |
| He Awakens With The Power Of The STRONGE | inovare manhwa br | 12 | — | 126 | pouco dado |
| Reincarnated With 999x LEGENDARY Power E | ForjaReact | 1 | — | 146 | pouco dado |
| Pharmacologist Reincarnated Into Isekai | Fio da Meada | 43 | — | 148 | pouco dado |
| He s the Only Genius Summoner with Creat | Fio da Meada | 143 | 2.2 | 153 | parar (assistem pouco) |
| This Useless Loser Swallowed God s Finge | inovare manhwa br | 5 | 0.6 | 158 | pouco dado |
| When a Top Player Gets 6 Unique Traits R | Fio da Meada | 39 | 0.8 | 173 | parar (assistem pouco) |
| 17  He got into the Medieval Age   bega | Fio da Meada | 50 | 0.6 | 179 | parar (assistem pouco) |
| Orphan Reincarnated With God s Leveling | HistoriasEmFrames | 11 | — | 184 | pouco dado |
| 6 He got into the Medieval Age   began | Fio da Meada | 44 | 1.4 | 185 | parar (assistem pouco) |
| 4 He got into the Medieval Age   began | Fio da Meada | 48 | 0.5 | 193 | parar (assistem pouco) |
| 16  He got into the Medieval Age   bega | Fio da Meada | 16 | 0.2 | 204 | pouco dado |
| 10  He got into the Medieval Age   bega | Fio da Meada | 50 | 2.7 | 207 | parar (assistem pouco) |
| 15  He got into the Medieval Age   bega | Fio da Meada | 47 | 0.4 | 211 | parar (assistem pouco) |
| 14  He got into the Medieval Age   bega | Fio da Meada | 115 | 2.6 | 218 | parar (assistem pouco) |
| 13  He got into the Medieval Age   bega | Fio da Meada | 57 | 8.9 | 218 | parar (assistem pouco) |
| 8 He got into the Medieval Age   began | Fio da Meada | 204 | 0.7 | 219 | parar (assistem pouco) |
| They Betrayed Him  Now He Solo Levels Up | Curiosidades Noturnas | 8 | — | 224 | pouco dado |
| He Destroys the Hunter Exam So Easily Th | CenaReact | 10 | — | 225 | pouco dado |

## PEDIDOS E OPINIÕES DA DONA (valem mais que o júri; atender antes de qualquer outra coisa)
- 30/10 00:20 | hipercool, longo | Hipercool está DESATIVADO de propósito (como o Historias em Frames, trocado pelo Claude Code Video); volta à produção na semana que vem, depois que terminar a postagem dos capítulos já feitos. Usar um projeto para melhorar o outro: o hipercool é o mais moderno — os personagens FALAM (ela pediu falas também nos longos) e tem muitos efeitos bons; os que não acrescentam muito tempo de render podem ir para os longos | aberto
<!-- central:fim -->
