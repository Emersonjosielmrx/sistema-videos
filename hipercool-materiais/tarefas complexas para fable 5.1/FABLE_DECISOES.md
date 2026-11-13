# FABLE_DECISOES.md — decisões do Fable 5.1 (LEIA ANTES DE MUDAR qualquer coisa marcada "Fable")

> **Regra da dona (29/10/2026):** decisão do Fable fica documentada AQUI, com o dado que a sustenta. Outro agente (Opus,
> Sonnet, Gemini, melhorador, sessão de linha) que quiser mudar algo marcado "29/10 (Fable…)" no código ou nos
> ajustes **lê esta pasta primeiro** e só muda se tiver dado NOVO que contradiga o daqui — e registra abaixo o que
> mudou e por quê. O risco que a dona quer evitar: o Fable melhora com número, e alguém depois "corrige" por gosto ou
> por um documento antigo e piora. Cada item tem: **decisão → dado → o que mudou (arquivo) → como desfazer → o que
> NÃO fazer**.

> Horas: os carimbos "29/10 03:xx–04:xx" nas seções "Fable — resultado" foram escritos adiantados em relação ao
> relógio (o trabalho real foi entre ~02:00 e ~03:00 de 29/10); a ORDEM está certa. Os arquivos/logs têm a hora real.

Documentos-base (detalhe e números): `ENGENHARIA_REVERSA (…)\ER_01..ER_04`, `CORTES_01`, `CORTES_02`, `CORTES_05`
(seção "Fable — resultado" de cada um). Scripts só-leitura: `D:\video-fila\engenharia_reversa\continuaram_x_views.py`,
`hora_idiomas.py`, `juri_x_views.py`.

---

## D1 — A régua dos Shorts é "elegível para o lote" e depois "% assistido", não views brutas nem "continuaram"
- **Dado (279 Shorts de parceiro, views 48–96 h × tabela do Studio, 29/10):** 168 de 279 (0–9 views) têm
  "continuaram assistindo" = 100% com 2–5 views → o feed mostrou a 2–5 pessoas, isto é, **não deu o lote de teste**.
  Entre os 98 que receberam o lote, continuaram × views = +0,23 (quase nada); o tercil que menos segura (10–42%)
  ainda tem 53% acima de 500. O 1º lote para em 1.000–1.500 (49 de 67). Quem passou de 2.000 (n 5): % assistido
  72% × 44% dos do platô, 13–24 s × 50–75 s.
- **O que mudou:** nada no código ainda além do T8 (D3) e do placar continuar; a regra está escrita em
  `CORTES_01` (desenho estatístico) para o melhorador/`anime_testes` seguir.
- **Como aplicar/desfazer:** para qualquer comparação A/B nos Shorts, EXCLUIR vídeos com `ret_lista.views_periodo < 20`
  (ou `continuaram == 100 e views_periodo < 10`); métrica primária `pct_media` (porta do 2º lote) e
  `log(views_periodo / mediana do canal)`. Não há nada a desfazer; é regra de análise.
- **NÃO fazer:** tirar conclusão de título/narrador/hora/efeito misturando os não elegíveis (foi isso que fez
  "título não separa", "narrador n pequeno" e "hora sem sinal" nas análises de 28/10). Não usar o campo `views` do
  `metricas()` por vídeo para decidir (D4).

## D2 — Leitor do Studio em lote com impressões de miniatura, CTR e intencionais (ER_02)
- **Dado:** `metricas_studio.json` tinha `continuaram`/`dur_media` em 367/413 vídeos (vinham do `retencao_lista` de
  23/10) e `impressoes` em 2: o `metricas()` por vídeo (3 páginas, 3 vídeos/hora) caía e a aba Alcance de Short
  pequeno vem em branco. Teste real 29/10 02:16 no inovare_ita: a tabela do modo avançado aceita as métricas extras
  (print `D:\postador-de-videos\logs\yt_web\20261029_021608_fable_impressoes.png`); "Mostrados no feed" vem "—" por
  vídeo (até no Total) — não existe por esse caminho.
- **O que mudou:** `D:\postador-de-videos\bin\youtube_studio_extras.py` `retencao_lista` (métricas na URL, parsing
  do FIM da linha com 13 colunas, espera 90 s + 1 recarga, scroll tolerante) e `metricas_rede.py` `coletar_lote`
  (preenche `impressoes/ctr/intencionais` quando vazios; `ret_lista` guarda tudo). Ritmo do lote NÃO mudou (4 canais
  por rodada, canal relido a cada 6 h, mesma trava/sessão).
- **Como desfazer:** voltar `mets` para `("VIEWS","AVERAGE_WATCH_TIME","AVERAGE_WATCH_PERCENTAGE","SHORTS_FEED_IMPRESSIONS_VTR")`
  e o parsing para `t[-3],t[-2],t[-1],t[-5]` com `len(t) < 6`. Backups não existem de propósito (git não há aqui):
  o trecho antigo está citado em `ER_02` e no histórico desta sessão.
- **NÃO fazer:** mudar a ordem/quantidade das métricas na URL sem ajustar o parsing (ele lê do fim: 13 colunas);
  trocar o parsing por cabeçalho (o cabeçalho repete cada nome 4× no DOM); aumentar canais por rodada (rajada no
  Studio = bloqueio, regra da dona).

## D3 — Teste T8 nos Cortes: Short curto (4–5 frases ≈ 20–27 s) × alvo de sempre, 50/50
- **Dado:** D1. Os 5 únicos Shorts acima de 2.000 views têm 13–24 s e 64–89% assistido; o teto de ~1.200 é o lote
  inteiro assistindo metade (44%). Entre os 18 medidos pelo ffmpeg que receberam lote: duração × % assistido −0,43.
- **O que mudou:** `D:\recapd-ambientes\producao\bin\anime_auto.py` (`fazer_short`: sorteio `md5("ct"+id)`, env
  `CORTES_CURTO`; `target_lines = 5 se fonte ≥ 60 s senão 4` quando B e fonte ≥ 30 s), `anime_publish.py` (postar.json
  `curto`), `cortes_ajustes.json` (`curto: "ab"` + histórico), `D:\postador-de-videos\bin\notificar_telegram.py`
  (placar `placar_cortes_testes.json` conta `curto`), `D:\video-fila\linhas\CORTES\TESTES.md` (T8).
- **Como decidir/desfazer:** `cortes_ajustes.json` `curto` = `"A"` (desliga), `"B"` (fixa curto), `"ab"` (teste).
  Regra: ≥ 6 vídeos ELEGÍVEIS por braço por canal; B vence se `pct_media` ≥ 65% em mais vídeos ou mais ≥500/≥1.500
  views. Não decidir por nota do júri nem por "ficou curto demais" a olho: o dado diz que o público assiste inteiro
  os de 13–24 s e não assiste os de 50–75 s.
- **NÃO fazer:** voltar o alvo para 14–18 frases "porque o resumo do parceiro conta a história inteira" (comentário
  de 21/10 no código) sem olhar o placar do T8; abrir T9 (título fixo, narração parcial, loop × CTA) antes do T8
  fechar — cruzar fatores de tela/duração com n pequeno mata os dois.

## D4 — O campo `views` do `metricas()` por vídeo não serve para decidir
- **Dado:** em ≥ 7 vídeos ele está ~10× acima da tabela de 4 semanas e das 48 h (VYUORRjhTe4: 13.000 × 1.285 × 1.286;
  iFZftj2HFZk: 12.000 × 1.206 × 1.204; tjr4YSnDCt4: 22.000 × 2.835 × 1.827). Provável cartão errado na Visão geral.
- **O que mudou:** nada no código (não achei a causa sem abrir a página de novo; o lote já não depende dele).
- **Como aplicar:** usar `medidas_48h` (telegram_estado) ou `ret_lista.views_periodo`. Quem quiser consertar:
  abrir `studio.youtube.com/video/<id>/analytics/tab-overview` de um desses e comparar com o print `metricas_<id>`.

## D5 — Idiomas it/id/ru/th/hi e hipercool: problema de ELEGIBILIDADE do canal, não de hora, título ou formato
- **Dado:** hora local mediana 11–16 h e mediana de views 0 em TODAS as faixas de hora (`hora_idiomas.py`);
  hipercool: 18 de 19 Shorts com "continuaram" lido têm 100% e todos 19 têm < 10 views no período. O viet (mesma
  fonte traduzida) recebe lote (1.418 views, 259 impressões). Então "canal novo de língua" sozinho não explica.
- **O que mudou:** nada (decisão de negócio da dona). Proposta de teste em `ER_04` (trocar 1 Short/dia por conteúdo
  não traduzido e comparar continuaram/views_periodo em 7 dias; conferir avisos de "conteúdo reutilizado" no Studio).
- **NÃO fazer:** mexer em horário, título ou efeitos desses canais esperando views: não há lote para medir.

## D6 — Júri dos Cortes: não ligar o melhorador por nota antes do cruzamento júri × views
- **Dado:** 115 vídeos com nota, 0 com views medidas (agendados de 27/10 19:15 a 04/11). Script pronto
  (`juri_x_views.py`), 1ºs pares na noite de 29/10, ~30–40 até 1/11.
- **Como decidir:** rodar o script; se Spearman nota × pct_media (só elegíveis) < 0,3 com n ≥ 30, o júri não prevê
  e a régua fica D1. Sugestão registrada em `CORTES_05`: verificador "retenção" perguntar "quantos segundos até
  sair" e penalizar > 30 s sem motivo; júri 1 em 2 nos canais que recebem lote.

## D7 — Longo: texto do resumo e das falas por CADEIA de modelos vivos, 1 tentativa por modelo, e "faltou" registrado
- **Dado:** 28/10 o `antigravity/gemini-3.8-flash-tiered` ficou 120–150 s sem responder; o `_post` do claude_client
  repete 3× com timeout 240 s = até 12 min preso por modelo, e o longo saía SEM resumo e SEM falas sem aviso.
  Latência medida 29/10 03:50 (`/v1/chat/completions`, "ok"): tiered 2,5 s, gemini-fila 5,3 s, gemini-3-flash
  4,6 s, agy/gemini-3.8-flash-high 29,7 s, gemini-4-argon pela :20128 > 60 s. Teste ao vivo da cadeia: modelo
  inexistente falha em 0,8 s → próximo responde em 2,7 s.
- **O que mudou:** `D:\recapd-ambientes\producao\bin\claude_client.py`: `generate_text_vivo(prompt, modelos, …)`
  (1 tentativa por modelo, pula 15 min quem falhou — `workspace/ia_saude.json`, cada chamada em
  `modelo_texto.jsonl` com `cadeia`), `CADEIA_TEXTO_LONGO` (tiered → agy 3.8 → gemini-fila → gemini-3-flash; nunca
  Opus/Kiro), `registrar_faltou(pasta, parte, motivo, tentativas)` (grava `faltou.json` na pasta do vídeo + Telegram
  `avisos.enviar(origem="longo", importante=True)`). `anime-pipeline.py`: resumo de abertura e falas de personagem
  usam a cadeia e registram "faltou" quando nada veio.
- **Como medir:** `% de longos com faltou.json` (glob `workspace\**\faltou.json`) e o `modelo_texto.jsonl` (quantas
  vezes caiu para a reserva, latência por modelo). Antes: 0 registro (silêncio).
- **Como desfazer:** voltar as duas chamadas para `claude_client.generate_text(..., model=os.environ.get(
  "GEMINI_TEXTO_VIDEO", "antigravity/gemini-3.8-flash-tiered"))`. Não precisa apagar as funções novas.
- **NÃO fazer:** pôr Opus/Kiro/Fable na cadeia (regra da dona); fazer o "faltou" TRAVAR a postagem (nenhum canal
  1 dia sem postar — ele avisa e registra); subir `max_retries` de volta para 3 na cadeia.

## D8 — Testes e análises no PC1 rodam com prioridade BAIXA (`D:\video-fila\baixa_prioridade.py`)
- **Dado (CORTES_08):** 28/10 21:55 PC1 a 100% (teste de vozes de outra sessão + 44 Chromes + 60 Pythons) e um
  Short travado no ffmpeg; de dia saem 1–4 Shorts/hora contra 4–7 de madrugada. Não há fila nem prioridade entre
  produção e testes.
- **O que mudou:** wrapper `baixa_prioridade.py <comando…>` (BELOW_NORMAL + I/O low, sem janela, o filho herda).
  Regra: todo teste de voz/vídeo/análise de chat ou de sessão roda por ele; a produção (anime_auto, hipercool, fila
  de render) continua em prioridade normal. O Windows dá a CPU para a produção primeiro; o teste só fica mais lento.
- **NÃO fazer:** o contrário (baixar a produção para o teste andar); matar processo de produção; rodar teste com
  Chrome do Remotion em paralelo com o render dos Cortes sem RAM ≥ 3 GB (regra do T5).
- Render pesado dos Cortes fora do PC1: o pipeline já tem "um render pesado por vez" (`anime-pipeline.py` ~752,
  fila do D:\video-fila) e o PC2 roda até 3 Shorts; mover mais exige mexer no PC2 (hipercool) — decisão da dona.

## D10 — QA do vídeo inteiro sem IA no `anime_publish` (`bin\qa_video.py`): avisa, não trava
- **Dado (LONGOS_12):** só 3–4 quadros eram conferidos; preto/congelado/mudo no meio passavam. Teste 29/10 04:40 num
  Short de 46 s: 7 s de varredura, resultado "QA ok (−14,2 LUFS)" (um bug de leitura do ebur128 — pegava o "I:" de
  progresso, −70 — foi corrigido lendo o "Summary").
- **O que mudou:** `qa_video.analisar(mp4)` = 1 passada ffmpeg em 320 px (`blackdetect` ≥ 1 s, `freezedetect` ≥ 6 s,
  `silencedetect` ≥ 4 s < −40 dB, `ebur128` loudness/pico), margens de 0,5 s/1,5 s nas pontas; `qa.json` na pasta de
  saída e `meta["qa"]` no postar.json; Telegram (origem longo/cortes, importante só se grave = preto, mudo, parado ≥
  20 s, duração não lida). `anime_publish.main` chama logo após o probe, em try/except.
- **NÃO fazer:** transformar em trava (regra: só censura trava — "defeito visual não trava"); subir os limiares sem
  olhar `qa.json` de uns 20 vídeos (quadro preto de 1 s pode ser transição legítima: olhar antes de apertar); rodar
  sem o `scale=320` (longo de 75 min ficaria lento).
- **Como medir:** % de vídeos com `qa.ok=false` por semana e se os reclamados pela dona estavam marcados.

## D9 — PRODUTOS: views/curtidas dos Reels medidas pelo cofre (sem API, sem token) e ligadas a cada vídeo
- **Dado (PRODUTOS item 1):** o placar das variações (`config\produto_variacoes.json`) estava todo [0, 0] porque o
  `variacoes.medir` dependia do token da API (venceu) e do `media_id` (postagem pelo navegador não tem). O projeto
  navegador-sem-navegador já lê o Instagram por GraphQL com o cookie do cofre e TLS do Chrome (curl_cffi). Medido
  29/10: a aba Reels dá views por código (12 por página, `page_size` ignorado, mas pagina por `end_cursor`); o feed dá
  data (sem legenda); o Reel aparece 1–3 min depois do `postado_em` (18:23:06 → 18:24; 20:32:57 → 20:35). 1º Reel
  medido de verdade: `De7qqXxsWTt` (disparoemmassa.ia, 25/10) = 0 views, 0 curtidas, variante real `sem_dono`.
- **O que mudou:** `D:\postador-de-videos\bin\produto\medir_web.py` (`medir(placar, log, so)`: por conta, 1 página
  do perfil + reels paginados (≤ 4) + feed = 3–6 chamadas, 25 s entre contas; casa pelo horário (0–20 min depois do
  postado_em, mais próximo; legenda confirma quando vier); grava `placar["videos"]["ig:<codigo>"]` com `views`
  (formato que `contagem`/`escolher` já usam) e `medidas.instagram` no `.json` do vídeo; remede a cada 24 h até 14
  dias; qualquer 401/403/429 = pausa de 24 h (`config\produto_medir_web_pausa.txt`) — não arrisca a conta). Sem
  `curl_cffi` no Python de quem chama, relança a si mesmo por `D:\veo\venv\Scripts\python.exe`. `variacoes.medir`
  chama no fim (a tarefa diária do produto já roda `medir` antes de produzir).
- **TikTok dos produtos:** fica fora — as contas de produto não estão no `reuso_plataformas.json` (TikTok é postado
  pelos notebooks). Quando entrarem, `services.tiktok.studio.TikTokStudio(conta).videos()` dá views/curtidas/salvos
  por vídeo com legenda e hora — mesmo casamento por hora.
- **NÃO fazer:** medir mais de 1× por dia por conta nem tirar a pausa de 24 h no erro (25/10: conta nova em aparelho
  novo foi suspensa; 429 na 1ª chamada do `medir_insta.py` antigo); casar por legenda só (o feed não a traz);
  voltar a exigir token/API (regra: Google/Meta só pelo navegador/cofre).
- **Como medir o ciclo:** `python -m produto.variacoes placar` deixa de ser [0, 0]; `contagem()` passa a separar as
  variantes por conta. Com ~10 vídeos medidos por conta o Thompson começa a puxar.
- **Resultado da 1ª rodada (29/10 02:44):** 10 Reels em 7 contas, todos com 0–2 views e 0 curtidas. Enquanto for
  assim, o Thompson das variantes não tem o que aprender: a linha PRODUTOS tem problema de ALCANCE (conta/
  classificação), não de vídeo. Decisão registrada no `PRODUTOS_…md` item 1: diagnosticar conta × conteúdo antes de
  voltar a otimizar formato/júri. **NÃO** ligar o melhorador dos produtos por nota de júri com esse placar.

## D11 — Curva de retenção por vídeo lida do SVG da aba Engajamento (`_curva_retencao`)
- **Dado (LONGOS_01):** a tabela do modo avançado não aceita dimensão por tempo; a aba Engajamento desenha a curva
  como SVG (ticks 0/40/80/120% e 0:00/meio/fim). Teste real 29/10 03:35: 100 pontos, 117,6% no início, 64% a 30%
  do vídeo, 18% no fim — coerente com "continuaram 63%" e "duração média 0:18" do mesmo vídeo.
- **O que mudou:** `youtube_studio_extras.py`: `JS_CURVA`, `_curva_retencao(pg)`, `ret_aos(curva, fracao)`;
  `metricas()` grava `curva` (50 pontos), `dur_video`, `ret30/ret60/ret10min` (pela curva, quando o cartão não dá),
  `ret_meio`, `ret_fim`. Nenhuma página a mais: aproveita a visita que a 1ª leitura de 48 h já faz.
- **NÃO fazer:** ler a curva em lote para o canal inteiro (não existe por canal; seria 1 página por vídeo, 3/h);
  aprender regra com curva de vídeo não elegível (2–5 views = ruído); mudar a calibração para "pixel fixo" — ela usa
  os ticks de texto justamente porque o Studio muda o tamanho do gráfico.

## D12 — Melhorador CENTRAL: um sistema para todos os vídeos, com conversa e botão (pedido da dona 29/10)
- **Pedido:** chats abertos + sentinela + 4 melhoradores separados trabalhavam um depois do outro; a dona quer um só,
  que analise os vídeos que vão saindo e trabalhe sempre que houver tokens, e que ela possa conversar com ele (ver
  histórico, dizer os pontos que viu, perguntar) por um botão — terminal ou VS Code — e, ao fechar, ele continue.
- **O que mudou:** `D:\video-fila\melhorador_central.py` (feed único de todas as linhas com dados reais → brief por
  linha injetado nas LIÇÕES/`CENTRAL_BRIEF` → pressão → roda SÓ a linha com mais pressão, 1 por passada, prioridade
  baixa, com teste de modelo vivo e RAM; botão único em `controle.json` "melhorador_central"; `ligar --aplicar` liga as
  4 linhas de vez, `desligar` desliga tudo), tarefa `MelhoradorCentral` (10 min, pythonw, `--rodar 9`),
  `conversa_central.py` + `linhas\CENTRAL\` (`CLAUDE.md` = papel, `PEDIDOS_DONA.md`, `HISTORICO.md`, `CONVERSA.md`,
  `DECISOES.md`), botões na Área de Trabalho ("Conversar / Ligar / Desligar Melhorador CENTRAL.bat"). Doc completa:
  `D:\video-fila\MELHORADOR_CENTRAL.md`. Começa **DESLIGADO**, modo sombra.
- **Por que assim (e não um motor novo):** os 4 melhoradores já têm o que importa (alavancas com faixa, revisor
  adversário, vigia de piora, desfazer); o que faltava era UM lugar que decide quem roda, com os dados que decidem
  views (D1/D2/D11) e com a voz da dona. Reescrever os 4 agora seria trocar o que foi testado por algo novo sem dado.
- **Como medir:** `estado\central\estado.json` + `HISTORICO.md`; semana a semana: % elegíveis e % assistido por linha
  (brief) subindo; QA ruim e "faltou" caindo; a dona usando o chat em vez de abrir sessões por linha.
- **NÃO fazer:** rodar duas linhas ao mesmo tempo (CPU/RAM do PC1; é o problema que ela descreveu); pôr Opus/Kiro na
  cadeia das linhas; deixar o central aplicar sem passar pelo revisor de cada linha; tirar o teste de modelo vivo
  (é o que faz "continuar quando volta token" sem chat).

## D13 — Argon inicia sozinho (`D:\gemini-argo\argon_manter.py`, tarefas ArgonManter/ArgonManterLogon)
- **Dado:** 28/10 20:46 o `gemini_http_proxy.py` (:20141) e o túnel `ssh -R` morreram no PC1; a VPS :20133 ficou
  respondendo 502 por 7 h; o `MonitorArgon` dizia "28 contas prontas, funcionando" (mede contas, não o proxy); todas
  as linhas caíram para o Gemini 3.8 em silêncio (a cadeia D7 pelo menos registrou). Teste após subir: "ok" em
  66 s e 44 s pela :20133, modelo `gemini-4-argon`.
- **O que mudou:** `argon_manter.py` (porta local → sobe proxy escondido; `ss` na VPS → recria túnel; estado em
  `argon_manter.json`; Telegram só ao relançar), tarefas a cada 5 min e ao iniciar o Windows.
- **NÃO fazer:** lançar o proxy/túnel por chat (morre com o chat); dois `ssh -R` para a mesma porta (o segundo
  falha com ExitOnForwardFailure — o guardião mata o antigo preso antes de recriar); confiar no MonitorArgon como
  prova de que o Argon responde — a prova é o `argon.log` ("OK … modelo=argon") ou `argon_manter.py --status`.

## D14 — Modelos do central por BOTÃO (Argon / Opus 5.5 / os dois / auto) + bancada "qual Argon chega mais perto do Opus"
- **Pedido (dona 29/10):** Argon enquanto ela gasta o Opus no chat; Opus quando não; botões para trocar e até usar os
  dois; numa aba do painel. E comparar as versões do Argon com o Opus 5.5 e o Gemini na mesma tarefa, com ideias de
  melhorar o melhor Argon.
- **O que mudou:** `config\modelos_central.json` (modo + conjuntos por papel: analista/decisor/revisor; "ambos" =
  Argon decide, Opus revisa; nunca Kiro); `melhorador_central.modo_modelos()` resolve "auto" (Opus só com a dona
  fora do chat — `~/.claude-vscode/sessions` sem sessão ativa há 30 min — e `cota_claude` com_cota ≥ 1) e passa o
  conjunto às linhas pela env `CENTRAL_MODELOS`; os 4 melhoradores (`cortes_melhorador.modelos`, `melhorador_longo.
  modelos`, `produto/melhorador._chamar`, `ccv melhorador.chamar`) usam essa cadeia quando rodam pelo central e a
  própria quando rodam sós. Painel: aba **Modelos da IA (Argon / Opus)** (`/api/modelos_central` GET/POST,
  `/api/bancada_rodar`), com botões, estado em vigor, última bancada e as rodadas do central.
  `bancada_modelos.py`: mesma tarefa real do decisor dos Cortes (júris + alavancas + brief) para cada candidato em
  paralelo, Opus 5.5 responde (referência) e julga anônimo (diagnóstico, alavancas, risco, distância, nota, ideia de
  melhoria por modelo); grava `estado\central\bancada\<data>\BANCADA.md` e acrescenta ao `COMPARACAO_MODELOS.md`.
- **Candidatos vivos em 29/10 04:05:** gemini-4-argon, argon-pro (74 s no "ok"), argon-gemini (121 s), argon-flash
  (29 s), agy/gemini-3.8-flash-high (28 s), antigravity/gemini-3-flash (5 s), cc/claude-opus-5-5 (5 s, com cota).
  Opus 4.6 do Antigravity estourou 150 s: fora.
- **NÃO fazer:** deixar o modo "opus" fixo com a dona no chat (ela sente no crédito — "auto" existe para isso);
  rodar a bancada em produção (ela não aplica nada, mas gasta 1 Opus de referência + 1 de juiz por rodada: não pôr em
  tarefa automática); tirar o filtro de Kiro.

---

## Registro de mudanças posteriores (quem mudar algo acima escreve aqui)
| data | quem | o que mudou | dado novo que justificou |
|---|---|---|---|
| 30/10 13h20 | sessão Hermes (Opus), pedido da DONA | Telão: "SEM CONEXÃO COM O PC1" em tela cheia só com 5 min SEGUIDOS sem alcançar o PC1 (antes: faixa pequena "Verificando a conexão"); `/pc1` do `telao_win.py`/`player.py` = porta 8790 com 8 s, senão ping (sem a 22, que o PC1 não tem; ping do Windows lido em bytes). Instalado nos notebooks e PC2 (Chrome do PC2 estava aberto desde 27/10 com o painel velho); desktop pela `DesktopVigia` 13:08. O `telao_win` do PC2 só pega o código novo quando reiniciar (não se mata pythonw no PC2). Chave `desktop-dona` liberada no PC2/x200ma/acer; PC1 liberado 13h40 (dona rodou `autorizar_desktop.ps1`; PC1 agora tem sshd). 14h20: `painel.html` se recarrega sozinho quando o arquivo muda no disco (HEAD + Last-Modified a cada 5 min) — antes, painel novo só entrava quando o Chrome do telão reabria | dona: "sem conexão aparece toda hora"; PC1 com CPU 100 % e 1,5 GB livres; 8790 passava dos 3 s com o PC1 ligado |
| 30/10 11h30 | sessão Hermes (Opus), pedido da DONA | **D42** (no fim): downloads com prioridade do PC2; longo no PC2 só de reserva; Kaggle baixa sem bloqueio (testado); canal Cozinha Noturna criado | IP de casa é um só para PC1/PC2/x200ma; VPS 209 barrada, Kaggle não |
| 30/10 08h25 | sessão Hermes (Opus), turno da noite | **D41** (no fim): `ERContinuo` (D17) 2 h → 6 h | a ER levou checagem de robô e pausou o yt-dlp do PC inteiro por 120 min (07:40), deixando os Shorts do PC2 sem fonte |
| 30/10 02h25 | sessão Hermes (Opus), turno da noite | **D40** (no fim): enviar/receber arquivo para Windows por HTTP temporário do PC1 (desktop sempre, PC2 se o scp falhar) | Veo perdeu a vez no desktop 00:30/01:34: a foto de referência não chegava por scp |
| 30/10 00h25 | sessão Hermes (Opus), turno da noite (dona: "decida tudo") | **D39** (no fim): alimentador do PC2 (AlimentarPC2, 5 min), CPU só barra com 2+ Shorts, 3 canais antes de desistir; Reel do desktop sem `cd /d` | PC2 trabalhou 20 % das últimas 24 h (1ª análise) |
| 29/10 23h59 | sessão Hermes (Opus), pedido da DONA | **D38b** (no fim): desktop entra por uma vigia (`DesktopVigia`, 10 min) que puxa arquivos por HTTP; telão+medidor instalados lá; medidor do PC1 e PC1 na análise de 24 h; `nsn_colher` do Windows sem `cd /d`. O D31/IMPLANTAR diziam "esperar o ssh estabilizar" | o ssh do desktop cai também pela rede de casa (não é a Tailscale) e comando curto passa às vezes; PC2 trabalhou 20 % das últimas 24 h |
| 29/10 16:25 | sessão PRODUTOS (pedido da DONA) | D9 "não ligar o melhorador dos produtos": LIGADO em modo aplicar, cadeia gweb/gemini-3.1-pro -> argon-pro -> argon-flash | decisão da dona após teste no mesmo vídeo real: com o prompt novo os 3 acertaram o gabarito (formato dono_tres -> peso_variante; ninguém comprou o falso da legenda); as alavancas são botões com faixa + vigia que desfaz. O alcance (D9) continua o problema maior — tarefa 10 do Fable com dados em `linhas\PRODUTOS\alcance\` |
| 29/10 09h | sessão CLAUDE-CODE-VIDEO | `melhorador_central.feed`: ficha de `_postados` com `"ccv": true` vai para a linha `ccv` (antes tudo era `produtos`). `produto\fila.py`: post do CCV agora grava a ficha (`_ccv_ficha`) para o `medir_web` (D9) medir; 7 fichas antigas criadas do `instagram_auto_posted.json` | O CCV JÁ postava no Instagram desde 26/10 (7 posts, `_ccv_postados.json`) mas sem ficha: nunca medido e misturado nos produtos. Desfazer: voltar `out["produtos"]` na linha do feed. |
| 29/10 tarde | sessão Hermes (Fable) | Fecha a parte Windows do D23: PC2 e **desktop** agora com worker nsn + venv próprio (`C:\postador-worker\nsn\venv`; PC2 usa o Python 3.13 do pgAdmin, desktop o Python 3.11). Libs curl_cffi/websocket-client/requests no venv. PC2: 5 contas IG com cookie colhido (`nsn_colher`) → HTTP ativo. Desktop: pronto, sem conta IG ativada nele ainda. x200ma/acer já estavam prontos. | O D23 dizia "não rodar no PC2/desktop antes de haver python no PATH do ssh" e `nsn_tem_cookie`=False no Windows. Resolvido criando o venv manualmente (o `_instalar_nsn_win` exige, mas não cria). SSH do desktop deu "Connection reset" transitório antes de responder. Desfazer: apagar `C:\postador-worker\nsn` nas Windows. |
| 29/10 17h | sessão Hermes (Fable), filha da sessão nsn | **D30** (abaixo): Veo/Flow por HTTP nas máquinas. `maquina_remota.instalar_nsn` agora leva `services/veo_flow/` (flow_gerar com modo worker, flow_http, saude_flow) e cria `saida/` nas máquinas; o `colher.py` passou a imprimir `google_logado=`. O D23 dizia que o worker era só Instagram. | PC2 e x200ma geraram 1 vídeo cada por HTTP com Chrome de 38 s / 51 s (antes: ~33 min por vídeo). |
| 29/10 22h | sessão Hermes (Fable/Opus), filha da sessão nsn | **D33** (abaixo): o D21 dizia "não aumentar posts/dia por causa do HTTP" — a dona REVOGOU com a condição do monitor de banimento; Reels/imagens/Veo agora com teto em `config	etos.json` e rampa automática (monitor_banimento.py, tarefa NSN_Banimento) | pedido da dona 29/10 19:40 ("pode subir mas adicione um monitor... principalmente de imagens") |
| 29/10 23h10 | sessão Hermes (Opus), filha da sessão nsn (pedido da DONA) | **D36** (abaixo): imagens do Flow em notebooks → PC2 (portas extras 9470–9475, várias juntas) → desktop → PC1 por último; antes `nb[:1] + pc1` e o PC2 só com a 9460 livre | 31 de 84 imagens de 29/10 saíram no PC1 e 7 no PC2, com o PC2 a 6 % de CPU |
| 29/10 22h50 | sessão Hermes (Opus), filha da sessão nsn | **D35** (abaixo): `gera_imagem.gerar_imagem` filtra as máquinas livres como o `tentativas` (telão/vez) e a 2ª conta não repete máquina pulada/que falhou; erro diz a causa; `pedidos_falhos.jsonl` novo. O D30/D33 diziam que o limite era "conta ocupada/Chrome fechado" sem causa | ~15 de 28 erros de 29/10 eram o acer no telão com as 2 contas indo nele; ~8 a tela do x200ma antes do HTTP (D30) |
| 29/10 18h | sessão Hermes (Fable) | **D31** (abaixo): todo o nsn roda em qualquer máquina com os cookies dela (`core/maquinas.py` + `Remoto.nsn_run`); `postar_insta_auto.postar_navegador` passou a tentar o HTTP NA MÁQUINA antes do HTTP do PC1 (o D23 dizia PC1 primeiro). | O caminho das máquinas do D23 nunca tinha rodado: o `instagram_auto.log` não tinha nenhum "HTTP no" — o HTTP do PC1 vencia sempre. |

## D32 — Longo: pedidos já na fila recebem os narradores por grupo; 1º narrador cobre resumo + começo (29/10 noite)
- **Dado:** pedido.json guarda a lista de vozes do dia em que foi enviado. 5 pedidos de 27–29/10 tinham listas antigas
  (Patrick Estrela, 10 vozes de jogo); o Top Fighter (27/10, render 29/10) é o exemplo que a dona reprovou.
- **O que mudou:** `D:\recapd-ambientes\producao\colab\corrigir_pedidos_fila.py` (reescreve só pedidos livres; pula
  em andamento e os já "grupos"); `bin\anime_tts._inicios_blocos` soma `ANIME_RESUMO_N` ao 1º bloco.
- **Como desfazer:** tirar a soma de `n_res` em `_inicios_blocos`; os pedidos não têm volta (a lista antiga está no
  `teste_narradores.json` antigo `.bkp_20261029_1717`).
- **NÃO fazer:** rodar o script com pedido em andamento no Kaggle (ele pula, de propósito).

## D38 — Longos, madrugada de 30/10: o que mudou no render, na fila do Kaggle e no conteúdo (detalhe em LONGOS_13 §5f)
- **Kaggle cortando render (Pastor):** `colab\kaggle_trabalhador._cabe` — só pega pedido que cabe em 11,5 h de sessão
  (roteiro × 24 s/frase; sem roteiro = 7 h). Dado: Pastor pego com 6,5 h de sessão, cortado às 12 h no acabamento.
  Desfazer: tirar o bloco `if pid and not _cabe(pid)` em `loop()`. Backups `.bak_20261030_cabe` nas 4 centrais.
- **Disco cheio no fim:** `anime-pipeline.run_one` apaga trechos e vídeo sem legenda antes do master/cortes (master e 5
  cortes do Pastor: "Conversion failed" ao fechar o arquivo).
- **Acabamento:** `longo.json` `ANIME_PRESET_INTER`/`ANIME_PRESET_LEGENDA` = veryfast (medido: acabamento do Top
  Fighter 2h45 de 4h44). Vazio = como antes.
- **Engenharia reversa → aplicado** (`referencias\PADROES_COMUNS.md`, 14 recaps, 3 com 450k–2,1M): título na tríade
  humilhação→virada→vingança (`seo_generator`, só longo pt); fala do clone +10% (`longo.json CORTES_FALA_DELTA=10`;
  topo 200–230 palavras/min × Pastor ~144); mini-gancho a cada 15 min (`_ganchos_longo`, `longo.json ganchos`);
  capítulo ~22 min "Comente PARTE 2" (`capitulos.parte2`). Proposto como próximo A/B: CTA fora dos 15 primeiros min.
- **Hipercool → longo:** zoom mirando o rosto (`fx_clips._rosto_no_trecho`, YOLO de rosto do hipercool,
  `ANIME_FX_ROSTO=1`, ~1% do render).
- **Conferência automática:** `linhas\LONGOS\conferir_pedidos.py` + tarefa `ConferirLongos` → CONFERENCIA.md,
  Telegram e brief do central. Pastor: 10/12 (reação da mascote veio depois; master refeito no PC).
- **NÃO fazer:** voltar o respiro entre falas por causa da fala +10% (o respiro foi aprovado pela dona e não mudou);
  tirar o "para no 1º bloqueio" do `engenharia_reversa.py` (13 consultas seguidas = rajada, regra da dona); pôr o rótulo
  do metadado sem "metad" (sai pelo IP de casa).

## D37 — Mascote reagindo no lugar de metade dos memes em tela cheia; CTA nunca usa gravação de reação (29/10 23h30)
- **Dado:** havia 2 gravações de reação dela andando (raiva, riso) sem uso; o reserva do CTA podia escolher uma delas.
- **O que mudou:** `bin\mascote_overlay.reacao_viva`; `bin\anime-pipeline._memes_resumo` (j ímpar das interrupções,
  ≤ 3 por vídeo); `pausa_viva`/`gravacao_viva` excluem `reacao_`. Detalhe em LONGOS_13 §5f.
- **Como desfazer:** tirar o bloco `if j % 2 == 1` em `_memes_resumo`. **Medir:** retenção no ponto da reação × meme.

## D34 — Mascote: Veo por HTTP no PC1 ANTES dos notebooks; 6 vídeos por rodada (29/10 noite)
- **Dado (`mascote_waifu_v2\veo.log`):** o HTTP do PC1 entregou em 16–17 s (20:56 e 22:35). As falhas e a demora vinham
  da ordem da cadeia: notebooks primeiro, onde o login de emersonjosiel2027 venceu (HTTP + Chrome lá = 2–4 min perdidos
  por máquina; no x200ma o Chrome gerou IMAGEM). Teste 22:35 com a ordem nova: 16 s no Veo, 317 s com o recorte.
- **O que mudou:** `linhas\LONGOS\bench\veo_mascote.py` chama `gera_auto._gerar_http` antes de `gera_auto.gerar` (conta
  que não é só-notebook); `mascote_producao.bat` `--videos 2` → `6` (3 rodadas/dia = até 18/dia, dentro do teto do D33).
- **Como desfazer:** tirar o bloco `_gerar_http` do veo_mascote; voltar `--videos 2`.
- **Falta (não é código):** renovar o login do Flow da emersonjosiel2027 no x200ma e no Acer (o cookie de lá venceu).

## D15 — "Navegador sem navegador" em produção: Studio por HTTP no lote + monitor de saúde com aba no painel (dona 29/10)
- **Pedido:** implantar os sistemas do `D:\projeto-navegador-sem-navegador` na produção, com forma de monitorar se estão
  MESMO funcionando (é invisível: não abre janela) e logs no painel; o melhorador deve acompanhar.
- **O que mudou:** (1) `metricas_rede._studio_http(slug)`: teste quieto do cookie (`D:\gemini-argo\cookies_youtube`)
  e, vivo, `StudioAnalytics.videos()` → views, % assistido, duração média, continuaram, impressões/CTR de miniatura e
  **mostrados no feed** (que a tela não dava) em ~4 s por canal, SEM Chrome; `coletar_lote` usa isso e só abre o
  Chrome se o cookie morreu (que também renova o login). (2) `tools\saude.py` (nsn): a cada hora testa por HTTP, sem
  nunca abrir Chrome, TODOS os canais do YouTube e amostra rotativa de TikTok (6)/Instagram (3) + Fotos/Flow; grava
  `relatorios\saida\saude.json` e `logs\saude.jsonl`; Telegram só quando muda (caiu/voltou). Tarefa `NSN_Saude`.
  (3) Painel: aba **Sem navegador (HTTP)** (`/api/nsn`): por serviço/conta vivo×morto, desde quando, último vivo,
  uso na produção (linhas "por HTTP" do metricas_rede) e o log dos testes. (4) Brief do melhorador central mostra a
  saúde e os mortos. 1ª rodada 07:13: YouTube 29/30 vivos (o `manter_cookies` com rotação funciona), TikTok 4/6.
- **NÃO fazer:** deixar o `saude.py` ressincronizar (abrir Chrome) — ele só mede; quem renova é a produção (Chrome do
  lote) ou `youtube_http.py sync`; aumentar a amostra de TikTok/Instagram por hora (risco de conta).

## D16 — Teste T9: fala rápida (+15 pontos %) × como sempre (pedido da dona 29/10: "variantes, sobrevive o melhor")
- `anime_tts._frase_v2` lê `CORTES_FALA_DELTA` (só no clone); `anime_auto` sorteia `md5("fr"+id)`; `postar.json`
  `fala_rapida`; placar conta. `cortes_ajustes.json` `fala_rapida: "ab"`, `fala_delta: 15`. A dona reprova de ouvido →
  `"A"`. Decisão como os outros testes (CORTES_01 item 3): elegíveis, pct_media, P(B>A) ≥ 0,95, n ≥ 12.

## D17 — Engenharia reversa CONTÍNUA com prioridades da dona no painel (pedido 29/10)
- `D:\video-fila\engenharia_reversa\continuo.py` (tarefa `ERContinuo`, 2 h; sem IA): (1) prioridades do painel
  (`config\er_prioridades.json`): canal → lista pelo `anime_discover.discover_canal` (cache/proxy/ytdlp_vez) → baixa
  top N e baixo N (480p, pausa 90 s, para no bloqueio, D ≥ 5 GB) em `amostras\prioridade_<nome>\`; vídeo → só ele;
  depois `medir.py` e a comparação top × baixo em `RESULTADOS_CONTINUO.md`; (2) todo `source.mp4` novo do Cortes
  ganha `fonte_medidas.json` (o pipeline/júri/brief sabem como é a fonte antes de cortar) + `medidas_fontes.jsonl`;
  (3) sem prioridade: amostra de fundo (`amostra.py --n 2 --max 4`); (4) `medir.py` + `medir_nossos.py`; (5) Telegram
  rotina. Painel: aba **Engenharia reversa** (`/api/er`, `/api/er_prioridade`): campo para colar canal/@ ou vídeo,
  fila com estado, resultados, log.
- **NÃO fazer:** rajada de downloads (1 por vez, pausa) — o IP de casa já foi bloqueado 2× em 28/10; baixar com D < 5 GB;
  trocar as medidas por opinião de IA (a régua é número; a IA entra só no `aprendizado.py`, que continua separado).

## D18 — Kwai: postar pelo app Android no Redroid da VPS, não pelo navegador (dona 29/10: "já temos o app e emuladores")
- **Dado:** `www.kwai.com` (site e PWA do atalho "Kwai") é só de assistir: `/upload`, `/creator/upload`,
  `/creator-center/upload` → 404, nenhum `input type=file`, mesmo logado (sondas 29/10 em jornalcomia e canalalucinaai,
  prints em `D:\hipercool-materiais\testes_kwai`). O que existe: 49/56 contas Kwai criadas via Google
  (`D:\projetos-navegador\credential-factory\kwai_contas.json`) e o Redroid (Android em Docker) na VPS hermes-bloqueio
  (`D:\whatsapp-activator2\vps-redroid`, Play Integrity ok em 26/10, app Toque para clicar).
- **Decisão:** o postador do Kwai é `D:\postador-de-videos\bin\kwai_redroid.py`: liga o contêiner, `adb push`,
  intent SEND para o app do Kwai, Toque confirma, `uiautomator dump` confirma, registra em `etapas.py`. Uma conta por
  Redroid. **Bloqueio que só a dona resolve:** instalar o Kwai pela Play Store do Redroid e logar (OAuth/SMS). Até lá
  `--sonda` só diagnostica. Detalhes: `D:\postador-de-videos\PLATAFORMAS_NOVAS_PENDENTE.md` §1.
- **Não fazer:** APK de terceiros; Kwai no Redroid enquanto o `manter-vivo.sh` do WhatsApp roda (ele desliga o
  contêiner no fim); mais de 1 conta no mesmo Android.

## D19 — yt-dlp com runtime JS (node) por config do usuário; cookies do Instagram colhidos para o nsn (29/10)
- **Dado:** a regra antiga de memória era "não mexer em opção/cookie do yt-dlp" (as rajadas e cookies é que causaram
  bloqueio). A dona disse que não entende a regra e perguntou do aviso. O aviso "some formats may be missing" é por
  falta de runtime JS, não de cookie.
- **Decisão:** `%APPDATA%\yt-dlp\config` com `--js-runtimes node:"C:\Program Files\nodejs\node.exe"` (vale para todos os
  projetos, sem tocar nos scripts; testado: "Solving JS challenges using node"). A regra "1 download por vez, sem
  cookie" continua. Instagram: `D:\projeto-navegador-sem-navegador\tools\colher_instagram.py` copia o cookie das
  contas logadas no cofre para o nsn (29/10: 9 colhidas + 12 que já tinham = 21 contas; faltam inovareagenda,
  inovareclone, inovarecrm, inovaresites (não estão no cofre) e msenergysolar.pa (deslogada) — da dona).
- **Não fazer:** cookie do YouTube no yt-dlp; rodar o colhedor com um Chrome do mesmo perfil aberto.

## D20 — Celular como proxy (IP de operadora) para testar as contas TikTok mortas (dona 29/10)
- **Dado:** 54 das 58 contas TikTok têm 0 views em 48 h em todos os posts recentes (`telegram_estado.medidas_48h_tiktok`,
  29/10); vivas só aulasrevolution, emersonjosiel2029, doramanoturno, filmenoturno. Todas postam por IP de datacenter
  (Webshare) ou de casa. Residencial grátis de verdade só existe o de casa e o de um celular com chip.
- **Decisão:** `D:\postador-de-videosin\proxy_celular.py` sobe `ssh -D 127.0.0.1:18210` até o Termux do Redmi A3
  (Tailscale 100.87.168.9:8022), mede a saída (IP, operadora, móvel?, igual ao de casa?) e grava em
  `config\proxy_celular.json`; tarefa **ProxyCelular** a cada 5 min. `postar_tiktok_auto.abrir_conta` manda pelo celular
  só as 6 contas em `contas_teste` (jornalcomia, canalhistoriacomia, canalalucinaai, entrevistacomia,
  inovaremanhwaverseesp, gameoftroneskingsroadbrasil) e só se `vivo()`: túnel medido há < 15 min, saída DIFERENTE do IP de
  casa, MB do dia < `mb_dia` (300). Fora disso, caminho normal. Teste = 7 dias: se essas 6 saírem de 0 views e as outras
  48 não, o IP é a causa e vale chip/celular por conta.
- **Depende da dona:** celular ligado com o Tailscale aberto (está offline há 5 dias), Termux com sshd por chave
  (passo 2 de `docs\CELULARES_ANDROID.md`), um chip com dados e o Wi-Fi do celular DESLIGADO (no Wi-Fi a saída é o IP de
  casa e o teste não vale: `igual_casa=true` bloqueia).
- **Não fazer:** like/view/comentário pelo celular; mais de 1 plataforma ao mesmo tempo pelo mesmo chip; senha no Termux.

## D21 — Instagram: o Reel sai por HTTP (nsn) e o Chrome virou reserva (dona 29/10: "implantar na produção")
- **Dado:** `services\instagram\postar.py:reel` provado em recenas.ia (29/10, DfE3hruzPD7); 21 contas com cookie colhido
  no nsn; o postador ainda abria o Chrome do cofre para toda conta sem token da Graph API.
- **Decisão:** `postar_insta_auto.postar_navegador` tenta primeiro `postar_http` (subprocesso no venv do Veo, que tem
  curl_cffi, janela oculta); confirmou "reel ok" = postado por HTTP; qualquer outra coisa = Chrome como antes. Liga/desliga:
  `instagram.postar_http` no reuso; por conta: `sem_http: true`. O mesmo PC, IP e User-Agent do Chrome do cofre, como o
  nsn exige. Teto da produção continua 2 posts/dia por conta.
- **Não fazer:** testar à mão em recenas.ia (está em `feedback_required` por excesso de testes em 28-29/10); copiar o
  cookie para outra máquina; aumentar posts/dia por causa do HTTP.

## D22 — YouTube: upload por HTTP só com "visita de token" do Chrome; não há token por HTTP puro (29/10)
- **Dado:** o `sessionInfo.token` do Studio vem da cadeia `att/esr` (challenge do BotGuard) → `get_web_reauth_url` →
  `ars/grst`. O token e o `ctx` não aparecem no HTML do Studio buscado por HTTP. Logo o nsn só envia (upload_http, provado
  em gamenoturno 29/10 05:15, vídeo privado) depois que um Chrome do canal abriu o Studio com o ouvinte passivo ligado.
- **Decisão (a fazer, com ok da dona porque mexe no caminho principal do YouTube):** (1) `tools	oken_studio.py`: abre o
  Chrome do cofre escondido no Studio do canal por ~15 s só para o ouvinte gravar `yt_sessao_<slug>.json`; (2) medir a
  validade do token (hoje "≥ 1 h", não medida); (3) `youtube_web_poster.subir` tenta `upload_http` quando há token fresco
  e cai no Chrome se não; (4) completar o que o HTTP não faz: "conteúdo alterado (IA)", capa, playlist, linha STATUS;
  (5) apagar os 2 vídeos privados de teste. Ganho: Chrome de minutos para segundos por canal, e 1 visita serve vários
  uploads enquanto o token valer.
- **Não fazer:** tentar fabricar o challenge do BotGuard; subir público direto (regra: sempre agendado).

## D23 — nsn em CADA máquina, com os cookies dela (dona 29/10: "cada PC tem seus próprios cookies, cada um posta com eles")
- **Dado:** a regra "nunca copiar cookies entre máquinas" continua. Notebooks (x200ma, acer) têm 2 GB de RAM e cada Chrome
  gasta ~600 MB; o postador do PC1 comanda o Chrome deles por ssh. Sem pip neles (Ubuntu 24.04 sem ensurepip).
- **Decisão:** `tools\empacotar_worker.py` (nsn) gera `dist
sn_worker` = código + `modelos_ig.json` (doc_ids SEM
  fb_dtsg/lsd/jazoest) + `colher.py`; `python bin\maquina_remota.py instalar-nsn [maq]` instala em `~/postador-worker/nsn`
  preservando `cookies/` de lá. curl_cffi/websocket-client foram instalados descompactando wheels (cp312 manylinux) no
  user-site, sem pip. `colher.py` lê os cookies do Chrome LOCAL (porta 9460 do chrome_conta) e grava lá.
  No PC1: `postar_insta_auto.postar_http_remoto` posta o Reel por HTTP NA máquina que já tem o cookie (vídeo + capa +
  medidas vão por ssh; o Acer não tem ffmpeg: `reel()` lê `<video>.meta.json`/`.capa.jpg`), sem ocupar a vez do Chrome;
  depois de todo post pelo Chrome de lá, `nsn_colher` grava o cookie para a próxima vez ser HTTP.
- **Ganho:** Reel sem Chrome nos notebooks (0 RAM extra, roda mesmo com o telão passando vídeo), Chrome só para
  renovar login. Ordem: HTTP local (PC1) → HTTP nas máquinas da conta → Chrome nas máquinas → Chrome no PC1.
- **Não fazer:** copiar `cookies/` entre máquinas (nem para o PC1); rodar o worker no PC2/desktop antes de haver python
  no PATH do ssh (PC2) — por enquanto `nsn_tem_cookie` devolve False no Windows e segue o Chrome.

## D24 — Argon: gerenciamento fora do caminho do pedido (dona 29/10: "melhore o gerenciamento, as contas, a estabilidade")
- **Dado (argon.log 27–29/10):** 106 ressincronizações de cookie pelo Chrome DENTRO do pedido (mediana 78 s, p90 1 h; um
  "responda ok" levou 226 s); 220 linhas "desbloqueada após 30 min" porque o desbloqueio nunca era gravado; no modo stream
  um erro antes do 1º pedaço não tentava outra conta; `mcp_argon.py` apontava para a porta 20140 (ninguém escuta);
  ProbeArgon ficou sem próxima execução; latência do modelo em si: mediana 15 s, p90 72 s (essa fica).
- **Decisão:** `gemini_argon.py`: trava nas gravações, desbloqueio gravado, sucesso limpa `bloqueada`, `stats` por conta,
  `marcar_cookies` (conta com cookie morto sai da fila: `cookies_mortos_ate`), `confirmar_volta`. `gemini_http.py`:
  1 Session por conta, grava só cookies que mudaram, cookie morto = `TrocarConta` (próxima conta na hora; Chrome só se não
  houver outra pronta), stream tenta a próxima conta antes do 1º pedaço, prazo total 580 s, 4xx limpa tokens, log com
  rotação e linha OK também no stream (com "gestão Ns"). `gemini_http_proxy.py`: vaga com prazo (503), erro no stream vira
  evento de erro, `/cota` mostra cookies_mortos/sem_cota. `argon_manter.py`: /health com prazo, derruba proxy preso,
  confere e reinicia o :20133 da VPS. **Novo `argon_zelador.py`** (tarefa ArgonZelador, 5 min; substitui ProbeArgon): confere
  cookies por HTTP, renova os mortos pelo cofre em segundo plano (6 por passada, RAM ≥ 3 GB) e aplica a REGRA DA DONA:
  conta cuja cota "voltou" recebe um "oi" individual (fica no chat da conta) antes de voltar à fila; Flash-Lite = ainda sem
  cota, hora exata do Google entra na fila; voltou = `voltou_em` + aviso Telegram. Fila (não rodízio) mantida como a dona
  pediu em 27/10.
- **Não fazer:** ressincronizar dentro do pedido quando há outra conta pronta; mudar o nível de raciocínio; girar
  1PSIDTS por HTTP (testado 29/10: accounts.google.com não devolve o init para o Gemini).

## D25 — Antigravity/Opus "rodando e não responde" e Claude web lento: a causa é o proxy de saída na VPS 209 (29/10)
- **Dado:** o OmniRoute (VPS 157) manda o tráfego de 123 contas (111 do Antigravity) pelo tinyproxy da VPS 209
  (`209.145.60.53:8888`). Esse tinyproxy está com `Allow 0.0.0.0/0` (proxy ABERTO na internet) e `MaxClients 100`: em 29/10
  havia 4 IPs externos (45.156.87.95, 45.153.34.67, 91.92.47.96, 65.108.40.195) com centenas de conexões, o journal mostra
  "Maximum number of connections reached. Refusing new connections", e no OmniRoute: 13.600 erros + 905 timeouts do
  Antigravity em 2 h, "Proxy unreachable", refresh de token falhando, Opus 499/504 em TODAS as contas desde 28/10 ~19h.
  Não é ordem de contas nem cota: é o funil.
- **Decisão:** a correção é na VPS 209 e é de segurança (a dona roda mudanças de segurança lá, regra de 03/10):
  `Allow 127.0.0.1` + `Allow 157.173.207.22` (tirar o 0.0.0.0/0), `MaxClients 400`, reiniciar o tinyproxy. Depois conferir
  no OmniRoute `proxy_logs` (status success voltando) e o Opus respondendo. A ordem de contas por modelo o OmniRoute já faz
  ("Model-only lockout for antigravity:<modelo>"); o combo_opus_fila (cron) só verá "vivas" quando o funil abrir.
- **Não fazer:** mexer nas atribuições de proxy no banco do OmniRoute por conta própria; abrir mais portas na 209.

## D26 — Claude web (cw/ no OmniRoute): monitor, renovação em vez de duplicar, e a lentidão é o funil da 209 (29/10)
- **Dado:** 3 contas claude-web (grátis, sessões vencem juntas em 25/11); em 24 h 1 ok / 40 erros (429 do plano grátis e 502
  de 50 s pela saída); um pedido curto direto respondeu em 1,6 s. O cadastro antigo sempre criava conta nova (duplicava).
- **Decisão:** `D:\sonnet web\monitor_sonnet_web.py` (tarefa SonnetWebMonitor 1 h) + `ler_claude_web.py` na VPS (só
  leitura) → `estado.json` → painel (aba Modelos) e Telegram. `cadastrar_omniroute_vps.py` atualiza pelo nome
  (PUT apiKey). Renovação das sessões escalonada antes de 25/11, pelo PC2 (pegar_cookies).
- **Não fazer:** cadastrar sem `--simular` antes; copiar `segredos\cookies.json` para outro lugar; mexer no tinyproxy da
  209 sem a dona (D25).

## D27 — "Oi" individual também no Opus 4.6 (Antigravity) e tarefas que morriam no pythonw (29/10)
- **Dado:** o sondador por conta já existia na VPS (`/opt/omniroute/probe_opus.py`, cron 5 min, cópia em `D:\gemini-argo`):
  manda "oi" só na conta que voltou (reset da cota ou fim da pausa). Mas usava timeout de 10 s (Opus com thinking leva
  10–30 s mesmo para "oi" → conta sã virava "travou" e ficava 20 min pausada) e não guardava a hora em que cada conta voltou.
  E no PC1, 126 scripts chamavam `sys.stdout.reconfigure` sem guarda: sob `pythonw` (tarefa agendada) `sys.stdout` é None
  → ArgonZelador, MelhoradorCentral, NSN_Saude, ERContinuo, ProxyCelular, SonnetWebMonitor terminavam com resultado 1.
  ssh em tarefa sem stdin também travava (90 s) → `ssh -n`.
- **Decisão:** `probe_opus.py`: timeout 40 s, 6 contas por passada, resultado por conta no log e
  `/opt/omniroute/probe_opus_voltas.json` (`voltou_em` = 1ª resposta "viva" depois de não-viva, histórico das últimas 10).
  `ler_claude_web.py` (VPS) devolve esse resumo; `monitor_sonnet_web.py` grava em `estado.json`; painel (aba Modelos):
  "Opus 4.6: vivas agora / ativas, pausadas, 3 h ok/erros, últimas voltas". Guarda `if sys.stdout:` em todos os scripts;
  `-n` nos ssh de tarefa. Enquanto o funil da 209 (D25) estiver fechado, nenhuma conta do Opus responde ao "oi".
- **Não fazer:** baixar o timeout do "oi" de novo; sondar pela fila (só testaria a primeira conta); criar tarefa nova sem
  conferir "Último resultado" 0.

## D28 — Nenhuma janela na tela: sitecustomize em todos os Pythons (dona 29/10, 2ª vez: "já disse pra colocar oculto")
- **Dado:** janelas de ssh.exe e python.exe continuavam aparecendo. Causa: processos SEM console (pythonw das tarefas:
  postar_longos, youtube_studio_extras, tunel_painel, gera_auto via cron) abrindo filhos de console sem CREATE_NO_WINDOW;
  o `sem_janela` só vale para quem o importa, e dezenas de scripts não importam.
- **Decisão:** `D:\hipercool-materiais\comum\sitecustomize.py` instalado no site-packages do Python313 e dos venvs
  (veo, recapd, hipercool, manhwa-react, historias) por `bin\instalar_sitecustomize.py`. Só age quando o processo atual
  NÃO tem console (GetConsoleWindow()==0): aí todo subprocess sem flags ganha CREATE_NO_WINDOW e os netos herdam.
  Terminal interativo não muda. Provado sob pythonw: filho python sem janela. Venv novo = rodar o instalador de novo.
- **Não fazer:** tirar o sitecustomize de um venv "porque não precisa"; usar `start`/cmd em .bat de tarefa (cria console).

## D29 — Claude web e Cline: a rotação estava OK; o que faltava era reordenar as contas cw (29/10)
- **Dado:** o combo sonnet-fila (prioridade) = cw/claude-sonnet-5-5 -> claude/claude-sonnet-5-5. O provedor claude-web tem
  18 contas ativas e o OmniRoute JA roda por prioridade (fill-first) em todas. Não era falta de conexão. O problema: contas
  que só davam 403/429/502 ficavam na frente (seebotsia prio 1 = só 403), o combo caía cedo no Claude Code e esse esgotou
  ("sonnet web parou por falta de token"). Os 502 vêm do proxy saturado da 209 (D25); os 429 são o limite do plano grátis.
- **Decisão:** `D:\sonnet web\ordenar_contas_cw_vps.py` (cópia /opt/omniroute/ordenar_contas_cw.py, cron 2 min, espelha o
  ordenar_contas_opus): contas que respondem 200 vão para a frente, 403/caídas/limitadas para o fim. Aplicado: seebotsia
  foi do 1º para o 18º; inovaremanhwaverse/aulasrevolution (deram 200) para o topo. O monitor_sonnet_web + aba Modelos já
  mostram o estado das 18.
- **Cline Opus 5.5 "começou e parou":** NÃO é defeito da ponte (cline-ponte, saúde ok, túnel ok, login válido). A conta
  Cline ficou com saldo NEGATIVO: "Insufficient balance. Your Cline Credits balance is $-1.47" -> a API responde 402. Só a
  dona resolve (recarregar créditos no Cline). A ponte reporta o 402 certo.
- **Não fazer:** mexer no proxy da 209 sem a dona; achar que cw não rotaciona (rotaciona); usar o Cline sem saldo.

## D30 — Veo/Flow por HTTP NAS máquinas: o Chrome do notebook/PC2 só fabrica o token do reCAPTCHA (dona 29/10: notebooks e PC2 fazendo por HTTP o que o PC1 já faz)
- **Dado (29/10, `D:\postador-de-videos\logs\maquina_remota.log`):** ~900 aberturas de Chrome em 2 dias nos notebooks/PC2
  (x200ma 399, pc2 319, acer 185), a maioria do Veo/Flow, até ~33 min cada (Playwright gerando o vídeo pela tela). Nos
  notebooks de 2 GB isso é a RAM inteira. O `flow_gerar.py` (HTTP + token pela armadilha, provado 28/10 na mundosolar) só
  rodava no PC1, dependendo do `contas.py`/`gera_imagem` do Veo.
- **Decisão:** o `flow_gerar.FlowGerador` ganhou o **modo worker** (`--porta 9460 --projeto <url> --nome <perfil>
  --fechar-chrome video @prompt.txt saida.mp4`): nada do Veo é lido na máquina; o Chrome do perfil é aberto pelo PC1 como
  sempre (`maquina_remota.tentativas` → `chrome_conta.py`, 1 Chrome por vez), o worker abre uma aba com a armadilha, pega o
  token, manda o pedido por HTTP (`FLOW_PEDIDO_OK`) e **fecha o Chrome na hora** (`chrome_conta.py fechar`, `FLOW_CHROME_SOLTO`);
  a espera do vídeo e o download são HTTP puro; o mp4 volta por scp (`Remoto.receber`). Cada geração também grava
  `cookies/cofre_<perfil>.json` lá (colheita sem Chrome a mais) — o cookie nunca sai da máquina.
  - Veo: `cadeia_veo.http_remoto(rem, ...)` chamado em `gera_auto._gerar_nos_notebooks` ANTES do Playwright, em cada
    máquina da etapa. Ordem: **HTTP na máquina → Chrome na máquina** (→ PC1, como antes). Estados: ok / pular (falhou
    antes de pedir = Chrome segue) / pediu (o Flow aceitou e o arquivo não veio = crédito gasto, NÃO repete no Chrome) /
    sem_credito / login. O saldo lido vai na linha `[CREDITOS] saldo lido no menu de conta: N` (o `creditos_contas` já lia).
  - Interruptores: `config.FLOW_HTTP_REMOTO` (env `FLOW_HTTP_REMOTO=0` desliga tudo), `config.FLOW_HTTP_FECHAR_CHROME`,
    por conta `contas.SEM_HTTP` (ou `"sem_http": True` na linha da conta). Conta sem projeto salvo em
    `logs\flow_projetos.json` segue o Chrome (que cria e salva o projeto); da próxima vez é HTTP.
  - Saúde (D15): `saude_flow.py` roda em cada máquina (1 ssh, `Remoto.nsn_flow_saude`) e cada perfil entra em
    `saude.json` como `flow <perfil>@<maquina>`; a aba **Sem navegador (HTTP)** ganhou a tabela "Flow (Veo) por máquina"
    e lê "Flow por HTTP" do `maquina_remota.log` no uso em produção. No PC1 `cookies/flow_<conta>.json` é renovado a
    cada geração (`FlowGerador.colher`) ou com `flow_gerar <conta> colher` (a seebotsia dava "cookies vencidos" só porque
    o arquivo era velho; renovado 17:29, créditos 10). Comandos: `maquina_remota.py saude-flow [maq]`,
    `colher-flow <perfil> [maq]`, `instalar-nsn [maq]`.
- **Medido (29/10, 1 vídeo real em cada, 9:16 8 s h264 720x1280 + aac):**

  | máquina | conta | Chrome aberto | pedido aceito | total até o mp4 no PC1 | mp4 |
  |---|---|---|---|---|---|
  | PC2 (Windows) | emersonjosiel2032 | **38 s** (chrome.log do PC2: 17:27:15 → 17:27:54) | 14 s | 77 s | 3,0 MB |
  | x200ma (Linux 2 GB) | inovaremanhwaverse2 | **51 s** | 18 s | 114 s | 4,5 MB |

  Antes: até ~33 min de Chrome por vídeo. O saldo caiu 510 → 490 no PC2 (20 créditos = 1 vídeo Fast, como no Chrome).
  **Imagens (29/10 17:39, pedido da dona "já existe feito nesse PC, é só fazer funcionar lá"):** `gera_imagem._gerar_http_remoto`
  (chamado em `_gerar_na_conta` antes do Playwright de cada máquina; `Remoto.nsn_flow_imagem`, refs vão por ssh). Prova: PC2,
  emersonjosiel2032, Nano Banana 2.1 9:16 → Chrome aberto **47 s**, total 52 s, png 703 KB (768x1376), via `http:pc2` no log.
  Pedido aceito e arquivo não veio = `_PediuSemArquivo` (não repete na tela nem em outra máquina).
- **NÃO fazer:** copiar `cookies/` entre máquinas (nem para o PC1); tirar o caminho do Chrome (é a reserva — `cadeia_veo`
  cai nele em qualquer falha antes do pedido); rodar dois Flows na mesma máquina (o `chrome_conta.py` segue com 1 Chrome por
  vez e o worker usa a porta 9460 dele); repetir no Chrome um pedido que o Flow já aceitou por HTTP (gasta 2×); colher em
  massa abrindo Chrome em 50 perfis por máquina (a colheita acontece sozinha a cada vídeo); o desktop ficou de fora em
  29/10 (ssh sem resposta): rodar `instalar-nsn desktop` quando voltar.

## D31 — "Roda onde o cookie está": todo o nsn em todos os notebooks e PCs (dona 29/10: "tudo isso tem que rodar em todos os notebooks e PCs")
- **Dado (29/10 18h):** só o Reel (D23) e o Flow (D30) tinham caminho para as máquinas; carrossel/story/perfil/DM/
  comentários (`services/instagram/postar.py`), robô QUERO (`tools/quero.py`), Google Fotos (`fotos_http.py`) e a leitura
  do Instagram (`web.py`) só rodavam no PC1 com os cookies do PC1. E o Reel pelas máquinas NUNCA rodou: o `postar_http`
  do PC1 vinha antes e vencia sempre (log sem nenhum "HTTP no").
- **Decisão:** um mecanismo só (D12: nada de motor paralelo):
  - `maquina_remota.Remoto.nsn_run(modulo, args, enviar, receber)`: roda QUALQUER módulo do worker na máquina, com os
    cookies de lá. Os argumentos vão num JSON UTF-8 e o módulo roda por `runpy` com `sys.argv` montado (nada de aspas do
    cmd/PowerShell/bash estragando acento); arquivos de entrada vão por ssh, saídas voltam por scp (arquivo ou pasta).
  - `core/maquinas.py` (nsn): `ou_remoto(perfil, modulo, ...)` no `main()` de `postar.py`, `web.py`, `fotos_http.py` e
    `quero.py`: cookie no PC1 → roda aqui; sem cookie aqui e máquina com cookie → roda LÁ e imprime a saída de lá.
    `--maquina x200ma` força a máquina, `--local` força o PC1. Dentro do worker o postador não existe → sempre local.
  - Worker (`empacotar_worker.py`) leva agora o nsn inteiro de produção (config, core/auth+session+maquinas, instagram
    web/postar/client, google_photos, veo_flow, tools/quero). PC2 e desktop ganharam Pillow no venv (o `postar.py`
    importa PIL e no PC2 isso nunca tinha sido testado).
  - Reel na produção: ordem nova em `postar_insta_auto.postar_navegador` = **HTTP na máquina → HTTP PC1 → Chrome na
    máquina → Chrome PC1** (a mesma ordem que o Chrome já tinha).
  - Saúde (D15): `saude_flow.py` testa também o Instagram de cada máquina (`cofre_ig_*`), e `saude.py` grava
    `instagram <conta>@<maquina>` ao lado de `flow <perfil>@<maquina>`: 29/10 18h = 16 contas IG vivas em x200ma/acer/pc2.
- **Provado 29/10 (pelo despacho genérico, saída idêntica à do PC1):** leitura do Instagram de canalhistoriacomia no
  x200ma (perfil + reels + posts em JSON); robô QUERO `--seco` de canalhistoriacomia no x200ma; Google Fotos de
  emersonjosiel2032 no PC2 (login ok, 0 itens para o termo). **Reel real pela máquina: 29/10 18:19, `_lucrocomia_` por HTTP no x200ma** (rodada do Instagram Auto; `instagram_auto.log`
  "HTTP no x200ma: ok", `maquina_remota.log` "Reel por HTTP"). Desktop: worker + Pillow instalados, mas o sshd de lá derruba
  conexões ("Connection reset by peer", mesmo após `Restart-Service sshd`): a prova do Flow lá fica para quando o ssh estabilizar.
- **Incidente 29/10 18:38–18:53 (corrigido):** o leitor do Reel remoto (`nsn_reel`) testava `"reel ok:" in saida`; quando o
  worker caía com traceback, a saída trazia a LINHA DE CÓDIGO `print("reel ok:", ...)` e o PC1 dava "postado" sem postar:
  6 falsos (sintetizerisada ×2 no PC2, jornalcomia ×4 no x200ma), vídeos marcados como usados. Corrigido: só URL real
  (`reel ok: https://www.instagram.com/reel/<id>/`) conta, e o erro real (última linha do traceback) vai para o log.
  Desfeito: 6 entradas tiradas do `instagram_auto_posted.json`, o produto `sintetizerisada_20261028_125829` voltou para a
  fila, o CCV `..._162051` saiu da lista `_ccv_postados.json` (ficha apagada). Os 4 Veo da jornalcomia (etapa no Drive)
  NÃO foram revertidos: reserva de centenas, custo de mexer no Drive maior que o ganho.
- **Vídeo em 2 fases (29/10 19:30, dona: "deixe as máquinas produzindo ao máximo"):** `Remoto.nsn_flow_video_2fases` + worker
  `video-pedir`/`baixar`: 1ª fase = token + pedido (Chrome 37 s no PC2), o worker fecha o Chrome e o Veo **libera a vez da
  máquina** (`liberar(maq, 'veo')`, 48 s depois do Chrome pronto); 2ª fase = download SEM Chrome com os cookies colhidos lá
  (13 s, mp4 6,2 MB válido). Antes a máquina ficava reservada até o mp4 chegar. `config.FLOW_HTTP_2_FASES=0` volta ao
  jeito de 1 chamada. Teto de produção continua sendo regra (controlador em repouso com reserva ≥ 500; posts/dia por conta).
- Guia de implantação por máquina (desktop, PC novo): `D:\projeto-navegador-sem-navegador\IMPLANTAR_MAQUINA.md`.
- **NÃO fazer:** copiar cookies; rodar um comando do nsn numa máquina cujo Chrome está com a vez de outro trabalho quando o
  comando precisar do Chrome (só o Flow precisa: o resto é HTTP puro e não ocupa a vez); confiar no `ou_remoto` dentro de
  tarefa agendada sem `-X utf8`; tirar o HTTP do PC1 (é a reserva da máquina fora do ar).

## D33 — Monitor de banimento + RAMPA automática dos tetos (dona 29/10 19:40: "pode subir mas adicione um monitor... e principalmente de imagens que precisamos muito")
- **Dado (29/10):** a produção era limitada por regra, não por máquina: 2 Reels/dia por conta (5 nas de produto), Veo com
  teto 40/dia e só gerando com reserva < 100, imagens sem teto escrito (o que limitava era falha: 28 de 52 "foto na hora"
  falharam hoje por "conta ocupada"/Chrome fechado, e cada pedido tenta só 2 contas). Maior dia de imagens numa conta:
  seebotsia 85 em 28/10, sem sinal. Sinais reais do dia: jornalcomia `400 "This user is inactive so they cannot upload"`
  (x200ma, 19:22 e 21:25); msenergysolar.pa em `/accounts/suspended` (várias rodadas desde 25/10); Flow
  emersonjosiel2027 e filmescomia com SESSAO_EXPIRADA. Atenção: o `instagram_auto.log` recebe DUAS rodadas intercaladas
  (Instagram Auto e MSEnergy_PostarInsta) e a do MS Energy nem sempre escreve "[conta]" antes do erro.
- **Decisão:**
  - `D:\projeto-navegador-sem-navegador\tools\monitor_banimento.py` (tarefa **NSN_Banimento**, 1×/h, pythonw, sem_janela;
    só lê logs, nunca abre Chrome nem pede nada a site). Fontes: `instagram_auto.log`, `maquina_remota.log`,
    `veo\beta\logs\cron_gerar_llm.log` e `foto_na_hora.jsonl`, nsn `flow_gerar.jsonl` e `saude.json`. Classes:
    **restrita** (1357031, "user is inactive", /accounts/suspended), **forte** (feedback_required, checkpoint, challenge,
    400 no upload, UNUSUAL_ACTIVITY, age-restricted, RECAPTCHA_BLOQUEIO, BLOQUEIO DETECTADO), **login** (deslogado,
    SESSAO_EXPIRADA, saúde morta), **fraca** (recusa por política). Conta da linha sem nome = item pendente mais antigo
    da rodada; legenda "Ms energy solar" = msenergysolar.pa (`LEGENDA_CONTA`). Grava `relatorios\saida\banimento.json`
    (tabela por conta: teto base→agora, estado da rampa, sinais 24 h/7 d, último sinal, máquina, saúde; e todos os
    degraus com data) + `logs\banimento.jsonl`. Telegram (`avisos.py`, origem "banimento"): sinal novo por conta;
    forte/restrita sai na hora; degrau da rampa também avisa.
  - `D:\postador-de-videos\config\tetos.json` + `bin\tetos.py` (leitura, biblioteca padrão; falhou = vale o padrão de
    antes, nunca para a produção). Lido por: `postar_insta_auto.main` (Reels/dia por conta), `flow-imagens\gera_imagem.
    gerar_imagem` (conta no teto do dia sai da lista; contas por pedido só sobe) e `video-fila\controlador._veo_tetos`
    (teto/dia e reserva mínima; o painel mostra o valor em vigor).
  - **Regra:** janela sem sinal na conta (e saúde não "morta") → +1 degrau, nunca mais de 1 por rodada; sinal forte →
    −1 degrau e `no_limite` (não sobe mais sozinha; a dona/agente troca para `subindo` se quiser tentar de novo);
    login/recusa → `segurando` (nem sobe nem desce; volta a `subindo` na janela limpa); restrita → `fora` (teto volta à
    base). Veo é global: forte em ≥ 2 contas do Flow ou bloqueio global = desce; login em ≥ 3 = segura.
  - **Tetos iniciais (degrau 0 = o que já roda hoje, nada cortado):** imagens 90/conta/dia, +15 a cada 24 h limpas, máx 180;
    contas por pedido 2, +1, máx 4. Reels = `max_dia` do reuso (2 ou 5), +1/dia a cada 36 h limpas, máx 8. Veo teto 40/dia
    +5 (máx 80) e reserva mínima 100 +25 (máx 250), a cada 72 h limpas. 1ª rodada (29/10 22:09): jornalcomia e
    msenergysolar.pa **fora**; Veo e várias contas em `segurando`; nenhum degrau subiu ainda.
  - Painel (:8790, aba **Sem navegador (HTTP)**): tabelas "Monitor de banimento × teto em vigor" e "Degraus da rampa"
    (`api_nsn` devolve `banimento`).
- **Não fazer:** subir vários degraus de uma vez ou mexer à mão no `nivel` sem anotar aqui; ler "último [conta]" no
  `instagram_auto.log` (rodadas intercaladas); apagar `vistos` do banimento.json (reenvia todos os sinais ao Telegram);
  usar a rampa para mudar a máquina de uma conta (cada conta segue pela mesma máquina, `ORDEM_NAVEGADOR` intocado);
  baixar a base de imagens abaixo do que já sai por dia (era 30 no 1º rascunho: cortaria a seebotsia).

## D35 — Imagens do Flow: por que metade do "foto na hora" falhava (acer no telão) e a 2ª conta não repete a máquina (29/10 noite)
- **Dado (29/10, `veo\beta\logs\foto_na_hora.jsonl` + as mensagens internas do `gera_imagem`, que só aparecem em
  `video-fila\logs\controlador_veo_gerar.log`):** 28 erros em 52. Até 17:40: 27 erros em 51 (53 %). A mensagem
  "conta ocupada (so notebook: maquinas ocupadas ou fora)" escondia a causa; o real era:
  - **acer passando vídeo no telão (~15 entradas, todas com `maquinas=["acer"]`):** a cadeia do Veo oferecia só o acer,
    o `gerar_imagem` o via "livre" (`maquina_livre` só olha o Chrome, não o telão nem a vez de outro), sorteava 2 contas
    do acer e as duas batiam no `tentativas` ("acer está exibindo vídeo no telão"); o `foto_na_hora` repetia isso 3×.
    Hipótese 1 da tarefa confirmada (as 2 contas iam para a mesma máquina bloqueada).
  - **tela (Playwright) do x200ma (~8):** `Locator.click Timeout 5000/8000ms` e `TargetClosedError` em 6 contas
    seguidas 16:45–17:01. Isso era antes da imagem por HTTP nas máquinas (D30, ligada 17:39).
  - 3 sem nenhuma conta tentada; 1 às 18:50 (PC1 seebotsia `TargetClosedError`, 1229 s).
  - Depois das 17:40: 1 erro em 1 pedido do foto_na_hora; 9 imagens no `geracoes.jsonl` (8 por HTTP nas máquinas).
  - Hipótese 2 (a "vez" fica reservada para o Veo depois que o HTTP solta a máquina): **não medida** — o Veo grava a
    reserva direto no `notebooks_reservados.json` sem log; nenhum "com a vez de 'veo'" nos logs de 29/10. Não mexido.
- **O que mudou (`D:\flow-imagens\gera_imagem.py`):**
  - `_maquina_pronta`: a lista de máquinas livres usa o mesmo filtro do `tentativas` (vez de outro respeitando
    `MAQUINA_VEZ_DE`, `maquina_livre`, telão `exibindo`). Acer no telão = nem entra: falha em 0 s e o `foto_na_hora`
    já para na 1ª tentativa ("imagem:" vazio) em vez de gastar 3.
  - `ruins` por pedido: máquina pulada ou que falhou numa conta não entra na próxima; conta só-notebook sem máquina
    restante é pulada sem gastar tentativa; o laço conta só tentativas de verdade (`max_contas`, padrão 2 sem PC1),
    então a 2ª tentativa vai para uma conta de OUTRA máquina livre.
  - Mensagem: `conta ocupada (so notebook: acer está exibindo vídeo no telão...)` / `x200ma falhou TimeoutError` (a
    palavra "ocupada" segue: não põe a conta de castigo). Erros por conta até 200 caracteres; `foto_na_hora` guarda 600.
  - `logs\pedidos_falhos.jsonl` (flow-imagens): 1 linha por pedido que ninguém entregou, de QUALQUER chamador (Veo,
    `cliente.py`, produtos, MS Energy), com `erros`, `ruins`, `livres`. O `geracoes.jsonl` segue só com acertos (o
    `tetos.imagens_hoje` conta dele).
  - Teste a seco (tentativas/HTTP falsos): acer no telão sem o filtro saber → a 2ª conta vai ao x200ma; só o acer →
    1 conta tentada, motivo na mensagem; filtro sabendo → 0 contas, 0 s. Ao vivo 22:46: o acer estava no telão e saiu
    da lista (antes teria gastado as 2 contas nele).
- **Como medir depois:** taxa de `"erro"` no `foto_na_hora.jsonl` por dia e as linhas do `pedidos_falhos.jsonl`
  agrupadas por `ruins` (telão/vez/OCUPADO/falhou). Desfazer: voltar `_maquina_pronta` para `maquina_livre` e
  `contas = nb[:2]` + `contas[:max_contas]` no `gerar_imagem`.
- **NÃO fazer:** tirar a palavra "ocupada" da mensagem (o `gerar_imagem` pune a conta sem ela); usar " | " dentro do
  motivo (o `monitor_banimento.f_foto_na_hora` separa as contas por ele); oferecer máquina com a vez de outro para
  ganhar imagem (D31: um Chrome por vez); mexer em `tetos.json`/`monitor_banimento.py` (D33) ou `ORDEM_NAVEGADOR`.

## D36 — Imagens do Flow: notebooks → PC2 (vários Chromes juntos) → desktop → PC1 por último (dona 29/10 23h)
- **Pedido (dona):** "se dá navegador roda nos notebooks, se der erro nos notebooks aí roda no navegador do PC2... e se
  não o desktop" (câmera desligada); PC1 = failback final; "no PC2 nem precisa ser um por vez como nos notebooks";
  "continuo vendo navegadores sendo abertos no PC1 mesmo vendo o PC2 sem nenhum aberto". Cada chat ajusta o projeto
  dele: este ajuste é só das imagens (`D:\flow-imagens\gera_imagem.py`).
- **Dado (29/10, `geracoes.jsonl`, 84 imagens):** PC1 31 (19 pela tela + 12 HTTP do PC1, que também abre Chrome aqui
  para o token), x200ma 24, acer 16, PC2 7, desktop 6. Causa: com `maquinas=None` (cliente.py, produtos, MS Energy) a
  lista era `nb[:1] + pc1` = 1 conta das máquinas e já as do PC1; e o PC2 só entrava com a 9460 livre (a 9460 do PC2
  fica com o Veo/postagem: 23h00 estava com inovaremanhwabr). PC2 às 22h50: CPU 6 %, 9,4 de 11,7 GB livres.
- **O que mudou:**
  - `ORDEM_IMAGENS = x200ma, acer, pc2, desktop` (uma máquina por vez, nessa ordem, pelo `tentativas([m])`); as contas
    são ordenadas pela melhor máquina livre delas (sorteio dentro do mesmo nível). O `ORDEM_NAVEGADOR` global NÃO mudou.
  - PC2: imagem abre o Chrome numa **porta extra 9470–9475** do `chrome_conta` (cada porta com o seu `ocupado_<porta>`,
    já existia para o TikTok em lote 9461+), então várias imagens rodam juntas no PC2 e nenhuma disputa a 9460. Livre =
    responde, sem "login" na vez, RAM ≥ 2,5 GB (`_pc2_pronto`); o perfil aberto na 9460 não é sorteado só para o PC2.
    `PC2_SEMPRE` (env `FLOW_IMAGEM_PC2_SEMPRE=0` desliga): o PC2 entra mesmo quando a cadeia do Veo não o passou em
    `maquinas` (a porta extra não toca na 9460 do Veo). Falha de uma conta no PC2 não tira o PC2 das próximas contas.
  - `maquinas=None`: `contas = nb + pc1`, no mínimo 3 tentativas, e a **última fica guardada para o PC1** (as das
    máquinas não podem gastar a última vez quando há conta do PC1).
  - Conta só-notebook com o Flow pedindo login em TODAS as máquinas dela → `_DeslogadaNasMaquinas` (sai do sorteio
    `FORA_S`); antes "ocupada" e era sorteada sem parar (maiteanajessicajesus no PC2, 23h).
- **Provado 29/10 (real):** 22:58 `--maquinas x200ma,acer,desktop`: x200ma OCUPADO → pulado, imagem por HTTP no acer em
  98 s. 23:00 `--maquinas pc2` com a 9460 do PC2 ocupada: abriu na **9470** (log do chrome_conta do PC2), 1ª conta
  deslogada, 2ª conta por HTTP em 78 s. Teste a seco: acer no telão com `maquinas=None` → PC1 só depois.
- **Visto e NÃO mexido (outros projetos, a dona pediu que cada chat ajuste o seu):** recap longo de anime NÃO roda no
  PC2 (controlador: "só nas GPUs do Kaggle") — bate com a regra; mas o **hipercool renderiza as LÍNGUAS (capítulo
  inteiro) na CPU do PC2** (`hipercool-videos\bin\fila.py pc2`, 22:52 "the-inheritor-cap15 em indonésio"). O PC2 fica
  parado entre Shorts: o controlador dispara 1 trabalho por rodada de ~20 min e o Short dura ~10 min (21:26 dispara,
  21:33 LIVRE; 22:23 rodada pulada por `wmic` do PC1; 22:14 scp para o PC2 estourou). Veo no PC2 só gera o vídeo; a
  montagem completa segue no PC1. Desktop fora muitas vezes por ssh ("Connection reset"/timeout) e microfone em uso.
- **NÃO fazer:** imagem na 9460 do PC2 (é a do Veo/postagem); portas 9461–9469 (TikTok em lote 9461+, claude_criar 9465);
  mudar o `ORDEM_NAVEGADOR` global por causa das imagens.

## D38b — Desktop trabalhando apesar do ssh que cai + medidor/análise de 24 h nos 3 PCs (dona 29/10 23h–00h)
- **Pedido (dona):** telão no desktop só com câmera desligada + botão para desligar; medidor de CPU/RAM 24/7 no PC2,
  desktop e PC1 com análise a cada 24 h (pelo ffmpeg também); "crie crons pra ir tentando e quando conseguir vá mandando
  os arquivos e executando"; dar ao desktop acesso aos outros PCs (plano B: em 24 h sem jeito, a IA roda no desktop e
  ele vira o PC principal).
- **Dado:** telão/medidor/análise JÁ existiam desde 27/10 (`vitrine\telao_win.py`, `analise_maquinas.py`, tarefa
  `AnaliseMaquinas24h` 08:05), mas o desktop nunca foi instalado (sem `C:\vitrine`; `estado\telao_desktop.json` não
  existia) e a análise nunca tinha gerado relatório (último resultado 1). O ssh do desktop (OpenSSH 10.4,
  `PerSourcePenalties no`) aceita a chave e derruba a sessão ("Connection reset" logo depois de "Server accepts key"),
  também pela rede de casa 192.168.18.45 → não é Tailscale nem excesso de conexões do PC1 (0 abertas no momento); a
  causa está no Windows do desktop (não diagnosticada: precisa olhar o Visualizador de Eventos lá). Comando curto
  passa às vezes; scp e comando grande quase nunca. PC1 não tem servidor ssh. 1ª análise rodada (23:37): **PC2 trabalhou
  20 % das últimas 24 h, parado 65 %** (CPU média 31 %); PC1 100 % CPU, RAM 86 %.
- **O que mudou:**
  - `D:\video-fila\desktop_vigia.py` + tarefa **DesktopVigia** (10 min, pythonw): 1 conexão de teste por rodada e no
    máximo 1 passo: telão (o desktop PUXA os arquivos por HTTP de um servidor temporário do PC1 em
    100.118.234.102:8798, só com os 3 arquivos do passo) → conferir (tarefa rodando + `saude.json`) → chave ssh PRÓPRIA
    do desktop (só a pública vem: `estado\desktop_chave.pub`) + `~\.ssh\config` lá com pc1/pc2/x200ma/acer → worker nsn
    (`instalar-nsn desktop`) → `colher-flow` de 2 perfis por rodada (só com `maquina_livre`) → `saude-flow`. Estado em
    `estado\desktop_vigia.json`, log em `logs\desktop_vigia.log`; Telegram em cada passo, ssh voltando após 3 h, e 24 h
    sem entrar (aponta o plano B).
  - `vitrine\instalar_desktop.ps1`: tarefa `Desktop_Telao` por `Register-ScheduledTask` (o python do desktop é
    `C:\Program Files\Python311` e o `schtasks /tr` partia o caminho no espaço). **Instalado 29/10 23:51** (arquivos com
    o tamanho certo, atalhos DESLIGAR/LIGAR TELAO). A conferência ainda não passou (ssh caiu).
  - `medidor_pc1.py` + tarefa **MedidorPC1** (10 min, sai se já roda): `estado\saude_pc1.csv`, mesmas colunas do
    `saude.csv`; tasklist que passa de 60 s (PC1 sem RAM) grava -1 nas contagens. `analise_maquinas.py` lê pc2, **pc1**
    e desktop.
  - `maquina_remota.Remoto.nsn_colher` (Windows): chama `colher.py` pelo caminho, sem `cd /d … &&` (não roda no
    PowerShell do desktop).
  - `autorizar_desktop.ps1` (a DONA roda, PowerShell admin no PC1): instala/liga o sshd do PC1 e autoriza a chave do
    desktop no PC1 (`administrators_authorized_keys`), PC2, x200ma e acer. Guia do plano B: `linhas\DESKTOP_PRINCIPAL.md`;
    as 106 tarefas do PC1 exportadas em `linhas\tarefas_pc1\` (XML + `LISTA.md`, sem segredos).
- **Pendente:** Reel por HTTP no desktop (`Remoto._nsn_reel_win` também usa `cd /d … &&`: falha no PowerShell e cai
  na próxima opção da ordem); causa do ssh do desktop (olhar no desktop).
- **30/10 03h:** a sonda da vigia fecha Chrome não-login aberto há mais de 45 min no desktop (`ocupado` velho): o colher
  das 02:41 abriu o Chrome, o ssh caiu antes do `fechar` e o desktop ficou travado para Veo/imagens/posts. Worker nsn
  instalado 02:06 por HTTP; chave 01:46.
- **NÃO fazer:** scp/stdin para o desktop (derruba); várias conexões coladas (a vigia faz 1 teste + 1 passo, 20 s
  entre eles); copiar cookies/perfis entre máquinas (plano B inclusive); a vigia autorizar chave ou ligar sshd sozinha
  (é a dona); deixar a tarefa duplicada no PC1 e no desktop se o desktop virar principal.

## D39 — PC2 no máximo de Shorts: alimentador a cada 5 min, CPU só barra com 2+, 3 canais antes de desistir (30/10 00h, turno da noite)
- **Dado:** 1ª análise de 24 h (29/10 23:37): PC2 trabalhando 20 %, parado 65 %, CPU média 31 %. No log do controlador
  de 29/10: 73 disparos para o PC2 no dia, nunca 2 Shorts na mesma rodada; uma rodada leva 15–20 min (código do PC2
  ~2,5 min + baixar a fonte 2–6 min) e o Short ~10 min lá. `pc2_vaga_short` barrava por CPU com 0 Shorts (a língua do
  hipercool a 100 %); 22:49 "sem vídeo novo em @grananerd" = PC2 vazio a rodada inteira.
- **O que mudou (D:\video-fila):** `alimentar_pc2.py` + tarefa **AlimentarPC2** (5 min, pythonw, trava própria): fora
  da rodada do controlador, traz os prontos e, se `pc2_vaga_short` deixa, dispara mais 1 Short (sai se já há despacho
  para o PC2 em andamento ou a vez do PC2 está cheia). O controlador segue com 1 por rodada — a 1ª versão desta noite
  punha 2 por rodada e foi desfeita: escolher+baixar a fonte pelo proxy leva 10+ min AQUI (00:07–00:21 de 30/10) e
  esticava a rodada inteira. `ocioso.pc2_vaga_short`: CPU > 85 % só barra com 2+ Shorts (RAM ≥ 2,5 GB e
  disco ≥ 8 GB seguem barrando sempre). `ocioso._disparar_parceiro_pc2`: tenta até 3 canais da fila (mesma ordem de
  prioridade) antes de "sem vídeo novo". Também `maquina_remota._nsn_reel_win` sem `cd /d` (Reel por HTTP no desktop).
- **00h41:** `PC2_SHORTS_MAX` 3 → 4 (2 Shorts rodando = CPU média 19 % e 6,9 GB livres). `ocioso._trazer_prontos_pc2`
  lista os prontos por PowerShell em UTF-8: o `dir` do cmd devolvia cp850 e a pasta "meu-irmão-é-mais-velho_cap1" ficou
  presa no PC2 desde 29/10 20:42 ("falhou trazer" a cada rodada).
- **01h25:** `ocioso.py` usa sempre o ssh/scp do Git (`maquinas.SSH`) e `_ssh` com `stdin=DEVNULL`: sob pythonw o
  "ssh" do PATH é o do Windows (System32, trava depois de autenticar — 17/10) e o AlimentarPC2 dizia "ainda fazendo"
  em Shorts com `.fim` pronto. A pausa de 3 falhas seguidas do PC2 (`pc2_parceiro_falhou.json`) vence em 2 h (antes só
  apagando à mão; a queda do gateway das 01:23 poderia parar o PC2 até de manhã). Backup: `estado\ocioso.py.bak_20261030_0135`.
  Falha de rede/gateway no log do Short (`URLError`, `WinError 10065/10060`, `gateway timeout`) = máquina (vídeo volta).
- **02h00:** trava EXCLUSIVA `estado\pc2_disparo.lock` em `ocioso._disparar_parceiro_pc2` (msvcrt, não espera): com o
  alimentador, o controlador e ele dispararam o MESMO vídeo (mrXSE5iDdFc 01:48/01:50) — a vez do `fila_render` deixa
  seguir depois de 72 s, então não serve de exclusão.
- **04h05:** PC2 caiu de 66 % para 31 % (03h–04h) porque o preparo de cada Short NO PC1 levou 793/438/770 s. Preparo
  antecipado: `ocioso.preparar_proximo_pc2()` (mesma trava do disparo) deixa 1 Short em `estado\pc2_prontos\<id>\`
  (source.mp4 + cap*.vtt + cand.json + meta.json; o id entra nos tentados na hora; > 8 h, já feito ou sem mp4 = apagado
  pelo `_prontos_pc2`). `_disparar_parceiro_pc2_travado` usa o pronto primeiro (`_enviar_pronto_pc2` = só scp + rodar).
  O AlimentarPC2 prepara o próximo em toda rodada, com ou sem vaga. Escolha separada em `_escolher_pc2`. Backup
  `estado\ocioso.py.bak_20261030_0405`.
- **Desfazer:** `schtasks /change /tn AlimentarPC2 /disable`; `n != 1` no `cpu_alta`; voltar `alvo = min(...)`.
- **Medir:** `analise_maquinas.py --so-ver` (trabalhando % do PC2) e número de "DISPAROU pc2" por hora.
- **NÃO fazer:** voltar a disparar vários Shorts DENTRO da rodada do controlador (cada um segura a rodada 10+ min); tirar a regra de RAM/
  disco do PC2; mexer no hipercool do PC2 (renderiza línguas na CPU — a dona pediu recap longo só em GPU; decidir com ela).

## D40 — Arquivos para/da máquina Windows por HTTP temporário do PC1 (desktop sempre; outras se o scp falhar) (30/10 02h25)
- **Dado:** `maquina_remota.log` 30/10 00:30 e 01:34: Veo abriu o Chrome no desktop (ssh ok) e perdeu a vez porque
  `envio de <foto>.png falhou (Read from remote host … Connection reset)` — o sshd do desktop derruba scp e comando
  grande (D38). A volta do mp4/png (`Remoto.receber`) também é scp.
- **O que mudou (`D:\postador-de-videos\bin\maquina_remota.py`):** `_HttpTemp` (servidor HTTP só da pasta temporária, em
  `PC1_TAILSCALE`:porta-do-sistema, aceita PUT quando é para receber), `Remoto._ps_enc` (PowerShell por
  -EncodedCommand, sem barra de progresso), `_enviar_http` (a máquina baixa do PC1 e confere o tamanho) e
  `_receber_http` (a máquina sobe; pasta vai em tar e é extraída aqui no lugar de `local`, como o `scp -r`).
  `MAQUINAS["desktop"]["puxar_http"] = True` → desktop usa sempre; nas outras Windows (PC2) é a reserva quando o scp falha.
- **Provado:** no PC2 (forçando o HTTP), 3,4 MB enviado e trazido de volta com o mesmo MD5; pasta com 2 arquivos trazida.
- **08h00:** `nsn_flow_video_2fases`: a 2ª fase (só baixar; o crédito já foi gasto) tenta de novo até 3× (20 s) quando
  a falha é de ssh/rede — 05:00 no desktop o Flow aceitou o pedido (inovaremanhwaverseviet) e a 2ª fase caiu no ssh:
  vídeo pago e perdido. O desktop já entrou na produção: 07:51 `video.mp4 enviado por HTTP (6639 KB)`.
- **Desfazer:** tirar `"puxar_http": True` do desktop (volta ao scp); o fallback só entra quando o scp já falhou.
- **NÃO fazer:** servir pasta que não seja a temporária (o servidor serve TUDO o que está nela); deixar o servidor
  aberto (`fechar()` no `finally`); usar para cookies (regra fixa: cookies nunca saem da máquina).

## D41 — Engenharia reversa (D17) a cada 6 h em vez de 2 h: ela estava pausando o yt-dlp da produção (30/10 08h25)
- **Dado:** `ytdlp_vez` pausado 120 min às 07:40 com motivo "engenharia reversa: … pass cookies" (checagem de robô do
  YouTube); a pausa vale para o PC inteiro e dobra a cada novo bloqueio. Na mesma madrugada os Shorts do PC2 ficaram
  sem fonte (PC2 6–11 % de uso nas horas pausadas; preparo da fonte 650–1965 s). O `ERContinuo` baixa top N + baixo N por
  canal priorizado + amostra de fundo a cada 2 h, no mesmo IP e na mesma via de 1 yt-dlp que a produção.
- **O que mudou:** tarefa `ERContinuo` repetindo a cada **6 h** (`Set-ScheduledTask`, logon Interativo mantido). Código
  do `continuo.py` intocado (1 download por vez, pausa 90 s, para no bloqueio continuam).
- **09h30:** só espaçar não bastou — a passada das 09:10 levou o 2º bloqueio (pausa de 120 min até ~11:13). Agora o
  `continuo.py` não baixa nada (prioridades nem amostra de fundo) se a última pausa do `ytdlp_vez` foi causada pela ER e
  terminou há menos de 12 h (`_bloqueio_recente_da_er`); medir/concluir/medir_nossos seguem.
- **Desfazer:** `$t = Get-ScheduledTask ERContinuo; $t.Triggers[0].Repetition.Interval = "PT2H"; Set-ScheduledTask -InputObject $t`. Tirar o bloco `_bloqueio_recente_da_er` do `main`.
- **Para a dona decidir:** se a ER pode rodar só de dia, ou com cookies próprios (a mensagem do YouTube pede cookies), ou
  num IP separado — hoje ela disputa o IP de casa com os Shorts.

## D42 — Downloads: PC2 tem prioridade; longo no PC2 só de reserva; Kaggle baixa sem bloqueio; canal Cozinha Noturna (30/10 11h30, dona acordada)
- **Dado:** PC1, PC2 e x200ma saem pelo MESMO IP público (191.36.137.42) — o bloqueio do YouTube é da internet de casa,
  não de um PC. Teste 30/10: VPS 209 (209.145.60.53) barrada em 2–3 s ("Sign in to confirm you're not a bot") com o
  yt-dlp do sistema e com o 2026.10.26 nos clientes tv/web_safari/mweb. **Kaggle (34.141.233.249, notebook só CPU
  `emersonjosiel/teste-ytdlp-ip`) baixou 2 vídeos sem bloqueio: 5 s e 2 s, 2–13 MB/s.**
- **O que mudou:**
  - `recapd ... bin\ytdlp_vez.py`: quem roda com `YTDLP_PRIORIDADE=pc2` marca `D:\video-fila\ytdlp_prioridade_pc2.json`
    enquanto espera a vez; os outros (Cortes do PC1, ER…) esperam ele passar (pedido de processo morto ou > 20 min
    não vale). Backup `D:\video-fila\estado\ytdlp_vez.py.bak_20261030_1120`. `ocioso._prebaixar_pc2` e
    `preparar_proximo_pc2` marcam a prioridade só durante o download.
  - `ocioso.longo_pc2_permitido()`: anime longo no PC2 só de reserva (dona: "na pior das hipóteses, pra não ficar
    parado") — sem Short rodando nem preparado, nenhum Short disparado há 30 min (`estado\pc2_ultimo_short.txt`) e
    yt-dlp sem pausa (o longo também baixa a fonte no PC1). `ANIME_LONGO_PC2=1` libera sempre, como antes. Usado no
    `disparar_anime_longo` e no `controlador._cortes_pc2`.
  - Canal novo **Cozinha Noturna** (`@cozinhanoturna`, `UCoAiFiUT99wnXjgZ2d7r_AQ`) na conta emersonjosiel02@gmail.com
    (cofre: entrada `emersonjosiel02@gmail.com`, pasta `perfis\nova_canal_20261030`, porta 9798). Escolha: culinária é o
    maior nicho de Shorts do Brasil que nenhum dos 22 canais do parceiro cobre. **Ainda fora da produção:** não há
    fonte do tipo culinária em `parceiro.json` (`fontes`: anime 26, fatos 24, filme 12, dorama 10…).
- **Próximo (proposto à dona):** baixador no Kaggle (o PC1 manda a URL, o Kaggle baixa e sobe no Drive, PC1/PC2 puxam)
  — tira os Shorts da dependência do IP de casa; fontes de culinária + canal no `parceiro.json`/`youtube_navegador.json`.
- **NÃO fazer:** usar a VPS de produção (62.171.128.241, compartilhada com Atlas/Lucrativa) para baixar do YouTube.

## D43 — Baixador do YouTube no Kaggle (outro IP) para os Shorts do PC2 quando o IP de casa está barrado (30/10 12h, dona: "sim, monte")
- **Dado (D42):** o bloqueio do YouTube é do IP de casa (PC1/PC2/notebooks = 191.36.137.42); VPS 209 barrada na hora;
  Kaggle (34.141.233.249) baixou sem bloqueio. Nas horas de pausa do `ytdlp_vez` (2× 120 min em 30/10) o PC2 ficou com
  6–11 % de uso por falta de fonte.
- **O que mudou:**
  - `D:\recapd-ambientes\producao\colab\kaggle_baixador.py`: kernel **emersonjosiel/baixador-yt** (CPU + internet,
    dataset `recap-worker-conf` para o rclone, igual ao `kaggle_trabalhador.py`), em loop até 11,5 h: pega
    `manhwa-drive:baixador/pedidos/<id>.json`, baixa no MESMO formato do `anime_fetch.download_video` (em pé até 720,
    H.264, mp4) + auto-legenda pt (es se faltar), sobe em `baixador/prontos/<id>/` com `ok.json` por último (ou
    `erro.json`); `baixador/vivo.json` a cada volta.
  - `D:\recapd-ambientes\producao\bin\kaggle_baixar.py`: `vivo()`, `baixar(url, id, pasta)` (pede, espera até 15 min,
    traz e limpa o Drive) e CLI `lancar|status|manter|teste <url>`; usa a conta/chave do `colab\kaggle_lancar.py`.
  - `D:\video-fila\ocioso._fonte_para`: fonte do Short do PC2 (preparo antecipado e download na hora) vai pelo Kaggle
    quando `ytdlp_vez.pausado()` e o baixador está vivo; senão o caminho de sempre. Kaggle falhou = caminho normal.
- **Desfazer:** parar a tarefa `KaggleBaixador` e `kaggle kernels` stop / não relançar; `_fonte_para` só usa o Kaggle
  com o baixador vivo.
- **NÃO fazer:** copiar cookies do YouTube para o Kaggle; usar o baixador para listar canais em rajada (a discovery
  continua no PC1, pelo proxy); deixar o `kaggle_baixador.py` na pasta `/kaggle/working` com o rclone.conf (fica em /tmp).
