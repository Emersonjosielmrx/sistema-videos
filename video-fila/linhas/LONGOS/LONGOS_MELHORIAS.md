# LONGOS — melhorias da engenharia reversa: A FAZER x JÁ FEITO (dona, 01/11/2026)



> "Tem que ter uma lista do que está pra fazer e uma do que já foi feito, tanto pro analisador não repetir as mesmas

> coisas como pro modelo não tentar implementar duas vezes e fazer errado a segunda."



**Este arquivo é a fonte única das mudanças nos LONGOS.** Vale a mesma obrigação dos Shorts

(`D:\video-fila\aprendizado\LEIA_ANTES_DE_MELHORAR.md`): todo chat que for melhorar LONGO (título, tags, descrição,

narração, roteiro, capa, abertura, ritmo) lê isto ANTES de editar.



## Regras de uso

1. **Antes de implantar um item de "A FAZER":** procure o ID (`L-xx`) no código (`grep -rn "L-xx" D:\recapd-ambientes`).

   Achou = alguém já fez: NÃO faça de novo; confira e mova para "JÁ FEITO".

2. **Implantou?** Ponha `# L-xx` no comentário do código, mova a linha para "JÁ FEITO" com data, arquivo/função, como

   desliga (config/env) e como testou. Item só vai pra "JÁ FEITO" testado num longo real (ou em teste A/B ligado).

3. **Reprovou?** Mova para "DESCARTADO" com o motivo. Não volta.

4. **Achado novo da engenharia reversa** (ANALISE.md de um vídeo novo, PADROES_COMUNS.md refeito): antes de acrescentar,

   confira as 3 listas. Já está em qualquer uma = NÃO acrescente; no máximo some o vídeo como mais uma evidência.

5. Fechar a resposta com: "Longos: X feitos, Y descartados, Z deixados (motivo)".



Fontes dos achados: `referencias\<id>\ANALISE.md` (um por vídeo) e `referencias\PADROES_COMUNS.md` (o que se repete);

números em `D:\hipercool-materiais\tarefas complexas para fable 5.1\ENGENHARIA_REVERSA (parceiros - o que da views)\ER_07_LONGOS_PRIORIDADE.md`.



---



## A FAZER (ordem = impacto esperado; evidência = vídeos que fazem)



| ID | Mudança | Evidência | Onde provavelmente entra | Cuidado |

|---|---|---|---|---|

| L-05 | **Abrir no choque (in media res)**: os primeiros 5–30 s mostram o pior/maior momento (traição, morte, desastre) e só depois "mas pra entender, vamos voltar…" | bXe7 2,1 mi, 5FDt, hJaA (avião aos 50 s), yKfg, 4wuf, XNKC | roteiro do longo (anime_script / resumo inicial do anime-pipeline) | Nosso Animescomia levou ~2 min explicando orfanato |

| L-06 | **Primeiro minuto acelerado**: 25–35 trocas de imagem no 1º min, cair para ~12–15/min depois do min 4 | 1TXD 51, 6d2a 42, SNhb 38, yKfg 33, bXe7 25 | montagem do longo (troca de painel/zoom) | ggQm (nosso) ficou em 44/min o vídeo inteiro: acelerar só o começo |

| L-07 | **Pequena vitória antes dos 8 min** (o prota cala/humilha um arrogante) — escolher o corte inicial pra isso aparecer cedo | bXe7 (5 min), hJaA (10 min), yKfg (2 min), 1TXD | escolha do trecho / ordem dos capítulos | Não inventar fato que não está na obra |

| L-08 | **Capa tríade**: prota no centro com cara fria + mulher reagindo + vilão/figurantes humilhados ao fundo; texto ≤ 3 palavras | 6 dos que estouraram | capa_ia_anime (REFAZER / capas_ab) | Capa B/C já existem (L-F4); aqui é a composição |

| L-09 | **Narrador "parça"** comentando como amigo ("nosso garoto caiu no golpe", "as red flags viraram verdes") em vez de leitura neutra | hJaA ("our boy"), Manhwa Fresh em geral | prompt do roteiro do longo | Sem palavrão (postar_longos reprova) |

| L-10 | **Card "nome da obra no comentário fixado 👇" aos ~5 min** (3 s, sem pausar a fala) | PADROES_COMUNS item 8 | overlay do longo + comentário fixado (extras_ledger) | Comentário fixado só depois da verificação do canal |

| L-11 | **Tags**: medir e copiar o padrão de tags dos parceiros (hoje sem análise) | — (falta medir: meta.json tem "tags") | seo_generator | Fazer a análise antes de mudar |

| L-12 | **Sufixo de maratona no título** ("- Completo", "(1-3)") | 1TXD "- Completo", 4wuf "(1-2)" | seo_generator | Só se o vídeo for mesmo completo |





### IMPLANTADO 01/11 noite — esperando o 1º longo real pra conferir (aí vai pra JÁ FEITO)

Pacote do Kaggle atualizado 01/11 ~23h20: o 1º longo renderizado depois disso já sai com tudo abaixo.

| ID | O que entrou | Onde | Desliga | Como conferir no 1º longo |

|---|---|---|---|---|

| L-05 | Resumo de abertura começa no CHOQUE (1ª frase = o pior momento, sem explicação) e só depois apresenta o prota; fecha com "pra entender, a gente precisa voltar" | recapd `bin\anime-pipeline.py` `_resumo_longo` (prompt; cache novo `resumo_v2.json`) | config/longo.json `resumo.ligado=false` | ouvir os primeiros 15 s |

| L-06 | 1º minuto com corte a cada 1,2 s (antes 2 s, só no resumo): resumo + as 13 primeiras frases; depois ritmo normal | recapd `binx_clips.py` (sprint em build_clip_from_video) | `ANIME_SPRINT_RESUMO=0` (A/B `cortes_resumo` segue valendo) | contar trocas no 1º minuto (meta 25-35); teste isolado: 8 trocas em 5 s |

| L-07 | Nos 2 primeiros blocos do roteiro (~6-8 min): se o trecho tem o prota calando/humilhando um arrogante, a IA dá destaque com 2-3 frases de reação; não inventa | recapd `bin\anime_script.py` `_VITORIA_CEDO` | — (prompt v14) | ver se há vitória antes dos 8 min |

| L-09 | Tom de "parça" no roteiro do longo: "o nosso garoto", "e lá vai ele cair no golpe", >= 2 por trecho, sem palavrão | recapd `bin\anime_script.py` `_COMENTARIO_NARRADOR` (prompt v14) | — | ouvir 2-3 trechos |

| L-10 | Cartão "NOME DA OBRA NO COMENTÁRIO FIXADO" com alfinete e seta, 3,2 s, na 1ª frase depois dos 5 min (só longo deitado > 8 min) | recapd `bin\anime_cartoes.py` `c_obra_fixado` | `ANIME_CARTAO_OBRA=0` | ver em ~5:00 (quadro de teste: tmp_logs\cartoes_teste\obra.jpg) |

| L-12 | Título: mantém "(1-2)" quando o vídeo-fonte é parte; "- Completo" só com `ANIME_LONGO_COMPLETO=1` (quem sabe que é a obra inteira liga) | recapd `bin\seo_generator.py` | não passar a env | testado nos 3 casos (parte / completo / normal) |



## JÁ FEITO (não refazer; para mexer, leia o código e o motivo)



| ID | Mudança | Onde está | Desliga | Data / quem |

|---|---|---|---|---|

| L-F1 | **Título em tríade** humilhado → virada → vingança/quem desprezava implora | recapd `bin\seo_generator.py` (bloco "engenharia reversa de 14 recaps") | `ANIME_TITULO_TRIADE=0`; A/B pelo render.json `ab.titulo_triade` | 30/10, Fable |

| L-F2 | **Gancho do narrador a cada ~15 min** provocando o que vem | recapd `bin\anime-pipeline.py` `_ganchos_longo` | config\longo.json `ganchos.ligado` | 30/10, Fable |

| L-F3 | **Capítulo "Comente PARTE 2" perto dos 22 min** | recapd `bin\anime-pipeline.py` (capítulos, `parte2`) | config\longo.json `capitulos.parte2=false` | 30/10, Fable |

| L-F4b | **Capas A/B/C v2 (dona 01/11)**: ficha da obra pela visão (protagonista fiel, mulheres da história, BIQUÍNI-FANTASIA temático de cada uma, Maria com fantasia da obra, cenas A/B/C) + pose do hipercool (2ª ref, descrita como situação inocente: "tropeçou e caiu por cima dele") + ref de corpo peituda (3ª ref); A fiel, B sensual cômica, C batalha+humilhação | recapd `bin\capa_longo_v2.py` (+ `_ficha_v2` em capa_ia_anime: capa_melhorada/capas_ab); poses em `D:\hipercool-materiais\capas_poses_ref` | `CAPA_LONGO_V2=0` | 01/11 |

| L-F4 | **3 capas A/B/C** (A = capa do parceiro melhorada com o MESMO protagonista; B sensual + etiqueta; C pose + rótulos) e teste A/B no Studio; vencedor lido em 14 dias | recapd `bin\capa_ia_anime.py`; postador `extras_ledger.py` (`checar_ab`) | `CAPA_AB=0` | 30–31/10 |

| L-F5 | **Sem pedido de like/inscrição na abertura** (intro de voz humana só sem CTA) | recapd `colab\cliente.py` (intros, `_INTRO_CTA`) | `INTRO_COM_CTA=1` | 01/11 |



- **11/11 memes do resumo (dona, Medieval 9: "memes horríveis no começo; o 1º com piiiii que deixa surdo; não dá

  prioridade aos memes novos")**: o resumo sorteava entre os 86 memes velhos de nome aleatório (o filtro de proibidos é

  pelo NOME e não pegava). (1) `bin/memes_apito.py` mede o SOM (apito contínuo / volume estourado) -> 1 achado

  (video_com_zoomXCGHK, 1000 Hz por 4,8 s, -4 dBFS) movido pra `memes_img/_fora_apito` e listado em

  `memes_proibidos_som.json` (fx_detect.meme_proibido lê; MEMES_FILTRO_SOM=0 desliga). (2) os 20 memes NOVOS em

  português (`memes_para_escolher_5l8a`, parados desde 01/11) agora são o sorteio do resumo

  (`assets/memes_img/memes_novos`, anime-pipeline._memes_resumo; MEMES_NOVOS_RESUMO=0 volta). Kaggle baixa os dois a

  cada pedido (kaggle_trabalhador, nas 4 centrais). Vale para os longos renderizados daqui pra frente.



## DESCARTADO (não sugerir de novo)



| Ideia | Por quê |

|---|---|

| "Muito corte o vídeo inteiro" | O campeão (2,1 mi) tem 6,9 cortes/min; o que conta é só o 1º minuto (virou L-06) |

| Palavras/min do Manhwa Fresh como meta | Vídeos em inglês; o Whisper traduziu — número não vale. Referência pt: Porão ~180/min, Mike ~198/min |

| CTA nos 10 primeiros segundos (lista "COPIAR" de algumas análises) | As análises se contradizem; os que estouram não pedem nada nos 10–15 primeiros min (virou L-F5) |

| Tela dividida antes/depois na capa | Pendente de decisão da dona (ER_07, D-capa): a checagem de capa reprova "dividida" hoje |



## A FAZER (10/11, chat dos longos) — longo que não cabe na sessão do Kaggle

- Achado: o roteiro tem 1 frase a cada 6,6 s do original (cliente.preparar / anime_preparo_longo); render ~24 s/frase.

  HZRT (206 min) = 1952 frases ≈ 13 h > 11,5 h da sessão → refeito 3x desde 08/11, nunca terminou.

- Feito: cliente.MAX_DUR_S 210→170 min (LONGO_MAX_MIN); HZRT e VgQU (207 min) em "ignorar" do alimentador; VgQU tirado

  da fila (→ _fila_parados/..._longo_demais).

- IMPLANTADO 13/11 (agente online, SEM teste em longo real — conferir no 1º fonte de 3 h+): **(a) teto de frases**. recapd `bin\anime_script.py` `alvo_com_teto` + `rewrite_longo_com_tempo` (vale pros 4 que chamam: anime_preparo_longo, cliente, anime_auto, anime_worker_daemon). Alvo acima de 1500 vira 1500 e, SÓ nesse caso, o pedido de cada trecho ganha "NO MÁXIMO N frases" (junta transição/repetição, mantém os momentos fortes); longo normal segue sem trava (dona 04/11). Desliga: `LONGO_TETO_FRASES=0`. Teste sem IA: `bin\teste_teto_frases_longo.py` (206 min -> 49 trechos × 33 = 1617 frases ≈ 10,8 h a 24 s/frase; antes 1854). Falta: refazer o pacote do Kaggle; depois de 1 longo de 3 h+ terminar, dá pra subir `LONGO_MAX_MIN` (170) e tirar HZRT/VgQU do "ignorar".

- Falta (mexer com o Kaggle calmo): (a) [feito acima; o resto desta linha é o histórico] teto de frases no roteiro (~1500) em anime_preparo_longo/rewrite_longo_com_tempo,

  em vez de 1 frase/6,6 s fixo — aí fonte de 3 h+ volta a caber; (b) kaggle_trabalhador: depois do roteiro gerado na GPU,

  conferir _cabe de novo e soltar se não couber (hoje só confere antes, com o pior caso 7 h).



## 12/11 tarde — JÁ FEITO (chat dos longos)

- **Fila na ordem da dona** (Medieval 13→14→15, depois outras línguas, depois os mais vistos): `colab\furar_fila.py <vid> <ordem>` (pid `20261027_<ordem>_<vid>`). As partes 14/15 estavam em `alimentar_estado.json "ignorar"` desde 10/11 (nunca seriam feitas).

- **Conta de longo no Kaggle**: todas estavam com papel "curto"; `kaggle_pool.json` inovaremanhwaverse9 = "longo" (bkp_1112_papel).

- **Longo em outra língua saía em português**: o roteiro traduzido subia como `roteiro_<lang>.txt` (o Kaggle só lê `roteiro.txt` e refazia em pt) e ia com a abertura de voz real (pt). `longo_idiomas.py` grava em `idioma_<lang>\roteiro.txt`; `cliente.enviar` não manda intro com "idioma" (LONGO_IDIOMA_SEM_INTRO=0 volta).

- **Tema escola/bullying** (dona: "por que bloquear se deu muito bom?"): entra quando o original tem ESCOLA_MIN_VIEWS (1 mi) ou mais — `cliente.py alimentar` e `garimpar_fontes.py` (GARIMPO_ESCOLA=0 barra tudo). Vale no próximo reinício do alimentador.

- **Disco segurava 6 longos prontos** (postar_longos "sem espaço"): `faxina_disco.py` agora apaga `postador\cache_reuso` > 2 dias e o `video_1080p.mp4` de Short já postado com original no Drive (FAXINA_1080_POSTADOS=0). 7,3 -> 16,5 GB. ATENÇÃO: `historias-em-frames\workspace` NÃO tem 25 GB (é junção pros assets, contada em dobro pelo PowerShell) — não apagar. Medir de verdade: `D:\tmp\tamanho_real_d.py`.



## 12/11 18h40 — JÁ FEITO

- **Replicar os campeões** (dona: "procure obras assim — sistema de gastar dinheiro com mulheres, sistema de dinheiro, ex-namorada humilhada"): `colab\garimpar_parecidos.py` — 5 temas (ex_arrependida e sistema_dinheiro -> InventoReact, onde "His Ex Girlfriend..." fez 516 views; loot_box, medieval_tecnologia e renasce_rico -> Fio da Meada, onde Medieval/Fist King/Loot Boxes deram 109-380). Até 3 por tema, logo depois da série Medieval na fontes_prioridade.json, com `canal_destino`. O `cliente.py` passa o canal_destino do pedido para o nuvem.json ("canal"), e o postar_longos só posta nele (mesmo mecanismo do longo traduzido). CANAL_DESTINO_PARECIDO=0 / GARIMPAR_PARECIDOS=0 desligam.

- **Achado (não consertável por nós):** a Fio da Meada tem LIMITE DIÁRIO de envios do YouTube por estar SEM TELEFONE VERIFICADO (youtube_http.log 07/11 e 12/11 03:53). É por isso que ela trava de tempos em tempos. Verificar o telefone do canal = só a dona.

- **Painel do Kaggle mente quando o proxy cai:** a central marcou a parte 13 como "1%/começando", mas o progresso_inovaremanhwaverse8.json no Drive mostra 92% (acabamento). A GPU segue; só a central perdeu contato (proxy Webshare). Ver o progresso no Drive antes de mexer.



## 12/11 19h20 — JÁ FEITO (dona: "o Short nos dispositivos não pode parar; pode fazer os internacionais, até nos celulares")

- **Filas pt cheias não param mais PC2/desktop**: `ocioso._escolher_pc2` faz o Short do canal pt de menor fila + as versões nas LÍNGUAS com fila abaixo do alvo (até LINGUAS_POR_SHORT=2, as de fila mais curta); `controlador._cortes` conta "língua faltando" como trabalho. `pc2_parceiro.ps1` e `pc3_parceiro.ps1` aceitam `-Idiomas` (antes fixo `ANIME_IDIOMAS=nenhum`). LINGUAS_QUANDO_CHEIO=0 desliga. Celulares: as versões em língua passam pelo mesmo xfade -> rodízio de celulares (celulares.CELULARES_RODIZIO).

- PENDENTE: mandar o `pc3_parceiro.ps1` novo pro desktop (`instalar_pc3.py`) quando ele estiver livre (19:00 estava num Short). O do PC2 vai sozinho pelo sincronizar_bin.

- **Aviso falso "conta de like deslogada" no x200ma**: `vitrine.JS_GOSTEI_PAGINA` — 401/403 com a página logada (ytcfg LOGGED_IN, avatar, LOGIN_INFO ou SAPISID) volta `recusado_logado_<n>` e não vira aviso. O like em si ainda é recusado pelo YouTube (investigar o porquê).

- **Painel de uso das máquinas**: o Flow não contava (PC2+desktop 59 imagens/h aparecendo 0%) — `uso_maquinas._flow_recente` (USO_CONTA_FLOW=0 desliga).

- **InventoReact**: 3 parecidos com o campeão furando a fila do Kaggle (KQMPGyt6PxA 1,2 mi, e2nIzNGXvmA 1,5 mi, 8fM6Ay7OJho 965 mil), com canal_destino = InventoReact (`furar_fila.py` leva o canal_destino da fontes_prioridade).

- 12/11 19h50 — **Não soltar pedido "travado" sem olhar o progresso no Drive**: a central diz "1%/começando" e "sem resposta há > 3 h" quando o proxy Webshare da conta cai, mas a GPU segue (parte 13 95%, parte 14 92% às 19:48 pelo progresso_<conta>.json). Soltar aí = renderizar de novo do zero.

- 12/11 20h — **Medieval 15 para 13/11 07:00** (PostarMedieval15; dona: 13 e 14 públicas já, 15 de manhã). **Fio da Meada JÁ tem telefone verificado** (dona conferiu): a mensagem "sem telefone verificado" do youtube_web_poster era palpite errado — o limite é por volume (11 envios em 24 h em 11-12/11). Mensagem corrigida. **Like do x200ma**: diagnóstico real = Chrome do telão SÓ com os cookies __Secure-3P* e ytcfg LOGGED_IN=false (sessão do YouTube caiu nesse perfil, embora o Google mostre a conta) -> aviso de "deslogada" era VERDADEIRO; `--logar-telao x200ma` aberto pra dona entrar. **Reserva de Shorts no Drive**: `hipercool-materiais\comum\reserva_shorts_drive.py` (7 dias x por_dia por canal ficam no PC, o resto sobe com conferência; "dispensada" = pronto, fica na fila) + `parceiro_diario` traz do Drive na vez de postar (RESERVA_VOLTA_DO_DRIVE=0 desliga). 287 Shorts / 8,1 GB.

- 12/11 21h — **Falas reais e falas de personagem (dona: "as falas reais às vezes acabam bruscamente no meio de uma palavra; mesmo assim são muito boas — ampliar as falas reais e as falas dos personagens sozinhos fora do narrador o máximo possível")**:

  - corte do banco (`colab\falas_narradores.py`, roda na hermes-staging): frase inteira até FALA_MAX_S 10 s (era 6); frase maior vai da palavra do padrão até a PRÓXIMA PAUSA real (vírgula/ponto ou silêncio >= 0,25 s), nunca "±2 palavras" (FALA_CORTE_PAUSA=0 volta); fim com 0,30 s de folga (era 0,08, comia a última sílaba; FALA_FOLGA_FIM) e fade de saída 0,18 s. Testado com frase sintética: antes "e ele nem, ligou, salve galera", agora "salve galera que coisa mais doida que aconteceu hoje aqui no canal". Bancos dos 7 narradores sendo refeitos em 12/11 21h (banco antigo em dados/<voz>/banco.bkp_1112).

  - no vídeo (`bin\anime_segments.py`): fala real 1 a cada 60 s (era 150; FALAS_REAIS_A_CADA) e aceita até 10,5 s (era 6,5).

  - falas de personagem (`config\longo.json` personagens.a_cada_s 25 -> 15; `anime-pipeline` PERSONAGEM_DIST_MIN 3 frases, era 5; pedido à IA prefere diálogo/resposta entre personagens, 3-18 palavras). Pacote do Kaggle atualizado (montar_pacote --codigo).

- 12/11 23h45 — **Série da dona não espera mais a cota de Short**: a Medieval 13 ficou pronta 22h10 e não subiu porque o Fio da Meada bateu o limite diário de envios com SHORTS (agendados pra 2 dias depois) entre 00h e 02h. `parceiro_diario._serie_esperando`: com parte da série pronta e não postada, o Short do Fio da Meada não sobe (SERIE_RESERVA_ENVIO=0 desliga). O limite libera 13/11 03:53 e a PostarMedieval13 posta na hora.

- 13/11 00h45 — relatório: caixa do pesquisador contava o texto das instruções como pendente (sempre 1 a mais); conta só os blocos '## [ ] PENDENTE'. Casos 'falhou' da vigilância eram VUUH (aplicada 00:04) e verificação de telefone do Manhwa Noturno (só a dona).

- 13/11 01h45 — reserva da série confirmada no log real: 01:25 'Fio da Meada: parte da série da dona pronta esperando este canal — Short não sobe'. Nenhum envio no Fio da Meada desde 12/11 03:53 -> o limite diário volta às 03:53 com a série na frente.

- 13/11 02h45 — 5 longos postados entre 01:43 e 02:43 (madrugada, fora do Fio da Meada); reserva da série segue segurando o Fio da Meada (nenhum envio desde 12/11 03:53).

- 13/11 03h45 — vietnamita (PDPOK) saiu da fila do Kaggle; inglês (dLd0) renderizando; parecido 'POOR Guy 90 BILLION' (InventoReact) começou. Central: linha proxy-rnprmtfo-11 (curto) assumindo longo porque as linhas de longo estão sem conta.

- 13/11 04h45 — Medieval 13 e 14 SUBINDO desde 04:32/04:33 (títulos 'PARTE 13 |' e 'PARTE 14 |'). Travou 03:53-04:22 por DISCO (vídeo 5,6 GB + folga 6 GB); faxina + reserva_shorts_drive (249 Shorts, 6,8 GB) resolveu. A fazer: a ReservaShortsDrive diária (04:50) roda tarde demais pra série da madrugada — rodar também antes de cada parte da série.

- 13/11 05h45 — 🔥 Medieval 13 (AVVxD9iZAxU) e 14 (ozdALiyIDVY) NO AR e PÚBLICAS (05:25/05:28); parte 8 (AjgJG8HAfLk) antes, na ordem da série. Cortes do longo passaram a esperar a série (postar_longos cortes: SERIE_RESERVA_ENVIO).

- 13/11 06h45 — GarimparParecidos (06:20) rodou sozinho: +8 parecidos (18 no total, 12 pro InventoReact); garimpo diário (05:40) também — lista de prioridade 37 -> 60. POOR Guy 90 BILLION (InventoReact) 95%.

- 13/11 08h — Medieval 15 presa 1 h no intervalo VIP do Fio da Meada ('último longo há 2 h'): parte da série com ficha pronta agora fura o intervalo (postar_longos._serie_publicar_ja_pronta; SERIE_FURA_INTERVALO=0 desliga). Disparada às 08:0x. GitHub: repositório público Emersonjosielmrx/sistema-videos (salvar_github.py; sem senhas/chaves; dona dispensou tirar e-mails/IPs — GITHUB_LIMPEZA_EXTRA=1 tira).

- 13/11 09h — GitHub PÚBLICO no ar: github.com/Emersonjosielmrx/sistema-videos (12.588 arquivos, 29 MB compactado; o GitHub barrou 1ª tentativa por chave do Asaas -> filtro ampliado: Asaas/Stripe/Mercado Pago/AWS/SendGrid/Facebook/chave privada). Medieval 15 PARADA a pedido da dona (9/13/14 rendendo pouco: abertura no meio da história + partes de 97-100 min). Parte 13 (AVVx): CTR 9,3% e 17 min de média com 4 views — cedo demais.



## 13/11 11h40 — DECISÕES DA DONA (não mexer sem ela pedir)

- **Senha do proxy Webshare NÃO será trocada** (dona 13/11): ela ficou exposta no GitHub público (veo/beta/_test_proxy.py) junto com o token do bot do Telegram (fluxos n8n) e cookies de sessão do YouTube (video-fila/REVISAO_MELHORIAS.md). A dona decidiu não trocar. O salvar_github.py já filtra os três a partir dos próximos envios.

- **Repositório github.com/Emersonjosielmrx/sistema-videos continua PÚBLICO** (dona 13/11), pra o agente online trabalhar nele. E-mails e IPs vão junto (GITHUB_LIMPEZA_EXTRA=0, decisão dela); senhas e chaves saem sempre. Sincronizar: o que o agente online muda lá precisa ser trazido pro D: antes do próximo envio automático (SalvarGithub 03:30), senão a cópia daqui sobrescreve.

- **Acer e x200ma deixam de ser telão** (dona 13/11): só produção (Flow/Veo/render).

- **Moto G20 entra na medição** de uso das máquinas.

- **Parte 15 do Medieval: dividir em 2 vídeos** usando os celulares/PC (não ocupar o Kaggle, que fica pros próximos).

- **"16 longos hoje" no relatório era errado**: 5 longos + 11 cortes (Shorts tirados do longo). Relatório vai separar.

- 13/11 14h25 — Kaggle: 2035 e 2037 já tinham chave; 2038 chave nova salva (saída rnprmtfo-17, papel curto, verificada=false) nas 4 centrais; 2039: Google BLOQUEOU a conta ao abrir pela saída rnprmtfo-18 — dona deixou pra depois (cofre google=bloqueada_13nov; não abrir sem ela).
- 13/11 14h45 — disco 6,4 -> 16,1 GB (cópias temporárias da parte 15 no D:\tmp, 10 GB, já no Drive + reserva de Shorts). Parte 10 do Medieval presa desde 13:18 por 'sem espaço' — disparada de novo.
- 13/11 15h20 — **Rodada de conferência (dona: "vá fazendo ao longo das rodadas conferências no melhorador, vigia e pesquisador")**: melhorador central aprovou só com prova e vetou 4; nos longos está em sombra (14 < 20 medidos). Melhorador dos Cortes reescreveu `bin\cortes_ajustes.json` (regras_roteiro: gênero do personagem, sem texto de prompt, ortografia, gancho sem saudação, só o visível) — conferidas, todas certas. Vigilância: 0 consertos gravados após 00h, 1 caso real (Lei e Lucro, resolvido pelo outro chat). Pesquisador: 1 reprovado (boato de regra do YPP 02/2027 sem fonte oficial), 1 vazio.
- **Capas dos longos**: `colab\auditar_capas_longos.py` confere a capa A no ar de cada longo (protagonista, mulher, sem roupa, sem letras/divisão/escura/foto) com a mesma visão das capas; reprovada volta pra fila de refazer (dona autorizou trocar). Rodando.
- **Reserva da série** (`parceiro_diario._serie_esperando`): só segura Short do Fio da Meada quando faltam 2 envios pro limite de 24 h (SERIE_LIMITE_24H=7, SERIE_GUARDA_ENVIOS=2), não o dia todo.
- **x200ma parado**: Chrome de conta esquecido aberto 20+ min deixava a máquina "ocupada". `maquina_remota.maquina_livre` fecha Chrome aberto > 25 min sem login (CHROME_ESQUECIDO_MIN=0 desliga). Acer/x200ma fora do telão (`vitrine.TELOES` vazio; VITRINE_NOTEBOOKS=1 volta). Moto G20 na medição (`uso_maquinas.MAQS`) — está fora do ar (ssh 8022 timeout).
- **CenaReact e Curiosidades "0 views"**: leitura da API parada nos dois desde 11:58 (views total idêntico), não é queda real.
- **Instagram "Reel não confirmou"**: erro 1357001 "Entre para continuar" = cookie de sessão do HTTP vencido; o postador já pega cookie fresco do Chrome e a próxima vai (canalhistoriacomia postou às 15:12 depois disso). **TikTok deslogado**: 3dfabricadeautomacoesia — o Google do perfil também caiu, aí o relogin automático não consegue (precisa da dona).
- 13/11 15h40 — **Capas apontadas pela dona nas prints (14)**: `colab\refazer_capas_dona_1113.py` pôs 13 na fila de refazer (capa velha em `.dona_1113`); a parte 9 (cIB4X-Q9MIk) ficou — a dona disse que é a única com o protagonista parecido. 4 longos antigos sem pasta no PC (N_O4ooMZ3do, 2dCDDjWiV2M, AznoavGpczU, dr6rZ8aeXXg) ganharam pasta só com a ficha (`videos laterais\refazer_capa_<vid>`).
  - **Capa A sem o protagonista agora reprova** (`capa_ia_anime.capa_melhorada`, CAPA_EXIGE_HEROI=0 desliga) — antes só faltar mulher reprovava.
  - **Rótulos sobrepostos** (PARTE 14: "INIMIGO" por cima de "EXÉRCITO DO PROTAGONISTA"): sem lugar livre o rótulo caía num canto fixo sem checar; agora tenta menor (70%/50%) e, se não couber, fica de fora (`_rotulos`, CAPA_ROTULO_SEM_SOBREPOR=0 volta). Testado (`D:\tmp\teste_rotulos.py`).
- 13/11 15h50 — parte 10 do Medieval (6,4 GB) subindo desde 15:05 (envio em andamento, só lento); a 1ª tentativa às 14:48 falhou por 'nao_aprovado' (aprovação gravada em seguida). 18 capas na fila de refazer, 6 vagas gerando desde 15:33. Kaggle 0 contas (emersonjosiel2034 terminou a sessão 15:11; central sem conta livre — 2035/2037/2038 precisam do telefone verificado).
- 13/11 17h40 — **Kaggle 2038 rodando Shorts** (dona: "já mandei o token, é pra estar rodando"): `verificada=true` no pool (local + hermes-prod, backup `kaggle_pool.json.bkp_*_2038`); a central mediu 30 h livres pela saída dela (rnprmtfo-17, exclusiva) e lançou às 16:40. Medição direta por fora da central foi barrada pelo portão — certo.
- **Parte 10 do Medieval no ar**: https://youtu.be/Hm4neTPGM_c (16:15).
- **Parte 16 não entrava na fila**: a ficha da 2ª metade da 15 (`na_nuvem\oLBasz5Hp16_16_...`) ficou sem `render.json` na divisão -> `_modelo_novo` falso -> "0 longos esperando". Copiei o render.json da 15; volta na fila (próxima do Fio da Meada).
- **Partes 4 e 6 reprovadas por palavrão** ("fodas"/"merdas" numa fala da narração) — a série tinha buraco. Novo `colab\bipar_palavrao.py <ficha>`: baixa do Drive, acha a palavra com faster_whisper, bipa só ela (vídeo sem re-encode), confere de novo, sobe no lugar (original vira `video_com_palavrao.mp4`) e tira dos reprovados; `postar_longos._tem_palavrao` aceita `SEM_PALAVRAO.txt` na ficha. BIPAR_SO_TESTE=1 não sobe.
- **Capas**: parte 14 (ozdALiyIDVY) saiu ainda com rótulo sobreposto — gerada por processo que começou 15:33, antes da correção (15:35); voltou pra fila. Auditor: das 5 marcadas "mulher vestida", só COp7UBa6CPo estava fora (só o herói) — na fila; as outras 4 conferidas por mim, ok. "letras/logo" do auditor = a palavra-gancho da própria capa (falso).
- 13/11 17h50 — **Relatório mostra a série TODA** (`relatorio_ronda.sec_serie`): além de 13/14/15, uma linha com cada parte (✅ / ⏳ esperando / ❌ reprovada (bipe pendente) / 🔁 bipada) e "Faltam no ar". RELATORIO_SERIE_TODA=0 tira. Hoje: faltam 4, 6, 16.
- **Continuação achada**: o parceiro postou a (16-17) (jcQ9GQz5CG4, 2 h, 58 mil views). A "parte 2" não falta — a nossa 1 é a (1-2) dele. Entrou em `fontes_prioridade.json` (serie medieval) e na frente do Kaggle (`furar_fila.py jcQ9GQz5CG4 3`). Vai virar 17+18 (divisão igual à 15).
- 13/11 18h45 — **Download do longo travado sem fim**: a parte 16 parou em 1,99/2,00 GB e o rclone ficou 10+ min parado sem errar (a rodada esperava pra sempre). `postar_longos._publicar`: rclone com `--timeout 2m --contimeout 60s --retries 5 --low-level-retries 20` e teto LONGO_DOWNLOAD_MAX_MIN=90 (LONGO_DOWNLOAD_TIMEOUT=0 volta o antigo). Compilado; rclone travado morto, a 16 tenta de novo assim que a rodada acabar.
- **bipar_palavrao.py mais rápido**: whisper nas 3 h inteiras passou de 1 h em CPU. Agora estima onde está a fala do palavrão (pipeline.log: audio_NNN + soma das durações dos clipes) e transcreve só ±10 min (BIPAR_JANELA_S). Parte 4 ~11 min, parte 6 ~47 min.
- 13/11 19h27 — **PARTE 16 do Medieval NO AR: https://youtu.be/L0-6t7qjKho** (destravada: render.json + download com timeout).
- **Parte 4 bipada** ("foda" em 14:52; conferido, sumiu) — vídeo novo no Drive, original como video_com_palavrao.mp4, saiu dos reprovados; os cortes dela não pegam o trecho. Entra na próxima rodada.
- **bipar_palavrao, parte 6**: a 1ª janela (soma dos clipes) não achou — a soma ignora memes/transições e o "wrote audio_N" do edge-tts paralelo pode ser da fala vizinha. Agora a janela vai da soma até o tempo do clipe no ORIGINAL (segments/landscape corte@), com folga. Parte 4 continua coberta (892 s).
- 13/11 19h45 — **Público após o envio com nova tentativa** (`postar_longos`, PUBLICO_TENTATIVAS=3, 3 min entre elas): a parte 16 subiu 19:27 e o "público JÁ" deu "página de edição não abriu" (vídeo processando); na mão 10 min depois = ok. Agora tenta 3x sozinho. Parte 16 pública conferida.
- Pesquisador LONGOS: 1 pendente (sons em alta dos Shorts) — avaliado: o motor reprovou tudo e não é da linha. STI saiu do Tailscale 19:28 no meio de um render (offline, sem ping) — precisa ligar/tomada.
- 13/11 20h45 — **Parte 4 voltou a "reprovada" sozinha**: o bipar tirou dos reprovados, mas a rodada que já rodava gravou o estado antigo por cima (`_gravar_estado` faz união e nunca tira). Agora ficha com `SEM_PALAVRAO.txt` sai dos reprovados em toda gravação. 4 e 6 na fila (a 4 sai primeiro: menor parte da série). Parte 6 bipada ("merdas" em 57:04, conferido).
- **Disco D: 6,9 -> 24 GB livres** (dona: "ganhar espaço"): bipe terminou (15 GB do D:\tmp\bipar), cache regenerável dos perfis Chrome (`logins-google\limpar_espaco.py`, 1,5 GB; cookies/logins intactos, perfis abertos pulados), cópias do Drive no `postador\cache_reuso` com mais de 1 dia (1,2 GB; original fica no Drive), D:\tmp\fatia (testes de 11-12/11). Perfis do cofre: só 5 contas "morto" (41 MB) — mantidos. hipercool-videos NÃO é antigo (o venv dele roda ~10 tarefas) e historias-em-frames ainda é lido por catalogo/edge_tts — ficam.
- 13/11 21h45 — **Disco: mais 5,3 GB pro Drive** (dona: João Lucas, shorts_hipercool, PRODUTOS_PARA_VER, capas_proximo_G1) — `rclone copy` + `check` 0 diferenças antes de esvaziar; pasta vazia fica no lugar. Documentado em `D:\hipercool-materiais\MOVIDOS_PRO_DRIVE.md` (links). Atalho do PRODUTOS_PARA_VER no Desktop.
- Kaggle voltou: 6 contas rodando (2038, inovaremanhwaverse8/9, emersonverse7, aulasrevolution...) — a (16-17) do Medieval começou. Parte 4 subindo desde 21:22 (QA: 16 s de imagem parada em 49:47 — posta, regra da dona).
- 13/11 22h45 — **Limite diário pela janela real de 24 h** (`politica.marcar_limite_diario`, LIMITE_JANELA_REAL=0 desliga; LIMITE_ENVIOS_24H=7): a parte 4 do Medieval subiu 2,9 GB e o YouTube recusou (Fio da Meada: 11 envios em 24 h, 7 deles Shorts agendados das 04:52–05:28). A espera fixa de 24 h deixava a série parada até 22:28 de amanhã; agora termina quando o envio que libera vaga sai da janela (+30 min): **14/11 05:41**. Ainda 1 tentativa por espera (regra da dona 22/10). Recalculado e gravado (backup `D:\tmp\limite_diario.bak_1113`).
- **HP Pavilion dv6 no sistema** (máquina "hp", `ssh hp`): render pelo celulares.py testado OK (8x mais lento que o PC1, fica depois dos S20), medição, maquina_remota ("lento") e login em lote (3 janelas) pra dona.
- 14/11 00h — **Relatório em TABELAS e mais completo** (dona: "relatório cada vez com menos coisas; Shorts gerados; tudo em tabela, sempre no mesmo padrão"): Números = 1 tabela (longos e CORTES separados — antes "19 longos" misturava; Shorts GERADOS por idioma/canal; Shorts subidos; TikTok; Instagram; capas; renders; Flow) com colunas Desde a última / Hoje / **Ontem** (`estado\relatorio_totais.json`, RELATORIO_ONTEM=0 tira); "Longos que mais rendem" = top 10 com views/dia e link; Kaggle e Máquinas em tabela (o PC1 sumia: corte fixo de 9 linhas e agora são 10 máquinas); Shorts por canal em tabela; Medieval foi pro fim (dona: "pode parar de focar no Medieval").
- **Foco nos mais vistos**: `fontes_prioridade.json` reordenado por views, série Medieval pro fim (backup `D:\tmp\fontes_prioridade.bak_1113_2310`). Nossos dados: tema ex/dinheiro/vingança = 112 views/dia, 7x o Medieval — documentado em `FORMATOS_LONGOS_NOVOS.md` com os formatos parecidos pra testar.
- **Vigilância sem alarme falso de capa** (`vigilancia.med_capas_longos`, VIGIA_AB_TODOS=1 volta): canal com recursos negados ou capa_depois não é cobrado de B/C — 25 falsos em 13/11, agora 0.
- **HP: login das banidas no Kaggle** (decisão da dona 13/11 23h, `login_em_lote._conta_kaggle`, LOGIN_BANIDAS_KAGGLE=0 volta): 42 contas liberadas, 14 vivas no Kaggle continuam proibidas em casa. 23/65 logadas até 00:11.
- 14/11 00h45 — **Conferência das capas pedidas pela dona (20)**: 18 trocadas e conferidas. opyASXVvTc4 (Animescomia, era o meme de gatinho) falhou 12x na rodada ("página de edição não abriu") — apliquei à mão, OK. **Parte 14 (ozdALiyIDVY) ainda saía com "INIMIGO" por cima de "EXÉRCITO DO PROTAGONISTA"**: os rótulos do original apontam pros NAVIOS do parceiro, a visão não acha navio na capa nova e os dois caíam no topo. Agora rótulo sem o objeto na capa nova fica de fora (`capa_ia_anime._compor`, CAPA_ROTULO_SO_COM_ALVO=0 volta) — testado. Parte 14 e parte 11 (BVAIHMQWDIo, setas pra nada) de volta na fila.
- 14/11 01h40 — **Asus Eee PC no sistema** (`ssh asus`): só navegador — render testado não aguentou (>10 min vs 24 s do PC1). **Enxugamento das máquinas** (dona: "tirar tudo que dá do sistema, permanente, só Chrome/Wi-Fi/render"): parte do usuário FEITA no STI/Acer/x200ma/Asus (Bluetooth, impressão, atualizações do Mint, Evolution, gvfs, tracker...), reversível; parte do sistema (cups, bluetooth, avahi, ModemManager, apt-daily...) precisa da senha — comando pronto. Tudo em `D:\video-fila\ENXUGAR_MAQUINAS.md`.
- **Relatório: seção dos geradores** (dona: "novos geradores de vídeo e imagem em avaliação; vamos corrigir quando der erro na rotação de contas"): Gemini sem navegador (imagem/vídeo) x Flow — OK desde a última/hoje, falhas, mediana de tempo, % de acerto, motivo dos erros (cota/timeout/cookie) e contas com erro.
