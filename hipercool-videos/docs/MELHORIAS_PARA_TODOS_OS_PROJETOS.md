# Melhorias do hipercool — LEITURA OBRIGATÓRIA em todo projeto de vídeo

Fonte ÚNICA: `D:\hipercool-videos\docs\MELHORIAS_PARA_TODOS_OS_PROJETOS.md`. Nos outros projetos o
`LEIA_MELHORIAS_HIPERCOOL.md` é só um ponteiro pra cá (desde 18/10), então não existe cópia velha. Atualizado em 18/10/2026.

**Regra do dono:** quem mexer no manhwa-react, no historias-em-frames, no recap de anime/parceiro (recapd-ambientes)
ou em qualquer outro projeto que produz/posta vídeo tem que aplicar estas melhorias lá também, quando fizer sentido. Se
a peça já existe aqui, copie/adapte o código daqui (caminhos abaixo) em vez de reinventar.

**Como manter (vale pra qualquer agente, de qualquer projeto):**
- Melhorou ou corrigiu algo que serve a outro projeto? Acrescente uma linha em **Novidades** (logo abaixo, a mais
  nova em cima): data, o quê, onde está o código, pra quem serve. Se mudou uma regra, corrija também a seção dela.
- Levou uma novidade pro seu projeto? Anote no controle do seu projeto (manhwa-react:
  `MELHORIAS_APLICADAS_E_PENDENTES.md`). Não se aplica? Anote o porquê lá também, pra ninguém tentar de novo.
- Não copie este texto pra outro lugar: aponte pra ele.
- **Código comum (desde 18/10):** módulo usado por mais de um projeto tem UMA versão em `D:\hipercool-materiais\comum`
  e cópia idêntica no bin/ de cada projeto; a cópia começa com a linha `# COMUM — fonte única`. Mexeu numa cópia
  dessas? Rode `python D:\hipercool-materiais\bin\recursos.py subir <x.py> --de <projeto>`: testa a versão nova em
  cada projeto e leva pra todos (o que não passar fica com a própria). `python D:\hipercool-materiais\bin\recursos.py`
  mostra o que é comum, que cópia foi mexida e os módulos SEPARADOS (mesmo nome, versões diferentes). Pra trazer um
  separado pro comum, junte o melhor das versões numa cópia (lendo as outras) e suba com `--juntei`.
- **Vigia (desde 18/10):** todo dia `D:\postador-de-videos\bin\vigia_melhorias.py` avisa o dono (Telegram + tela) do
  que cada projeto ainda não tratou daqui e de projeto que mudou código sem linha nova aqui. Tratou (aplicou ou não se
  aplica)? Marque, senão o aviso repete: `python D:\postador-de-videos\bin\vigia_melhorias.py --marcar <projeto> <id>
  feito|nao --motivo "..."` (ids e pendências: `--listar`). Projetos: hipercool, historias, manhwa-react, recapd. O
  projeto de origem sai da coluna "Código"; os destinos, da coluna "Serve pra" (cite o nome do projeto ou "todos").

---

## Novidades (a mais nova em cima)

| Data | O quê | Código / onde ver | Serve pra |
| 04/11 | Ducking pela VOZ: sinal de controle = voz achatada (passa-faixa + ganho + limitador) e 90 ms adiantado; trilha abaixa igual com voz alta ou baixa e já na 1ª sílaba. Medido: pausas e voz alta iguais, voz baixa +1,5 a 4,6 dB de ducking | recapd `bin/fx_music.py` add_background_music (ANIME_DUCK_VOZ=0 desliga; ANIME_DUCK_NIVEL) | hipercool fx_music.py e fx_acabamento.py:650 usam o sidechain antigo — copiar o bloco |
| 02/11 | **GERENTE DO KAGGLE: cota REAL por conta + GPU nunca parada** (dona: "controle no painel pra saber quantas contas ainda tem"). Achados medidos: (1) cota real por conta pela API `GetAcceleratorQuotaStatistics` (sem navegador) = **30 h/semana**; ARMADILHA: `to_dict()` do kagglesdk perde os dias do timedelta e mostra 30 h como 6 h — ler `total_seconds()` direto. 02/11 12h40: ~211 h livres até sexta 21h nas 10 contas utilizáveis; staging/bloqueio/revolutionemerson estavam "sem internet" mas tinham gasto as 30 h; 17 contas da hermes-prod nunca usaram GPU (sem telefone) = 510 h/semana paradas; (2) **o vídeo nunca passa pela Webshare** (o kernel baixa/sobe direto do Drive; Webshare só leva comandos da API do Kaggle em KB) e as 97 contas grátis estão com banda (teste real 200/402); (3) P100 aposentada: todo kernel é **T4 x2** e o pipeline só usava a GPU 0. Feito: `vps_central.py` mede a cota de hora em hora pela saída da conta, não lança conta com < 0,75 h nem GPU sem pedido nas filas (longo/Shorts/comentários), passa `TRAB_COTA_H` pro kernel; `kaggle_trabalhador.py` limita a sessão à cota, pula longo que não cabe (tenta o próximo), sai após 20 min sem trabalho e roda Shorts/comentários na **GPU 1** (`CUDA_VISIBLE_DEVICES=1`) enquanto o longo usa a 0; painel :8790 cartão KAGGLE + tabela por conta (ordena/filtra/CSV) + estado Webshare | `D:\hipercool-materiais\comum\kaggle_gerente\PROGRESSO.md`; `recapd colab\vps_central.py` (`vps_central.py cotas` lista e mede já), `webshare_saude.py` (tarefa WebshareSaude 6/6 h); backups `*.bkp_20261102_cotas` | todos que mandam trabalho pro Kaggle (longos, Cortes/parceiros, Comédia Noturna) |
| 02/11 | **META DE RESERVA: 1 SEMANA de vídeos em todo projeto (dona: "deixando vídeos pra uma semana guardados caso paremos de gerar por uma semana")**. Reserva do canal = agendados no YouTube + prontos não subidos, ÷ teto diário; meta = 7 dias. Produção feita em LOTES e o que não posta hoje fica no Drive (volta na hora de postar). Aplicado: **Cortes/parceiros** `config\parceiro.json` `fila_alvo` pt = 7 × por_dia (21; antes 6-9) — o controlador e o parceiro_diario produzem até lá; **MS Energy** `controlador.RESERVA_DIAS`: abaixo de 14 no estoque gera 4/dia (antes 2); **Comédia Noturna** `D:\videos-comentarios\bin\producao.py` RESERVA_DIAS/ESTOQUE_NUVEM (24) em lote no Kaggle + aviso no Telegram se < 1 dia. EXCEÇÕES: **Veo** (TikTok ~100/dia = 700 numa semana: limite é crédito do Flow) segue a rampa `tetos.json` (VEO_RESERVA_MIN, hoje 100 = 1 dia); **longos** (render só em GPU Kaggle, ~4-5 h cada) = fila contínua, reserva cresce com mais contas no pool; **hipercool e histórias** fora (praticamente parados). Medição 02/11: nenhum canal tinha 7 dias (melhor Game Noturno 6,7; rede manhwa-react 1,2-2,5; Tech Noturno 0,7) | `config\parceiro.json` (`_reserva_obs`), `D:\video-fila\controlador.py` (RESERVA_DIAS), `D:\videos-comentarios\bin\producao.py`; backup `parceiro.json.bak_20261102_reserva7` | todos os projetos de vídeo |
| 02/11 | **Recursos do GitHub aprovados pela dona (vídeos de teste em `D:\hipercool-materiais\testes_github_02nov`)**: módulo COMUM `realce_visual.py` — `parallax` (DepthFlow, câmera 3D sobre o mapa de profundidade, ~12 s/clip 4 s 720p na Intel), `transicao_inicio` (7 shaders gl-transitions do último quadro do clip anterior pro começo deste; duração e áudio intactos), `igualar_cor` (cor do começo do clip puxada pra do anterior, soltando em 1,5 s), `ampliar` (Real-CUGAN) e `morph` (RIFE); tudo com fallback (sem lib/GPU = caminho antigo) e `disponivel(nome)` antes de trocar efeito. Ferramentas em `D:\hipercool-materiais\tools`. LIGADO: hipercool (modo profundidade = DepthFlow, mais rápido que o antigo; 50% das transições sorteadas viram gl, nunca encostando em painel sensível), recapd e historias (`_render_xfade_segment`: 40% das fronteiras fala->fala viram gl com junta seca; starts/duração conferidos), produtos/MS Energy (`produto/video.py`: cor igualada entre cenas de vídeo seguidas), comentários (60% das trocas de comentário), Remotion do claude-code-video (`TextoQueCabe`, `BorraoMovimento` no `lib/efeitos.tsx` + EDITOR*.md). Legenda: a MIX continua (dona: "a nossa é melhor"). Kaggle/PC2/desktop sem as libs = sem mudança | `D:\hipercool-materiais\comum\realce_visual.py`; progresso e como desfazer em `D:\hipercool-materiais\testes_github_02nov\PROGRESSO_INTEGRACAO.md` | todos (manhwa-react: sem encaixe — cortes de um vídeo só) |
| 31/10 | **Capas: mascote/rótulos portados + teste A/B lido no Studio (com auditoria)**. hipercool `capa_ia` ganhou os layouts "etiqueta" e "rotulos" no rodízio e a mascote colada (rótulos sem rosto achado caem pra frase grande); manhwa-react `mr\capa` ganhou mascote e B = etiqueta, C = rótulos, com a coluna da mascote reservada pra não cobrir o título. Placar: o medidor de 48 h pontua SÓ a pose da capa A (a que subiu); B/C aprendem pelo vencedor do Studio (`extras_ledger.checar_ab` → `youtube_studio_extras --checar-ab` → `capa_ia_anime.registrar_vencedora_ab`, placar próprio `capas_ab`). Imagem do Flow com proporção diferente da pedida é descartada (veio foto de pessoa real numa capa B). NÃO marcar ae5a41 como feito sem conferir as capas reais do projeto | `D:\hipercool-materiais\tarefas complexas para fable 5.1\ENGENHARIA_REVERSA (parceiros - o que da views)\ER_08_AUDITORIA_ACOES_PRODUCAO.md` (seção 2b: o que estava errado e o que foi corrigido) | hipercool, manhwa-react, historias, recapd |
| 30/10 | **Shorts: vídeo quebrado não sai mais + duração**. Legenda que falha na queima = espera RAM, tenta 1x e o Short não sai (antes publicava sem texto); frase sem áudio = Short não sai (saiu um de 4 s com 1 de 10 frases); cortes do fim sem repetir o plano (passada de trás pra frente, adianta até 8 s); delogo com teto de 12% da altura (maior vira "vidro derretido"); filtro de instrução da IA narrada ("envie a transcrição…"); saudação de enchimento na 1ª fala sai; mascote/elementos dentro da área segura do Shorts (0,06–0,84 da altura, até 0,88 da largura); `source.f396.mp4` parcial do yt-dlp nunca vira fonte; Whisper acha a pasta do modelo sem depender do cwd. Dado de views: < 30 s rendem muito mais que 60 s+ e fonte < 100 mil views rende 1/3; 15–21 h pior em 9 de 9 canais | recapd `docs\MELHORIAS_SHORTS_2026-10-30.md` (anime-pipeline, anime_segments `_inicios`, anime_auto, anime_script, parceiro_marca `DELOGO_MAX_H`, cortes_mascote, _whisper_sub, parceiro_diario `_ordem_horarios`) | hipercool, manhwa-react, historias (qualquer Short vertical com legenda queimada, delogo ou Whisper) |
| 30/10 | **Capas do recap: 3 pro teste A/B, mascote e rótulos com seta (dona)**. Longo de parceiro sobe com A = capa dele melhorada (mesmo protagonista + mulheres), B = a MAIS SENSUAL (roupa reveladora que cobre tudo; palavra única estilo AmericanNickas com meia-lua até o rosto dela), C = o mesmo protagonista numa pose do catálogo em rodízio (rótulos estilo Porão/Zeni/Trigger: papel dele "PROTA/RANK S…" + fala dela, cada um com seta pro rosto, rostos achados pela mesma visão que aprova a capa). Mascote colada como FIGURINHA (PNG, canto de baixo) — nunca desenhada pela IA: ela é chibi e a checagem de menor reprovaria. Visão ganhou "exposto" (nudez reprova). `extras_ledger` monta o teste A/B do Studio quando o vídeo abre. Referências (8 canais da dona, folhas por canal) em `D:\video-fila\engenharia_reversa\CAPAS_REFERENCIA.md` | recapd `bin\capa_ia_anime.py` (`capas_ab`, `_colar_mascote`, `_desenhar_etiqueta`, `_rotulos`, `_seta`); `bin\anime_publish.py` (`thumbs_ab`); postador `bin\extras_ledger.py` (`--ab`) | hipercool (`capa_ia` já tem A/B; falta mascote/rótulos), manhwa-react, historias |
| 28/10 | **Do Hypit, no recap (Cortes):** (1) LEGENDA POR SENTIDO — cartão nunca separa artigo/negação/preposição + seguinte, nome de 2 palavras, número+unidade; impacto sozinho; alvo 2, máx. 3; tempo real por palavra mantido (`SUB_AGRUPAR=fixo` volta). (2) CORTE NA TROCA DE CENA — 1 leitura ffmpeg 12 qps 32x32 dá trocas (dif./255 >= 0,1) e brilho; início encosta na troca ±1,5 s sem repetir take; (3) trecho escuro desvia até 4 s; (4) nome do personagem com cor fixa no Short solo | recapd `bin\fx_subtitles.py` `cartoes_por_sentido`; `bin\anime_segments.py` `_analise_fonte`/`_encostar_na_troca`/`_fugir_do_escuro`; `bin\anime_formatos.py` `_cores_dos_nomes` | todo projeto com legenda palavra a palavra e corte de vídeo-fonte (hipercool, manhwa-react, longo) |
| 28/10 | **Argon (modelo que "pensa") + pedido curto = lixo na tela**: gancho com max_tokens=40 voltou "[EMPTY RESPONSE]" ou o raciocínio em inglês ("LANGUAGE:", "WINDOW") e foi queimado em 13 de 49 Shorts. Pedido de texto curto pro vídeo: max_tokens >= 600, validar a resposta (sem `: [ ] ( )`, 1 palavra latina = lixo, inglês em saída pt = lixo) e tentar 2x; resposta-aviso ("[EMPTY RESPONSE]", null, undefined) = falha | recapd `bin\anime_gancho.py` `_frase_valida`; `bin\claude_client.py` `_placeholder` | todo projeto que mandou texto de vídeo pro Argon |
| 28/10 | **Hypit, GSAP, Three.js, PixiJS (reanálise) + voz narrador_chris**: Hypit (repo `D:\caches\hypit`): método de engenharia reversa de vídeos virais (playbook reference-video.md) e caption-fine word-level → adotar no claude-code-video; testar como motor de ads de produto (MS Energy). GSAP: só para landings-produtos (ScrollTrigger via CDN); NÃO no Remotion (modelo de tempo incompatível). Three.js: JÁ instalado no Remotion, não usado — criar componentes 3D (título, partículas, produto 360°). PixiJS: não instalar agora, efeitos.tsx cobre o necessário. **Voz narrador_chris** (Todo Mundo Odeia o Chris) instalada em `models\rvc\vozes\narrador_chris\` (pth+index do HuggingFace linnhoAI123/Chrisnarrador) | `D:\hipercool-materiais\novas_tecnologias_analise.md` (reanálise completa com tabela de ações) | claude-code-video (método+caption), postador\produto (Hypit ads), landings-produtos (GSAP), todos (voz narrador_chris) |
| 27/10 | **Métricas do YouTube SEM navegador (HTTP puro)**: público (inscritos, views totais, views por vídeo/Short) via `youtubei/v1/browse` sem login; Studio (views/horas/inscritos/impressões/CTR/duração média por período, top vídeos com CTR, uploads com agendado_para, engaged views, reivindicação, restrição, monetização) via `yta_web/get_cards` e `creator/list_creator_videos` com cookies `.youtube.com` + SAPISIDHASH. 28 canais em ~75 s, sem Chrome; cookies pegos 1× pelo cofre e se refazem sozinhos se o login cair. Pode trocar os tokens OAuth (vencem ~29/10) e o Studio aberto no navegador de quem só LÊ dados. Ainda não ligado em painel/vigia | `D:\gemini-argo\youtube_http.py` (`studio --todos 28`, `sync <slug>`); receita em `D:\gemini-argo\docs\HTTP_PURO_GUIA.md` | painel :8790, vigias, status_videos, quem lê métrica do YouTube |
| 27/10 | **Argon com ferramentas (proxy)**: o `proxy_argon.mjs` na VPS (porta 20133) agora converte Tool Use do Claude Code em protocolo de texto para o Argon (`tool_call` / `[resultado da ferramenta]`), e a resposta de volta em `tool_use` Anthropic. Argon usa Read/Edit/Bash/Grep normalmente pelo Claude Code. Benchmark 7 tarefas/140 testes: Opus 5.5 140/140 1ª (140 s), Argon 116→140 (223 s), Kiro 129→140 (155 s). Teste real: achou e consertou 2 bugs em calc.py (53–74 s, 6 turnos). Descrição no seletor atualizada para "com ferramentas via proxy" | `D:\gemini-argo\proxy_argon.mjs` (funções `instrucaoFerramentas`, `extrairChamadas`, `forwardToArgonTools`); VPS `/opt/antigravity-cc-proxy/proxy.mjs` | qualquer modelo no seletor do Claude Code |
|---|---|---|---|
| 24/10 | **Veo no FUNIL + RAMPA** (dono: "o Veo tem que passar pela rampa de melhorias do YouTube, preferindo o mais viral"): o medidor de 48 h pontua o TEMA de cada Veo (nome do arquivo, pois o Veo não tem ficha postar.json) e a FOTO (na hora x antiga) contra a mediana do canal; o gerador sorteia o tema por horário × Thompson e a rede soma até +3 (Thompson) na nota do clipe do tema vencedor; o teto do Veo por canal segue o `politica.teto_canal` (rampa + max_dia do cadastro, como o hipercool: InventoReact segue 2/dia; ManhwaReact caiu de 2 para 1 porque o código antigo passava do max_dia 3 do cadastro). **Imagem do Flow com lista de máquinas** (`gera_imagem(..., maquinas=)`/`--maquinas`): quem tem cadeia de máquinas passa a lista e o Flow não abre Chrome no PC1 em pausa de carga nem no desktop em chamada. 1ª leitura: cassetadas_ia 10,8 mil views, dicas_financeiras 0/2. **Foto na hora**: o Flow cria a foto do dono no cenário do vídeo a partir das bases de fundo branco e um revisor de rosto (OpenCV YuNet+SFace, limiar 0,50) só deixa passar o rosto dele | postador `notificar_telegram._placar_veo` (placares `placar_veo_temas`/`placar_veo_foto`); manhwa-react `mr/rede.py` (`_bonus_viral_veo`, `veo_peso_viral`, `_teto_canal`); veo `beta/cron_gerar_video_llm.py` (`escolher_canal_inteligente`), `beta/foto_na_hora.py`, `docs/FOTO_NA_HORA.md` | qualquer projeto sem ficha: pontuar pelo nome do arquivo; o revisor de rosto serve pra qualquer imagem gerada do dono (capas etc.) |
| 22/10 | **MICROCORTES OBRIGATÓRIOS na narração dos SHORTS** (dona: "o que é muito usado nos Shorts é cortar as pausas entre as falas — micro cortes em vez de acelerar a fala"; e "bom pros CURTOS, não pros longos"): todo silêncio > 0,07 s (cauda do `pos_processar`, pausa do `humanizar` antes do impacto, vírgula, começo mudo do TTS) fica com 0,07 s, com o som original das pontas e crossfade de 6 ms; a FALA NÃO ACELERA; respiração, alongamento e eco ficam; o `<wav>.words.json` acompanha. O clip dura o que o áudio dura, então o vídeo encurta junto (6 falas reais: 39,0 s → 34,1 s). Ajuste: env `NARRACAO_GAP_MICROCORTE` (0,03–0,3). **Dona (22/10, depois): "os microcortes podem ser feitos em qualquer tipo de vídeo, mas tem que haver um teste antes"** — em cada projeto, re-render de um capítulo pronto com o material do CACHE (zero IA, única diferença = os cortes) pra ela ver; só depois liga na produção. Amostra de voz em ritmo de Short = velocidade normal + microcortes, nunca fala lenta/pausada | comum `narracao_curva.microcortes` (subido pelo `recursos.py`); recapd: no vertical, numa cópia da fala (`anime_segments._fala_do_short`) + `CLIP_GAP_S` do vertical 0,2 → 0 (`anime-pipeline.py`); hipercool: `elenco._microcortes` (edge, Gemini, `idiomas.py`, 16:9), ligado por padrão (`HIPER_MICROCORTES=0` desliga) | recapd Short LIGADO. hipercool LIGADO (teste do cap 14 aprovado: 214 s -> 194 s, "não senti diferença"). historias: falta o teste e o `split-shorts` dele corta no silêncio (precisa cortar na fronteira de cena antes). recapd deitado: falta o teste |
| 22/10 | **FUNIL INTELIGENTE (dono: "usar o que vai funcionando")**: o medidor de 48 h agora alimenta placares de PALAVRAS/TAGS do título, variante de capa (A/B/C), NARRADOR e VOZ-BASE (além de estilo/fonte/pose); o `seo_generator` do recapd injeta as palavras/tags vencedoras no prompt (`quentes()`), a variante da capa sai por Thompson, o bônus de narrador usa as medições públicas (amostra ~10×) e a produção do parceiro desempata a favor do CANAL que rende mais. **RAMPA de uploads por canal** (`postador bin/rampa_canais.py`): teto 4/dia sobe pra 5, 6… (máx 8) quando o canal enche o teto, não pega "limite diário" e rende; desce na hora se o YouTube recusar; 7 canais subiram pra 5/dia em 22/10 | postador `notificar_telegram.py`, `politica.py`, `rampa_canais.py`; recapd `seo_generator.py`, `anime_publish.py`, `anime_voz_clonada.py`, `parceiro_diario.py` | todos que postam/medem (hipercool e historias podem ler os mesmos placares via `placar_titulos.taxas`) |
| 22/10 | **"Limite diário de envios" do YouTube: espera 24 h SEM reenvio** (dona: "tem que esperar e não ficar tentando" — o ForjaReact fez 199 tentativas em 4 dias, cada uma reenviando o arquivo inteiro). `politica.marcar_limite_diario`/`em_limite_diario` + veto no `checar_upload` (status "limite"); upload ok zera; estado em `config\limite_diario.json`. O Telegram agora AVISA o canal preso (padrão novo no `ALERTAS_LOG` do `notificar_telegram.py`, lendo os logs do parceiro) | postador `bin/politica.py`, `bin/notificar_telegram.py` | todos que postam no YouTube |
| 22/10 | **Agendado futuro NÃO é "último upload"**: a fila do hipercool travou 6 canais por 4 dias porque o Short do parceiro agendado pra daqui a dias contava como último upload e o intervalo dava hora NEGATIVA. Quem calcula intervalo/parado pelo ledger deve filtrar `publish_at <= agora` (o teto do dia continua contando os agendados de hoje) | hipercool `bin/fila.py` `_pode_postar` | quem decide postagem pelo ledger |
| 22/10 | **Status único com erros/top-flop/máquinas + página HTML**: `status_videos.py` ganhou seções "o que deu errado (24 h)" (avisos importantes + tarefa com resultado ruim traduzido), top/flop por vídeo do placar e as 3 máquinas; `status_videos.py html` gera `painel_web\status.html` (botão `STATUS_PAINEL.bat`). Tarefa Disabled absorvida pelo controlador aparece como "absorvida" | `D:\video-fila\status_videos.py` | todos |
| 22/10 | **Voz pt do hipercool: humanizar comum LIGADO** (`voz_humana.humanizar_comum` em config/fila.json, ok da dona) + `_edge_para_wav` captura WordBoundary → `<wav>.words.json`; línguas (`idiomas.falar`) ganharam o tratamento do pt: limpeza de rubrica, pronúncia, curva do clímax e -20 LUFS. NÃO ligar `respiracao`/`pausa_variavel` junto (efeito dobrado). Lição: as Multilingual erram a LÍNGUA em certas frases ("maçaneta" virou inglês) — voz NATIVA (Francisca) não erra; pra obra nova, considerar nativa/clone | hipercool `bin/elenco.py`, `bin/idiomas.py` | quem narra com edge |
| 22/10 | **Capa A/B/C chegou no recapd** (`anime_publish._tratar_capa`, rodízio determinístico, variante em `postar.json.capa_variante`); análise de nudez do recapd alinhada à regra "só nudez segura" (`anime_revisao`/`anime_publish`: erro técnico AVISA e sobe); clone com guarda de RAM + 1 retry (`anime_tts`); estados atômicos (`parceiro_diario._json_atomico`, `anime_voz_clonada`) | recapd `producao/bin/*` | historias (capa A/B/C já tem), quem usa análise/clone |
| 22/10 | **Base de consertos (RAG leve, dono 21/10: "o vigia aprende")**: `base_consertos.bloco_prompt(texto)` devolve os 3 casos mais parecidos já vistos (consertos aplicados pela IA do painel + blocos RESOLVIDO / NADA A FAZER dos `VIGIA_DIARIO.md` do vigia geral e do hipercool), pronto pra colar no prompt de qualquer agente; vazio se nada parecido (nota < 5). A IA do painel e o vigia geral já usam. Junto: cada pedido da IA do painel vira documento `D:\video-fila\consertos_ia\<id>.md` (pra outra IA continuar), janela com a conversa e botão "corrigir todos". | `D:\video-fila\base_consertos.py` (`buscar`, `bloco_prompt`; `python base_consertos.py buscar "<texto>"`), `painel_ia.py`, `vigia_geral.py`; detalhes em `D:\video-fila\MELHORIAS_PAINEL.md` (Frente E) | vigia do hipercool (falta ligar: somar `bloco_prompt(motivo)` ao prompt dele), qualquer agente |
| 20/10 | Capa IA: Gemini do gateway DESLIGADO por hora (dono; 403/429 desde 19/10) e reserva nova grátis: Cloudflare klein-4b → Pollinations `flux.2-klein-4b` (mesmo modelo, sem o filtro do Cloudflare: faz as poses de RECUSA) → Pollinations `z-image-turbo`. Religar o Gemini = `GATEWAY = True` no comum. Log diz o provedor (`@cf/…` ou `pollinations/…`) | `imagem_reserva.py` (COMUM: `GATEWAY`, `_pollinations`) + `_gerar` de capa_ia / capa_ia_historias / capa_ia_anime; `secrets/pollinations.json` (central + PC2 do hipercool); comparativo em hipercool `workspace/capas_reserva_teste/alternativas_20out` | hipercool, historias, recapd |
| 20/10 | **Voz clonada 2.0 + narração mais humana (dono ouviu e aprovou o v2)**: com `VOZ_CLONADA_VERSAO=2` o clone usa o perfil medido do narrador real (`models\rvc\vozes\<voz>\perfil_v2.json`: ritmo, pausa, tom entre frases, faixa de entonação, volume, EQ) e o roteiro sai no jeito de falar dele (`linguagem_v2.json`). Sem perfil = v1. **Humanizar + variação** (vale pra qualquer narração, com ou sem clone; dono: "não pode ser igual do começo ao fim"): função comum `narracao_curva.humanizar(wav, texto, indice, impactos, total)` logo depois do `pos_processar`, 1 ffmpeg por frase (~0,5 s): pausa antes da revelação/impacto, respiração (com `VOZ_CLONADA`: respiração REAL do narrador recortada do material dele; sem: sintética, cada uma diferente), ênfase nas palavras fortes, ritmo dentro da frase (alonga fim de oração e palavra forte, acelera o resto, mesma duração), fundo da sala do narrador, de-esser no clone. Quanto de cada um: `narracao_curva.variacao()` — situação (abertura, subida, impacto, respiro, pergunta, grito, final) + trechos de 3–7 frases que ligam/desligam recursos e sorteiam valores + onda de energia; vizinha não repete respiração/pausa. **O `<wav>.words.json` (legenda) é corrigido junto** — antes a pausa deixava a legenda adiantada. Kokoro agora também grava words.json (`models\kokoro\kokoro-v1.0-dur.onnx`, `voz_clonada._base_tts(palavras=)`). Fim de frase do narrador no clone: `final_st` por base no perfil (patch Applio `APPLIO_F0_FINAL_ST`). Medir tom com o RMVPE do Applio, não pyin (piso 60 Hz lê lixo no fim grave). Base: Francisca+clone = pronúncia, Kokoro+clone = emoção, **Andrew+clone = gringo, não usar**. | recapd `bin/anime_tts.py` (`_perfil_v2`, `_frase_v2`, `preparar_clone`, `narrate`), `bin/anime_voz_clonada.py` (3 bases por narrador), comum `narracao_curva.py`; perfis por `D:\hipercool-materiais\bin\clone2.py` | todos que narram |
| 19/10 | **Portão único do Telegram** (dono: "manda muita mensagem, não leio todas"): todo aviso passa por `avisos.enviar(texto, origem, importante=)` — repetido (mesmo texto sem números) não sai por 12 h; importante (inscrito, comentário, vigia quebrou/consertou, erro, conta com problema) sai na hora; rotina (postagens, capítulo pronto, filas, 1.000 views, relatórios) vai num resumo às 9h/14h/21h. Registro em `video-fila\estado\avisos.jsonl` (`python avisos.py` = o que saiu/segurou nas 24 h). Já ligados: `_tg_safe.send` e `notificar.aviso` (comuns), `notificar_telegram` (rotina), `anime_health_monitor` (era 24/dia do mesmo alerta), `vigia_melhorias`, fila do hipercool. NÃO mande direto pra api.telegram.org. | `D:\video-fila\avisos.py` | todos |
| 19/10 | **Voz clonada dos parceiros PRONTA (dono ouviu e aprovou: "ótimas")**: porao, drezin, mike, mattz, ijax, mangaticos, jubertim; as outras 9 (momo, pie=@PieRecaps, guugou…) vão chegando sozinhas — pronta = pasta com `.pth` em `D:\hipercool-materiais\models\rvc\vozes`. Todas autorizadas pelo dono (narrar inteiro também). Uso: o projeto narra como hoje (edge Multilingual, ritmo de locutor) e passa o áudio pelo `converter` → mesma fala com a voz do parceiro, tom automático. **Só CPU no PC1** (sem GPU): ~5× a duração com o PC livre, ~19× com ele lotado (90 s levaram 29 min em 19/10) — começar por Shorts, aberturas e vídeos curtos; compilado de 1 h+ não. Uma voz fixa por canal/obra (regra do elenco, §4b). Amostra: `amostras_voz\2026-10-18_vozes_clonadas\porao_teste_converter_90s.wav`. Comando (Python do `venv_vozes` dos materiais centrais): `voz_clonada.py converter <voz> <narracao wav ou mp3> <saida.wav>`. | materiais centrais: `bin\voz_clonada.py` (`converter_audio`), caminhos completos na §4b | todos |
| 19/10 | **Silhueta branca fálica**: obra que "censura" o pênis pintando de branco/luz deixa o contorno legível — detector de nudez não vê, e fosco/mosaico por cima de branco grande mantém a forma. Gemini (prompt só dessa forma) acha a caixa, o branco é apagado por inpaint e a área leva mosaico, antes de qualquer outra censura. | hipercool `bin/censura_visual.py` (`PROMPT_SILHUETA`, `localizar_silhuetas`, `apagar_silhuetas`, `censurar_imagem`) | recapd/parceiro (manhwa +18), historias, qualquer censura de painel |
| 19/10 | Jeito de falar dos 15 narradores BR (repertório v2.1, agora com o Porão) no roteiro de outro projeto: presente, discurso indireto, apelido do nicho, lista de roteiro automático proibido, `nao_usar`, 1 tirada sorteada por trecho (anime/manhwa). Também 2 estilos de título novos no rodízio medido (`ate_y`, `segunda_pessoa`). | `config/repertorio_narrador.json`; recapd `bin/anime_script.py` `_jeito_do_nicho()` (já aplicado); `config/seo_palavras.json` estilos_titulo; análise em `D:\hipercool-materiais\referencias_narradores\ANALISE_LINGUAGEM.md` (leva 4) | historias-em-frames, manhwa-react (rede: comentário/descrição, roteiro do react) |
| 18/10 | **Unificação FEITA (11 de 12)** — o que todo projeto passa a usar: **cadastro único de canais** `postador\config\canais.json` (dono, alimentadores livre/sobra, teto; se refaz sozinho; decisões em `canais.py` DECISOES); postar com o **projeto de verdade** (`postar_youtube(projeto=, tipo=)`, NUNCA `reservado_para(canal)`); **ledger** com projeto/tipo/caminho; **agenda única** no `politica.horario_publicacao` (teto por dia de publicação somando todos + intervalo; público sempre agendado +11 min); **liga/desliga único** `D:\video-fila\controle.py` + **status único** `status_videos.py`; **secrets único** (pastas `secrets\` são junção pro do postador); **medidor único dos 3 PCs** `video-fila\maquinas.py` + vez por máquina (`fila_render.vez(maquina=)`, `marcar`); **placar comum** `postador\_analise\aprendizado_global.json` (por projeto/tipo, idioma); comum novo: `_tg_safe`, `groq_api`, `notificar`, `edge_tts_engine`. Detalhes, testes e o que ficou de fora: ver o doc. | `D:\hipercool-videos\docs\ANALISE_UNIFICACAO_PROJETOS.md` (seção Execução) | todos |
| 18/10 | **Código comum entre projetos**: 12 módulos que já eram iguais viraram comuns (sem_janela, landscape_filters, master_loudness, narracao_curva, panel_fx_auto, musicgen_local, content_analyzer, contextual_motion, effects_memory, panel_classifier, sfx_categorizer, styled_transitions). Mudou um deles em qualquer projeto: `recursos.py subir` leva pros outros. Ainda há ~60 módulos SEPARADOS (edge_tts_engine, gemini_llm, censura_visual, fx_*, split-shorts…): ao mexer num deles, vale juntar as versões e trazer pro comum. Ver "Como manter". | `D:\hipercool-materiais\bin\recursos.py`; fonte em `D:\hipercool-materiais\comum` | todos |
| 18/10 | **Tela final nos completos + rascunhos presos, pelo Studio (navegador).** O completo sobe numa playlist de nome FIXO e genérico (sem nome da obra; criada no 1º upload) e, depois de público, ganha a tela final "1 vídeo + esta playlist". Rascunhos presos (upload que travou no meio) só são LISTADOS no log, 1x por dia por canal; apagar continua manual (`--limpar-rascunhos --apagar-mesmo`). Ainda não saiu em vídeo real (vale a partir do próximo completo). | manhwa-react `mr/rede.py` `PLAYLIST_COMPLETOS`; `D:\postador-de-videos\bin\extras_rede.py` (`planejar`, fim do `main`) | recapd (`studio_extras_anime`) e historias (`studio_extras_historias`): playlist sem nome de obra |
| 18/10 | **Capa A/B/C sem gerar 3 imagens**: a mesma capa sai em 3 tratamentos — A controle, B gradiente na cor do gênero, C escurecida da esquerda pra direita; gênero deduzido do título/descrição por palavra-chave. As 3 vão pro teste A/B do Studio quando o vídeo abre. | manhwa-react `mr/capa.py` (`GENRE_COLORS`, `genero_de`, `_tratamento`, `caminhos_ab`); `mr/grande.py` grava `thumbs_ab` | recapd (anime tem 1 capa só); historias se quiser A/B sem gastar geração de imagem |
| 18/10 | **Foley por palavra-chave: falsos positivos** (conferido com narração real de 48 min): "bateu" sozinho é "bateu na porta", não soco; "espada" só em frase ("empunha/saca a espada"); "rajada" só "rajada de vento"; "tapa" só "dá/deu um tapa" (não "tapa os ouvidos"); "comemora" não é aplauso. | manhwa-react `mr/foley.py` `FOLEY_MAP` | hipercool e historias (`bin/fx_foley.py`) |
| 18/10 | **Compilado 16:9 de histórias** (Shorts do mesmo gênero viram um vídeo longo deitado, concat sem re-encode). Cada história é convertida pra 16:9 com fundo estilizado (`landscape_filters`) e cacheada; quando junta `compilado_min` do gênero, sai o compilado com capítulos na descrição e capa IA 16:9. Entrega em `grandes/<slug>/` com `.postar.json` pra rede postar como completo. | historias `bin/compilado_longo.py` (`converter_com_cache`, `talvez_compilar`); pipeline etapa 12 em `bin/story_pipeline.py` | hipercool já tem (`bin/hiper-longo.py`); recapd se tiver Shorts curtos do mesmo gênero |
| 18/10 | **Métricas de histórias (loop A/B de capas)**: lê views no Studio (navegador) dos vídeos postados pela rede, compara com a mediana do canal, e registra vitória/derrota da pose da capa via Thompson. Títulos NÃO são medidos (a rede reescreve todos por canal). Roda 1x/dia pelo `auto_producer.py`. | historias `bin/metricas_historias.py` (`coletar`, `decidir`); `bin/capa_ia_historias.py` `registrar_resultado` | hipercool já tem (`bin/metricas.py`); recapd se tiver rodízio de capas |
| 18/10 | **Fix studio_extras_historias**: parâmetro de teste A/B ia como `capas_teste_ab` mas `youtube_studio_extras.rodar()` espera `ab=`; chave do resultado ia como `teste_ab_capa` mas o retorno é `teste_ab`. Corrigido. | historias `bin/studio_extras_historias.py` linhas 178, 188, 194 | quem chamar `youtube_studio_extras.rodar` com teste A/B de capa |
| 18/10 | **Nenhum canal fica um dia sem postagem.** Impedimento (marca d'água, análise reprovando, capítulo sendo refeito, defeito pequeno) só AVISA; o vídeo sobe com o que tem. Canal brasileiro: 3/dia; canal sem post no dia agenda pra +11 min (nunca público direto). Ver §6 e §7. | hipercool `bin/postar_hipercool.py` (análise só avisa), `bin/fila.py` `postar_pt`; parceiro `recapd-ambientes\producao\bin\parceiro_diario.py` (urgente) | todos. **Conferir trava que ainda segura:** recapd `anime_revisao`/`anime_publish` gravam `pronto: false` quando a análise reprova |
| 18/10 | **O limite do postador (4 envios/canal/dia) é dividido entre os projetos** que postam no mesmo canal: conta pelo ledger, na hora do upload. Quem posta fora da fila de prioridade rouba vaga. Caso real: `shorts_a_cada_2h.py` subiu 1 Short antes da fila tentar o compilado, e o compilado ficou pro dia seguinte. Manhwa Noturno = hipercool + parceiro. | `D:\postador-de-videos\bin\politica.py` `cota_restante` | todos que postam em canal dividido |
| 18/10 | Ordem da postagem no hipercool: compilado 16:9 > completo (1/dia) > Shorts (**1 por rodada**, no pico). Corrigido: com `--max-novos 1` o resumo `faltam=N` era lido como "todos os Shorts postados" e o resto do capítulo nunca subia. | hipercool `bin/fila.py` `postagem`, `postar_pt` | quem tem fila própria com Shorts em partes |
| 18/10 | **ffmpeg**: congelar o último quadro com `-ss` a menos de ~0,5 s do fim do arquivo falha (exit `4294967274` = -22, sem quadro pra decodificar). Limite o `-ss` a `duração − 0,5`. | hipercool `bin/split-shorts.py` (`cta_seek`) | quem corta Shorts com cartão/CTA final congelado |
| 18/10 | **Windows**: `print` com emoji num processo sem UTF-8 (tarefa agendada, cp1252) dá `UnicodeEncodeError` no fim, o exit sai ≠ 0 e quem chamou acha que falhou, mesmo com o trabalho feito. Rode com `PYTHONUTF8=1` ou `sys.stdout.reconfigure(encoding="utf-8", errors="replace")`, ou tire o emoji do log. | hipercool `bin/split-shorts.py` | todos |
| 18/10 | **Narrador v2**: 34 moldes de piada em rodízio (não repete nos últimos 2 capítulos da obra), fórmulas de abertura e fechamento sorteadas, lista `nao_usar` completa, marcas de "roteiro automático" proibidas. Vem da análise de 15 canais narradores de referência. | hipercool `config/repertorio_narrador.json` + `bin/narration.py` (`_sortear_repertorio`, `_sortear_formula`, `_proibido_roteiro_automatico`); análise em `D:\hipercool-materiais\referencias_narradores\ANALISE_LINGUAGEM.md` | quem narra com LLM: recapd (anime/parceiro), historias |
| 18/10 | **CTA no fim como peça separada** (pedido de like/comentário depois do último quadro, não no meio da história). Texto pelo LLM, nunca sobre corpo/roupa/toque nem com duplo sentido (o canal já levou advertência). No vertical: clipe depois do último painel; no compilado: segmento no fim (`intros_voz.segmento`). Ainda não saiu num render real (sai a partir do cap 17). | hipercool `bin/narration.py` `gerar_cta_fim`; `bin/hiper-pipeline.py` (`HIPER_CTA_FIM`); `bin/hiper-longo.py` `_cta_compilado` | recapd/parceiro, historias |

---

## 1. Título, descrição e tags (SEO)

- **NUNCA o nome da obra original** no título, na descrição, em hashtag ou em tag. Dá margem a reivindicação de
  direitos autorais. Nome de personagem pode ir na descrição.
- O título é a soma de duas coisas:
  - **provocação**, sensual ou de curiosidade: "ELE VIU TUDO", "HERANÇA PROIBIDA", "ELA É SUA?!";
  - **o máximo que couber de palavras que o público busca** e que tenham a ver com a história: reencarnou,
    sistema, rei, apocalipse, talento, selado, habilidade, rank SSS, overpower, bilionário, fracassado/humilhado,
    garota, família, magia, gênio, harém, romance escolar, voltou no tempo…
- Estilo dos canais que mais crescem, tirado do autocompletar real do YouTube: frases longas como
  "ELE FOI HUMILHADO por ser POBRE mas … e agora TODAS querem ele" ou "ele despertou o sistema de …".
  - Até ~95 caracteres.
  - 3-5 palavras-chave em MAIÚSCULAS.
  - No máximo 1 emoji.
- Descrição em 3 parágrafos:
  1. gancho com palavras buscadas;
  2. o que acontece, sem contar o final, usando "manhwa recap", "resumo manhwa" e o gênero;
  3. pergunta + inscrição.
  - Termina com hashtags de gênero/busca (#manhwa #manhwarecap #resumomanhwa #romance…).
- Tags: 20-30 frases como o público digita ("manhwa romance completo", "ele foi humilhado manhwa").
- **Banco de palavras**: `D:\hipercool-videos\config\seo_palavras.json`.
  - Montado com o autocompletar da busca do YouTube em pt-BR, endpoint público `suggestqueries.google.com`
    (`client=youtube&ds=yt&hl=pt-BR`), sem chave de API.
  - Refazer a pesquisa de tempos em tempos e para cada gênero novo.
  - Os gêneros de cada obra ficam em `config/fila.json` (`obras[].generos`) e o nome proibido em
    `nomes_proibidos`.
- **Variar e medir**: o completo sai com 3 títulos (estilos `busca` / `provocacao` / `curiosidade`).
  - Um deles é escolhido por amostragem de Thompson (`workspace/titulos_estilos.json`).
  - O estilo usado fica gravado no estado da postagem (`estilo_titulo`) para comparar o CTR depois.
- Código: `bin/seo.py` (`REGRAS`, `_palavras`, `_sem_obra` — apaga o nome da obra se o LLM escorregar,
  `escolher_estilo`).

## 2. Capas (thumbnails)

Capa é o que mais pesa no clique: a pessoa não abre os vídeos um por um, escolhe pela capa e pelo título sugerido.

- **Estilo**: arte REDESENHADA, limpa e colorida (estilo O Porão da Cidadela / "Manhwa Recap"), perto do limite
  sem cruzar. Personagens parecidos com os da história (`config/capas.json`).
  - Referências do dono: `D:\hipercool-videos\config\capas_referencia\` (20 capas — não pedir de novo).
- **Catálogo de poses em rodízio**, todas com roupa — `bin/capa_ia.py` `POSES`:
  - perna em volta do PESCOÇO dele, em várias posições;
  - ela montada no peito ou nas costas dele;
  - no colo de frente, **só com 2+ mulheres**;
  - harém na cama / um em cima e as outras em volta / disputa — abraço **só em harém**;
  - close do rosto dela com a boca bem aberta e a língua pra fora.
  - Aprovadas na 1ª rodada: harém na cama e ela ajoelhada por cima dele no chão.
  - Já testadas, não repetir: ela sozinha em cima / no colo de frente.
- **Roupa**: SÓ lingerie, biquíni, camisola, babydoll ("roupa comum = muita roupa"). Obra de época = roupa de
  época chamativa.
- **Poses de fantasia** (obra de fantasia/ação): 1 das variantes do teste A/B vira batalha — golpe de espada,
  contra monstro, magia, duelo, despertar de poder, dupla lutando (`POSES_GENERO`).
  - É uma alternativa para atrair outro público, **sem largar as sensuais** (que são as que mais chamam).
  - Liga pelos gêneros da obra.
- **Texto**: 2 balões (fala dela + reação dele, ex. "VOCÊ SERÁ MEU MARIDO!" / "ELA É MALUCA!") ou frase grande
  + balão. Selo do capítulo.
- **LIMITE (inegociável)**:
  - nada de ato sexual na miniatura — nem implícito: rosto de orgasmo/olho revirado, baba, fluidos, camisinha,
    mão no seio, recorte de painel de cena de sexo;
  - nada de mamilo/genital, de mosaico/borrão na capa, de cara de menor ou uniforme escolar.
  - Miniatura aparece pra todo mundo e isso derruba/dá strike.
  - A checagem por visão do `capa_ia` reprova isso.
- **Teste A/B**: cada vídeo sai com 3 capas de poses diferentes (`<capa>.json` com a pose de cada uma).
  - O Studio testa ("Teste A/B" do menu da miniatura).
  - A pose vencedora ganha peso: Thompson em `workspace/capas_poses.json`, `registrar_teste`/`registrar_vencedora`.
- **Shorts também têm capa**: 9:16 (720x1280), mesmas poses/falas do capítulo, selo "CAP. N • i/total"
  (`capa_ia.capas_short`, `postar_hipercool.capas_short`).
- **Gerador**: gateway OmniRoute `antigravity/gemini-3.1-flash-image`.
  - O plano de texto (cenário/falas/título) NÃO pode levar a descrição das poses/lingerie: Gemini e Claude
    recusam. Pose e roupa vão só no prompt da imagem.

## 3. Acabamento no YouTube Studio depois do upload

Módulo do postador (compartilhado): `D:\postador-de-videos\bin\youtube_studio_extras.py`. Pelo navegador, sem API.
Usar em **todo canal que já está liberado**. Canal em verificação devolve "pendente" e a fila tenta de novo a cada 3 h.

| Recurso | Onde | Observação |
|---|---|---|
| Tela final "1 vídeo, 1 playlist" | vídeo normal (não Short) | vídeo = melhor para o espectador; playlist = a do vídeo (nome repetido: a com mais vídeos) |
| Comentário fixado | completo, longo e Shorts | pt: "Algumas cenas foram censuradas… comenta SEM CENSURA". **Fixar exige o canal verificado** |
| Teste A/B de capa | vídeo normal | exige o canal verificado ("A verificação por vídeo está em análise" = pendente) |
| Vídeo relacionado | Shorts | liga o Short ao vídeo completo; exige o canal verificado |
| Limpar rascunhos presos | Conteúdo | uploads que travaram viram rascunho; apaga com conferência do título |

- No hipercool: `postar_hipercool._extras_de` grava no estado o que fazer, e `rodar_extras` executa/repete.
  - A fila chama a cada rodada de postagem.
  - Manual: `python bin/postar_hipercool.py --extras`.
- Seletores e armadilhas estão no docstring do módulo:
  - aba nova antes de fechar as velhas;
  - comentário numa aba própria;
  - o emoji vira `<img>` no texto do comentário;
  - aviso "todos podem ver o que você escreveu" no 1º comentário;
  - "Fixar no topo".

## 4. Estrutura do vídeo (retenção)

- **Abertura**: ~3 s de montagem dos rostos da 2ª metade (teaser) + gancho na tela. Nada de intro parada.
- Legenda palavra a palavra com pop, palavra de impacto gigante + emoji, barra de progresso, selo obra/capítulo
  (só no vídeo, não no título), CTA sobre o último painel.
- Punch-in/tremor nos impactos, SFX por palavra-gatilho (com anti-poluição), memes de comédia com moderação
  (máx. 1 a cada 8 clips).
- Trilha:
  - nivelada (-28 LUFS) com ducking pela voz;
  - master em -14 LUFS / -1 dBTP;
  - nenhuma faixa > 100 s seguidos, crossfade;
  - sem repetir as dos últimos vídeos.
- Propaganda/créditos do scan nas pontas e no meio: detectar e pular.
- **Shorts**:
  - corte nas fronteiras de painel, 30-58 s, nunca no meio de uma fala;
  - Short com mais de 50% censurado não sobe;
  - título por parte "(Parte N)".
- **Vídeo longo 16:9**: compilação que "cresce" (cap 1 ao último pronto), lista de capítulos com minuto na
  descrição, playlist "Maratona".
- **Voz humana no começo do vídeo longo** (feito no compilado 16:9 do hipercool em 15/10, `bin/intros_voz.py`): o
  feed toca o início no hover e o público usa isso para checar se é voz de IA.
  - Vozes SÓ dos canais que autorizaram o dono (15/10/2026; lista em `config/intros_voz.json` → `autorizados`).
    Canal fora da lista: não usar.
  - Só fala genérica: saudação, "deixa o like/se inscreve", "bora pra história". Nunca o nome do canal/criador,
    obra, personagem ou trama; sem palavrão (anúncio limitado nos primeiros segundos); uma abertura = um criador.
  - A música do canal sai (separação de voz, por causa do Content ID) e entra a nossa trilha com ducking.
  - Vídeo da abertura: capa nítida só no 1º meio segundo, depois capa desfocada com memes animados SEM som trocando
    com a fala + legenda palavra a palavra + selo INSCREVA-SE/LIKE; emenda sem re-encode no mesmo formato do resto.
    Falas que são só "deixa o like" vão no MEIO do vídeo (troca de capítulo perto de 1/3), não no começo.
  - Cada vídeo longo postado leva uma abertura diferente (rodízio; depois Thompson pela retenção dos 30 s).
  - Pra outro projeto: copiar `bin/intros_voz.py` + `config/intros_voz.json` (e `assets/intros_voz/*.wav`).

## 4b. Vozes (TTS) — decisões do dono em 15/10

- **PROIBIDAS em qualquer projeto**:
  - `pt-BR-AntonioNeural`: voz masculina ruim;
  - `pt-BR-FranciscaNeural`: aposentada;
  - `it-IT-IsabellaNeural`: italiana, fica com sotaque em português.
- **Aprovadas** ("ótimas"), as edge **Multilingual**, grátis e sem chave:
  - femininas: Thalita, Ava, Emma, Seraphina, Vivienne;
  - masculinas: Andrew (a preferida), Brian, William, Florian, Remy, Giuseppe, Hyunsu.
  - Cada uma ganha variações virtuais de velocidade/tom (-8..+15%, -8..+8 Hz) para ter muito mais vozes.
- **Voz fixa**:
  - narrador, protagonista e par principal fixos na obra/série (podem mudar de uma obra pra outra);
  - cada personagem sempre com a mesma voz;
  - a IA às vezes chama o protagonista de "Rapaz"/"Jovem" e a voz trocava — normalizar o nome antes da voz;
  - nunca escolher voz por `hash()` do Python (muda a cada execução): usar md5 ou um arquivo de elenco.
- **Tempo**:
  - Gemini TTS ~70 min por capítulo de ~100 falas (limite de cota; no melhor caso 15–20 min);
  - edge ~5 s por fala (~9 min);
  - local no processador: Supertonic-3 ~1,3x tempo real (pt, hi, id, it, ru, vi; sem th); Kokoro 0,3x (lento).
  - Local só como reserva e no PC2.
- **Voz clonada dos parceiros (desde 19/10)**: a narração edge pronta passa por
  `D:\hipercool-materiais\python\venv_vozes\Scripts\python.exe D:\hipercool-materiais\bin\voz_clonada.py converter <voz> <narracao> <saida.wav>`
  e sai com a voz do parceiro (tom automático). Vozes prontas = `D:\hipercool-materiais\models\rvc\vozes\<voz>\<voz>.pth`.
  CPU no PC1: ~5× a duração com o PC livre, ~19× lotado. Shorts/aberturas/vídeos curtos; compilado longo não.
  **Qual voz base** (dono ouviu, 19/10): edge **Francisca + clone = pronúncia perfeita** (o `edge_tts_engine` comum
  ainda troca a Francisca pela Thalita — trava de 16/10; com `VOZ_CLONADA` setado ela passa); **Kokoro + clone = emoção e fala acelerada**
  ("narração de jogo"); **Andrew + clone = sotaque de gringo, não usar em pt**. Melhor dos dois = **misto**: Kokoro na
  abertura e chegando nos impactos da curva de locutor, Francisca no resto (mesmo timbre, ritmo humano).
  Frase a frase: `voz_clonada.py lote <voz> <lista.json>` (1 processo, o modelo carrega 1x; `--tom-base` = tom fixo
  por base, sem pular semitom entre frases). Referência pronta: recapd `bin/anime_tts.py preparar_clone` +
  `bin/anime_voz_clonada.py` (rodízio narrador × base nos Shorts de parceiro anime/manhwa). Edge+clone ~1/3 mais
  rápido que Kokoro+clone (o clone é o que pesa: ~2–4× a duração).
  **v2 (20/10, em produção no recapd)**: `VOZ_CLONADA_VERSAO=2` + `perfil_v2.json` da voz → ritmo/tom/volume/EQ do
  narrador real em cima da curva de locutor; o `lote` aceita `tom_extra`, `f0_escala`, `eq` por item. Depois do
  `pos_processar`, `narracao_curva.humanizar` põe respiração, micro-pausa e ênfase (ver Novidades 20/10).
  **Short: por último, `narracao_curva.microcortes`** (22/10, obrigatório em Short, nunca no longo): pausa > 0,07 s
  sai, a fala não acelera. Áudio compartilhado com o longo = cortar numa cópia (recapd `anime_segments._fala_do_short`).
- **Código de referência**: `D:\hipercool-videos\bin\elenco.py` (elenco por obra em `config/elenco/<obra>.json`,
  motor em `config/fila.json` `tts_motor`).
- **Janelas na tela**: processo agendado (pythonw/vbs oculto) que abre programa de console abre janela nova.
  Importar `D:\hipercool-videos\bin\sem_janela.py` (CREATE_NO_WINDOW em todo subprocess) no ponto de entrada.

## 4b2. Nome da obra em LUGAR NENHUM (dono, 15/10)

- Nem título, descrição, tags, hashtags, PLAYLIST, comentário, texto na tela (selo, cartão de capítulo), nem traduzido.
- Playlist: nome no padrão dos títulos (premissa/provocação + palavras buscadas), gerado uma vez e gravado na
  config (a playlist é achada pelo nome). Hipercool: `seo.nome_playlist` + `postar_hipercool._nome_playlist`.
- Já postado: trocar no Studio (`D:\postador-de-videos\bin\youtube_studio_extras.py --metadados` e
  `--renomear-playlists`). Já renderizado: NÃO renderizar de novo (ordem do dono), só renomear o que der.

## 4c. Groq (Whisper) — sempre pelo proxy Webshare (dono, 15/10)

- Chaves em `D:\postador-de-videos\secrets\groq_keys.json` (o dono mandou 6 novas em 15/10; a 1 deu 401 e ficou
  `"status": "invalida"`).
- Todo pedido sai por um proxy da Webshare (`secrets/proxies.txt`, a mesma rotação da voz do Gemini); sem proxy, não
  vai direto. Código: `D:\hipercool-videos\bin\groq_api.py` (`transcrever`, `--testar`).
- Mandar áudio comprimido (FLAC/Opus), não WAV: a banda do proxy é limitada.
- Atenção: `urllib` com o User-Agent padrão leva 403 do Cloudflare do Groq; usar `requests`.
- O manhwa-react usa as mesmas chaves: ao mexer lá, passar as chamadas por esse mesmo esquema.

## 4d. ffmpeg 8: imagem parada como clipe, não `-loop 1` (15/10)

- Num gráfico com muitas entradas (vídeo + overlays + emojis/figurinhas), várias entradas `-loop 1 -t X -i imagem.png`
  fazem o ffmpeg 8.1 travar sem usar CPU, sempre no mesmo quadro (o hipercool perdeu horas: cap 6 e cap 8). Trocar
  `tpad` por `setpts`, `-threads 1` ou `-framerate 5` NÃO resolve.
- Solução conferida: converter cada imagem parada num clipe `.mov` curto com alfa (`-c:v qtrle -pix_fmt argb`, em
  cache) e usar como entrada comum. Código: `D:\hipercool-videos\bin\fx_acabamento.py` → `_clipe_parado`.

## 5. Efeitos 2.5D e profundidade (`bin/fx_parallax.py`, `bin/hiper-pipeline.py`)

- Personagem recortado (modelo local isnet-anime, CPU) + inpaint do fundo.
  - Personagem e fundo andam em velocidades diferentes, com desfoque de profundidade no fundo, sombra e
    contorno de luz no personagem, balões nítidos.
- Modos:
  - `parallax`;
  - `foco` (câmera vai ao personagem);
  - `close` (punch-in no rosto — YOLOv8 de rosto de anime; nunca em painel +18/sugestivo);
  - `objeto` (close em coisa pequena quando a fala cita objeto);
  - `andar` (personagem de corpo inteiro atravessa a cena);
  - `impacto`, `tensao`.
- ~50% dos clips com efeito (antes 16%), nunca dois parallax seguidos.
- Cor e vinheta pelo clima da cena.
- Passe final em Quick Sync quando houver GPU Intel.

## 6. Censura (versão que vai pro YouTube)

- Só **nas partes explícitas do painel**: mosaico local com borda suave; balões e legenda nítidos.
- Nunca borrar a tela inteira / o vídeo pronto por janela de tempo.
- Detector:
  - Sightengine nudity-2.0 (NudeNet de reserva);
  - caixas pelo Gemini;
  - veredito do Gemini antes de censurar ("não explícito" = intacto).
- Chamada "SEM CENSURA" (pt): na descrição e no comentário fixado, **sem link** — link pra conteúdo adulto =
  strike. Mede a procura pelos comentários.
- **Análise do vídeo pronto antes de postar — obrigatória (16/10).** O canal pt do hipercool levou advertência do
  YouTube ("Nudez e conteúdo sexual") por um compilado com painel sem censura e mosaico no lugar errado: a censura
  por painel errou e ninguém assistiu o arquivo final. No hipercool: `bin/revisao_video.py` tira 2 quadros/s do
  vídeo FINAL e pergunta ao Gemini, um quadro por vez, se há mamilo/genitália/nádegas à mostra sem mosaico ou com
  mosaico fraco (3 opiniões, basta 1 "sim"). **Desde 18/10 ela só AVISA** (regra do dono: nenhum canal fica sem
  postagem): marca os painéis pra fosco no próximo render e o vídeo sobe mesmo assim. Copie o módulo como aviso, não
  como trava. Com o Gemini do proxy: só um quadro por pedido, vocabulário de moderação e resposta booleana — senão o
  filtro do Google recusa.
- Painel com score baixo no Sightengine também pode ter nudez (manhwa engana o detector): pergunte à visão.
- Reaproveitamento em TikTok/Instagram só de vídeo que passou nessa análise.

## 7. Postagem

- **Nenhum canal fica um dia sem postagem** (dono, 18/10). Nenhum impedimento segura a postagem: avisa e sobe.
- Produção e postagem são independentes (cada uma liga/desliga).
- Agendado sempre (publishAt 10+ min), nunca público direto — é PROTEÇÃO, não atraso (dono 19/10): agendado, o YouTube
  checa direitos autorais antes de ir ao ar; se achar problema o vídeo não é publicado e o canal não leva advertência.
  O postador já força isso pra todos (`politica.horario_obrigatorio`).
- Posta no **pico de cada país** (hora de lá), poucos vídeos por dia, intervalo entre eles.
- Línguas: cada canal só recebe vídeo NO idioma dele. Postagem só pelo navegador (sem Data API).
- Playlist por obra: "<Obra> — Recap" (capítulos) e "<Obra> — Maratona" (longo).
  - Pendente de decisão do dono: o nome da playlist é público e hoje leva o nome da obra.

## 8. O que medir (e onde fica)

- Pose/layout de capa: `workspace/capas_poses.json`.
- Estilo de título: `workspace/titulos_estilos.json` + `estilo_titulo` em `workspace/postagens/*.json`.
- Extras do Studio por vídeo: `workspace/postagens/*.json` → `extras`.
- Falta ligar: ler CTR/retenção por vídeo no Studio (Analytics pelo navegador) e alimentar
  `registrar_vencedora` / `seo.registrar_resultado`.
