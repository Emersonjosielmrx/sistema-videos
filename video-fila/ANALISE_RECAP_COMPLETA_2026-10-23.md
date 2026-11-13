# Análise completa do RECAP (Cortes / Shorts de parceiro) — 23/10/2026 (claude-8a)

Pedido do dono (23/10 ~01:05): "analise todo o projeto e faça todas as melhorias possíveis que encontrar; analise cada
categoria, cada função e cada código melhorando ele". Feito DIRETO (Opus: sem Workflow/subagente, regra do dono), RETOMÁVEL:
cada achado é gravado aqui na hora. Crons "continue": 01:19, 05:13, 06:14. Outras sessões mexem no recap ao mesmo tempo:
antes de editar, conferir a data do arquivo; backup `.bak_20261023_<motivo>`; py_compile + teste; produção nunca para.

## Inventário (D:\tmp\analise_recap\inventario.py -> vivos.json)
57 módulos VIVOS (fecho dos imports + subprocessos a partir de parceiro_diario e anime_auto) de 180 no bin; 17.697 linhas.
Maiores: fx_clips 1889, parceiro_diario 932, anime_auto 875, fx_subtitles 857, edge_tts_engine 730, fx_detect 718,
narracao_curva 712, gemini_tts 689, anime_script 638, fx_music 604, anime_discover 569, anime_publish 512.

## Frentes (status)
- [x] F1 pyflakes nos 57 vivos: nome indefinido (bug que só explode na hora), import sobrando, variável morta.
- [x] F2 erros/avisos REAIS dos logs de 20-23/10 (_parceiro_*.log, parceiro_producao.log, parceiro_postar*.log),
      agrupados por tipo e contados; consertar os que mais se repetem.
- [x] F3 padrões de risco no código vivo: subprocess sem timeout, janela piscando (sem CREATE_NO_WINDOW), estado JSON
      sem escrita atômica, except que engole erro calado, caminho de outro usuário/PC escrito no código.
- [x] F4 tempo de cada etapa do Short (de onde vêm os 13 min) e o que dá pra cortar sem perder qualidade.
- [x] F5 qualidade do que sai: auditoria dos Shorts prontos (D:\tmp\auditoria_shorts.py) em amostra grande.
- [ ] F6 revisão por módulo (do maior pro menor), função por função, só no que tem prova de problema.

## Achados e consertos (na ordem em que foram feitos)
- F1 (01:20) pyflakes nos 57 vivos: 63 avisos (D:\tmp\analise_recap\pyflakes.txt). ÚNICO bug real: fx_clips.py
  build_clip / build_clip_with_shake / build_clip_animated montavam a chave do cache do clipe com `color_filter` ANTES
  de ele existir -> NameError engolido pelo except -> cache de clipe NUNCA valia nessas 3 (re-render sempre). Conserto:
  chave com `mood` (ou nada no animated). Backup fx_clips.py.bak_20261023_cache_cor; py_compile ok. Obs.: o recap NÃO
  usa essas 3 (só concat_with_xfade e add_dynamic_music do motor); ganha quem usar o fluxo de painel. Conferidos e
  inofensivos: edge_tts_engine `proxy` (o _try_generate(use_proxy=True) carrega por dentro), fx_subtitles `th`,
  master_loudness `testes` (script de teste). 31 imports sobrando + 9 f-strings sem variável + 6 "import *" do
  effects_engine = cosmético: NÃO mexi (risco sem ganho em arquivo de produção).
- F2 (01:35) logs 20-23/10 (D:\tmp\analise_recap\erros_logs.py e por_dia.py): 2.853 linhas, 118 tipos. Por dia:
  RESOLVIDOS — Edge TTS "Proxy falhou" 1.098 + pool esgotado 10 + 20 frases perdidas = SÓ 20/10 (o serviço respondia
  "No audio was received"); upload "Locator.click Timeout" (Dicas 56, Forja 40, Filme 8) parou após o conserto das
  hashtags de 22/10 02:20; disco cheio/memória = 20/10; KeyError 'limite' (27, o tipo novo de bloqueio do P03 sem lugar
  no STATUS_BLOQUEIO) = último 22:46, consertado por outra sessão 23:08; KeyError 'tom_extra' (3 em 21/10) já usa .get.
  AINDA ACONTECE — capa IA recusada pelo filtro + reserva sem saldo (53 em 21/10, 15 em 22/10): proposta pro dono =
  gerador do Flow (D:\flow-imagens) como reserva, mas ele usa as contas do Veo que fazem o MS Energy (cliente): DONO
  decide. Pausa do IP / "Nenhum candidato" = frente da sessão principal + estoque na pausa (feito 22/10 23:00).
  (Atualização: a memória diz que outra sessão já ligou o Flow nas capas via flow-imagens\cliente.py — conferir antes.)
- F3 (01:50) riscos nos vivos (D:\tmp\analise_recap\riscos.py): 15 subprocess sem timeout. O curl do gemini_llm já tem
  --max-time; o resto é render (limitado pelas 6 h do parceiro_diario) ou ffprobe/tasklist. PROVA: 541 rodadas desde 18/10,
  mediana 2 min, maior real 94 min (a de 193 min em 18/10 foi fechada à força): nenhum travamento -> NÃO mexi (risco no
  coração sem ganho). Caminhos C:\Users\Emerson-IA no anime_fetch = de propósito (PC2 usa o mesmo bin). except: puro
  só em volta de ffprobe = inofensivo. F3 sem conserto.
- F4 (02:00) tempo: 32 Shorts prontos em 22/10, mediana 18 min (soma 669 min = o PC1 produziu ~11 h das 24); download+
  transcrição mediana 1 min (soma 45 min); só 1 Short pegou o "espaçando downloads ... esperando N min" (ytdlp_vez da
  sessão principal, depois de 3 bloqueios no dia). Gargalos: (1) pausas do IP = PC1 parado ~13 h/dia -> estoque na
  pausa (feito); SUGESTÃO pra sessão principal: no "espaçando downloads", preferir candidato do estoque em vez de
  esperar 10 min; (2) render+voz clonada ~17 min/Short -> GPU do Kaggle (frente da claude-c2).
- F5 (02:20) auditoria de 31 Shorts de 22/10 (D:\tmp\auditoria_shorts.py 00:00): nenhuma imagem parada no fim, volume
  -17 dB em todos. ACHADO 1 = SINCRONIA: em 22/10, 21/21 Shorts com legenda do YouTube tiveram "roteiro com tempo",
  0/11 dos feitos pelo Whisper (proxy da legenda barrado) — 1 em 3 Shorts sem a fala no quadro certo. CONSERTO
  (backups *.bak_20261023_tempos_whisper; não toquei no anime_fetch, que é da sessão principal): _whisper_sub.py grava
  <wav>.tempos.json ([[início, texto]], formato do legenda_tempos.json) e anime_auto._prepara_candidato move pra
  legenda_tempos.json quando a legenda do YT não veio (>= 3 trechos). Teste: fonte real 30 s -> 6+ trechos com tempo,
  saída normal igual. CONFERIR: log "[fetch] tempos do Whisper viraram legenda_tempos.json" + "roteiro com tempo".
  ACHADO 2 = iyZiQ1Q2M08 saiu com 220 s (Short do YouTube vai até 180 s): ver abaixo.
- F5 (03:52) TETO DE 180 s: 2 de 303 Shorts de parceiro em 20-22/10 passaram de 180 s (the-spoiled-little-princess 220 s
  Dorama Noturno; o-marido-m4tou-sua-família _hi 185 s) = viram vídeo comum, fora do feed de Shorts. CONSERTO no fim do
  render (anime-pipeline.py, cobre pt e idiomas, que também passam por ele): `_teto_short` — vertical acima de 178 s é
  acelerado (imagem+voz juntas, setpts+atempo) na medida exata pra fechar em 176 s, até 1,25x; acima disso só avisa e
  deixa (voz rápida demais). Backup anime-pipeline.py.bak_20261023_teto180; py_compile ok; teste com vídeos sintéticos
  (D:\tmp\teto180\teste.py): 200 s -> 176,1 s; 60 s intacto; 260 s intacto + aviso. CONFERIR: log
  "Short tinha N s: acelerado".
- F6 (04:05) ACHADO 3 — SHORTS MORRENDO POR IMPORT DO HIPERCOOL: 3 Shorts perdidos (22/10 23:24, 23/10 01:53 e 02:30) com
  `ImportError: enhance_narration_audio from fx_foley (D:\hipercool-videos\bin)` e `add_dynamic_music() unexpected
  keyword 'no_copyright'`. Causa: monitor_bordoes._transcrever (criado 22/10 22:06 pro R7) fazia
  sys.path.insert(0, D:\hipercool-videos\bin) e deixava lá; os imports seguintes do mesmo processo (fx_foley, fx_music)
  pegavam a versão do hipercool. Só acontecia em narração com bordão (intermitente). CONSERTO: o caminho entra no FIM
  (hp_common continua o do recap) e sai logo depois do import do groq_api. Backup monitor_bordoes.py.bak_20261023_syspath;
  teste real (Groq pelo proxy): depois da transcrição fx_foley/fx_music/hp_common vêm do recap e o hipercool sai do path.
  Varredura dos outros sys.path.insert em tempo de execução: D:\video-fila (anime-pipeline, _tg_safe, notificar) e
  D:\flow-imagens (imagem_reserva) NÃO têm nome igual a módulo do recap; propaganda_lateral nem existe (só deitado).
  CONFERIR: zero "unexpected keyword argument 'no_copyright'" / "enhance_narration_audio" depois de 04:05.
- F6 (04:00) idiomas "0/0 línguas" desde 22/10 = NORMAL: as 6 línguas ativas estão com fila 2/2 e agendadas até 29/10
  (fila_alvo 2 por língua desde 21/10). Whisper rc=1 de 01:16 = falha ao carregar o modelo (linha 31), 1 vez só, não é
  da mudança dos tempos. "publish erro: name 'os'" (22/10 12:46) = 2 min depois de outra sessão salvar
  anime_voz_clonada.py; hoje pyflakes limpo -> já resolvido.
- F6 (04:10) ACHADO 4 — UPLOAD TRAVADO POR TAGS (> 500 caracteres): desde 22/10 21:46 (Curiosidades Noturnas) e 23/10
  02:03-03:46 (Esporte Noturno, Fio da Meada, Manhwa Noturno, ManhwaReact) toda rodada dava "não cheguei no passo
  Visibilidade"; print logs\yt_web\*_erro_visibilidade.png = campo de tags VERMELHO no Studio. Duas causas:
  (a) youtube_web_poster cortava as tags em 480 contando só vírgulas, mas o Studio conta as ASPAS de cada tag com espaço
  (28 tags: 470 pelo código, 518 no Studio). Conserto: soma len+2 por tag com espaço + vírgulas <= 480 (backup
  postador\bin\youtube_web_poster.py.bak_20261023_tags500). No vídeo que travava: 26 tags, 462 no Studio.
  (b) o funil de 22/10 (seo_generator, tags "quentes") colava as 8 tags que mais renderam em QUALQUER nicho: Short de
  futebol com 'manhwa hindi', 'webtoon hindi', 'resumo de filme', 'melhor cena do cinema' (metadado enganoso + estouro).
  Conserto: nova tag_do_nicho — tag com palavra de nicho (manhwa, filme, dorama, futebol, hindi...) só entra se o vídeo
  já é daquele nicho; genérica ('curiosidades interessantes') entra sempre (backup seo_generator.py.bak_20261023_tags_nicho).
  Teste: futebol -> só a genérica; filme -> as 2 de filme + genérica. Limpos os 7 pendentes (pronto/esperando) em
  postar.json+metadata.json (gravação atômica). Avisada a claude-2c (os arquivos 66ae4e/ab0048 mudaram no mesmo segundo).
  CONFERIR: rodada ParceiroKaijinre-Postagem 04:15 sobe Esporte/Fio da Meada/Manhwa Noturno sem "passo Visibilidade".
- F6 (04:15) outros itens conferidos: (1) capa IA no Short VALE o tempo (2-4,5 min): o Studio aceita capa personalizada
  em Short (print yt_web 20261023_034358_capa.png); a demora é a cadeia de reserva (Cloudflare recusa -> Flow). (2) RVC
  do clone = 30-38 s por frase na CPU (+40 s pra carregar), ~10 min por Short: frente da GPU (claude-c2), não mexi.
  (3) "roteiro com tempo veio com 0 frases marcadas" (2 em 25, respostas de 1,5 s e 8 s): o aviso agora grava os
  160 primeiros caracteres da resposta pra saber a causa na próxima (anime_script.py.bak_20261023_log_tempo).
  (4) placar "tags" registra só as 12 primeiras tags do vídeo; as quentes entram no fim -> não se realimentam.
- F6 (04:32) CONFIRMADO NA PRODUÇÃO: rodada 04:15 -> Esporte Noturno SUBIU 04:25 (C3jYbTtyYfE, o vídeo que travava
  desde 02:03; ledger). Fio da Meada 04:21 = "O limite diário de envios foi alcançado" (as tentativas travadas
  gastaram a cota; volta em 24 h ou com a verificação por telefone do dono). ManhwaReact 04:26 = "Processamento
  interrompido" num vídeo da rede manhwa-react (IA/negócios, lbfx8E6B9tY) — arquivo que o YouTube não processou, não é
  tag nem recap. PENDE DO DONO: envios privados que sobraram das tentativas (listar com youtube_studio_extras.py
  --canal <id> --limpar-rascunhos; apagar só com o ok dele).
- F6 (04:38) CONFIRMADO ACHADO 1 (tempos do Whisper): 23/10 depois do conserto, 3/3 Shorts feitos pelo Whisper
  (02:42, 03:01, 03:22) saíram com "roteiro com tempo" (8, 8 e 12 frases); antes, 0/4 no mesmo dia. Falhas do clone
  (22/10 05:28-05:36, rc=1 e 0xC0000005) pararam depois da nova tentativa em 90 s que outra sessão pôs 23/10 00:12.
- STATUS (04:38): F1-F5 feitos; F6 feito no que tinha prova nos logs/prints (achados 3 e 4 + itens conferidos). Falta
  CONFERIR depois: zero "no_copyright"/"enhance_narration_audio" nos logs; "Short tinha N s: acelerado"; Manhwa Noturno e
  Fio da Meada voltando a subir (cota volta em 24 h); a 1ª resposta registrada de "0 frases marcadas".
- F6 (05:22) TAREFAS DA MADRUGADA: (1) ReacoesColheita 01:30 saiu calada (log 0 bytes, rc 0) — BUG MEU de 22/10: o "40"
  do --max-pedidos virava filtro de nome de voz e nenhuma voz casava. Conserto em hipercool-materiais\bin\reacoes_colheita.py (backup .bak_20261023_argv) + linha "início" no log. Teste real (porao, 3 pedidos): lista os 15
  vídeos OK, mas a legenda pelo proxy volta "Sign in to confirm you're not a bot" nos 3 proxies (o MESMO bloqueio da
  legenda da produção, 39x em 22-23/10) -> a colheita só rende quando os proxies voltarem a passar; nada a mudar no
  código. (2) TrechosNoite 03:20 desistiu numa pausa de "mais 1 min": agora espera pausa de até 30 min se acabar antes
  das 06:30 (trechos_noite.py.bak_20261023_espera; teste com pausa simulada: esperou 150 s e seguiu).
  (3) ForjaReact sem vídeo novo desde 19/10: espera de 24 h do limite até 23/10 12:13 (126 tentativas de 18-22/10);
  verificação por telefone = item do dono. Curiosidades Noturnas no limite, mas agendado até 28/10 (sem buraco).
- F6 (05:25) CONFIRMADO ACHADO 3 NA PRODUÇÃO: 05:09 o monitor_bordoes transcreveu 2 bordões (jessie_toy_story:
  "Iiiiii-hajjj!" 0,33 ESTRANHO; "Céus dos cachorros!" 1,00) no meio do anime-pipeline — a mesma situação que matava o
  Short — e o Short ficou PRONTO 05:11 (RPqhJDOAyfU). Zero "no_copyright"/"enhance_narration_audio" depois de 02:30.
- F6 (05:30) ACHADO 5 — LEGENDA DO YOUTUBE MORTA DESDE 22/10 ~13:00: "legenda YT obtida" 64 (20/10), 62 (21/10), 25 (22/10,
  última 12:59), 0 de 10 em 23/10 (todas "not a bot"/429 pelo proxy). Cada Short levava de 25 s a 20 min (mediana ~4 min,
  soma 59 min em 10 Shorts, com a fila do yt-dlp) até desistir, e cada "not a bot" tirava 1 proxy da roda por 1 h (22
  hoje; os mesmos do download de emergência). CONSERTO no anime_auto (NÃO no anime_fetch, que é da sessão principal):
  _legenda_yt = disjuntor — 6 falhas seguidas = direto pro Whisper (que agora dá roteiro com tempo); 1 teste a cada 2 h;
  legenda já baixada numa rodada anterior é usada sem pedido. Estado em producao\logs\legenda_disjuntor.json
  (semeado com as 10 falhas reais de hoje). Backup anime_auto.py.bak_20261023_disjuntor_legenda; teste com fetch simulado:
  8 Shorts falhando = 6 pedidos; depois de 2 h testa, legenda volta = fechado. CONFERIR: "[auto] legenda do YouTube
  pulada" nos próximos Shorts e "VOLTOU — disjuntor fechado" quando o proxy passar.
- F6 (05:35) VIGIA APRENDENDO ERRADO: a IA do vigia (01:55 e 02:35) culpou "cache .pyc desatualizado" pelo TypeError
  no_copyright e apagou o bin\__pycache__ (inofensivo, mas o erro voltou às 02:30). Corrigido no VIGIA_DIARIO.md: os 2
  blocos ganharam "DIAGNÓSTICO ERRADO" e entrou o bloco RESOLVIDO "20261023_0405" com a causa real (sys.path) e como
  reconhecer; `base_consertos.py buscar` agora devolve esse caso em 1º (nota 26). Disco D: 9,0 GB livres às 05:27 (mín.
  8; o backup de hora em hora + guardião cuidam).
- F6 (05:45) ACHADO 6 — ESTOQUE VAZIO E NUNCA REPOSTO: o estoque salvou 3 Shorts na pausa de hoje (02:30, 02:57, 03:16,
  zero download), mas está em 0/8 e "estoque: +N" NUNCA apareceu no parceiro_producao.log: estoque_fontes.repor só
  baixa com o D: >= DISCO_MIN_GB (10 GB) e o disco está em 5-9,8 GB há dias -> próxima pausa do IP = produção parada de
  novo. O motivo saía só no logging (que o parceiro_diario não grava): agora sai "estoque: nada reposto (0/8; disco
  9.8 GB < 10 GB)" (parceiro_diario.py.bak_20261023_estoque_log). NÃO mexi no estoque_fontes (sessão principal):
  SUGESTÃO = DISCO_MIN_GB 8,5 (8 fontes de Short ~ 0,3 GB; a produção para em 8) ou liberar ~1 GB no D:. Obs.: no
  estoque, entre "uso o ESTOQUE" e "veio do ESTOQUE" iam 4-12 min de tentativa de legenda — o disjuntor corta isso.
- F6 (05:58) CONFIRMADO ACHADO 5 NA PRODUÇÃO: 05:57:03 "[auto] legenda do YouTube pulada (10 falhas seguidas; testa de
  novo a cada 2 h) — vai pro Whisper" e o download começou no MESMO segundo (antes: 25 s a vários min de tentativa). 2ª
  prova do achado 3: 05:40 monitor_bordoes (patrick_estrela) no meio do render e Short PRONTO 05:42. A linha "estoque:
  nada reposto (...)" aparece no fim da próxima rodada (a de 05:01 carregou o parceiro_diario antes da mudança).
- F6 (06:20) ACHADO 7 (SÓ DOCUMENTADO — decisão de produto): 13 de 50 Shorts com roteiro com tempo (20-23/10) têm o último
  corte VOLTANDO no original (ex. 0 7 14 6) = a última frase repete imagem já mostrada. 9 são de 1-2 s (imperceptível),
  4 são grandes (5-8 s) — todos de fonte CURTA (16, 20, 22, 56 s) com narração 1,4-2x maior. Causa de fundo: em 12 dos 13
  a NARRAÇÃO É MAIOR QUE O ORIGINAL — anime_auto mira 5,5 s por frase com mínimo de 5 frases (21/10), mas a frase real sai
  com ~7,5 s (5 a 10 s): a narração passa o original em ~30% e a imagem se repete ao longo do Short (sobreposição de 1-2 s
  por corte) e no fim. NÃO mudei (ritmo/tamanho de todos os Shorts; em 21/10 a escolha foi não espremer a história).
  Opções pro dono: (a) mínimo de 3 frases quando a fonte tem < 30 s (só os casos graves, ~1 por dia); (b) divisor 7,5 no
  lugar de 5,5 (todo Short ~25% mais curto, ~1:1 com o original); (c) deixar como está. Recomendo (a).
- (10:14) RASCUNHOS APAGADOS com o ok do dono: 21 envios presos (Esporte Noturno 8, Curiosidades Noturnas 7, Manhwa
  Noturno 6, Fio da Meada 0), todos cópias de envios que travaram; os vídeos ficam no PC e sobem de novo. A ferramenta
  (youtube_studio_extras.limpar_rascunhos) não apagava linha "Processamento interrompido" (botão "Excluir vídeo" na linha,
  sem menu Opções e sem miniatura): consertado (backup .bak_20261023_rascunho_falha). Conferido: 0 rascunhos nos 3.

## RODADA 23/10 TARDE — aprovado pelo dono (~10:20): "1 sim, verificação pendente; 2 sim tudo; 3 começa pelo Flow; voz
## clonada sim; corrija o mesmo defeito em outros projetos". Crons continue 14:23 e 15:23.
- [x] T1 FEITO 10:30: anime_auto (parceiro) fonte < 30 s = 3 frases (backup anime_auto.py.bak_20261023_fonte_curta)
- [x] T2a FEITO: estoque_fontes DISCO_MIN_GB 10 -> 8,5 (backup .bak_20261023_disco)
- [x] T2b FEITO: ytdlp_vez.espera_download_s() (COMUM, subido p/ hipercool/manhwa-react/recapd) + anime_auto usa o
  ESTOQUE quando o download esperaria > 2 min (log "download esperaria N min — uso o ESTOQUE"); backups .bak_20261023_espera/_estoque_espaco
- [x] T2c DIAGNOSTICADO: os 97 são Webshare ROTATIVOS (IP novo a cada pedido); teste direto 15 pedidos de legenda =
  1 ok, 8 "not a bot", 6 x 429 (~7%). yt-dlp 2026.10.21 (atual). Retry não resolve. Saída = proxy RESIDENCIAL (pago)
  ou cookies na legenda (regra atual proíbe mexer em cookie do yt-dlp) -> DONO decide. Sem mudança de código.
- [x] T3 JÁ ESTAVA: imagem_reserva.MODELOS tem o Flow em 1º desde 22/10; hoje 5/5 capas IA saíram pelo Flow (os ~4 min
  são o próprio Flow no navegador).
- [x] T4 AVALIADO: Kaggle pronto e testado (9,5 min de narração em ~17 min de ida e volta), mas Short NÃO compensa
  (ida e volta > os ~10 min de CPU); o ganho é em vídeo GRANDE = peça 7 do GPU_KAGGLE_VIDEOS_GRANDES.md, dono escolhe o
  1º projeto (anime longo do Cortes no PC2 ou compilado do hipercool).
- [x] T5 FEITO: 137 inserts de pasta de outro projeto em 10 projetos; só 2 com módulo de mesmo nome e outra versão:
  hipercool bin\vigia_telegram.py (postador na frente, 20 módulos diferentes: claude_client, effects_engine...) =
  CONSERTADO igual ao recap (append + import politica + remove; backup .bak_20261023_syspath; teste: politica lê o ledger,
  claude_client volta a ser o do hipercool) — vale no próximo início do vigia_telegram; postador comercial_veo.py = insert
  dentro de um subprocesso próprio (inofensivo).

## RODADA 23/10 11:00 — dono: "adicione na inteligência as melhores escolhas de fontes (as que dão mais resultado); nas
## outras línguas tente outros tipos de vídeo além de manhwa; 4 sim: aumentar postagens de maneira inteligente — quando a
## rampa sobe (ex. 4 -> 5) vale nos dias seguintes já agendados (abre mais 1 vaga em cada dia), e agendar SEMPRE em ordem:
## preenche um dia pra poder fazer o próximo". Crons continue 14:23 e 15:23.
- [x] U1 FEITO: parceiro_diario._escolher_fonte.uso — peso do placar "fontes" vale com 2 medidas e vai de ~0,3x a ~2,5x
  (era 1x-2x com 3); sem medida 1,2. Ex.: d_UCSJ6_g 2/2 = 2,5x; xiuliamelo 2/3 = 1,7x; king_chan01 1/7 = 0,45x.
- [x] U2 CONFERIDO: placar provocacao 8/19, busca 6/21, curiosidade 5/22 -> sorteio dá provocação 76% (3000 sorteios). Nada a mudar.
- [x] U3 FEITO: parceiro_diario._linguas_para — cada canal de língua sorteia o nicho (Thompson no placar nicho_canal;
  sem medida = aposta) e só ganha a versão quando a fonte é desse nicho (ou 15% teste); fila vazia = qualquer nicho;
  finanças fora. Simulação: manhwa -> ru/it 15%, vi/hi 23-24%; fatos/dorama/filme -> 25-30% em todas. Log "línguas: ...".
- [x] U4 FEITO: (a) CAUSA da rampa não valer: politica.teto_canal cortava em max_dia do cadastro (3 em 19 canais) ->
  o degrau soma também ao max_dia (postador politica.py.bak_20261023_rampa_maxdia); (b) parceiro_diario: por_dia =
  cadastro + degrau da rampa (8 canais em +1 = 4/dia, todos os dias), vaga extra no meio do maior intervalo dos
  horários, e agenda EM ORDEM (dia mais próximo completo antes do seguinte; era 1/dia na semana antes do 2º).
  Ensaio: os canais agora pedem as vagas de HOJE primeiro ("nada pronto pra 23/10 16:00" = produção é o gargalo).
  Backup parceiro_diario.py.bak_20261023_rampa_ordem.
- (14:30, cron) CONFERIDO: todos os consertos continuam nos arquivos (outras sessões mexeram em politica/anime_auto/
  trechos_noite). BURACO 11:00-14:00: IP barrado de novo + ESTOQUE 0/8 ("nada reposto (0/8; yt-dlp em pausa)") =
  "Nenhum candidato" em toda rodada — o DISCO_MIN 8,5 entrou 10:40 e o IP caiu antes da 1ª reposição. 14:01 voltou
  produzindo com a fonte UCSJ6 (d_UCSJ6_g, mediana 1634: peso novo da U1 agindo). IP livre às 14:25 -> rodei
  `estoque_fontes.py repor --novos 2` (fila do yt-dlp + espaçamento, sem rajada). Postagem: sem erro de tag; Curiosidades/
  ForjaReact/Dicas/Fio da Meada no limite diário (tentam a cada 3 h); 1 timeout de página em branco no indonésio 14:18.
- (15:25, cron) Estoque: 1 fonte guardada (jsKL-sF2dGo, 17 MB); a 2ª reposição (processo à parte) espera a vez — 7
  bloqueios do IP hoje = 15 min entre downloads. Produção: Short de fonte longa (161 s, 18 frases, voz clonada 38 min)
  em andamento desde 14:01. Línguas agendadas: thai e viet em 30/10 (24-29 cheios). "[xfade seg] falhou" (dado
  inválido num clipe) 3x em 4 dias: cai no concat simples e a legenda vai pela estimativa — raro, não mexi.
  AINDA SEM DADO: 4º do dia nos canais com rampa e "línguas: ..." com nicho novo (quase sem produção 11-15 h).
