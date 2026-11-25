# PLANO DE MELHORIAS — consolidado do levantamento noturno (24/11)

Gerado em 25/11 a partir de levantamentoreas\levantar_*.json (12 áreas). Ordem: impacto alto e esforço
baixo primeiro. Faltaram 2 áreas (maquinas-render, confiabilidade-falhas) — boa parte delas foi resolvida no
trabalho de 25/11 (ver ARQUITETURA_PC1_SUPERVISOR.md).

## Fila (fazer de cima pra baixo)

| # | Área | Achado | Impacto | Esforço | Estado |
|---|---|---|---|---|---|
| 1 | aprendizado-metricas | Leitura do Studio em colapso: o aprendizado inteiro está sem alimento | alto | baixo | PARCIAL 25/11 (lote pula canais sem perfil; falta fallback pela API pública) |
| 2 | aprendizado-metricas | FocoShorts morre antes do --aplicar: notas de fonte, voz e receitas paradas desde 22/11 | alto | baixo | FEITO 25/11 (limite 60 min) |
| 3 | aprendizado-metricas | Motor de voz (Fish x antigo) não é sinal medido em nenhum placar | alto | baixo | a fazer |
| 4 | arquitetura | Nao existe um ponto unico de caminhos: centenas de 'D:\...' fixos e o Colab precisa de gambiarra para traduzir | alto | baixo | a fazer |
| 5 | codigo-morto | Fork esquecido do trabalhador do Kaggle: kaggle_trabalhador_VPS_fish.py (87 KB) já divergiu do oficial | alto | baixo | a fazer |
| 6 | disco-arquivos | D:\tmp\cenas3d_longo: 10,4 GB de longos 3D sem ninguém para limpar, e o laço de tentativas segura os arquivos  | alto | baixo | a fazer |
| 7 | disco-arquivos | faxina_disco não chega ao fim desde 22/11: o cache_reuso (e outras faxinas) parou de ser limpo | alto | baixo | FEITO 25/11 (ordem trocada; chega ao TOTAL em 37 s) |
| 8 | modelos-ia | Kiro gasto escondido: painel_ia cai pro Kiro, aplica o conserto e a vigilância joga fora e pede de novo | alto | baixo | a fazer |
| 9 | modelos-ia | Alarme 'reserva_zero' reabre o mesmo canal a cada 6 h sem fechar o anterior: 195 casos presos e 23,5 h de Gemi | alto | baixo | FEITO 25/11 (dedup + 222 fechados) |
| 10 | modelos-ia | Júri dos Cortes roda em quase todo Short (JURI_CADA=4 anulado) com 4 sessões claude.exe cada | alto | baixo | FEITO 25/11 (1 a cada 4) |
| 11 | narracao-longos | O motor novo da narração não tem medida de retenção e as views caíram | alto | baixo | a fazer |
| 12 | narracao-longos | As falas de personagem saem com a voz do narrador e a CONFERENCIA marca OK | alto | baixo | a fazer |
| 13 | narracao-longos | A IA devolve JSON quebrado e o longo sai sem falas e sem ganchos, sem aviso à dona | alto | baixo | FEITO 25/11 (_lista_json_ia; aviso à dona ainda não) |
| 14 | narracao-shorts-fish | Portar para o Fish dos Shorts o pós-processamento do Fish dos longos (gol, lento, desfecho, S do respeito, ris | alto | baixo | FEITO 25/11 (FISH_ONLINE_POS) |
| 15 | narracao-shorts-fish | Texto do Fish online sai cru: sem _texto_fish (kkk vira risada de robô, '...' imprevisível, pergunta ao públic | alto | baixo | FEITO 25/11 (_texto_fish no online) |
| 16 | narracao-shorts-fish | Créditos: 320 mil/mês dão ~23 Shorts/dia, não 100. Falta um teto por dia até o dia 18 e uma ordem de prioridad | alto | baixo | a fazer |
| 17 | postagem-recuperacao | Metade da produção do dia vai para o Fato Chocante, que não consegue subir nada (perfil deslogado desde 20/11) | alto | baixo | a fazer |
| 18 | redes-tiktok-insta-fb | Medição parcial do TikTok (6 de 58) derruba o teto das contas fortes no mesmo dia | alto | baixo | a fazer |
| 19 | redes-tiktok-insta-fb | vigia_tiktok_ip pausou contas fortes e nunca despausa; lista de 'boas' congelada em 12/11 | alto | baixo | a fazer |
| 20 | redes-tiktok-insta-fb | aulasrevolution (3ª maior do TikTok) ficou 3 dias sem post: conta VIVA do Kaggle sem fonte própria | alto | baixo | a fazer |
| 21 | redes-tiktok-insta-fb | Facebook: rodada estoura 55 min tentando baixar do Drive vídeos que não existem mais | alto | baixo | a fazer |
| 22 | tarefas-agendadas | Renders longos no PC1 por tarefa com limite de 72 h e IgnoreNew prendem a fila | alto | baixo | a fazer |
| 23 | vigia-relatorio | URGENTE da vigilância nunca sai na hora: cai no resumo das 9/14/21 h | alto | baixo | a fazer |
| 24 | vigia-relatorio | notificar_telegram preso desde 03:14: liberar_esperas não roda e o aviso de disco a 6 GB ficou retido | alto | baixo | a fazer |
| 25 | vigia-relatorio | Problema que precisa da dona (checkpoint) é reaberto e rediagnosticado a cada 6 h | alto | baixo | a fazer |
| 26 | vigia-relatorio | Sem medidor de disco no vigia, e o relatório mostra disco errado (22-28 GB contra 6 GB reais) | alto | baixo | a fazer |
| 27 | vigia-relatorio | Longo reenviado 19 vezes sem ninguém avisar: só existe o prazo de 36 h pro último ok | alto | baixo | a fazer |
| 28 | visual-shorts | Placar fechou T6 (fx_choque=B) e T8/T11 comparando braços placebo; sinal 'raio azul 1,31x' vem só de 28/10-01/ | alto | baixo | a fazer |
| 29 | visual-shorts | Cerca de 40% dos Shorts de 22-23/11 ainda sorteiam testes FECHADOS (curto, fx_choque, ninguem_esperava): confi | alto | baixo | a fazer |
| 30 | aprendizado-metricas | A/B dos Shorts nunca fecha sozinho: placar parado desde 17/11 e testes 'sem diferença' eternos | alto | medio | FEITO 25/11 (decisor_ab.py + DecisorAB) |
| 31 | aprendizado-metricas | Loop mínimo proposto: medição → decisão automática (amarra os achados) | alto | medio | a fazer |
| 32 | arquitetura | Ciclo de dependencia video-fila <-> postador/bin (e cofre/kaggle_pool como hubs ocultos) | alto | medio | a fazer |
| 33 | codigo-morto | 254 scripts .py que nada chama (nenhuma tarefa, import, .bat ou .vbs) | alto | medio | a fazer |
| 34 | codigo-morto | Cópia antiga do pipeline manhwa dentro do postador: 80 módulos com o mesmo nome do producao\bin, 42 já diferen | alto | medio | a fazer |
| 35 | disco-arquivos | GerenteVideos travado: python órfão desde 04:01 segura a trava, a rodada das 05:53 morreu e o inventário está  | alto | medio | conferido 25/11: GerenteVideos rodou 13:53 com resultado 0 |
| 36 | disco-arquivos | D:\caches\c_movido: 14 GB, a maior parte de sessões de chats AUTOMÁTICOS (lapidar/produto_fila), marcada como  | alto | medio | a fazer |
| 37 | narracao-longos | O padrão XTTS 8 + S2-Pro 13 nunca foi produzido: o único misto é v2 e pegou 8% das frases | alto | medio | a fazer |
| 38 | narracao-longos | Imagem parada de 55 a 62 s passa no QA e é postada | alto | medio | a fazer |
| 39 | narracao-longos | A retenção dos longos é de 1 a 4 min: o começo decide e o experimento do resumo está parado | alto | medio | a fazer |
| 40 | narracao-shorts-fish | Fish online parou de narrar os Shorts desde 21/11, com 270-330 mil créditos parados | alto | medio | FEITO 25/11: narrador sumiu do Fish (404); trocado pelo ac63ad94 aprovado; Fish narra de novo |
| 41 | postagem-recuperacao | Esteira de envio pelo PC quase parada: 5 ok contra 21 falhas em 23/11, e só o PC1 acerta | alto | medio | a fazer |
| 42 | postagem-recuperacao | O so_nobre do médico vale só para upload novo, e os Shorts já agendados dos canais tratados continuam fora das | alto | medio | a fazer |
| 43 | redes-tiktok-insta-fb | Instagram posta pelo IP compartilhado do TikTok (3-9 contas por IP), contra a regra 1-conta-por-IP do Instagra | alto | medio | a fazer |
| 44 | redes-tiktok-insta-fb | Estoque do TikTok parado em contas mortas enquanto as contas com view ficam sem vídeo | alto | medio | a fazer |
| 45 | tarefas-agendadas | 36 tarefas com 0x800710E0: disparos recusados viram ruído e escondem falha real | alto | medio | a fazer |
| 46 | tarefas-agendadas | DriveChaveRenovar falha desde 16/11: a chave do Drive não renova | alto | medio | FEITO 25/11: chave renovada + tarefa diária (drive_chave.py diario) |
| 47 | vigia-relatorio | Fila de conserto entupida: 191 casos 'consertar' sem prazo, teto diário gasto em caso velho | alto | medio | a fazer |
| 48 | visual-shorts | Efeitos T5/T6/T7 e impacto lateral NÃO são renderizados desde 01/11 (vivem só no caminho PNG morto) | alto | medio | a fazer |
| 49 | aprendizado-metricas | A/B dos longos: amostra impossível e 'vencedores' de ruído | medio | baixo | a fazer |
| 50 | aprendizado-metricas | Longos não registram o motor de voz: XTTS x Kitten x Fish nunca vai ter placar | medio | baixo | a fazer |
| 51 | arquitetura | Copia COMUM desatualizada: narracao_curva.py do hipercool-videos esta parada em 13/11 | medio | baixo | a fazer |
| 52 | arquitetura | Estado do Kaggle espalhado em 5 arquivos, 3 deles mortos e um ainda usado como reserva | medio | baixo | a fazer |
| 53 | arquitetura | Postador nao tem venv proprio: roda no Python do projeto veo (e 4 interpretadores fixos espalhados) | medio | baixo | a fazer |
| 54 | arquitetura | URL do OmniRoute fixa em 68 arquivos | medio | baixo | a fazer |
| 55 | codigo-morto | 17 snapshots + 2 backups do manhwa de julho em producao\bin (7,7 MB, 20 cópias de hiper-pipeline.py) | medio | baixo | a fazer |
| 56 | codigo-morto | vigia_backups com 140 pastas e 70 MB, sem rodízio | medio | baixo | a fazer |
| 57 | codigo-morto | Cerca de 180 arquivos .bak/.bkp nas pastas vivas, 50 só do kaggle_pool.json | medio | baixo | a fazer |
| 58 | codigo-morto | 43 tarefas Desativadas continuam registradas, com scripts que já viraram legado | medio | baixo | a fazer |
| 59 | disco-arquivos | Mesmo longo de 3,4 GB guardado em duas cópias independentes (_longos_postar e LONGO_PARA_CONFERIR) | medio | baixo | a fazer |
| 60 | disco-arquivos | D:\tmp\estudo_voz: 3,8 GB crescendo (1.166 arquivos novos em 3 dias) sem dono, com o registro de testes vazio | medio | baixo | a fazer |
| 61 | disco-arquivos | O RELATORIO_MANHA.md do trabalho noturno não foi gerado: as decisões pendentes de disco não chegaram à dona | medio | baixo | a fazer |
| 62 | modelos-ia | Argon do texto dos Shorts: timeout de 120 s custa 4,6 h por semana; o sucesso responde em 5-36 s | medio | baixo | a fazer |
| 63 | modelos-ia | Caixa do recap: cc-sobra, ag-opus-5-5 e ag-hydrogen entregaram 1 de 50 tentativas e gastam 3,2 h antes do Gemi | medio | baixo | a fazer |
| 64 | modelos-ia | Hydrogen passa no teste de 5 tokens mas falha no trabalho real e segue como 2º consertador da vigilância | medio | baixo | a fazer |
| 65 | modelos-ia | Júri dos Cortes: modelo de reserva igual ao principal, então o timeout de 900 s se repete | medio | baixo | FEITO 25/11 (reserva agy/gemini-3.8) |
| 66 | narracao-longos | A mascote fala com a voz do narrador em todos os longos XTTS | medio | baixo | a fazer |
| 67 | narracao-longos | Longo de 3,4 GB leva 6,7 h para subir e falha no fim, travando a fila | medio | baixo | a fazer |
| 68 | narracao-longos | A Fish na nuvem falhava calada e caía no Kitten (0/345) | medio | baixo | a fazer |
| 69 | narracao-longos | A legenda escorrega no XTTS e no S2-Pro: conserto de 22/11 ainda sem prova | medio | baixo | a fazer |
| 70 | narracao-shorts-fish | Efeito e 'fim que sobe' de OUTRA voz aplicados por cima da voz do Chris | medio | baixo | a fazer |
| 71 | narracao-shorts-fish | Tags de emoção do S2-Pro 13 ([laughing], [excited tone], [sigh], [shouting], [chuckle]) não passam para o Fish | medio | baixo | a fazer |
| 72 | narracao-shorts-fish | Piada de virada em 2 linhas ('...hein?!' / 'Mentiraaa, galera!') só existe no roteiro do longo | medio | baixo | a fazer |
| 73 | narracao-shorts-fish | Whisper dos tempos das palavras roda na CPU do PC1 no caminho local do Fish | medio | baixo | a fazer |
| 74 | postagem-recuperacao | O reagendar_nobre mexeu nos canais de CONTROLE do experimento do médico duas horas depois do sorteio | medio | baixo | a fazer |
| 75 | postagem-recuperacao | Canal punido (1 por dia) com fila cheia agenda Shorts até 3 meses à frente (30/12, 02/01, 15/02) | medio | baixo | a fazer |
| 76 | postagem-recuperacao | Canais recuperados perdem vagas: o envio pula Shorts 'prontos mas sem video.mp4' (estão no Drive) | medio | baixo | a fazer |
| 77 | postagem-recuperacao | A agenda dos celulares e o cadastro ainda usam 15 h, hora marcada como EVITAR, e deixam de lado a 7 h (RECEITA | medio | baixo | a fazer |
| 78 | redes-tiktok-insta-fb | Escada do Facebook decide com a soma dos reels visíveis: leitura errada vira bônus de post e falso 'viral' | medio | baixo | a fazer |
| 79 | redes-tiktok-insta-fb | Instagram: foco congelado em 14/11 mantém conta com 0 view e deixa de fora as que dão view | medio | baixo | a fazer |
| 80 | redes-tiktok-insta-fb | Relatório mostra 'Instagram: 0 leituras hoje' lendo um arquivo parado desde 14/11 | medio | baixo | a fazer |
| 81 | tarefas-agendadas | KaggleSaudeContas_0800 e _2130 apontam para script apagado | medio | baixo | a fazer |
| 82 | tarefas-agendadas | '1min visita diaria' falha todo dia e não grava nada desde 31/10 | medio | baixo | a fazer |
| 83 | tarefas-agendadas | ZeladorSonnet trava em ssh de 120 s e falha todo dia | medio | baixo | a fazer |
| 84 | vigia-relatorio | Fila do celular: 113 pedidos 'parado' (38 com vídeo pronto, 1 GB) que nenhum medidor nem relatório mostra | medio | baixo | a fazer |
| 85 | vigia-relatorio | A tabela 'Vigilância' do relatório infla acertos e esconde que nada foi consertado | medio | baixo | a fazer |
| 86 | vigia-relatorio | Relatório diz 'Pesquisador: Motor LIGADO', mas a dona pausou a tarefa | medio | baixo | a fazer |
| 87 | vigia-relatorio | Evidência do sem_sucesso perde o erro mais repetido (precedência do ternário) | medio | baixo | a fazer |
| 88 | visual-shorts | Mascote T7 e gancho Remotion T5 estão 'ab' há 3 semanas sem nenhum vídeo B real | medio | baixo | a fazer |
| 89 | visual-shorts | 'Legenda lateral' está fixada mas não é aplicada, e o próprio placar diz que lateral é PIOR em retenção | medio | baixo | a fazer |
| 90 | visual-shorts | Placar dos testes parado desde 17/11: gancho_meio, saudação e fala rápida sem decisão há uma semana | medio | baixo | a fazer |
| 91 | visual-shorts | Capa: 'pesca' (maior mídia, 1,23x) e negócios/saúde ficam fora do CaparShorts; 71% dos Shorts saem sem capa/1º | medio | baixo | a fazer |
| 92 | aprendizado-metricas | Posts pelos celulares ficam fora da medição (sem video_id) | medio | medio | a fazer |
| 93 | aprendizado-metricas | Médico da recuperação: bom molde, mas ainda não rodou pela tarefa e só cobre 2 alavancas | medio | medio | a fazer |
| 94 | aprendizado-metricas | Receitas 'SORTE' nunca viram teste: o cruzamento acha hipótese e ninguém confirma | medio | medio | a fazer |
| 95 | arquitetura | 39 modulos com MESMO nome e conteudo DIFERENTE entre recapd/bin e postador/bin (risco de sombra no sys.path) | medio | medio | a fazer |
| 96 | arquitetura | Cadastro de canais em 5 arquivos + credenciais OAuth em JSON aberto lido por 23 scripts | medio | medio | a fazer |
| 97 | codigo-morto | Módulos comuns copiados à mão em 3 lugares (bin, postador e comum) | medio | medio | a fazer |
| 98 | disco-arquivos | R9-R12 e DISCO_MIN_GB ficaram fora do gerente: rodaram uma vez à noite como scripts soltos | medio | medio | a fazer |
| 99 | narracao-shorts-fish | Reserva 'sem crédito = XTTS 8 no PC' não existe no PC1: cai no p3 | medio | medio | a fazer |
| 100 | narracao-shorts-fish | Short com narrador parceiro (Momo, Mike, Pie...) sai na voz do Chris: falta voz do narrador no site | medio | medio | a fazer |
| 101 | postagem-recuperacao | Fila dos celulares: de cada 3 tentativas, 2 dão erro (troca de conta e câmera sem botão de importar) | medio | medio | a fazer |
| 102 | redes-tiktok-insta-fb | TikTok mede views 1x por dia, de uma vez, pelo Chrome de uma conta (msenergypara) e trava | medio | medio | a fazer |
| 103 | tarefas-agendadas | Medidores TikTok_MedirViews, Marcas_Carrossel e MSEnergy_Metricas morrem no meio (0x8007042B) | medio | medio | a fazer |
| 104 | aprendizado-metricas | Testes sem dado vivo continuam sorteando (abertura abcd e horario_fraco) | baixo | baixo | a fazer |
| 105 | arquitetura | 16 arquivos falam direto com a API do Telegram, por fora do avisos.py | baixo | baixo | a fazer |
| 106 | arquitetura | Nenhum dos 6 projetos tem historico de versao local; protecao e por .bak solto | baixo | baixo | a fazer |
| 107 | codigo-morto | Chave ANIME_MASCOTE_TOM é gravada e nunca lida | baixo | baixo | a fazer |
| 108 | codigo-morto | Chaves FLOW_* no cron_produto_videos.bat sem leitor na cadeia do postador (conferir) | baixo | baixo | a fazer |
| 109 | codigo-morto | Scripts de diagnóstico e engenharia reversa soltos em video-fila (testes\ 12, engenharia_reversa\ 10, estado\* | baixo | baixo | a fazer |
| 110 | codigo-morto | Utilitários vivos que parecem mortos: teste_remoto.py, memes_pt_baixar.py e cenas3d_no_longo.py (NÃO mover) | baixo | baixo | a fazer |
| 111 | disco-arquivos | Logs grandes: um morto (82 MB) e um crescendo sem rotação (34 MB). Os do video-fila estão sob controle | baixo | baixo | a fazer |
| 112 | disco-arquivos | O gerente ignora *.partial do rclone nas pastas de Short e as sobras .tmp do estado | baixo | baixo | a fazer |
| 113 | modelos-ia | Pausa de 15 min do Argon depois de UMA falha manda 866 textos para a reserva sem nem tentar | baixo | baixo | a fazer |
| 114 | modelos-ia | Vigilância: 'pergunta' do vigia com mediana de 222 s e até 45 voltas para confirmar alarme simples | baixo | baixo | a fazer |
| 115 | narracao-longos | Os testes solo dão alarme falso de revezamento | baixo | baixo | a fazer |
| 116 | narracao-shorts-fish | Velocidade base: não acelerar o Fish por igual (o teste fala_rapida mostra que o +15% rende menos) | baixo | baixo | a fazer |
| 117 | postagem-recuperacao | Ficam 14 pedidos velhos em fila_celulares\pendentes, alguns com data já passada (20/11) e outros para 30/12 e  | baixo | baixo | a fazer |
| 118 | redes-tiktok-insta-fb | TikTok: contas paradas por máquina sem disco e Chrome remoto caído entram em toda rodada | baixo | baixo | a fazer |
| 119 | tarefas-agendadas | 11 tarefas de 'uma vez' já vencidas seguem ligadas (lixo de testes e lembretes) | baixo | baixo | a fazer |
| 120 | tarefas-agendadas | AmostraGanchoDona aponta para o scratchpad de um chat no C: | baixo | baixo | a fazer |
| 121 | tarefas-agendadas | MonitorOpus roda python.exe direto (sem rodar_oculto) a cada 10 min | baixo | baixo | a fazer |
| 122 | tarefas-agendadas | Tarefas de estudo e teste já encerradas seguem ligadas (AcompanharNoite21Nov, InstalarPC3, ArgonManterLogon) | baixo | baixo | a fazer |
| 123 | tarefas-agendadas | 12 tarefas desligadas há mais de 30 dias, algumas com caminho quebrado | baixo | baixo | a fazer |
| 124 | vigia-relatorio | Seção 3D publica links quebrados 'youtu.be/celular:@...' como se fossem vídeos | baixo | baixo | a fazer |
| 125 | vigia-relatorio | Seção 'Outras línguas' fixa em 2 IDs de 27/10: ocupa espaço e roda rclone à toa | baixo | baixo | a fazer |
| 126 | visual-shorts | Tratamento de capa B (receita 'B:drama' 2,0x/1,38x) está desligado: CAPA_TRATAMENTO nunca é definido | baixo | baixo | a fazer |
| 127 | visual-shorts | Já ligados por padrão (não propor de novo): hora 21-22 h, delogo, Short curto, 'NINGUÉM ESPERAVA' liberado | baixo | baixo | a fazer |
| 128 | visual-shorts | Shorts renderizam em 720x1280 e são esticados para 1080: ANIME_RENDER_1080 nunca é ligado | baixo | medio | a fazer |

## Detalhe de cada achado

### 1. [aprendizado-metricas] Leitura do Studio em colapso: o aprendizado inteiro está sem alimento

- **problema:** Todo o aprendizado dos Shorts (sinais, receitas, nota de fonte e de voz, placar A/B, avaliar_testes_voz) usa só metricas_studio.json, e a leitura dele quase parou. Os Shorts novos (Fish, canais em recuperação) não entram em nenhuma conta.
- **evidencia:** postador-de-videos/logs/metricas_rede.log, leituras ok por dia: 20/11=33, 21/11=17, 22/11=7, 23/11=2, 24/11=1. Falhas: 18x 'Locator.inner_text: Timeout 30000ms' e 5x 'Page.goto Timeout 90000ms' em 23-24/11. Último lote: '573 video(s) sem views em 43 canal(is); lendo 4 (0 lido(s) nas ultimas 6 h)'. metricas_studio.json, lido_em por dia: 15/11=125 … 23/11=21, 24/11=7; ret_lista teve leitura em massa só em 16-17/11 (591+1660). Uploads de 17-21/11: 348 no uploads_ledger, 287 sem métrica do Studio.
- **proposta:** (a) Fallback de views pela API pública já coletada: em analise_sinais_shorts.carregar() e placar_variantes, quando o vídeo não está no Studio, usar views de video-fila/estado/videos_canais.json (cobre 163 dos 287 que faltam). A razão views/mediana do canal funciona igual; só 'continuaram' fica None. Chave SINAIS_VIEWS_API=0 desliga. (b) Diagnosticar o timeout do Studio (mudou o seletor 'ytcp-'?) fora do PC1 e pela saída fixa de cada conta, sem laço de contas no mesmo IP.
- **risco:** baixo
- **ja_existe:** videos_canais.py (API pública, cache de 1 h) já grava views por vídeo, mas o aprendizado não usa. metricas_rede existe e está falhando.

### 2. [aprendizado-metricas] FocoShorts morre antes do --aplicar: notas de fonte, voz e receitas paradas desde 22/11

- **problema:** A tarefa tem limite de 20 min e o script passou a imprimir as tabelas e ser morto antes do bloco que grava. As decisões automáticas (peso da fonte no parceiro_diario, ranking de voz, RECEITAS) usam dados de 2 dias atrás, e cada dia piora.
- **evidencia:** Get-ScheduledTask FocoShorts: ExecutionTimeLimit PT20M, LastTaskResult 267014 (0x41306, encerrada). logs/foco_shorts.log: a última linha 'fontes por canal' é a 2109 (rodada de 22/11); a rodada de 24/11 (linha 2130, '2177 Shorts…') termina nas tabelas CANAL x TIPO, sem 'fontes por canal' nem 'ajustado pelo horário'. mtimes: estado/sinais_shorts.json, RECEITAS_DO_SUCESSO.md, recapd/estado/fontes_por_canal.json e narradores_ajustado.json = 22/11 05:42-05:43. O CSV de 23 e 24/11 foi escrito (06:00 e 05:57), o que mostra que o script rodou e foi cortado depois.
- **proposta:** Pôr o bloco --aplicar (fontes_por_canal, inteligencia_ajustada.gravar, gravar_receitas, aplicar) ANTES das impressões longas, ou subir o limite para PT45M. Gravar também sinais_shorts.json completo (hoje o --json do analise_sinais_shorts só roda à mão; gravar_receitas só atualiza 'receitas'). Adicionar ao relatorio_ronda um alerta 'dado de aprendizado com mais de 36 h'.
- **risco:** baixo
- **ja_existe:** FOCO_RECEITAS=0 desliga as receitas. Não há alerta de dado velho.

### 3. [aprendizado-metricas] Motor de voz (Fish x antigo) não é sinal medido em nenhum placar

- **problema:** Fish é a voz primária dos Shorts desde 19/11 e gasta crédito pago, mas a análise que diz 'o que dá view' não olha o motor. A gravação do campo também é falha: postar.json pós-19/11 mostra motor_voz só em parte dos Shorts.
- **evidencia:** analise_sinais_shorts.py:27-30, a tupla CAMPOS não tem 'motor_voz'. bin/anime_publish.py:575 grava 'motor_voz': _motor_voz(video), que devolve None quando falta audio_cache/_voz_online.json (linhas 350-363). Nos 400 últimos uploads_ledger com postar.json legível, entre os de 20/11 em diante: 54 com a chave motor_voz e 63 sem. Nos lidos, o valor 'motor' veio None em 351 de 351 (Counter por get('motor')).
- **proposta:** Gravar sempre motor_voz = {'motor': 'fish'|'xtts'|'kitten'|'p3'} no postar.json (sem marca = gravar o motor que de fato narrou, não None). Incluir 'motor_voz_motor' (texto) em CAMPOS do analise_sinais_shorts e em receita_ou_sorte. Com o fallback de views da API (achado 1), em ~3 dias dá para saber se o crédito Fish se paga.
- **risco:** baixo
- **ja_existe:** parceiro_diario.py:982-985 lê motor_voz só para pôr na frente da fila, não para medir.

### 4. [arquitetura] Nao existe um ponto unico de caminhos: centenas de 'D:\...' fixos e o Colab precisa de gambiarra para traduzir

- **problema:** Cada script monta seu sys.path e seus caminhos na mao. Mover/renomear qualquer pasta (ou rodar em outra maquina) quebra dezenas de arquivos em silencio. O proprio Colab ganhou um sitecustomize que reescreve 'D:\' para /content/raiz porque o codigo nao tem raiz configuravel.
- **evidencia:** Contagem de sys.path.insert/append distintos (grep nos 7 projetos): r"D:\logins-google" 68, r"D:\video-fila" 61 (+13 append, +3 'D://video-fila'), r"D:\postador-de-videos\bin" 24+6+6, r"D:\hipercool-materiais\comum" 20+5, r"D:\hipercool-materiais\comum\fish_audio" 16, r"D:\recapd-ambientes\producao\bin" 12. video-fila/*.py cita 'hipercool-materiais' 512x e 'postador-de-videos' 277x. controlador.py:41-51 tem 11 constantes Path(r"D:\..."). recapd/colab/sitecustomize.py:1-2: 'o codigo do PC tem caminhos fixos D:\... e C:\...; aqui eles viram /content/raiz/D/...'. Busca por modulo de caminhos (caminhos.py/raiz/CAMINHOS) em comum e video-fila: nenhum.
- **proposta:** PRIMEIRO PASSO CONCRETO: criar D:\hipercool-materiais\comum\caminhos.py (so constantes + os.environ override, ex.: RAIZ=os.environ.get('SISTEMA_RAIZ','D:\\'); VIDEO_FILA, POSTADOR_BIN, RECAPD, COMUM, FISH, LOGINS, KAGGLE_POOL, OMNIROUTE_URL, PY_HIPER/PY_VEO/PY_MR, VBS) e registra-lo no recursos.json com 'recursos.py subir caminhos.py --de recapd' para que cada bin/ receba copia identica (mesmo mecanismo que ja funciona para 22 modulos; PC2/desktop recebem pelo sync de bin). Nenhum import existente muda neste passo. Depois migrar 1 constante por vez nos arquivos, comecando pelos de maior contagem.
- **risco:** baixo
- **ja_existe:** recursos.py (D:\hipercool-materiais\bin\recursos.py:1-20) ja distribui copias identicas e confere hash; falta so o modulo de caminhos. Colab tem traducao propria em colab/sitecustomize.py.

### 5. [codigo-morto] Fork esquecido do trabalhador do Kaggle: kaggle_trabalhador_VPS_fish.py (87 KB) já divergiu do oficial

- **problema:** Existem 4 versões do trabalhador em colab. Só kaggle_trabalhador.py é enviado ao Kaggle. O _VPS_fish tem o lote de teste de voz, e o oficial não tem. O oficial tem o puxador de código de 22/11, e o _VPS_fish não tem. Se alguém subir a VPS com o fork, roda código de 19/11 sem as correções de 20 a 22/11.
- **evidencia:** colab\kaggle_lancar.py:63 copia só "kaggle_trabalhador.py". O grep por 'VPS_fish'/'kaggle_trabalhador_' nos .py/.bat/.sh de colab e nas tarefas dá 0 chamadas. Funções que só existem de um lado (diff de 'def'): _puxador_de_codigo (kaggle_trabalhador.py:332, 22/11) contra lote_teste_voz (kaggle_trabalhador_VPS_fish.py:961, 17/11; 'fila_teste_voz' aparece 5 vezes no fork e 0 no oficial). Mais 2 forks sem uso: kaggle_trabalhador_NO_AR.py (10,5 KB) e kaggle_trabalhador_ROBUSTEZ_nao_testado.py (17,7 KB), ambos de 26/10.
- **proposta:** Decidir se o lote_teste_voz ainda serve (os testes de voz estão pausados, segundo a memória). Se servir, passar a função para o kaggle_trabalhador.py atrás de TESTE_VOZ=0, como o próprio docstring do fork prevê. Depois mover os 3 forks para colab\_arquivo\ com uma nota de 1 linha.
- **risco:** baixo
- **ja_existe:** Não existe nota de decisão sobre o fork. O montar_pacote.py:20 não exclui esses arquivos do pacote (FORA só tira _SNAPSHOT*, _BACKUP*, _snapshots, *.bak*, *.bkp*), então os 3 forks vão junto em todo pacote.

### 6. [disco-arquivos] D:\tmp\cenas3d_longo: 10,4 GB de longos 3D sem ninguém para limpar, e o laço de tentativas segura os arquivos até 36 h

- **problema:** O cenas3d_no_longo.py baixa o final_anime_deitado.mp4 do Drive (~5 GB) para D:\tmp\cenas3d_longo\<pid>\final.mp4 e só apaga quando dá PRONTO. Quando o scp ou o ssh para o desktop falha (exit 255), o arquivo fica. O rodar_cenas3d.py repete por até 36 h, e já há dois longos de 5 GB parados.
- **evidencia:** du: 5,5 GB em 20261122_215730_eRJ1kFR196s e 4,9 GB em 20261123_111119_eRJ1kFR196s_C. Os final.mp4 têm 5.897.833.709 e 5.252.534.143 bytes. Em D:\recapd-ambientes\producao\bin\cenas3d_no_longo.py:119-122, o unlink só roda no caminho de sucesso (`if r_.returncode == 0`). Em D:\tmp\cenas3d_auto.log (23/11 22:50 a 24/11 01:45), todas as tentativas falharam (scp 255, 'desktop não baixou o vídeo', timeout no rclone do roteiro). Em D:\tmp\estudo_voz\rodar_cenas3d.py:14, `fim = time.time() + 36 * 3600`. Em D:\limpeza_c\donos.json, D:\tmp\cenas3d_longo tem 'limpa: NINGUÉM (24/11 01:50: 10,4 GB)'. O ULTIMO_ALERTA.txt das 02:24 lista os dois como as maiores gravações em 48 h.
- **proposta:** (1) Em cenas3d_no_longo.py, envolver o trecho do scp até o final num try/finally que apaga o `loc` local depois que o scp para o desktop terminar (o original continua no Drive em fila_src). (2) No gerente_videos, criar a regra R13: D:\tmp\cenas3d_longo\*\final*.mp4 parado há mais de 12 h é apagado só se o rclone lsjson de fila_src/<pid>/final_anime_deitado.mp4 tiver o mesmo tamanho. (3) Ou baixar direto no desktop (`rclone copyto` lá), mas o comentário de 23/11 diz que o rclone do desktop aponta para outra conta. Por isso a saída é (1)+(2).
- **risco:** baixo
- **ja_existe:** Não. O donos.json marca 'NINGUÉM' e o gerente só conta D:\tmp na tabela 'Outras pastas', sem regra (gerente_videos.py:48-50; INVENTARIO_VIDEOS.md: D:\tmp com 101 vídeos e 13,05 GB).

### 7. [disco-arquivos] faxina_disco não chega ao fim desde 22/11: o cache_reuso (e outras faxinas) parou de ser limpo

- **problema:** O main() da faxina_disco.py roda vozes_drive/fontes_drive (rclone moveto, que pode levar mais de 1 h) ANTES de limpar o cache_reuso, os *.tmp.mp4 e os testes vencidos. Desde 22/11 o log mostra só as primeiras etapas, e a linha 'TOTAL' não aparece mais.
- **evidencia:** Em D:\video-fila\logs\faxina_disco.log, o último 'TOTAL' é de [22/11 07:07:31]. Em 23/11 aparecem 'vozes_drive: TimeoutExpired ... timed out after 4571 seconds' (08:20) e 'fontes_drive: TimeoutExpired' (08:53), e depois nada de cache_reuso. Em 24/11 só existe a linha '06:23:37 longos com envio falho'. Na ordem do faxina_disco.py:242-317, as etapas VELHOS_EXTRA vêm na linha 317, depois do vozes_drive na linha 280. D:\postador-de-videos\cache_reuso tem 758 MB em 22 arquivos, inclusive 1c4d81ab_video.mp4 de 04/11, 22a382d2 de 06/11 e bf95b369 de 09/11, apesar da regra de apagar acima de 1 dia (faxina_disco.py:49, FAXINA_REUSO_DIAS=1). Também há 6 *.partial do rclone (até 52 MB, de 23/11).
- **proposta:** Mudar a ordem no main(): primeiro as limpezas locais rápidas (VELHOS_EXTRA, tmp.mp4, upscale_de_postados, testes, orphan_) e por último as subidas ao Drive (vozes/fontes/amostras/mapa_drive). Dar a cada uma um timeout menor (por exemplo 15 min) e `--timeout 60s`. Incluir '*.partial' com mais de 6 h na varredura do cache_reuso e da pasta animes recap\shorts.
- **risco:** baixo
- **ja_existe:** O cache_reuso tem dono declarado (faxina_disco VELHOS_EXTRA, e catalogo.liberar em catalogo.py:504). O mecanismo existe, mas não roda porque a função trava antes de chegar lá.

### 8. [modelos-ia] Kiro gasto escondido: painel_ia cai pro Kiro, aplica o conserto e a vigilância joga fora e pede de novo

- **problema:** Quando a vigilância pede um consertador (gemini/gemini-4-hydrogen, 1minopus-sonnetweb) e ele não pega, painel_ia usa ia_reserva.modelos(cfg['modelo']) = kr/claude-sonnet-4.5 (conserto=True e kiro_para_consertos=true). O Kiro roda até o fim e até APLICA, mas vigilancia.py vê usado != consertador, marca 'sem_token' e devolve o caso pra 'consertar' — o trabalho conta como perdido e é refeito. Esses jobs não entram no d['dia']['kiro'] (só soma quando m começa com kr/), então o teto KIRO_DIA_MAX=30 não vale para eles.
- **evidencia:** estado\painel_ia\*.json desde 17/11: 15 jobs modelo_fixo=gemini/gemini-4-hydrogen -> modelo=kr/claude-sonnet-4.5 (custo_usd somado 54,6), 15 de 1minopus-sonnetweb -> kr (40,5), 5 de gemini-4-argon -> kr (18,4); 39 jobs da vigilância com fallback = 1141 voltas. Ex.: job 20261124_000435_22d4 (caso 20261118_065033_232) tem aplicado_em=20261124_003327_6ad1, e vigilancia_casos.jsonl:1976 registra 'sem_token pedido=gemini/gemini-4-hydrogen usado=kr/claude-sonnet-4.5' e o caso segue em etapa 'consertar' no vigilancia.json. Código: painel_ia.py:727-731 (fixo só vale se não estiver _fora; senão fica o kr do claude_proxy.json), vigilancia.py:686-692 (descarta) e 678-679 (só conta kiro se m.startswith('kr/')). claude_proxy.json: modelo=kr/claude-sonnet-4.5.
- **proposta:** No pedido da vigilância com modelo_fixo, passar ao painel 'sem reserva' (ex.: job['so_fixo']=True): fixo fora = job termina 'sem_token' em ~1 s, sem chamar Kiro. Alternativa mínima: na vigilância, se usado começa com kr/ e o job tem aplicado_em, aceitar o resultado (seguir pra revisão) e somar d['dia']['kiro'] em vez de descartar.
- **risco:** baixo
- **ja_existe:** Não. kiro_conta_gota.json tem consertos_kiro_por_dia=6, mas só vigia_geral.py:465 lê; vigilancia.py tem KIRO_DIA_MAX=30 que não pega esses fallbacks.

### 9. [modelos-ia] Alarme 'reserva_zero' reabre o mesmo canal a cada 6 h sem fechar o anterior: 195 casos presos e 23,5 h de Gemini

- **problema:** med_reserva_zero gera um alarme por canal zerado; abrir_casos só olha d['alarmes'][chave] (6 h) e não se já existe caso ABERTO com a mesma chave. Resultado: o mesmo canal vira dezenas de casos, cada um passa pelo vigia LLM (pergunta com até 45 voltas) e depois por um consertador. O problema é de estoque/produção (canal sem vídeo, canal encerrado ainda ativo), não de código: o LLM só redescobre o que reserva_status.py já diz.
- **evidencia:** estado\vigilancia.json: 300 casos, 206 não fechados, 195 em 'consertar'; chaves: reserva_zero:dentrodascoisas3d 24, fatochocante 19, inventoreact 19, mundoquenaoexiste 18, esportenoturno 18, codigobilhao3d 13. vigilancia_casos.jsonl desde 17/11: 169 passos 'vigia' só de reserva-canal (de 238 no total). painel_ia desde 17/11: 234 jobs 'pergunta' agy/gemini-3.8-flash-high, mediana 222 s, 23,5 h somadas. Código: vigilancia.py:177-187 (med_reserva_zero), :603-608 (dedup só por tempo, REPETIDO_H=6 em :71).
- **proposta:** Em abrir_casos, pular a chave se já existir caso com essa chave em etapa não final (vigia, vigia_rodando, consertar, consertando, revisar). Para categoria reserva-canal, não chamar o vigia LLM: o medidor já é a prova (ir direto para aviso/fila de produção, ou um diagnóstico sem IA: canal encerrado em contas_travadas.json, alimentador vazio em canais.json). Fechar em lote os 195 casos duplicados mantendo 1 por canal.
- **risco:** baixo
- **ja_existe:** Só o filtro de 6 h (REPETIDO_H). Os próprios diagnósticos do vigia (vigilancia_casos.jsonl 24/11 04:33-05:51) apontam causas de cadastro (canais.json:159, :1084, contas_travadas.json:50) que não se resolvem com conserto de código.

### 10. [modelos-ia] Júri dos Cortes roda em quase todo Short (JURI_CADA=4 anulado) com 4 sessões claude.exe cada

- **problema:** cortes_juri.py faz júri se o Short tem texto do Argon ('medir Argon x Gemini', 27/10). Hoje o Argon é o padrão (cortes_ajustes.json texto_video_modelo=gemini-4-argon), então quase todo Short tem texto_modelo e o 'júri em 1 a cada 4' deixou de existir. Cada júri = 4 verificadores em paralelo, cada um um claude.exe -p com até 30 turnos e timeout de 900 s.
- **evidencia:** juri.log 17-24/11: 774 Shorts com movimento medido, 768 com '| júri' (ex.: 20/11 191/188; 17/11 162/161). postar.json em D:\hipercool-materiais\animes recap\shorts: 3895 de 4433 com texto_modelo='gemini-4-argon'. Código: cortes_juri.py:375-383 (argon or n_total % JURI_CADA == 1), :37 (JURI_CADA = 4), :98-107 (claude.exe -p --max-turns), :339 (4 em paralelo). As notas ficam concentradas em 7,5-9,25 (juri.log: 8,25=50, 8,5=69, 8,75=55, 9,0=52), quase sem diferença entre os Shorts.
- **proposta:** Trocar o gatilho para 'argon E sorteio' ou só n_total % JURI_CADA == 1 (a comparação Argon x Gemini já não tem grupo de controle: 88% é Argon). Corte de ~75% nas chamadas do júri. Chave nova CORTES_JURI_TODO_ARGON=1 volta ao jeito atual.
- **risco:** baixo
- **ja_existe:** JURI_CADA=4 existe, mas está anulado pela regra do Argon (comentário de 27/10 em cortes_juri.py:376).

### 11. [narracao-longos] O motor novo da narração não tem medida de retenção e as views caíram

- **problema:** Os longos do motor novo, de 19 a 22/11, não têm leitura nenhuma no Studio, e a ficha de postado não diz qual motor narrou. Por isso não dá para provar se o XTTS ou o S2-Pro seguram mais ou menos que o Kitten/RVC. Pelas views, os novos estão bem abaixo dos antigos.
- **evidencia:** colab\views_longos.json (lido 24/11 00:18): motor novo WEmcyeDuSxc 1, dMPo1zvSyCs 0, yOrT3vgoa4U 1, _r_CMoP9Hyw 16, t8tD4RSqdJs 2 (XTTS KkVirjão), Xiw0GwqrJXo 2 (XTTS trio), RhT093bQeNw 3 (S2-Pro Momo). Motor antigo no mesmo canal (Fio da Meada) de 13 a 16/11: AjgJG8HAfLk 204, SPThI7oMKGw 143, ozdALiyIDVY 115. postador _analise\metricas_studio.json: RhT093bQeNw, t8tD4RSqdJs, Xiw0GwqrJXo, _r_CMoP9Hyw e yOrT3vgoa4U não aparecem. dMPo1zvSyCs tem 'erro: TimeoutError'. Os campos de longos_postados.json['postados'] são nome, vid, canal, canal_nome, url, titulo, em, duracao_s, narradores_modo, seo_versao, estilo_titulo e tags: não há motor_voz.
- **proposta:** Gravar motor_voz, versões e % do S2-Pro na ficha de postado. Ler o motor do TESTE_NARRADORES.txt ou do longo_override do render.json; a ficha já tem narradores_modo, então é só acrescentar a chave. Pôr os longos do motor novo na leitura do Studio com dur_media e pct_media. Feito isso, a ronda compara a retenção por motor no mesmo canal. Sem esse número, a escolha XTTS 8 + S2-Pro 13 é só gosto de ouvido.
- **risco:** baixo
- **ja_existe:** Os Shorts já gravam motor_voz no postar.json (LONGOS_MELHORIAS.md 19/11 13:25). Nos longos não existe.

### 12. [narracao-longos] As falas de personagem saem com a voz do narrador e a CONFERENCIA marca OK

- **problema:** Nos longos XTTS a IA marcou as falas de personagem, mas as vozes dos personagens não estavam na máquina do Kaggle e tudo saiu na voz do narrador. A CONFERENCIA conta só as falas marcadas e mostra OK. A dona fica achando que o vídeo tem elenco de vozes e ele não tem. A troca de narrador, que é o item que mais segura em diálogo, não acontece.
- **evidencia:** na_nuvem\e2nIzNGXvmA_xtts_momo\CONFERENCIA.md: '✅ | 135 falas marcadas; vozes: sett_lol, rem, bulma...'. No pipeline.log:90-115 do mesmo longo, as 26 vozes dão '[personagem] voz X não está nesta máquina — falas ficam com o narrador'. Contagem nos pipeline.log de 21/11: 82ge1YYkUyA_qwen3 10 vozes faltando, 82ge1YYkUyA_s2pro 16, gJve_WjefZs 17, e2nIzNGXvmA 26. Código em bin\anime_segments.py:386-391.
- **proposta:** (1) Conferir no próximo longo se o _baixar_voz_drive de 23/11 (anime_segments.py:388) resolveu. A prova é o log sem 'não está nesta máquina'. (2) Fazer a linha 'Falas de personagem com outra voz' da CONFERENCIA contar as falas que saíram com outra voz, não as marcadas. Para isso, registrar no render.json as vozes que narraram de verdade.
- **risco:** baixo
- **ja_existe:** O download da voz do Drive entrou em 23/11 (anime_segments.py:388, comentário '23/11: o elenco é escolhido aqui dentro'), mas nenhum longo foi feito depois dele. A CONFERENCIA continua contando só as marcadas.

### 13. [narracao-longos] A IA devolve JSON quebrado e o longo sai sem falas e sem ganchos, sem aviso à dona

- **problema:** Quando a IA devolve JSON cortado ou mal formado, o longo sai com 0 falas de personagem e 0 mini-ganchos. O aviso 'faltou' também não sai no Kaggle, porque o módulo avisos não existe lá. A dona não fica sabendo.
- **evidencia:** CONFERENCIA de 124 longos em na_nuvem\*: 36 com 'Falas de personagem ❌ 0 falas marcadas' e 36 com 'Mini-ganchos ❌ 0'. Os logs registram 4x '[longo] falas de personagem: IA falhou (JSONDecodeError)' e 2x 'ganchos: IA falhou (JSONDecodeError)'. RzoyNcnlIj8 pipeline.log: '[claude_client] aviso de 'faltou falas de personagem' não saiu (ModuleNotFoundError)'. Código em bin\anime-pipeline.py:986-995 (re.search r'\[.*\]' + json.loads) e 1286, e bin\claude_client.py:815-825 (import avisos de D:\video-fila).
- **proposta:** (a) Ao dar JSONDecodeError, aproveitar os objetos completos até o ponto do corte, cortando no último '}' antes do ']', ou pedir à IA em lotes menores. Hoje a_cada_s é 15 (config/longo.json:144), o que pede centenas de falas num único JSON. (b) No Kaggle, gravar o 'faltou' num arquivo da pasta, como o faltou.json que já existe. Do lado do PC1, o postar_longos lê esse arquivo e avisa a dona.
- **risco:** baixo
- **ja_existe:** O registrar_faltou e a cadeia de modelos com rodadas=3 já existem (anime-pipeline.py:982-997). Não existe recuperação de JSON cortado nem aviso que funcione a partir do Kaggle.

### 14. [narracao-shorts-fish] Portar para o Fish dos Shorts o pós-processamento do Fish dos longos (gol, lento, desfecho, S do respeito, risada real)

- **problema:** No caminho dos longos (Fish nuvem), cada frase passa por _ritmo_fish (curva do locutor + frase lenta por conteúdo + aceleração do gol), _desfecho_gol (gol rápido / falha triste / fecho grosso), _esticar_s_respeito e _risada_real. No caminho online dos Shorts só roda _acabamento_fish (volume -20 LUFS + efeito + fim que sobe). Resultado: o Short no Fish fica numa velocidade só, sem o clímax acelerando, e com o RES-peito lido 'normal'.
- **evidencia:** anime_tts.py:1776-1781 (_marcar_gol no fish nuvem), 1867 (_ritmo_fish), 1869-1876 (desfecho, respeito, risada). Já anime_tts.py:2080-2085 (_narrar_online) só tem _acabamento_fish + margem final. As técnicas foram aprovadas pela dona em 20/11 (memória feedback_narradores_jeito_de_falar: ACELERAÇÃO DO GOL, 'piada = devagar sempre', 'tensão nunca devagar').
- **proposta:** Em _narrar_online, depois de fish_lote.gerar: chamar climas_voz.escolher + _marcar_gol(lines, climas) e, para cada frase feita, _ritmo_fish(out, <nome da voz>, texto, i, _impactos_do(audio_dir), len(lines)) + _desfecho_gol + _tem_respeito_piada/_esticar_s_respeito + _risada_real quando o texto tinha kkk. São as mesmas funções, sem código novo de áudio, e são só ffmpeg atempo/asetrate. Custo: 0 crédito e poucos segundos de CPU por Short. Ritmo SEMPRE pelo código (atempo), nunca por prosody.speed do Fish. Motivos: a dona disse em 20/11 que 'o Fish se atrapalha ao acelerar por ele' (anime_tts.py:1786-1789), e velocidade diferente de 1 deixa de reaproveitar o histórico grátis (fish_http.py:127). Chave para desligar: FISH_ONLINE_POS=0. Teste: 1 Short em narração contínua (regra 'homogeneidade > técnica isolada' de 20/11).
- **risco:** baixo
- **ja_existe:** As funções existem e são usadas no Fish nuvem, no Kitten sub (anime_tts.py:2287-2304) e no XTTS (1736). Só o caminho online dos Shorts não chama nenhuma delas.

### 15. [narracao-shorts-fish] Texto do Fish online sai cru: sem _texto_fish (kkk vira risada de robô, '...' imprevisível, pergunta ao público errada)

- **problema:** _narrar_online manda _seguro(line) direto para o Fish. A limpeza que a dona pediu em 20/11 para o Fish fica de fora: tirar kkk/haha ('risada de robô'), letra repetida no máximo 2x, tirar '...' do meio (silêncio longo ou sílaba repetida no Fish), 'Eu faria esse acordo! ... E vocês, fariam?' e RES-peito voltando a 'respeito'.
- **evidencia:** anime_tts.py:2074 'texto = _seguro(line)' (online). Já anime_tts.py:796-810 (_texto_fish) é usado em 1358 (S2-Pro), 1667 (XTTS) e 1806 (Fish nuvem), nunca no online. O roteiro dos Shorts escreve 'com todo RES-peito' (anime_script.py:266), e o Fish online lê o hífen do jeito que vier.
- **proposta:** Em _narrar_online: 'texto, riso = _texto_fish(_seguro(line))' e guardar o riso para pôr _risada_real depois. Isso também economiza crédito, porque kkk, letras repetidas e reticências são caracteres pagos (1 crédito por caractere). Chave: reusar FISH_DUPLO_SENTIDO / FISH_RISADA_REAL, que já existem.
- **risco:** baixo
- **ja_existe:** _texto_fish existe (anime_tts.py:796). _pronuncia e o palavrão disfarçado já entram pelo _seguro (anime_tts.py:79-86, viralizador.py tem PALAVRAO_SUAVE).

### 16. [narracao-shorts-fish] Créditos: 320 mil/mês dão ~23 Shorts/dia, não 100. Falta um teto por dia até o dia 18 e uma ordem de prioridade

- **problema:** Sem teto, o Fish gasta tudo no ritmo que vier e acaba no meio do mês, ou (como agora) não gasta e perde a cota no dia 18. A ronda calcula o gasto com um número fixo (n_mp3 x 110), conta como gasto o mp3 que só foi reaproveitado do cache (os.utime) e soma 'restantes' sem descontar o gasto_desde_leitura.
- **evidencia:** creditos.json: 48 contas, 40 logadas, soma de restantes 330.923, lido_em entre 19/11 e 23/11. ronda_tarde.txt:76: 270.557 créditos, '100 Shorts/dia x ~900 car = 90.000/dia = ~3 dias'. creditos.py:21 MINIMO=300 ('um Short tem ~450 caracteres'). fish_http.py:130 os.utime(cache) no reaproveitamento. relatorio_ronda.py:1047-1050 (n3*110, soma 'restantes' crua). COMO_OPERAR.md:146-152: 1 crédito por caractere, 8.000/mês, renova dia 18.
- **proposta:** Conta: 40 x 8.000 = 320.000/mês; ~450 car/Short dá ~710 Shorts/mês, ~23/dia. Teto do dia = saldo_estimado_total / dias_até_o_próximo_dia_18, calculado no fish_lote.disponivel(). Passou do teto, o Short vai para a reserva. Prioridade dentro do teto: (1) Shorts agendados para 21-22 h (memória: horário nobre rende ~100x; sinais_shorts receitas hora 21 RECEITA 20,25); (2) canais com receita; (3) o resto. Economia sem perder qualidade: _texto_fish (achado 3) e roteiro curto (sinais 'curto' A=1,13 x B=1,06, n≈330 cada). Não usar prosody.speed≠1, que perde o histórico grátis. Não usar misto por frase Fish+p3 no mesmo Short: a dona reprovou emendas de motores diferentes ('parecem vários áudios emendados, até de pessoas diferentes', 20/11). Na ronda, ler o gasto real em creditos.json (gasto_desde_leitura) em vez de n_mp3 x 110. Nunca consultar saldo em laço de contas: só a conta escolhida, pelo IP dela, como já faz o fish_http.escolher.
- **risco:** baixo
- **ja_existe:** A escolha por crédito, o cache e o histórico grátis existem (fish_http.py:256-366, 124-143). Teto diário e prioridade não existem (grep teto/por_dia em fish_lote, fish_http e creditos: só o teto do cache).

### 17. [postagem-recuperacao] Metade da produção do dia vai para o Fato Chocante, que não consegue subir nada (perfil deslogado desde 20/11)

- **problema:** O youtube_web_poster devolve 'morto: perfil do navegador não está logado' para o Fato Chocante desde 20/11. Nada marca o canal como bloqueado, então a produção (parceiro.json, fila_alvo 7) e o postador continuam mandando vídeos para ele todo dia. O canal tem 5 vídeos e 8 views no total. Enquanto isso, os canais que se recuperaram ficam sem vídeo.
- **evidencia:** D:\tmp\ronda_tarde.txt: 'Shorts gerados hoje ... por canal: Fato Chocante 46, Mistérios Noturnos 17, Anime Noturno 15' (46 de 92). D:\postador-de-videos\logs\envios_por_maquina.jsonl (desde 20/11): fatochocante = morto 56, erro 7, ok 1. Por dia, 'não está logado': 20/11 21, 21/11 15, 22/11 8, 23/11 12; último registro 23/11 17:09. estado\canais_views_hist.jsonl 24/11 00:14: Fato Chocante 'views': 8, 'videos': 5. youtube_web_poster.py:450 levanta Falha('morto', ...), mas grep 'marcar_canal|token_morto' em youtube_web_poster.py dá 0 ocorrências: só o youtube_poster.py (API, linha 281) chama politica.tratar_erro. Há 11 video.mp4 pendentes do novo_fatochocante em animes recap\shorts (postar.json). D:\recapd-ambientes\producao\config\parceiro.json: Fato Chocante 'ativo': true, 'fila_alvo': 7 (conserto do vigia em 23/11).
- **proposta:** (a) No youtube_web_poster, quando o mesmo canal der 'morto' (perfil não logado / sem login no cofre) 2 vezes em 24 h, chamar politica.marcar_canal(canal, 'token_morto', ...). O bloqueio cai sozinho no relogin pelo token_hash. Se o hash não servir para o web, criar uma lista 'login_pendente' com validade de 24 h. O parceiro_diario já consulta pol.motivo_bloqueio (parceiro_diario.py:1394), então a produção para sozinha. (b) Avisar a dona uma vez (Telegram) que o Fato Chocante precisa de --logar, e só com ela: a conta é comprada/vietnamita e não pode ser logada de outro IP. (c) Mandar as vagas de produção desse canal para Anime Noturno, Mistérios e Tech, que estão recuperados.
- **risco:** baixo
- **ja_existe:** Existe para a API: politica.tratar_erro marca token_morto (politica.py:1087-1096). Para o poster web não existe. O vigia (vigilancia.py) não tem caso para 'perfil não logado'.

### 18. [redes-tiktok-insta-fb] Medição parcial do TikTok (6 de 58) derruba o teto das contas fortes no mesmo dia

- **problema:** TIKTOK_AMPLIFICAR lê sempre o arquivo mais recente de logs/tiktok_views, sorted(glob)[-1]. Em 23/11 o medir_tiktok travou: o arquivo tem só 6 contas e não há 'exit=' no log. A partir dele nenhuma conta forte foi achada, e filmenoturno, inovarecap e fabricadeautomacoesia voltaram a 4/dia. O tiktok_pausar_zeradas, o vigia_tiktok_ip e o relatório também leem esse arquivo.
- **evidencia:** postar_tiktok_auto.py:359-366: `ult = sorted(...glob('*.json'))[-1]`. logs/tiktok_views/2026-11-23.json: 6 contas, só 2 com abriu=True (jornalcomia, emersonjosiel2026), lido até 09:48. logs/medir_tiktok.log: '[23/11/2026 7:34:09] === medir tiktok ===' e depois só TimeoutNegativeWarning, sem exit=. Posts no tiktok_20261123.log: filmenoturno 4, contra 6 em 21/11 e 22/11. 00:08 de 23/11 (ainda com o arquivo de 22/11): 'fabricadeautomacoesia 6 de 19', 'filmenoturno 6 de 27'.
- **proposta:** Em filas(): usar o arquivo mais recente com cobertura >= 80% (abriu em >= 0,8 x contas da config) e, por conta, o último valor com abriu=True nos últimos 3 dias, em vez de [-1]. Fazer o mesmo nos leitores (vigia_tiktok_ip._med, tiktok_pausar_zeradas.ler_views, medir_tiktok.main 'anteriores'). No medir_tiktok.py, pôr um prazo total (ex.: 90 min) e gravar 'parcial': true quando parar. Chave, ex.: TIKTOK_MEDICAO_MINIMA=0.8.
- **risco:** baixo
- **ja_existe:** TIKTOK_MEDIR_ROBUSTO e MAX_FALHAS (medir_tiktok.py:78-79) param após 6 falhas, mas o arquivo parcial passa a valer como medição do dia para todos.

### 19. [redes-tiktok-insta-fb] vigia_tiktok_ip pausou contas fortes e nunca despausa; lista de 'boas' congelada em 12/11

- **problema:** Quando uma conta 'boa' cai 2 dias, o vigia pausa TODAS as outras do mesmo IP, inclusive contas fortes. Não há volta automática quando a boa se recupera. A lista _boas é de 12/11 e não inclui contas que cresceram depois (seebotsia, aulasrevolution, inovaremanhwaversehindi). Além disso, o 'normal' de fabricadeautomacoesia é julgado com dias em que a medição dela falhou ou foi parcial.
- **evidencia:** config/reuso_plataformas.json: seebotsia e emersonjosiel2030 pausadas em '21/11: vigia_tiktok_ip — a boa inovarecap do IP 8 caiu'; inovaremanhwaversehindi, canalalucinaai, inovaremultiatendimento e inovaremanhwaverseind pausadas por 'a boa fabricadeautomacoesia do IP 3 caiu'. logs/tiktok_views/2026-11-21.json: seebotsia 2878 views (2ª maior), inovaremanhwaversehindi 1583 (5ª). logs/vigia_tiktok_ip.json: 22/11 'IP 8 inovarecap: hoje 315 | normal 336.4 | ok' (recuperou), mas as pausas continuam. vigia_tiktok_ip.py:101-110 só põe 'pausada', nunca tira. proxy_tiktok.json _boas 'em': '20261112_0753'. Estoque preso: seebotsia 38 vídeos.
- **proposta:** (1) Não pausar conta cujo ganho próprio, medido por vídeo como ganho(), é >= o da boa ou >= MIN_NORMAL. (2) Quando a boa voltar a 'ok' por 2 dias, tirar só as pausas com motivo 'vigia_tiktok_ip' daquele IP e avisar. (3) Recalcular _boas a cada 7 dias com o ganho por vídeo, 1 por IP. Fazer dentro do mesmo script, guardando backup como já faz (.bkp_vigia_*). Despausar exige o OK da dona, pela regra da memória 'não pausar/consertar sem falar com a dona': levar a proposta a ela.
- **risco:** medio
- **ja_existe:** Vigia existe (VigiaTikTokIP, VIGIA_TIKTOK_IP=0 desliga); falta a volta e a atualização das boas.

### 20. [redes-tiktok-insta-fb] aulasrevolution (3ª maior do TikTok) ficou 3 dias sem post: conta VIVA do Kaggle sem fonte própria

- **problema:** A conta só recebe vídeo pela reserva Veo (sem temas, projetos ou postados_em). Desde que virou conta viva do Kaggle, só pode postar no PC1 pela ponte. Em 20/11 o post saiu depois de 3 máquinas recusarem. De 21 a 23/11 ela nem entrou na fila. Situação parecida: doramanoturno (2ª maior, sem_proxy) recebe 1 vídeo por dia porque depende só do canal Dorama Noturno.
- **evidencia:** config/reuso_plataformas.json l.482-492: aulasrevolution só tem cofre, _obs 'Veo de reserva' e maquina. logs/tiktok_20261120.log 08:38: 'desktop/x200ma/acer: aulasrevolution é conta VIVA do Kaggle — não abre Chrome fora do IP fixo dela' e depois 'OK #2 (aulasrevolution)'. grep aulasrevolution: 0 linhas em tiktok_20261121/22/23.log. tiktok_views/2026-11-22.json: aulasrevolution 4270 views (era 1945 em 15/11). Log 23/11: 'doramanoturno 1 de 1 disponiveis'.
- **proposta:** Dar a aulasrevolution e doramanoturno uma fonte fixa ('postados_em' ou 'projetos' de canais afins com estoque), junto com a redistribuição do achado 2. Para aulasrevolution, tirar 'maquina' remota da lista (já é recusada) para não gastar 3 tentativas, e deixar só o PC1 pela ponte (cofre.saida_kaggle). Mudar o que a conta posta é decisão da dona: perguntar qual tema.
- **risco:** baixo
- **ja_existe:** Trava Kaggle em maquina_remota.py:216 e postar_tiktok_auto.py:209 (correta); falta a fonte de vídeo.

### 21. [redes-tiktok-insta-fb] Facebook: rodada estoura 55 min tentando baixar do Drive vídeos que não existem mais

- **problema:** postar_facebook_paginas.postar_um tenta até 15 candidatos. Cada um chama catalogo.baixar (rclone até 120 s). As cópias de parceiro/2_tiktok e _postados_lote_1011 falham sempre e, diferente do TikTok, não são marcadas como puladas. Resultado: a rodada passa do prazo e a Página posta 0.
- **evidencia:** logs/facebook_paginas.log (desde 20/11): 192 'não baixou' (112 de parceiro/2_tiktok, 66 de _postados_lote_1011, 8 de 3_instagram); 12 '(rodada passou de 55 min — encerrada)'; as mesmas sem-obra-5b80bf e sem-obra-6b7df3 falham em 17:21 e 23:27 de 23/11; '[Bicho Noturno] ... hoje 0/3'. postar_facebook_paginas.py:118-126: `except Exception as e: print('não baixou:', str(e)[:150]); continue`, sem registrar. O TikTok já resolve isso: postar_tiktok_auto.py ~l.494-502 (catalogo.pular quando 'directory not found') e drive_falhas >= 3 = só vídeos do PC.
- **proposta:** Copiar a mesma lógica para o FB: no except, se a cópia não existe, gravar reg['pulados'][caminho] (que candidatos() já lê, l.66) e, após 3 falhas do Drive na rodada, só candidatos com no_pc. Gravar a mensagem inteira (não cortar em 150) para saber o motivo. Chave, ex.: FB_PULA_DRIVE_FORA=0.
- **risco:** baixo
- **ja_existe:** Feito no TikTok (07/11 e 03/11), não no Facebook.

### 22. [tarefas-agendadas] Renders longos no PC1 por tarefa com limite de 72 h e IgnoreNew prendem a fila

- **problema:** ComentariosProducao (ciclo de 2 h), CaparShorts (15 min) e Cortes_Juri (30 min) rodam no PC1 com ExecutionTimeLimit de 72 h. Uma rodada fica viva por 5 a 7 h, e todo disparo seguinte é recusado. O PC1 fica ocupado a madrugada toda, o oposto da regra 'PC1 livre pro VS Code'. Nenhum dos três entra no MatarTravados, que só olha hiper-pipeline/hiper-longo/anime-pipeline/anime_auto, nem no PESADOS_PC1 do controlador, então o controlador nem conta esses processos como render.
- **evidencia:** Processos vivos às 06:25 de 24/11 (Win32_Process): 'producao.py ciclo' desde 23/11 22:52, 'capar_shorts.py' desde 24/11 00:14 e 'cortes_juri.py rodar' desde 01:16. COM: ComentariosProducao, CaparShorts e Cortes_Juri com LastTaskResult 0x800710E0. XML: <ExecutionTimeLimit>PT72H nos três. D:\video-fila\matar_travados.py:27 (regex 'hiper-pipeline|hiper-longo|anime-pipeline|anime_auto'). D:\video-fila\controlador.py:72-73 (PESADOS_PC1 sem producao.py, capar_shorts e cortes_juri). D:\videos-comentarios\logs\producao.log, 05:56: 'rclone copy falhou 3x (timeout)', ou seja, o ciclo fica parado esperando o Drive.
- **proposta:** Baixar o ExecutionTimeLimit para o tempo real de uma rodada (por exemplo 2 h no ComentariosProducao, 1 h no CaparShorts e no Cortes_Juri). Pôr 'producao.py ciclo|capar_shorts|cortes_juri' no PESADOS_PC1 e no regex do matar_travados (só mata se a CPU estiver parada, como já faz). O render pesado de comentários pode ir para fora do PC1 (teste_remoto/desktop).
- **risco:** baixo
- **ja_existe:** prioridade_vscode.ps1 já baixa a prioridade de capar_shorts (linha 17), mas não cobre producao.py ciclo nem cortes_juri, e não impede a fila travada.

### 23. [vigia-relatorio] URGENTE da vigilância nunca sai na hora: cai no resumo das 9/14/21 h

- **problema:** O aviso '🚨 URGENTE: <processo>: sem sucesso há N h' passa por avisos.enviar com importante=True, mas o portão só segura e manda erro quando o texto bate com ERRO_RX. 'sem sucesso' não bate, então vira importante=False e vai pro resumo. O carrossel MS Energy (66 h → 78 h) nunca chegou como alerta imediato.
- **evidencia:** D:\video-fila\estado\avisos.jsonl: 23/11 10:40:40 e 22:56:25 'URGENTE: Carrossel MS Energy' situacao="resumo"; 16:40:47 e 24/11 05:02:20 situacao="repetido". Mesmo destino para 'URGENTE: Shorts no PC2', 'TikTok' e 'Gemini sem navegador' (resumo). avisos.py:183 ERRO_RX (erro|falh|parou|caiu...; sem 'sem sucesso'); avisos.py:511-512 'if not _e_erro: importante = False'; vigilancia.py:620-621 manda o URGENTE.
- **proposta:** Mandar o URGENTE por uma origem que sai sempre (pôr 'vigilancia-urgente' em SEMPRE_NA_HORA) ou incluir 'sem sucesso há' / '🚨' no ERRO_RX. Deixar uma chave de ambiente pra voltar ao comportamento antigo (ex.: VIGIA_URGENTE_DIRETO=0).
- **risco:** baixo
- **ja_existe:** O URGENTE existe desde 20/11 (vigilancia.py:618), mas na prática fica mudo por causa do filtro AVISOS_SO_ERRO_ABERTO de 11/11.

### 24. [vigia-relatorio] notificar_telegram preso desde 03:14: liberar_esperas não roda e o aviso de disco a 6 GB ficou retido

- **problema:** liberar_esperas() só é chamada dentro de despachar_resumo(), e quem chama é a tarefa NotificarTelegram. A execução das 03:14 não terminou (2 pythonw vivos com CreationDate 03:14 e telegram.log parado em 03:15). As seguintes são recusadas porque a anterior ainda roda. Resultado: a fila 'espera' acumula, incluindo 'Disco D com apenas 6.05 GB livres' das 03:09 e 5 alertas de TikTok 0 posts. Nada vai pro Telegram e nada vigia esse travamento.
- **evidencia:** Get-ScheduledTaskInfo NotificarTelegram: LastRunTime 05:34, LastTaskResult 2147946720 (0x800710E0, instância recusada); Win32_Process pythonw notificar_telegram.py PIDs 24632/22884 criados 24/11 03:14:00; D:\postador-de-videos\logs\telegram.log última linha [24/11 03:15]; D:\video-fila\estado\avisos_estado.json 'espera' com 6 itens de 03:08 a 05:09 (vídeos: Disco D 6.05 GB; vigia-postagem TikTok 0 posts); avisos.py:665-666 (único chamador de liberar_esperas).
- **proposta:** Tirar liberar_esperas do processo pesado: chamar a função na própria volta do vigilancia.py ou numa tarefa leve separada. Pôr um prazo (timeout) no notificar_telegram e cadastrar 'telegram.log' em config_processos_vigiados.json com max_h=1. Essa vigilância precisa sair por outro caminho, que não dependa do Telegram travado.
- **risco:** baixo
- **ja_existe:** A espera de 30 min existe desde 11/11 (avisos.py:513-515, ESPERA_ERRO_MIN), mas nada vigia quem a esvazia.

### 25. [vigia-relatorio] Problema que precisa da dona (checkpoint) é reaberto e rediagnosticado a cada 6 h

- **problema:** O carrossel MS Energy está parado por checkpoint do Instagram (precisa de login humano). O próprio carrossel_ms.py já sabe disso, grava checkpoint_ig.json e pausa. Mesmo assim, o vigia abriu 4 casos (10:40, 16:40, 22:56, 05:02) e gastou o Gemini 4 vezes pra chegar sempre a 'REAL — checkpoint'. Depois mandou pro consertador de código, que não tem como resolver. O caminho certo seria 'dona' + aviso humano.
- **evidencia:** vigilancia_casos.jsonl: casos 20261123_104034_300, _164034_300, _225055_300 e 20261124_050044_300 com diagnóstico 'carrossel_ms.py:423 — checkpoint (OAuthException 190)'. vigilancia.json: os 3 primeiros estão em etapa=consertar. D:\ms-energy\bin\carrossel_ms.py:493-529 (marca checkpoint_ig.json + aviso). vigilancia.py:575-577 (REPETIDO_H=6 abre caso novo).
- **proposta:** No med_sem_sucesso, se existir marca de pausa humana (checkpoint_ig.json ou um campo 'pausa_humana' no config_processos_vigiados.json), abrir direto em etapa 'dona' com 1 aviso _humano_ok ('conta @msenergycap precisa de login') e não reabrir enquanto a marca existir. O mesmo vale quando o diagnóstico do vigia trouxer checkpoint/login/senha.
- **risco:** baixo
- **ja_existe:** O carrossel_ms manda aviso de checkpoint 1 vez (avisos.jsonl 23/11 18:42), mas ele também caiu em situacao="resumo".

### 26. [vigia-relatorio] Sem medidor de disco no vigia, e o relatório mostra disco errado (22-28 GB contra 6 GB reais)

- **problema:** vigilancia.py não tem medidor de disco. A ronda mostra 'Disco D livre 22,7 GB' nos Números e '28.3 GB (lido 16:02)' no gerente. Hoje o D: está com 6,3 GB (abaixo do mínimo de 8 GB). O inventário das 02:59 já dizia 6.5 GB e D:\tmp sozinho ocupa 13 GB 'SEM regra automática'. O único alerta veio do vigia_geral e ficou preso na espera (achado 2).
- **evidencia:** df /d: 6.3G livres (167G). D:\video-fila\estado\inventario_videos.json em=2026-11-24T02:59:50 livre_gb=6.5, outras['D:\\tmp']=(101 vídeos, 13.0 GB). grep 'disco|disk' em vigilancia.py = 0 ocorrências. relatorio_ronda.py:1011-1032 (sec_videos_disco só mostra a hora da leitura, sem alerta de mínimo).
- **proposta:** Criar med_disco: livre < 10 GB vira alarme urgente com o top 3 pastas do inventario_videos.json, e o caso vai direto pro faxina/gerente_videos, sem IA. Na ronda, pôr '🔴 abaixo de 8 GB' na linha do disco e mostrar a idade da leitura do inventário quando passar de 2 h.
- **risco:** baixo
- **ja_existe:** Existem gerente_videos.py (GerenteVideos 2/2 h) e o incidente 'disco' do avisos.py (avisos.py:105), que só fecha. O alarme de disco abaixo de 8 GB está no vigia_geral, preso na espera.

### 27. [vigia-relatorio] Longo reenviado 19 vezes sem ninguém avisar: só existe o prazo de 36 h pro último ok

- **problema:** O processo 'Longos no YouTube' só alarma após 36 h sem 'ok: https'. Como algum longo sobe a cada 1-2 dias, o alarme nunca dispara, enquanto o mesmo título é reenviado dezenas de vezes e cai em 'erro DEPOIS de subir (406 min) — pode ter ficado rascunho'. Isso gasta o PC1 por horas e pode deixar rascunhos duplicados. Nenhum medidor conta tentativas por título.
- **evidencia:** D:\recapd-ambientes\producao\colab\postar_longos.log 17-24/11: 'subindo: ELE FOI REJEITADO pela amiga...' 19x, 'ELE FOI TRATADO COMO SERVO...' 9x, 'HUMILHADO PELA NAMORADA...' 5x; 5 'erro DEPOIS de subir' entre 20 e 24/11 (ex.: [23/11 22:58] RzoyNcnlIj8... 406 min). Só 7 'ok: https' de 20 a 24/11. config_processos_vigiados.json: Longos max_h=36.
- **proposta:** Criar med_longos_tentativas: o mesmo título com 3 ou mais 'subindo' em 48 h sem 'ok', ou qualquer 'erro DEPOIS de subir', abre alarme com o título e o canal. Na ronda, uma linha 'Longos tentando subir: N títulos, maior X tentativas'.
- **risco:** baixo
- **ja_existe:** Só o prazo de 36 h (config_processos_vigiados.json). LONGOS_MELHORIAS.md não foi conferido por este achado.

### 28. [visual-shorts] Placar fechou T6 (fx_choque=B) e T8/T11 comparando braços placebo; sinal 'raio azul 1,31x' vem só de 28/10-01/11

- **problema:** O placar_variantes pega o braço do dicionário 'variantes' quando o _testes_usados.json não existe. Assim, cerca de 1.100 Shorts sem efeito contaram como 'fx B'. O 'PRONTO PARA DECIDIR' de fx_choque (p=0,954) é ruído entre dois grupos iguais. O 1,31x do raio_00d1ff em sinais_shorts.json vem dos únicos ~52 vídeos em que o efeito realmente saiu (28/10 a 01/11, com veredito 'SORTE' em receitas).
- **evidencia:** placar_variantes.py:118-123 (v = vdict[nome]; só troca por tu[campo] se _testes_usados.json tiver valor) e :133-134. placar_cortes_testes.json (gerado em 17/11 20:44): fx_choque B n_medidos=551, p_melhor_que_ref_ajustado=0,954, 'PRONTO PARA DECIDIR'. cortes_ajustes.json historico 2026-11-17T20:55: 'fx_choque ab -> B | T6 fechado'. sinais_shorts.json: fx_choque raio_00d1ff n=52 razao_med=1,31; receitas: fx_choque raio_00d1ff veredito 'SORTE' (n_antigos 42, n_recentes 10).
- **proposta:** No placar_variantes, para os campos de CAMPO_RENDER (fx_choque, mascote, gancho_remotion), contar como B só os vídeos com _testes_usados.json, ou seja, efeito realmente renderizado. Sem esse arquivo, o vídeo vai como 'nao_renderizado' e fica fora da comparação. Reabrir T6 depois de portar o efeito (achado 1) e registrar no historico do cortes_ajustes que o fechamento de 17/11 foi feito sobre placebo.
- **risco:** baixo
- **ja_existe:** O placar já trata o 'A_falhou' do render (nota em gancho_remotion/mascote), mas não trata a falta do arquivo.

### 29. [visual-shorts] Cerca de 40% dos Shorts de 22-23/11 ainda sorteiam testes FECHADOS (curto, fx_choque, ninguem_esperava): config ou código antigo em outra máquina

- **problema:** No PC1, o cortes_ajustes.json fixa curto=B e ninguem_esperava=A desde 17/11. Mesmo assim, uma parte grande dos Shorts novos ainda sai com curto=A (versão longa, perdedora) e com 'NINGUÉM ESPERAVA' proibido (braço B, perdedor). Esses vídeos também não têm o teste T13 'abertura', o que bate com uma cópia antiga do variantes.py e do cortes_ajustes.json no produtor.
- **evidencia:** cortes_ajustes.json (PC1): "curto": "B", "ninguem_esperava": "A", "fx_choque": "B". Pastas *_20261122 e *_20261123: 219 com variantes = abertura,fala_rapida,gancho_meio,gancho_remotion,mascote,saudacao (config atual, curto=B 219/219) e 151 com variantes = curto,fala_rapida,fx_choque,gancho_meio,gancho_remotion,mascote,ninguem_esperava,saudacao (config antiga: curto A=72/B=79, ninguem_esperava A=91/B=60; 103 das 151 sem 'abertura'). Nos últimos 5 dias: curto A=348 de 1.223 e ninguem_esperava B=308. _sync_bin.py:8-12 sincroniza para o PC2 (C:\recapd-e-animes\bin) só 7 .py, sem cortes_ajustes.json e sem variantes.py.
- **proposta:** Descobrir qual produtor grava os 151 (PC2/desktop/Kaggle/celulares, a partir do log de cada máquina e não por ssh em rajada) e incluir cortes_ajustes.json e variantes.py na sincronização do bin dessas máquinas. Também gravar no postar.json a máquina que renderizou e a versão do cortes_ajustes (hoje nenhum metadata.json/postar.json diz a origem).
- **risco:** baixo
- **ja_existe:** _sync_bin.py existe, mas com lista fixa curta (FILES) que não inclui a config dos testes.

### 30. [aprendizado-metricas] A/B dos Shorts nunca fecha sozinho: placar parado desde 17/11 e testes 'sem diferença' eternos

- **problema:** O placar_variantes só escreve o .md e diz 'Não muda nada sozinho'. Nenhuma tarefa o roda: só 3 testes foram fechados, à mão, em 17/11. Seis testes seguem 'ab' com 300+ elegíveis por braço e 'sem diferença clara', ou seja, gastam sorteio para sempre sem decidir. horario_fraco ainda sorteia, embora o médico e o politica já forcem a hora nobre.
- **evidencia:** linhas/CORTES/placar_cortes_testes.json 'gerado': '2026-11-17 20:44'. bin/placar_variantes.py:12 'Não muda nada sozinho'. Nenhuma tarefa agendada chama placar_variantes (busca nas Actions). cortes_ajustes.json: gancho_meio/gancho_remotion/mascote/fala_rapida/saudacao/horario_fraco = 'ab'. Placar: gancho_meio A 346 x B 322 elegíveis, P_ajustado(B>A)=0.78; saudacao 299/310, P=0.83; fala_rapida 323/324, P=0.35. O histórico de cortes_ajustes mostra fx_choque→B, curto→B e ninguem_esperava→A em '2026-11-17T20:55' pelo 'chat ronda'.
- **proposta:** Tarefa diária oculta (rodar_oculto.vbs) 'DecisorAB': roda placar_variantes e aplica a régua que já existe. PRONTO (D3+D16, P>=0,95) → grava o braço vencedor. Com n>=200 por braço e 0,2<P<0,8 → EMPATE, fixa o braço A (o padrão, mais barato) e libera a vaga. Grava em cortes_ajustes.json com linha no 'historico' (quem='decisor_ab', porque=número) e avisa no relatório. Chave DECISOR_AB=0. Não é o melhorador (pausado): é uma regra fixa, sem LLM.
- **risco:** medio
- **ja_existe:** A régua D1/D3/D16 e o cálculo de P existem em placar_variantes.py. Falta rodar e aplicar.

### 31. [aprendizado-metricas] Loop mínimo proposto: medição → decisão automática (amarra os achados)

- **problema:** Cada medidor escreve um .md diferente para a dona ou o melhorador ler, e com o melhorador pausado ninguém decide. As decisões que de fato mudaram algo desde 17/11 foram manuais (histórico de cortes_ajustes.json) ou do médico.
- **evidencia:** Saídas só-leitura: placar_cortes_testes.md, AB_RESULTADOS.md, RECEITAS_DO_SUCESSO.md, TESTES_VOZ_RELATORIO.md, MEDICO.md. Decisores automáticos ativos: inteligencia_ajustada (peso de fonte e voz), foco aplicar (canal x tipo) e medico_recuperacao. Os três dependem de metricas_studio.json, que está em colapso (achado 1).
- **proposta:** Um único job diário oculto, após o MedicoRecuperacao (≈07:30): 1) atualizar views (Studio, ou API pública como reserva) → 2) analise_sinais_shorts --json + placar_variantes + placar de longos → 3) decisor com régua fixa (vencedor, empate, 'nao_funciona', controle sorteado) gravando em cortes_ajustes.json e config/longo.json com histórico, sempre reversível → 4) bloco 'Decisões automáticas de hoje' no relatorio_ronda, com o número que justificou cada uma. Sem LLM e sem conta, só arquivos locais. Chave geral DECISOR_AUTO=0.
- **risco:** medio
- **ja_existe:** As peças existem (placar_variantes, analise_sinais_shorts, medico, inteligencia_ajustada). Falta o orquestrador e a escrita da decisão.

### 32. [arquitetura] Ciclo de dependencia video-fila <-> postador/bin (e cofre/kaggle_pool como hubs ocultos)

- **problema:** Orquestracao e postador se importam mutuamente por caminho fixo; mexer em politica.py/catalogo.py (postador) derruba o controlador, e mexer em avisos.py/controle.py (video-fila) derruba o postador. Nao ha fronteira clara de quem e dono de que.
- **evidencia:** Matriz de imports (grep '^from X import|import X'): politica = 31 arquivos no postador, 29 no video-fila, 4 manhwa-react, 4 hipercool-videos; catalogo = 9 postador, 21 video-fila; youtube_web_poster = 6 postador, 8 video-fila, 3 manhwa-react, 2 recapd/bin; avisos (mora so em video-fila/avisos.py) = 27 no postador, 7 recapd/bin, 5 colab, 4 comum; controle (video-fila) = 2 recapd/bin, 1 postador. cofre.py mora em D:\logins-google (fora do mapa) e 'logins-google' aparece em 85 arquivos. colab/kaggle_pool.json e lido por 13 arquivos fora do colab.
- **proposta:** Nao mover nada ainda. Passo 2 (apos caminhos.py): declarar 4 'contratos' com dono fixo e importar so por eles: avisos+controle (dono video-fila), politica+catalogo (dono postador), cofre.saida_kaggle (dono logins-google), kaggle_pool (dono colab). Escrever em D:\video-fila\aprendizado\LEIA_ANTES_DE_MELHORAR.md a tabela 'modulo -> dono -> quem pode importar'. So depois, um a um, mover o modulo-contrato para comum\ deixando no lugar antigo um arquivo de 2 linhas 'from comum_x import *' (o import antigo continua valendo).
- **risco:** medio
- **ja_existe:** controle.py (video-fila/controle.py:1-20) ja e o liga/desliga unico; nao ha documento de dono por modulo.

### 33. [codigo-morto] 254 scripts .py que nada chama (nenhuma tarefa, import, .bat ou .vbs)

- **problema:** Scripts de uso único, sondas e testes ficaram na pasta de produção. Atrapalham o grep e a leitura dos chats e dos auditores, e alguns falam como conta se forem rodados por engano (por exemplo fb_tentar_login.py, kaggle_ver_conta.py, _tmp_ver_kaggle_conta.py, logar_pool_noite.py).
- **evidencia:** Saída da varredura: 254 arquivos com 0 menções pelo nome e ausentes das 224 tarefas. Grupos principais: video-fila\_tmp_*.py = 34 arquivos (129 KB, de 07/11 a 17/11). postador\bin\fb_*.py = cerca de 33 sem uso dos 50 fb_*.py (os .bat do Facebook só chamam fb_escada, fb_medir e fb_saturacao, segundo cron_facebook_inteligencia.bat). fish_audio\: capturar_fish, criar_fish_proton, criar_fish_temp, criar_proton_fish, fazer_referencia, logar_dona, logar_pool_noite, mao_real, relatorio_fish, importar_token_desktop. comum\_drive_*.py (8 arquivos de 11/11) + drive_chave_cloud.py (20 KB). producao\bin\: audit_*.py (8), patch_*.py (4), teste_*.py (11, de 13/11), postar_lote_inovaremanhwabr.py, postar_todos_canais_manhwa.py, postar_deitados_todos13.py e postar_animes_ate_bloquear.py. colab\: abrir_colab, abrir_prontos, kaggle_contas_novas, kaggle_abrir_conta e vps_baixador.
- **proposta:** Mover em lote (só depois do OK da dona) para <pasta>\_arquivo\AAAA-MM\, guardando a lista. Os scripts que falam como conta (fb_*login*, kaggle_*conta*, logar_*) vão primeiro, porque assim ninguém roda por engano um caminho que não passa por cofre.saida_kaggle. Não apagar.
- **risco:** baixo
- **ja_existe:** Não há pasta _arquivo nessas pastas e nenhuma rotina move _tmp_*. A memória 'Testes temporários' (testes.py) cobre testes de imagem, não scripts _tmp_.

### 34. [codigo-morto] Cópia antiga do pipeline manhwa dentro do postador: 80 módulos com o mesmo nome do producao\bin, 42 já diferentes

- **problema:** postador-de-videos\bin guarda a cadeia manhwa de julho (hiper-pipeline, queue-runner, night-shift-driver, dual-pipeline, claude_client...). Os nomes são iguais aos do producao\bin com conteúdo diferente. Quem fizer import com o sys.path errado pega a versão velha, e o grep de um auditor ou chat cai no arquivo errado.
- **evidencia:** Comparação md5: producao\bin x postador\bin têm 80 nomes em comum, 38 idênticos e 42 diferentes. Exemplos: claude_client.py tem 32.193 B (bin, 16/11) contra 17.221 B (postador), e censura_visual.py tem 21.358 B contra 15.893 B. Nenhuma das 224 tarefas roda queue-runner, night-shift-driver, dual-pipeline ou o hiper-pipeline do postador (grep no CSV vazio). postador\bin\fix_indent.py:1 abre 'D:/hipercool-inferior-fix/bin/hiper-pipeline.py', pasta que não existe mais. narration_ensemble.py tem 0 referências, e claude_client.py só é usado por gemini_llm, haiku_helpers e narration_ensemble.
- **proposta:** Marcar o grupo manhwa-julho do postador (hiper-*, queue-runner, night-shift-driver, dual-pipeline, tia-fetcher, narration_ensemble, fix_indent, panel-splitter, landscape-compiler e o que só eles importam) e mover para postador\bin\_arquivo_manhwa_jul\. Antes, conferir que o postador ativo (youtube_web_poster, politica, produto\) não importa nada dali. Já sei que gemini_llm é usado por curadoria.py e postar_tudo_hoje.py, então é preciso olhar caso a caso.
- **risco:** medio
- **ja_existe:** Não existe nota de decisão sobre isso.

### 35. [disco-arquivos] GerenteVideos travado: python órfão desde 04:01 segura a trava, a rodada das 05:53 morreu e o inventário está parado em 02:59

- **problema:** A tarefa tem limite de 2 h (ExecutionTimeLimit PT2H). Quando o Windows encerra a tarefa, ele mata o wscript do rodar_oculto.vbs, mas o python.exe filho continua vivo. Esse processo segura D:\limpeza_c\travas\gerente_videos.lock, e as rodadas seguintes saem sem fazer nada até a trava ficar com mais de 3 h (trava.py VELHA_S). Na prática, a limpeza fica 4 h ou mais sem rodar justo com o disco em 6 GB.
- **evidencia:** O schtasks GerenteVideos mostra a última execução em 24/11 05:53:26 com resultado 267014 (encerrada), MultipleInstances=IgnoreNew e ExecutionTimeLimit=PT2H. O processo 17388 (`python gerente_videos.py --limpar`) foi criado às 04:01:27; às 06:30 tinha CPU de 11 s e I/O parado (ReadOperationCount 4830 igual em duas leituras com 5 s de intervalo) e não tinha filho além do conhost. O gerente_videos.lock contém '17388 1795503777' (04:02). INVENTARIO_VIDEOS.md e inventario_videos.json são de 02:59. A última linha do logs\gerente_videos.jsonl é de 2026-11-24T01:56:28. Em D:\limpeza_c\trava.py, VELHA_S = 3 * 3600.
- **proposta:** (1) Pôr um timeout em toda operação que pode pendurar: rclone com `--timeout 60s --contimeout 20s`; o subprocess.run do R8 já tem 120 s, mas o rclone_move_conferido tem 7200 s por arquivo. Para o rglob das OUTRAS (inclui D:\tmp com 10 GB), usar um os.walk que pula pastas gigantes ou que tem limite de tempo. (2) Fazer o main gravar uma batida (`hora`) dentro do lock e fazer a trava considerar velha a rodada sem batida há 45 min, e não só depois de 3 h. (3) Colocar no rodar_oculto ou no próprio script um teto (por exemplo, sair sozinho aos 100 min) abaixo do PT2H, para não deixar órfão. Antes de mexer, conferir com py-spy/faulthandler onde o 17388 está parado.
- **risco:** baixo
- **ja_existe:** A trava C1 foi feita em 24/11 01:42 (D:\limpeza_c\noite\C1\progresso.md). Ela resolveu a sobreposição, mas criou este efeito: o processo órfão bloqueia por até 3 h. Não existe timeout global nem batida.
- **estado:** conferido 25/11: GerenteVideos rodou 13:53 com resultado 0

### 36. [disco-arquivos] D:\caches\c_movido: 14 GB, a maior parte de sessões de chats AUTOMÁTICOS (lapidar/produto_fila), marcada como 'NUNCA apagar'

- **problema:** A LimpezaDiariaC move o histórico de chats parados do C: para D:\caches\c_movido\claude_projects por junction, e ninguém limpa lá. Das 723 pastas, quase todas são sessões de trabalhos automáticos (lapidar r1/r2/r3, produto_fila, CORTES juri), não conversas da dona. Ocupam 13 GB num disco com 6 GB livres.
- **evidencia:** du: c_movido = 14 GB (claude_projects 13 GB, .rembg 1,3 GB). 723 subpastas; C:\Users\Haylla\.claude\projects tem 723 junções que apontam para lá. Por prefixo: 14 de claude-code-video-trabalhos-advance-novoestrela (lapidar-r1..r3), 7 de video-fila-produto-fila-futebolcom, 7 de msenergycap etc. A maior é D--postador-de-videos-remotion, com 1,7 GB. D:\limpeza_c\DISCO_LEIA_PRIMEIRO.md §3 diz 'Nunca: ... D:\caches\c_movido (histórico dos chats)'. donos.json: 'limpa: NUNCA apagar (histórico)'.
- **proposta:** Decisão da dona. Sugestão: separar as sessões de JOB automático (padrão '-trabalhos-*-lapidar-r', '-produto-fila-', '-linhas-CORTES-juri-' com mais de 7 dias) e mandá-las ao Drive com rclone move + check (manhwa-drive:arquivo-pc1/claude_jobs), deixando um _NO_DRIVE.md. Chats humanos continuam. O .rembg (1,3 GB de modelos) não é histórico: conferir se o rembg ainda usa esse caminho.
- **risco:** medio
- **ja_existe:** Existe a regra 'NUNCA apagar' (DISCO_LEIA_PRIMEIRO.md). Não há nada que diferencie sessão de job de chat da dona. Só a dona pode liberar.

### 37. [narracao-longos] O padrão XTTS 8 + S2-Pro 13 nunca foi produzido: o único misto é v2 e pegou 8% das frases

- **problema:** O config diz S2-Pro v13 com teto de 40% desde 23/11, mas o único longo misto pronto usou a v2, com teto de 25%. Nele a detecção de emoção mandou só 54 de 653 frases ao S2-Pro (8%). Quase tudo saiu no XTTS e a parte expressiva que a dona pediu (risada, piada) quase não aparece. O S2-Pro também é caro: 34 min só para montar o llama.cpp e o modelo, e cerca de 53 s por frase.
- **evidencia:** config\motor_voz.json: s2pro_versao '13', _padrao_23nov 'teto 40%'. na_nuvem\RzoyNcnlIj8_misto_xtts8_s2pro_momo\TESTE_NARRADORES.txt: motor {'s2pro_versao': '2'}. pipeline.log:89 '[s2pro] llama.cpp + modelo prontos em 2062s'. pipeline.log:178 'modo misto v2: 54/54 frases em 2879s (de 653)'. '[xtts] 597/597 frases em 3105s'. O pipeline foi de 08:48 a 13:41 (4h53). anime_tts.py:1351 teto 0,40 só na v13.
- **proposta:** Antes de tratar a v13 como padrão de fato, rodar 1 longo com ela e conferir no log o '[s2pro] modo misto v13: N/M'. A meta é N/M perto de 25 a 40%. Se ficar baixo, as regras _S2_EMO e _s2_tags_v13 (anime_tts.py:1229 e 1362) estão pegando pouco. Para cortar os 34 min de preparo, guardar o build do llama.cpp e o GGUF prontos no dataset ou cache do Kaggle. Não tocar no PC1.
- **risco:** baixo
- **ja_existe:** O modo misto existe (anime_tts.py:1325-1400). O que não existe é longo provado com a v13 nem cache do build.

### 38. [narracao-longos] Imagem parada de 55 a 62 s passa no QA e é postada

- **problema:** O QA dos longos detecta imagem congelada longa, mas o vídeo é postado mesmo assim. A regra é que só censura trava. Um trecho de 1 min com a imagem parada e só a narração por cima é o ponto clássico em que o público larga o vídeo.
- **evidencia:** 50 qa.json em na_nuvem\*: 18 com problema. e2nIzNGXvmA_xtts_momo 'imagem parada 2820–2881 s (61,7 s)'. 8pWoAFAT49w '496–553 s (57,4 s)'. Qet3goTGf0Q '3042–3097 s (55,0 s)'. 65WBxTrMYGQ '169–189 s (19,5 s)'. Quadro preto em LUQDew946Ps, SjQHP-0GKJs, McmTVgI6efk e 65WBxTrMYGQ. colab\postar_longos.py:339-358 (_avisar_qa): 'avisa e POSTA (regra da dona: só censura trava)'. bin\qa_video.py:6 freezedetect >= 6 s. render.json de e2nIz entre 2815 e 2885 s tem só 1 marca ('seta').
- **proposta:** Não travar a postagem, que é decisão da dona. O caminho é consertar antes do render. Trecho congelado acima de cerca de 15 s ganha zoom/deriva ou troca de cena (painel vizinho da fonte), aproveitando os ANIME_FX_MOV/DERIVA que já existem no perfil. Ou então o QA re-renderiza só esse trecho no Kaggle antes de subir. A ordem é a dona decidir se o limite é 15 s.
- **risco:** medio
- **ja_existe:** O QA e o aviso existem (qa_video.py e _avisar_qa, de 04/11). Não existe conserto automático do trecho congelado.

### 39. [narracao-longos] A retenção dos longos é de 1 a 4 min: o começo decide e o experimento do resumo está parado

- **problema:** A duração média assistida dos longos medidos vai de 37 a 248 s, ou 0,6 a 4,2% do vídeo. Quase todo o público sai nos primeiros minutos, então narração com energia, resumo/gancho e troca de voz no 1º minuto pesam mais que o resto. O experimento resumo_curto_gancho está em 0 x 0 vídeos.
- **evidencia:** postador _analise\metricas_studio.json ret_lista: ylUd-_4-GQ8 dur_media 185,7 s (3,4%), ozdALiyIDVY 248,4 s (4,15%), cIB4X-Q9MIk 70,4 s (2,07%), AjgJG8HAfLk 37,0 s (1,17%), uUqCHE_Dacg 38,0 s (0,59%), DCyOfv2lI2E 52 s (1,72%). D:\tmp\ronda_tarde.txt:147 'experimento resumo_curto_gancho: A 0 / B 0 vídeos analisados (precisa 2)'. Os 3 mais assistidos da ronda (linhas 84-86) têm 3:05, 4:08 e 2:09 de média.
- **proposta:** Pôr o S2-Pro (frases expressivas) e a troca de voz no resumo de abertura e no 1º minuto, sem espalhar por igual: o teto de 40% concentrado onde o público ainda está. Marcar a variante A/B do resumo no render.json para o experimento andar sem o melhorador, que segue pausado. A comparação sai da leitura do Studio do 1º achado.
- **risco:** baixo
- **ja_existe:** O resumo de abertura existe (resumo_fim.json, 'Resumo de abertura ✅' em 121 de 124). O experimento A/B existe, mas não tem dados. Não existe regra de colocar o S2-Pro no começo.

### 40. [narracao-shorts-fish] Fish online parou de narrar os Shorts desde 21/11, com 270-330 mil créditos parados

- **problema:** A regra da dona (Fish online primeiro nos Shorts) não está acontecendo. Os Shorts recentes saíram no p3 (kokoro/francisca + RVC). Os créditos estão sobrando, e eles vencem: a cota grátis renova no dia 18 sem acumular.
- **evidencia:** Cache do Fish (D:\hipercool-materiais\comum\fish_audio\cache, mtime): 18/11=47, 19/11=212, 20/11=167, 21/11=22, 22/11=0, 23/11=3. workspace\anime\_parceiro_2026112X.log: 'frases online em' = 17 em 20/11, 7 em 21/11 e 0 em 22, 23 e 24/11. Antes, todas eram pelo caminho do lote do Kaggle (lote_shorts_kaggle._fish_antes), que foi pausado em 21/11 13:40 (LONGOS_MELHORIAS.md:453, shorts_kaggle.json ligado=false). Últimos 300 animes recap\shorts\*\postar.json: motor_voz=None em todos; voz_base kokoro 209, francisca 72, misto 15. Os workspaces recentes (Jd5Drpvup 23/11, GTUW7 23/11, XMbSf 24/11) têm audio_cache\_base_clone\lista.json com 4-5 frases no lote do RVC e nenhum _voz_online.json. fabrica_fish.log de 23-24/11 tem vários 'Chrome da conta ... não abriu a porta em 45 s (PC lento?)' e 'reCAPTCHA Enterprise não carregou'. O jCV32N2H09M (22/11) caiu no RVC com 'DefaultCPUAllocator: not enough memory' (_base_clone\clone.log).
- **proposta:** Antes de portar qualquer técnica: (1) descobrir por que _narrar_online não gera no caminho LOCAL do anime_auto. A saída do anime-pipeline não aparece no _parceiro_*.log de 22-24/11, então falta um log: gravar uma linha '[online] Fish: N/M' também no parceiro_producao.log. (2) A fábrica falha por RAM/CPU do PC1 (Chrome que não abre em 45 s): aquecer a conta só quando a RAM livre for maior que ~1,5 GB e preferir contas com sessão HTTP já guardada (sessoes.json). (3) Pôr na ronda o número 'Shorts com Fish hoje / total' lido do postar.json motor_voz, em vez de contar o cache. Sem isso, nada do que vem abaixo chega ao ar.
- **risco:** baixo
- **ja_existe:** O caminho existe (anime_auto.py:987-995 põe VOZ_ONLINE=fish; anime_segments.py:556 também chama sem clone). O marcador motor_voz existe (anime_publish.py:350). O que falta é o diagnóstico e o aviso.
- **estado:** FEITO 25/11: narrador sumiu do Fish (404); trocado pelo ac63ad94 aprovado; Fish narra de novo

### 41. [postagem-recuperacao] Esteira de envio pelo PC quase parada: 5 ok contra 21 falhas em 23/11, e só o PC1 acerta

- **problema:** Fora o Fato Chocante, as falhas são timeouts do Playwright no Studio (Locator.click/wait_for) e o longo do Fio da Meada, que falha em todas as máquinas: 10 erros e 1 ok. O ledger mostra que os uploads do youtube_web_poster caíram de 117 (17/11) para 17-18/dia (21-22/11). Os canais recuperados não usam a rampa toda porque o envio não dá conta.
- **evidencia:** envios_por_maquina.jsonl, ok/falha por dia: 17/11 13/22, 18/11 4/52, 19/11 11/41, 20/11 12/26, 21/11 2/18, 22/11 2/27, 23/11 5/21. Falhas desde 17/11: pc1 'Locator.click: Timeout' 42, 'Locator.wait_for: Timeout' 26, 'idioma do Studio vi-vn' 14. ok por máquina: pc1 30, x200ma 12, hp 5, acer 1, pc2 1. logs\uploads_ledger.jsonl, youtube_web_poster.py por dia: 117, 71, 79, 63, 18, 17, 29 (17-23/11). Fio da Meada em 23/11: pc2 'TimeoutExpired ssh' (6,4 min, 3402 MB) e pc1 'Locator.wait_for ytcp-uploads-dialog' (124,8 min, 3,64 Mbps).
- **proposta:** Separar a medida por classe: tirar 'morto' (achado 1) e o longo do Fio da Meada de 3,4 GB, que ocupa o PC1 por 2 h. Para o longo: recomprimir para menos de 1,5 GB antes de subir (1080p mínimo mantido) ou só tentar na máquina com mais banda. Os 42+26 timeouts de seletor precisam de print no momento da falha (logs\envios_falhos já existe, politica.py:1326) para identificar o seletor quebrado. É um conserto de código no poster, com teste fora do PC1.
- **risco:** baixo
- **ja_existe:** Já existe: registro por máquina (_registrar_envio), envios_falhos, e o ?hl=pt-BR para o Studio em vietnamita (youtube_web_poster.py:442). Ainda assim o 'vi-vn' deu 14 erros em 19/11; não há esse erro depois de 19/11 no log.

### 42. [postagem-recuperacao] O so_nobre do médico vale só para upload novo, e os Shorts já agendados dos canais tratados continuam fora das 21-22 h

- **problema:** horario_publicacao (politica.py:640-648) só empurra o horário pedido de upload NOVO. Esses canais já têm Shorts agendados para os próximos dias fora do nobre, e o reagendar_nobre falha justamente neles. O médico mede o efeito 3 dias depois (DIAS_AVALIAR=3) e vai concluir que 'so_nobre não funciona' sem a alavanca ter valido. Esse rótulo vai para est['nao_funciona'] e desliga a alavanca para sempre (medico_recuperacao.py:183).
- **evidencia:** Ledger, Shorts que abrem entre 24 e 28/11 (calculado do publish_at): HistoriasEmFrames (so_nobre desde 23/11 11:33) tem 2 no nobre e 5 fora; Filme Noturno (so_nobre) 1 no nobre e 2 fora; Imóvel em Foco (so_nobre) 2 e 1. logs\reagendar_nobre.log 23/11 18:21: 'HistoriasEmFrames: DlClp8f5nTo ... metadata_update falhou' e 'Filme Noturno: ... cookies mortos'; 13:26: 'HistoriasEmFrames ... SSLError'. medico_recuperacao.py:43-45: DIAS_AVALIAR=3. Linhas 182-183: 'so_nobre' not in est['nao_funciona'].
- **proposta:** (a) O médico só começa a contar os 3 dias quando todos os Shorts agendados do canal estiverem no nobre ou depois do último agendado fora dele: gravar 't0_efetivo' na decisão. (b) Marcar como 'não aplicada' (em vez de 'não funciona') a alavanca cujo canal ainda tinha Shorts fora do nobre no período medido. (c) Para os que já estão agendados, priorizar o reagendar_nobre nos canais com so_nobre: hoje ele ordena por rendimento e pula o que não tem post no dia.
- **risco:** baixo
- **ja_existe:** Já existem o reagendar_nobre.py (tarefa ReagendarNobre 08:20/13:20/18:20) e o so_nobre em politica.horario_publicacao. Ainda não existe ligação entre o médico e o que já está agendado.

### 43. [redes-tiktok-insta-fb] Instagram posta pelo IP compartilhado do TikTok (3-9 contas por IP), contra a regra 1-conta-por-IP do Instagram

- **problema:** A exceção da dona (12/11) de dividir IP vale SÓ para o TikTok; no Instagram continua 1 conta por IP. Mas postar_insta_auto._ip_insta usa proxy_tiktok.ip_da_conta, o mesmo mapa de 10 IPs grátis do TikTok, onde cada IP tem ~9 contas. As contas em foco no Instagram saem pelo mesmo IP de várias contas do TikTok e de outras do Instagram.
- **evidencia:** postar_insta_auto.py:129-139 (_ip_insta -> proxy_tiktok.ip_da_conta) e 163-166, 279-282; comentário em postar_insta_auto.py ~l.159: 'o mesmo mapa do TikTok: proxy_tiktok.ip_da_conta'. config/proxy_tiktok.json: IP 4 = sintetizerisada (IG em foco) + canalhistoriacomia, crmchatwoot.ia, emerson20308.ia (IG) + emersonjosiel1995, emersonjosiel649, emersonjosiel2031, gameoftroneskingsroadbrasil, emersongencshin, inovaremanhwaverseing (TikTok); IP 2 = fakenews.ia4 + iapro.mentoria + inovareclaw.ia (3 IG) + jogoscomia, inovaremanhwabr, inovaremanhwaverseviet etc. Memória project_tiktok_ips_compartilhados.md: 'Kaggle, Google, YouTube e Instagram continuam 1 conta por IP'. proxy_tiktok.ip_da_conta (proxy_tiktok.py:63-70) aloca conta nova no IP menos usado, sem olhar a rede.
- **proposta:** Não mexer sozinho: levar à dona com esta prova. Opções: (a) dar às 4-5 contas do foco Instagram IPs Webshare próprios das contas novas com banda (há 16 no pool desde 19/11, ver memória project_webshare_contas_banda.md), com um mapa separado (ex.: config/proxy_instagram.json); (b) se a dona quiser estender a exceção do TikTok ao Instagram, registrar isso por escrito no reuso_plataformas.json. Até decidir, no mínimo fazer ip_da_conta recusar conta IG em IP que já tem outra conta IG.
- **risco:** baixo
- **ja_existe:** Proxy por conta já existe (INSTA_PROXY, PROXY_FORA), mas o mapa é o compartilhado do TikTok.

### 44. [redes-tiktok-insta-fb] Estoque do TikTok parado em contas mortas enquanto as contas com view ficam sem vídeo

- **problema:** catalogo._conta prende cada vídeo à 1ª conta cujo 'postados_em'/tema bate (canal do YouTube de origem). Contas ligadas a canais que produzem muito, mas com 0 view no TikTok, acumulam dezenas de vídeos. As contas que dão view ficam com 0 a 5. O teto (4/dia, 6 nas fortes) não se aplica porque não há o que postar. A reserva Veo só completa com Veo, e só quando sobra.
- **evidencia:** Catálogo salvo (config/catalogo_videos.json via catalogo.disponiveis('tiktok')): 571 disponíveis; revolutionemerson1 82, revolutionemerson2 58, emersonjosiel2027 51, emersonjosiel2033 25. logs/tiktok_views/2026-11-22.json: revolutionemerson1 0 views/48 vídeos, revolutionemerson2 0/24, emersonjosiel2033 0/24, curiosidadesnoturnas 0/24. Na mesma medição: doramanoturno 5765, aulasrevolution 4270, emersonjosiel649 2419. logs/tiktok_20261123.log 00:08: 'doramanoturno 1 de 1', 'emersonjosiel649 3 de 3', 'revolutionemerson1 4 de 91'. Posts em 23/11: doramanoturno 1, revolutionemerson1/2 4 cada. catalogo.py:328-347 (_conta: 1ª regra que bate ganha).
- **proposta:** No filas() de postar_tiktok_auto.py, depois de montar cand, mover o excedente: conta com views==0 e zerados==videos na última medição VÁLIDA (ver achado 3) fica com no máximo 1/dia, e o resto do estoque dela vai para as contas fortes do mesmo tema/afinidade, na ordem de views. Reaproveitar o padrão do reserva_veo.completar (rodízio) para qualquer projeto, não só Veo. Chave para desligar, ex.: TIKTOK_REDISTRIBUIR=0. O vídeo continua único por rede (catalogo já impede repetir). Respeitar o 'vídeo único por canal'.
- **risco:** baixo
- **ja_existe:** TIKTOK_AMPLIFICAR (teto 6 para quem tem >=300 views, postar_tiktok_auto.py:352-372) e reserva_veo.completar (só Veo, reserva_veo.py:93-150). Nenhum dos dois move estoque de conta morta para conta forte.

### 45. [tarefas-agendadas] 36 tarefas com 0x800710E0: disparos recusados viram ruído e escondem falha real

- **problema:** Mais de 1/3 das tarefas ligadas mostra 'último resultado' diferente de 0 só porque a rodada anterior ainda estava viva. Isso inclui ControladorVideos, EncherPilha, AlimentarPC2/PC3, BackupDriveVideos, HipercoolPostagem, ParceiroKaijinre-Postagem, LimpezaChrome e NotificarTelegram. Quem lê o Agendador (ou um vigia que cheque Último resultado) não distingue isso de erro. Somado aos ~615 disparos por hora, sobra muito processo wscript+cmd+python de curta duração no PC1.
- **evidencia:** estado_tarefas.txt (COM Schedule.Service, 24/11 06:2x): 36 linhas com 0x800710E0. Tarefas a cada 1-2 min: PlantaoTelegram (PT1M), LiberarRamVigia, PrioridadeVSCode e TunelCelularVPS (PT2M); a cada 5 min: mais 18 (xml.json). Processos duplicados na lista: 'controlador.py' duas vezes (06:00 e 06:02), 'encher_pilha.py' duas vezes (06:07 e 06:12).
- **proposta:** Para as de 5 min com rodada mais longa que o intervalo (ControladorVideos tem limite de 30 min com intervalo de 10, EncherPilha 20 min com intervalo de 5), alinhar intervalo e limite, ou juntar num laço só. No relatório ou vigia, tratar 0x800710E0 como 'ainda rodando' e não como falha, e alertar só quando a mesma instância passar de N vezes o intervalo.
- **risco:** baixo

### 46. [tarefas-agendadas] DriveChaveRenovar falha desde 16/11: a chave do Drive não renova

- **problema:** A tarefa de 5 em 5 dias que renova o token do rclone (manhwa-drive/conta32) falhou nas duas últimas rodadas. Se o token vencer, Drive, backup, reserva de Shorts e Kaggle param juntos. Isso pode explicar os 'rclone copy falhou (timeout)' de hoje, mas isso não está provado.
- **evidencia:** D:\hipercool-materiais\comum\drive_chave.log: '[16/11 04:22] FALHOU renovar: rclone authorize não deu o link' e '[21/11 04:21] FALHOU renovar: rclone authorize não deu o link'; a última OK foi em '[11/11 11:32] renovada (vale 7 dias)'. COM: DriveChaveRenovar com 0x00000001. Próxima rodada em 26/11.
- **proposta:** Conferir à mão se o token ainda vale (a tarefa DriveChaveConferir existe) e consertar o passo 'rclone authorize' em drive_chave.py renovar (perto da linha 122, login_hint). Avisar no Telegram já na 1ª falha. Fazer isso pela saída correta da conta 32, nunca de outro IP de conta.
- **risco:** medio
- **ja_existe:** DriveChaveConferir (ligada, 0x41306 = rodando) existe, mas não pegou nem avisou a falha da renovação.
- **estado:** FEITO 25/11: chave renovada + tarefa diária (drive_chave.py diario)

### 47. [vigia-relatorio] Fila de conserto entupida: 191 casos 'consertar' sem prazo, teto diário gasto em caso velho

- **problema:** Casos nunca expiram e andar() percorre do mais antigo pro mais novo. Os 12 consertos do dia (CASOS_DIA_MAX) são gastos logo depois da meia-noite em casos de 16-18/11, quase todos reserva_zero repetidos. O carrossel e os alertas de hoje nunca chegam ao consertador. Hoje o Hydrogen recebeu 12 casos às 00:04 e o painel caiu no Kiro em 11 (sem_token); o 12º falhou. Não há conserto aprovado desde 11/11.
- **evidencia:** D:\video-fila\estado\vigilancia.json: etapas = consertar 191, falso 74, sem_mudanca 21, dona 4; dia={'data':'2026-11-24','consertos':12}. Chaves em 'consertar': reserva_zero 150 (dentrodascoisas3d 21, fatochocante 19, inventoreact 19...). vigilancia_casos.jsonl 24/11 00:04:35-37: 12x consertando gemini/gemini-4-hydrogen nos casos 20261116_005034_212...20261118_234034_243; 00:31-00:50: 11x sem_token usado=kr/claude-sonnet-4.5; 00:21:57: 1x falhou. 'aprovado' total = 9, o último em 2026-11-11. vigilancia.py:791 (ordem por 'aberto'), 690 (teto), 61 CASOS_DIA_MAX=12.
- **proposta:** (a) Fechar como 'vencido' o caso com mais de 48 h, ou fundir com o caso mais novo da mesma chave (hoje a mesma chave abre um caso novo a cada 6 h e o velho fica). (b) Ordenar 'consertar' por urgente, depois mais novo. (c) Se o painel cair pra outro modelo, não contar no teto do dia. (d) reserva_zero é falta de produção, não bug de código: tirar do consertador e mandar pro relatório.
- **risco:** baixo
- **ja_existe:** O teto e a ordem fixa Argon→Hydrogen→Sonnet→Kiro são de 23/11 (vigilancia.py:47-55). Não há expiração de caso.

### 48. [visual-shorts] Efeitos T5/T6/T7 e impacto lateral NÃO são renderizados desde 01/11 (vivem só no caminho PNG morto)

- **problema:** O Short usa sempre o libass (legenda MIX). Os efeitos de raio/fogo (T6), a mascote nas pausas (T7), o gancho Remotion (T5) e a palavra de impacto lateral (T3) só são aplicados no caminho PNG (render_subtitles_short + burn_subtitles), que só roda se o libass falhar. O braço B é sorteado e gravado no postar.json, mas o vídeo sai igual ao braço A.
- **evidencia:** anime_captions.py:75-76 (short_mix = ANIME_SHORT_MIX padrão '1' -> libass, return na linha 87); CORTES_FX_CHOQUE só é lido em fx_subtitles.py:1435, dentro de render_subtitles_short (def na 1340); CORTES_LEGENDA_ESTILO só em fx_subtitles.py:1433; no caminho ASS o impacto é sempre centralizado: fx_subtitles.py:1026-1032 (\an5\pos(vw//2, vh*0.42)); a mascote T7 fica em anime_captions.py:105-116 (depois do caminho libass); o gancho Remotion fica em anime_gancho.queimar, chamado só em anime_captions.py:137 (ramo PNG). Contagem nas pastas de 'animes recap/shorts' por data: fx_choque real = 68 em 31/10, 9 em 01/11 e 0 de 02/11 a 24/11 (só 1 caso em 06/11), com fx_sort_B entre 22 e 132 por dia; mascote real = 76 em 31/10 e depois ~0; nos últimos 5 dias, 0 de 1.223 pastas têm _testes_usados.json.
- **proposta:** Portar para o caminho libass (burn_subtitles_ass) o que já existe: (1) os quadros PNG de raio/fogo de _fx_choque como overlay na mesma passada do ffmpeg, onde a mascote do CTA já entra (fx_subtitles.py:1162-1196); (2) o impacto lateral (rotação \frz e posição de lado no Dialogue do impacto, linha 1031) quando CORTES_LEGENDA_ESTILO=lateral; (3) a camada Remotion do gancho como input extra. Até portar, marcar no placar que os braços B desses testes são placebo desde 02/11.
- **risco:** medio
- **ja_existe:** O código dos efeitos existe (fx_subtitles._fx_choque, cortes_mascote.aplicar, anime_gancho._camada_remotion) e os assets também (D:\hipercool-materiais\assets\cortes_fx com impacto_/varredura_ raio_00d1ff, raio_ffc83d, fogo_ff2a1a). Só não estão ligados ao caminho que roda.

### 49. [aprendizado-metricas] A/B dos longos: amostra impossível e 'vencedores' de ruído

- **problema:** Cada pedido de longo sorteia 4 fatores juntos (5x3x2x2 = 60 combinações). Com ~122 longos postados na vida, o AB_RESULTADOS declara vencedor com n=4-10 e views/h de 0,01-0,21, o que é ruído. Além disso o resumo só era gerado pelo melhorador_longo, que está PAUSADO, então parou em 23/11. O experimento 'resumo_curto_gancho' está aberto desde 17/11 com 4 x 4 e não fecha mais.
- **evidencia:** config/longo.json ab_fatores: fala_rapida A-E, ganchos_15min A-C, cortes_resumo A/B, titulo_triade A/B (colab/cliente.py:333-349, md5 por fator). colab/longos_postados.json 'postados' = 122. linhas/LONGOS/AB_RESULTADOS.md (23/11 11:38): 'fala_rapida vence E' com n=10 e 0,13 views/h; 'narradores_modo vence so_primarios' com 0,21 views/h. melhorador_longo.py:388 'Só aponta vencedor com n >= 4'. Tarefa RecapMelhoradorLongo = Disabled. linhas/LONGOS/experimento.json: ativo=true, enviados A 4 / B 4, aberto 2026-11-17.
- **proposta:** Testar UM fator por vez nos longos (os outros fixos em A) e usar como métrica principal horas assistidas/longo (a mesma do pesar_fila), com mínimo de 12 por braço e mesmo canal. Tirar _resumo_variantes do melhorador para um script só-leitura diário (não religa o melhorador). Fechar como 'sem conclusão' o experimento.json parado.
- **risco:** baixo
- **ja_existe:** pesar_fila.py (PesarFilaLongos, 3/3 h) já pesa tema por horas e views/dia e funciona (res 0). O A/B por fator existe, mas é amplo demais.

### 50. [aprendizado-metricas] Longos não registram o motor de voz: XTTS x Kitten x Fish nunca vai ter placar

- **problema:** A decisão do motor dos longos (XTTS v2 como principal, 21/11) foi tomada por ouvido. O registro do longo postado não guarda qual motor narrou, então não dá para confirmar com views e horas.
- **evidencia:** colab/longos_postados.json 'postados': as chaves presentes em 122 itens são nome, vid, canal, canal_nome, url, titulo, em, duracao_s, seo_versao, estilo_titulo, tags, narradores_modo, ab, variante e experimento. Não há motor_voz. colab/postar_longos.py:143-149 só copia ('ab', 'narradores_modo', 'experimento', 'variante'). O teste XTTS foi postado à parte (colab/postar_xtts_teste.py), sem grupo de comparação.
- **proposta:** Em postar_longos (linha 149) copiar também 'motor_voz' e 'xtts_versao' do render.json/longo_override para longos_postados.json, e incluir os dois como fator no placar de longos (achado 6).
- **risco:** baixo
- **ja_existe:** O longo_override já carrega motor_voz/xtts_versao (memória project_modos_de_voz). Falta gravar na postagem.

### 51. [arquitetura] Copia COMUM desatualizada: narracao_curva.py do hipercool-videos esta parada em 13/11

- **problema:** O mecanismo de copia identica tem buraco: a copia do hipercool nao recebeu a versao de 24/11 e ninguem foi avisado. A narracao do hipercool roda codigo velho achando que e o comum.
- **evidencia:** cmp: comum/narracao_curva.py 42724 B (24/11 00:30) = recapd/bin (24/11 00:29), mas hipercool-videos/bin/narracao_curva.py 41590 B (13/11 13:16) DIFERENTE, com o cabecalho '# COMUM — fonte unica'. recursos.json registra narracao_curva.py com projetos ['hipercool','historias','recapd'] (de recapd, em 2026-10-22). Existe ate narracao_curva.py.antes_sync_1113_1316 no comum (sync do GitHub mexeu fora do recursos.py).
- **proposta:** Decidir com a dona se o hipercool deve receber a versao de 24/11 (rodar 'recursos.py subir narracao_curva.py --de recapd --testar' primeiro). Para nao repetir: o vigia (VigilanciaSistema, ja ativo) pode chamar o painel do recursos.py 1x/dia e mandar aviso so quando houver 'MUDOU la'/copia divergente de modulo registrado (sem religar melhorador). Tambem: sincronizar_github.py deve passar pelo recursos.py quando o arquivo for COMUM.
- **risco:** medio
- **ja_existe:** recursos.py detecta 'MUDOU la' (recursos.py:252-253), mas so quando alguem roda o painel; nao ha rotina.

### 52. [arquitetura] Estado do Kaggle espalhado em 5 arquivos, 3 deles mortos e um ainda usado como reserva

- **problema:** Mesmo dado (contas e horas do Kaggle) em varios JSON com idades diferentes; o maquinas.py cai num arquivo de 23 dias quando a central falha e mostra horas falsas no painel.
- **evidencia:** python lendo os JSON: colab/kaggle_pool.json = 87 contas (27 nao banidas); video-fila/estado/kaggle_horas.json em=2026-11-01T06:36 (58 contas); estado/colab_contas.json em=2026-10-24; estado/abastecedor_kaggle.json em=2026-11-21 (3 vivos); estado/balanco_kaggle.json em=2026-11-24 01:10. Tarefa \KaggleHoras = Desabilitado (schtasks). maquinas.py:203-209 usa kaggle_horas.json como reserva ('quebrado em 02/11: 401 em quase todas') sem checar idade.
- **proposta:** Fonte unica = kaggle_pool.json (contas) + estado da central (horas). No maquinas.py:204, ignorar kaggle_horas.json com 'em' mais velho que 48 h (mostrar 'sem medida' em vez de numero velho). Renomear kaggle_horas.json e colab_contas.json para *.morto_<data> SO depois de confirmar com grep que o unico leitor e maquinas.py/kaggle_horas.py (confirmado hoje). Nenhuma consulta a conta envolvida.
- **risco:** baixo
- **ja_existe:** Comentario em maquinas.py:203 ja admite que a reserva quebrou em 02/11; nao foi tirada.

### 53. [arquitetura] Postador nao tem venv proprio: roda no Python do projeto veo (e 4 interpretadores fixos espalhados)

- **problema:** Postagem depende do venv de outro projeto; atualizar pacote no veo (ou apagar D:\veo) quebra a postagem. Interpretador e escolhido por caminho fixo em dezenas de arquivos.
- **evidencia:** controlador.py:41 PY_POST = Path(r"D:\veo\venv\Scripts\python.exe"); 18 arquivos de video-fila/postador citam veo\venv\Scripts\python; contagem de interpretadores fixos: hipercool-videos\venv ~52, veo\venv ~34, manhwa-react\.venv ~13, hipercool-materiais\python\venv 2. ls: D:\postador-de-videos\venv e .venv nao existem; recursos.py:47 usa sys.executable para 'postador'.
- **proposta:** Colocar PY_POST/PY_HIPER/PY_MR/PY_RECAPD em caminhos.py (passo 1) e trocar primeiro o controlador.py:41-43. Nao criar venv novo agora (memoria: NUNCA mover python\venv); so centralizar o nome para que uma troca futura seja de 1 linha.
- **risco:** baixo
- **ja_existe:** Nao.

### 54. [arquitetura] URL do OmniRoute fixa em 68 arquivos

- **problema:** Troca de IP/porta da VPS 157 exige editar 68 arquivos; ja ha um IP antigo (62.171.128.241) sobrando no comum.
- **evidencia:** grep 'http://157.173.207.22:20128' = 68 arquivos .py nos projetos do mapa; 65 arquivos tambem leem OMNIROUTE_URL/OMNI_URL do ambiente (ou seja, o padrao com override ja existe pela metade). comum/teste_salvar_github.py:82 cita http://62.171.128.241:20128.
- **proposta:** OMNIROUTE_URL em caminhos.py com o mesmo default; migrar os 68 por substituicao mecanica em lotes pequenos (por projeto), conferindo py_compile em cada lote.
- **risco:** baixo
- **ja_existe:** Variavel de ambiente OMNIROUTE_URL ja usada em 65 arquivos, cada um com seu default.

### 55. [codigo-morto] 17 snapshots + 2 backups do manhwa de julho em producao\bin (7,7 MB, 20 cópias de hiper-pipeline.py)

- **problema:** As pastas _snapshots\ (17 versões de 29/06 a 03/07), _BACKUP_20260707 e _SNAPSHOT_ANIME_20260712_2200 repetem os módulos de produção com o mesmo nome. Um grep por anime_tts, fx_clips ou effects_engine devolve até 20 resultados.
- **evidencia:** du: _snapshots = 6,3 MB, _BACKUP_20260707 = 1,3 MB, _SNAPSHOT_ANIME_20260712_2200 = 141 KB. Na lista de nomes repetidos, hiper-pipeline.py e effects_engine.py aparecem em 20 pastas, e fx_clips.py e anime_tts.py também no _SNAPSHOT_ANIME. Fora do filtro do montar_pacote.py:20 (FORA = '_SNAPSHOT*/**', '_BACKUP*/**', '_snapshots/**'), nenhum .py ou .bat referencia essas pastas.
- **proposta:** Compactar as 3 pastas num zip, mandar para o Drive (manhwa-drive: arquivo) e, depois do rclone check, tirar do bin, seguindo a regra 'rm só após rclone check'.
- **risco:** baixo
- **ja_existe:** Só existe a exclusão no montar_pacote.py:20, que tira essas pastas do pacote do Kaggle. No disco e no grep elas continuam.

### 56. [codigo-morto] vigia_backups com 140 pastas e 70 MB, sem rodízio

- **problema:** O vigia_geral manda copiar o original antes de editar, mas nada apaga as cópias. As pastas trazem anime_fetch.py, anime_tts.py e claude_client.py antigos com o mesmo nome dos de produção.
- **evidencia:** video-fila\vigia_geral.py:367: 'Antes de editar QUALQUER arquivo, copie o original para D:\\video-fila\\vigia_backups\\{hora}\\'. A tarefa VigiaVideos está Habilitada (CSV). du -sh vigia_backups = 70M, com 140 pastas, a mais recente 20261114_0256. Repetições vistas: anime_fetch.py em 5 pastas, de 20261018_1415 a 20261021_1415.
- **proposta:** Juntar as pastas com mais de 7 dias em zip mensal e mandar para o Drive, ou aplicar o rodízio da 'Reserva de 1 semana'. Uma regra de 5 linhas no próprio vigia_geral resolve, com a chave VIGIA_BACKUP_DIAS=7 e 0 para desligar.
- **risco:** baixo
- **ja_existe:** Não tem rodízio. A última pasta é de 14/11, então o vigia parou de gravar backups ou parou de editar, o que vale conferir à parte.

### 57. [codigo-morto] Cerca de 180 arquivos .bak/.bkp nas pastas vivas, 50 só do kaggle_pool.json

- **problema:** Cópias de estado e de código se acumulam ao lado do arquivo vivo. Isso leva a erro de leitura ('qual pool vale?') e o kaggle_pool.json.bak_* guarda contas antigas, inclusive banidas.
- **evidencia:** find -name '*.bak*': producao = 84 arquivos (3,3 MB), video-fila = 47 (2,9 MB), postador = 51 (0,9 MB), comum = 4. Em colab há 52 arquivos kaggle_pool*: 1 vivo, 11 .bak_* (340 KB, de bak_02nov_ban a bak_23nov_desktop) e cerca de 40 .bkp_* (de bkp_20261029_0923 a bkp_20261108_0150_46). Em bin ficam anime_tts.py.bak_20261119_165331_melhorador, fx_clips.py.bak_20261120_160147_melhorador (126 KB) e _PRE_SPLIT_effects_engine.py.bak (173 KB). Os .bkp do pool aparecem em kaggle_token_cofre.py, kaggle_token_proxy.py e pesar_fila.py.
- **proposta:** Uma regra só: .bak/.bkp com mais de 7 dias vão para <pasta>\_bak\ e daí para o Drive. Para o kaggle_pool, guardar só os 3 mais recentes no PC. Antes, conferir se kaggle_token_cofre, kaggle_token_proxy e pesar_fila apenas CRIAM os .bkp ou se também os LEEM, porque se leem não se pode mover.
- **risco:** baixo
- **ja_existe:** O montar_pacote.py:20 já tira *.bak* e *.bkp* do pacote. Não há limpeza no disco.

### 58. [codigo-morto] 43 tarefas Desativadas continuam registradas, com scripts que já viraram legado

- **problema:** Tarefas desligadas há semanas apontam para scripts que ninguém mais chama, como video-fila\ocioso.py, colab\kaggle_lancar.py manter, hipercool-videos\bin\fila.py e recapd\cron_anime_*.bat. Fica difícil saber o que é pausa (decisão da dona) e o que está morto.
- **evidencia:** CSV das tarefas: 43 linhas com 'Desativado', entre elas AnimeOcioso (D:\video-fila\ocioso.py), KaggleRecapManter, KaggleBaixador, KaggleHoras, HipercoolFila, HipercoolReligarProducao, HipercoolShorts2h, HipercoolVigia, AnimeRecapMonitor, AnimeRecapNoturno, PostarMedieval15, VeoProducaoDiaria7h, TrocarVenvUnico, AgendadorVO3, SupervisorMelhorador e VigiaMelhorias. Em video-fila\estado há também ocioso.py.bak_20261030_0135 e _0405.
- **proposta:** Não religar nem apagar. Escrever um TAREFAS_DESLIGADAS.md em video-fila com 1 linha por tarefa: 'pausa da dona' (MotorPesquisador, CobradorPesquisador, MelhoradorCentral, RecapMelhoradorLongo) ou 'aposentada em DATA porque X'. A dona aprova a lista de aposentadas, e só depois os scripts delas vão para _arquivo.
- **risco:** baixo
- **ja_existe:** O CLAUDE.md lista só as 4 pausadas do pesquisador e dos melhoradores. Para as outras 39 não achei decisão escrita.

### 59. [disco-arquivos] Mesmo longo de 3,4 GB guardado em duas cópias independentes (_longos_postar e LONGO_PARA_CONFERIR)

- **problema:** O longo_para_conferir.py baixa do Drive outra cópia do longo que o postar_longos já baixou para _longos_postar. As duas não são hardlink, então ocupam 3,4 GB em dobro com o disco a 6 GB.
- **evidencia:** D:\hipercool-materiais\_longos_postar\RzoyNcnlIj8_misto_xtts8_s2pro_momo\final_anime_deitado.mp4 e D:\hipercool-materiais\LONGO_PARA_CONFERIR\RzoyNcnlIj8_misto_xtts8_s2pro_momo.mp4 têm os dois 3.402.299.732 bytes. O `fsutil hardlink list` de cada um mostra só o próprio nome (não são o mesmo arquivo). Em D:\recapd-ambientes\producao\colab\longo_para_conferir.py:95, `rclone copyto d['drive'] tmp`. Em D:\limpeza_c\noite\C4\progresso.md 02:23, _longos_postar estava com 0 GB (o caso apareceu depois).
- **proposta:** Em longo_para_conferir.py, antes do rclone copyto, procurar o mesmo nome em _longos_postar\<nome>\*.mp4 com o tamanho igual ao do Drive e usar os.link (fallback: baixar). Fazer o mesmo no sentido contrário no postar_longos (se LONGO_PARA_CONFERIR tem o arquivo, faz o link). O gerente R8 e a troca do longo_para_conferir apagam só um nome, sem risco.
- **risco:** baixo
- **ja_existe:** A C4 (noite 24/11) tratou o hardlink entre _longos_postar e 'videos laterais' (faxina_disco.py:189-239), mas não o LONGO_PARA_CONFERIR.

### 60. [disco-arquivos] D:\tmp\estudo_voz: 3,8 GB crescendo (1.166 arquivos novos em 3 dias) sem dono, com o registro de testes vazio

- **problema:** Os experimentos de voz (jobs, coleta_volta, iter_volta, cega_volta, replica_volta) gravam em D:\tmp\estudo_voz e ninguém limpa. A regra de registrar teste (testes.py, que deixa a faxina limpar sozinha quando vence) não está sendo usada.
- **evidencia:** du: estudo_voz = 3,8 GB (jobs 1,1 GB com 76 pastas; coleta_volta 801 MB; iter_volta 739 MB; cega_volta 559 MB; replica_volta 369 MB). Datas dos arquivos: 22/11 = 406, 23/11 = 3.046, 24/11 = 434. D:\video-fila\TESTES_TEMPORARIOS.md tem '(nenhum teste registrado)'. donos.json: 'D:\tmp\estudo_voz' com 'limpa: NINGUÉM (manual / arquivo_testes_voz no Drive)'. Em D:\tmp também estão coleta_narradores (432 MB), previas_tela (253 MB) e prev7_*.mp4 (128 MB, de 23/11).
- **proposta:** Não criar nada novo: fazer os scripts que geram estudo_voz/jobs chamarem `testes.py registrar <pasta> --dias 3` (o mecanismo que já existe e que a faxina limpa). Para o que já está lá, aplicar a regra da memória 'Limpar testes de voz no fim': mover as subpastas de 21-22/11 (gol, xtts_*, s2v_*, qwen3_*, tempos_*) para o Drive arquivo_testes_voz com rclone check, como pede a dona. Só funciona se a faxina voltar a terminar (achado 3).
- **risco:** baixo
- **ja_existe:** testes.py e TESTES_TEMPORARIOS.md existem (faxina_disco.py:327-331 chama testes.limpar), mas ninguém registra. A regra da memória project_limpeza_testes_voz também existe e ainda não foi executada.

### 61. [disco-arquivos] O RELATORIO_MANHA.md do trabalho noturno não foi gerado: as decisões pendentes de disco não chegaram à dona

- **problema:** O plano noturno termina com um relatório para a dona com o que só ela pode decidir (node_modules 1,7 GB duplicado, c_movido, amostras_voz, rvc). O arquivo não existe, e as decisões continuam espalhadas em 7 resultado.md.
- **evidencia:** `ls D:\limpeza_c\noite\RELATORIO_MANHA.md` retorna 'No such file'. Em PLANO.md, 'Fim (07:50) — RELATORIO_MANHA.md'. A6\progresso.md 06:00: 'Resto (node_modules remotion 1,7 GB, __pycache__..., log 82 MB do drive_central) fica para decisão da dona no RELATORIO_MANHA'. A6\resultado.md §3: D:\claude-code-video\remotion\node_modules e D:\postador-de-videos\remotion\node_modules com 847,89 MB cada, cópias exatas.
- **proposta:** Consolidar num relatório só, a partir dos resultado.md A1-A7 e C1-C6, com a lista de decisões: hardlink ou junção do node_modules do remotion (847 MB), D:\tools\drive_central\logs\inovaremanhwabr.log (82 MB, parado desde 12/11), c_movido, amostras_voz e models\rvc. Se o cron noturno já fechou às 08:00, alguém precisa gerar à mão.
- **risco:** baixo
- **ja_existe:** Previsto no PLANO.md, mas ainda não executado (às 06:30 de 24/11).

### 62. [modelos-ia] Argon do texto dos Shorts: timeout de 120 s custa 4,6 h por semana; o sucesso responde em 5-36 s

- **problema:** _texto_video espera até TEXTO_VIDEO_TIMEOUT=120 s antes de cair pro Gemini 3.8. Quando o Argon trava ele quase sempre bate exatamente no teto, e o render fica parado esperando. A mediana do sucesso é 5,3 s e o p95 é 36 s.
- **evidencia:** D:\recapd-ambientes\producao\workspace\modelo_texto.jsonl desde 17/11: gemini-4-argon 1239 chamadas, 176 falhas (136 TimeoutError, 32 HTTP 429, 6 RemoteDisconnected); dos timeouts, 103 em 120 s e 21 em 121 s; tempo somado nas falhas = 17941 s (4,6 h só nos timeouts). Sucessos: p50 5,3 s, p75 11,3 s, p90 21,4 s, p95 36,2 s, p99 97 s. Código: claude_client.py:466-467 (timeout), anime_auto.py:710-712, cortes_ajustes.json:28-30 (texto_video_timeout_s=120).
- **proposta:** Baixar texto_video_timeout_s para 45 s em bin\cortes_ajustes.json (pega cerca de 96% dos sucessos e corta de 120 para 45 s cada travada). Volta: pôr 120 de novo.
- **risco:** baixo
- **ja_existe:** O teto existe e é configurável (texto_video_timeout_s); o valor 120 é de 27/10, quando a mediana medida era 71 s (comentário em claude_client.py:466). Hoje a mediana é 5,3 s.

### 63. [modelos-ia] Caixa do recap: cc-sobra, ag-opus-5-5 e ag-hydrogen entregaram 1 de 50 tentativas e gastam 3,2 h antes do Gemini 3.8

- **problema:** A cadeia do conserto de código do melhorador dos longos (melhorador_longo.json codigo: modelo=cc-sobra, reservas=[ag-opus-5-5, ag-hydrogen, agy/gemini-3.8-flash-high]) tenta sempre os 3 primeiros, que voltam '429/503 all targets were skipped ... reset after 44m' ou '(sem resposta)'. Só o Gemini 3.8 entrega. Cada passada perde de 5 a 25 min antes de chegar nele.
- **evidencia:** estado\placar_modelos.jsonl (19-23/11): cc-sobra 19 tentativas, 1 entregou, 3202 s; ag-opus-5-5 17/0, 5415 s; ag-hydrogen 14/0, 3139 s; agy/gemini-3.8-flash-high 11/9. resumo_gemini.txt em D:\hipercool-materiais\_melhorador_caixa\20261123_*: 'API Error: Request rejected (429) ... reset after 46m 14s', '503 ... claude-opus-5-5-high 100%'. Relatório 23/11 (D:\tmp\ronda_tarde.txt:167-169): Hydrogen 0/14; OmniRoute Hydrogen 0/53. Código: melhorador_longo.py:622-641, caixa_gemini.py:20 (padrão Hydrogen primeiro).
- **proposta:** Antes de cada modelo da cadeia, um teste de 5 tokens (ia_reserva.testar já faz isso) e, se a resposta trouxer 'reset after Xm', guardar o modelo fora até essa hora (como ia_reserva._ate). Com o placar atual, pôr o Gemini 3.8 em 1º no codigo.reservas e deixar Hydrogen fora da caixa até voltar a entregar. Não religa nada: vale quando a dona religar o RecapMelhoradorLongo.
- **risco:** baixo
- **ja_existe:** O placar existe (comum\placar_modelos.py, 18/11) e mostra o resultado no relatório, mas nada o lê para mudar a ordem. melhorador_longo.py:636 só passa pro próximo modelo pela resposta; não guarda 'fora até'. Tarefa RecapMelhoradorLongo está Desabilitada (pausa da dona).

### 64. [modelos-ia] Hydrogen passa no teste de 5 tokens mas falha no trabalho real e segue como 2º consertador da vigilância

- **problema:** vigilancia.py (23/11) põe gemini/gemini-4-hydrogen em 2º em CONSERTADORES. _disponivel usa ia_reserva.testar (5 tokens), que passa, mas os pedidos reais caem na reserva (Kiro) ou falham. Resultado: 12 casos de uma vez foram para o Hydrogen às 00:04 de 24/11 e todos caíram pro Kiro ou falharam.
- **evidencia:** vigilancia_casos.jsonl 24/11 00:04:35-00:04:37: 12 'consertando' com gemini/gemini-4-hydrogen; 00:21:57 'falhou'; 00:31-00:50 10 'sem_token pedido=gemini/gemini-4-hydrogen usado=kr/claude-sonnet-4.5'. painel_ia desde 17/11: Hydrogen pedido 16 vezes, só 1 rodou nele mesmo. Relatório 23/11 (ronda_tarde.txt:169): no OmniRoute 'Hydrogen: 0/53 ok'. Código: vigilancia.py:53 e :556-571.
- **proposta:** Tirar o Hydrogen dos CONSERTADORES até o placar do OmniRoute mostrar acerto (ou testar com um pedido real curto com ferramenta, não 5 tokens). Também limitar o lote: no máximo 2-3 consertos novos por volta para o mesmo modelo, para não queimar 12 de uma vez.
- **risco:** baixo
- **ja_existe:** A ordem é decisão da dona de 23/11 (comentário em vigilancia.py:48-51, 'Argon ou Hydrogen, senão o Sonnet web, senão o Kiro'). Mudar a ordem precisa do OK dela; o limite de lote não existe.

### 65. [modelos-ia] Júri dos Cortes: modelo de reserva igual ao principal, então o timeout de 900 s se repete

- **problema:** MODELO e MODELO_RESERVA são o mesmo (antigravity/gemini-3-flash), mas o docstring diz agy/gemini-3.8-flash-high com reserva automática. Quando o 3-flash trava (900 s), o verificador tenta o MESMO modelo de novo, até 30 min por foco, 4 focos em paralelo.
- **evidencia:** cortes_juri.py:35-36 (MODELO = MODELO_RESERVA = 'antigravity/gemini-3-flash'); :7 do docstring cita 'agy/gemini-3.8-flash-high, reserva automática'; :232-238 (laço pelos dois). juri.log: 23 'timeout 900s' entre 21 e 23/11 (21/11: 7, 22/11: 11, 23/11: 5), ex.: '[23/11 05:50:41] [verificador historia] antigravity/gemini-3-flash falhou: timeout 900s'.
- **proposta:** MODELO_RESERVA = 'agy/gemini-3.8-flash-high' (o mesmo usado no texto e no vigia, 98,6% ok em modelo_texto.jsonl) e timeout do verificador em 300 s.
- **risco:** baixo
- **ja_existe:** Não; o comentário do topo diz que já era assim, mas o código não está.

### 66. [narracao-longos] A mascote fala com a voz do narrador em todos os longos XTTS

- **problema:** A mascote tem uma voz clonada (ANIME_MASCOTE_CLONE) que não está no Kaggle. As falas dela, fora as pausas gravadas, saem na voz do narrador. A CONFERENCIA marca 'Mascote reagindo' como OK.
- **evidencia:** Todos os pipeline.log de 21 e 22/11 (82ge1YYkUyA x2, 8fM6Ay7OJho x2, e2nIzNGXvmA, gJve_WjefZs, kxohroSbgS8, RzoyNcnlIj8) têm '[mascote] sem voz clonada da mascote nesta máquina — as falas dela ficam com o narrador'. Código em bin\anime_segments.py:322-328, que exige VOZES_DIR/clone/clone.pth. RzoyNcnlIj8\CONFERENCIA.md: '✅ 4 reações'.
- **proposta:** Usar o mesmo _baixar_voz_drive de 23/11 (anime_segments.py:348) para o clone da mascote antes da checagem da linha 326. Fazer a CONFERENCIA separar as reações com a voz dela das que saíram com o narrador.
- **risco:** baixo
- **ja_existe:** O download existe só para as vozes de personagem (anime_segments.py:388). A mascote não passa por ele.

### 67. [narracao-longos] Longo de 3,4 GB leva 6,7 h para subir e falha no fim, travando a fila

- **problema:** O longo misto, único do motor padrão, levou 401 min de upload e deu Timeout na tela seguinte. Ficou preso ao Fio da Meada e recomeçou à 01:01. Cada tentativa ocupa o envio por quase 7 h, e o canal VIP fica 1 envio por vez.
- **evidencia:** colab\postar_longos.log [23/11 22:53]: 'envio: 3402 MB em 401 min (normal)' e 'erro: TimeoutError: Locator.wait_for: Timeout 60000ms'. [23/11 22:58]: 'erro DEPOIS de subir (406 min) — pode ter ficado rascunho'. [24/11 01:01]: 'preparando RzoyNcnlIj8_misto_xtts8_s2pro_momo' de novo. Duração em qa.json: 3545,6 s. Taxa média: 3402 MB x 8 / 3545 s = cerca de 7,7 Mbps.
- **proposta:** (1) Antes de subir de novo, conferir no Studio pela saída da conta se já existe o rascunho da tentativa anterior (o próprio log avisa). Senão o canal ganha um duplicado. (2) Codificar o longo final em 1080p com cerca de 4 a 5 Mbps (CRF/2 passadas). Fica dentro da regra de 1080p mínimo e corta perto de 40% do upload.
- **risco:** medio
- **ja_existe:** O LONGO_PRESO_AO_CANAL existe (postar_longos.py:970). Não existe checagem de rascunho órfão antes de reenviar nem teto de bitrate do longo.

### 68. [narracao-longos] A Fish na nuvem falhava calada e caía no Kitten (0/345)

- **problema:** Em 20/11 o Fish do Kaggle narrou 0 frases em longos inteiros e tudo caiu no kitten_tudo. O longo saiu no motor antigo sem ninguém saber. Hoje o padrão é XTTS e esse caso só importa se o Fish voltar. Mas o padrão é o mesmo: a queda para o motor reserva é silenciosa e pode acontecer com o XTTS e o S2-Pro.
- **evidencia:** na_nuvem\iWIgK8o9pxE...\pipeline.log:50 '[fish nuvem] 0/345 frases em 33s (narrador momo); o resto no kitten_tudo', :743 0/160 e :1066 0/161. ZaWVmJcOjfo 0/25. Bb3C8_mEpUE 0/2.
- **proposta:** Fazer a CONFERENCIA ganhar a linha 'Motor de voz: X% no motor pedido'. Ler '[xtts] N/M', '[s2pro] N/M' e '[fish nuvem] N/M' do pipeline.log e marcar ❌ abaixo de 90%, com aviso à dona pelo arquivo da pasta (ver achado 4).
- **risco:** baixo
- **ja_existe:** Para o Fish, o LONGO_SO_FISH_POSTAR barrava a postagem (LONGOS_MELHORIAS 19/11 17:30), mas o postar_xtts_teste o desliga e não há equivalente para o XTTS. A CONFERENCIA não tem linha de motor.

### 69. [narracao-longos] A legenda escorrega no XTTS e no S2-Pro: conserto de 22/11 ainda sem prova

- **problema:** O XTTS e o S2-Pro não produzem .words.json e a legenda era estimada pelo tamanho do texto, saindo fora da voz. O conserto mede no Whisper (GPU) toda frase sem tempos, mas nenhum longo pós-conserto foi conferido.
- **evidencia:** LONGOS_MELHORIAS.md:455 (22/11): 'anime_segments._tempos_fish agora mede no Whisper (GPU) TODA frase com áudio e sem tempos... TEMPOS_TODA_FRASE=0 volta'. O único longo depois disso é o RzoyNcnlIj8, de 22/11 08:48, e o pacote --codigo foi enviado em 22/11 sem hora. Não dá para afirmar se ele já pegou o conserto.
- **proposta:** No próximo longo v13, conferir no pipeline.log que o Whisper dos tempos rodou em todas as frases, e ver 2 ou 3 prints com legenda e onda de áudio. Não é para mexer no código: o conserto já existe.
- **risco:** baixo
- **ja_existe:** Sim: TEMPOS_TODA_FRASE (22/11). Falta só a prova num longo real.

### 70. [narracao-shorts-fish] Efeito e 'fim que sobe' de OUTRA voz aplicados por cima da voz do Chris

- **problema:** O Fish online narra com a voz do nicho (narrador do Chris, Neymar ou Iberê), mas o acabamento usa VOZ_CLONADA, que é o narrador clonado escolhido para o Short (ex.: d_va_overwatch, momo, mike). Com isso, o efeito próprio dessa voz (ex.: tremido) e o +st do 'fim que sobe' do Mike/Momo/KkVirjão são aplicados na voz do Chris.
- **evidencia:** anime_tts.py:2083 '_acabamento_fish(..., os.environ.get("VOZ_CLONADA"))'. A voz real vem de fish_lote.voz_do_nicho (fish_lote.py:166-172; voz_por_nicho.json padrao=4b215a58... Chris). _acabamento_fish chama aplicar_efeito_voz(voz) e _fim_que_sobe(voz) (anime_tts.py:459-482), e FISH_FIM_ST={'mike':1.5,'momo':0.8,'kkvirjao':1.0} (anime_tts.py:485-490). Log de 23/11: 'voz clonada: d_va_overwatch', 'guugou', 'seu_madruga' em Shorts com VOZ_ONLINE=fish.
- **proposta:** Passar para _acabamento_fish o nome da voz QUE O FISH USOU: a chave de vozes_site.json do id usado, ou 'narrador_chris' quando for o padrão. Efeito e fim que sobe só se essa voz tiver cadastro. Também gravar no _voz_online.json qual voz do site foi usada, para o postar.json e o sinais_shorts mostrarem 'narrador real = Chris' (hoje o campo narrador diz 'momo' em Short narrado pelo Chris, o que confunde a análise de receita do narrador).
- **risco:** baixo
- **ja_existe:** Não.

### 71. [narracao-shorts-fish] Tags de emoção do S2-Pro 13 ([laughing], [excited tone], [sigh], [shouting], [chuckle]) não passam para o Fish online

- **problema:** Nos longos, o S2-Pro 13 faz as frases de emoção com tags dentro do texto, e foi isso que fez a 'piada contada, não lida'. O Fish online (backend drama-3) recebe só o texto, então piada, suspiro e grito saem lidos.
- **evidencia:** anime_tts.py:1266-1300 (_s2_tags_v13: '[laughing] [excited tone]' na virada, ênfase no 'hein'). MOTOR_DE_VOZ_PADRAO_23NOV.md (seção S2-Pro 13 e 'Piada contada'). fish_http.py:147-157 manda parameters {text, model_id, latency, backend drama-3, normalize false}, sem nenhuma tag. Memória project_modos_de_voz: S1-mini aceita (excited)(laughing) e S2-Pro aceita [laughing]; o Drama 3 do site não foi testado com tags.
- **proposta:** Teste pequeno e barato antes de ligar: 1 conta, 4 frases (~250 créditos) com o mesmo texto com e sem _s2_tags_v13, pela ponte da própria conta. Para comparar: auditor Whisper (a tag não pode ser LIDA em voz alta) e ouvido da dona. Se o Drama 3 aceitar: em _narrar_online usar _s2_tags_v13 só nas frases de piada/virada/'coitado'/'isso!' (as tags custam caracteres; limitar a no máximo 2 por Short). Chave FISH_ONLINE_TAGS=0. Se ler a tag em voz alta: reprovar e registrar.
- **risco:** medio
- **ja_existe:** As tags existem só no S2-Pro do Kaggle. No Fish online, nunca foram testadas.

### 72. [narracao-shorts-fish] Piada de virada em 2 linhas ('...hein?!' / 'Mentiraaa, galera!') só existe no roteiro do longo

- **problema:** A técnica de 23/11 que fez a piada soar contada, e não lida, depende do roteiro trazer a provocação e a virada em linhas separadas. Nos Shorts, o roteiro usa os moldes do repertório (1 tirada por trecho), sem esse formato. Assim o Fish recebe a piada inteira numa frase e lê tudo direto.
- **evidencia:** anime_script.py:849-870 (_COMENTARIO_NARRADOR com a PIADA DE VIRADA) é usado só em rewrite_longo_com_tempo (anime_script.py:907/977). O roteiro dos Shorts (_jeito_do_nicho, anime_script.py:178-275) tem moldes_piada/duplo sentido, mas não o formato de 2 linhas. PIADA_CONTADA está em anime_tts.py:1281-1283.
- **proposta:** Para Short de anime/manhwa (_TIPOS_COM_PIADA) com 5 frases ou mais: permitir no máximo 1 piada de virada em 2 linhas (a 2ª linha curta, 'Mentiraaa, galera!'). No Fish, a pausa vem do ponto final entre as frases (é assim que o _texto_fish já trata as pausas). A linha da virada ganha o _ritmo rápido do gol, e a tag [laughing] só se o achado 7 aprovar. Chave: PIADA_CONTADA (já existe), aplicada também ao Short.
- **risco:** medio
- **ja_existe:** Existe no longo (anime_script._COMENTARIO_NARRADOR + anime_tts._s2_tags_v13). No Short, não.

### 73. [narracao-shorts-fish] Whisper dos tempos das palavras roda na CPU do PC1 no caminho local do Fish

- **problema:** Depois de gerar, o fish_lote roda faster-whisper 'small' na CPU para a legenda cinética. Em 19/11 isso levou 75 min para 3 frases e travou a produção. O desligamento (FISH_TEMPOS=0) só é aplicado no caminho do lote do Kaggle, que está pausado. No caminho local, padrão FISH_TEMPOS=1, o Whisper volta a rodar no PC1.
- **evidencia:** fish_lote.py:84-96 (comentário de 19/11 sobre os 75 min; WhisperModel small cpu int8). lote_shorts_kaggle.py:157-161 é o único lugar que põe FISH_TEMPOS=0. shorts_kaggle.json ligado=false. LONGOS_MELHORIAS.md:363: sem words.json a legenda escorrega para o SFX.
- **proposta:** No Fish online já se sabe o texto exato. Usar alinhamento barato: o Whisper 'tiny' com 2 threads só quando a CPU estiver abaixo de 70% (mesma regra do INTRO_CPU_MAX) e, se não, a estimativa por sílaba dentro da duração real do mp3, deixando fx_subtitles esconder a legenda no SFX (LEGENDA_ESCONDE_NO_SFX já existe). Chave FISH_TEMPOS_MODO=tiny|estimar.
- **risco:** baixo
- **ja_existe:** FISH_TEMPOS=0 existe, mas só no lote do Kaggle. A estimativa por tamanho existe como reserva da legenda.

### 74. [postagem-recuperacao] O reagendar_nobre mexeu nos canais de CONTROLE do experimento do médico duas horas depois do sorteio

- **problema:** O médico escolheu como CONTROLE (sem mexer) o CenaReact, o Curiosidades Noturnas, o Fio da Meada e o AssistIA às 11:33. Às 13:22 o reagendar_nobre levou 7 Shorts do Curiosidades Noturnas e 1 do CenaReact para 21-22 h. O controle passou a receber o mesmo tratamento, e a comparação 'alavanca vs controle' (vs_controle >= 1,3) vai dar falso 'não melhorou'.
- **evidencia:** D:\video-fila\MEDICO.md: 'Curiosidades Noturnas: controle_so_nobre ... CONTROLE (não mexo, comparo)' e 'CenaReact: controle_so_nobre' (23/11 11:33). logs\reagendar_nobre.log: '[23/11 13:22:54] OK Curiosidades Noturnas: 3FONnkUd69U 24/11 13:30 -> 24/11 22:00' e mais 6 até 30/11, e '[23/11 13:24:51] OK CenaReact: fwbFz4n3S8c 26/11 11:00 -> 26/11 21:00'. grep 'controle|so_nobre|medico' em reagendar_nobre.py: nenhuma ocorrência. medico_recuperacao.py:266-268 calcula vs_controle.
- **proposta:** No reagendar_nobre.candidatos(), pular os canais cujo rampa_canais.json tem 'medico' começando com 'controle_' enquanto a medição não termina. Alternativa: o médico ignora como controle o canal que teve reagendamento no período (cruzando com o log). Para esta rodada, registrar em medico_recuperacao.json que o controle de Curiosidades e CenaReact foi contaminado.
- **risco:** baixo
- **ja_existe:** Não existe.

### 75. [postagem-recuperacao] Canal punido (1 por dia) com fila cheia agenda Shorts até 3 meses à frente (30/12, 02/01, 15/02)

- **problema:** Com punido = 1/dia (PUNIDO_POR_DIA), o laço de horario_publicacao (até 40 dias, politica.py:649-666) empurra o vídeo para o primeiro dia livre, e o parceiro aceita mesmo assim. O vídeo é enviado agora, fica privado meses, gasta upload (o 'limite diário' conta envio) e trava o estoque. Quando o canal sair da punição, a agenda continua presa nesses horários. A regra de DIAS_FRENTE = 7 do parceiro (parceiro_diario.py:41) não segura isso.
- **evidencia:** recapd-ambientes\producao\logs\parceiro_postar_auto.log: '[2026-11-21 23:10:52] Bilionário Noturno: AGENDADO ... -> 15/02 07:30 lá (pedido 06/01 07:30)', '[2026-11-22 23:57:42] Empresário Inteligente IA: ... -> 15/02 09:30', '[2026-11-23 00:13:57] Clínica Lucrativa IA: ... -> 15/02 09:30'. uploads_ledger: 39 Shorts com publish_at mais de 7 dias à frente (Dorama Noturno 25, Curiosidades 3, Bilionário 2, Empresário 2, Clínica 2, HistoriasEmFrames 1 com 2026-12-30, AssistIA 1 com 2027-01-02, CodigoInteligente 1 com 2027-01-01). fila_celulares\pendentes tem pedidos para 2026-12-30 e 2027-01-01 (historiasemframes, clinicalucrativaia, imovelemfoco, vendasqueescalam).
- **proposta:** Em politica.horario_obrigatorio/checar_upload: se o horário calculado passar de agora + AGENDA_MAX_DIAS (ex.: 7), devolver 'cota' (não sobe agora). O vídeo fica no estoque (Drive) e vai para um canal que rende, ou espera o canal sair da punição. Chave nova AGENDA_MAX_DIAS, com 0 desligando.
- **risco:** baixo
- **ja_existe:** Só existe o DIAS_FRENTE=7 do parceiro_diario, para planejar. Não há teto no politica.horario_publicacao, e os logs mostram vídeos agendados para 15/02.

### 76. [postagem-recuperacao] Canais recuperados perdem vagas: o envio pula Shorts 'prontos mas sem video.mp4' (estão no Drive)

- **problema:** Anime Noturno (3.101 views/dia contra 58 antes) e inovare manhwa br (parcial, 37%) têm rampa alta (extra 4), mas abriram só 3 e 2 Shorts em 23/11. Na rodada, o parceiro_postar varre dezenas de pastas que estão no Drive e pula. Só o escolhido volta do Drive na hora (_trazer_do_drive), e em canal com intervalo de 45 min entre envios (rajada) a vaga se perde.
- **evidencia:** parceiro_postar_auto.log em 23/11: 35 linhas 'está pronto mas sem video.mp4 — pulado' (Anime Noturno 15, inovare manhwa br 14, Inovaremanhwaversethai 4, Tech Noturno 2); 'Anime Noturno: último envio do canal às 17:06 — o próximo só depois de 17:51'. uploads_ledger, aberturas por dia: Anime Noturno 22/11 4, 23/11 3; inovare manhwa br 7 (14/11) caindo para 2 (23/11). rampa_canais.json: novo_animenoturno extra 3 + max_dia 3 (cadastro mostra extra=4 por canais.json); hNQrW5ouNe0Ni5Me extra 4. parceiro_diario.py:1498-1500 ('só o ESCOLHIDO volta do Drive, na hora de subir').
- **proposta:** Pré-busca: uma vez por hora, para os canais com rendimento alto (recuperado ou parcial na ronda), trazer do Drive os N video.mp4 das próximas vagas do dia (N = teto - abertos), fora do caminho do upload. Usa o _trazer_do_drive que já existe, com uma chave PARCEIRO_PREBUSCA=0 para desligar. Ocupa pouco disco (cerca de 25 MB por Short).
- **risco:** baixo
- **ja_existe:** Já existe _trazer_do_drive (parceiro_diario.py:954), mas só na hora do envio. A reserva de 1 mês no Drive (estoque_drive) é a causa.

### 77. [postagem-recuperacao] A agenda dos celulares e o cadastro ainda usam 15 h, hora marcada como EVITAR, e deixam de lado a 7 h (RECEITA)

- **problema:** Os sinais medidos em 2.160 Shorts dizem: 21 h = 8,9 vezes a mediana; 15 h = EVITAR (razão 0,53 e 0,70 nas duas metades); 7 h = RECEITA (1,5 e 1,8). Mesmo assim, o noite_encher planeja 15:00 em todo canal de celular, a escada usa EXTRAS=['15:00','18:00'], e 4 canais do cadastro têm horário de 15 h. A faixa 16-20 h também rende abaixo da mediana (0,67 a 0,8).
- **evidencia:** D:\video-fila\estado\sinais_shorts.json: hora 21 razao_med 8.9 (n 70); receitas hora 15 'EVITAR' (razao_antigos 0.53, recentes 0.7, n 77/78); hora 7 'RECEITA' (1.5/1.8); hora 16 0.67, 19 0.8, 20 0.78. D:\projeto celular sub controle\canal_pronto\noite_encher.py:33 HORARIOS = ['10:30','12:30','15:00','18:00','21:05']. escada_celulares.py: EXTRAS = ['15:00','18:00']. postagens_celular.jsonl, posts ok desde 20/11 por hora agendada: 15 h = 6, 18 h = 8. config\canais.json, horarios_parceiro/rede às 15 h: animescomia, filmenoturno, inovare_thai, manhwareact.
- **proposta:** Trocar 15:00 por 07:30 ou 22:30 no noite_encher.HORARIOS e na escada EXTRAS, e tirar o 15:xx de animescomia, filmenoturno e manhwareact no cadastro. É só configuração, com o comentário de data e o sinal que justifica. Não muda o número de posts por dia.
- **risco:** baixo
- **ja_existe:** O sinal está medido (sinais_shorts.json, 22/11) e o so_nobre/reagendar_nobre cuida das 21 h. Nada aplica o 'EVITAR 15 h' nem o 'RECEITA 7 h' na agenda.

### 78. [redes-tiktok-insta-fb] Escada do Facebook decide com a soma dos reels visíveis: leitura errada vira bônus de post e falso 'viral'

- **problema:** fb_escada._ganho usa a soma das views dos reels lidos na medição (1 a 8 visíveis). Se o número de reels lidos muda, ou se um reel vem com valor errado (play_count_reduced), o ganho fica negativo ou explode. Isso dispara 'estagnou, +1 Reel' ou 'Reel decolando, segura'. O leitor HTTP lê só o HTML inicial da aba Reels, sem paginação. Quando a Página passar de ~8 reels, os antigos somem da soma.
- **evidencia:** logs/fb_views.jsonl (261 linhas): 88 medições com 1 reel, 36 com 2, máximo 8. curiosidades, mesmo reel 1185451154437599: 793 views às 19:54 de 23/11 e 19 às 00:41 de 24/11. logs/fb_escada.log l.106: '[curiosidades] estagnou (+-773 x média 76): +1 Reel hoje', e config/fb_escada.json curiosidades com viral_desde 23:41 e bonus_dia 24/11 ao mesmo tempo. fb_escada.py:65-84 (soma por medição). services/facebook/paginas.py:39-57 (só o GET de profile.php?sk=reels_tab, sem cursor).
- **proposta:** Calcular o ganho reel a reel, como vigia_tiktok_ip.ganho: reel nos 2 dias = max(0, diferença); reel novo = o que já fez; reel que sumiu não conta. Ignorar queda > 50% no mesmo id (leitura ruim) em vez de usar. Para medir mais de 8 reels, guardar o último valor de cada id visto, em vez de exigir que apareça de novo, ou seguir o cursor da aba. Não fala com a conta além do que já é lido.
- **risco:** baixo
- **ja_existe:** A medição HTTP já existe (services/facebook/medir.py, fonte 'http' em 251 linhas); falta o ganho por reel.

### 79. [redes-tiktok-insta-fb] Instagram: foco congelado em 14/11 mantém conta com 0 view e deixa de fora as que dão view

- **problema:** O config/instagram_foco.json fixa 5 contas escolhidas por seguidores em 14/11, a no máximo 2 Reels/dia. fakenews.ia4, a de mais views, está pausada como 'inactive' até 26/11. futebolcom.ia2 segue no foco com 0 views nos últimos 12 reels. canalhistoriacomia e emerson.josiel.cu dão mais views e estão paradas. O teto da rampa já subiu (5 a 8/dia), mas o foco corta para 2, então o total fica em 8/dia.
- **evidencia:** config/instagram_foco.json: contas ['sintetizerisada','fakenews.ia4','_lucrocomia_','iapro.mentoria','futebolcom.ia2'], max_dia 2. D:/projeto-navegador-sem-navegador/logs/instagram_metricas.jsonl (última leitura por conta): fakenews.ia4 views_12 1566; emerson.josiel.cu 1000 (13/11); sintetizerisada 732; canalhistoriacomia 617, seguidores 1->3 (23/11); iapro.mentoria 23; futebolcom.ia2 0. logs/instagram_20261123.log: '[fakenews.ia4] em pausa até 26/11 00:20: conta inativa', '[sintetizerisada] teto da rampa: 8/dia ... restam 6'. instagram_auto_posted.json: 2/dia em cada uma das 4 de 20 a 23/11. postar_insta_auto.py:370-379 (foco corta para max_dia 2).
- **proposta:** Recalcular o foco 1x por semana a partir do instagram_metricas.jsonl (views_12 e ganho de seguidores), trocando conta com views_12 < 30 pela próxima com mais views. Na conta em foco que ganha view, deixar valer o teto da rampa (tetos.py), mantendo o intervalo de 4 h, em vez do 2 fixo. Mudar quais contas postam é decisão da dona (INSTAGRAM_ESTRATEGIA.md): levar a tabela a ela. E só depois de resolver o IP do achado 1.
- **risco:** medio
- **ja_existe:** INSTA_FOCO (14/11) e tetos.py (rampa) existem; um anula o outro e a lista não se atualiza.

### 80. [redes-tiktok-insta-fb] Relatório mostra 'Instagram: 0 leituras hoje' lendo um arquivo parado desde 14/11

- **problema:** A ronda lê D:/video-fila/estado/instagram_publico.jsonl (página pública com IP rotativo), que não é gravado desde 14/11. As métricas reais de views do Instagram estão em outro arquivo, gravado a cada post na sessão da própria conta. A dona não vê views do Instagram no relatório.
- **evidencia:** relatorio_ronda.py:760-766 lê estado/instagram_publico.jsonl. Últimas linhas desse arquivo: 'em': '2026-11-14T11:37' (62 linhas, 24 'null'). ronda_tarde.txt l.280: '- Instagram (contas de IA): 0 leituras hoje'. O arquivo bom: D:/projeto-navegador-sem-navegador/logs/instagram_metricas.jsonl, 234 linhas, última 23/11 09:19, com views_12/curtidas_12 (services/instagram/postar.py:375-399, IG_MEDIR). Nenhum .py de video-fila ou postador lê instagram_metricas.
- **proposta:** Em relatorio_ronda.sec_insta_http, ler instagram_metricas.jsonl: última leitura por conta, views_12, seguidores e ganho desde a anterior, no mesmo formato da tabela do Facebook. Manter o arquivo antigo como alternativa. Só leitura local.
- **risco:** baixo
- **ja_existe:** A coleta já existe (IG_MEDIR=1); falta mostrar.

### 81. [tarefas-agendadas] KaggleSaudeContas_0800 e _2130 apontam para script apagado

- **problema:** Duas tarefas ligadas rodam todo dia D:\tmp_logs\kaggle_verificar\saude_contas.py, que não existe mais, e falham com 'arquivo não encontrado'. Pelo nome, um 'saude_contas' que varre contas do Kaggle no PC1 é o tipo de laço que a regra proíbe. Se alguém restaurar o script, ele volta a rodar sozinho.
- **evidencia:** Último resultado 0x00000002 nas duas (COM). XML: '...pythonw.exe -X utf8 D:\tmp_logs\kaggle_verificar\saude_contas.py' com CalendarTrigger 08:00 e 21:30. ls D:\tmp_logs\kaggle_verificar -> 'No such file or directory'.
- **proposta:** Pedir à dona para apagar as duas tarefas. A saúde do Kaggle já é coberta pelo gerente/abastecedor, pela saída de cada conta.
- **risco:** baixo

### 82. [tarefas-agendadas] '1min visita diaria' falha todo dia e não grava nada desde 31/10

- **problema:** A tarefa diária que resgata os 15 mil créditos do 1min.ai sai com código 1, e o arquivo de visitas não muda desde 31/10. Os créditos diários não estão sendo resgatados, ou estão, mas sem registro. Ela também roda com pythonw direto, sem rodar_oculto, e fala como conta (aulacomia): o caminho de saída precisa ser conferido.
- **evidencia:** COM: '1min visita diaria' 0x00000001, última 24/11 06:10. D:\opus-gratis-v2-desktop\umin\visitas.jsonl: 22 linhas, modificado em 'Oct 31 23:50'; a última linha é de 2026-10-31T23:49:45. visita_diaria.py:30 LOG = AQUI / 'visitas.jsonl'.
- **proposta:** Rodar à mão uma vez (pela saída fixa da conta) para ver o erro, ou desligar se o 1min não é mais usado (a memória diz 'só opus-auto').
- **risco:** medio

### 83. [tarefas-agendadas] ZeladorSonnet trava em ssh de 120 s e falha todo dia

- **problema:** O zelador do Sonnet web chama ssh hermes-bloqueio e estoura o tempo. A tarefa termina com erro (código 1). Ele não cuida do Sonnet web, que é o único modelo que o vigia usa hoje.
- **evidencia:** COM: ZeladorSonnet 0x00000001 (última 24/11 04:20). D:\sonnet web\zelador_sonnet_saida.log (fim): "subprocess.TimeoutExpired: Command '[...ssh.exe', ..., 'hermes-bloqueio', 'python3 /opt/omniroute/sonnet_estado.py']' timed out after 120 seconds".
- **proposta:** Tratar o TimeoutExpired, registrar 'não conferi' (sem quebrar) e ver se o host hermes-bloqueio ainda é o certo. A regra 'ssh com script embutido trava' também pede um .sh por scp, não comando inline.
- **risco:** baixo

### 84. [vigia-relatorio] Fila do celular: 113 pedidos 'parado' (38 com vídeo pronto, 1 GB) que nenhum medidor nem relatório mostra

- **problema:** med_celulares só olha 'pendente', 'conferir', laços e adb. Pedidos 'parado' se acumulam: 28 por 'horário passou antes de postar' (vídeo renderizado e desperdiçado), 14 'nenhum Short Fish de esportes' no A3 e 5 'A3 sem chip'. A planificação continua mandando trabalho pro A3, que tem 42 parados. A ronda mostra só ok/erro do postagens_celular.jsonl.
- **evidencia:** D:\projeto celular sub controle\canal_pronto\pedidos\*.json: estados parado 113, PRONTO 60, preparar 10, aguardando 9, pendente 5. Por celular: A3 42, A2 22, S20U 17, S20 17, G20 15 parados. 38 parados com video_final existente = 1.06 GB; pasta videos\ = 1.9 GB. Motivos: 'horário passou antes de postar' 28, "nenhum Short pronto inédito da mídia 'esportes' com voz Fish" 14. vigilancia.py:399-472 (med_celulares sem 'parado'). relatorio_ronda.py:1035-1082.
- **proposta:** Em med_celulares: 'parado' criados nas últimas 24 h ≥ 8, ou 'horário passou' ≥ 3, abre alarme por celular. A mídia sem estoque Fish deve parar de planejar pro celular. Na ronda, uma tabela por celular com pendente/PRONTO/parado (motivo principal) e o GB de vídeo parado.
- **risco:** baixo
- **ja_existe:** Em 23/11, noite_encher.py:136-170 passou a reabrir 'parado' por erro passageiro (Command/post:). Não cobre 'horário passou' nem falta de estoque.

### 85. [vigia-relatorio] A tabela 'Vigilância' do relatório infla acertos e esconde que nada foi consertado

- **problema:** Na tabela, 'Acertou' = consertando + falso + real. Pedido enviado ao consertador e diagnóstico contam como acerto. A ronda mostrou 'Acertou 34 / Errou 1' e '12 consertos hoje', mas os 12 foram tentativas que caíram no Kiro ou falharam (sem_token 11), e não há aprovado desde 11/11. A lista de últimos eventos filtra passos que não existem ('consertou', 'conserto'), então só aparecem os 'falso'.
- **evidencia:** relatorio_ronda.py:543-545 (ok_v = consertando+consertou; Acertou = ok_v+falso+real); 503 (filtro com 'consertou','conserto'). ronda_tarde.txt: '| Vigilância | 98 | 34 | 1 |' e 'passos hoje: ... consertando 12, sem_token 11'. vigilancia_casos.jsonl: último 'aprovado' em 2026-11-11T15:10:37.
- **proposta:** Contar acerto só como aprovado (não 'voltou') e erro como falhou + desfeito + voltou. Mostrar à parte 'casos parados em consertar: N (mais velho de dd/mm)' e 'tentativas desviadas pro Kiro/sem token: N'. No filtro de eventos, trocar por ('aprovado', 'desfeito', 'dona', 'falhou', 'sem_token').
- **risco:** baixo
- **ja_existe:** O placar por agente é de 14/11 (RELATORIO_PLACAR_IA). A fórmula é a mesma desde então.

### 86. [vigia-relatorio] Relatório diz 'Pesquisador: Motor LIGADO', mas a dona pausou a tarefa

- **problema:** sec_pesquisador lê 'Motor: **LIGADO**' do PAINEL_PESQUISADOR.md. O painel parou de ser gerado em 23/11 11:41, quando a tarefa foi desabilitada, então o texto fica congelado como LIGADO e engana quem lê a ronda. A seção também mostra a fila do melhorador como '✅ em dia', também pausada.
- **evidencia:** schtasks MotorPesquisador: Status 'Desabilitado'. PAINEL_PESQUISADOR.md cabeçalho '— 23/11 11:41' e 'Motor: **LIGADO**'. ronda_tarde.txt: '- Motor LIGADO | hoje 19 pesquisas'. relatorio_ronda.py:581-590.
- **proposta:** Ler o estado real da tarefa (Get-ScheduledTask MotorPesquisador/MelhoradorCentral). Desabilitada = uma linha só, '⏸️ pausado pela dona em 23/11', sem números. Também mostrar a idade do painel.
- **risco:** baixo
- **ja_existe:** Não. A regra de pausa está no CLAUDE.md (23/11), mas o relatório não sabe dela.

### 87. [vigia-relatorio] Evidência do sem_sucesso perde o erro mais repetido (precedência do ternário)

- **problema:** Em med_sem_sucesso, o texto '; erro mais repetido 12 h (Nx): ...' entra só no ramo else do ternário, ou seja, só quando nunca houve sucesso. No caso comum (já teve sucesso e parou), o alarme, o Telegram e o topo da ronda chegam sem o motivo. Por isso o vigia precisa de IA pra descobrir um checkpoint que estava escrito no log.
- **evidencia:** D:\video-fila\vigilancia.py:382-384: f"{f}: último ... {ultimo_ok:%d/%m %H:%M}" if ultimo_ok else f"{f}: nenhum ..." + f"; erro mais repetido...". ronda_tarde.txt topo: '— D:\ms-energy\logs\carrossel.log: último 'PUBLICADO' em 20/11 22:40' (sem o erro).
- **proposta:** Pôr parênteses no ternário: (A if ultimo_ok else B) + '; erro mais repetido...'.
- **risco:** baixo
- **ja_existe:** Não.

### 88. [visual-shorts] Mascote T7 e gancho Remotion T5 estão 'ab' há 3 semanas sem nenhum vídeo B real

- **problema:** Os dois testes continuam sorteando e gastando metade da amostra num braço que não renderiza (achado 1). O placar diz 'dados suficientes, sem diferença clara', o que é esperado, já que os dois braços são idênticos. Isso polui a leitura dos outros testes e o sinais_shorts.
- **evidencia:** cortes_ajustes.json: "mascote": "ab", "gancho_remotion": "ab". Últimos 5 dias: mascote sorteado B=582 e renderizado B=4; gancho_remotion sorteado B=615 e renderizado 2 ('fora'). Pastas por data: masc_real = 76 em 31/10, 13 em 01/11 e depois 0-1. placar_cortes_testes.json: mascote B n=556 e gancho_remotion B n=528 com 'sem diferença clara ainda'.
- **proposta:** Ou portar o efeito para o libass (achado 1) e recomeçar a contagem a partir da data do porte, ou pôr "mascote": "A" e "gancho_remotion": "A" até o porte, com uma linha no historico explicando o motivo.
- **risco:** baixo
- **ja_existe:** Não. O historico não tem nenhuma linha sobre o caminho PNG ter saído do Short em 01/11.

### 89. [visual-shorts] 'Legenda lateral' está fixada mas não é aplicada, e o próprio placar diz que lateral é PIOR em retenção

- **problema:** O melhorador fixou legenda_impacto=lateral em 30/10 'sem views' (o próprio placar avisa isso). No libass o impacto sai sempre no centro, então o valor fixo não muda nada. O sinal 1,1x de 'lateral' em sinais_shorts vem de 666 postar.json que só carregam o rótulo. Os vídeos de antes de 30/10, que tinham lateral de verdade, dão pct_ge65 de 16% contra 36% no centro.
- **evidencia:** cortes_ajustes.json historico 2026-10-30T04:44 'legenda_impacto ab -> lateral' (motivo: impacto cobrindo rostos, sem views). placar_cortes_testes.json legenda_impacto: nota 'fechado em lateral pelo melhorador em 30/10 04:44 (sem views)'; centro pct_ge65=0,36 vs lateral 0,162; p_melhor_que_ref_pct65 lateral=0,023; sugestao "['lateral'] pior que centro". Postar.json dos últimos 5 dias: legenda_estilo lateral=1.222/1.223, com impacto centralizado em fx_subtitles.py:1031.
- **proposta:** Não ligar o lateral como 'vencedor'. Registrar no cortes_ajustes que o rótulo 'lateral' não representa o vídeo desde 01/11 e trocar o campo legenda_estilo para o que o libass realmente faz. Se a dona quiser o lateral, portar para o ASS (\frz) e reabrir como teste 'ab'.
- **risco:** baixo
- **ja_existe:** O valor 'lateral' já está fixado, mas sem efeito no vídeo.

### 90. [visual-shorts] Placar dos testes parado desde 17/11: gancho_meio, saudação e fala rápida sem decisão há uma semana

- **problema:** O placar_variantes.py não roda sozinho: o arquivo é de 17/11 e não há tarefa agendada com esse nome. Os testes T4 (gancho_meio), T9 (fala_rapida), T10 (saudação) e T13 (abertura, 1 vídeo medido) seguem 'ab'/'abcd' sem reavaliação. Os sinais de 22/11 apontam saudação A 1,29x, fala rápida A 1,2x e gancho_meio B 1,12x, mas o placar mais recente não confirma nenhum deles (por exemplo, saudação B p=0,826 no ajustado e p=0,207 no pct65).
- **evidencia:** ls: placar_cortes_testes.json/.md com data 17/11 20:44. 'schtasks /query' filtrado por placar|variante|sinais não devolveu nada. sinais_shorts.json (_quando 2026-11-22T05:43): saudacao A 1,29 vs B 1,2; fala_rapida A 1,2 vs B 1,0; gancho_meio B 1,12 vs A 1,06. placar_cortes_testes.json: gancho_meio, fala_rapida e saudacao 'dados suficientes, sem diferença clara ainda'; abertura 'esperando dados' (pergunta n=1).
- **proposta:** Agendar o placar_variantes.py (só lê e grava placar) uma vez por dia de forma oculta (rodar_oculto.vbs), depois do medidor de 48 h, e mandar o resumo para a ronda. Decidir saudação, fala rápida e gancho_meio só pela régua D1/D3 do placar, não pela razão crua do sinais_shorts.
- **risco:** baixo
- **ja_existe:** O script já existe (bin\placar_variantes.py); o que falta é rodar de forma recorrente.

### 91. [visual-shorts] Capa: 'pesca' (maior mídia, 1,23x) e negócios/saúde ficam fora do CaparShorts; 71% dos Shorts saem sem capa/1º quadro

- **problema:** O CaparShorts só capa anime/manhwa e os de QUADRO_REAL (dorama, filme_sem_voz, fatos). Pesca é a maior produção (433 de 1.223 em 5 dias) e um dos melhores sinais de mídia, mas nunca ganha o 1º quadro chamativo. Além disso, a tarefa perde vídeos por timeout de ffprobe/ffmpeg e o teste do quadro real tem um teto de 2 por rodada.
- **evidencia:** capar_shorts.py:33 QUADRO_REAL = ('dorama','filme_sem_voz','fatos'); :80-82 filtro por midia; :290-291 limites CAPA_QUADRO_REAL_POR_RODADA=2 e CAPAR_POR_RODADA=4. Postar.json dos últimos 5 dias: thumb False=874/1.223, capa_no_inicio True=309, midia pesca=433. sinais_shorts.json midia: pesca razao 1,23 (zerado 27%), fatos 1,28. logs/capar_shorts.log 23/11: 4 TimeoutExpired (17:17, 17:25, 23:50, 23:54) e 'rodada: 0 Short(s)'.
- **proposta:** Pôr 'pesca' (e talvez negocios/saude) em QUADRO_REAL como variante 'ab' pelo variantes.py (capa no 1º quadro x sem capa), medida no placar. Subir o teto de quadro real quando a fila de anime/manhwa estiver vazia.
- **risco:** baixo
- **ja_existe:** O CaparShorts e o quadro real (D:/fabrica-poses) já funcionam para dorama/fatos/filme_sem_voz. Pesca não está na lista.

### 92. [aprendizado-metricas] Posts pelos celulares ficam fora da medição (sem video_id)

- **problema:** Os celulares postam todo dia em canais próprios (Oculto Mundial, Segredos Revelados, Curioso Demais, Curiosidades do Mundo 3d, Dentro das Coisas 3D), mas nenhum desses posts entra no ledger com ID. Sem view, não dá para decidir se o celular ou esses canais valem o esforço (38 erros/dia).
- **evidencia:** D:\projeto celular sub controle\postagens_celular.jsonl: 66 'ok' e nenhum com video_id (campos: titulo, email, troca.canal, agendado_para…). uploads_ledger.jsonl: só 2 registros 'celular:<serial>' (18 e 19/11). relatorio_ronda.py:1079 diz 'Views desses posts ainda não são medidas'. Na ronda_tarde, a tabela kit3d mostra links 'youtu.be/celular:@dentrodascoisas3d:…'. metricas_rede.log: 'lote OcultoMundial: sem perfil… canal não encontrado'. Teste local: casando título normalizado com videos_canais.json, 9 dos 66 casam; os canais Oculto/Segredos/Curioso não estão na lista da API (nenhum slug deles).
- **proposta:** Script de reconciliação (só leitura de API pública, sem conta): pôr o yt_id desses canais em rede_canais.json para o videos_canais coletar, e casar cada post 'ok' do celular por (canal, título normalizado, publishAt ±30 min). Gravar o video_id no postagens_celular.jsonl e no uploads_ledger (projeto='celular'). A partir daí entram no sinais e no placar como 'origem=celular'.
- **risco:** baixo
- **ja_existe:** videos_canais.py já lê uploads por canal via API pública; falta o casamento e o cadastro dos canais.

### 93. [aprendizado-metricas] Médico da recuperação: bom molde, mas ainda não rodou pela tarefa e só cobre 2 alavancas

- **problema:** É o único laço com grupo controle e com aprendizado do que não funciona, e por isso deve virar o modelo dos outros. Hoje: a tarefa nunca rodou sozinha (a rodada de 23/11 foi manual), o controle é escolhido alternando a lista (não por sorteio) e só existem as alavancas so_nobre e descanso.
- **evidencia:** Get-ScheduledTaskInfo MedicoRecuperacao: LastRunTime 30/11/1999 (nunca), NextRun 24/11 07:10. estado/medico_recuperacao.json: 9 decisões em 2026-11-23T11:33 (5 so_nobre, 4 controle_so_nobre), nao_funciona=[]. rampa_canais.json: so_nobre '21-23' nos 5 canais tratados e None nos 4 de controle. medico_recuperacao.py:177-189 compara com o controle e marca melhorou com vs_controle>=1,3; DIAS_AVALIAR=3.
- **proposta:** Conferir amanhã que a rodada das 07:10 gravou sozinha. Extrair o núcleo (decidir → controle → avaliar em N dias → nao_funciona) para um módulo reaproveitável que o DecisorAB (achado 3) e o placar de longos usem. Sortear o controle (md5 do canal + data) em vez de alternar pela ordem de media_pre_ban.
- **risco:** baixo
- **ja_existe:** medico_recuperacao.py completo, MEDICO_ALAVANCAS=0 e estado/medico_recuperacao.off desligam.

### 94. [aprendizado-metricas] Receitas 'SORTE' nunca viram teste: o cruzamento acha hipótese e ninguém confirma

- **problema:** O receita_ou_sorte separa RECEITA/EVITAR/SORTE, mas SORTE (20 dos 26 vereditos) só vai para um .md. Nenhum processo dá mais amostra a esses valores para confirmar ou descartar, então a lista não converge.
- **evidencia:** estado/sinais_shorts.json 'receitas': 6 RECEITA, 4 EVITAR, 16 SORTE (ex.: narrador mike 0,44→2,67; iki 0,84→3,05; hora 22 1,02→3,56). Fora do próprio analise_sinais_shorts.py, nenhum .py lê 'receitas' (grep em video-fila, recapd bin, postador bin). RECEITAS_DO_SUCESSO.md é só para leitura.
- **proposta:** No DecisorAB, transformar cada SORTE de narrador ou fonte com n_recentes>=9 em 'teste dirigido': peso x1,5 na escolha (parceiro_diario._escolher_fonte / ranking de voz) por 7 dias, depois reclassificar. Se não repetir, volta ao peso normal. Chave RECEITAS_TESTE=0.
- **risco:** medio
- **ja_existe:** EVITAR já chega de forma indireta: fontes_por_canal 'geral' tem grananerd-k3r 0,4 e papodebixo 0,7 (via inteligencia_ajustada).

### 95. [arquitetura] 39 modulos com MESMO nome e conteudo DIFERENTE entre recapd/bin e postador/bin (risco de sombra no sys.path)

- **problema:** Script que poe os dois bins no sys.path importa a versao que vier primeiro, nao a mais nova. Hoje isso funciona por sorte da ordem do insert.
- **evidencia:** Comparacao md5 por nome entre os bins: 39 nomes divergentes, ex. claude_client.py (recapd 16/11 32193 B x postador 13/11 17221 B), gemini_llm.py (recapd 16/11 19384 B x postador 21/10 24403 B), censura_visual.py, narration_ensemble.py, motion_director.py, omniroute_tts.py, postagem_meta.py, curadoria.py. video-fila/reagendar_nobre.py:39 insere recapd/bin na posicao 0 e :76 insere postador/bin na posicao 1; video-fila/vitrine.py:119 (recapd/bin) e :474 (postador/bin) idem. Nestes dois nao achei import direto dos nomes divergentes (grep), entao hoje e risco, nao bug medido.
- **proposta:** Rodar 'python D:\hipercool-materiais\bin\recursos.py' (painel, so leitura) e usar a secao SEPARADOS como lista de trabalho; para os que nenhum outro projeto importa (test_*, omniroute_* antigos do postador de 07-09), marcar o nome com sufixo do projeto quando for mexer. Regra nova no LEIA_ANTES: script que poe 2 bins no sys.path tem que importar com 'import importlib.util' pelo caminho (como politica.py:274-277 ja faz) ou usar so modulos COMUM.
- **risco:** baixo
- **ja_existe:** recursos.py tem painel 'SEPARADOS' (recursos.py:272-279) que lista exatamente isso; mas so 22 modulos entraram no comum.

### 96. [arquitetura] Cadastro de canais em 5 arquivos + credenciais OAuth em JSON aberto lido por 23 scripts

- **problema:** O dado 'canal' tem 5 donos: config/canais.json (gerado), rede_canais.json, canais_status.json, rampa_canais.json e D:\credenciais-canais\youtube_canais.json. O gerador depende por caminho fixo de arquivos de OUTROS projetos. As credenciais (clientSecret/refresh_token) ficam em texto puro e sao lidas direto por muitos scripts em vez de passar pelo cofre.
- **evidencia:** postador/config/canais.json: 43 canais, '_leia': 'Cadastro UNICO... se refaz sozinho' ; rede_canais.json: 34 canais, '_leia': 'Mapa da rede de canais (fonte unica)' (duas 'fontes unicas'). politica.py:262-264 FONTES_CADASTRO inclui Path(r"D:\recapd-ambientes\producao\config\parceiro.json") e Path(r"D:\hipercool-videos\config\fila.json"). youtube_canais.json = lista de 71 entradas com clientId/clientSecret/refresh_token; 'youtube_canais.json' aparece em 23 arquivos .py; parceiro.json do recapd e lido por 11 arquivos fora do recapd.
- **proposta:** Manter politica.cadastro() como a unica porta de leitura (ja existe) e trocar, aos poucos, leitura direta de rede_canais/canais_status por politica.cadastro_do_canal()/estado_do_cadastro(). Para credenciais: um acessor unico (ex. politica.carregar_creds(), que ja existe) e grep periodico para leituras diretas novas. Ajustar o _leia do rede_canais.json para 'fonte de origem do cadastro' (texto, sem mudar logica).
- **risco:** baixo
- **ja_existe:** politica.cadastro() regera canais.json quando a origem muda (politica.py:267-281) e estado_do_cadastro calcula bloqueio na hora (politica.py:293-296).

### 97. [codigo-morto] Módulos comuns copiados à mão em 3 lugares (bin, postador e comum)

- **problema:** chaves_gemini, _tg_safe, edge_tts_engine, content_analyzer, contextual_motion, effects_memory e outros existem em 2 ou 3 cópias. Hoje estão iguais, mas uma correção feita numa cópia não chega nas outras, como já aconteceu com claude_client e censura_visual.
- **evidencia:** md5: producao\bin x comum têm 19 nomes em comum, os 19 idênticos. postador\bin x comum têm 13 em comum, os 13 idênticos. Exemplos: chaves_gemini.py com fd6f9694 nas 3 pastas e edge_tts_engine.py com c2e999ca nas 3 (bin modificado em 16/11, os outros em 30/10). Nenhum script de sincronização copia essas cópias: o único sincronizar_*.py do comum é sincronizar_github.py, que também não tem uso.
- **proposta:** Deixar a fonte em hipercool-materiais\comum e trocar as cópias por import, com sys.path.append ao FIM e nunca na frente (regra da memória 'pasta alheia nunca na frente'). Começar pelos 19 idênticos de bin x comum. Exceção: módulo que vai no pacote do Kaggle continua copiado pelo montar_pacote.
- **risco:** medio
- **ja_existe:** A memória 'Código comum' (reference_codigo_comum.md, recursos.py) já define o comum como fonte, mas as cópias continuam lá.

### 98. [disco-arquivos] R9-R12 e DISCO_MIN_GB ficaram fora do gerente: rodaram uma vez à noite como scripts soltos

- **problema:** O plano C5 pedia regras novas NO gerente e o uso de DISCO_MIN_GB 'de verdade'. Foram feitos D:\limpeza_c\noite\C5\r9_juri.py e r10_r12.py, executados uma vez (1,10 GB). O gerente_videos.py não tem R9-R12 nem DISCO_MIN_GB (aparece só no docstring), então ms-energy\videos, veo\beta\videos(_pos) e canal_pronto voltam a acumular.
- **evidencia:** grep em gerente_videos.py: 'DISCO_MIN_GB' só na linha 17 (docstring) e nenhuma ocorrência de R9/R10/R11/R12. D:\limpeza_c\noite\C5\progresso.md 05:04: 'R10-R12 aplicado: 107/107 movidos ... 1,10 GB'. D:\limpeza_c\noite\PLANO.md (C5): 'Usar DISCO_MIN_GB de verdade: se D: < 12 GB, a rodada roda as regras R9-R12 primeiro'. donos.json: canal_pronto\videos com 'limpa: NINGUÉM (GerenteVideos R12 proposto em C5)'. D:\veo\beta\videos = 1,9 GB e videos_pos = 960 MB (du).
- **proposta:** Importar r10_r12.py/r9_juri.py como funções em gerente_videos.limpar(), mantendo as mesmas salvaguardas (prova no ledger/log, parado há mais de 2 h, copyto + check 0, _NO_DRIVE.md), e rodar antes das demais regras quando shutil.disk_usage('D:').free < 12 GB. O CSV da A4 é estático, então a prova precisa vir do ledger e do postagem_log a cada rodada (o r10_r12 já revalida por PROVAS).
- **risco:** baixo
- **ja_existe:** Os scripts existem e foram testados em D:\limpeza_c\noite\C5 (simular e aplicar), mas não estão ligados a nenhuma tarefa agendada.

### 99. [narracao-shorts-fish] Reserva 'sem crédito = XTTS 8 no PC' não existe no PC1: cai no p3

- **problema:** O padrão de 23/11 diz: Shorts = Fish online 1º; sem crédito, XTTS 8 (PC). No Windows o XTTS só liga com um venv montado à mão em XTTS_VENV_DIR, e nenhum está montado. Por isso todo Short sem Fish sai no p3 (kokoro/francisca + RVC), que é o motor antigo.
- **evidencia:** anime_tts.py:1132 XTTS_VENV padrão '/tmp/venvs_voz/xtts'. anime_tts.py:1594-1596 'if os.name == "nt": return False  # nos PCs: venv montado à mão'. D:\tmp\venvs_voz não existe, e XTTS_VENV_DIR só aparece em anime_tts.py (grep em bin, config, colab e video-fila). MOTOR_DE_VOZ_PADRAO_23NOV.md: 'PC local (reserva) = XTTS 8 sozinho'. postar.json recentes: voz_base kokoro/francisca.
- **proposta:** Não montar XTTS no PC1 (regra 'PC1 livre pro VS Code'; o XTTS na CPU é pesado). Duas saídas: (a) a reserva sem crédito vai para a máquina de render remota (desktop/PC2) com o XTTS 8 montado lá, testado com teste_remoto.py --tipo pesado; ou (b) aceitar o p3 como reserva e corrigir o doc MOTOR_DE_VOZ_PADRAO_23NOV.md e a memória project_modos_de_voz (hoje dizem algo que não acontece). A decisão é da dona; registrar no doc.
- **risco:** baixo
- **ja_existe:** O código do XTTS existe e funciona no Kaggle. O que falta no PC é o venv, e a regra do PC1 desaconselha montar lá.

### 100. [narracao-shorts-fish] Short com narrador parceiro (Momo, Mike, Pie...) sai na voz do Chris: falta voz do narrador no site

- **problema:** No Short, o narrador escolhido pelo nicho só ganha voz própria no Fish se existir em vozes_site.json. Os 13 parceiros com referencia_fish.wav (Momo, Mike, KkVirjão, Pie...) não estão no site, então o Fish online usa a voz do Chris e o 'narrador' do Short perde a identidade. Os sinais mostram que o narrador importa: pie = RECEITA (1,56 → 1,88).
- **evidencia:** anime_tts.py:2052-2069: só fala de PERSONAGEM procura vozes_site.json, e o narrador vai para voz_do_nicho (Chris). COMO_OPERAR.md:366-368: 'narrador sem voz no site (parceiros: momo, guugou...) = não usa o site'. vozes_site.json: 66 entradas, só personagens e narradores públicos (ibere, cid...). sinais_shorts.json receitas: narrador pie RECEITA, n 12/16.
- **proposta:** Sem gastar crédito à toa (a regra de 19/11 proíbe gerar áudio no site só para ter referência): conferir no site se CRIAR um modelo privado a partir do referencia_fish.wav já existente cobra crédito. Teste em 1 conta, pela ponte dela, com 1 narrador (pie, que é receita). Se não cobrar e o modelo ficar visível para as outras contas (público ou não listado), cadastrar o id em vozes_site.json com papel 'narrador' e fazer _narrar_online usar a voz do narrador quando existir. Se o modelo valer só na conta que criou, NÃO fazer: obrigaria login em várias contas, e o risco de ligar as contas não compensa. Consentimento: só narradores em CONSENTIMENTOS.json / parceiros autorizados.
- **risco:** medio
- **ja_existe:** A colheita de referência de PERSONAGEM sem gastar existe (fish_lote._colher, colher_referencias.py). Narrador parceiro no site, não.

### 101. [postagem-recuperacao] Fila dos celulares: de cada 3 tentativas, 2 dão erro (troca de conta e câmera sem botão de importar)

- **problema:** Postar pelo celular (canal_pronto e escada) deu 18 ok e 38 erros em 23/11. Os erros vêm quase todos de dois aparelhos e de três telas: a troca de conta não abre (app do YouTube ou lista de Contas), a câmera do Shorts não tem o botão de importar, e o título não aparece no canal. Sem ID do vídeo, as views desses posts não são medidas, então o médico e a rampa não enxergam esses canais.
- **evidencia:** D:\projeto celular sub controle\postagens_celular.jsonl, por dia (ok/erro/incerto): 20/11 13/34/5, 21/11 15/3/5, 22/11 4/10/1, 23/11 18/38/1. Erros desde 20/11: 100.92.36.34 (A2) 'lista de Contas não abriu' 15, 'não vi o título no canal' 12, 'câmera do Shorts sem botão de importar' 9, 'app do YouTube não abriu' 8; 100.117.134.73 'app do YouTube não abriu' 13; 100.75.139.24 (G20) 'câmera sem botão de importar' 7; 2 casos 'NameError name forcar is not defined'. ronda_tarde.txt: 'Views desses posts ainda não são medidas (o app não devolve o ID do vídeo)'.
- **proposta:** (1) Corrigir o NameError 'forcar' (bug de código, aparece em 2 aparelhos). (2) No A2, que soma 47 dos erros, cortar a troca de conta: deixar 1 canal por aparelho e mandar os outros para aparelhos com 1 conta. Isso também reduz o risco do padrão de 17/11 (várias contas num aparelho). (3) Depois do 'ok', gravar o ID lido na lista 'Seus vídeos' no uploads_ledger para entrar na medição. Não religar a fila geral (PARAR.txt da dona).
- **risco:** medio
- **ja_existe:** fila_celulares\PARAR.txt (dona 17/11) segue valendo, e devolver_fila_celular.py devolveu 166 pedidos. O canal_pronto/escada é outro caminho e está ativo. A2 com 2 contas (2035 e 2042) e A3 com 2 (2054 e mrx) foram autorizados pela dona em 20/11 (comentário em escada_celulares.py:37-41).

### 102. [redes-tiktok-insta-fb] TikTok mede views 1x por dia, de uma vez, pelo Chrome de uma conta (msenergypara) e trava

- **problema:** medir_tiktok abre os 58 perfis em sequência no Chrome do cofre msenergypara (07:23). Nos dias em que trava ou o TikTok não abre, todas as decisões do dia seguinte ficam sem dado (amplificar, pausar zeradas, vigia). O 'abriu' de fabricadeautomacoesia, uma das 'boas', falha com frequência, e o vigia não pode julgar.
- **evidencia:** cron_medir_tiktok.bat (07:23, msenergypara). medir_tiktok.log: 19/11 '6 não abriram' (terminou às 11:14), 23/11 sem exit. tiktok_views/2026-11-23.json: fabricadeautomacoesia abriu=False 'TikTok - Make Your Day', emersonjosiel2027 'erro TimeoutError | about:blank'. vigia_tiktok_ip.json histórico: 'medição falhou hoje' em várias boas (IP 2 em 19, 20 e 21/11, IP 7 em 20 e 21/11).
- **proposta:** Ler a perfil público em várias passadas curtas ao longo do dia, ex.: 10 contas por vez, e reaproveitar o 'refaz só as que falharam' que já existe (medir_tiktok.py:64-66), com prazo total. Avaliar ler o perfil público por HTTP sem login (como medir_instagram_publico.py) pelo IP rotativo, sem sessão de conta. Não falar como conta: hoje o Chrome é da msenergypara lendo perfis alheios, confirmar com a dona que isso é aceito pela regra do IP. Teste fora do PC1 (teste_remoto.py).
- **risco:** medio
- **ja_existe:** Refazer as falhas (15/11) e TIKTOK_MEDIR_MAX_FALHAS já existem; falta prazo total e o fatiamento.

### 103. [tarefas-agendadas] Medidores TikTok_MedirViews, Marcas_Carrossel e MSEnergy_Metricas morrem no meio (0x8007042B)

- **problema:** Os três diários da manhã terminaram em 23/11 com o processo morto de fora (0x8007042B). O .bat não chegou a gravar o 'exit'. O MSEnergy_Metricas também deu HTTP 400. Resultado: as métricas de TikTok e Instagram de 23/11 ficaram sem medir. O horário bate com a faxina das 07-08 h (LimpezaChrome a cada poucos min fecha Chrome com mais de 3 h), mas isso não está provado.
- **evidencia:** COM: TikTok_MedirViews, Marcas_Carrossel e MSEnergy_Metricas com 0x8007042B. D:\postador-de-videos\logs\medir_tiktok.log: '[23/11/2026 7:34:09] === medir tiktok ===' sem 'exit=' depois (nos dias 20-22 terminou 'exit=0'). D:\postador-de-videos\logs\carrossel_marca_tarefa.log: '[23/11 7:22:11] inicio' sem 'fim'. D:\ms-energy\logs\metricas.log: 'HTTPError: HTTP Error 400' e '[23/11 9:19:01] exit=1' (em 02/11, 09/11 e 16/11 deu exit=0).
- **proposta:** Ver nos logs do LimpezaChrome/matar/liberar_ram de 23/11 07-10 h quem matou o processo. Marcar o Chrome desses medidores como 'em uso' para a faxina não fechar. Para o HTTP 400 do metricas_insta.py, ver o token ou o endpoint.
- **risco:** baixo

### 104. [aprendizado-metricas] Testes sem dado vivo continuam sorteando (abertura abcd e horario_fraco)

- **problema:** O teste 'abertura' (4 braços) tem 0-1 elegível por braço e divide a amostra em 4. 'horario_fraco' segue 'ab' embora a política de hora já tenha sido decidida (nobre primeiro e so_nobre do médico), então mede algo que o sistema já sobrescreve.
- **evidencia:** placar_cortes_testes.json: abertura contraste 0/15, custo 0/19, fato 0/17, pergunta 1/14 elegíveis, 'esperando dados'. horario_fraco: 'dá pra olhar (só indício)'. cortes_ajustes.json: abertura='abcd', horario_fraco='ab'. politica.py:641-648 força 21-23 h nos canais com so_nobre. parceiro_diario.py:1051+ põe o nobre primeiro.
- **proposta:** Fechar horario_fraco (fixar o valor que a política já usa). Reduzir abertura a 2 braços (fato x pergunta) até ter 12 elegíveis por braço. Regra no DecisorAB: no máximo 3 testes 'ab' ativos por vez nos Shorts.
- **risco:** baixo
- **ja_existe:** variantes.py aceita 'A' fixo para fechar (linha 19: 'Para fechar: "x": "B"').

### 105. [arquitetura] 16 arquivos falam direto com a API do Telegram, por fora do avisos.py

- **problema:** A regra 'Telegram so erro nao consertado, espera 30 min' vive no avisos.py; quem chama api.telegram.org direto escapa dela e de qualquer controle de duplicidade.
- **evidencia:** grep 'api.telegram.org/bot': video-fila/avisos.py, bots_conversa.py, painel_controlador.py, plantao.py; postador/bin/notificar_telegram.py, vigia_melhorias.py, _tg_safe.py; recapd/bin/anime_health_monitor.py, _tg_safe.py (+2 copias em _snapshots, 1 em _BACKUP_20260707); colab/vps_central.py; comum/notificar.py, _tg_safe.py, teste_salvar_github.py. _tg_safe.py esta no recursos.json (copia identica), notificar.py tambem.
- **proposta:** Nao mudar quem ja e o 'cano' (_tg_safe/notificar). Para os chamadores diretos (anime_health_monitor.py, vigia_melhorias.py, plantao.py, painel_controlador.py, vps_central.py) checar se mandam aviso de erro; se sim, trocar pela chamada do avisos.py. Um por vez.
- **risco:** baixo
- **ja_existe:** avisos.py e importado em 27 arquivos do postador e 37 do video-fila; falta fechar os desvios.

### 106. [arquitetura] Nenhum dos 6 projetos tem historico de versao local; protecao e por .bak solto

- **problema:** Sem git local, toda reorganizacao (inclusive a incremental proposta aqui) fica sem rede de seguranca e sem diff; a memoria da dona ja registra o trauma de git reset na producao, e o que sobrou foram arquivos .bak/.antes_sync espalhados.
- **evidencia:** Nenhum .git em recapd-ambientes/producao, postador-de-videos, video-fila, hipercool-materiais, manhwa-react, kit3d-producao (so D:\github_sistema/.git, ultimo commit 2026-11-23 'atualizacao automatica'). 20 arquivos *.bak*/*.antes* nos bins de recapd/postador/video-fila (ls). comum tem narracao_curva.py.antes_sync_1113_1316 e .bak_20261022_reacoes.
- **proposta:** Usar o espelho que ja existe: antes de cada passo de migracao, rodar o salvar_github.py (ja existente) e citar o commit no documento do passo, em vez de criar .bak. Git dentro da producao: so se a dona aprovar, e sem reset/checkout (regra dela).
- **risco:** medio
- **ja_existe:** D:\github_sistema + comum/salvar_github.py e sincronizar_github.py (espelho e merge 3 vias).

### 107. [codigo-morto] Chave ANIME_MASCOTE_TOM é gravada e nunca lida

- **problema:** O tom ou velocidade da mascote configurado em mascote.tom não tem efeito. A voz da mascote hoje sai da pausa gravada ou do clone, e a chave ficou da época do edge.
- **evidencia:** recapd-ambientes\producao\bin\anime-pipeline.py:1111 faz os.environ.setdefault("ANIME_MASCOTE_TOM", m.get("tom") or "+6%,+22Hz"). Os únicos leitores das irmãs estão em anime_segments.py:285 (FALAS), :288 (VOZ) e :326 (CLONE). Grep de 'MASCOTE_TOM' em bin e comum: só a linha 1111 e o docstring de anime_segments.py:282.
- **proposta:** Tirar a linha 1111 e o campo 'tom' do config da mascote, ou anotar que é só legado. Também vale confirmar se ANIME_MASCOTE_VOZ (pt-BR-FranciscaNeural, edge) ainda é usada fora da pausa, já que edge puro é proibido pela memória 'Vozes'.
- **risco:** baixo
- **ja_existe:** Não.

### 108. [codigo-morto] Chaves FLOW_* no cron_produto_videos.bat sem leitor na cadeia do postador (conferir)

- **problema:** O .bat da tarefa Produto_Videos define FLOW_HEADLESS, FLOW_ASPECT, FLOW_MODEL e FLOW_DURATION. Nenhum .py do postador ou do comum lê essas chaves, só o D:\veo\beta. Se o caminho atual não passa pelo veo\beta\config, a configuração é ilusória.
- **evidencia:** postador-de-videos\bin\cron_produto_videos.bat:6-10. Grep das 4 chaves em postador\bin e comum: 0 leitores. Leitores existem em D:\veo\beta\config.py, gera_auto.py, cron_gerar_video_llm.py e monitor_recursos.py. produto\video.py:639 e :711 fazem sys.path.insert(0, r"D:\veo\beta"), então PODE chegar ao config.py. Por isso o caso fica como 'conferir', não como morto confirmado. O log produto_videos.log mostra a tarefa viva às 15:00 de hoje.
- **proposta:** Ler produto\video.py nas linhas 630-720 e confirmar se a função importada de veo\beta usa FLOW_MODEL e FLOW_DURATION. Se não usar, tirar as 4 linhas do .bat ou passar os valores explicitamente.
- **risco:** baixo
- **ja_existe:** Não.

### 109. [codigo-morto] Scripts de diagnóstico e engenharia reversa soltos em video-fila (testes\ 12, engenharia_reversa\ 10, estado\*.py 8)

- **problema:** Ficam .py dentro de estado\ (pasta de JSON), entre eles ocioso.py.bak e ytdlp_vez.py.bak, e scripts de teste de leads de 01/11 que nada chama. Isso confunde quem procura o código vivo do ytdlp_vez e do ocioso.
- **evidencia:** Sem referência: video-fila\estado\_conta_prioridade.py, _semear_leads.py, _teste_lead_real.py, _teste_leads_whatsapp.py, _teste_portao_leads.py, _teste_vigia_leads.py, _ver_ponte.py e esperar_desktop_telao.py. Em testes\, 12 sem uso (teste_guarda.py 39 KB, teste_camada_opus.py 24 KB, todos de 24/10). Em engenharia_reversa\, 10 sem uso (de 29 a 30/10). Em estado\ também: ocioso.py.bak_20261030_0135/_0405 e ytdlp_vez.py.bak_20261030_1120.
- **proposta:** Mover os .py de estado\ para testes\_arquivo\ e deixar estado\ só com dados. A engenharia_reversa fica onde está porque é análise, conforme a memória 'Engenharia reversa = análise', mas ganha um LEIA.md dizendo que não roda em produção.
- **risco:** baixo
- **ja_existe:** Não.

### 110. [codigo-morto] Utilitários vivos que parecem mortos: teste_remoto.py, memes_pt_baixar.py e cenas3d_no_longo.py (NÃO mover)

- **problema:** A varredura também marca scripts chamados só à mão ou recém-criados. Movê-los quebraria regras da dona. Ficam aqui como lista de exceção para quem fizer a limpeza.
- **evidencia:** video-fila\teste_remoto.py tem 0 referências em código, mas é a ferramenta obrigatória do CLAUDE.md global ('python D:\video-fila\teste_remoto.py --tipo ...'). memes_pt_baixar.py e producao\bin\cenas3d_no_longo.py foram modificados em 24/11, hoje. mover_testes_imagem_drive.py (21/11) é citado pela memória 'Testes de imagem no Drive'.
- **proposta:** Na limpeza dos achados 2 e 11, pular estes e qualquer arquivo modificado nos últimos 7 dias ou citado em CLAUDE.md, MEMORY.md ou LEIA_*.md.
- **risco:** baixo
- **ja_existe:** Não existe lista de exceção.

### 111. [disco-arquivos] Logs grandes: um morto (82 MB) e um crescendo sem rotação (34 MB). Os do video-fila estão sob controle

- **problema:** Nas pastas do mapa não há log acima de 100 MB. Fora delas, há um log morto que pode sair e um jsonl de saúde que só cresce.
- **evidencia:** find -size +20M em video-fila, postador, recapd (bin/colab/logs), comum, manhwa-react/logs, kit3d e hipercool-videos/logs: só D:\tools\drive_central\logs\inovaremanhwabr.log (86.471.675 bytes, parado em 12/11) e D:\projeto-navegador-sem-navegador\logs\saude.jsonl (35.633.320 bytes, gravado em 24/11). Em video-fila\estado, os maiores são avisos.jsonl (4,98 MB), uso_maquinas.jsonl (2,9 MB) e canais_views_hist.jsonl (1,6 MB). logs\faxina.jsonl tem 8 MB.
- **proposta:** Compactar ou apagar o inovaremanhwabr.log (com a decisão da dona, já listada no A6). No escritor do saude.jsonl, rotacionar quando passar de 10 MB (renomear para .1 e manter um). Os demais não precisam de ação agora.
- **risco:** baixo
- **ja_existe:** Já apontado em D:\limpeza_c\noite\A6\resultado.md §2, sem ação aplicada.

### 112. [disco-arquivos] O gerente ignora *.partial do rclone nas pastas de Short e as sobras .tmp do estado

- **problema:** Quando um download ou upload do rclone é interrompido, fica um <arq>.<hash>.partial dentro da pasta do Short. O inventário do gerente só olha .mp4/.mov/.mkv/.webm, então essas sobras não aparecem e não saem.
- **evidencia:** D:\hipercool-materiais\animes recap\shorts\sem-obra-15dbe0_cap1_20261122\video.mp4.aaf6fe74.partial (23,5 MB, 23/11 18:23). No cache_reuso há 6 *.partial (52 MB, 17,8 MB e outros, de 23-24/11). Em video-fila\estado há 6 celulares_medida.<pid>.tmp de 0 byte (18/11 a 23/11). gerente_videos.py:52, VID = ('.mp4', '.mov', '.mkv', '.webm').
- **proposta:** Em inventario(), tratar '*.partial' com mais de 6 h nas pastas de Short como uma regra R2b (apagar), porque o rclone não retoma o .partial dele. No celulares.py, apagar o .tmp quando a escrita atômica falhar (try/finally).
- **risco:** baixo
- **ja_existe:** A R2 cobre só capa_tmp e *.tmp.mp4 (gerente_videos.py:116-117).

### 113. [modelos-ia] Pausa de 15 min do Argon depois de UMA falha manda 866 textos para a reserva sem nem tentar

- **problema:** Qualquer erro do Argon (inclusive um 429 ou um RemoteDisconnected isolado) grava argon_pausa.txt por 900 s, e todo texto desse período vai direto pro Gemini 3.8. Isso não é desperdício de cota, mas tira o Argon de 866 textos numa semana: o modelo escolhido pela dona para o texto do vídeo não é usado, e a comparação Argon x Gemini fica torta.
- **evidencia:** modelo_texto.jsonl desde 17/11: as 1042 chamadas do agy/gemini-3.8-flash-high são todas reserva; reserva_de='pausa' 866, Timeout 136, 429 32. Código: claude_client.py:476-480 (pausa 900 s em qualquer erro).
- **proposta:** Pausar só depois de 2 falhas seguidas, ou pausa curta (3 min) no 1º erro e 15 min a partir do 2º. Vale junto com o timeout menor (achado 4).
- **risco:** baixo
- **ja_existe:** Pausa fixa de 15 min (27/10). Não tem contagem de falhas seguidas no _texto_video (o ia_saude.json do generate_text_vivo já conta falhas_seguidas, mas não é usado aqui).

### 114. [modelos-ia] Vigilância: 'pergunta' do vigia com mediana de 222 s e até 45 voltas para confirmar alarme simples

- **problema:** O vigia (Gemini 3.8 via claude.exe) recebe voltas=45 e lê logs para confirmar cada alarme. Para categorias em que o medidor já é a prova (reserva-canal, postagem-facebook com 20 vigias, sem-sucesso-*), isso é caro e sem ganho: o 'falso' saiu só 24 vezes em 238 vigias na semana.
- **evidencia:** painel_ia desde 17/11: 223 'pergunta' agy/gemini-3.8-flash-high terminou + 11 erro, mediana 222 s. vigilancia_casos.jsonl desde 17/11: 238 'vigia', 24 'falso', 199 'real'. Código: vigilancia.py:637-644 (voltas=45, LIMITE de 10 leituras só no texto do prompt).
- **proposta:** Por categoria, uma lista 'sem_vigia_llm' (começando por reserva-canal) que vai direto para 'real' com a evidência do medidor; para as outras, voltas=15.
- **risco:** baixo
- **ja_existe:** Não. O limite de 10 leituras está só no texto do prompt; o teto real é voltas=45.

### 115. [narracao-longos] Os testes solo dão alarme falso de revezamento

- **problema:** Os longos de teste 'só Momo', 'só Mike' e afins são solo por pedido da dona, mas a CONFERENCIA marca '❌ Narradores por grupo (sem revezamento)'. Isso polui o placar ('11 de 13') e esconde as falhas de verdade.
- **evidencia:** CONFERENCIA de RzoyNcnlIj8, e2nIzNGXvmA_xtts_momo, 82ge1YYkUyA_s2pro e 82ge1YYkUyA_qwen3: '❌ (sem revezamento)'. e2nIzNGXvmA_xtts_momo\render.json: narradores_modo 'solo'. No total, 29 de 124 conferências falham nesse item.
- **proposta:** Quando narradores_modo for 'solo' no render.json, a linha sai como 'n/a', sem ❌.
- **risco:** baixo
- **ja_existe:** Não encontrei o gerador da CONFERENCIA em producao\*.py. Ele deve estar no pacote do Kaggle. Não há tratamento de solo.

### 116. [narracao-shorts-fish] Velocidade base: não acelerar o Fish por igual (o teste fala_rapida mostra que o +15% rende menos)

- **problema:** É tentador ligar prosody.speed 1,1-1,15 em tudo para 'ficar dinâmico'. Os dados dos Shorts dizem o contrário, e a dona também: nos longos, o que funcionou foi variar por frase (gol acelera, piada desacelera), não acelerar tudo.
- **evidencia:** sinais_shorts.json (22/11, n=2160): fala_rapida A (normal) razao_med 1,2, acerto 39 (n=321) x B (+15% fala, anime_publish.py:586) 1,0, acerto 35 (n=324). Memória feedback_narradores_jeito_de_falar: o Fish já vem na velocidade natural (Momo 227 ppm x 221 real); 'piada = devagar sempre'; piso 0,92 na frase lenta.
- **proposta:** Manter o Fish online em speed 1 (de quebra, reaproveita o histórico grátis) e deixar toda a variação para o _ritmo_fish (achado 2). Desligar o braço B do teste fala_rapida quando o Short for narrado pelo Fish. Não registrar como proposta nova de religar nenhum melhorador (estão pausados).
- **risco:** baixo
- **ja_existe:** O teste fala_rapida existe (variantes.py:40, CORTES_FALA_RAPIDA). A ligação com o motor de voz, não.

### 117. [postagem-recuperacao] Ficam 14 pedidos velhos em fila_celulares\pendentes, alguns com data já passada (20/11) e outros para 30/12 e 01/01

- **problema:** A fila geral está parada (PARAR.txt), mas o pendentes ainda tem 14 pedidos que o devolver_fila_celular não devolveu (pulou: o posted_url é outro ou não há postar.json). Três são de 20/11 (inovaremanhwabr), quatro de 21/11 (cenareact) e outros agendados para 30/12 e 01/01. O distribuidor sobe de novo a cada ~30 min e para no PARAR. Se a dona tirar o PARAR, sobem Shorts velhos em horário vencido ou meses à frente.
- **evidencia:** fila_celulares\pendentes (14 arquivos): 20261118_024505...json inovaremanhwabr agendar '2026-11-20 08:30' (3 assim); 20261119_*.json cenareact '2026-11-21 08:30' (4); 20261123_091720...json historiasemframes '2026-12-30 07:30'; clinicalucrativaia '2026-12-30 09:30'; imovelemfoco e vendasqueescalam '2027-01-01 09:30'. fila.log 24/11 00:14 a 01:08: 'distribuidor de pé' e logo depois 'PARAR.txt — distribuidor parado', 4 vezes.
- **proposta:** Rodar a limpeza (o devolver_fila_celular.py já faz isso) com um critério a mais: pedido com 'agendar' vencido ou mais de 7 dias à frente vai para devolvidos_23nov, e o vídeo original volta para a fila normal. Fazer isso antes de qualquer decisão de religar a fila. Só com o OK da dona, porque mexe em estado.
- **risco:** baixo
- **ja_existe:** Já existe devolver_fila_celular.py (23/11), que devolveu 166 pedidos (pasta devolvidos_23nov) mas pulou estes 14.

### 118. [redes-tiktok-insta-fb] TikTok: contas paradas por máquina sem disco e Chrome remoto caído entram em toda rodada

- **problema:** Várias falhas de 23/11 são da máquina, não da conta: o desktop sem espaço em disco e o CDP recusando. A conta tenta, falha, e o post vai para a próxima rodada, 90 min depois. Hoje só o relogin tem uma trava de 3 falhas (feita em 23/11).
- **evidencia:** logs/tiktok_20261123.log: 4x 'falhou no desktop (abrir Chrome: [WinError 112] Espaço insuficiente no disco)', 3x 'connect_over_cdp: socket hang up', 2x 'ECONNREFUSED', 2x 'ERROR: file input not found after 120s'. 98 falhas no dia (ronda_tarde.txt l.194). A trava do relogin (postar_tiktok_auto.py:128-157, TIKTOK_RELOGIN_MAX) é só para login.
- **proposta:** Na rodada, guardar as máquinas que falharam com erro de máquina (WinError 112, ECONNREFUSED, ssh) e tirá-las da rodada, como já se faz com ip_fora (postar_tiktok_auto.py ~l.445-460). Avisar o disco cheio do desktop uma vez, pelo avisos.py. Chave, ex.: TIKTOK_PULA_MAQUINA_FORA=0.
- **risco:** baixo
- **ja_existe:** TIKTOK_PULA_IP_FORA (19/11) para o IP; nada parecido para a máquina.

### 119. [tarefas-agendadas] 11 tarefas de 'uma vez' já vencidas seguem ligadas (lixo de testes e lembretes)

- **problema:** Tarefas de disparo único que já passaram continuam ligadas e poluem a lista e o relatório: AmostraGanchoDona, GeminiChavesRetentativa, HipercoolReligar_0211, LembreteFacebook21Nov, LembreteKaggleTelefone, LembreteTikTokIPs e 5 NSN_CapturaFB_* de 20/11. A HipercoolReligar_0211 é perigosa: se alguém a disparar à mão, ela religa a produção do hipercool 'religado sozinho 02/11'.
- **evidencia:** xml.json: TimeTrigger sem repetição, StartBoundary entre 2026-10-23 e 2026-11-21, Enabled=true. HipercoolReligar_0211, ação: 'controle.py ligar hipercool producao "religado sozinho 02/11 01:00 (pausa da dona por disco cheio)"'. As NSN_CapturaFB_criar_1337/1637/1937 rodam o mesmo 'capturar_passivo.py 45' (duplicadas).
- **proposta:** Listar para a dona apagar (ou desligar) as 11.
- **risco:** baixo

### 120. [tarefas-agendadas] AmostraGanchoDona aponta para o scratchpad de um chat no C:

- **problema:** A tarefa ligada roda um .bat dentro de AppData\Local\Temp\claude\...\scratchpad, uma pasta temporária de sessão que já não existe. Falha desde 30/10 e infringe a regra 'nada no C'.
- **evidencia:** xml.json: AmostraGanchoDona, '"D:\rodar_oculto.vbs" "C:\Users\Haylla\AppData\Local\Temp\claude\D--hermes-pc-base\af3c5b53-...\scratchpad\amostra_gancho.bat"' (o arquivo não existe, conforme a checagem os.path.exists). COM: 0x00000001, última execução em 30/10.
- **proposta:** Apagar a tarefa (com o OK da dona).
- **risco:** baixo

### 121. [tarefas-agendadas] MonitorOpus roda python.exe direto (sem rodar_oculto) a cada 10 min

- **problema:** É a única tarefa ligada que usa python.exe (com console) e não passa pelo rodar_oculto.vbs nem usa pythonw. Com LogonType S4U não deve abrir janela, mas fica fora do padrão 'sempre oculto' e abre janela se o tipo de logon mudar.
- **evidencia:** C:\Windows\System32\Tasks\MonitorOpus: <Command>...Python313\python.exe</Command> <Arguments>D:\monitor_opus.py</Arguments>, <Interval>PT10M</Interval>, <LogonType>S4U</LogonType>. Processo vivo às 06:16: 'python.exe D:\monitor_opus.py'.
- **proposta:** Trocar para pythonw.exe, ou passar pelo wscript rodar_oculto.vbs como as demais.
- **risco:** baixo

### 122. [tarefas-agendadas] Tarefas de estudo e teste já encerradas seguem ligadas (AcompanharNoite21Nov, InstalarPC3, ArgonManterLogon)

- **problema:** AcompanharNoite21Nov foi feita para 'a noite 21/11' e roda a cada 20 min desde 21/11 (rclone no Drive). O log mostra NaoConferi repetido. InstalarPC3 ficou ligada com falha (código 1) desde 27/10. ArgonManterLogon duplica o ArgonManter (mesmo argon_manter.py, que já roda a cada 5 min e deu 0x800710E0).
- **evidencia:** AcompanharNoite21Nov: docstring de D:\tmp\estudo_voz\acompanhar_noite.py:1 'Acompanhamento da noite 21/11'; TimeTrigger 2026-11-21 rep=PT20M, ligada; acompanhar_noite.log termina em 'NaoConferi: manhwa-drive:baixador/prontos/e2nIzNGXvmA'. InstalarPC3: COM 0x00000001, última 27/10. ArgonManter/ArgonManterLogon: os dois apontam para D:\gemini-argo\argon_manter.py (an.py == DUP).
- **proposta:** Perguntar à dona se o acompanhamento de 21/11 acabou e, se sim, desligar. Apagar InstalarPC3. Manter só o ArgonManter.
- **risco:** baixo

### 123. [tarefas-agendadas] 12 tarefas desligadas há mais de 30 dias, algumas com caminho quebrado

- **problema:** Desligadas antigas que só poluem a lista: MegaEngageMonitor (desde 17/07), HistoriasEmFrames-Producao (28/07, 0xFFFFFFFF), VeoProducaoDiaria7h (31/08), AgendadorVO3 (16/10), AnimeRecapNoturno, HipercoolFila, HipercoolShorts2h, TrocarVenvUnico, HipercoolVigia, AnimeOcioso, AnimeRecapMonitor e Trader Binance - limpeza de dados. Algumas apontam para arquivos que não existem: Trader Binance (venv e limpeza_dados.py), Atlas sincronizar/vigia (rodar_oculto.vbs do atlas), Laboratorio - papeis, VozFidelidadePiloto. Cinco nunca rodaram (Cortes_Agente, Cortes_Melhorador, HipercoolReligarProducao, MSEnergy_Gerar, MelhoradorProdutos). Pesquisador e melhoradores pausados pela dona ficam como estão.
- **evidencia:** estado_tarefas.txt (COM, Enabled=False, ordenado por LastRunTime): MegaEngageMonitor 2026-07-17, HistoriasEmFrames-Producao 2026-07-28 0xFFFFFFFF, VeoProducaoDiaria7h 2026-08-31 0x8007042B, AgendadorVO3 2026-10-16 etc.; as 5 com '1999-11-30' (nunca rodaram). Saída 'MISSING' do an.py: D:\trader_binance\atlas\rodar_oculto.vbs, D:\trader_binance\trader_binance\deploy\limpeza_dados.py, D:\hipercool-materiais\amostras_voz\clone2\fidelidade\piloto_fidelidade.py e laboratorio\papel\rodar_papeis_oculto.vbs, todos inexistentes.
- **proposta:** Entregar a lista à dona para apagar as que têm caminho quebrado ou nunca rodaram, e exportar o XML das demais para uma pasta de arquivo antes de apagar. Não tocar em MotorPesquisador, CobradorPesquisador, MelhoradorCentral e RecapMelhoradorLongo (pausados por decisão dela).
- **risco:** baixo

### 124. [vigia-relatorio] Seção 3D publica links quebrados 'youtu.be/celular:@...' como se fossem vídeos

- **problema:** Shorts 3D postados pelo celular gravam no ledger um id falso do tipo 'celular:@handle:data'. A ronda monta 'https://youtu.be/' + id, gerando 5 links inválidos (um com ':None'), e conta esses Shorts como 'postados' sem ID real nem views.
- **evidencia:** relatorio_ronda.py:965; ronda_tarde.txt: 'https://youtu.be/celular:@dentrodascoisas3d:2026-11-20 21:10', '...:None' (3d-geladeira-v2).
- **proposta:** Se o id começar com 'celular:', mostrar 'postado pelo celular dd/mm hh:mm (sem ID)' em vez do link. Contar esses à parte de 'postados com ID'.
- **risco:** baixo
- **ja_existe:** Não.

### 125. [vigia-relatorio] Seção 'Outras línguas' fixa em 2 IDs de 27/10: ocupa espaço e roda rclone à toa

- **problema:** sec_frentes consulta, toda ronda, 2 pastas fixas da fila do Drive criadas em 27/10 (vietnamita e inglês) e sempre responde 'saiu da fila (pronto/postado)'. São duas chamadas rclone lsf por ronda sem informação nova.
- **evidencia:** relatorio_ronda.py:432-436 (pids fixos 20261027_000010_PDPOK7xOyas e 20261027_000011_dLd0uCJVaEc); ronda_tarde.txt 'Longo em vietnamita: saiu da fila' e 'Longo em inglês: saiu da fila'.
- **proposta:** Tirar essas 2 linhas, ou trocar por contagem dinâmica de longos não-pt na fila. Deixar só a 'Lista de prioridade'.
- **risco:** baixo
- **ja_existe:** Não.

### 126. [visual-shorts] Tratamento de capa B (receita 'B:drama' 2,0x/1,38x) está desligado: CAPA_TRATAMENTO nunca é definido

- **problema:** O _tratar_capa devolve 'A' sempre que CAPA_TRATAMENTO for diferente de '1', e nenhum script, .bat ou JSON define essa variável. A receita B:drama não volta a ser produzida e a amostra fica parada em 9+14. A dona pediu em 01/11 'capas sempre coloridas e não dark', o que pesa contra a C, mas não necessariamente contra a B, que só tinge de leve.
- **evidencia:** anime_publish.py:257-260 (comentário de 01/11 da dona + 'if os.environ.get("CAPA_TRATAMENTO") != "1": return "A"'). grep CAPA_TRATAMENTO em bin/colab/config e em D:/video-fila: só a própria linha 259. Postar.json dos últimos 5 dias: capa_variante A=39, B:romance=1, vazio=1.183. sinais_shorts.json receitas: capa_variante B:drama RECEITA razao_antigos 2,0 (n 9), razao_recentes 1,38 (n 14).
- **proposta:** Perguntar à dona se a B (tinta de gênero com alfa 0,45, sem escurecer) entra na regra 'colorida, não dark'. Se entrar, ligar só A/B (sem a C) com CAPA_TRATAMENTO=1 restrito a A/B. A amostra é pequena (23), então continua como teste.
- **risco:** medio
- **ja_existe:** O código existe e está desligado de propósito desde 01/11 (decisão da dona sobre capas escuras).

### 127. [visual-shorts] Já ligados por padrão (não propor de novo): hora 21-22 h, delogo, Short curto, 'NINGUÉM ESPERAVA' liberado

- **problema:** Para fechar o cruzamento com o sinais_shorts: os vencedores de horário e cobertura já estão no padrão. O curto=B e o ninguem_esperava=A também, mas só no PC1 (ver achado 3).
- **evidencia:** parceiro_diario.py:973-975 horas_nobres() padrão HORARIO_NOBRE_BR='21,22' e :1051-1073 (nobre primeiro na fila); sinais_shorts hora 21 = 8,9x (receita 20,25x recente). cortes_ajustes.json "cobertura_legenda": "delogo" (sinal delogo 1,11x; postar.json 5 dias: delogo 887, nada 335). cortes_ajustes "curto": "B", "ninguem_esperava": "A" (historico 17/11 20:55). ronda_tarde.txt:57-65: canais em so_nobre/controle_so_nobre ainda com só 0-9 Shorts às 21-22 h em 20-44.
- **proposta:** Nada a ligar aqui. O ponto aberto é de quantidade: canais com poucos Shorts às 21-22 h (ronda 23/11), o que já é acompanhado pelo médico da recuperação.
- **risco:** baixo
- **ja_existe:** Sim: HORARIO_NOBRE_BR, cobertura_legenda=delogo, curto=B, ninguem_esperava=A.

### 128. [visual-shorts] Shorts renderizam em 720x1280 e são esticados para 1080: ANIME_RENDER_1080 nunca é ligado

- **problema:** Todo o motor de efeitos roda em 720x1280 e só no fim sobe para 1080 (scale + unsharp). A regra do 1080p mínimo é cumprida, mas o texto da legenda e o que vem do quadro saem reamostrados. O _fx_choque também exige exatamente 720x1280. O comentário de 31/10 diz que a comparação de custo/qualidade do render nativo nunca foi concluída.
- **evidencia:** fx_assets.py:41-45 (_HD = ANIME_RENDER_1080 == '1'; senão W,H = 720,1280). grep ANIME_RENDER_1080 em bin/colab/config: só fx_assets.py:41. fx_subtitles.py:1127-1151 (upscale para 1080x1920 com unsharp quando min(vw,vh) < 1080). fx_subtitles.py:309 (_fx_choque só funciona com (W,H) == (720,1280)).
- **proposta:** Testar fora do PC1 (teste_remoto.py --tipo render) um Short com ANIME_RENDER_1080=1 contra o padrão: medir tempo e conferir a nitidez da legenda por print. Se o custo couber, virar variante 'ab' no variantes.py. Os quadros de fx precisariam de versão 1080 ou de um scale no overlay.
- **risco:** medio
- **ja_existe:** A chave existe (31/10) e está desligada; não há registro da comparação.
