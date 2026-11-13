# Melhorias possíveis no painel (http://localhost:8790)

Pedido do dono (21/10 02:13): "analise todas as possíveis melhorias que podemos fazer no painel pra eu acompanhar
melhor tudo lá e até acionar a IA pra consertar algo".

Análise feita direto (sem Workflow: no Opus a regra da memória proíbe subagentes). Cada frente é gravada aqui assim que
termina; se os tokens acabarem, retomar da primeira frente sem [feito].

## Frentes
- [x] A. O que o painel mostra hoje (inventário: rotas, abas, dados)
- [x] B. Saúde e alertas (vigias, avisos, tarefas agendadas, discos, PC2, logins, cotas)
- [x] C. Produção vídeo a vídeo (ciclo de vida, falhas, refazer, prévia)
- [x] D. Postagem, agenda e visualizações (canal sem post, views hoje/ontem, TikTok/Insta, comentários)
- [x] E. Botões de ação (o que hoje só se faz pelo chat/Telegram/script)
- [x] F. Acionar a IA pelo painel (perguntar e consertar, histórico, desfazer)
- [x] G. Visual, celular, velocidade e segurança
- [x] H. Projetos e sistemas que não aparecem no painel
- [x] Lista final priorizada (ondas) — no fim do arquivo; ESPERANDO o dono escolher por onde começar

## Achados

### A. O que o painel mostra hoje [feito]
- Servidor `painel_controlador.py` (712 linhas, só 127.0.0.1:8790). GET: geral, medir, canais, postagens, ranking,
  canais_views, placar, hipercool, producao; /rede (iframe do painel da rede). POST (X-Painel): controle, abrir.
- Abas (`painel_web/index.html`, 838 linhas): Visão geral, Produção ao vivo, Liga/desliga, 7 projetos (Cortes,
  Hipercool, MS Energy, Veo, ManhwaReact, Histórias, Postador), Postagens, Canais hoje, Views por vídeo, Views e
  inscritos, Placar 48 h, Rede, Como funciona. Atualiza sozinho a cada 30 s só a Geral, a Produção e a aba do projeto aberta.
- Bem servido: Cortes (Short a Short com etapa/%/LUFS/voz/canal/abrir), filas por canal, MS Energy, Hipercool
  (capítulos x línguas), postagens com título/link/views, views/inscritos por canal com série, liga/desliga real.
- Fraco ou ausente: ManhwaReact/Histórias/Postador só mostram processo + cauda de log; nenhuma tela de erros/avisos,
  nada da voz clonada, do aprendizado, dos comentários, das contas (TikTok/Insta/logins), das tarefas agendadas, do
  Drive/disco ao longo do tempo, da IA (vigia) e nenhum jeito de pedir algo à IA.

### B. Saúde e alertas [feito]
Dados que já existem e o painel não mostra:
- `estado/avisos.jsonl` (356 avisos: em, origem, importante, situacao, texto) = histórico de TUDO que foi (ou foi
  segurado) pro Telegram. Origens: hipercool 130, aprendizado 60, postagens 55, monitor do anime 37, opus 16...
- `vigia_geral.checar()` já calcula a lista de problemas a cada 20 min (log travado, fila de render presa >3 h,
  nenhum Short em 5 h, postagem parada 75 min, controlador parado 30 min, código comum mexido, modelo morto no
  gateway, disco D:<8/C:<5 GB) mas só grava no log/Telegram; `estado/vigia_estado.json` tem subvigias e últimas
  checagens; `VIGIA_DIARIO.md` + `logs/vigia_agente_*.log` (114) = tudo o que a IA já fez.
- Tarefas agendadas (medido 21/10 02:20): 35 nossas, 24 ligadas, 5 com resultado anormal — ManhwaReact-Lote 0x1
  (falhou 02:00 hoje), TikTokRodadaExtra 0x6A, VozClonadaFila 0xFFFFFFFF, HipercoolPC2 e Parceiro-Postagem 0x800710E0
  (pedido recusado porque a anterior ainda roda). Nada disso aparece em lugar nenhum.
Propostas:
- B1 Aba **"O que está errado agora"** (primeira coisa da Visão geral): cartões vermelhos/amarelos vindos do
  `checar()` do vigia (rodar no painel a cada 2-5 min, sem o agente) + máquinas + tarefas com erro + canais sem post
  + bots sem "Iniciar". Cada cartão: desde quando, última vez que esteve ok, link pro log, botão "pedir pra IA" (F).
- B2 Aba **Avisos** = avisos.jsonl em tabela (filtra por origem/bot/importante/segurado, busca no texto, CSV),
  contador por origem/dia (ver o que mais incomoda e o que dá pra calar).
- B3 Aba **Tarefas agendadas**: nome, ligada, última, resultado traduzido (0x1 = falhou, 0x800710E0 = ainda rodando,
  0x41301 = rodando), próxima, duração; botão "rodar agora" e "ver log" (só das nossas; desabilitar/habilitar com
  confirmação, nunca as que o dono desligou de propósito).
- B4 **Saúde dos serviços**: OmniRoute/gateway (cota do Opus, Kiro), proxy Webshare, Groq, edge-tts, yt-dlp (vez e
  último bloqueio), worker 8772 do PC2, Chrome/CDP das portas do postador, rclone/Drive — cada um com "último ok" e
  "último erro".
- B5 **Linha do tempo de incidentes** (dia/semana): parada de produção, disco cheio, mudos, bloqueios — com duração
  ("produção parada 2 h 10 min") pra ver o que mais custa.
- B6 **Discos com histórico** (D:, C:, PC2 C:) e previsão "enche em X h" no ritmo atual; o guardião do disco
  (`_guardiao_disco`) registrar no painel quando agiu.
- B7 **"Por que está parado?"**: todo PC/projeto parado mostra o motivo em português, vindo do log do controlador
  (hoje o PC2 aparece só "ocioso / nada rodando" enquanto o log diz: worker 8772 fora, parceiro pausado após 3
  falhas, e o hipercool_pc2 disparado 16x em vão).
- B8 **Disparo que morre na hora**: trabalho do controlador que termina em menos de 2 min várias vezes seguidas =
  cartão vermelho (21/10: `fila.py pc2` saiu 16 vezes com "outro pc2 rodando" porque o `pc2-trazer` travou 1 h no
  tar do cap09/th; PC2 parado ~2 h e o painel mostrava "Disparos hoje 18" como se fosse bom).

Provas reais achadas durante esta análise (21/10 02:20-02:35), nenhuma aparecia no painel:
1. ManhwaReact-Lote falhou às 02:00: Pillow do Python central sem 11 arquivos (sequela do venv que foi pro Drive
   em 20/10). CONSERTADO: repostos 13 arquivos com sha256 conferido no RECORD (pillow + bcrypt), lote rodado de novo ok.
2. PC2 parado: `pc2-trazer` do hipercool trava 1 h por vez (registrado em hipercool docs/correcoes_pendentes.md).
3. /api/canais leva 58 s e /api/producao 12 s (o painel parece travado).

### C. Produção vídeo a vídeo [feito]
Hoje: só o Cortes do PC1 tem tabela vídeo a vídeo, e só do dia (log `_parceiro_<dia>.log`); PC2 aparece como uma
linha "Short no PC2 pra X"; Hipercool/Veo/MS Energy/ManhwaReact = processo + cauda de log.
- C1 **Ficha do vídeo** (clicar em qualquer linha): vídeo do parceiro (link, views), roteiro, narrador/voz e
  Config 1/2 (o .txt da cópia da voz clonada), trecho original usado, LUFS, duração, capa, veredito da análise do
  vídeo pronto (`postar.json` revisao), censura, canal, título/descrição/tags, agendado para, link no ar, views depois.
- C2 **Player e prévia no próprio painel** (rota /video com suporte a "range", miniatura gerada por ffmpeg 1x):
  ver o vídeo pelo celular, não só "abrir no PC" (`api_abrir` usa os.startfile).
- C3 **Histórico de produção por dia** (escolher o dia, não só hoje): feitos x falhas por projeto, minutos por
  vídeo, top causas de falha agrupadas ("pipeline falhou: X" 5x).
- C4 **PC2 com o mesmo detalhe do PC1**: etapa/% dos Shorts e do anime longo lendo o log que o `pc2_recapd` traz.
- C5 **Fila de render** completa (quem está rodando/esperando, desde quando) — hoje só o número na Visão geral.
- C6 **Previsão do dia**: "até 23h devem sair ~N vídeos" com as durações que o controlador já mede (`duracoes`).
- C7 **Voz clonada**: fila/rodízio (`videos_voz_clonada\_rodizio.json`), próximo narrador, Config 1 x 2, cópias
  por narrador com a descrição, falhas (tarefa VozClonadaFila está com resultado 0xFFFFFFFF).
- C8 **Vídeos segurados** (mudo, reprovado por nudez, sem voz) numa lista própria com o motivo e o que fazer.

### D. Postagem, agenda e visualizações [feito]
Hoje: Postagens (catálogo, 327 KB por chamada), Canais hoje (58 s), Views por vídeo, Views e inscritos, Placar 48 h.
- D1 **Agenda em grade** canal x hora (próximas 48 h): o que está agendado, buracos (canal sem nada amanhã),
  regra BR 3/dia, pico de cada país.
- D2 **Canal sem post hoje** em destaque no topo, com contagem até meia-noite e o que o controlador vai fazer.
- D3 **Views por vídeo nas primeiras 24/48 h x média do canal**: marca acerto/fracasso cedo; "mil views" já existe
  como aviso (origem "mil views") e iria pra cá.
- D4 **Contas TikTok/Instagram** (`config\reuso_plataformas.json`, logs tiktok_*/instagram_*, cofre): logada,
  banida, sem cookie, postados hoje x limite, último erro; botão "logar de novo" (cofre.py logar).
- D5 **Comentários**: últimos por canal, respondidos pelo auto_responder, sem resposta (`config\telegram_estado.json`,
  extras_ledger.log, sem_token.log).
- D6 **Saúde dos canais YouTube**: suspensos/desativados/token morto (`config\canais_status.json`), pausados com
  advertência (fr 2 strikes, en bloqueado — só mostrar, nunca botão de despausar), limite diário de envio atingido
  (ForjaReact 20/10).
- D7 **O que dá mais view** cruzando ledger + métricas + .txt da voz: por gênero/nicho, narrador, Config 1 x 2,
  tipo de título, horário, duração — é o que o dono precisa pra escolher entre Config 1 e 2.
- D8 **Parceiros**: por canal parceiro, Shorts feitos/postados e views que renderam (qual fonte vale mais).
- D9 **Views exatas dos canais sem dado** pelas chaves OAuth em `D:\downloads\toeks youtube` (5 contas) — depende
  do dono autorizar 1x no navegador.

### E. Botões de ação [feito]
Hoje: liga/desliga por projeto/etapa e "abrir vídeo". Tudo o mais é pelo chat, Telegram ou script. Botões que
fazem falta (todos com confirmação, motivo e registro em `estado/painel_acoes.jsonl`, só comandos de lista branca):
- E1 Rodar agora: rodada do controlador, uma tarefa agendada (Start-ScheduledTask), postagem do parceiro
  (`parceiro_diario.py postar`, que sempre agenda), "produzir pra este canal".
- E2 Por vídeo: refazer (libera o ID como no `_feitos_short*.txt`), reprovar/segurar, liberar, deixar privado no
  YouTube (`youtube_studio_extras.visibilidade`, já existe), abrir pasta/log.
- E3 Aprendizado: aprovar/reprovar achado com o trecho tocando na tela (hoje só no Telegram).
- E4 Vozes: aprovar/reprovar narrador, escolher Config 1/2/mistura.
- E5 Canais: mudar alvo da fila e prioridade de gênero (parceiro.json), pausar canal (despausar só sem advertência).
- E6 Manutenção: atualizar yt-dlp (`atualizar_ytdlp.py`), religar worker 8772 do PC2 (o controlador já sabe),
  limpeza segura do guardião (só a lista branca com rclone check), testar bots do Telegram (getChat) com link
  t.me/<bot>?start pra apertar Iniciar.
- E7 Nunca terá botão: publicar direto (sempre agendado), despausar canal com advertência, matar pythonw, apagar
  vídeo/pasta fora da lista branca.

### F. Acionar a IA pelo painel [feito]
O que já existe e dá pra reaproveitar (nada precisa ser inventado):
- `video-fila\vigia_geral.chamar_agente(motivo)`: Claude Code headless (`hipercool-videos\tools\claude\claude.exe`
  2.1.301) pelo proxy (Kiro Sonnet 4.5, `secrets\claude_proxy.json`), trava única, 40 min, regras duras no prompt,
  backup em `vigia_backups\<hora>\`, diário `VIGIA_DIARIO.md`, resposta `STATUS: OK|CONSERTEI|REVISAR`. Escopo:
  Cortes/recapd e video-fila (proíbe hipercool, postador e manhwa-react\mr).
- `hipercool-videos\bin\vigia_agente.chamar_agente(motivo, max_turns, modo)`: modo **consulta** (10 voltas, só
  responde, linha `RESPOSTA:`) e modo **vigia** (30 voltas, conserta). É o que o Telegram usa (`vigia_telegram.py`,
  perguntas em `workspace\vigia_perguntas*.jsonl`, ferramentas `consultar_producao.py views|ranking|comentarios|...`).
- Limites de hoje: a saída só aparece no fim (`subprocess.run(capture_output)`), uma IA por vez (sem fila: "já
  está rodando, mande de novo"), postador/manhwa-react sem agente com permissão.
Propostas:
- F1 **Caixa "Perguntar à IA"** em todas as telas (igual ao Telegram): modo consulta com `--disallowedTools
  Edit,Write,NotebookEdit` (só lê de verdade, não só no prompt), já mandando o contexto da tela aberta (ex.: a linha
  do Short que falhou). Histórico junto com o do Telegram. `--resume` pra continuar a conversa ("e agora?").
- F2 **Botão "Pedir pra IA consertar"** em todo cartão vermelho, linha com falha, tarefa com erro e log: monta o
  motivo sozinho (erro + trecho do log + arquivo + regra do dono) e chama o agente do projeto certo (Cortes ->
  vigia_geral; hipercool -> vigia_agente modo vigia; postador/manhwa-react -> precisa de um escopo novo aprovado pelo dono).
- F3 **Acompanhar ao vivo**: rodar com `--output-format stream-json --verbose --include-partial-messages` gravando
  num .jsonl; o painel mostra cada passo ("lendo anime_tts.py", "rodando teste", "editando linha 37"), tempo
  correndo e botão **Parar** (encerra só aquele claude.exe).
- F4 **Fila da IA**: pedido com a IA ocupada entra na fila (não se perde); o painel mostra "IA ocupada com <motivo>
  desde hh:mm" e a posição.
- F5 **Histórico da IA** (VIGIA_DIARIO.md dos dois vigias + logs vigia_agente_*): quando, motivo, status,
  arquivos mexidos, backup; botões **"Ver o que mudou"** (diff backup x atual) e **"Desfazer"** (volta o backup,
  com confirmação). Hoje desfazer = copiar à mão o comando escrito no diário.
- F6 **Modo "propor antes de aplicar"** (padrão quando o pedido vem do celular): 1ª rodada só investiga e devolve
  o plano + diff proposto; o dono clica **Aplicar** e a 2ª rodada (`--resume`) aplica.
- F7 **Diagnóstico automático**: cada cartão vermelho novo já ganha um diagnóstico curto em modo consulta (barato), o
  dono vê "provável causa" antes de clicar; conserto só com clique (ou regra explícita do dono por tipo de problema).
- F8 **Custo e modelo à vista**: qual modelo (Kiro Sonnet pelo proxy; Opus fica fora por causa das cotas/429), cota
  do gateway (o monitor do Opus já lê no OmniRoute), voltas usadas, teto de chamadas por dia pelo painel.
- F9 **Regras sempre junto**: o prompt do painel inclui as regras do dono (PC2/pythonw, sempre agendar, nunca
  despausar canal com advertência, nada de apagar no D: sem rclone check, Google só navegador, Groq só pelo proxy,
  yt-dlp sem rajada, vozes proibidas, censura só nas partes) + os aprovados do aprendizado.
- F10 **Resultado avisado**: no painel (notificação do navegador) e no bot do vigia, com link pra tela do histórico.
- F11 **Segurança** (obrigatório antes de abrir o painel fora do PC): o agente roda com
  `--dangerously-skip-permissions`, então quem abre o painel manda na máquina. Login com senha/token, registro de
  quem pediu, limite de pedidos e só ações de lista branca.

### G. Visual, celular, velocidade e segurança [feito]
Prints de 21/10 02:24 (`logs\prints_painel\analise_desk_geral.png` / `analise_cel_geral.png`): visual Hermes bom,
celular empilha certo, sem erro de JS. Problemas:
- G1 **Velocidade**: /api/canais 58 s, /api/producao 12 s, /api/postagens 3,5 s e 327 KB, abrir a Geral 14 s.
  Calcular tudo em segundo plano (thread a cada 30-60 s ou o próprio controlador gravando) e a tela só ler o pronto
  (resposta < 0,3 s); postagens paginadas/filtradas no servidor; "atualizado há X s" em cada bloco.
- G2 **Abrir no celular fora de casa**: hoje só 127.0.0.1. Servir no IP da Tailscale (100.x) com login (G/F11) e
  "instalar como app" (PWA) com notificação — o painel pode substituir parte do Telegram.
- G3 **Topo de dono em 5 segundos**: uma frase "Tudo ok / 2 problemas · 23 vídeos feitos · 31 postados · 12,4 mil
  views hoje" e os problemas primeiro; hoje o topo são 9 números sem dizer se está bom ou ruim.
- G4 **Busca única** (título, canal, ID do vídeo, arquivo) que abre a ficha (C1).
- G5 **Gráficos de tendência 7/30/90 dias**: produção por projeto, postagens por rede, views, falhas, disco.
- G6 **Ao vivo sem esperar 30 s** (SSE) na Produção e na IA (F3).
- G7 **Erro de API vira cartão** com "tentar de novo" e "pedir pra IA" (hoje aparece o texto do erro cru).
- G8 Pequenos: contador nos itens do menu (já existe `contador()`) usado pra problemas/avisos novos; modo
  compacto pra tela pequena; som opcional quando aparece vermelho.

### H. O que não aparece no painel [feito]
- H1 **Voz clonada**: rodízio, narrador da vez, Config 1/2, cópias por narrador, treino, falhas (C7).
- H2 **Aprendizado**: 72 achados (59 pendentes, 13 descartados) em `aprendizado\acervo.jsonl` com trecho
  (mp4/mp3) — aba com tocar trecho + aprovar/reprovar + filtro por tipo/modelo/vídeo (E3).
- H3 **Comentários** (D5), **contas e logins** TikTok/Insta/YouTube por porta/cofre (D4).
- H4 **Bots do Telegram**: quais já têm "Iniciar", quantos avisos cada um mandou hoje, o que foi segurado pelo
  portão (`avisos.jsonl`).
- H5 **Backup no Drive e disco**: `manhwa-react\logs\backup_drive.jsonl` (o que foi pro Drive, quanto liberou),
  rclone ok/erro, guardião do disco.
- H6 **Tarefas agendadas** (B3) e **sessões/vigias** (vigia_geral, VozClonadaVigia, subvigias: anime_monitor,
  vigia_melhorias, extras_ledger, sem_token, aprendizado — última rodada e resultado de cada).
- H7 **Trader**: só um cartão de saúde (vigia de segurança ligado? último alerta) com link pro painel dele (8787).
- H8 **Gateway/VPS 157** (OmniRoute: cota, 503 de heap; FluxIA/n8n): cartão de saúde com link.
- H9 **Desktop (3º PC, Tailscale)**: ocioso/ocupado e o que roda lá, já que a fila comum mede os 3.
- H10 **Melhorias entre projetos** (`hipercool-videos\docs\MELHORIAS_PARA_TODOS_OS_PROJETOS.md`) e este documento
  na aba "Como funciona".

## Lista final priorizada (21/10 02:40)

### Onda 1 — o que mais ajuda já (teria pego os 3 problemas desta madrugada)
1. **Painel rápido** (G1): tudo pré-calculado em segundo plano; nenhuma tela esperando 58 s.
2. **"O que está errado agora"** no topo (B1 + B7 + B8 + G3): problemas primeiro, com "por que está parado" e
   "disparo que morre na hora".
3. **Tarefas agendadas** com resultado em português e "rodar agora" (B3 + E1).
4. **Perguntar à IA** no painel, só leitura de verdade, com o passo a passo ao vivo e fila (F1 + F3 + F4).
5. **"Pedir pra IA consertar"** em cada problema, propondo antes de aplicar, com histórico, "ver o que mudou" e
   "desfazer" (F2 + F6 + F5).
6. **Bots sem "Iniciar"** com o link de cada um (H4, pequeno).

### Onda 2 — acompanhar vídeo a vídeo e decidir com dado
7. Ficha do vídeo + player no painel (C1 + C2).
8. Aba Avisos (B2) e aba Aprendizado com trecho tocando e aprovar/reprovar (H2 + E3).
9. Agenda em grade + canal sem post em destaque (D1 + D2).
10. O que dá mais view: gênero, narrador, Config 1 x 2, título, horário (D7).
11. Contas TikTok/Insta e saúde dos canais YouTube (D4 + D6).
12. Voz clonada (C7/H1) e vídeos segurados (C8).
13. Botões por vídeo: refazer, segurar, liberar, privado (E2).

### Onda 3 — maior ou depende do dono
14. Abrir no celular fora de casa (Tailscale + login + app/PWA + notificação) — só depois do login (F11/G2).
15. Tendências 7/30/90 dias, busca única, histórico de produção, linha do tempo de incidentes, disco com previsão
    (G5, G4, C3, B5, B6).
16. Views exatas pelas chaves OAuth (D9) — precisa o dono autorizar 1x por conta.
17. Cartões de saúde: Drive, trader, VPS 157, desktop, serviços (H5, H7, H8, H9, B4).
18. Diagnóstico automático e custo/cota da IA à vista (F7 + F8).

### Decisões que são do dono
- Por qual onda começar (sugestão: Onda 1 inteira, na ordem).
- A IA do painel pode consertar também o postador e o manhwa-react? (hoje nenhum agente tem permissão lá)
- "Consertar" sempre propõe antes, ou coisa pequena pode aplicar direto?
- Abrir o painel no celular pela Tailscale (com senha)?

## Implementação (dono 21/10 02:45: "faça todas"; cron 05:41 continua, 07:01 analisa)
Padrões sem resposta do dono: IA propõe antes de aplicar (Aplicar = clique do dono); celular pela Tailscale só com
token de acesso. Marcar [x] cada item assim que testado no painel real.
- [x] 1 Painel rápido — cache em 2º plano (canais 58 s -> 0,004 s; produção 12 s -> 0,005 s) (cache em segundo plano)
- [x] 2 "O que está errado agora" (/api/problemas) no topo da Visão geral
- [x] 3 Tarefas agendadas (/api/tarefas + rodar agora)
- [x] 4 IA: perguntar (painel_ia.py, stream ao vivo, fila, parar)
- [x] 5 IA: consertar (propor -> aplicar com backup automático por hook, ver diff, desfazer) + histórico
- [x] 6 Bots sem Iniciar (/api/bots)
- [~] 7 Ficha do vídeo + player — player/abrir pasta/IA por Short feitos; FALTA ficha com roteiro/capa/análise (/video com range)
- [x] 8 Aba Avisos + aba Aprendizado (tocar trecho, aprovar/reprovar)
- [x] 9 Agenda em grade + canal sem post
- [~] 10 O que dá mais view — canal/projeto/hora/dia/fonte; FALTA narrador e Config 1x2 (o ledger não guarda a voz)
- [x] 11 Contas TikTok/Insta + saúde dos canais
- [~] 12 Voz clonada — rodízio/narradores/falhas; FALTA lista própria de vídeos segurados + vídeos segurados
- [~] 13 Botões por vídeo — ver/abrir pasta/pedir pra IA; FALTA segurar/liberar/refazer/privado (segurar/liberar, abrir pasta)
- [~] 14 Celular — tailscale serve (só tailnet) + chave de acesso, testado do PC2; FALTA o dono pôr a Tailscale no celular; PWA/notificação exigem HTTPS (desligado na tailnet) (Tailscale + token + PWA + notificação)
- [~] 15 Tendências — 30 dias de produção/postagens/views + disco gravando + busca única; FALTA histórico de produção por dia escolhido, busca, histórico de produção por dia, disco com histórico
- [x] 16 Cartões de saúde (Drive, trader, VPS 157, serviços)

### Produção garantida (dono 21/10 ~05:55: "garanta que a produção não pare")
- PC2 parado pelo `pc2-trazer` do hipercool: consertado `hipercool-videos\bin\pc2.py` `_baixar` (backup
  pc2.py.bak_20261021_trazer): lista curta na linha de comando (o stdin não chegava ao tar do PC2), keep-alive no ssh,
  estouro de tempo = falha sem derrubar. Testado: 2 arquivos em 0,4 s; cap09/th que travava 1 h veio (180 MB).
- Shorts de parceiro no PC2 pausados desde 18/10 (yt-dlp do PC2; já resolvido pelo _prebaixar_pc2): pausa tirada
  (estado/pc2_parceiro_falhou.json.bak_20261021). 3 falhas de novo = pausa volta sozinha.
- Worker do anime 8772: subia e morria com a sessão do ssh. Religado pelo WMI (Win32_Process.Create) e o
  `controlador._reiniciar_anime_daemon_pc2` passou a usar o mesmo jeito.
- Python central sem arquivos do Pillow/bcrypt (ManhwaReact-Lote 02:00): repostos (repor_venv.py).

### Como ficou (21/10 06:35) — testado no painel real e com prints (logs\prints_painel\v3_*)
- Arquivos: `painel_controlador.py` (rotas novas: problemas, tarefas, bots, avisos, aprendizado, ia, agenda,
  desempenho, contas, voz, tendencias, saude, /midia com range; POST tarefa_rodar, aprendizado_marcar, ia_pedir,
  ia_acao; cache em 2º plano; chave de acesso pra fora do PC), `painel_ia.py` (novo), `painel_web\index.html`.
- IA testada de ponta a ponta: pergunta (5 voltas, dados reais); conserto propor -> aplicar (backup por hook) ->
  diff -> desfazer (arquivo voltou). O agente roda com `--setting-sources project,local` (sem os hooks do Claude
  interativo do dono, que travavam o conserto pedindo planejador).
- Celular: `tailscale serve --http=8790` (só tailnet; desligar: `tailscale serve --http=8790 off`); fora do PC só
  com a chave (`estado\painel_chave.txt`; apagar troca a chave). Testado do PC2: sem chave 401, com chave 200.
- Registro de toda ação feita pelo painel: `estado\painel_acoes.jsonl`. Histórico do disco: `estado\painel_disco.jsonl`.
FALTA (próxima rodada): ficha completa do vídeo; segurar/liberar/refazer/privado por vídeo; narrador e Config 1x2 no
"o que dá mais view" (gravar a voz no ledger); vídeos segurados; histórico de produção por dia; comentários (D5);
diagnóstico automático (F7); cota do gateway (F8); linha do tempo de incidentes (B5); ao vivo por SSE (G6).

### Revisão da cron 07:01 (21/10)
- Velocidade medida no painel real: todas as rotas < 1 s (a maioria < 0,25 s); só `/api/medir` (botão "medir agora",
  ssh no PC2 na hora) leva ~55 s, e a tela já avisa.
- Defeito achado pelo teste e corrigido: voltar pra aba Postagens ou trocar o período apagava a tabela (o "carregando"
  trocava o conteúdo e a tabela achava que continuava montada; existia antes de hoje). Tabela agora se remonta.
- Iframe da aba Rede seguia carregando escondido: agora para ao sair da aba.
- Feito: lista de **segurados** do Cortes (reprovados + "verificar", com ver e IA), **Shorts de qualquer dia** (seletor de
  dia, `/api/cortes_dia`), **narrador e Config 1 x 2** no "o que dá mais view" (cruza o rodízio da voz -> postar.json ->
  métricas; 14 vídeos ligados, views entram quando o Studio ler).
- Produção: `maquinas.medir` tenta 2x antes de "não respondeu" (07:01 o PC1 a 100% deu ValueError e virou "ocupado").
- Teste completo no navegador (07:10-07:35): 27 abas x computador e celular sem erro de JavaScript; tabela (busca,
  CSV, período, voltar à aba), segurados, dia do Cortes, player (carregou 83 s de vídeo), confirmações, busca única,
  cartão -> IA; IA pela tela: pergunta, conserto (propor -> Aplicar -> o que mudou -> Desfazer) ok.
- Corrigido também: rolagem lateral no celular em 4 abas (coluna de grade esticava até a tabela: `min-width: 0`);
  "o que dá mais view" com projeto/hora/dia em "?" (agora vem do catálogo e da idade lida no Studio); a IA errava
  somas (disse 1 e depois 21 postagens amanhã, eram 28): `/api/agenda` devolve `totais` prontos e o prompt manda usar
  as rotas já contadas e dizer de onde veio cada número (refeito: respondeu 28, certo); a IA escrevia no diário pelo
  terminal (escapa do backup): o prompt do Aplicar proíbe mudar arquivo pelo terminal.
AINDA FALTA: ficha completa do vídeo (roteiro/capa/análise); segurar/liberar/refazer/privado por vídeo; comentários;
diagnóstico automático; cota do gateway; linha do tempo de incidentes; ao vivo por SSE; PWA/notificação (precisa HTTPS).


### Frente E — IA do painel: janela da conversa, documento, corrigir todos, base de consertos (22/10 08:20, Opus 5.5)
Pedido do dono (21/10): "1 clique abre JANELA com a conversa da resolução; tudo documentado do que fez (pra outra IA
continuar); botão corrigir todos; base de conhecimento dos problemas resolvidos (o vigia aprende; RAG leve)".
- Janela (dialog dlg-ia): no "O que está errado agora", "consertar com a IA" agora é 1 clique (cria a proposta e abre a
  janela com a conversa AO VIVO, atualiza a cada 3 s); problema que já tem pedido mostra "ver a conversa" com a
  situação. Na aba IA: ícone de janela em cada pedido e botão "abrir em janela"; no "O que os vigias já fizeram",
  clicar no título abre o bloco do diário + a resposta completa do agente (logs\vigia_agente_<hora>.log; o agente às
  vezes escreve a hora do diário em UTC: a janela pega o log mais próximo e avisa). Conversa = texto da IA, ferramenta
  usada (abre o comando/arquivo) e o que ela devolveu, lida do estado\painel_ia\<id>.jsonl (rota /api/ia_conversa).
  Os mesmos botões do painel lateral (Aplicar, Parar, Desfazer, ver proposta/aplicação) dentro da janela.
- Documento por pedido: D:\video-fila\consertos_ia\<id>.md (pedido, contexto, resposta, arquivos mudados com backup e
  diff, passos, sessão pra --resume) + consertos_ia\INDICE.md (1 linha por pedido). Gerado pelo código ao fim de cada
  pedido e ao desfazer (não depende da IA lembrar). Botão "documento (pra outra IA continuar)" na janela
  (/api/ia_doc). Os 11 pedidos antigos já foram documentados.
- Corrigir todos (botão no topo dos problemas, POST /api/ia_corrigir_todos, ensaio primeiro): 1 proposta por problema,
  um de cada vez; proposta que sai PROPOSTA vira aplicação SOZINHA (backup + Desfazer como sempre; aplicação passa na
  frente da fila). Pula problema com pedido na fila/rodando ou de menos de 6 h. Telegram: só o resultado da aplicação.
- Base de consertos: D:\video-fila\base_consertos.py (BM25 simples, sem acento, só biblioteca padrão). Lê na hora os
  consertos aplicados pelo painel (CONSERTEI não desfeito), as propostas "nada a fazer" e os blocos RESOLVIDO / NADA A
  FAZER dos 2 VIGIA_DIARIO.md (20 casos em 22/10). Os 3 mais parecidos (nota >= 5) entram no prompt da IA do painel
  (pergunta e conserto; a janela mostra "casos parecidos que a IA recebeu") e do vigia geral (vigia_geral.chamar_agente).
  Teste: "yt-dlp barrado 429" achou os 2 casos certos (nota 21 e 19); "controlador parado" não puxou nada (só 2-3).
  python base_consertos.py buscar "<texto>"  /  listar
- Testado: rotas com entrada inválida recusadas; corrigir todos sem o cabeçalho X-Painel = "não permitido"; ensaio
  não cria pedido; navegador de verdade (D:\tmp\teste_janela_ia.py) computador e celular: janela abre com a conversa,
  documento, fecha, janela do vigia, confirmação do corrigir todos (cancelada), 0 erro de JavaScript, 11 pedidos antes
  e depois. Prints D:\video-fila\logs\prints_painel\e22_*.png. Backups *.bak_20261022_janela (painel_ia.py,
  painel_controlador.py, painel_web\index.html) e vigia_geral.py.bak_20261022_base.
- Falta (próximo): o vigia do hipercool (D:\hipercool-videos) ainda não consulta a base (é do projeto dele; a função
  é base_consertos.bloco_prompt(motivo)); "corrigir todos" ainda não foi usado de verdade (é botão do dono).
