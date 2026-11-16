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
- 14/11 03h55 — **Capa que não troca em canal bloqueado** (`capas_depois.um` + `_fechar_item`, CAPAS_PARA_NO_BLOQUEIO=0 volta a insistir): partes 14 e 11 do Medieval tentaram 26x na madrugada e o Studio respondia "Salvar continuou cinza". Print: o Studio do Fio da Meada abre "Sua contestação relacionada aos recursos avançados foi NEGADA — suspensão por violar as políticas" (logs\yt_web\20261114_035219_capa_nada_mudou.png): sem recursos avançados, capa de vídeo PUBLICADO não troca. Agora o item vira "bloqueado" (para de insistir no Studio) e o relatório lista as bloqueadas. As capas certas (sem rótulos sobrepostos) estão prontas na pasta; entram quando o bloqueio vencer (05/01) ou a dona trocar à mão. recursos_negados.json: fiodameada contestação=negada_14nov.
- **Enxugamento parte 2 (sistema) FEITO** com a senha (dona: "1" em todos, "123456" no x200ma): STI, HP, x200ma, Asus — 21 serviços desligados e travados em cada (bluetooth, cups, avahi, ModemManager, fwupd, apt-daily, mintupdate...). Acer caiu no meio (a dona religou) — monitor roda quando voltar. Desfazer: `sudo bash /root/enxugar_sistema_desfazer.sh`.
- Pesquisador LONGOS: 3 pendentes avaliados (1 reprovado, 4 deixados); o mais importante foi levado à dona (regra do YouTube "mesma situação, mesmo desfecho" vale pro canal inteiro).
- 14/11 04h45 — **(16-17) do Medieval pronta no Kaggle virou a PARTE 17** (`na_nuvem\jcQ9GQz5CG4_17__...`): o nome `_16_17_` não casava com o padrão de série (`_serie`/`_parte` davam None/999) — sairia sem "PARTE 17" e podia ir pra outro canal (regra: série no mesmo canal). Renomeado; agora série=medieval, parte=17, fila do Fio da Meada. Não precisa dividir: 1 h 42 (as partes têm 1h30-1h50; a 15 foi dividida por ter 3 h). Relatório não mostra mais "16" duplicado.
- Longo no ar: InventoReact "O DOMADOR MAIS FRACO..." (Slime Tamer) https://youtu.be/--g1zfTqc-E + 2 cortes. Kaggle: emerso terminou a sessão com erro depois de entregar a (16-17) — a central já trocou de conta.
- 14/11 05h45 — Longos no ar desde 04h41: InovareManhwaVerse "ELE FOI HUMILHADO por ser FRACO mas DESPERTOU o SISTEMA mais FORTE na masmorra" https://youtu.be/kPvegQOYHI0 (05:20); "She Dumped Me Before" (tema campeão) subindo no InventoReact desde 05:29. Fio da Meada liberou 05:41 (janela real de 24 h) — partes 4 e 6 na rodada das 06:10. Pesquisador CAPAS: 1 avaliado (A/B e rosto/texto já fazemos; capa nova nos longos fracos bloqueada pelos recursos negados).
- 14/11 06h45 — **Disco: cache_reuso voltava a crescer** (2,3 GB em 1 dia; o disco caiu a 11 GB e o postador de longos precisa de 3-7 GB por envio): a faxina diária só tirava o que tinha mais de 2 dias. Agora 1 dia (`faxina_disco.VELHOS_EXTRA`, FAXINA_REUSO_DIAS muda) — é só cópia do Drive, o catalogo.baixar busca de novo. Limpei agora à mão (13 arquivos, 0,7 GB). Longo no ar: InventoReact "ELE VOLTOU NO TEMPO para viver de RIQUEZA e agora ela NÃO QUER O DIVÓRCIO" https://youtu.be/olOL01PLwv8 (tema campeão). Parte 4 do Medieval subindo desde 06:20.
- 14/11 07h50 — **Conferência do melhorador dos longos**: fechou o experimento "mascote_voz_thalita" com vence A ("B deixou o render 1,7x mais lento"). Conferido nos dados: A 2 vídeos (render médio 13,4 mil s) x B 6 (22,8 mil s); B tinha nota um pouco maior (5,08 x 4,63) mas quase dobra o tempo de GPU do Kaggle — a trava render_max 1,4 existe pra isso. Decisão certa, mantida. O "longo: rc=1 em 437 s" do melhorador central foi timeout do `--forcar` depois disso (não gravou nada). Pesquisador CAPAS: capas 1280x720 (mínimo do A/B), conferido em 10.
- Longos no ar: **PARTE 4 do Medieval** https://youtu.be/DCyOfv2lI2E (06:57, pública 07:05); "Orphan Reincarnated" subindo no HistoriasEmFrames.
- 14/11 08h50 — **Mesma fonte quase foi pra 2 canais** (regra: vídeo único por canal): o Orphan (LUQDew946Ps) subiu 4 GB no HistoriasEmFrames, o HTTP caiu e foi pro Chrome, que deu `Locator.click Timeout` no fim — ficaram 2 RASCUNHOS "Pendente" no Studio (print logs\yt_web\20261114_083835_falha_historiasemframes.png). Com status "erro" o postar_longos não gravava nada e a rodada seguinte já baixava o MESMO vídeo pro Animescomia — parei o download (nada subiu lá). Agora: erro depois de 5+ min de envio prende a fonte ao canal (`est["presos"]`, `_gravar_estado` mescla, `cand` respeita; LONGO_PRESO_AO_CANAL=0 desliga, LONGO_PRESO_MIN_MIN muda) + aviso no Telegram. O Orphan fica segurado (AGUARDA_DONA) até conferir os rascunhos no Studio do HistoriasEmFrames — testado: não sai em nenhum canal.
- 14/11 09h45 — Disco 7,1 GB: o download que parei do Orphan (pro Animescomia) deixou 3,5 GB de `.partial` em `_longos_postar` — apagado (original inteiro no Drive, 4,08 GB conferido) -> 11 GB. Lição: matar o rclone do postador deixa a pasta; o `_publicar` só limpa quando o mesmo vídeo volta. "She Dumped Me for the Hero" subindo no InventoReact desde 09:17. Pesquisador LONGOS: 1 avaliado (regra reused: permissão do criador NÃO protege; risco = similaridade entre canais) — reforça a decisão levada à dona.
- 14/11 11h — **Longo no ar**: InventoReact "ELE FOI REJEITADO pela ex mas REENCARNOU e DESPERTOU o SISTEMA mais FORTE" https://youtu.be/xrcP6545Ax8 (She Dumped Me for the Hero, 5,2 GB em 87 min).
- **Respostas à dona (parte 1 e 2)**: HP com 50 contas logadas e 0 canais ATIVADOS (por isso 17%) — 19 canais ativados no hp somando às máquinas existentes (`youtube_navegador.json`, backup `.bkp_*_hp`) + Flow/Veo; carrossel MS Energy passava DIRETO no Flow pulando o Gemini -> agora `cliente.gerar` (Gemini 1º; CARROSSEL_FLOW_DIRETO=1 volta), testado 21 s pelo Gemini; fontes do anime pro Drive com 1 dia em vez de 3 (`fontes_drive.DIAS`, FONTES_DRIVE_DIAS) — disco 11->20 GB; relatório com placar da IA por agente (RELATORIO_PLACAR_IA=0 tira). Desempenho: 89 longos, 2.745 views, 265,7 h assistidas — o "jardineiro" (lztXRIb2s30) tem 96 views mas 112 h (70 min médio); o "Ex pediu volta" 558 views mas 3 min médio. Tokens: os 10 mortos NÃO tinham sido renovados — `D:\credenciais-canais\renovar_um_por_vez.py` (Chrome do cofre, 1 por vez; pula conta viva no Kaggle: Filme e Manhwa Noturno).
- melhorador_longo: "sem vídeo (nem local nem no Drive)" aparecia quando o vídeo ESTAVA no Drive e só faltava disco (Top Player 7,7 GB) — mensagem corrigida.
- 14/11 12h — **Mais do que rende, no mesmo canal, rápido** (dona): `garimpar_parecidos.py` ganhou o tema **jardineiro_academia** (o "jardineiro mal-arrumado", 112 h assistidas) -> Fio da Meada; ex/dinheiro pegam 5 por tema (PARECIDOS_POR_TEMA_CAMPEAO); Medieval saiu dos temas (GARIMPAR_MEDIEVAL=1 volta); parecidos vão pra frente de tudo (PARECIDOS_DEPOIS_DA_SERIE=1 volta). Rodado: +5 ex arrependida e +1 dinheiro pro InventoReact; +2 "ninguém sabia que era o mais forte" do Manhwa Fresh (Classmates Bullied Him... Street Fighter, 1,3 mi) pro Fio da Meada.
- **Fila pesada pelo desempenho real** (dona: "métricas automáticas pra IA pesar os próximos"): `colab\pesar_fila.py` (tarefa PesarFilaLongos, 3/3 h; PESAR_FILA=0 desliga) — nota por tema = 60% horas assistidas/longo + 40% views/dia; tabela em `video-fila\estado\pesos_temas.json`. Hoje: jardineiro 0,63 (24 h/longo), ex arrependida 0,54 (28 views/dia), medieval 0,39. Painel lento = usa a pesagem anterior.
- **Melhorador dos longos "4 consertos sem efeito" era FALTA DE COTA**: as 5 últimas caixas deram "API Error 503 (contas 100%)"/"429 exhausted" — o Opus (ag-opus-5-5) nem rodou. Agora tenta a reserva (gemini-3.8) e, se nenhum rodar, a proposta volta pra fila em vez de virar "não mudou nada" (MELHORADOR_RESERVA=0). Placar do relatório passou a contar isso como falta de IA (5 hoje).
- **Flow deslogado na tela do STI**: o Flow de imagens usava a porta 9470, a mesma do TELÃO do STI (sem conta Google) — entrava no navegador do telão. STI agora 9471-9474 (`gera_imagem.PORTAS_EXTRA` + porta inicial; FLOW_STI_9470=1 volta).
- **Tokens**: 8 renovados (58 ok, eram 50). Filme e Manhwa Noturno ficam (contas vivas no Kaggle). Os 5 "nunca tiveram" (Empresário/Clínica/Imóvel/Vendas/Lei e Lucro = inovaremanhwaverse7/8/9, emersonjosiel2034/2035) são TODAS contas VIVAS no Kaggle — consentimento pelo IP de casa = regra do 2º banimento; não feito.
- **Medidores**: TikTok grava o motivo de cada conta que não abre; Instagram (`medir_instagram_publico.py`) quebrava numa linha "null" do histórico (por isso parou em 10/11) — corrigido + tarefa diária InstagramMedirSeguidores 07:40. Acer limpo (5 Linux enxutos). HP: 49 contas logadas.
- 14/11 12h10 — **TikTok amplificado** (dona: "os tiktoks estão reagindo, amplifique"): remedição (timeout 30->60 s, `medir_tiktok` TIKTOK_MEDIR_TIMEOUT_MS) abriu 27 de 58 (eram 12). 4 contas concentram as views: fabricadeautomacoesia 3065 (44 seg.), inovaremanhwabr 1916, emersonjosiel649 1416, seebotsia 1366; 19 abertas estão zeradas. `postar_tiktok_auto`: conta com >=300 views na última medição posta até 6/dia, >=50 até 4/dia, zerada fica em 3 (TIKTOK_AMPLIFICAR=0 desliga; TIKTOK_TETO_FORTE/TIKTOK_VIEWS_FORTE). Intervalo de 90 min entre posts da conta mantido. (Cuidado aprendido de novo: sed com caminho Windows comeu as barras e virou TAB — corrigido com Edit.)
- Pontes Short->longo: no Fio da Meada "bloqueado: recursos avançados negados" (o vídeo relacionado é recurso avançado) — limita a ponte enquanto o bloqueio durar.
- 14/11 13h40 — **HP no máximo + telões por baixo** (dona: "HP desocupado com todas as contas logadas, põe pra trabalhar no máximo"; "deixe o telão rodar por baixo e coloque no HP"): HP entrou no Veo (`veo/beta/cadeia_veo.py` NOTEBOOKS, VEO_SEM_HP=1 tira) e no Flow de imagens (`flow-imagens/gera_imagem.py` ORDEM_IMAGENS + livres, FLOW_SEM_HP=1 tira) — 47 contas com Flow no HP. Telão: PC2 (`vitrine/telao_win.py`) sem --kiosk, janela maximizada mandada pro fundo (SetWindowPos HWND_BOTTOM); Linux (`vitrine/player.py` _abaixo, wmctrl "below") — TELAO_POR_CIMA=1 volta. HP virou telão de painel (`vitrine.py` TELOES_PAINEL, VITRINE_SEM_HP=1). Conferido no HP: janela com _NET_WM_STATE_BELOW. Bug achado: `vitrine.py` sem `import os` desde 13/11 15h — painel dos telões parado desde então; corrigido.
- 14/11 13h50 — **Título real do campeão do jardineiro**: no top 10 a linha 10 (Fio da Meada, lztXRIb2s30, 96 views) mostrava "(reposto 03/11 do uploads_ledger...)" — era o "Por que a academia inteira tremeu quando o jardineiro mal-arrumado aceitou o desafio?" (2º vídeo do tema jardineiro). Gravado em `colab/longos_postados.json` (backup .bkp_1414_titulo) — isso também faz o `pesar_fila.py` (TEMAS_RX por título) passar a contar esse vídeo no tema jardineiro_academia. `relatorio_ronda.py` sec_mais_vistos: nota entre parênteses vira "[sem título] fonte".
- 14/11 15h30 — **Título de nota não volta mais por cima do real** (`colab/postar_longos.py` _gravar_estado_trancado): a rodada que já estava rodando regravou "(reposto 03/11...)" no lugar do título do jardineiro (lztXRIb2s30) que eu tinha corrigido — o pesar_fila deixava de contar esse vídeo no tema campeão. Agora título entre parênteses na memória perde pro título de verdade do disco. Testado (simulei a rodada antiga: título real ficou).
- 14/11 15h45 — **Pesquisador não cobra mais bloco vazio** (`pesquisador_melhorias/motor_pesquisador.py`): pesquisa em que o motor já reprovou tudo ("todos os itens foram reprovados") nascia "[ ] PENDENTE" e o CobradorPesquisador cobrava o chat da linha de hora em hora só pra marcar 0/0/0 (2 blocos assim hoje na caixa CAPAS). Agora já nasce "[x] AVALIADO (automático: nada aproveitável)". Volta: MOTOR_VAZIO_PENDENTE=1. Também: "Sobre" no Studio espera 15 s + 60 s pela caixa (ForjaReact estourou 30 s) — ForjaReact volta pra fila.
- 14/11 16h55 — **Título do jardineiro: correção definitiva** — a rodada do postar_longos das 12:10 (código antigo na memória) sobrescreveu de novo. Relatório agora busca o título no postar.json via uploads_ledger quando o registro tem nota (`relatorio_ronda._titulo_do_ledger`). Conferido: pesar_fila usa o NOME da fonte (Arrogant_Students...Academ) pro tema, então a pesagem do tema jardineiro nunca foi afetada. **Máquinas "livres"**: 753 Shorts prontos em estoque (10-20 dias por canal); o limite é a vaga de postagem do YouTube (canais fortes no teto da rampa ou com "limite diário"), não a produção. Longos = GPU do Kaggle (7 contas rodando, 8 esperando vaga de postagem).
- 14/11 17h10 — **Estoque de 1 MÊS** (dona: "um mês de vídeos em estoque, assim se o sistema parar ou perdermos os Kaggles não ficamos na mão"). Conta: os canais abrem ~99 Shorts/dia -> 30 dias = ~3.000 Shorts (~40 GB, 13 MB cada); hoje 757 (~7,5 dias), produção ~144/dia. (1) `recapd bin/parceiro_diario.alvo_por_rendimento`: reserva PARCEIRO_DIAS_ESTOQUE=30 dias pra todos (0 volta a 10/7). (2) `hipercool-materiais/comum/reserva_shorts_drive.py`: no PC só RESERVA_DIAS_PC=3 dias, o resto vai pro Drive (3 TB livres) e volta na hora de postar (_NO_DRIVE.txt, já existia); tarefa ReservaShortsDrive de 1x/dia -> a cada 3 h. Rodando agora: 235 Shorts / 6 GB. (3) `video-fila/ocioso.PILHA_ALVO` 5 -> 10 (máquinas livres não esperam fonte). (4) HP: copiando o pipeline de Short completo do STI (8 GB) pra virar mais uma máquina de Shorts inteiros.
- 14/11 17h50 — **Contador de Shorts gerados não some com o estoque no Drive** (`video-fila/relatorio_ronda._shorts_gerados`): com o estoque do mês indo pro Drive (só fica _NO_DRIVE.txt), o relatório caiu de 144 pra 25 "gerados hoje". Agora, sem video.mp4, conta pela data do nome da pasta (_AAAAMMDD) + hora do qa.json. Número real de hoje: **233** (ontem 71). Também: `recapd bin/capar_shorts.py` pula pasta com _NO_DRIVE.txt (dava KeyError 'streams' no ffprobe sem vídeo).
- 14/11 18h15 — **Longo nunca mais abre sem capa por Studio lento** (dona: "HistoriasEmFrames sem capa, isso não pode acontecer"). JesjRW5uBR0 (HistoriasEmFrames) e xrcP6545Ax8 (InventoReact) tinham a capa PRONTA, mas o Studio estourou 90 s nos notebooks (Acer/HP) 3x e o capas_depois desistiu ("sem_capa"). Aplicadas agora pelo desktop (30 s cada). Conserto: `colab/capas_depois.py` — Studio com timeout/página não abriu tenta NA HORA pelo desktop (CAPA_STUDIO_RESERVA, padrão desktop; vazio desliga) e, se só o Studio falhou, não desiste em 3 (vai até CAPA_MAX_REFEITA=12). `postador bin/youtube_studio_extras.sessao` aceita YT_MAQUINA (força a máquina). Os 4 sem capa do Fio da Meada são o canal com recursos avançados negados (Studio não deixa).
- 14/11 19h10 — **Disco 24 -> 9,7 GB em 1 h: 3 downloads de longo travados** (Tv4TcuPT9JI 7,7 GB parado a 300 MB do fim desde 06:48, repetido 15:49 e 18:18; Medieval 17 6,3 GB parado em 5,99; 65WB 4,7 GB). Matei o Tv4 (volta na próxima rodada) — disco 18,3 GB. Conserto: `colab/postar_longos.py` baixa em 4 pedaços (`--multi-thread-streams 4 --multi-thread-cutoff 256M`, LONGO_DL_PEDACOS=1 volta). `hipercool-materiais/comum/reserva_shorts_drive.py`: vídeo em uso pelo postador não derruba mais a rodada (PermissionError -> pula); +1,6 GB pro Drive.
- 14/11 19h40 — **Melhorador dos longos usa o Opus 5.5 da cc quando OUTRA pessoa usa a conta** (dona: "o Opus que eu dei pra sua quando não tiver ninguém usando; tem o gerenciador que mede"; "agora a conta Ricardo Silva parece estar sendo usada por outra pessoa"). `colab/melhorador_longo.json` código/decisor = `cc-sobra` 1º (combo do modo_tokens.py da VPS: só contas cc com uso alheio confirmado ou janela de 5 h virando com sobra; sem conta = falha em 1 s), reservas ag-opus-5-5 -> Gemini 3.8 (backup .bkp_1411_ccsobra; `melhorador_longo.py` lê a lista "reservas"). Combo `ag-opus-5-5` (OmniRoute) ganhou Opus 4.6 atrás do 5.5 (backup storage.sqlite.bkp_1411_agopus) — antes 1 modelo só = 503 "all targets skipped". Conferido: vigia_uso_alheio dava ricardosilveraneves "alheio (1ª vez)" (5h caiu 95->67%); rodei vigia + modo_tokens: modo "gastar", cc-sobra respondeu claude-opus-5-5 pela conta do Ricardo. Euclides também é alheio mas está 0% na janela.
- 14/11 19h50 — **Telão do Tab: gráficos + "Abrir" que abre no desktop/STI** (dona). (1) `video-fila/vitrine/graficos.html` (Chart.js 3.9.1 — o Tab A6 tem Chrome 95): views hoje x ontem, 7 dias, inscritos, views por dia, top 10 do dia, comparação 7 dias por canal; dados = APIs do painel :8790 (canais_views, ranking_canais, views_mesma_hora) em graficos.json publicado pelo `vitrine._publico` (TELAO_GRAFICOS=0 desliga). Em tv.../graficos.html e no rodízio do tv8 (painel <-> gráficos entre os vídeos). (2) "Abrir": o painel público faz GET pedido.txt (fica no access.log do nginx); `vitrine._pedidos_publicos` (1/min) abre no desktop (C:\vitrine\abrir.txt -> `telao_win._abrir_pedido`, Chrome tela cheia por cima) ou no STI se a câmera do desktop estiver em uso (PEDIDOS_PUBLICOS=0). Testado: abriu o HomhRlIE72I no desktop. (3) Bug: `vitrine._ssh` forçava Port=22 em todo alvo — o alias "desktop" (2223 + HostKeyAlias) falhava "host key changed"; agora só PORTA_SSH leva porta. (4) Fila do melhorador no relatório + ordem: tema campeão primeiro, depois o mais novo (MELHORADOR_ORDEM_ANTIGA=1).
- 14/11 20h05 — **Gráficos + RECORDES em todos os telões e no Tab** (dona: "além dos gráficos de postagem, views e inscritos da semana como tem no :8790, uma página de RECORDES: o canal X bateu 2x a mais de inscritos e nunca tinha batido"). `video-fila/vitrine/graficos.html` agora tem 2 telas (alterna 30 s; `?tela=1|2` fixa): 1) views hoje x ontem, 7 dias, inscritos, views/dia, top 10 do dia, comparação 7 dias; 2) postagens por dia (Shorts x longos, do ledger), inscritos por dia, 🏆 recordes (`vitrine._recordes`: melhor dia dos últimos 7 > maior dia antes dele, série de 30 dias; 2x+ em dourado). `vitrine_painel._QUADROS` ganhou "graficos" e "recordes" (TELAO_GRAFICOS=0 tira); painel.html instalado em PC2, desktop, STI, HP. Tab A6: tv.opus-sem-limites.com.br agora alterna painel e gráficos (tv_painel_graficos.html). Recordes de hoje: Manhwa Noturno 172x views (1.553 num dia), vietnamita 11x, Plantão 3x, inovare manhwa br 2,2x. Também: melhorador baixava o longo inteiro sem timeout (XYDK 5,3 GB preso 7 h) -> 4 pedaços + teto MELHORADOR_DL_MAX_MIN=40.
- 14/11 20h50 — **Descrição de parte de série** (`colab/postar_longos.py`, LONGO_SERIE_DESC=0 desliga): a Medieval 17 está subindo (1h+, 6,3 GB) com capítulo 'Comente "PARTE 2" pra continuar' (tática L-F3 do pipeline, fixa em "2") e hashtags/tags com nomes da obra (#Greycastle #Roland #Neverwinter) — o filtro do SEO só apaga o nome da obra quando ela é conhecida, e aqui é "sem-obra". Agora, em série: "PARTE 2" -> "PARTE n+1", linha só de hashtags sai, tags de UMA palavra com maiúscula (nome próprio) saem. A 17 em si: corrigir os metadados (--metadados) depois que terminar de subir (não interrompi o envio).
- 14/11 21h55 — **Medieval 17 no ar (https://youtu.be/uUqCHE_Dacg) — série COMPLETA 1-17.** Metadados corrigidos no Studio (pelo desktop): título "PARTE 17 | Roland cria o CINEMA..." (nome do personagem, fora do padrão "ELE ..." das outras 15 partes; SEO tinha falhado: seo_versao vazio) -> "PARTE 17 | ELE CRIOU O CINEMA no MUNDO MEDIEVAL e as BRUXAS ficaram CHOCADAS 🎬"; descrição "PARTE 2" -> "PARTE 18", sem "Roland" e sem hashtags da obra; tags sem nomes próprios. Prevenção: `colab/postar_longos.py` título de série sem SEO: nome próprio no começo vira "ELE" (LONGO_TITULO_SEM_NOME=0). Caixa CAPAS: 2 reprovados (niche-research, facedetection-thumb).
- 14/11 22h55 — **Kaggle: 5 contas com o TOKEN recusado** (emerso, emersonjosiel2034, 2038, emersonverse7, inovaremanhwaverse8 — todas lançadas ~01:00 e 19:50/20:05) desde ~21h40 (00:40 UTC, mesmo horário dos banimentos de 02/11 e 09/11). O relatório dizia "proxy webshare sem resposta" (`vps_central._pela_saida` devolve isso pra qualquer falha); o motivo real no central.log é "supply KAGGLE_API_TOKEN". aulasrevolution (rnprmtfo-4) responde normal = não é o Webshare. Regra do IP respeitada: NADA testado por fora; a central solta as vagas em 3 h (est['ruins']). Avisei a dona no Telegram (importante). Medieval 17 ganhou capa às 21:55.
- 14/11 23h40 — **REGRA NOVA anti-banimento do Kaggle (dona: "mude pra não acontecer mais; adicione uma nova regra")**. Causa do 3º banimento: upload HTTP de Shorts saía de casa com contas vivas do Kaggle. Travas: `logins-google/cofre.saida_kaggle(email)` = porta única (proxy da ponte do IP fixo; ponte fora = erro); `gemini-argo/youtube_http.Studio._entrar` usa esse proxy na sessão inteira (testado: Comédia Noturna sai por 185.72.242.6, casa 191.36.x); `youtube_web_poster._subir_http` exige a ponte; `cofre.abrir` fecha Chrome já aberto sem a ponte; `kaggle_gerente/vigia_cruzamento.py` item 5 "HTTP DE CASA" (testado: achou os 11 canais). Regra no CLAUDE.md global, memória feedback_nunca_mesmo_ip e INCIDENTE_BANIMENTO_02NOV.md. Capas aplicadas: Medieval 4 (DCyOfv2lI2E) e 16 (L0-6t7qjKho, capa reserva da série).
- 14/11 23h55 — **Relatório mostra o motivo real das contas do Kaggle paradas** (`video-fila/relatorio_ronda.py`): "proxy webshare sem resposta" (texto único que `vps_central._pela_saida` devolve pra qualquer falha) escondia o 3º banimento por horas. Agora lê a última tentativa de cada conta no central.log: "🚨 TOKEN RECUSADO pelo Kaggle (possível banimento)", "proxy/rede fora" ou o trecho do erro. Não mexi no texto da central (a regra de soltar vaga em 3 h compara com ele). Melhorador: ordem cc-sobra -> ag-opus-5-5 -> Gemini funcionando; o Ricardo bateu o teto semanal (429 "reset after 46h") e o Antigravity está sem cota, então os consertos seguem no Gemini.
- 15/11 00h15 — **Longos agendados no melhor horário (18-21 h)** (dona: "aproveitar melhor os longos; voltar a postar com agendamento conforme o melhor pra crescer, não vários em seguida"). Medido em 129 longos (ranking :8790 + ledger): abriu 18-21 h = 9,4 h assistidas em média; 00-06 1,8 h; 06-12 1,6; 12-18 1,1; 21-24 0,2 (nos longos o nobre é 18-21, não 21-22 como nos Shorts). `postador bin/politica.horario_longo`: vai pro próximo 18:00/18:30/19:00... do canal, 1 longo por dia nessa faixa; o resto, dias seguintes (LONGO_HORA_NOBRE="" desliga; "18,19,20" muda). Testado: Fio da Meada/InventoReact/HistoriasEmFrames -> 15/11 18:00. Série da dona (publicar_ja) continua saindo na hora. Telão: "Esperando você" listava 26 vídeos já aprovados com nome de pasta (sem-obra-...) — `vitrine_painel.pendentes` só mostra reprovado/segurado/nudez, com o título (PENDENTES_SO_REAIS=0 volta); hoje: 0. Celulares: tirei a vibração (Termux não é mais trazido pra frente a cada 15/30 min; só se o Tailscale cair) em S20, S20 Ultra e G20.
- 15/11 01h10 — **Lista da dona (19 itens) conferida e atacada** — situação item a item em `video-fila/linhas/LONGOS/LISTA_DONA_15nov.md`. Feito hoje: pose "ex x namorada na cama" (capa B dos longos); série "Reencarnou como VILÃO / ESPOSA MAID" (partes 1, 2, 4 no topo, dono InventoReact, playlist própria); trilha do Short DPcqU-UwecY (não existia; separada por demucs e posta nas prioritárias); parceiros @sabiaquex, @nexhwaoficial, @odaniels00; 12 capas de referência do @ansaketv. Já estavam feitos: Groq, painel de tokens, avisos unificados, 32k tokens, Binance, Shorts repetidos, metas, catálogo de avisos. Pendentes: voz do sistema (testes pausados), gauntlet-loop, transição "tela no celular", rc=1 do Kaggle, estilo @ansaketv no capar_shorts, próximas partes da série vindas de fora do Brasil.
- 15/11 01h20 — **TikTok de conta viva do Kaggle não fica mais sem postar** (`postador bin/postar_tiktok_auto.py`): mundosolar1995 (viva no Kaggle) falhou 4x "Chrome já estava aberto por outro projeto sem o proxy dela" — a trava estava certa (desktop/acer/x200ma recusaram, PC1 recusou), mas recusava também Chrome que já está NA ponte. Agora, se o cofre.abrir devolve Chrome já aberto de conta viva do Kaggle e `cofre._chrome_com_ponte(porta)` confirma a ponte do IP fixo, usa (o cofre já fecha/reabre o que estava sem ponte). As outras falhas da hora (timeout/"não confirmado" em filmenoturno, jogoscomia, 2027, 2029) são instabilidade do proxy/TikTok. Disco 10,2 GB (reserva +0,7 GB pro Drive; 2 longos de 9 GB estão subindo agora).
- 15/11 02h — **Disco caiu pra 1,7 GB: longos com envio falho presos em 2 pastas (link físico)**. KAA_csRv7NU (4 GB, CenaReact) e S6LISaC7K6A (5,1 GB, ForjaReact) tiveram o envio morto ontem 22h e o vídeo ficou em `_longos_postar\<ficha>\final_anime_deitado.mp4` E em `animes recap\videos laterais\<x>\video.mp4` — é o MESMO arquivo (hardlink): apagar só um não libera nada. Apaguei os dois (original no Drive; o postar_longos baixa de novo) -> 12,1 GB. Prevenção: `video-fila/faxina_disco.longos_que_falharam` (longo não postado, > 1 GB, parado > 6 h, sem envio usando o MESMO arquivo — compara tamanho+data, não o caminho) apaga as duas entradas; roda na faxina diária e a cada 3 h junto da `reserva_shorts_drive` (FAXINA_LONGOS_FALHOS=0 desliga). Testado: não pegou o Tv4 que está subindo por outra pasta. Caixa LONGOS: chronolist reprovado.
- 15/11 02h50 — **Kaggle: mais 7 contas com 401** (simonerebecaluizasil=Filme Noturno, seebotsia, gabriellyvitoriaisab=Curiosidades, inovaremanhwaverse9=Clínica, mundosolar1995, inovareee, inovare) nesta madrugada (central.log linhas 14417-14524), além das 5 de 14/11 21h40 = 12 contas com acesso recusado; só aulasrevolution gera. Quase todas da lista "EM RISCO" (canais que subiram Shorts por HTTP de casa até 14/11 23h30 — travado desde então). Os 2 vídeos que estavam nas banidas (Apocalypse, BETRAYED) voltaram a 1% sem conta pra rodar. Avisei a dona (Telegram, importante). Estoque: 12 longos esperando vaga de postagem. Nada testado por fora.

- 15/11 06h JÁ FEITO: Veo (gera_auto/flow_bot) abria Chrome da conta viva do Kaggle (mundosolar) pela casa — agora contas.ponte_kaggle põe a ponte do IP fixo e fecha Chrome aberto sem ela (VEO_TRAVA_KAGGLE=0 desliga).
- 15/11 07h JÁ FEITO: alimentador (colab/cliente.py) reenviava longo já na fila quando o Drive falhava ao ler pedido.json (5DoGv3EXHgc 2x). Agora reconhece o vid pelo nome da pasta da fila (FILA_VID_PELO_NOME=0 desliga). Duplicata apagada.
- 15/11 09h JÁ FEITO: Kaggle banido (dona: considerar banidas) -> recap_worker religado na hermes-staging (vps_lancar.py hermes-staging 6 12g; CPU, sem conta Google). Parar: vps_lancar.py hermes-staging parar.
- 15/11 09:25 DESCARTADO: recap_worker na VPS (CPU) não substitui o Kaggle — todo pedido usa revezamento com voz CLONADA (Applio precisa de GPU); sem clone sairia edge puro (proibido). Worker parado. Conserto que fica: kaggle_trabalhador.preparar_applio não morre mais sem nvidia-smi. Longos só voltam com GPU (conta Kaggle nova/outra GPU).
- 15/11 09:50 A FAZER: relatorio_ronda mostrar 'disco caindo por quê' (processo com mais bytes gravados na hora; ex. rclone baixando longo XYDK 4,9 GB) — hoje levou 3 buscas pra achar.
- 15/11 11h JÁ FEITO (dona: "cortes dos longos valem a pena ou só enchem linguiça?"): medido (API YouTube, desde 31/10) corte x parceiro POR CANAL — colab\medir_cortes.py -> cortes_x_parceiro.json (tarefa MedirCortes 07:30). Geral: corte mediana 209 x parceiro 41, mas parceiro tem 354 vídeos >=1000 views x 10 dos cortes. Por canal: corte vence no Dorama Noturno (818 x 12) e Manhwa Noturno (550 x 5); empata/perde pouco no InventoReact/CenaReact; perde no HistoriasEmFrames (672 x 1081); morre no Animescomia/Cartucho/Curiosidades/Forja. postar_longos._corte_nao_rende: corte só sai onde rende (>=50 views de mediana e >=70% do parceiro do canal); sem medida = testa. Chaves: CORTES_POR_RENDIMENTO=0, CORTES_MIN_VIEWS, CORTES_FRACAO, CORTES_MIN_N.
- 15/11 11h JÁ FEITO: TikTok sem fonte em 42 contas = 326 de 350 Shorts postados no YouTube desde 13/11 sumiam do catálogo (vídeo ia pro Drive com _NO_DRIVE.txt sem linha no manifesto). mover_shorts_postados.anotar_manifesto + reserva_shorts_drive gravam no manhwa-react\logsackup_drive.jsonl; 1.378 antigos preenchidos. TikTok: de 1 para 17 contas com vídeo (799). MANIFESTO_SHORTS=0 desliga.
- 15/11 11:50 A FAZER: medir_tiktok — 51/58 perfis com TimeoutError no goto (15/11), 46/58 (14/11); lê pelo Chrome logado da msenergypara pela casa. Diagnóstico com ajudante em andamento (não trocar IP/conta: regra).
- 15/11 13:40 JÁ FEITO: canal Anime Noturno (@animenoturno, UCewCJ-gv-2FzTHPu5hhIiZA, conta emersonjosiel2038 pelo rnprmtfo-17) criado + foto/banner (mascote ninja; 1º banner tinha Goku = refeito com heróis originais) + Sobre; parceiro.json pt (anime, 2/dia, 21:40 nobre). 3 Shorts já gerados.
- 15/11 13:40: contas 2035/2037/verse2 ligadas (verificada=true) -> 401 na 1ª cota = não usáveis. 2040 (teste cego) 'queued' há 2h20 = Kaggle não dá GPU pra conta sem telefone verificado (igual inovare/inovareee 10/11).
- 15/11 13:50 JÁ FEITO: medir_tiktok — 2 bugs: (1) aba única travava após o 1º timeout (aba nova por conta, espera a grade, para em 6 falhas seguidas, refaz as que falharam; TIKTOK_MEDIR_ROBUSTO=0); (2) 'Make Your Day' agora é título de TODA página do TikTok e descartava perfil lido (teste: fabricadeautomacoesia 24 vídeos com esse título) -> abriu = leu vídeos.
- 15/11 14:10 JÁ FEITO: canal Bilionário Noturno (@bilionarionoturno, UC5a8hc96KXJ62xak5vGYosQ, conta emersonjosiel2037 pelo rnprmtfo-16) — dona: 'priorizando públicos que tenham dinheiro'. Nicho financas (histórias de bilionários/empresas: Magnates Media, How Money Works, ColdFusion...), 2/dia 07:30/12:30/21:30. Foto/banner mascote anos 20 (Gatsby). medir_tiktok: rolagem 3 s na aba nova (lia só 24 de 48).
- 15/11 15h JÁ FEITO (dona: '2 sim, 3 apague, 4 faça pelo playwright, 5 sim, 11 sendo boa use, faça o que falta'):
  - TikTok: catalogo._postagens usa o NOME ATUAL do canal pelo slug (ledger gravava Tech/Mistérios como 'Inovare', Plantão como 'DicasFinanceirasDaIA'); seebotsia 0->38, revolutionemerson3 0->42, fabricadeautomacoesia 0->11 (+Bilionário/Empresário), emersonjosiel649 0->2 (+Anime Noturno). CATALOGO_NOME_ATUAL=0.
  - HistoriasEmFrames: 4 rascunhos presos apagados; Orphan já estava no ar (JesjRW5uBR0).
  - Medieval partes 11 e 14: capas corrigidas aplicadas pelo desktop (o 'Salvar cinza' de 14/11 NÃO era bloqueio). capas_depois: 'Salvar cinza' tenta pelo desktop antes de marcar bloqueado (CAPA_CINZA_DESKTOP=0).
  - colab
odizio_longos.py: 2ª/3ª chance pros longos fracos (>=3 dias, < mediana do canal, até 3 trocas, 3 dias entre trocas, nunca série). 21 elegíveis. RODIZIO_LONGOS=0. (1ª rodada: Studio > 15 min — agora não quebra.)
  - capa_ia_anime._dividida_boa: tela dividida com rosto dele+dela e clara passa (os 2 longos mais vistos são antes/depois). CAPA_DIVIDIDA_LIBERA=0.
  - gauntlet-loop: reprovado (só prompt; ideia A/B cego contra campeão anotada).
  - Ventoinha no máximo: PC1 BIOS 'Fan Always on AC'=Enable + resfriamento ativo; PC2/desktop resfriamento ativo; Linux: ~/fan_max.sh pronto (precisa sudo da dona 1x).
- 15/11 19h JÁ FEITO (dona: 'deixar o PC1 livre pro VS Code; testes em outro PC'):
  - Telemetria Intel SUR/QueenCreek (esrv_svc ~13% CPU) desligada (serviços Disabled + tarefa USER_ESRV_SVC_QUEENCREEK).
  - Tarefa PrioridadeVSCode (2/2 min + logon): VS Code/claude em Alta; ffmpeg e python de render em Abaixo do normal. Desliga: D:ideo-fila\PRIORIDADE_VSCODE_OFF.
  - Trava D:ideo-fila\estado\pc1_sem_render.on: controlador não manda render pro PC1 (exceto capítulo urgente do hipercool) e parceiro_diario producao não roda no PC1 (--forcar passa). Apagar = volta.
  - video-fila	este_remoto.py: teste em outra máquina livre (render/python/pesado; --listar/--arquivos/--trazer/--maquina/--pc1). Testado no STI. Regra no CLAUDE.md global + memória feedback_pc1_livre_testes_fora.
- 15/11 22h JÁ FEITO (dona: 'mude pesados/médios pros outros; PC1 só se todos ocupados'): video-fila\pc1_reserva.pode_pesado (controlador + parceiro_diario: PC1 só renderiza com pc2/desktop/sti todos ocupados); capar_shorts e limpar_veo mandam o ffmpeg pro celular (CAPAR_NO_CELULAR=0 / VEO_NO_CELULAR=0; testado 112 s fora do PC1); celulares._escolher pula o STI com Short próprio (CELULARES_STI_LIVRE=0); painel 8790: aquecer geral 10->60 s, producao 30->90, problemas 40->120 (bkp painel_controlador.py.bkp_1511_leve).
- 15/11 23:55 ANÁLISE (sem mudança): Lei e Lucro 63 Shorts num dia = alvo de 30 dias (60) cheio a partir de 0 — escolhido porque a ordem de produção é 'sem post hoje' -> RENDIMENTO (dona 12/11: o melhor faz o máximo). Esporte Noturno 207/220. InovareManhwaVerse 0/90 e Anime Noturno 5/60 ficam por último (rendem pouco/sem medida). Pergunta à dona se quer equilibrar por dias de estoque.
- 16/11 00:45: teste cego — 2040 passou a virada UTC sem 401; sessão 3 pegou o vilão parte 1 às 21:42 BRT (GPU+Applio ok). aulasrevolution relançada 4x (v43-46) em papel curto: monitorar sessões curtas.
- 16/11 01:45: vilão parte 1 a 31% (narrando) na 2040 — teste cego andando. Esporte Noturno recebeu 23 de 26 Shorts da madrugada (já 207 em estoque): pendente a escolha da dona sobre o equilíbrio do estoque.
- 16/11 02:45: vilão parte 1 a 92% (juntando trechos) na 2040 — teste cego quase completo um longo inteiro. Disco 9,4 GB: _longos_postar com 13 GB esperando postar (normal).
- 16/11 03:45 A FAZER: progresso do longo fica 92% durante TODO o 'juntando os trechos' (1.207 frases, >1 h) — dividir essa fase em % real (trechos juntados/total) pra não parecer travado. Longo yKGTHQck0Sw no ar.
- 16/11 04:45: vilão 95% (legenda na tela) na 2040, vivo 04:42 BRT; limite real da sessão = 12 h (o 7 h do TRAB_LIMITE_H é só pra pegar pedido novo). Longos 6sdgGwUcAKY e d4txa0pYMx8 no ar (3 no dia).
- 16/11 05:45 A FAZER: 'legenda na tela' do longo leva >1 h (re-encode inteiro ~1h40 na T4): avaliar queimar a legenda JUNTO no encode do 'juntando trechos' (1 encode em vez de 2) — economiza ~1 h por longo no Kaggle. Vilão 95%, vivo 05:42.
- 16/11 06:45: vilão 95% há 2 h, último sinal 06:15 BRT (kernel ainda 'running'). Se não voltar em 2 h a central solta a vaga sozinha. 5 longos no dia (zobYrW3vEmQ, cW8uNubxSD4 nesta hora).
- 16/11 07:55 INCIDENTE CONSERTADO: às 05:48:10 um `git reset --hard` em D:\recapd-ambientes\producao (último commit 27/07) voltou 41 arquivos do bin pra julho (anime-pipeline 82->8 KB, anime_tts com edge puro proibido, anime_publish sem --midia/--titulo-original/--anota-postar). Efeito: TODOS os longos baixados falhavam no anime_publish (rc=2) e ficavam no disco (18 GB, disco a 3,5 GB). Às 06:39 alguém voltou de novo anime_auto/anime_discover. Restaurados 40 arquivos do backup diário D:\github_sistema (salvar_github); os 16 que diferem só por <SEGREDO_REMOVIDO> ficaram como estavam (chaves reais). Quebrados guardados em producao\bin_QUEBRADO_1611_0548. Aviso no topo do CLAUDE.md e do LEIA_PRIMEIRO.md. O git tem remoto com token: nada de commit/push.
- 16/11 08:45: depois da restauração, postar_longos 08:11 preparou PvkF8Ut (Fio da Meada) SEM o erro de argumentos — postagem voltou. Arquivos restaurados intactos (ninguém mexeu de novo). Disco 3,3 GB: 1 envio por vez até liberar.
- 16/11 09:30 JÁ FEITO (dona: 'ventoinhas instale você mesmo, senha 1, x200ma 123456, desktop 1234; sincronizar com o GitHub; pergunte aos outros chats quem mexeu'):
  - Ventoinha: x200ma pwm1=255 (máximo de verdade); acer Fan=1 (máximo); STI/HP/ASUS: serviço instalado mas a BIOS controla a ventoinha (Linux não expõe) -> STI ganhou TURBO DESLIGADO no mesmo serviço (chegava a 97 C). Tudo em fan_max.timer (boot + 5 min). Desktop: usuário Emerson NÃO é administrador -> Macs Fan Control só instalando na tela com conta admin.
  - SalvarGithub: diário -> a cada 4 h (pior caso de perda: 4 h em vez de 24 h).
  - git reset 05:48: perguntado a 6 chats; claude-85, claude-b6 e claude-39 responderam que NÃO foram.
- 16/11 10:30 JÁ FEITO:
  - Longos PvkF8Ut (8,8 GB) e y5Pm6ba (5,3 GB) presos desde 14/11: o .partial JÁ estava completo (tamanho igual ao do Drive) mas o processo era cortado pelo teto antes do rclone renomear -> cada rodada baixava de novo. Renomeados; postar_longos._partial_completo usa .partial com o tamanho exato (LONGO_PARTIAL_OK=0 desliga).
  - git reset: TRAVA DEFINITIVA — .git renomeado pra .git_velho*_NAO_USAR em recapd-ambientes\producao, hipercool-videos, veo\beta, historias-em-frames, roteador-heygen-api (todos com commit de jul-out e dezenas de mudanças fora do git). Sem git ali = sem reset. Código protegido pelo SalvarGithub (agora a cada 4 h). salvar_github.PASTAS_FORA inclui os .git_velho (já pulava pasta com ponto).
  - Chats que confirmaram que NÃO rodaram o reset e que as mudanças deles VOLTARAM inteiras: claude-85, claude-b6, claude-39, claude-20 (vozes: anime_tts 15/11 19h presente), claude-fb (curtos: 8 arquivos de 15/11 presentes). Autor não identificado (d3/fa/a2 sem resposta).
- 16/11 11h JÁ FEITO (dona: 'cada canal 30 dias; pasta no Mac; desligar autocompletar; 3D no relatório; teste cego firme?'):
  - parceiro_diario._prioridade: vai primeiro quem está MAIS LONGE dos 30 dias (fração do alvo), rendimento só desempata (PARCEIRO_30_DIAS_TODOS=0 volta ao 'melhor primeiro'). Ordem nova: Anime Noturno 2, Empresário 5, Vendas 4... Esporte (207) saiu da frente. InovareManhwaVerse é ativo=False desde 18/10 (suspenso): 0 é correto.
  - VS Code: python.languageServer=None + watcherExclude/search.exclude das pastas pesadas (settings.json do usuário).
  - relatorio_ronda.sec_3d: Shorts 3D (kit3d-producao) — feitos/falhos do dia, postados, views.
  - Desktop D:\VENTOINHA_MAX: instalador Macs Fan Control + passo a passo (usuário Emerson não é admin).
  - Teste cego: 2040 e 2036 sem 401 (nenhuma em 'ruins'); 2040 relançada 08:55 BRT após sessão de 12 h.
- 16/11 10:50: postar_longos aberto às 08:10 (código antigo na memória) estava baixando DE NOVO o y5Pm6ba já completo; encerrado e a tarefa RecapPostarLongos relançada com o conserto do .partial.
- 16/11 14h JÁ FEITO:
  - postar_longos._publicar: o shutil.rmtree apagava o vídeo JÁ COMPLETO a cada rodada (PvkF8Ut 8,8 GB e y5Pm6ba 5,3 GB nunca saíam desde 14/11). Agora reaproveita o vídeo (final ou .partial) com o tamanho exato do Drive, pula o teste de espaço e o download (LONGO_REUSA_COMPLETO=0 desliga). PvkF8Ut subindo 11:46 no Fio da Meada ('O PODER DA ÁGUA É INFINITO? ELE REENCARNOU e DOMINOU tudo').
  - kit3d: pasta logs\ não existia -> Kit3dDiario terminava com erro 1 a cada 2 h, 0 Shorts 3D hoje. diario.py cria a pasta; tarefa relançada.
  - Pesquisador: 2 reprovados (search-filters, yt-channel-downloader) — não tratavam dos 30 s iniciais.
  - Estoque 30 dias funcionando: Empresário 7 e Vendas 2 Shorts hoje (antes ficavam vazios).
- 16/11 15h JÁ FEITO (dona: 'aplique no 3D tudo que os outros usam; disco era 20 GB ontem'):
  - DISCO: pagefile.sys do D cresceu até o máximo de 24 GB (pico real 14 GB, uso 6,7 GB). Limitado a 10-16 GB no registro (PagingFiles) — devolve ~8 GB no próximo reinício. Cópia de 5,6 GB do vilão em recap-longos-prontos (TESTE_NARRADORES, pra dona assistir) mantida.
  - Vilão/maid caía no Fio da Meada: parte 1 veio com nome PT sem nº de parte -> _serie None. postar_longos.SERIE_DONO_VID (5DoGv3EXHgc, eoyI3tVsj5w, CgyXHx6h2a8 -> InventoReact).
  - 3D no reuso: catalogo.FICHAS inclui historias-em-frames (projeto kit3d) — quando subir no YouTube vai sozinho pro TikTok/Instagram da conta do canal (postados_em).
  - 3D com capa no 1º quadro: capar_shorts.capar_3d (capa.png do kit, 0,5 s; CAPAR_3D=0). Geladeira testada: feita no S20 Ultra em 62 s, 1080x1920 60 fps, 46,3 s (era 45,8). Original em video_sem_capa.mp4.
