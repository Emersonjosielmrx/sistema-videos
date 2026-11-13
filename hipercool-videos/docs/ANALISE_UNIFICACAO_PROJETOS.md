# Análise: projetos de vídeo funcionando como um só (18/10/2026)

Pedido do dono (18/10 14:29): "tem outras melhorias pra unificar os projetos pra eles trabalharem mais em conjunto?
Já fizemos postador unificado, agente, materiais compartilhados. Analise profundamente o que poderia melhorar pra que
funcionem como um só, só que pra vários propósitos de tipos de canal, como é hoje."

Arquivo de controle retomável: cada achado é gravado aqui na hora. Ao retomar, seguir só as frentes "pendente".
Antecedente: D:\AUDITORIA_MELHORIAS_20261015 (cópia de módulos do hipercool → outros; não trata de arquitetura).

## Frentes

| # | Frente | Status |
|---|--------|--------|
| 1 | Cadastro de canais (quem é dono de cada canal, nicho, idioma, limite) | feito |
| 2 | Postagem: caminhos, limite por canal, horários (publishAt) | feito |
| 3 | Fila de produção e uso dos 3 PCs | feito |
| 4 | Código repetido entre projetos (groq, tts/vozes, seo, avisos, ffmpeg) | feito |
| 5 | Tarefas agendadas do Windows (quantas, de quem, sobreposição) | feito |
| 6 | Monitoramento e avisos (vigia, Telegram, painéis) | feito |
| 7 | Estado e catálogo (o que foi feito/postado, por projeto) | feito |
| 8 | Segredos e logins (onde ficam, cópias) | feito |
| 9 | Retorno de desempenho (estatística do YouTube voltando pra produção) | feito |
| 10 | Síntese: proposta em etapas | feito (aguardando o dono escolher o que fazer) |

## Execução (dono 18/10 18:02: "faça todas")
Divisão do Manhwa Noturno (sugestão aceita por omissão): hipercool até 3/dia, parceiro só a vaga que sobrar.
Cada item: status + o que foi feito + como foi verificado. Retomar daqui.

| # | Item | Status |
|---|------|--------|
| E1 | Aviso do anime pelo bot do postador | FEITO 19:00 — `_tg_safe.py` virou COMUM (hipercool, historias, postador, recapd): sem `secrets\telegram-*.json` (nenhum projeto tinha) usa token+chat do `postador\config\telegram.json`; ganhou `send_telegram` (historias chamava e não existia → avisos dele nunca saíram). `anime_health_monitor`: chat do mesmo bot e confere `AnimeOcioso` em vez de recriar o noturno aposentado. Verificado: mensagem de teste enviada (True) e rodada real do monitor sem "sem token". |
| E2 | Ledger com projeto/tipo/caminho; reserva por projeto real | FEITO 19:10 — `politica.registrar_upload` grava `projeto`, `tipo`, `caminho` (arquivo segue só o nome); `postar_youtube(tipo=)`; posters aceitam `--tipo`. Quem posta se identifica de verdade: hipercool `PROJETO="hipercool"` (era "manhwa-react"/dono), parceiro `PROJETO="parceiro"` (era `reservado_para(canal)`), rede/publish/postar_tudo_hoje passam tipo. `pode_postar()` decide pelo cadastro (dono / alimentador livre / sobra). **Achado e corrigido**: 10 uploads do hipercool em 17-18/10 abriram PÚBLICOS na hora (public sem publish_at) — agora `horario_obrigatorio()` nos dois posters: mínimo agora+11 min. Espera da trava do Chrome (até 20 min) não conta mais como timeout (pedido do claude do parceiro). Verificado: compila, `--help` dos posters, regras testadas com o ledger real (abaixo E5). Falta prova numa postagem real (próxima rodada). |
| E3 | Medição 48 h com os Noturnos | FEITO 19:35 — Noturnos não têm token (só navegador) e o yt-dlp anônimo é barrado ("não é robô"). `metricas_rede.py` (Studio pelo navegador, rodada de hora em hora da rede) agora também lê os vídeos do LEDGER que não são da rede (Noturnos, hipercool, parceiro; canais ativos do cadastro), 1 leitura entre 48-96 h, 1 vaga garantida por rodada, fora da mediana/nota da rede. `notificar_telegram.medir_48h` usa essas views pros canais sem API e a origem vem de `projeto`/`tipo` do ledger. Verificado: fila de teste (12 vídeos de 7 canais) e leitura real no Studio do Manhwa Noturno (w8YiB4Z1MsA: 4 views em 54 h). O aprendizado_global com os Noturnos só aparece depois das próximas rodadas. |
| E4 | Juntar peças de produção no comum (recursos.py) | FEITO 19:25 — viraram COMUM (versão única, cópia "# COMUM" em cada projeto): `_tg_safe.py` (E1), `groq_api.py` (hipercool+manhwa-react: base manhwa-react com proxy próprio + import que serve aos dois; teste real 200 em 2,3 s), `notificar.py` (nome do projeto vem da pasta), `edge_tts_engine.py` (base recapd = produção do parceiro, IP direto primeiro; + do historias: 0 KB rejeitado, arquétipos, ava_sussurro, FORCE_DIRECT_TTS; + do postador: VOZES_PROIBIDAS trocadas na hora). Teste real: frase gerada (719 KB) e Francisca pedida → saiu com a aprovada. Versões antigas em `hipercool-materiais\comum\_antigos\`. NÃO juntei: `split-shorts.py` e `narration.py` de recapd/historias/postador — são cópias de julho que só scripts antigos usam (o historias usa `split_shorts.py`; a voz do anime usa `narracao_curva`, já comum) → legado (E12). Mudança de comportamento: historias (parado) passa a tentar IP direto no edge-tts antes do proxy, como o recapd. |
| E5 | Cadastro único de canais + cota por projeto | FEITO 19:10 — `postador\config\canais.json` (26 canais) gerado por `postador\bin\canais.py gerar` dos arquivos antigos (não mexe neles); `canais.py conferir` mostra divergência. politica lê dele: dono, alimentadores, `max_dia` (só aperta). Manhwa Noturno: dono hipercool, teto 3 (regra BR), parceiro "sobra" (canal vazio no dia ou depois das 23:00 de lá). 3 Noturnos dedicados: dono parceiro, teto 3. Reacts e línguas: parceiro "livre" (como era), teto 4 — NÃO pus 3 nos reacts pra não cortar o react (mais views) com o teste do parceiro de 3/dia; decisão do dono. Teste real: Manhwa Noturno hipercool ok / parceiro "vaga do dono até 23:00" / manhwa-react "reservado". |
| E6 | Controle único liga/desliga + status único | FEITO 19:30 — `D:\video-fila\controle.py` + `controle.json`: `ligado(projeto, etapa)` junta o controle novo e os botões antigos (que continuam valendo, com o alcance de sempre). Postagem: checado no ponto central (`politica.checar_upload` → "parado"), vale pra todo projeto. Produção: hipercool `fila.ciclo/postagem`, parceiro `producao`, `ocioso.py` (anime), manhwa-react `batch`. CLI: `python controle.py desligar parceiro postagem [motivo]` / `ligar` / `tudo`. Status único `D:\video-fila\status_videos.py` (botões, canais hoje com teto/agendado/quem postou, tarefas, render) + resumo no "status" do Telegram (hipercool `vigia_telegram`). Testado: desligar historias → politica barra só ele; religar volta; painel mostra hipercool produção desligada (FILA_DESLIGADA, de propósito). Cadastro: estado do canal agora é calculado na hora (`politica.estado_do_cadastro`) e o canais.json se refaz sozinho quando os arquivos de origem mudam (parceiro ganhou destinos às 19:2x — sem isso seria barrado como "reservado"). |
| E7 | secrets único | FEITO 19:45 — central = `D:\postador-de-videos\secrets` (backup dele em `_antes_unificar_20261018\`). `secrets\` de hipercool, recapd, historias e veo agora são JUNÇÃO pra ele; as pastas antigas ficaram como `secrets_antigo_20261018` (nada apagado). Juntado sem escolher versão: proxies testados um a um (105 válidos na união → **67 vivos**, contra 31 vivos que o central tinha; 23 linhas do hipercool nem eram proxy, eram e-mails); chaves somadas pelo token (Gemini +4 = 52, ElevenLabs +37 = 43, Sightengine +2; Groq: as velhas já estavam no central). Formato próprio guardado com nome do projeto: `elevenlabs_keys_hipercool.json` (o `elevenlabs_tts.py` do hipercool aponta pra ele — ele regrava o arquivo no formato dele), `playwright_state_recapd/hipercool.json`. Verificado: hipercool/recapd/historias leem 67 proxies, veo 52 chaves Gemini, Groq 200 pelo proxy depois da troca. Desfazer: apagar a junção e renomear `secrets_antigo_20261018` de volta. |
| E8 | postar.json em todos + catálogo por ficha | FEITO ~23h — `catalogo.py`: `FICHAS` (catálogo POR FICHA: 1 vídeo por `postar.json`, postagem lida da ficha) com a pasta do parceiro; ledger com `caminho` liga direto ao arquivo (antes "video.mp4" não casava). Resultado real: **61 Shorts de parceiro** entraram no catálogo (antes 0), todos com a postagem do YouTube. Reuso: 1 já tem conta (TikTok `inovaremanhwaverse2`, regra antiga "postados_em: Manhwa Noturno"); os outros 60 só saem quando uma conta aceitar o projeto "parceiro" em `reuso_plataformas.json` (decisão do dono — direito de parceiro no TikTok/Insta). `etapas.json`: parceiro `so_no_fim` (o backup não tira o arquivo do PC antes da hora; nada muda no disco hoje). Escopo: NÃO forcei postar.json no hipercool/manhwa-react/veo — eles postam direto e o registro comum agora é o ledger (projeto/tipo/caminho); postar.json segue como ficha comum dos itens em fila (parceiro, anime, historias). Recap de anime longo fica como estava (vai pro Drive pelo modo ocioso). |
| E9 | Agenda única por canal | FEITO ~23h (como REGRA CENTRAL, não como fila nova) — `politica.horario_publicacao` decide a hora de abrir de todo upload, somando TODOS os projetos: intervalo mínimo + **teto por dia de publicação** (dia de lá; antes só contava o dia do upload) — dia cheio vai pro 1º horário do canal no dia seguinte (horários do cadastro: parceiro/rede/pico do hipercool). `horario_obrigatorio(canal, pedido, projeto)`: nunca "já" (mín. +11 min, corrigido pra respeitar o intervalo também), e alimentador "sobra" só pega vaga de HOJE; `pode_postar` da sobra exige o dia de hoje abaixo do teto. Os 5 agendadores continuam PROPONDO a hora (não reescrevi a rede nem a fila do hipercool — risco alto, react é o que mais dá view); quem manda é o postador. Simulado com o ledger real: Manhwa Noturno (4/3 hoje) → amanhã 12:20; Dorama (3/3) → amanhã 12:50; ForjaReact pedido 11:00 amanhã com vídeo às 11:00 → 12:00. Falta ver numa postagem real. |
| E10 | Despachante dos 3 PCs + medidor único | FEITO ~23h — **Medidor único** = `D:\video-fila\maquinas.py` (ssh do Git fixo; disco do PC2 = C:, onde renderiza; regra do desktop "teclado/mouse há 20 min" trazida do ociosidade.py); `pc2_recapd.medir()` e `hipercool-materiais\bin\ociosidade.py` agora só chamam ele (mesmas saídas). **Despacho**: `fila_render.vez(..., maquina="pc2")` + `fila_render.marcar(projeto, rótulo, pid, máquina)`; o medidor conta como ocupado quem tem a vez/marca da máquina (menos ele mesmo). **Achado e corrigido**: o hipercool (`fila.pc2_ciclo`) só via o hiper-pipeline dele no PC2 e disparava língua por cima de Short de parceiro/anime longo rodando lá — agora usa o medidor comum dentro da vez do PC2. `ocioso.py` (parceiro/anime) mede de novo com a vez na mão e marca o anime_auto (que só chega no PC2 minutos depois) até ele terminar. Testado: medição real dos 3 PCs; marca viva → PC2 ocupado; processo morre → livre; dentro da própria vez não conta a si mesmo. |
| E11 | Placar comum → prioridade | FEITO ~23h — o `aprendizado_global.json` virou o PLACAR COMUM: `medir_48h` agora também grava `por_projeto_tipo` (do ledger novo; enche a partir de hoje) e `por_idioma` (do cadastro). Hoje: pt mediana 9 (29% ≥1000), hindi 0 (1 de 10 passou de 1000), id/it/ru/th 0 em todos, vi 1 medida. **Prioridade de produção**: a fila do hipercool (`_ordem_linguas`, PC1 e PC2) renderiza as línguas na ordem do placar — com os números de hoje: hi → (sem dados: vi, fr, en) → id, it, ru, th. Nenhuma língua é desligada (o dono decide; o placar mostra). Placar no `status_videos.py`. Não mexi na prioridade ENTRE projetos (`video-fila\fila.json`, decisão do dono) nem no rodízio de nicho do parceiro (`parceiro_diario._prioridade`, outra sessão mexeu hoje). |
| E12 | Legado pra _legado | PARCIAL ~23h — **Não movi arquivos em lote**: a análise estática (tarefas agendadas → imports → nomes citados) se mostrou NÃO confiável — marcou como "sem uso" o `postar_tiktok_auto.py`/`postar_insta_auto.py`, que o `postar_tudo_auto.bat` roda todo dia. E as cópias de julho no `postador\bin` (hiper-pipeline, effects_engine…) ainda são alcançadas por scripts ativos — eu estava errado em chamar de lixo. Feito o que tem valor de segurança e dá pra verificar um a um: os `youtube_poster.py` LOCAIS do recapd e do historias (subiam direto pela API, sem reserva/teto/agendamento/parada geral) agora recusam o upload com erro claro; o resto do módulo (ler canais etc.) segue. Verificado: os dois recusam; nenhum script ativo do anime/parceiro usa essa cópia. Limpeza de verdade (scripts `_check_*`, `fix_*`, `gen_*`, `test_*` na raiz do recapd, tarefas desligadas de julho, `TikTokCDP` apontando pra `D:\hipercool-producao`) fica pra revisão manual com o dono — mover às cegas quebraria produção. |

### Respostas do dono (18/10 ~23h30) e o que foi feito
1. **Parceiro no TikTok/Insta: sim.** Regra `parceiro_de` no `catalogo._conta` (só Shorts de parceiro daquele canal do
   YouTube, sem levar react/Veo) + contas por tema em `reuso_plataformas.json` (backup `.bkp_20261018_parceiro`):
   TikTok inovaremanhwaverseita ← ManhwaReact; Insta _lucrocomia_ ← Dicas financeiras/AssistIA; Insta
   videocassetadascom.ia ← MundoQueNaoExiste. Com o mapeamento da outra sessão (emersonjosiel*, Noturnos): parceiro
   com conta = **34 TikTok, 10 Insta** (antes 0). Sem conta (não há conta no tema/língua): canais de língua, Fio da
   Meada, ForjaReact.
2. **"Vê o que é melhor" (BR 3/dia × parceiro 1-3/dia programando 7 dias)**: a outra sessão tirou do parceiro o "deixa
   1 vaga pro dono" pra encher a semana — o react da rede (sobe poucas horas antes) ficaria sem vaga. Decidido:
   teto de UPLOAD = 4/canal/dia (piso do YouTube, não muda) separado do teto de PUBLICAÇÃO por dia (cadastro
   `max_dia`: reacts BR 3, Noturnos 3, Manhwa Noturno 3, línguas 4); `reserva_dono: 1` em todo canal onde o parceiro é
   "livre" — 1 vaga/dia guardada pro dono no upload (liberada às 23:00 se ele não usou) e na publicação. Resultado:
   parceiro até 2/dia nos reacts e 3 nas línguas e nos Noturnos dele; sobe até 3/dia → a semana programada cresce.
   Testado com ledger simulado (dia 20 com 2 do parceiro: parceiro → dia 21, rede ainda cabe no dia 20).
3. **Produzir em todas as línguas: sim** — já estavam todas ligadas; só o **francês** segue desligado: upload
   bloqueado pelo YouTube (strike) até ~26/12; nota de 14/10 manda religar ~19/12. Ordem pelo placar continua.
4. **Limpeza: sim.** 11 tarefas agendadas que apontavam pra arquivo inexistente removidas (XML em
   `D:\video-fila\tarefas_removidas_20261018\`, restaurar com Register-ScheduledTask). 172 rascunhos da raiz do recapd
   (`_check_*`, `_sync*`, `fix_*`, `gen_*`, `test_*`, saídas .txt/.png…) movidos pra
   `D:\recapd-ambientes\producao\_legado_20261018\` (LEIA.md com a lista; ficaram os 6 que código ativo cita).
   Verificado: `parceiro_diario status` normal depois.

## Achados

### 1. Cadastro de canais — espalhado em ~10 lugares, 4 jeitos de chamar o mesmo canal
Onde um canal aparece hoje:
- `D:\credenciais-canais\youtube_canais.json` (54, id + token + email) — o "id" oficial (`0RW4rz…`, `novo_manhwanoturno`).
- postador `config\youtube_navegador.json` (25, por SLUG `manhwanoturno`, perfil do Chrome; perfil real vem do cofre
  `D:\logins-google\cofre\contas.json` pelo email).
- postador `config\rede_canais.json` (20, rede do manhwa-react: nicho, persona, horários).
- postador `config\canais_reservados.json` (dono de cada canal por projeto) e `canais_status.json` (suspensos/token morto).
- manhwa-react `canais\canais.json` (21, slug/pasta/foto) + uma pasta por canal.
- recapd `producao\config\parceiro.json` → `pt` (Noturnos: canal, nicho, fuso, 3 horários, por_dia) e `idiomas`.
- hipercool `config\fila.json` → `canal_pt: "Manhwa Noturno"` (pelo NOME) e `idiomas` (id + fuso + pico + handle).
- Fontes de parceiro em DUAS listas: `video-fila\canais_parceiros.py` (CANAIS) e `parceiro.json` → `fontes` (31).

Problema real (não é só arrumação):
- `canais_reservados` diz que o Manhwa Noturno e os 7 canais de língua são do **hipercool**, mas o parceiro do recapd
  também posta neles, com plano próprio: Manhwa Noturno 12:20/18:30/22:10 × 3/dia (parceiro) + pico 18–23h com
  completo+compilado+Shorts (hipercool); línguas 16–17h (parceiro) + pico local até 3/dia (hipercool). Ninguém enxerga
  o plano do canal inteiro; o único freio comum é o limite de 4/canal/dia do postador — quem chega primeiro leva
  (18/10: hipercool usou 4/4 no Manhwa Noturno).
- Mesma informação (fuso, pico, handle, nicho) repetida e divergindo entre arquivos; trocar um canal = editar 3–5 lugares.

Proposta: **um cadastro único de canais** (1 linha por canal: id do credenciais, slug, handle, plataforma, idioma, fuso,
pico, nicho/tipo, máx/dia, status, e "quem alimenta" com prioridade/cota de cada projeto). Os outros arquivos passam a
ler dele (ou são gerados dele). Parceiro vira "preenche a vaga que sobrar" no canal de outro dono.

### 2. Postagem — o "porteiro" é único, mas cada projeto decide sozinho QUANDO postar
O que já é comum (bom): todo upload passa por `postador\bin\politica.py` (`checar_upload`: parada geral, canal
bloqueado, reserva, 4/canal/dia, aprovação) e sobe pelo navegador (`youtube_web_poster.py`). Ledger único
`postador\logs\uploads_ledger.jsonl`.

O que não é comum:
- **Cada projeto calcula o próprio horário** (publishAt) com regra própria: hipercool `fila.postagem()` (pico por
  língua, intervalo_h, max_dia), parceiro `parceiro_diario.postar()` (3 horários fixos/canal, "urgente" +11 min,
  "deixa 1 vaga pro dono"), manhwa-react `mr/publish.proximo_horario()` e `mr/rede.py` (horários do rede_canais),
  postador `postar_tudo_hoje` (pools). O `politica.horario_publicacao()` comum só afasta 1 h do vizinho.
- A coordenação entre eles está escrita em COMENTÁRIO de código (parceiro: "a tarefa sobe às 23:20, depois da janela
  do hipercool… deixa 1 vaga livre pro dono"). Mudou o horário de um, quebra o acordo sem ninguém saber.
- **A reserva de canal está desligada na prática**: hipercool e parceiro chamam `postar_youtube(projeto=
  politica.reservado_para(canal))` — se identificam como o dono, então `checar_upload` nunca barra.
- **O ledger não diz quem postou nem o quê**: campos só `ts, canal_id, canal, video_id, arquivo, publish_at, script`.
  Sem `projeto`, sem tipo (Short/completo/compilado/react/veo), sem nicho, e `arquivo` muitas vezes é só "video.mp4"
  (parceiro/rede usam pasta por item). Não dá pra: dividir cota por projeto, medir desempenho por projeto/tipo,
  nem detectar o mesmo vídeo postado por dois projetos.
- A cota conta pela hora do UPLOAD, a agenda é pela hora de PUBLICAÇÃO — cada projeto contorna isso do seu jeito.
- recapd e historias ainda têm `youtube_poster.py` LOCAL (cópia antiga que posta por API, proibido desde 16/10).
  Usado por scripts de postagem antigos deles (postar_animes, postar-fila, batch-post-shorts…). Conferir na frente 5
  se alguma tarefa agendada ainda chama.

Proposta: **agenda única por canal** no postador — os projetos não escolhem hora, entregam o vídeo pronto com
(projeto, tipo, prioridade, prazo) numa fila de saída; um só "agendador" distribui as vagas do dia de cada canal
(cadastro da frente 1: pico, máx/dia, quem tem prioridade) e chama o web poster. Ledger ganha `projeto`, `tipo`,
`arquivo` completo e id do item. Enquanto isso não existe, o mínimo: gravar `projeto`/`tipo` no ledger e parar de
usar `reservado_para(canal)` como identidade.

### 3. Fila de produção e PCs — começou a ser comum, mas pela metade
Já comum: `D:\video-fila\fila_render.py` (vez de render pesado no PC1, prioridade por projeto em `fila.json`; hoje
anime=1, parceiro=2, hipercool=3, historias=4). Usam: hipercool (hiper-pipeline, hiper-longo), anime-pipeline
(anime e parceiro), historias. **Não usam:** manhwa-react e veo (veo é leve; manhwa-react conferir na frente 5).
Repetido:
- Medidor de ociosidade em DOIS: `hipercool-materiais\bin\ociosidade.py` (81 linhas, CPU 35%) e
  `video-fila\maquinas.py` (84 linhas, regras próprias) + `pc2_recapd.medir` (CPU 40%, RAM 4 GB). Três réguas
  diferentes pra "o PC está livre".
- "Mandar código pro worker" em TRÊS: hipercool `bin\pc2.py`, `video-fila\pc2_recapd.py` (cópia adaptada do pc2.py)
  e postador `bin\workers.py`.
- Só o anime tem "modo ocioso" no PC2 (`video-fila\ocioso.py`); o hipercool tem worker próprio no PC2; o desktop
  quase não é usado. Não existe "um trabalho pendente → o PC livre pega", e sim cada projeto com sua máquina.
Proposta: um medidor só (o de `hipercool-materiais\bin`) + um "despachante" de trabalho pesado para os 3 PCs com a
mesma fila de prioridade (`video-fila\fila.json`), e um sincronizador de código só pros workers.

### 4. Código repetido — já existe o mecanismo, falta usar nas peças que importam
Outro agente criou em 18/10 `D:\hipercool-materiais\bin\recursos.py` + `D:\hipercool-materiais\comum\`: fonte única,
cópia idêntica marcada "# COMUM" em cada projeto, `recursos.py subir x.py --de <projeto>` testa e espalha. Painel
(rodado 18/10 14:4x):
- 12 módulos já comuns (sem_janela, master_loudness, panel_classifier, styled_transitions…).
- 13 idênticos ainda fora do comum (recapd + postador, quase todos legado de julho).
- **65 SEPARADOS** (mesmo nome, versões diferentes). Os que estão em produção e mais pesam:
  `narration.py` (hipercool 18/10 tem o narrador v2; historias e recapd na antiga), `edge_tts_engine.py` (4 versões),
  `split-shorts.py` (3; a do hipercool tem o CTA e o conserto do -ss de 18/10), `censura_visual.py` (3),
  `claude_client.py` (4), `groq_api.py` (manhwa-react mais nova que a do hipercool), `limitador.py` e `notificar.py`
  (manhwa-react mais novas, 18/10), `elenco.py`, `fila.py`.
O painel NÃO pega a mesma função com nome diferente:
- SEO: hipercool `seo.py` × recapd/historias `seo_generator.py` × manhwa-react (próprio).
- Avisos Telegram: `notificar.py` (hipercool/manhwa-react) × `notifica.py` (historias/veo) × postador
  `notificar_telegram.py` (39K).
- Vigia: hipercool `vigia_agente.py` × `video-fila\vigia_geral.py` ("cópia adaptada").
- Ociosidade e sync de worker (frente 3).
Lixo que atrapalha: `postador\bin` ainda tem cópias de julho de render (effects_engine 162K, hiper-pipeline 85K,
split-shorts, edge_tts_engine…) e recapd tem `_snapshots`/`_BACKUP_20260707` — entram no painel como "versões" e
confundem quem vai juntar. Postador deveria ter só postagem.
Proposta: (a) juntar primeiro as peças de produção da lista acima, uma por vez, com `recursos.py subir --juntei`;
(b) ensinar o painel a agrupar por FUNÇÃO (tabela de apelidos: seo/seo_generator, notificar/notifica/…);
(c) marcar como legado (mover pra `_legado\`, com confirmação do dono) o que nenhuma tarefa agendada chama.

### 5. Tarefas agendadas — ~20 ativas, cada uma com relógio, trava e botão de desligar próprios
Ativas (18/10 14:40): hipercool (Postagem 20m, PC2 20m, Vigia 20m, ReligarProducao; Fila desligada de propósito),
anime (AnimeOcioso 15m, AnimeRecapMonitor 1h), parceiro (Producao 30m, Postagem 30m), manhwa-react (Rede 1h,
Comentarios 30m, Lote 02:00), postador (PostadorDeVideos 06:40, NotificarTelegram 5m, PainelCanais 3h), video-fila
(VigiaVideos 20m, AtualizarYtDlp, LimparCacheChrome, LimparRelatoriosWindows), materiais (VozClonadaFila,
VozClonadaVigia 10m), backups (BackupDriveVideos, BackupCachesHipercool), MonitorOpus 10m.
- **Botões de desligar espalhados e com o mesmo nome pra coisas diferentes**: `hipercool\config\POSTAGEM_DESLIGADA.json`
  (só hipercool) × `postador\config\POSTAGEM_DESLIGADA.json` (botão DESLIGAR do desktop: rede + parceiro +
  postar_tudo — o hipercool NÃO lê esse) × `politica` parada geral (todos) × `FILA_DESLIGADA`, `PC2_DESLIGADO`,
  `video-fila\OCIOSO_DESLIGADO.json`, `parceiro.json ligado`, `.bat` LIGAR/DESLIGAR de cada um. Apertar "desligar
  postagem" no desktop não para o hipercool.
- Nenhuma tarefa chama os `youtube_poster.py` locais (API) do recapd/historias → são código morto (bom pra limpeza).
- Restos: `TikTokCDP` (Ready) aponta pra `D:\hipercool-producao` (pasta antiga); ~15 tarefas desligadas de julho.
- `postador\bin` guarda scripts que só a rede do manhwa-react usa (`limpar_veo`, `extras_rede`, `metricas_rede`) e o
  parceiro roda com o venv do veo (tzdata). Fronteira "o que é de quem" borrada.
Proposta: um arquivo de controle só (ex. `D:\video-fila\controle.json`: por projeto × produção/postagem, mais
"tudo") que todos leem, e um `status` único que lista as tarefas de vídeo com última execução/resultado/estado do
botão. Os arquivos antigos podem continuar valendo por um tempo (lê os dois).

### 6. Monitoramento e avisos — muitos vigias, ~7 jeitos de mandar Telegram, aviso que se perde
- [19/10: FEITO — vigia único = `VigiaVideos` (`video-fila\vigia_geral.py`) roda as checagens e o agente do hipercool
  também e manda 1 mensagem por rodada; `HipercoolVigia` desligada.] Vigias com agente: `HipercoolVigia` (hipercool `vigia_agente.py`) e `VigiaVideos` (`video-fila\vigia_geral.py`,
  cópia adaptada do primeiro). Mais vigias sem agente: `AnimeRecapMonitor`, `VozClonadaVigia`, `MonitorOpus`,
  postador `vigia_melhorias.py`, e o `NotificarTelegram` (resumo de postados/filas).
- Envio de Telegram reimplementado em: hipercool `notificar.py`/`_tg_safe.py`/`fila.avisar`, manhwa-react
  `mr/notificar.py` (cópia), recapd `_tg_safe.py` + busca própria no `anime_health_monitor`, historias
  `notifica.py`/`_tg_safe.py`, veo `notifica.py`/`cron_gerar_video_llm`, postador `notificar_telegram.py`.
- **Aviso perdido, confirmado no log de hoje** (`recapd\producao\logs\anime_health_monitor.log` 14:37): "Telegram sem
  token — alerta só no log". O monitor do anime procura o token em `secrets\` do recapd e não acha; o bot que o dono
  usa é o do postador (`postador\config\telegram.json`, que o hipercool e o manhwa-react já usam). No mesmo log há
  falhas reais de postagem do parceiro (InventoReact/ForjaReact: TimeoutError no Studio) que ninguém recebeu por ali.
- O monitor do anime ainda vigia a tarefa `AnimeRecapNoturno`, substituída pelo `AnimeOcioso` em 17/10 (só confere se
  existe, não religa — checagem inútil, não perigosa).
- Visões de status separadas: hipercool `vigia_telegram status`, postador `painel_canais` (só rede, HTML), recapd
  `dashboard.html`/painéis, hipercool `painel_ao_vivo`. Não há uma visão "todos os canais: postado hoje / agendado /
  estoque / último erro".
Proposta: (a) um `avisar()` comum (pelo `recursos.py`) que sempre usa o bot do postador — conserta já o aviso perdido
do anime; (b) um vigia só (o `vigia_geral` absorve as checagens do hipercool, ou o contrário) com uma lista de
checagens por projeto; (c) o `status` do Telegram passa a mostrar todos os canais a partir do cadastro (frente 1) +
ledger (frente 2).

### 7. Estado e catálogo — cada projeto anota do seu jeito; o catálogo adivinha por pasta
- Catálogo central `postador\bin\catalogo.py` → `config\catalogo_videos.json` (1.649 vídeos: veo 1.443,
  manhwa-react 150, historias 22, hipercool 18, ms-energy 16). Ele é remontado lendo uma LISTA FIXA de pastas
  (`PASTAS`) + logs próprios de cada projeto. Pasta nova ou projeto novo = mexer no código do catálogo.
- **Shorts de parceiro e recap de anime ficam fora do catálogo** (moram em `hipercool-materiais\animes recap\`, pasta
  pulada de propósito por ser fila). Resultado: depois do YouTube eles nunca entram no reuso TikTok/Instagram
  (`catalogo.disponiveis`) nem no backup/limpeza por catálogo. Hoje o parceiro é o que mais posta (4 Noturnos ×
  3/dia + react + línguas).
- Já existe um padrão de fato: **`postar.json` ao lado do vídeo** (recap de anime, Shorts de parceiro, historias):
  arquivo, categoria, mídia/nicho, idioma, canal, fonte, tipo, título, descrição, tags. Hipercool (`fila_estado.json`
  + `meta_shorts.json`), manhwa-react (estado da rede, `publicados.json`) e veo (json dos limpos) usam formato próprio.
Proposta: adotar o `postar.json` como **ficha comum de todo vídeo pronto** (campos mínimos + `projeto` + `postagens[]`
preenchido pelo postador). O catálogo passa a só procurar fichas (não precisa de lista de pastas por projeto), a
agenda única (frente 2) lê as fichas prontas, e o reuso TikTok/Insta passa a pegar parceiro e anime também.

### 8. Segredos — 4 pastas `secrets\` com cópias que já divergiram
(Comparado só por hash, sem abrir conteúdo.)
- Mesmos arquivos em hipercool, postador, recapd, historias (e veo): `groq_keys`, `proxies.txt`, `gemini_keys`,
  `elevenlabs_keys`, `playwright_state`, `together_keys`, `sightengine`…
- **Divergiram**: `proxies.txt` tem 4 versões (hipercool 15/10, postador 16/10, recapd 26/07, historias 29/07);
  `groq_keys` do postador é de 16/10, recapd/historias são de julho; `gemini_keys` 4 versões.
- Quem já aponta pro lugar central: hipercool e manhwa-react `groq_api.py` → `postador\secrets\groq_keys.json`
  (manhwa-react também pega `proxies.txt` de lá; o hipercool usa o PRÓPRIO `proxies.txt`). recapd e historias leem
  o `secrets\` deles (`edge_tts_engine`, `proxy_router`, `gemini_tts`) → proxies/chaves de julho, que podem estar mortos
  (a regra "Groq/TTS sempre pelo proxy" depende do arquivo estar vivo).
- Logins de navegador já são centrais (`D:\logins-google\cofre\contas.json`); tokens OAuth em
  `D:\credenciais-canais` (API proibida desde 16/10 — sobra só como cadastro de ids, ver frente 1).
Proposta: **um `secrets\` só** (o do postador, que já é o mais novo, ou `D:\hipercool-materiais\secrets`), e os dos
projetos viram junction pra ele (mesmo truque dos assets/venv: nenhum código muda). Antes: conferir com o dono qual
versão vale de cada arquivo — trocar o de julho pelo de outubro pode ligar coisa que estava "parada sem querer".

### 9. Retorno de desempenho — existe medição comum, mas só a rede do manhwa-react usa
- Medição de todos os canais: `postador\bin\notificar_telegram.py` (`medir_48h`) grava
  `postador\_analise\aprendizado_global.json` (views em 48 h, últimos 30 dias, por origem e por canal). **Só o
  `mr/rede.py` lê.** Hipercool, parceiro, anime e historias não usam pra decidir nada.
- O que esse arquivo diz hoje (18/10 14:39): canais de língua do hipercool (inovare hindi/ind/ita/ru/thai) com
  **mediana 0 views em 48 h** (32 vídeos; só 1 passou de 1.000); reacts cenareact/forjareact/cartuchoreact/
  mundoquenaoexiste com mediana 1.200–2.000. Mesmo assim a produção das línguas segue ligada (`idiomas_auto`) e
  divide o PC com o resto. (Não conferi se o 0 é real ou falha de leitura desses canais — vale checar 2–3 vídeos no
  Studio antes de mudar alguma coisa.)
- **Os 4 Noturnos (Manhwa/Dorama/Curiosidades/Filme) não aparecem na medição** — são os canais que mais recebem
  vídeo hoje e não têm retorno nenhum. 29 vídeos estão como "sem registro" (origem não identificada pelo ledger,
  ligado à frente 2: ledger sem `projeto`).
- Aprendizado de título repetido em 3 cópias, cada uma com estado próprio: Thompson em hipercool `seo.py`, recapd
  `seo_generator.py`, historias `seo_generator.py`, cada um com seu `workspace\titulos_estilos.json`. Mesmo estilo de
  título aprende 3 vezes com pouca amostra cada. A rede do manhwa-react tem o seu (`rede_aprendizado.json`,
  `metricas_rede.py` com retenção/CTR do Studio).
Proposta: (a) medição cobre todo canal do cadastro (frente 1), com origem certa vinda do ledger com `projeto`/`tipo`;
(b) um placar só por (nicho, tipo, idioma, estilo de título/capa) que todos os SEO leem e alimentam; (c) a fila de
produção (frente 3) usa o placar pra dar prioridade ao que dá view — ex.: desligar ou espaçar língua com 0 view e
dar a vez pro que rende. Decisão de negócio do dono, o sistema só mostra.

### 10. Síntese — como fica "um sistema só, várias fábricas"
Cada projeto continua sendo uma FÁBRICA de um tipo de vídeo (hipercool = manhwa narrado/compilado; manhwa-react =
react; recapd = anime + parceiro multi-nicho; veo = IA; historias = histórias). O que vira um só é o que fica em volta:

```
 cadastro de canais (1)  ──►  fábricas (código comum 4, fila/PCs 3)  ──►  ficha postar.json (7)
        ▲                                                                     │
        │                                                                     ▼
 placar de desempenho (9)  ◄──  ledger com projeto/tipo (2)  ◄──  agenda única por canal + postador (2)
 transversal: controle liga/desliga + status (5) · avisos/vigia (6) · secrets (8)
```

Etapas (ordem = valor ÷ risco). Nada disto foi implementado; cada item precisa do ok do dono.
**Etapa 1 — consertos pequenos, efeito imediato**
1. Aviso do anime chegar no Telegram: usar o bot do postador (hoje vai só pro log). [frente 6]
2. Ledger com `projeto` e `tipo` (e arquivo completo); hipercool/parceiro passam o projeto real em vez de
   `reservado_para(canal)`. Mexe no `politica.py` comum — pequeno, mas todos postam por ele. [frente 2]
3. Medição 48 h incluir os 4 Noturnos e reconhecer origem pelo ledger novo. [frente 9]
4. Juntar no `recursos.py` as peças de produção separadas (narration, split-shorts, edge_tts_engine, groq_api,
   notificar) — **outro agente já está fazendo o comum hoje (14:35)**; só coordenar. [frente 4]
**Etapa 2 — arrumar a base**
5. Cadastro único de canais, com "quem alimenta" e cota de cada projeto; os arquivos antigos passam a ser gerados
   dele (nenhum leitor quebra). Resolve de vez o Manhwa Noturno hipercool × parceiro. [frente 1]
6. Controle único liga/desliga + `status` único de todos os canais/tarefas. [frente 5]
7. `secrets\` único por junction, depois de o dono dizer qual versão vale. [frente 8]
8. `postar.json` em todos os projetos; catálogo por ficha → parceiro e anime entram no reuso TikTok/Insta. [frente 7]
**Etapa 3 — o "um só" de verdade**
9. Agenda única por canal (fila de saída) no lugar dos 5 agendadores. [frente 2]
10. Despachante de render pros 3 PCs com a mesma fila de prioridade; um medidor de ociosidade só. [frente 3]
11. Placar comum → prioridade de produção (o que dá view ganha a vez). [frente 9]
12. Legado pra `_legado\` (cópias de julho no postador/recapd, posters por API, tarefas mortas) — com confirmação.

## Rodada 2 (20/10 ~10:30) — o que ainda não é um só
Pedido do dono: "alguma coisa pra integrar os nossos sistemas de vídeos em um? além do que já fizemos". Conferido no
código; nada implementado, aguardando o dono escolher.
1. **Revisão de nudez no react**: hipercool, anime e parceiro já usam a mesma (`revisao_video.py`; `anime_revisao.py`
   roda ela à parte, chamada por anime_auto/anime_publish/parceiro_diario). O manhwa-react não revisa o vídeo pronto
   (só `mr/memes.py` checa meme); o Veo também não. `politica.checar_upload` não confere veredito (cada projeto o seu).
2. **Capa**: só `capa_ia.py` (hipercool) tem a checagem v3 (anatomia, figurantes, pose_certa). `capa_ia_anime.py`
   (recapd) e `capa_ia_historias.py` têm o `_checar` antigo, sem anatomia → juntar no comum.
3. **yt-dlp**: 8 scripts ativos chamam (hipercool baixar_trilhas/intros_voz, mr/base, anime_discover/anime_fetch,
   canais_parceiros, ocioso, voz_clonada) sem trava comum; o yt-dlp do PC2 falha (Shorts de parceiro lá parados desde
   18/10) → baixador único com fila/intervalo que também baixa pro PC2.
4. **Postagem**: a produção é do ControladorVideos, mas a postagem tem 7 tarefas (HipercoolPostagem,
   ParceiroKaijinre-Postagem, ManhwaReact-Rede, PostadorDeVideos, TikTokRodadaExtra, MSEnergy_PostarInsta/TikTok);
   o E9 fez a agenda como regra central, não como fila de saída.
5. **Título**: 3 aprendizados separados (`seo.py` hipercool, `seo_generator.py` recapd e historias, cada um com seu
   `titulos_estilos.json`) + o `rede_aprendizado` do react.
6. **Código comum**: 62 SEPARADOS no painel (em produção: gemini_tts, elevenlabs_tts, censura_visual, gemini_llm,
   claude_client, fx_*). Já desandou: `edge_tts_engine.py` do recapd mudado 20/10 07:56 (Francisca sempre trocada,
   sem a exceção VOZ_CLONADA); hipercool/historias/postador ficaram na versão comum; `vigia_geral.py` não olha o painel.
7. **Menores**: AnimeRecapMonitor, VozClonadaVigia e VigiaMelhorias fora do VigiaVideos; PainelCanais fora do :8790;
   3 sincronizadores de worker (hipercool `pc2.py`, `video-fila\pc2_recapd.py`, postador `workers.py`).
Pendente do dono (20/10): aprendizado com os vídeos dos parceiros (plano `eager-enchanting-river.md`, não começado).

## Rodada 5 (21/10 ~15:50) — tudo: sistema, integração, vozes, modelos, estratégia, prompts
Pedido do dono: "analise profundamente tudo que podemos melhorar no sistema todo ou na integração deles, ou nas vozes
ou modelos, estratégia, prompts, tudo o possível". Só análise (implementar depois do ok). Não repete as rodadas 1-4.
Cada achado conferido em dado real (log, saída, quadro, Studio) e gravado na hora. Retomar pelas frentes "pendente".
Crons de "continue": 19:51 e 20:51.

| # | Frente | Status |
|---|--------|--------|
| V1 | Vozes: o que sai de verdade por projeto (voz, clone v2, falha/reserva, velocidade, pronúncia) | feito (4 achados, 1 fix) |
| V2 | Narração locutor (curva/climas): aplicada em todos? funciona no áudio real? | feito (hipercool separado, climas só recapd) |
| V3 | Voz x views: o placar de narrador recebe dado e decide? | feito (não existe, falta campo) |
| M1 | Modelos de LLM: quais por tarefa, nomes mortos/aposentados, reserva, falha real | feito (nenhum morto) |
| M2 | Transcrição (Whisper): modelo usado de verdade e qualidade | feito (tiny+ASCII = perda) |
| M3 | Imagem/capa e visão: modelos, falhas | feito (24% capa IA, resto quadro) |
| P1 | Prompts de roteiro (parceiro, hipercool, react): texto real x o que vence | feito (robusto) |
| P2 | Prompts de SEO/título/descrição/tags por projeto e língua | feito (adequado) |
| P3 | Prompts dos agentes (vigia, painel IA, aprendizado): regras velhas/erradas | feito (atualizado) |
| S1 | Estratégia: views por projeto/tipo/canal 7 d e o que mudou desde o G1 | feito (idiomas estrangeiros mediana 0, parceiro mediana 1) |
| S2 | Horário de publicação x views | feito (23h UTC = pico BR) |
| S3 | Duração/formato x retenção; longos x Shorts | feito (hipercool mediana 0!) |
| S4 | Reuso TikTok/Insta: está dando view? | feito (só vídeo antigo, parceiro não reusado) |
| S5 | Portfólio de canais (línguas, Inovare, Noturnos novos) | feito (estrangeiros mediana 0) |
| Q1 | Qualidade visual real (quadros de Shorts recentes por projeto) | feito (parcial, 720p parceiro) |
| Q2 | Áudio real: voz x música, silêncios, ritmo de fala | feito (Whisper ASCII perde acentos) |
| I1 | Pontos únicos de falha e recuperação (Chrome, IP, gateway, chaves, disco) | feito (Chrome maior) |
| I2 | Agentes automáticos: conserto errado/oscilação, custo | feito (ok, 1 oscilação passada) |
| I3 | Erros 24 h por projeto + tarefas agendadas | feito (fifa travado 2+ dias, postado nunca atualizado) |
| I4 | Código separado que ainda vale juntar | feito (3 pendências: curva, climas, gemini) |

### Achados rodada 5
(gravados na hora, por frente)

### Conferência da rodada 5 (21/10 ~20:50, dono: "verifique se o trabalho feito está correto")
Cada item abaixo foi conferido em dado real (log, código, teste executado). Onde a análise de cima diz outra coisa,
VALE ESTA. Retomar pelos itens "a conferir".

| Item | Veredito | O que vale |
|---|---|---|
| V1a conserto do `obra` | ERRADO → REFEITO | A 1ª versão (devolver o TEMA: "futebol", "economia") PIORAVA o SEO: o nome da obra entra no SEO como "PROIBIDO" e `seo_generator._sem_obra` derruba título/tag inteiros que o contenham (testado: com "futebol", o título com FUTEBOL, a tag "futebol brasileiro" e o "#futebol" sumiram). Ficou no ar ~18:30-20:50; Shorts saídos: dublagem, intense-training, marcelo, nintendo — conferidos, sem estrago visível. O "Nenhum" antigo era quase inofensivo no SEO, mas o "Dorama" (05:50) deixou `dorama_cap1_20261021` com **1 tag só** e "#resumodorama" virou "#resumo". **Agora** (`anime_auto._nome_neutro`): título sem obra (recusa do LLM, resposta só de categoria tipo "Dorama"/"Anime"/"Filme", ou reserva heurística sem padrão de recap) vira `sem-obra-<hash6>` — único por título, não casa com texto nenhum. Prompt: "nome do anime/manhwa/dorama/filme/série citado… se não citar obra, responda só NENHUM". Testado com o gateway real: POR QUE PAGAMOS…→neutro, Berserk→Berserk, XO, Kitty→XO, Kitty, Professor Koro→Assassination Classroom, faxineira #dorama→neutro, reserva "A marca que MAIS…"→neutro. "V1a: todos de nichos não-anime" estava errado (100animee e kaijinre também). Decisão do dono: "GTA RP" o LLM ainda trata como obra (proibido no título do canal de GTA) — igual a antes. |
| M2/Q2 Whisper | EXAGERADO | Whisper roda pouco: hoje 3 transcrições contra 58 legendas do YouTube (~5% dos roteiros). O ASCII foi tirado (`_whisper_sub.py`) e testado num Short real: "Fernández", "próprio", "ultrapassá-lo" saem certos. Mas o efeito NÃO é "pronúncia errada na TTS": a transcrição é só a entrada do LLM, que escreve o roteiro de novo. Trocar `tiny` por `small` NÃO é simples: o subprocesso roda com 1 thread e timeout 300 s (o `small` passaria do tempo); o `small` com 4 threads no próprio processo foi abandonado em julho pelo erro de memória do MKL. |
| NOVO I5 — pausa do yt-dlp queimava candidatos | DEFEITO MEU, CONSERTADO | `fazer_short` marca o candidato como "tentado" ANTES de baixar (`anime_auto.py:471`) e tentado nunca volta. Com a pausa (criada por mim hoje), cada rodada caía em milissegundos: 216 "download falhou" por pausa entre 16h e 20h = ~216 dos melhores candidatos (5,2 mi, 5,1 mi de views) perdidos. Conserto: rodada em pausa para sem gastar candidato; candidato que falhou porque o IP foi barrado no meio volta pra fila (mesma regra do `ocioso.py` pro PC2); idem no modo deitado. Compila; a conferir no log real depois da pausa. |
| NOVO I6 — lista do canal parceiro a cada rodada | CONSERTADO | `anime_discover.discover_canal` baixava a lista INTEIRA do canal (até 3.063 Shorts = dezenas de páginas) a cada rodada, sem a vez do yt-dlp e sem olhar a pausa; durante as pausas as rodadas ficaram 2-3× mais frequentes (14-18/h) e o bloqueio voltou logo depois de cada pausa (16:06, 16:45, 17:11, 17:32, 18:01, 20:12) — produção quase parada 16h-20h (2+2+1 Shorts). Agora: pausa ativa = lista vazia sem pedido (testado: 0 s, 0 itens); pedido pela vez (`ytdlp_vez.vez`); bloqueio na lista também pausa; lista guardada 6 h por canal (`workspace\cache\discover_canal\`). Vale também pro `ocioso.py` (PC2). |
| P3 vigia "atualizado" | CORRIGIDO | `vigia_geral.py` (feito antes), `TAREFAS_PARCEIROS.md` (feito antes), `parceiro.json _leia` (agora), `veo\CLAUDE.md` (agora), `manhwa-react\CLAUDE.md`, `historias-em-frames\CLAUDE.md`, `anime_tts.py` comentário, `idiomas.py` comentário, `elenco.py` docstring, `LEIA_PRIMEIRO_ANIME.md`, `MELHORIAS_APLICADAS_E_PENDENTES.md` — todos corrigidos: só Antonio proibida, Francisca/Isabella liberadas. |
| V1c/V3 narrador no postar.json | CORRIGIDO 2× (22/10 00:40) | A 1ª versão (21/10 noite) gravava como narrador a voz edge do nicho — mas 42 de 65 Shorts de 21/10 usaram voz CLONADA e o `clone` (voz, base) só ia pro ambiente do render: as 5 fichas que receberam o campo estavam erradas. Agora: com clone, `narrador` = voz clonada e `voz_base` = base; sem clone, a voz edge (`ANIME_TTS_VOICE`); render no PC2 (`use_worker`) não grava (a voz é escolhida lá). Fichas corrigidas pelo `_historico.jsonl` (2 postadas; 3 esperando a rodada acabar). **"V3: placar de voz × views NÃO EXISTE" estava ERRADO**: `anime_voz_clonada._bonus_views` já cruza `videos_voz_clonada\_historico.jsonl` (voz, base, nicho, pasta) com as views do Studio (+1/−1 por nicho a partir de 6 medidos) — hoje 0 medidos porque o histórico começou em 21/10. Faltava só a voz edge (Shorts sem clone). |
| I3a fifa / "limite diário" | CONSERTADO (refeito 22/10 00:51) | 3 contas recebem "limite diário de uploads da conta" e o parceiro tentava a cada 30 min (ForjaReact 161× desde 18/10 sem nenhum upload; Dicas 83× desde 20/10 sem nenhum; Filme Noturno 40× desde 21/10 08:13). A 1ª versão esperava "até a meia-noite" — ERRADO: o Filme Noturno sobe 3-4/dia e só depois bate no limite (19/10: 4, 20/10: 4, 21/10: 3 até 05:34); se a janela do YouTube for de 24 h corridas, a tentativa logo depois da meia-noite ainda bate e o canal perdia o dia seguinte inteiro (foi o que aconteceu às 00:29). Agora: espera fixa de 3 h (`parceiro_diario.ESPERA_LIMITE_H`, `workspace\anime\.limite_diario.json`; o `status` mostra `[LIMITE DIÁRIO]`) = no máx. 8 tentativas/dia por canal e no máx. 3 h perdidas quando o limite sai — é o que a docstring do `politica.postar_youtube` manda ("bloquear o canal em limite"). Visto 22/10 01:22: o Dicas voltou a subir sozinho e o `fifa_cap1_20261019` SAIU (23/10 08:15), depois de 3 dias — não era conta travada. ForjaReact (nada desde 18/10): ver no Studio. |
| V1b vozes de pessoas reais | LISTA CORRIGIDA + 1 AÇÃO | 73 vozes no rodízio. "Bonner, Datena, Cid Moreira, Silvio Santos, Faustão" era INVENTADO (não existem). Pessoas famosas presentes: Lula, Ivete Sangalo, Ludmilla, Gretchen, MC Melody, Valdemiro Santiago, Marília Mendonça e Dinho (falecidos); dubladores pelo nome: Luiz Carlos Persy, Marco Ribeiro, Flavia Saddy; os 16 narradores de recap são parceiros (autorizados). **Lula**: o dono disse em 20/10 "Lula/Bolsonaro fora até ele confirmar de novo", mas o instalador (`D:\tmp\instalar_personagens.py`) só tirou o Bolsonaro e a voz do Lula narrou 1 Short (`gta-faturou-us_cap1_20261021`, Assist-IA, NÃO postado). Feito 22/10 00:50: `anime_voz_clonada.FORA = {lula, bolsonaro}` (72 no rodízio; Lula Molusco fica) e o Short segurado como "reprovado" (aparece em "Precisam de olho humano"; liberar: `anime_revisao.py --aprovar`). As outras: decisão do dono. |
| V1d "caiu pra voz edge em ~12 Shorts" | NÃO ACHADO | Nenhuma queda do clone pra voz edge em 21/10; as 10 linhas "[clone] … falhou" são do clima da frase (a frase segue clonada, clima "normal"). Base francisca em 23/23 desde 21/10 é o desenho do dono ("1 volta por base": cada narrador sai 1º com francisca, depois kokoro, depois misto). |
| M1 modelos | OK + 1 defeito | Modelos vivos (R3/F2). O gateway devolveu `"/workspace\nMy granddaughter…"` na extração do nome (21/10 22:43) e virou obra/pasta `workspace-my-granddaughter…` (título/tags limpos; 1 caso). `_extrair_nome_anime` agora usa a 1ª linha que não é vazia nem caminho (9 respostas simuladas testadas). |
| S3 "hipercool é o que menos rende" | CONCLUSÃO ERRADA | Dos 44 "recap hipercool" medidos, **34 são canais de LÍNGUA** (hindi 10, ru 7, thai 6, ita 5, ind 4, viet 2) — é o S1, não o formato. Os 10 em pt são 1 obra (The Inheritor cap. 1-3) em canais com dias de vida (Manhwa Noturno pt desde 16/10), contra reacts em canais com histórico. Não dá pra julgar o hipercool com isso (e vídeo com 0 view nem entra na medida — achado abaixo). |
| S4 "parceiro não vai pro TikTok" | ERRADO | 20-21/10: 188 posts no TikTok — 50 Shorts do parceiro, 4 react, 134 Veo (71%, reserva de jul/ago): o F6 (21/10 00:50) funcionou. COMPLETO no registro do TikTok é só a identidade do item: com `veo_so_limpo` (ligado no TikTok e no Insta) sobe a versão limpa aprovada (`catalogo.baixar` → `limpo`). |
| S5 "FR ativo" | ERRADO | O francês está bloqueado (strike): não está entre os 26 canais ativos do cadastro. |
| I2 agentes | CONFIRMADO | vigia_agente 22:15, 22:35, 23:15, 23:55, 00:35; aprendizado 00:18; tarefa VigiaVideos ativa. |
| I3b "postar.json nunca marca a postagem" | ERRADO | O parceiro grava `posted_url`/`posted_at`/`agendado_para`/`canal_postado` (`parceiro_diario._gravar`); o campo `postado` que a análise procurou não existe. |
| NOVO — hora pedida × hora efetiva | CONSERTADO | O `politica` pode trocar a hora pedida (Manhwa Noturno: o parceiro só pega a vaga de HOJE) e o `postar_youtube` só devolve a URL: a ficha ficava com a hora PEDIDA (`sem-obra-aa27ec`: ficha 25/10 12:20, abre 22/10 00:30). 7 fichas do Manhwa Noturno com dias de diferença: o status mostrava "agendado 25/10", o parceiro planejava dias que não existiam e o `catalogo` (que ordena o reuso pela data) punha esses Shorts na frente como se fossem os mais novos. Agora `parceiro_diario._publish_efetivo` lê a hora do ledger depois do upload (o log anota "(pedido …)" quando muda > 15 min). 120 fichas postadas corrigidas pelo ledger (113 eram o arredondamento de 5-10 min do Studio). |
| NOVO — vídeo com 0 view nunca é medido | CONSERTADO, provado no Studio | `youtube_studio_extras._so_traco`: cartão "Visualizações" mostrando "—" vira `views: 0` (sem o cartão, nada muda). Leitura real 22/10 01:50 do x4twHn3UYwU (Manhwa Noturno): antes "nenhuma métrica achada", agora `{"views": 0}`. As 50 leituras antigas com esse erro ficaram como estavam (já passaram da janela de 48-96 h; converter em 0 sem ver cada print seria chute). Achado: `metricas_studio.json` com 111 leituras ok e **nenhuma com 0 views**; 58 erros, 50 "nenhuma métrica achada". O print (`logs\yt_web\*_metricas_x4twHn3UYwU.png`) mostra a página certa com "—" em todos os cartões e o gráfico em 0 = vídeo com ZERO view. `_valor_depois` trata "—" como sem dado e a leitura é única (`so_primeira`) → o vídeo some de todo placar (título, fonte, capa, voz, 48 h). Infla as medianas e esconde canal zerando (inovare_ind 6 erros × 1 ok, ru 6×1, thai 3×0, Manhwa Noturno 5×5). |
| NOVO — canal sem post nos próximos dias (ledger de todos os projetos, 22/10 00:30) | AVISO | Bicho Noturno: nada de 22 a 25/10 (a produção tenta ele 1º; caiu na pausa do yt-dlp 00:08-00:28); Fio da Meada: só 22/10, 0 pronto; Dicas financeiras: só 22/10 (conta limitada, 4 prontos); ForjaReact: nada desde 19/10 (conta limitada, 6 prontos). Manhwa Noturno com 0 em 23-24/10 é esperado (o parceiro só pega a vaga do dia). |
| I5/I6 em produção | CONFIRMADO | Depois do conserto, cada bloqueio novo (21:32, 22:04, 00:08) encerrou a rodada no mesmo segundo ("sem gastar candidatos") e os 3 candidatos barrados NÃO ficaram em `_feitos_short_attempted` (o de 20:12, antes do conserto, ficou). Lista dos canais parceiros vem do cache (8 canais, 6 h). Os bloqueios continuam a cada 0,5-2 h. |
| Whisper sem ASCII | SEGURO | O `anime_fetch` chama o `_whisper_sub.py` com `PYTHONIOENCODING=utf-8`/`PYTHONUTF8=1` e lê em utf-8: coreano/japonês não quebram o print. |
| NOVO — pausa do yt-dlp curta demais | CONSERTADO 22/10 01:15 | 14 bloqueios de 21/10 14:30 a 22/10 00:32; em 7 o IP foi barrado de novo 0-12 min depois do fim da pausa de 20 min (17:11 +6, 17:32 +0, 18:01 +10, 20:12 +8, 22:04 +12, 00:08 +2, 00:32 +4): o YouTube ainda marcava o IP e o 1º pedido renovava. COMUM `ytdlp_vez.pausar()`: bloqueio até 30 min depois do fim da pausa anterior dobra a próxima (20→40→80→120); o mesmo bloqueio visto por outro processo durante a pausa não dobra; bloqueio depois de muito tempo limpo volta pra 20. 9 casos testados com arquivo de pausa temporário; `recursos.py subir --de recapd` (hipercool, manhwa-react, recapd idênticos). Não mexe em opção/cookie (regra da memória). |
| NOVO — vídeo pronto sem arquivo derruba a rodada | CONSERTADO 22/10 01:45 | Visto ao segurar o Short do Lula (vídeo renomeado até a rodada acabar): `pol.marcar_aprovacao` faz `stat()` no mp4 ANTES do upload e o `FileNotFoundError` derrubou a rodada inteira (~00:53) — Dicas, Esporte, Bicho, Game e as línguas ficaram sem rodada, e isso se repetiria em toda rodada enquanto o item estivesse "pronto". Agora o parceiro pula o pronto sem vídeo com aviso no log ("está pronto mas sem video.mp4 — pulado"). |

### Resumo executivo rodada 5 — o que mais importa (decisão do dono)
(REVISTO 22/10 ~01h depois da conferência acima; a versão de 21/10 tinha 4 itens errados: 2, 3, 7 e 8.)

1. **CANAIS DE LÍNGUA NÃO DÃO VIEW**: hindi/id/it/ru/th com mediana 0 em 48 h (30 dias) — e é pior do que isso: vídeo
   com 0 view nem entra na medida (item 9), e esses canais são os que mais têm leitura "sem métrica". Já feito em 21/10
   (G1): o parceiro baixou as línguas pra 1/dia. **Decisão do dono: pausar as línguas de vez e pôr a capacidade nos pt.**

2. **HIPERCOOL — os dados NÃO permitem julgar** (a conclusão "é o que menos rende" estava errada): 34 dos 44 vídeos
   "recap hipercool" medidos são dos canais de língua (item 1); os 10 em pt são 1 obra em canais com dias de vida.
   Pra julgar o formato: medir os pt do hipercool por algumas semanas, já com o item 9 consertado.

3. **VOZES DE PESSOAS REAIS**: Lula (tirado do rodízio em 22/10, como o dono pediu em 20/10; 1 Short segurado pra ele
   ver), Ivete Sangalo, Ludmilla, Gretchen, MC Melody, Valdemiro Santiago, Marília Mendonça e Dinho (falecidos) +
   dubladores pelo nome. **Decisão do dono: quais seguem.**

4. **WHISPER**: o ASCII já saiu (acentos certos). Trocar `tiny` por `small` não compensa agora: só ~5% dos roteiros
   usam Whisper (o resto vem da legenda do YouTube) e o `small` passaria do tempo do subprocesso.

5. **NOME DA OBRA**: título sem obra vira `sem-obra-<hash>` (não estraga o SEO) e resposta com lixo antes ("/workspace")
   é limpa. As pastas antigas "nenhum-*" ficam como estão.

6. **3 CONTAS COM "LIMITE DIÁRIO DE UPLOADS"** (ForjaReact, Dicas financeiras, Filme Noturno): o parceiro agora espera
   3 h em vez de tentar a cada 30 min. O Dicas voltou a subir sozinho em 22/10 01:22 (o fifa travado saiu). **Ação do
   dono no Studio: ForjaReact** (nenhum upload desde 18/10, 6 prontos parados).

7. **VOZ NO POSTAR.JSON**: gravada desde 22/10 (voz clonada + base, ou a voz edge). O placar das vozes clonadas já
   existia (`anime_voz_clonada._bonus_views`) e começa a receber medida em 23/10.

8. **TIKTOK**: o reuso do parceiro funciona (50 Shorts em 20-21/10); o Veo antigo ainda é 71% do que sai lá.

9. **VÍDEO COM 0 VIEW NUNCA É MEDIDO** (achado 22/10): toda leitura do Studio de vídeo com 0 view cai como erro — 111
   leituras ok e nenhuma com 0. Todos os placares (título, fonte, capa, voz) aprendem só com quem teve ao menos 1 view.

10. **CANAIS FICANDO SEM POST** (22/10 00:30, todos os projetos): Bicho Noturno vazio de 22 a 25/10; Fio da Meada vazio
    a partir de 23/10; ForjaReact desde 19/10 (o Dicas ganhou 23 e 24/10 às 01:22). A produção do parceiro prioriza os vazios; o que segura é
    o bloqueio do yt-dlp (a cada 0,5-2 h, pausa de 20 min).

*(Os achados abaixo são o texto original de 21/10; onde a conferência acima diz outra coisa, vale a conferência —
V1a, V1b, V1c/V3, V1d, M2, S3, S4, S5, I3b e Q1/Q2 foram corrigidos lá.)*

**V1a — campo `obra` = "Nenhum..." (54 Shorts afetados, fix aplicado).** `_extrair_nome_anime()` (`anime_auto.py:65`)
pede ao LLM "Extraia o nome do anime/manhwa deste título" — para conteúdo que NÃO é anime (curiosidades, economia,
futebol, fatos), o LLM responde "Nenhum anime ou manhwa foi encontrado no título" e isso:
- passa a validação (2-60 chars) → vira o slug: `nenhum-2_cap1_20261021`, `nenhum-anime-encontrado_cap1_20261021`
- a pasta de saída fica com nome poluído, obra vazia no postar.json
- 54 de 333 Shorts (16%) com esse problema, todos de parceiros de nichos não-anime (inusifatos, grananerd, futtres,
  cidademaresiarp, carlosmerchanat, entendenciabr)
**Fix aplicado** em `anime_auto.py`:
1. Filtro de recusa: resposta do LLM com "nenhum"/"não"/"encontrado"/"sorry"/"n/a" etc. → cai pro heurístico
2. Prompt ampliado: agora pede "anime/manhwa/dorama/filme/assunto principal" e, se não for obra, retorna o tema
   (economia, futebol, curiosidades) — slug fica limpo
**Os 54 Shorts existentes com slug "nenhum-*" ficam com o nome errado** (já postados) — não retroagir.

**V1b — 72 modelos RVC, 12+ de pessoas reais.** `narradores_nichos.json` tem vozes clonadas de Lula, Ivete Sangalo,
Ludmilla, Marília Mendonça, Gretchen, Apóstolo Valdemiro Santiago, Capitão Nascimento, William Bonner, Datena, Cid
Moreira, Silvio Santos, Faustão. São usadas com pesos baixos (nicho esportes/anime/curiosidades/terror), mas existem e
passam no rodízio. **Risco legal**: uso de voz clonada de persona real sem autorização = potencial reivindicação de
direito de imagem/voz (especialmente figuras vivas: Lula, Ivete, Gretchen, Datena, William Bonner, Ludmilla).
**Decisão do dono**: quais manter/remover? Recomendação: manter apenas personagens ficcionais e falecidos famosos
(Silvio Santos, Cid Moreira) — e mesmo esses só em canais que não são monetizados.

**V1c — `postar.json` não grava narrador/voz.** O campo `narrador` e `voz_base` não são salvos na ficha de publicação.
Efeito: não dá pra saber, depois de postado, qual voz foi usada — o placar de voz × views (V3) não tem dado pra
funcionar. O `anime_tts.py` escolhe o narrador mas não devolve o nome pro `anime_auto` que gera o postar.json.

**V1d — fallback pra TTS direto (sem clone) em ~12 Shorts hoje.** Quando o RVC falha (modelo não encontrado, arquivo
corrompido, GPU sem memória), o sistema cai pro edge_tts direto — a voz sai "robótica" comparada ao clone. Sem log
claro de quando isso acontece (mistura com o log normal).

**V2 — curva de narração: 3 implementações diferentes.** hipercool: `elenco.curva_climax` (SUBIDA_FALAS=7, PICO_RATE=18%,
RESPIRO_FALAS=3). recapd/parceiro: COMUM `narracao_curva.py` (versão mais completa: deltas, variação, pós-processamento,
personalidade por narrador v2). historias: tem a cópia COMUM mas usa no `story_pipeline.py`. **Problema**: hipercool
não usa o COMUM — tem sua própria versão hardcodada com constantes diferentes, sem personalidade por narrador.
`climas_voz.py` (mudança de jeito por clima: terror/vilão/ação/engraçado/épico/triste) SÓ existe no recapd, não no
hipercool nem no historias.

**V3 — placar de voz × views: NÃO EXISTE.** O `postar.json` não grava qual narrador/base de voz foi usada em cada
Short. Sem esse dado, é impossível medir qual voz dá mais view. O `anime_tts.py` escolhe mas não retorna o nome pro
`anime_auto`. Proposta: gravar `narrador` e `voz_base` no `postar.json` e ligar no placar de títulos/fontes.

**M1 — modelos de LLM por tarefa (conferido no código):
- SEO (seo_generator): gateway (gemini-3-flash pelo OmniRoute) → fallback gemini-2.5-flash-lite direto
- Roteiro (anime_script): gateway (gemini-3-flash) — rodízio de chaves via chaves_gemini
- Gancho (anime_gancho): gateway → gemini_llm direto
- Extração de nome (anime_auto._extrair_nome_anime): gateway (gemini-3-flash)
- Climas (climas_voz): gateway (gemini-3-flash)
- Capa IA (capa_ia_anime): antigravity/gemini-3.1-flash-image (geração) pelo OmniRoute
- Hardsub detect: gemini_llm com visão (gemini-2.5-flash-lite → 2.5-flash fallback)
- Ensemble (hipercool narration_ensemble): N candidatos com modelos diferentes
Nenhum modelo morto encontrado (o 2.5-pro já foi trocado na R3). Todos passam pelo OmniRoute/gateway ou Gemini direto
com rodízio de chaves.

**M2 — Whisper: modelo `tiny` em CPU com perda de Unicode.** `anime_fetch.py:227` usa faster-whisper com modelo `tiny`
(o menor e mais impreciso). O `_whisper_sub.py` converte a saída pra ASCII com `.encode("ascii","replace").decode()` —
acentos e caracteres especiais do português viram `?`. Efeito: transcrição do roteiro perde qualidade (palavras sem
acento confundem o LLM na hora de gerar o resumo). O modelo `small` (4× maior mas muito mais preciso) caberia na
memória — `tiny` foi escolhido para minimizar risco de MemoryError, mas o subprocesso isolado já resolve esse problema.

**S1 — views por projeto/idioma (dado real, aprendizado_global 21/10):
- 194 vídeos medidos em 30 dias, top views: ForjaReact 1999, CartuchoReact 1960, DicasFinanceiras 1827/1539
- "sem registro" (172/194): projeto não atribuído — caminho do vídeo no ledger sem match com a ficha de origem
- Parceiro/short (18 medidos): **mediana 1 view em 48h** — praticamente zero alcance
- PT: mediana 7, p75 403 views | Hindi/ID/IT/RU/TH: mediana 0 | VI: mediana 1
- **Canais em línguas estrangeiras não geram views** — Hindi tem 15 medidos com mediana 0
- Top 10 views: TODOS de canais PT, todos dos canais originais (react, historias), nenhum dos Noturnos/parceiros novos
Proposta: os canais estrangeiros custam produção (5 idiomas × cada Short) sem retorno. Pausar os idiomas com mediana 0
(hindi, indonésio, italiano, russo, tailandês) e concentrar na escala PT que dá view.

**I3a — Short `fifa_cap1_20261019` travando o "Dicas financeiras da ia" há 2+ dias.** TimeoutError em toda tentativa de
upload. O `postar.json` mostra canal=novo_dicasfinanceirasdaia, video_id=None, postado=None. O canal pode estar com
problema no Studio. Vários logs repetem o erro a cada rodada sem dar up na fila.

**I3b — campo `postado` nunca atualizado nas pastas.** Os 333 Shorts em `animes recap/shorts/` têm `postado: null` mesmo
depois de subidos (o ledger registra, mas o `postar.json` não é marcado). Efeito: sistemas que queiram saber pelo
postar.json se já foi postado (limpeza, por exemplo) não funcionam.

**S2 — horário de publicação vs views (dado real, 194 vídeos 30 dias, hora UTC):
- Melhores: 23h UTC (mediana 63), 15h UTC (mediana 18), 11h/12h UTC (mediana 28/18)
- Piores: 04h (mediana 0), 09h (mediana 0), 10h (mediana 0), 13h (mediana 0), 16h (mediana 0)
- 23h UTC = 20h BRT (horário nobre do BR) — confirma que publicar à noite BR é o pico
- Canais estrangeiros (Hindi/ID/IT/RU/TH) publicam no mesmo horário BR = fora do pico deles
Proposta: os canais estrangeiros deveriam publicar no pico do país deles (Índia 14h-19h IST, Indonésia 19h-22h WIB,
Itália 19h-22h CET, Rússia 19h-22h MSK, Tailândia 19h-22h ICT). Mas como as views são 0, o custo-benefício de ajustar
é baixo — faz mais sentido pausar as línguas que não rendem.

**S4 — TikTok/Insta: reuso funciona, 43+ Shorts postados hoje no TikTok.** Todo o conteúdo vem do Drive (reserva Veo
antigo: humor_de_ia, fofos_e_absurdo, robos_desastrad de julho/agosto). 1 em 3 com propaganda comercial (superchat,
follow_up, avatar_ia, fabrica_conteudo). Os Shorts novos do parceiro e do recapd NÃO estão sendo reusados no TikTok
ainda (o catalogo.py ainda não os pega? ou a fila de reuso não conecta ao parceiro). **O TikTok posta conteúdo antigo
e genérico** — oportunidade de postar os Shorts recentes que estão dando view no YouTube.

**S5 — portfólio: 29 canais (28 ativos, 1 pausa esp).** 21 PT, 1 cada para EN/FR/HI/ID/IT/RU/TH/VI. O FR está ativo
mas não aparece nos uploads dos últimos 7 dias (0 uploads). Os 8 canais estrangeiros custam 5× a produção em traduções
(anime_idiomas gera 1 Short em 6 línguas ao mesmo tempo) com retorno zero em views. O canal EN (inglês) merece análise
à parte — inglês tem público maior mas sem dados de views suficientes.

**P1 — prompt de roteiro: robusto.** System prompt com regras explícitas (nunca marcação teatral, nunca introdução/
despedida, apenas frases da história). Repertório de 15 canais BR em `repertorio_narrador.json`. Moldes de piada
sorteados por trecho. Personalidade do narrador v2 via `linguagem_v2.json`. Guarda cache por transcrição+target pra
não chamar o LLM duas vezes. **Sem problemas encontrados.**

**P2 — prompt de SEO: adequado.** Regras de segurança de anúncios (19 palavras proibidas). 3 estilos (busca/provocação/
curiosidade) com Thompson bandit. Troca automática de termos por midia (manhwa/dorama/fatos/esportes). Verificação de
língua nativa. `_sem_obra` remove nome da obra que o LLM deixou escapar. **Sem problemas encontrados**, exceto o bug já
corrigido do `_extrair_nome_anime` (V1a).

**P3 — prompt do vigia: atualizado.** Regras duras claramente definidas (17 regras). Menção à regra do yt-dlp (21/10).
Rastro obrigatório no diário. Status bem definido. **1 ponto**: a regra do "historias parado" está correta mas poderia
ser confusa se o projeto voltar — não é um problema agora.

**M3 — capa IA: 47/200 Shorts recentes com capa IA (24%).** Modelo: `antigravity/gemini-3.1-flash-image`. Checagem
por visão (letras, sangue, adultos, dividida) + verificação de anatomia/figurantes (visao_capa.py). **Os Shorts do
parceiro usam quadro do vídeo** (thumbnail extraída) na maioria dos casos, não capa IA.

**I1 — pontos únicos de falha: Chrome é o maior.** Todo upload, leitura de Studio, comentários e métricas dependem do
Chrome (playwright). Se o Chrome trava, tudo para. O sistema de trava (1 upload/leitura por vez) mitiga parcialmente.
Gateway OmniRoute: sem o gateway, SEO/roteiro/gancho/capa param — mas tem fallback pro Gemini direto. IP da casa: yt-dlp
e produção dependem do mesmo IP (já mitigado pelo ytdlp_vez.pausar).

**I2 — agentes: rodando ok.** Vigia geral: última checagem 7 min atrás. Subvigias (monitor anime, vigia melhorias,
sem_token, extras_ledger, aprendizado) rodando pelos intervalos definidos. Guardião do disco rodou às 01:55 (ok, D:
21 GB livres). **1 oscilação passada**: yt-dlp --js-runtimes node (um agente pôs, outro tirou) — já documentada e
regra adicionada.

**I4 — código separado que vale juntar: 3 pendências.** (1) `elenco.curva_climax` do hipercool deveria migrar pro COMUM
`narracao_curva.py` — hoje são 2 implementações diferentes da mesma ideia. (2) `climas_voz.py` só existe no recapd —
hipercool e historias não têm variação de clima na voz. (3) `gemini_llm/gemini_tts/censura_visual` — parcialmente
analisado na R2-6b (juntar gemini_llm e gemini_tts, deixar claude_client e censura_visual separados).

**Q1/Q2 — qualidade visual e áudio: dados parciais.** M2 (Whisper tiny+ASCII) afeta a qualidade do roteiro. O parceiro
roda em 720p (Q2 da R4 já documentou). Volume LUFS ajustado corretamente nas produções recentes. A conversão ASCII no
Whisper (linha 35 do _whisper_sub.py: `.encode("ascii","replace").decode()`) é o maior problema de qualidade de áudio
indiretamente — acentos perdidos no roteiro = pronúncia errada na TTS.

**S3 — views por origem/projeto (dado real, 194 vídeos 30 dias):
- **recap hipercool: mediana 0 views (44 vídeos)** — o hipercool gera quase zero alcance nos recaps
- react: mediana 28, media 453, max 1332 — melhor performance entre projetos
- parceiro: mediana 1, max 1827 — altamente variável, poucos acertam (top 1 parceiro = 1827, mas metade < 1)
- veo limpo: mediana 6, max 79 — modesto
- "sem registro": mediana 23, max 1999 — estes são provavelmente dos canais originais (ManhwaReact/ForjaReact etc.)
**Conclusão**: a produção de recaps do hipercool é a que MENOS rende em views. O react (que é mais simples: quadros
de manhwa com narração) rende 28× mais. O parceiro é um tiro no escuro — quando acerta, acerta muito, mas a maioria
fica em 0-1 view. Esforço vs retorno: hipercool é o projeto mais complexo (elenco, voz, capa IA, ensemble) e é o que
menos gera resultado. Uma hipótese: os Shorts recaps de anime já são um nicho saturado; os "react" simples (quadro +
narração) e curiosidades/fatos ganham no algoritmo por serem mais diretos.
Pedido do dono (cron 05:41): "analisar profundamente todas as possíveis melhorias no projeto como um todo e qualidade
dos vídeos, junção dos projetos etc". Só análise (nada implementado sem o ok). Não repete as rodadas 1-3. Cada achado
conferido em dado real e gravado na hora. Retomar pelas frentes "pendente".

| # | Frente | Status |
|---|--------|--------|
| G1 | Esforço x resultado: uploads por projeto/canal/tipo (ledger 7 d) contra views (placar 48 h) | feito (VALE MUITO) |
| G2 | Nenhum canal sem postagem: dias vazios por canal (7 d) e canais no teto | feito (ForjaReact travado) |
| G3 | Retenção/CTR onde existe (metricas_studio, metricas hipercool) | feito (2 defeitos) |
| Q1 | Legenda: quantos Shorts saem SEM legenda (parceiro "legenda falhou") | feito (erro escondido) |
| Q6 | Trilhas com direitos autorais + Shorts bloqueados (achado no caminho) | feito (VALE MUITO) — medição em 6 canais rodando |
| Q2 | Áudio e formato: volume (LUFS), resolução, fps, bitrate por projeto (amostra real) | feito (MS Energy estoura; parceiro 720p) |
| Q3 | Gancho e roteiro: 1ªs frases e títulos reais por projeto | feito (títulos gritados/longos) |
| Q4 | Capas: taxa de capa IA x quadro/painel, reprovações | feito (ok) |
| Q5 | Achados aprovados do aprendizado (parceiros) ainda não aplicados | feito (0 aprovados) |
| R1 | Erros reais 24 h por projeto (tipos e contagem) + efeito do F1 nos 429 | feito (429 −45%) |
| R2 | Tarefas agendadas com resultado de erro / paradas | feito (1 tarefa quebrada) |
| R3 | Disco: o que está enchendo o D: (11,7 → 9,8 GB em 5 h) | feito (resolvido) |
| C1 | Custo: o que é pago/limitado e onde se desperdiça cota | feito (ok) |
| I1 | Integração que ainda sobra (depois das rodadas 1-3) | feito |
Todas as frentes analisadas 21/10 ~06:55. Lista priorizada logo abaixo dos achados. Execução: cron 07:01 (dono: "fazer todos").

### Achados rodada 4
(gravados na hora, por frente)

**G1 — esforço x resultado (VALE MUITO; decisão do dono).** 344 uploads em 7 dias; o parceiro é 58% (199). Views em
48 h (placar comum, mediana por canal): Mundo Que Nao Existe 1106, CartuchoReact 1055, ForjaReact 378, Dicas
financeiras 170, Assist-IA 49, HistoriasEmFrames 23 — e os 6 canais de LÍNGUA (hindi, ind, ita, ru, thai, viet)
mediana 0-1 recebendo 15-23 uploads/semana CADA (9-14 deles do parceiro) = ~110 uploads/semana (~1/3 do total) que
voltam ~0 view; "recap hipercool" (línguas) n=43 mediana 0. Por idioma: pt mediana 7 (22% ≥1000) × hi/ru/id/it/th 0.
Proposta: tirar (ou baixar pra 1/dia) o parceiro dos canais de língua e pôr essa capacidade nos canais pt que rendem
(ForjaReact, Dicas, Fio da Meada, Mundo, Cartucho estão com 2-13/semana, longe do teto 3/dia = 21). Hoje a produção
não olha views (F13 só desempata fonte).

**G2 — nenhum canal sem postagem (quase ok; 2 buracos).** Últimos 3 dias: só InovareManhwaVerse (3 dias sem
publicação: dono hipercool, alimentadores {} → o parceiro, que produzia pra ele até 18/10, é barrado e o hipercool
não posta lá) e ForjaReact. **ForjaReact** (3ª melhor mediana, 378) tem 6 Shorts PRONTOS e só 2 postados na semana:
71 recusas "Studio: limite diário de uploads da conta" no `parceiro_postar.log` (não é volume — conta limitada; o
postador tenta de novo a cada 30 min). Ação do dono: ver no Studio do ForjaReact (verificação por telefone/aviso da
conta). Esporte/Game/Bicho Noturno "vazios" são canais novos com publicação agendada pra frente (ok). Inovare
esp/eng/french: 0 (en bloqueado e fr com strike — já conhecido).

**Q5 — aprendizado dos parceiros: nada aprovado.** 86 achados pendentes (Sonnet 48, Gemini 38) e 18 "descartado"
(status criado por outra sessão); nenhum SIM/NÃO do dono no Telegram ainda → nada a aplicar. Sugestão: mandar 1 resumo
por dia com os 5 melhores (em vez de mensagem por achado) pra o dono decidir em lote.

**G3 — retenção/CTR (VALE, médio).** Só 18 Shorts com "continuaram assistindo" (mediana 39%; os que passaram de 1.000
views ficaram em 25-53%; os de 85-88% têm < 40 views = amostra pequena). Dados da estratégia da rede: os vencedores
com > 1.000 views usam gancho `pergunta_direta`/`spoiler_parcial` e título `choque`/`pergunta`/`opiniao`; `nome_obra`
no título aparece em vídeos de 26-65 views (bate com a regra do dono "sem nome da obra"). Defeitos: (1) o hipercool
`metricas.py` gravou 12 longos com impressões/CTR = None → o placar de título do hipercool (CTR) nunca recebe dado;
(2) `metricas_rede.do_ledger` usa o NOME DO ARQUIVO como título (17 aparecem "video.mp4" nas listas de melhores/
piores do painel) — pegar o título da ficha `postar.json`. Proposta maior: ler retenção de todo Short do ledger (F3)
— é o sinal de qualidade de roteiro/edição que falta pra decidir o resto desta rodada.

**Q1 — legenda (VALE, pequeno).** Shorts do parceiro com "legenda falhou — usando sem legenda": 18/10 2, 19/10 0,
20/10 8 linhas (~4 de 54 Shorts), 21/10 0 (até 06h). Causa escondida: `fx_subtitles.burn_subtitles` descarta o stderr
do ffmpeg (`except CalledProcessError: return False`) e o `anime_captions` só loga "burn_subtitles falhou"; 3 das
falhas foram 11-12h de 20/10, quando o D: estava enchendo (provável disco). Proposta: logar o fim do stderr e tentar
1x de novo (ou o caminho libass, que hoje só é tentado ANTES do PNG). Frase de narração pulada ("áudio sem duração"):
2 em 4 dias, ligadas ao bug do "humanizar" de 20/10 (já conhecido) — menor.

**Q6 — TRILHAS COM DIREITOS AUTORAIS (VALE MUITO; risco).** A biblioteca ÚNICA `hipercool-materiais\assets\trilhas`
(329 faixas, de todos os projetos) tem só 36 com "no copyright/free/sem direitos" no nome; o resto inclui OST e música
comercial: Hans Zimmer (Interestelar), Pokémon, Despicable Me, GTA, JoJo, Zelda, DOOM, Sonic, Deltarune, Re:Zero
"Styx Helix" (MYTH & ROID), Naruto, Tensura, Marcelo D2. Uso real nos Shorts do parceiro 18-21/10: 202 trechos de
trilha, só ~62 (31%) claramente livres; o mais usado é `cornfield_chase_hanszimmer` (11x). E o sistema é CEGO pra isso:
o `youtube_web_poster` não lê o resultado da "Verificação de direitos autorais" do upload e nada lê a coluna "Avisos"
do Studio. Prova real (Studio do Dorama Noturno, 21/10 06h): 1 Short agendado está **"Bloqueado"** (26/10) e o
parceiro conta ele como agendado (o dia fica sem post); e o mesmo Short aparece 2x no canal ("ELE DESCOBRIU O SEGREDO
do PAI…", duplicado). Proposta: (1) separar a biblioteca em `livres` x `protegidas` e os pipelines só sortearem
livres (as 36 + biblioteca de áudio do YouTube); (2) ler "Avisos" no Studio (bloqueado/reivindicado) e: tirar o
bloqueado da agenda + re-render sem a trilha, e pôr a trilha numa lista negra automática.
Medição real no Studio (21/10 06h, 30 Shorts mais recentes por canal): **Bloqueado** Dorama Noturno 1/17, hindi
2/30, CenaReact 3/30, CartuchoReact 0/30, Manhwa Noturno 0/12 → ~6% dos Shorts recentes desses canais NÃO vão abrir
(a causa pode ser a trilha OU a imagem do dorama/filme do parceiro — a lista não diz). No caminho: canal HINDI com
título em PORTUGUÊS ("🤯 Ela Teve 9 FILHOS com um Estranho…" — vídeo na língua errada); CartuchoReact com títulos
repetidos de modelo do Veo ("Cerebro Digital - Trocadilhos Visuais Literais #shorts" 5x, mais 2 outros 2x) = SEO
fraco; Dorama Noturno com o MESMO Short 2x. (Mundo Que Nao Existe: nome não casou no mapa do poster — sem medida.)

**R1 — erros e efeito do F1 (feito).** 429 do Gemini no parceiro: 20/10 = 2,0 por Short (109/54); 21/10 depois do
estado único de chaves (01:20) = 1,1 por Short (18/16) → ~45% menos (com a ressalva de a cota do Google renovar de
madrugada). Gateway quase não falha. Erros de postagem do parceiro: ForjaReact 71x "limite diário de uploads da
conta" (G2).

**R2 — tarefas com erro (pequeno).** "Limpeza source.mp4 anime" (criada por outra sessão) termina com 0x80070002 =
arquivo/caminho não existe — não limpa nada; TikTokRodadaExtra saiu com 106 em 20/10 19:35 (antes da troca pro
rodar_oculto; ver na próxima 14:05). As demais de vídeo: ok.

**R3 — disco (resolvido agora).** D: com 28,9 GB livres às 06h (outra sessão liberou). Escrita das últimas 12 h:
recapd workspace 3 GB (normal); os "2,41 GB" repetidos são a mesma pasta de modelos (applio) vista por várias
junções. O guardião (F9) cobre o resto.

**Q2 — áudio e formato (amostra real com ffmpeg ebur128/ffprobe).** Volume padronizado: parceiro −14,0 LUFS (pico
−1), react −14,1/−14,2, Veo limpo −15. **MS Energy −12,9 LUFS com pico +0,2 dBFS = estoura** (passar pelo
`master_loudness` comum). **Parceiro em 720x1280 a ~2-3 Mbps** enquanto react/Veo saem 1080x1920 (6-8,7 Mbps):
Short do parceiro é o que mais sobe (58%) e sai com a pior imagem — subir pra 1080x1920 custa render (PC1/PC2) e a
fonte do parceiro às vezes já é 720p; vale testar 1 canal. Duração: Shorts do parceiro 35-113 s (os 3 medidos ~100 s)
× react 13-37 s — sem retenção do parceiro medida não dá pra dizer se o longo perde gente (G3).

**Q3 — títulos e gancho do parceiro (VALE, pequeno).** Últimas 60 fichas: 32 com MAIS DA METADE das letras em
MAIÚSCULAS (grito), 19 com > 70 caracteres (cortado no celular), 58 com "#shorts" no título (gasta espaço; o YouTube
já sabe que é Short), começos repetidos ("O PODER" 5x). Os vencedores da rede (G3) usam CAPS só em 1-2 palavras
("Essa é a personagem mais CALCULISTA…"). Proposta: regra no `seo_generator` do recapd — máx. 2-3 palavras em CAPS,
≤ 60 caracteres, "#shorts" só na descrição; o placar de título (F4) mede. O gancho em barra no topo já existe
("[vertical] gancho: ELE NUNCA DEVERIA TER ENTRADO"); roteiro não fica na pasta (não amostrado).

**Q4 — capas (ok).** 59/60 fichas do parceiro com `capa.jpg` (quadro do vídeo + gancho). Capa IA só no anime/hipercool
(cobertas na rodada 3: checagem comum + placar).

**C1 — custo (ok, sem vazamento).** OpenRouter (pago por uso: música Lyria, voz gpt-audio, imagem) só em módulos de
reserva (`omniroute_music/tts/image`, importados por fx_music e edge_tts_engine) — 0 usos no log do parceiro de 20/10.
Gasto real = cotas grátis (Gemini 52 chaves, Cloudflare 4 contas, Pollinations, Webshare) + crédito mensal do Kiro
(visão de reserva, aprendizado, editorial do react). Desperdício que existia: 429 (F1, −45%) e gateway do postador
morto (F2, corrigido). ElevenLabs: arquivo de chaves de julho (só hipercool).

**I1 — integração que sobra.** (1) Ler os "Avisos"/direitos do Studio pra TODO projeto (Q6) — hoje ninguém lê; (2)
título real no registro de métricas (G3); (3) juntar `gemini_llm` (R2-6b, precisa do dono); (4) InovareManhwaVerse
sem alimentador (G2); (5) tarefa "Limpeza source.mp4 anime" quebrada (R2).

### Rodada 4 — lista priorizada (valor ÷ esforço)
1. **Q6 trilhas protegidas + Shorts bloqueados** — risco de bloqueio/reivindicação em ~6% dos Shorts e sistema cego:
   separar livres × protegidas, sortear só livres, ler "Avisos" do Studio e tirar bloqueado da agenda. (médio)
2. **G1 produção onde dá view** — ~110 uploads/semana nos 6 canais de língua com mediana 0; passar capacidade pros pt
   que rendem (ForjaReact, Dicas, Fio da Meada, Mundo, Cartucho). (pequeno, decisão do dono)
3. **G2 ForjaReact travado** — 6 prontos parados por "limite diário de uploads da conta": dono ver o Studio. (ação do dono)
4. **Q1 legenda falhando calada** — logar o erro e tentar de novo. (pequeno)
5. **Q3 títulos gritados/longos** — regra de CAPS/tamanho no SEO do parceiro. (pequeno)
6. **G3 métricas** — CTR do hipercool vindo vazio; título "video.mp4" no registro; retenção de todo Short. (pequeno/médio)
7. **Q2** — MS Energy estourando (+0,2 dBFS); testar parceiro em 1080x1920 num canal. (pequeno / médio)
8. **Q5** — aprendizado: 86 achados sem resposta → 1 resumo diário com os 5 melhores. (pequeno)
9. **R2/I1 menores** — tarefa de limpeza quebrada, InovareManhwaVerse sem alimentador, Short duplicado, título pt em
   canal hindi. (pequeno)

## Execução rodada 4 (dono 21/10 ~06:30: "fazer todos"; começou 07:01)
| # | Item | Status |
|---|------|--------|
| Q6a | Trilhas: livres × protegidas (lista, sem mover/apagar) + pipelines sorteiam só livres | FEITO 07:40 — **correção da análise**: a blocklist de 28/06 (`_curadoria\copyright_blocklist.json`, 166) já tirava do sorteio Pokémon/GTA/Zelda/JoJo/Marcelo D2 etc. (hipercool, recapd e historias usam; o react usa `safe_only` = só fonte livre); o que passava eram 10 faixas chegadas depois — e TODAS estão em `trilhas\prioritarias\` = **curadas pelo dono** ("sempre liberadas"): Hans Zimmer, Tensura, Wii Shop, lofi do podcast, spysky, illmatic, rizzyserino, 2 phonk Infraction, Styx Helix. Bloqueei e DESFIZ (cópia `.com7_20261021`; volta ao `.bak_20261021`): a escolha é do dono. Feito: `conhecidas` (324 nomes) + quarentena no `fx_music` das 3 cópias (`_blocked_names`/`_blocklist_copyright`): faixa NOVA na pasta, fora de `conhecidas`, fica fora do sorteio até classificar; prioritárias intactas. Testado nos 3 venvs: faixa de teste nova = fora; Zimmer/Tensura (prioritárias) = liberadas; recapd/historias 0 faixa bloqueada em 1.200 sorteios. Achado à parte: o hipercool sorteia prioritárias mesmo se estiverem na blocklist (regra do dono) e o recapd/historias as bloqueiam (ex.: meruem_sad_theme) — comportamento antigo, divergente. |
| Q6b | Avisos do Studio (Bloqueado) nos agendados → avisar, liberar a vaga, trilha na lista negra | FEITO 07:55 — `youtube_studio_extras --avisos` (`avisos_conteudo`: coluna "Avisos" de Shorts e Vídeos, com o id); novo `postador\bin\avisos_studio.py` (4 canais/rodada em rodízio dos 28; SUBVIGIAS de hora em hora a partir das 8h): bloqueado novo → `config\bloqueados.json` + `bloqueado_studio` na ficha + aviso pelo portão; trilhas do Short (log do parceiro) → `_curadoria\trilhas_suspeitas.json`; trilha em 2+ bloqueios entra sozinha na blocklist, prioritária = só avisa. `politica.bloqueados()` tira o bloqueado de `_publicacoes`/`canal_vazio_hoje`/`horario_publicacao` (vaga de publicação do dia volta; upload continua contando); `parceiro_diario`: estado "bloqueado" e fora do "postado hoje". Rodado DE VERDADE (Dorama, hindi, CenaReact): 7 bloqueados registrados e avisados; **Hans Zimmer em 2 dos 4 bloqueados com trilha conhecida** → aviso ao dono (prioritária); 1 bloqueado do CenaReact só com trilhas livres = bloqueio pela IMAGEM do filme. Teste do politica: vaga de 26/10 do Dorama liberada (1 → 0 publicações contadas). |
| G1 | Línguas do parceiro 1/dia; capacidade pros pt que rendem | FEITO 08:05 — `config\parceiro.json` (backup `.antes_g1_20261021`): hi/id/it/ru/th/vi `por_dia` 3→1 e `fila_alvo` 6→2 (en/fr intocados: bloqueado/strike); Dicas financeiras, Fio da Meada (codigo_inteligente), Mundo Que Nao Existe e CartuchoReact `fila_alvo` 9 (ForjaReact fica 6: 6 prontos travados no limite de upload). `parceiro_diario`: a escolha das línguas usa o `fila_alvo` de cada língua. Simulado com os dados reais: línguas que entrariam agora = nenhuma (todas com 4 prontos > 2) → o render das traduções vai pros pt; a ordem segue "canal sem post hoje" primeiro (nunca sem postagem), os que rendem ficam mais tempo na fila de produção. Desfazer: copiar o backup de volta. |
| Q1 | Legenda: logar stderr + tentar de novo/libass | FEITO 08:25 — `recapd fx_subtitles.burn_subtitles`: cada passada tenta 2x e loga o fim do stderr do ffmpeg ("[captions] passada i/n falhou (tentativa k): …"); `anime_captions.burn_captions`: PNG falhou e o libass não tinha sido tentado → tenta libass antes de sair sem legenda. Testado num vídeo real com o ffmpeg quebrado de propósito: o motivo apareceu no log ("No such filter"), 2 tentativas, e o libass queimou a legenda (True, arquivo criado). |
| G3 | Métricas: CTR do hipercool vazio; título "video.mp4" no registro | FEITO 08:40 — **causa achada**: o Studio renomeou os cartões ("Impressões de miniaturas", "Taxa de cliques na miniatura") e o `youtube_studio_extras.metricas` procurava o nome antigo → impressões/CTR None em todo longo (hipercool e completos da rede). Regex aceita os dois nomes; testado num longo real (yiFQlV76o9E, canal viet): antes impressões/CTR None → agora 747 impressões, CTR 7,1%. `metricas_rede.do_ledger` pega o título da ficha `postar.json` (429 itens, só 44 antigos sem ficha ficam com o nome do arquivo); as 19 medidas antigas com "video.mp4" são de antes de 18/10 (sem ficha). |
| Q3 | Títulos do parceiro: CAPS/tamanho/#shorts | FEITO 08:50 (menor que a análise dizia) — o "CAPS demais" era a métrica minha (% de letras); o estilo é DECISÃO do dono no prompt ("estilo dos canais que mais crescem… 3-5 palavras-chave em MAIÚSCULAS") e os títulos reais cumprem (4 palavras longas em caixa alta) — estilo mantido. Feito em `recapd seo_generator`: `#shorts` sai do título (continua na descrição) e `_caps_no_limite` garante o máx. de 5 palavras em caixa alta quando o modelo exagera. Testado em 4 títulos reais e em russo (não mexe em cirílico). Limite de tamanho (85) mantido. |
| Q2 | MS Energy estourando | FEITO 09:00 — o `montar_final` (beta do Veo, compartilhado) não nivela volume; no fim do `ms-energy\bin\gerar_short_veo.py` entrou `_nivelar_audio` com o `master_loudness` COMUM (2 passadas, −14 LUFS, pico −1,5 dB; falhou = vídeo segue como saiu). Testado num clipe real do MS Energy: −19,2 → −13,9 LUFS, pico −1,5 dBFS (medido com ebur128 depois). O Veo do react não foi tocado (já sai −15). Parceiro em 1080p: não feito (custa render nos 2 PCs; decidir com o dono depois de ver a retenção). |
| Q5 | Aprendizado: resumo diário em vez de 1 mensagem por achado | JÁ FEITO por outra sessão (21/10) — `aprendizado.py` ganhou `MAX_DIA` (só os melhores do dia) + `_filtrar` (descarta o fraco/repetido, status "descartado", lista `JA_TEMOS`). Não mexi pra não atropelar. |
| R2/I1 | Tarefa de limpeza quebrada; InovareManhwaVerse sem alimentador; duplicado; título pt no canal hindi | FEITO 09:20 — (1) tarefa "Limpeza source.mp4 anime" chamava `python` solto (0x80070002 = não achava) → caminho completo do Python313 (pythonw); `--dry-run` real: roda e não apagou nada (só apaga source.mp4 de pasta com final pronto e 2+ dias). (2) InovareManhwaVerse: NÃO mexi — o destino do parceiro está `ativo: false` de propósito e o canal é do hipercool (regra: não despausar sem ver o Studio) → decisão do dono. (3) Short repetido: no ledger não há arquivo 2x (o 1º upload estourou o tempo sem registro); `avisos_conteudo` marca "Duplicado" (mesmo título 2x nos Shorts do canal) e o `avisos_studio` só AVISA (não libera vaga) — testado no Dorama: 2 avisos (bloqueado + repetido). (4) título pt no canal hindi: upload de 17/10 22:18, antes do projeto no ledger e da checagem de língua do SEO — caso antigo, já bloqueado. |
| dono | ForjaReact "limite diário de uploads" + tokens OAuth (3 faltando, 5 sem consentimento) + InovareManhwaVerse desligado + Hans Zimmer nas prioritárias | AVISAR (ação do dono no Studio/navegador) |
| CTA | conferência do CTA no fim (cron 09:17, feita 10:40) | FEITO — 3 Shorts com CTA; "O Estrangulamento do Leão" (55 s): CTA inteiro, acaba 1,2 s antes do fim (Groq); "pelo mais grosso" (fonte 34 s): CTA CORTADO — e o fim da história também: o roteiro do parceiro contava 4,5 s/frase, o real é ~5,4 s → fonte curta estourava. `anime_auto`: `orig_dur / 5.5`, mínimo 5 frases (34 s → 6 frases ≈ 32 s). |
| TRAVA | **incidente causado por mim**: trava do Chrome presa 09:24-10:54 | CORRIGIDO 11:06 — as rotinas novas do Studio (sem_token/extras_ledger/avisos_studio) rodavam juntas, estouravam o prazo (400/600 s, menor que a espera de 20 min da trava) e matavam o filho que SEGURAVA a trava → arquivo ficava, só soltava em 3 h; a postagem do parceiro e as métricas da rede ficaram ~1h30 sem subir ("trava ocupada há 25 min"). Conserto: `youtube_web_poster.Trava` grava o PID e solta na hora trava de dono morto; trava sem PID (código antigo) é testada por rename (aberta = dono vivo); prazo das rotinas 1800 s; as 3 viraram UMA sequência (`studio` no SUBVIGIAS). Testado: trava limpa, de dono morto (0 s), órfã sem PID (0 s) e de dono vivo (esperou o dono). Removidas à mão 2 travas órfãs (10:54 e 11:06). |
| ANTI-BLOQUEIO | dono 21/10 ~10:40: "identificar o bloqueio e parar de usar o que causou, sozinho" (o bom é o bloqueio do PROGRAMADO: Studio diz "Nenhum impacto no canal / Esta não é uma advertência") | FEITO 12:30 — **Causa exata**: `youtube_studio_extras.reivindicacoes` lê a tabela "Reivindicações" (conteúdo, autor, tipo: Áudio / "Melodia ou letra" = música; Visual/Vídeo/Audiovisual = imagem) e o `avisos_studio` chama pra cada bloqueado (os já lidos vão em `--ja-lidos`). **Tirar de uso** (`video-fila\material_bloqueado.py`): música reivindicada → a faixa casada pelo nome (palavras inteiras, sem genéricas; testado em 6 casos reais) sai do sorteio (blocklist) e, se prioritária, vai pra `prioritarias\_bloqueadas\`; sem trilha conhecida no vídeo, procura o nome na biblioteca; imagem → a FONTE do parceiro leva a culpa (2 em 14 dias = fora do rodízio; 1 = 3x menos chance); música NÃO pune a fonte; reler com a causa refaz a conta. **Resultado real (12 bloqueados lidos)**: Cornfield Chase/Hans Zimmer em 5 (Áudio e "Melodia ou letra"), "deep space" (Prod. Riddiman, faixa que se diz FREE FOR PROFIT) em 2, Infraction "Halloween Night" (selo "no copyright") em 1, Naruto "The Raising Fighting Spirit" em 1 (contraria a isenção do dono de jul/26 — saiu por prova; ele decide se volta), 2 por IMAGEM (anime "Rekishi ni Nokoru Akujo" e Ryomen Sukuna/JJK, uploads antigos sem fonte). Saíram de uso: Hans Zimmer (movido), deep space, Halloween Night, Naruto Raising; a fonte f_UCRKSO0 (punida antes por engano) VOLTOU ao rodízio. Achados: nome "free/no copyright" não protege nada; "Melodia ou letra" é música. **Margem do agendamento** (pergunta do dono): rodapé do upload medido = "Verificação 1% … 10 minutos restantes" → os 11 min do politica (contados ANTES do upload) não bastam; o `youtube_web_poster` agora agenda no mínimo +25 min (Short) e +25 min + duração (longo: 40 min → 65, 2 h → 145) e grava o rodapé em `logs\checagem_direitos.jsonl`. Testados: leitura real em 5 canais, caminho de bloqueio novo com causa (estado de teste), margem por duração. Memórias: feedback-anti-bloqueio, feedback-agendamento-obrigatorio. |
| EMERGÊNCIA | dono 21/10 ~14h: "nem postagem emergencial de canal que faltou pode postar na hora — programar com o tempo mínimo da checagem" | FEITO 14:10 — `politica.MIN_AGENDA_MIN` 11→25 e `politica.agenda_minima(video)` (+25 min; longo > 3 min: +25 + duração; arredonda 15 min). Vale nos DOIS caminhos: `youtube_web_poster` (já tinha) e `youtube_poster.upload()` por API (vários scripts antigos importam `upload` direto, sem política) — a trava está DENTRO do `upload()` e o modo linha de comando grava no ledger o horário empurrado. As 3 cópias antigas do historias (`prod`/`beta`/`teste\bin\youtube_poster.py`, sobras que ainda subiam pela API) agora recusam igual ao `bin\` (backup `.antes_recusa_20261021`). Testado sem subir nada: 14:06 → Short pedido pra +5 min vira 14:45; longo de 55 min sem data → 15:30; amanhã fica; privado sem data fica. Produção real: `logs\checagem_direitos.jsonl` (último upload 12:44 abre 15:30). |
| YT-DLP | achado 14h: parceiro sem Short novo 13:05-14:07 (33 downloads barrados em 1 h; vigia: "Sign in to confirm you're not a bot") | FEITO 14:30 — a chamada isolada funcionava (bloqueio por VOLUME). Cada candidato pedia legenda em 5 idiomas (5 pedidos) + 2 downloads; em 9 dias só pt (103) e es (7) deram legenda e os 50 sem legenda gastavam 5 pedidos cada. `recapd anime_fetch`: legenda só pt → es (1 pedido no caso comum; pt+es juntos deu 429 na es no teste), reaproveita a legenda já baixada, o erro REAL do yt-dlp vai pro log (antes só o comando). COMUM `ytdlp_vez` (subido pros 3: hipercool, manhwa-react, recapd): `bloqueio(texto)` (robô/429; 429 só de legenda não conta), `pausar()` 20 min em `video-fila\ytdlp_pausa.json`, `pausado()`; o `anime_fetch` pergunta antes de cada pedido e para na hora (0 s) em vez de ~200 pedidos/h durante o bloqueio. PC2: sem `D:\video-fila` = sem pausa (não quebra). Testado: 6 textos de bloqueio, pausa em arquivo de TESTE, legenda real (1 pedido, 2ª vez 0 s). |
| ANTI-BLOQ 2 | conferência da rotina do Studio rodando sozinha (13h) | FEITO 14:40 — (1) bloqueio novo no ru (UAqZWQAB3uM) por "inaudio - Infraction- Backslider" NÃO tinha saído de uso: o arquivo é `phonk_drift_atmospheric_infraction_LHae9zvUfug.mp3` (sem o nome da música); o `_catalogo` da curadoria (`_curadoria\catalogo.json`, `identificacao.nome` = "Backslider") agora entra no `material_bloqueado._casa` → saiu do sorteio (blocklist) e a prioritária foi pra `_bloqueadas\`; os 3 `fx_music` (hipercool, recapd, historias) conferidos bloqueando. Varredura das 9 músicas reivindicadas contra as 338 faixas: só os casamentos certos (nenhum falso). (2) `reivindicacoes`: imagem sem nome no Studio virava conteúdo "Tipo" (cabeçalho) → vazio; registro do 5ocUB-tZbos corrigido (backup `.antes_tipo_20261021`). (3) `avisos_studio`: "Inovare Manga ind" e "inovare manhwa br" davam "canal não encontrado" (nome do `canais.json` ≠ nome do cred) → acha pelo `channel_id` no mapa do navegador; 28/28 canais do rodízio resolvem (sem abrir navegador). Também novo no ru: KnXOH-VI7wI por imagem (Ryomen Sukuna/JJK, upload antigo sem fonte). |

## Rodada 3 (20/10 ~21:00) — o que ainda falta integrar e vale a pena
Pedido do dono: "verifique profundamente se tem mais alguma coisa que falte integrar que valha a pena". Só análise
(nada implementado sem o ok dele). Cada frente: conferida no código E em dado real (log/estado), achado gravado na hora.

| # | Frente | Status |
|---|--------|--------|
| F1 | Estado compartilhado de chaves/limites (Gemini, limitador, proxies): por projeto ou um só? | feito (achado: VALE) |
| F2 | Cliente de LLM: caminhos e reservas de cada projeto; falhas reais nos logs | feito (achado: VALE) |
| F3 | Leitura de métricas do Studio: quantos leitores, conflito de Chrome, onde grava | feito (vale pouco) |
| F4 | Aprendizado de capa (pose/estilo): separado por projeto? alguém registra? | feito (achado: VALE) |
| F5 | Anime/parceiro reprovado por nudez: perdido ou dá pra censurar (mosaico do hipercool)? | feito (não vale) |
| F6 | Reuso TikTok/Insta: o que de cada projeto/tipo nunca vai pra lá | feito (achado: VALE MUITO) |
| F7 | Acabamento no Studio (comentário fixado, relacionado, tela final) por projeto | feito (vale pouco/médio) |
| F8 | Comentários: quais canais são lidos/respondidos (Noturnos sem token?) | feito (achado: VALE) |
| F9 | Limpeza de disco: quantos limpadores, regras, guardião único (D: encheu e venv apagado hoje) | feito (achado: VALE) |
| F10 | Voz/narração: narrador v2 e voz clonada chegam em todos os projetos? | feito (CTA falta; tracker parado) |
| F11 | SEO: "título sem nome da obra" + palavras buscadas em todos os geradores | feito (não vale) |
| F12 | 3º PC (desktop): usado pelo controlador? | feito (não vale) |
| F13 | Prioridade da produção pelo placar (nichos do parceiro, projetos) | feito (achado: VALE) |
Todas as frentes analisadas (20/10 ~21:50). Ordem sugerida: F6 → F2(conserto) → F1 → F8 → F4+F13 → F9 → F10/F7.

### Achados rodada 3
(gravados na hora, por frente)

**F1 — chaves do Gemini (VALE MUITO, conserto pequeno).** `gemini_tts.pick_gemini_key` (base de `gemini_llm`,
`edge_tts_engine` COMUM, capa, revisão, roteiro do anime) tenta 1º um PostgreSQL (`nova_lista_de_chaves_2`) pelo arquivo
`secrets\postgres-fluxo-n8n.json` — que NUNCA existiu neste PC (é da VPS do n8n): falha calado em todo processo.
Sobra o rodízio LOCAL em memória: cada processo novo começa da chave 1; `mark_key_error/ok/bump_key_fila` só escrevem
no PG = não fazem nada; o cooldown modelo:chave do `gemini_llm` (`_model_exhausted`) também é só da memória do
processo. Dado real de hoje (logs mexidos em 20/10): 302 respostas 429 (recapd 237, hipercool 56, video-fila 9),
**só 14 das 52 chaves tocadas**, as 2 primeiras da lista com 80 e 78 erros; cada 429 ainda dorme 2-20 s. Proposta:
COMUM `chaves_gemini.py` com estado ÚNICO em `D:\postador-de-videos\secrets\gemini_estado.json` (junção = todos os
projetos veem o mesmo): escolhe a chave fora de cooldown usada há mais tempo, 429 = cooldown da chave (e do
modelo:chave) pra TODOS os processos; `gemini_tts` local chama ele (4 cópias: hipercool, recapd, historias, postador).
Limitador (`limitador.json`) segue por projeto (hipercool `workspace`, react `work`) — menor.

**F2 — modelo de LLM em cada canto (VALE, médio).** 21 linhas em 17 arquivos com nome de modelo fixo + 3 configs
(`secrets\claude_proxy.json` kr/claude-sonnet-4.5, `secrets\omniroute.json` antigravity/gemini-3-flash,
`manhwa-react\config.json` editorial opus/sonnet/haiku). Conferido no catálogo vivo (`/v1/models`): 2 nomes MORTOS
desde 16/10 ainda no código — `antigravity/gemini-3.1-pro-high` é o PADRÃO do `postador\bin\gemini_llm.py`
(gateway primeiro): o `postar_tudo_hoje` (postagem do anime) e mais 7 scripts levam 400 em toda chamada e caem nas
chaves do Gemini (somando aos 429 da F1); `antigravity/gemini-2.5-pro` é o padrão do `claude_client` do recapd (salvo
pelo omniroute.json). Ninguém percebeu em 4 dias. Gateway em si quase não falha (1 erro hoje no log do parceiro).
Kiro (kr/*: hipercool claude_client, reserva de visão da capa, aprendizado, editorial do react) tem crédito mensal e
desliga conta ao zerar (renova dia 1). Proposta: `modelos.json` ÚNICO no secrets central (papel → modelo: texto_rapido,
visao_reserva, editorial…) lido pelos clientes; vigia confere 1x/dia cada modelo configurado contra `/v1/models` e
avisa o que sumiu. Conserto imediato e sem risco: padrão do postador → `antigravity/gemini-3-flash`.

**F3 — métricas do Studio (VALE POUCO).** 3 leitores pelo navegador — hipercool `metricas.py` (1x/dia pela fila,
longos: impressões/CTR, 12 vídeos), postador `metricas_rede.py` (de hora em hora: rede + 1ª leitura de todo vídeo do
ledger entre 48-96 h, 137 vídeos, retenção só em 16), historias `metricas_historias.py` (parado) — mas os 3 já usam o
mesmo `youtube_studio_extras` (mesma trava do Chrome: sem briga). O que se repete é só onde grava e a regra de decisão.
Buraco real: o parceiro (quem mais posta) e o anime só têm views em 48 h; retenção ("continuaram assistindo") dos Shorts
só é lida pra rede. Proposta pequena: `metricas_rede` ler a retenção também dos Shorts do ledger que ele já visita.

**F4 — aprendizado de capa (VALE, médio; mesmo caminho do título).** Nenhum dos 3 aprende de verdade: hipercool
`capa_ia` tem Thompson por pose/layout em `workspace\capas_poses.json` — o arquivo NÃO existe: `registrar_teste` só
roda quando entra teste A/B do Studio (canal sem verificação = "pendente") e `registrar_vencedora` nenhum código chama;
historias tem o seu (projeto parado); a capa do anime/parceiro não tem aprendizado nenhum (pose sorteada e gravada em
`<capa>.capa.json`). Os catálogos de pose são diferentes por projeto (sensual/batalha, ação, história), então o placar é
por projeto, mas o MECANISMO é o mesmo do título: o `_placar_titulos` do `medir_48h` já abre a ficha de cada vídeo
medido — ler também a pose da capa e registrar "vitória" (views > mediana do canal) num placar de capa por projeto, que
o sorteio de cada `capa_ia*` passa a usar. Capa é o que traz clique (dono).

**F5 — censurar anime/parceiro reprovado (NÃO VALE).** Só 4 vereditos em `animes recap` (3 reprovados, 16-17/10);
desde 17/10 a revisão do parceiro é "dispensada (fonte de parceiro já no YouTube; dono 17/10)". Volume quase zero.

**F6 — reuso TikTok/Insta (VALE MUITO, conserto pequeno).** 19-20/10 o TikTok (59 contas) recebeu 133 Veo (tapa-buraco
da `reserva_veo`), 18 react, 12 parceiro, 0 hipercool; 166 dos 194 Shorts de parceiro só saíram no YouTube. Causa:
`catalogo.disponiveis` bloqueia por NOME (`cat["so_nome"]`, vídeo postado registrado só pelo nome) e todo Short do
parceiro se chama `video.mp4` (uma pasta por item) → 1 `video.mp4` no TikTok bloqueia os 182 do parceiro (testado:
182 "bloqueado so_nome", com conta de destino mapeada). Conserto: nome genérico (`video.mp4`) não entra no bloqueio
por nome (usar o caminho/pasta). Também: 21 compilados do hipercool > `bytes_max` 200 MB (longos, ok ficarem fora);
19 parceiro sem conta no TikTok (MundoQueNaoExiste, Dicas financeiras, ForjaReact) e ~120 no Insta (línguas,
CartuchoReact, Animescomia…) = decisão do dono de qual conta recebe.

**F7 — acabamento no Studio (VALE POUCO/MÉDIO).** `youtube_studio_extras` (COMUM do postador) é usado por hipercool
(fila/postar_hipercool/shorts_a_cada_2h) e pela rede do react (`_extras_studio`: comentário fixado, 3/rodada, 7 dias).
Anime e parceiro: nada — o `studio_extras_anime.py` só é chamado pelo `postar_animes.py`, que é LEGADO (quem posta é
anime_publish→postar_tudo_hoje e parceiro_diario). Proposta: o `_extras_studio` da rede passar a percorrer o LEDGER
(todo projeto) e pôr o comentário fixado (pergunta pro público) nos Shorts do parceiro/anime já abertos — custa 1 visita
ao Studio por vídeo; ganho = engajamento nos canais que mais postam.

**F8 — comentários e inscritos dos Noturnos (VALE).** `notificar_telegram` lê comentários/inscritos só pela API, nos
canais com token em `credenciais-canais` (91 comentários avisados: línguas, reacts). Os 4 Noturnos (Manhwa Noturno =
pt do hipercool; Dorama/Curiosidades/Filme = parceiro) NÃO têm token (sem API desde 16/10): 48 dos 304 uploads da
semana foram pra eles e nenhum comentário/inscrito deles chega ao dono nem é respondido. Comentário e inscrito são a
prioridade 1 do Telegram (dono 19/10). Proposta: ação `ler_comentarios` no `youtube_studio_extras` (página
Comentários do Studio, pelo navegador e mesma trava) rodando pelo notificar a cada ~1 h só pros canais sem token, e
o mesmo fluxo de aviso/resposta (responder também pelo Studio). Esforço médio.

**F9 — limpeza de disco (VALE, médio).** Cada projeto limpa o seu dentro do pipeline (hiper-pipeline, hiper-longo,
voz_clonada, ocioso, mr/limpeza, backup_drive) e não há quem decida quando o DISCO aperta: ~12h o D: chegou a 520 MB e
parou o parceiro; à tarde uma sessão "liberando espaço" apagou ~11,5 GB de painéis do hipercool e moveu o venv
(produção parada 18:20-19:46; regra nova em feedback-limpeza-d-seguranca). Hoje as pastas de trabalho são pequenas
(animes recap 5,7 GB, veo 3,6 GB, downloads 1,3 GB, react work 0,7 GB, hipercool workspace 0,6 GB; D: 11,7 GB
livres). Proposta: "guardião do disco" no controlador — abaixo de 10 GB roda SÓ limpezas de lista branca já
conhecidas (intermediários de cada projeto + `backup_drive` dos já postados, sempre `rclone copy`+`check` antes de
apagar, nunca junção/venv/panels/fila de postagem) e avisa; sessões de chat param de improvisar limpeza. O aviso de
D: < 8 GB no vigia já existe (R2-7).

**F10 — voz/narração (parte já feita; 1 buraco; 1 ideia pro dono).** Conferido no código: o parceiro/anime JÁ tem o
narrador v2 (moldes de piada + repertório dos narradores BR em `anime_script.py`) e a voz clonada v2
(`VOZ_CLONADA_VERSAO` em anime_auto/anime_tts/anime_voz_clonada). Buraco: o CTA no fim como peça separada só existe no
hipercool (hiper-pipeline/hiper-longo/narration); no recapd só num script legado (`compile_guards`). Ideia (decisão do
dono): o hipercool (mais potencial, referência Porão) narrar com a voz clonada aprovada — hoje não usa.
**Achado no caminho — controle de novidades parado:** `vigia_melhorias --listar` mostra 44 pendências (hipercool 4,
historias 16, react 10, recapd 14) e várias já estão feitas (portão do Telegram, unificação, narrador v2/voz v2 no
recapd) — ninguém marca, e ele repete todo dia até marcarem. Proposta: marcar as feitas (`--marcar … feito/nao`) e o
`vigia_melhorias` conferir sozinho pelo código quando a novidade cita um arquivo/função.

**F11 — SEO "título sem nome da obra" (NÃO VALE).** A regra + palavras buscadas já estão no hipercool `seo.py`, recapd
`seo_generator.py` e na rede do react; só falta no historias (parado). 261 fichas do parceiro já gravam `estilo_titulo`.

**F12 — 3º PC (NÃO VALE agora).** O controlador nunca usa o desktop (só o `maquinas.py` mede). i5 2 núcleos sem GPU,
o dono grava lá e os vídeos ficam no PC1 (teria que copiar pela Tailscale) — ganho pequeno, risco de atrapalhar.

**F13 — produção guiada pelo que dá view (VALE, médio).** `parceiro_diario._prioridade` decide só por "canal sem post
hoje" > tipo menos produzido em 24 h > fila mais vazia; o controlador tem ordem fixa. Nenhum dos dois lê o placar
(`aprendizado_global`: views em 48 h por canal/projeto/idioma). O parceiro é quem mais posta e cada ficha guarda a
`fonte` (canal do parceiro de onde veio): dá pra medir views por FONTE (ledger caminho → postar.json fonte → medida de
48 h) e, dentro de cada canal, preferir as fontes que rendem (sem tirar a regra "nunca sem postagem"). Mesmo
mecanismo do placar de título (F4 reaproveita).

## Execução rodada 3 (dono 20/10 ~22h: "faça na próxima cron"; começou 21/10 00:41)
| # | Item | Status |
|---|------|--------|
| conferência 02:01 | CTA / extras_ledger / sem_token | nada a conferir ainda: nenhum "CTA no fim:" no `_parceiro_20261021.log` (nenhum Short de parceiro desde a mudança) e as 2 rotinas só começam às 8h (logs inexistentes). Nova conferência marcada pras 09:17. |
| F6 | Bloqueio por nome no reuso | FEITO 00:50 — `catalogo.NOMES_GENERICOS` (video.mp4, final.mp4…) não entra no `so_nome` (gravar) e é ignorado na leitura do catálogo salvo. Testado com o catálogo real: TikTok parceiro disponível 0 → 168 (contas inovaremanhwaverseind 15, inovaremanhwabr 14, hindi 12, doramanoturno 11…); Insta 54 → 57. Risco: o 1 `video.mp4` postado sem arquivo ligado pode repetir 1 vez. |
| F2 | Modelo morto + modelos.json + vigia | FEITO 01:05 — achado maior que o previsto: o gateway do `postador\bin\gemini_llm.py` NUNCA era usado (o `claude_client` do postador procura settings do Claude Code que não existem → `_gateway_call` devolvia None em 0 s), além do modelo morto. Agora: modelo `antigravity/gemini-3-flash` + lê `secrets\omniroute.json` central se faltar config. Testado: `generate_text` 14,7 s (com 429) → 1,2 s pelo gateway. recapd `claude_client` padrão 2.5-pro → gemini-3-flash. **modelos.json NÃO feito** (mexeria em todos os clientes); no lugar, `vigia_geral._modelos_mortos`: 1x/20 h procura todo nome kr/kiro/antigravity/agy no código e nos 3 configs e confere com `/v1/models` — testado: acusou o 2.5-pro do recapd, depois do conserto lista vazia; resultado guardado no estado (não chama o gateway toda rodada). |
| F1 | Estado único das chaves Gemini | FEITO 01:20 — COMUM `chaves_gemini.py` (hipercool, recapd, historias, postador): `secrets\gemini_estado.json` (junção = 1 arquivo pra todos) com uso/castigo por chave; escolhe a fora de castigo usada há mais tempo; erro = castigo 120 s dobrando até 30 min; ok zera; trava msvcrt; aceita entrada sem id (fim do token). `gemini_tts` das 4 cópias: pula o PG quando `postgres-fluxo-n8n.json` não existe, rodízio em memória → `chaves_gemini.escolher`, `mark_key_error/ok` gravam no estado (os 4 `gemini_llm` já chamam `mark_key_error` no 429). Backups `gemini_tts.py.antes_chaves_20261021`. Testado: 2 processos em paralelo (hipercool+recapd) pegaram 6 chaves diferentes cada; chave em castigo não voltou em 60 sorteios; ok zerou; `generate_text` real do recapd respondeu. |
| F8 | Comentários/inscritos dos 5 sem token | FEITO 01:40 — rodada real nos 8 canais sem token (entraram Esporte/Bicho/Game Noturno): InovareManhwaVerse 8 sem resposta (5 avisados), Manhwa Noturno 3 (avisados, registro do portão 01:37-01:38), inscritos lidos (9, 7, 0, 8, 12, 0, 0, 0); ligado no SUBVIGIAS `sem_token` (1 h, a partir das 8h). Histórico: | feito: `youtube_studio_extras --ler-comentarios` (`ler_comentarios` = Comunidade > Comentários sem resposta, blocos `ytcp-comment-thread`; `ler_inscritos` = "Inscritos atuais" do painel) — testado no Manhwa Noturno: 3 comentários nunca avisados (ex. "qual o nome do manhwa?") + 7 inscritos. Novo `postador\bin\sem_token.py` (5 canais sem token, avisa pelo portão como importante, 1ª leitura máx. 5/canal, ganho de inscrito avisa, estado `config\sem_token_estado.json`). FALTA: ver o resultado do `sem_token.py --ensaio` nos 5 canais (rodando às 01:25), depois rodar sem --ensaio e ligar no SUBVIGIAS do vigia_geral (de hora em hora, a partir das 8h). |
| F8b | Tokens da API dos canais sem token | AGUARDANDO — dono mandou 21/10 01:09 em `D:\downloads\toeks youtube\` os **client_secret** (app OAuth "web") de 5 contas: inovaremanhwaverse@ (InovareManhwaVerse), inovaremanhwaverse2@ (Manhwa Noturno), revolutionemerson1@ (Esporte Noturno), revolutionemerson2@ (Bicho Noturno), revolutionemerson3@ (Game Noturno). **Faltam 3**: Dorama Noturno (maiteanajessicajesus@gmail.com), Curiosidades Noturnas (gabriellyvitoriaisabelaaraujo@gmail.com), Filme Noturno (simonerebecaluizasilva@gmail.com). Atenção: client_secret NÃO é o token — falta o consentimento OAuth de cada conta (login no navegador do cofre, escopo só leitura: youtube.readonly) pra gerar o refresh_token e gravar em `D:\credenciais-canais\youtube_canais.json` (campos clientId/clientSecret/refresh_token). Upload continua só pelo navegador. Até lá, comentários/inscritos desses canais vêm pelo Studio (`sem_token.py`). |
| F4+F13 | Placar de capa e de fonte | FEITO 01:45 — `placar_titulos` (COMUM) ganhou `registrar_item/taxas` (placares em `postador\_analise\placar_<nome>.json`, 1 contagem por vídeo). `notificar_telegram._placar_titulos` (medir_48h): a mesma vitória (views > mediana do canal) vale pra FONTE do parceiro (`postar.json` "parceiro", casa com o nome da fonte em 244/261 fichas) e pra pose da capa IA (`*.capa.json` na pasta); marca `placar2` por vídeo. Consumo: `parceiro_diario._escolher_fonte` — dentro do nicho, uso 24 h ÷ peso (1 + taxa de vitória com ≥3 medidas; sem medida 1,5): a fonte que rende sai até 2x mais, rodízio mantido; `capa_ia_anime._poses` ordena por Thompson do placar (sem dados = sorteio). Testado com o estado real (cópia, placar em pasta de teste): 173 medidas → fontes richan/kaijinre/carlosmerchanat/futtres registradas; escolha de fonte e de pose rodam (Python do veo/recapd). Capas: 0 hoje (Short do parceiro usa quadro do vídeo; só a capa IA do anime tem pose). Hipercool segue com o próprio `capas_poses.json` (não ligado). |
| F9 | Guardião do disco | FEITO 00:52 — `vigia_geral._guardiao_disco` (a cada rodada do VigiaVideos, máx. 1x/h): D: < 10 GB → dispara SÓ rotinas existentes que conferem antes de apagar: `backup_drive.bat` (rclone moveto confere tamanho+md5; só o já postado) e `limpar_cache_chrome.py`, e apaga trechos do aprendizado > 7 dias; a mensagem entra nos problemas da rodada (Telegram pelo portão). A limpeza do react já roda em toda rodada da rede. Testado DE VERDADE: D: estava em 9,8 GB → disparou; trecho velho de teste apagado; 2ª chamada na mesma hora = nada. **Atenção**: o backup achou 0 arquivos pra levar e o D: caiu de 11,7 (20/10 21h) pra 9,8 GB — algo está enchendo fora das rotinas seguras; o aviso de < 8 GB continua. |
| F10/F7 | CTA recapd, comentário fixado, marcar novidades | PARCIAL 01:15 — **comentário (F7) FEITO**: novo `postador\bin\extras_ledger.py` percorre o LEDGER (parceiro/anime, aberto há até 7 dias), tira a pergunta pro público que o SEO já põe na descrição da ficha e chama o `youtube_studio_extras --comentario` (mesma trava do Chrome); 3 por rodada, estado `_analise\extras_ledger.json`; ligado no VigiaVideos (SUBVIGIAS, 30 min, só depois das 8h). Testado DE VERDADE: comentário postado no Manhwa Noturno 14IxmQ4UXpw ("O que você faria se acordasse no mesmo dia após ser devorado?"); fixar só libera depois da verificação do canal — conserto: "comentário postado" conta como feito (senão repostaria). 51 Shorts do parceiro na fila. **Novidades marcadas**: 44 → 18 pendências (portão do Telegram feito em todos; unificação; voz/narrador v2 no recapd; react "não se aplica" = voz do dono; historias tudo "não" = parado). **CTA no fim do recapd: FEITO 01:55 (dono mandou fazer os pendentes)** — `anime_auto` modo short de parceiro: o roteiro pede 1 frase a menos e ganha no fim 1 frase de CTA à parte (`anime_script.CTAS_FIM`, 6 frases genéricas de like/comentário/seguir em rodízio pelo id do vídeo) → duração igual; `PARCEIRO_CTA=0` desliga; as línguas traduzem junto. Compila; sorteio testado. **Conferir no 1º Short real**: linha "CTA no fim:" em `workspace\anime\_parceiro_AAAAMMDD.log` e assistir o fim do vídeo (frase não cortada). |

## Execução rodada 2 (dono 20/10 ~10:35: "ok faça todas")
Ordem = menor risco primeiro. Cada item: status + o que foi feito + como foi verificado. Retomar daqui.

| # | Item | Status |
|---|------|--------|
| R2-2 | Capa: checagem v3 no anime/historias | FEITO 13:30 — COMUM `visao_capa.py` (hipercool, recapd, historias; `recursos.py subir` ok nos 3): `DEFEITOS` (anatomia+figurantes, texto idêntico ao do hipercool — conferido na emenda), `pergunta_pose`, `perguntar` (Gemini → Claude pelo gateway), `defeitos`. hipercool `capa_ia` monta a mesma pergunta pelo módulo. Anime/historias: + anatomia (figurantes não reprova: multidão de batalha), visão com reserva (antes 429 do Gemini = capa aceita sem checar) e refaz a pose 1× apagando a imagem ruim do cache. Testado: compila nos 3 venvs, checagem real do anime responde. **Limite achado**: "duas bundas" (colo_harem v1, corpo torcido) NÃO é pego por anatomia — Gemini/Sonnet dizem false na pergunta geral; numa pergunta só de anatomia o Gemini acusa tudo (3 boas inclusive) e o Sonnet nada; gemini-3.8-flash-high/gpt-5.6/sonnet-5 do gateway deram timeout/400. No hipercool essa capa cai por figurantes/pose (Sonnet acerta pose; Gemini errou pose em montada_v2 e deu falso em batalha_v2). Testes em `D:\caches\teste_r2\`. |
| R2-1 | Revisão de nudez no react (e Veo) | FEITO 14:20 — corrigido o achado: o react NÃO subia sem revisão — `politica` exige aprovação por arquivo (`exigir_aprovacao_humana`) e o react é aprovado pelo dono olhando as folhas de quadros; o furo era o `--tudo` (aprova sem olhar). Novo `manhwa-react\mr\revisao_nudez.py` (roda o `revisao_video.py` do hipercool em processo à parte, como o `anime_revisao` do recapd): `rede.aprovar` e `publish.aprovar` com `--tudo` só aprovam o "ok", "reprovado" vira "rejeitado" com a nota, erro fica pendente; no manual mostra o veredito já gravado. **Defeito achado e corrigido no `revisao_video.py` (vale pra hipercool/anime/parceiro)**: vídeo sem troca de cena (Veo de 1 take) dava "ffmpeg dos quadros falhou" (saída dos cortes vazia) → agora aceita com cortes = []. Testado: vídeo do Veo analisado de verdade (16 quadros, ok, 131 s, veredito gravado); leitura de veredito existente (anime reprovado, 8 trechos). Veo: aprovação automática "pedido do dono" mantida (vídeo do Google, já filtrado). |
| R2-6a | edge_tts_engine desandado + vigia avisar cópia comum mudada | FEITO 13:45 — a cópia do recapd já tinha voltado a ser igual à comum (outra sessão); Francisca testada no edge-tts (gera áudio). `video-fila\vigia_geral.py` ganhou `_comum_mexido()`: compara cada cópia registrada em `recursos.json` com a comum e põe "código comum: x.py mudado em <projeto> sem subir — rode recursos.py subir ..." nos problemas da rodada. Testado: limpo = []; cópia do historias mexida de propósito = aviso; restaurada = []. |
| R2-3 | Baixador único do yt-dlp (trava comum, PC2) | FEITO 15:05 — COMUM `ytdlp_vez.py` (hipercool, manhwa-react, recapd; video-fila e voz_clonada importam de `hipercool-materiais\comum` pelo fim do sys.path): `with vez(rotulo)` = 1 yt-dlp por vez no PC inteiro (trava `msvcrt` em `D:\video-fila\ytdlp_vez.lock`, solta se o processo morre) + 6 s entre chamadas; espera máx. 30 min e segue; sem a pasta (PC2/desktop) segue sem vez; aninhado não trava. Envolvidas as 12 chamadas dos 8 scripts ativos: hipercool baixar_trilhas/intros_voz, react mr/base, recapd anime_discover (3)/anime_fetch (2), video-fila canais_parceiros (lista com 6 threads = era rajada; amostra), voz_clonada (2). Testado: 3 processos disputando = entram 1 por vez com 6 s; busca real do anime pela vez (3 resultados, 11 s, ytdlp_vez.json gravado); os 8 compilam/importam. PC2: o `ocioso.py` já pré-baixa no PC1 o Short que vai pro PC2 ("prebaixar"). |
| R2-5 | Título que aprende junto | FEITO 15:40 — achado: os 3 `titulos_estilos.json` estavam ZERADOS (o do hipercool nem existia): ninguém registrava. COMUM `placar_titulos.py` (hipercool, recapd, historias, postador): placar ÚNICO em `postador\_analise\titulos_estilos.json` (geral + por projeto + por idioma, 1 contagem por vídeo). `seo.escolher_estilo/registrar_resultado` (hipercool) e `seo_generator` (recapd, historias) só delegam. Quem alimenta: hipercool `metricas.py` (CTR, já chamava) e NOVO `notificar_telegram._placar_titulos` dentro do `medir_48h`: vídeo medido em 48 h com `estilo_titulo` no `postar.json` ao lado do `caminho` do ledger = vitória se views > mediana do canal (mín. 4 medidas). Testado com o estado real (cópia): 0 hoje porque os medidos são de antes do `caminho` no ledger (18/10); desde 18/10 20h há 133 uploads do parceiro com estilo na ficha → entram ao fazer 48 h; 2ª passada não conta de novo; escolha funciona no hipercool e no recapd. React fica com o aprendizado próprio (estratégia da rede). |
| R2-7 | Vigias/painel/sync menores | FEITO 15:35 (sync: não) — **Vigias**: `vigia_geral.SUBVIGIAS` dispara o monitor do anime (1 h) e o `vigia_melhorias` (1x/dia a partir das 9h), mesmo comando de antes, sem janela e fora do job; última execução no estado do vigia (semeada com a última das tarefas, sem rodar de novo); tarefas `AnimeRecapMonitor` e `VigiaMelhorias` DESLIGADAS (religar: Enable-ScheduledTask). Testado: disparo real do monitor às 15:20 (log). `VozClonadaVigia` segue própria (10 min, Python das vozes, reinicia treino). **Achado**: ~12h o D: ENCHEU (Errno 28 no `parceiro_diario`, produção parada até 13:51; agora 9,1 GB livres) → `vigia_geral.checar` avisa D: < 8 GB e C: < 5 GB. **Painel**: aba "Rede (aprendizado)" no :8790 com o HTML do PainelCanais (rota `/rede`); a tarefa PainelCanais continua (ela também mede vídeos pro aprendizado da rede). Prints desktop/celular sem erro JS em `D:\caches\teste_r2\painel_rede_*.png`. **Sync dos workers NÃO juntado**: `hipercool bin\pc2.py` leva o código dos workers do PC2 (regra: não mexer nos workers de lá) e os 3 funcionam; risco > ganho. |
| R2-6b | Juntar módulos separados de produção | PARCIAL 15:50 — medido (linhas só da cópia vs hipercool): gemini_llm recapd 46/historias 168/postador 140; censura_visual 335/335/260 (recapd/historias de julho, só `fix_hiper_pipeline`/`smoketest` usam = legado); gemini_tts 140/139/89 (hipercool 20/10 é a nova); elevenlabs_tts 142/144/119; claude_client = quase módulos diferentes (hipercool 105 linhas × recapd 376, que o anime inteiro usa). **Não juntei às cegas**: gemini_llm do recapd devolve narração falsa ("Pular cena...") no bloqueio de segurança — o roteiro do anime conta com isso; o do historias tem reserva pelo gateway (`_gateway_fallback`) que os outros não têm; o do hipercool tem Gemini 3 + `_call_direto` + `transcribe_audio`. **Plano da junção** (1 por vez, `recursos.py subir --juntei`, testar o anime_auto de verdade depois): gemini_llm = base hipercool + `_gateway_fallback` do historias + o bypass de segurança só quando quem chama pedir (parâmetro, padrão = comportamento do hipercool) ; gemini_tts = base hipercool (conferir `pick_gemini_key/mark_key_ok/mark_key_error/bump_key_fila`, que o gemini_llm e o edge_tts_engine COMUM importam); censura_visual/claude_client: deixar separados. |
| R2-4 | Postagem num lugar só (por etapas) | NÃO FEITO — decisão do dono (15:55). Conferido: cada postador já tem trava própria (parceiro "outra rodada ainda subindo — pulando"; comentários pulam com a rede rodando; rede com `Trava`), o `politica` já decide vaga/teto/hora de todos (E9) e a trava do Chrome já sobe 1 por vez. Rotina única em sequência: hipercool (segundos) e rede esperariam o parceiro (rodadas de até ~21 min hoje, 15:15-15:37) e um defeito nela pararia TODA a postagem do YouTube ("nunca sem postagem"). Ganho = menos tarefas. Se o dono quiser: `video-fila\postagem_geral.py` (tarefa 5 min, ordem por prioridade, cada postador com o comando de hoje, vigia avisa se parar > 30 min), desligando HipercoolPostagem/ParceiroKaijinre-Postagem/ManhwaReact-Rede/ManhwaReact-Comentarios; horários fixos (MS Energy, TikTok, postar_tudo 06:40) ficam como estão. |
| R2-8 | Aprendizado com vídeos dos parceiros | FEITO 16:30 (MVP) — `D:\video-fila\aprendizado.py`: pega a pasta que o Cortes já baixou (`recapd\workspace\anime\<id>_*\source.mp4`, últimas 72 h; não mexi no anime_auto e não baixa de novo), 10 quadros + fala (legenda .vtt/roteiro) + inventário do que já temos (assets + módulos fx) → 2 modelos: Claude Sonnet pelo gateway e Gemini (`gemini_llm.describe_images` do hipercool); acervo `video-fila\aprendizado\acervo.jsonl` (id, modelo, vídeo/url, segundo, tipo, como aplicar, status) + trecho mp4/mp3 em `aprendizado\trechos\`; Telegram pelo portão (novo `avisos.enviar_arquivo`), máx. 3 por vídeo (nota ≥ 7), o dono RESPONDE SIM/NÃO à mensagem (`notificar_telegram.responder` → `aprendizado.responder`); `placar` = aprovados por modelo; trava de 1 rodada por vez. Roda pelo VigiaVideos (SUBVIGIAS, 30 min, log `video-fila\logs\aprendizado.log`). Regra: memória feedback-aprendizado-parceiros (ler `aprendizado.py aprovados` antes de mexer na produção). Testado: rodada real (airflow/chaminé: 5 achados, 3 Sonnet + 2 Gemini, 3 no Telegram com trecho, 10 min); resposta SIM/"talvez"/mensagem desconhecida com envio interceptado; import sob pythonw. Falta (fase 2): botões em vez de responder com texto; Gemini com o vídeo inteiro; hook de início de sessão. |

