# ⚠️ VERSÃO CORRENTE DO CÓDIGO — LEIA ANTES DE MEXER

> 🚨🚨 **ANTES DE MEXER EM CENSURA, PRODUÇÃO, OU RE-GERAR UM CAPÍTULO: leia
> `_LEIA_FLUXO_PRODUCAO_E_CENSURA.md` (OBRIGATÓRIO).** Contém: ordem de diagnóstico da censura
> (isolar clip → checar DETECÇÃO antes de mexer em limiar), causa-raiz já resolvida (a fórmula de
> score ignorava `erotica` → painel explícito passava batido), fluxo teste→aprovação→versão gemini
> com aproveitamento de voz, quando regerar voz (e quando NÃO), e alta produção (IA em fila serial +
> render em paralelo). Escrito porque em 2026-07-01 se perdeu HORAS re-descobrindo um fix já feito.

Atualizado: **2026-07-03** (🟢 VERSÃO OFICIAL DE PRODUÇÃO congelada + REORGANIZAÇÃO das cópias).

> 🟢🟢 **SNAPSHOT OFICIAL (a verdade AGORA): `bin/_VERSAO_CORRENTE_20260703_V8OFICIAL/`** (md5 em `_MD5.txt`).
> É o código VALIDADO que gerou cap01-07 OK pelo driver noturno (censura por cor/blur com cens_jobs
> reconstruindo o clip +18 sem deslocar a timeline; WordBoundary sync legenda; 126 efeitos; mascote;
> elementais). Conferir md5 antes de editar qualquer .py.
> md5: hiper-pipeline `0745603693aa8c5dd2cb3293fb1ec34b`, effects_engine `656e38b415ef838fec175a0b62ae3272`,
> censura_visual `f143004fed5356b54aa32b8da0b4e842`, edge_tts `01d23d05878e0837f797e3a12f4e5313`,
> elemental_transitions `5f4660c011ba4d34521db84e43f88924`.
>
> 📦 **GIT DE VERDADE**: esta versão está commitada (`ff0fdb8`) + tag `v8-producao-20260703`. Backup real.
>
> 🗂️ **REORGANIZAÇÃO 2026-07-03** (pra outro agente não se perder):
> - `D:\hipercool-producao` = NOVA cópia OFICIAL limpa (git próprio, commit `51e3d1f`), gerada deste código.
>   É a de POSTAR. A -fix continua sendo o laboratório.
> - `D:\hipercool-producao_OLD_20260703` = produção ANTIGA renomeada (NÃO apagar até confirmar a nova).
> - `_testes/` (843MB de protótipos de efeito já aprovados) APAGADO. Sem perda de produção: os efeitos que
>   o pipeline USA estão preservados — `elemental_transitions.py` (65 ELEMENTS / 68 ASSET_FILE) + 102 .mov em
>   `assets/overlays/elemental/` + 96 HTMLs-fonte em `D:\hipercool-hyperframes/compositions/`. O
>   `COMANDOS_PROTOTIPOS.sh` (builders standalone de rascunho) foi junto, mas a lógica já está em `panel_effects.py`.
>   Snapshots de código em `bin/` MANTIDOS (histórico, ~5MB).

Atualizado antes: **2026-07-01** (FIX CENSURA raiz: score incluía só activity/display/suggestive e ignorava
`erotica`+`none` → nu explícito com score 0.12 passava sem censura. Agora `max(ponderado, 1-none)` com
erotica; cache recalcula sozinho (zero token). Forte=só tarja, leve=só cor. LIMIAR_NSFW 0.35.)
Antes: (FIX SYNC: WordBoundary ligado na legenda + elementais + vraa/reprovação + mascote)

> 🟢 **SNAPSHOT DESTA VERSÃO (a verdade): `bin/_VERSAO_CORRENTE_20260702_V7CENSURACOR/`** (md5 em `_MD5.txt`).
> Validado no cap05: painel explícito dos ~42s (score subiu 0.12→0.93) agora com tarja; frames 38/40/42s
> pretos, painel limpo vizinho intacto; censurada 1080p, áudio≈vídeo 290.6s. Confira md5 antes de editar .py.
> md5: hiper-pipeline `a799464f23fe0a7506a77afec9769c27`, effects_engine `656e38b415ef838fec175a0b62ae3272`,
> censura_visual `8b33b205494089968fcfa6dd2121dd1f`.
> (Nota: outro agente somou features novas ATRÁS DE FLAGS OFF — LYRIA_OPENING, GEN_THUMBNAIL,
> LYRIA_MOOD_FALLBACK, todas default "0" → não afetam o fluxo do cap05. Snapshot atualizado 19:xx.)

> 🟢 **SNAPSHOT ATUAL (a verdade): `bin/_VERSAO_CORRENTE_20260702_V7CENSURACOR/`** (md5 em `_MD5.txt`).
> Conferir md5 antes de editar qualquer .py. Correções desta versão (todas validadas em cap01,
> sync A/V 444.4s≈444.5s, log em `logs/night-shift.md` 2026-07-01):
> 1. **Drift legenda RESOLVIDO NA RAIZ (WordBoundary)**: o cache não guardava o timing real
>    (.words.json). Agora: `edge_tts_engine._move_words_sidecar` move o sidecar tmp_mp3→out_wav
>    (normaliza o shift do TRIM_SILENCE); `tts_panel` guarda/recupera o sidecar no cache; o pipeline
>    coleta `clip_word_times` por clip e passa `word_times` pro `render_subtitles_short`, que agora usa
>    o timing REAL de cada palavra (não a estimativa por nº de letras). Pra popular sidecars em cache
>    antigo, rodar com `--force-tts` uma vez (edge-tts é grátis).
> 2. **Elementais falhavam 100% (OOM com 25 overlays)**: `_apply_lote` blindado (Path); `apply()`
>    já loteava (ELEM_BATCH=6). Agora aplica as 25 de verdade.
> 3. **TAREFA_18** vraa/reprovação: 12 wavs em `workspace/assets/sfx/`, disparo por keyword em
>    `pick_sfx_for_text` (`_pick_from_pool` anti-repetição).
> 4. **Mascote**: `MASCOTE_MAX` default 2→5.
> 🤖 **Cron a60b88ab (:13/:43)** roda `bin/night-shift-driver.py`: 1 cap/vez (guarda por PID + log
>    fresco → nunca 2 simultâneos), gemini+censura+tudo ligado, valida sync (áudio≈vídeo) e refaz se
>    quebrado. Estado em `workspace/night_shift_state.json`. NÃO faz commit/push.

Atualizado antes: **2026-06-30** (confirmada a cópia certa + criada convenção de versionamento datado)

> 🎯 **CHAT NOVO? Para implementar os efeitos/mascote/censura criados em 2026-06-30, comece por
> `IMPLEMENTAR_TUDO_AGORA.md`** (índice mestre: pré-condições, md5, ordem de leitura de todos os docs,
> passos A-D, receita p/ criar+registrar efeito). Tudo pronto em assets; falta só APLICAR no .py.

## 🔌 ANTES DE "MELHORAR" LEGENDA / TRANSIÇÃO / TTS / ÁUDIO — LEIA OBRIGATÓRIO
Pasta **`MELHORIAS_EXTERNAS/`** tem análise LINHA A LINHA de 8 projetos open-source maduros
comparados com o nosso código, com plano de implementação por área. Comece por
`MELHORIAS_EXTERNAS/_LEIA_PRIMEIRO_INDICE.md`. NÃO reimplemente sem ler — já foi mapeado o que
copiar e o que NÃO copiar. Maior retorno: **WordBoundary do edge-tts** (doc 01) resolve a queixa
da legenda que some/dessincroniza na RAIZ. Clones em `D:\outros projetos para extrair melhorias\`.
⚠️ Os docs são um MAPA — na hora de implementar, ABRA e LEIA o código-fonte dos clones (cada doc
dá o arquivo:linha exato) pra confirmar tudo e achar mais coisa; não copie nada só pelo resumo.

## 📌 DOCS DE FEATURE EM ANDAMENTO — LEITURA OBRIGATÓRIA ANTES DE IMPLEMENTAR
> Se você foi chamado pra mexer em CENSURA ou em MOVIMENTO/ANIMAÇÃO de imagem, leia o doc
> correspondente ANTES de tocar no código. Ordem: ler doc → conferir md5 → implementar.

> 🆕 **TAREFAS PENDENTES (portadas do n8n, aprovadas pela usuária):** se você abriu um
> chat novo e NÃO foi direcionado a uma feature específica, LEIA
> **`TAREFAS_AGENTE/_LEIA_PRIMEIRO.md`** — 13 melhorias prontas pra implementar, de TRÊS fluxos n8n:
> Grupo A (texto/fila — viralizador/anti-ban, tags de emoção, fila resiliente) do
> `fabrica de animes-1-funcional copy 2.json`; Grupo B (efeitos/qualidade do vídeo — memória de
> continuidade, análise adaptativa, legenda por contexto, movimento por emoção, SFX expandido,
> perfis de qualidade) do `fabrica de animes-3-cria video pequeno copy.json`; Grupo C (versão
> COMPILADA/paisagem — ⭐ painéis em paisagem com efeitos 16:9 e 2 painéis lado a lado, merge
> hierárquico, robustez de disco/quarentena, CTAs+capítulos) do
> `fabrica de animes-4-cria videos grandes compilados.json`, alvo `bin/landscape-compiler.py`.
> Cada tarefa EXIGE analisar o JSON original correspondente e tem flag própria (default OFF).
> NÃO mexer em censura (outro agente cuida).

- **CENSURA (visual +18)** — feature em andamento, módulo `bin/censura_visual.py` já existe.
  - Estado atual e decisões: `HANDOFF_20260630_VOZES_CENSURA.md` (FONTE DA VERDADE, mais recente).
  - Bug de timing + correção: `BUGS_CENSURA_DIAGNOSTICO.md`.
  - Análise comparativa com o n8n (fábrica de animes): `ANALISE_CENSURA_N8N_vs_HIPERCOOL.md`
    ⚠️ PARCIALMENTE DESATUALIZADA: assumia que Sightengine retorna bounding box, mas o agente
    da censura descobriu que `nudity-2.0` só dá SCORE (sem box) → solução real usa banda
    preventiva + NudeNet local. Use o HANDOFF como verdade; este doc só pra contexto do n8n.
  - Prompt de implementação (referência): `PROMPT_AGENTE_CENSURA_CIRURGICA.md`.

- **MOVIMENTO REAL nas imagens (parallax 2.5D)** — ✅ IMPLEMENTADO no pipeline 2026-06-30 ~17h.
  - Módulo `bin/parallax_engine.py` (md5 `ecf799720c963784cb80b733b7b28126`) + integração em
    `bin/hiper-pipeline.py` (md5 `15564c308edd4ca7230d6127a2bc853c`, era `1434af...`).
  - Snapshot: `bin/_VERSAO_CORRENTE_20260630_parallax/` (+ _MD5.txt). Pré-edição em
    `bin/_PRE_PARALLAX_20260630_1707/` (reverter aqui se quebrar).
  - LIGA com env **`PARALLAX=1`**. Gate: só na versão FINAL (TTS_ENGINE=gemini/eleven + censura),
    OU se o painel já tem depth no cache (prévia edge reusa), OU `PARALLAX_FORCE=1` (sempre, teste).
    `PARALLAX_TERROR=1` adiciona atmosfera (vinheta/grão/tom frio) — p/ canal de terror.
  - Cache de depth COMPARTILHADO com MotionFrames: `D:\hipercool-motionframes\cache\depth\<md5>.png`
    (override por env MOTIONFRAMES_DEPTH_CACHE). O cron do MotionFrames pré-fabrica os depths.
  - Depth real Depth-Anything-V2 (CPU; ~20s/painel sem cache, ~5s com cache). 720x1280, FPS=30.
  - FALLBACK TOTAL: qualquer falha → Ken Burns de sempre (build_clip). Default OFF = pipeline intacto.
  - ✅ Testado: módulo isolado gera clip 720x1280, áudio sync exato (dur 3.00s), usa cache.
    ⏳ PENDENTE: rodar pipeline COMPLETO com PARALLAX_FORCE=1 (render estava ativo) + aprovação visual.
  - Plano: `PLANO_AGENTE_PARALLAX_MOVIMENTO_REAL.md`. Testes: `_testes/parallax/`, `_testes/terror/`.
    Projeto MotionFrames (depth em background): `D:\hipercool-motionframes`.


## ONDE estamos trabalhando
Diretório ÚNICO: `D:\hipercool-inferior-fix`  (TTS = edge-tts)
NÃO confundir com: hipercool-videos (Gemini TTS, DESCARTADA), -inferior, -dev, -test, -BOM, -materiais.

### Teste de 1 comando pra saber se está na cópia certa:
```bash
grep -c render_subtitles_short bin/hiper-pipeline.py   # 0 = cópia ERRADA, pare | >0 = certa
```
Sintoma de cópia errada: legenda em frase inteira (devia ser 1-2 palavras estilo TikTok),
sem transições/memes inseridos entre painéis.

## 🔖 VERSÃO ATUAL DATADA (2026-06-30) — snapshot congelado
Snapshot: **`bin/_VERSAO_CORRENTE_20260630/`** (3 .py + `_MD5.txt`). Git: master, base `b9b2bc8` (não commitado).
md5 da versão de 2026-06-30:
| arquivo | md5 |
|---|---|
| effects_engine.py | `9e46ee5525d380e771f084a3f411f3ea` |
| hiper-pipeline.py | `41d44a93938a64f07e1a59993fd627d3` |
| edge_tts_engine.py | `951fdac0ad1d4a48ae8f482c1e60f194` |

## 🔥 TRANSIÇÕES ELEMENTAIS (HyperFrames alpha) + CURADORIA — adicionado 2026-06-30 (manhã)
Resolve a queixa #1 de verdade: transições ELEMENTAIS (fogo/água/gelo/rasgar) que APARECEM nos cortes.
**md5 ATUAIS no working tree (2026-06-30 tarde — elementais expandidos 4→10 efeitos, validados):**
| arquivo | md5 |
|---|---|
| effects_engine.py | `17cdb243a5961f5284cde1ee4efbf498` (era abd6→9e46) |
| hiper-pipeline.py | `102fa2534482b50699e9dfe80a2f4f27` (era 1cfc→41d4) |
| edge_tts_engine.py | `951fdac0ad1d4a48ae8f482c1e60f194` (intacto) |
| elemental_transitions.py | `c7e3effb55c4458680634010043aad3f` (era 2ce5; agora 10 efeitos) |

> ELEMENTAIS validados de ponta a ponta (2026-06-30 tarde): 10 efeitos (fire/water/ice/tear/
> smoke/lightning/shockwave/disintegrate/glitch/tvoff), todos os .mov alpha presentes, detecção
> PT/EN ok, apply() sem drift de áudio (teste 12s: vídeo=áudio=12.000s). Demo p/ aprovar:
> `_testes/ELEMENTAIS_10fx_demo_20260630.mp4`. Aprovado → congelar snapshot _VERSAO_CORRENTE_20260701.

- **`bin/elemental_transitions.py`** (NOVO): detect_element(desc)→fogo/água/gelo/rasgar por keyword PT/EN; apply() sobrepõe overlay alpha (MOV ProRes das 4 compositions HyperFrames) NOS CORTES via ffmpeg overlay, ÁUDIO=copy (não toca no concat single-pass). Anti-repetição. ELEMENTAL_FORCE=1 força efeitos em todo corte (teste).
- **`hiper-pipeline.py`**: nova lista `clip_descs` (alinhada com clips, paralela a clip_texts) + gancho pós-concat atrás de flag **`ELEMENTAL_TRANS=1`** (default OFF). Usa _CLIP_ABS_STARTS pro tempo. Fallback total: erro/sem cena elemental → vídeo intacto.
- **Assets**: `workspace/assets/overlays/elemental/trans_{fire,ice,water,tear}.mov` (alpha yuva444p12le 1080x1920, vindos de D:\hipercool-hyperframes/compositions). Vale pras DUAS versões: hyperframes-from-normal parte do normal → herda de graça.
- **CURADORIA integrada** (effects_engine.py): 25 whooshes (`whoosh_cinematic_01..25.wav` do pack, fatiado) no pool SFX_TRANSITION; `rezero_respawn.wav` (4s) sorteia 50/50 com rezero_rewind no transition "rewind". 6 trilhas aprovadas copiadas p/ trilhas/ + trilhas/prioritarias/ e registradas no moods.json com priority=true (peso 3x): cornfield_chase(épico), phonk_drift+phonk_football(tense), styxhelix_rezero+tensura(sad/emotional), lofi_fundo_podcast(funny/chill).
- **Demos pra aprovar**: _testes/ELEMENTAIS_forcado_20260630.mp4 (efeitos forçados em todo corte, sync 0.03s) e _testes/INTEGRADO_curadoria_20260630.mp4 (fluxo normal: whooshes tocando, sem cena elemental no cap01, sync 0.02s).
- **PENDENTE**: aprovação visual da usuária. Depois: congelar snapshot _VERSAO_CORRENTE_20260701 com os md5 novos. Compositions extras (desintegrar/partículas) se quiser cobrir mais elementos — pode baixar MP4 e usar como overlay no mesmo módulo.

## 🎬 HYPERFRAMES + TRANSIÇÕES ESTILIZADAS — adicionado 2026-06-30 (madrugada)
NÃO mexeu nos 3 .py do snapshot (md5 9e46/41d4/951f intactos). Aditivos:
- `bin/styled_transitions.py` (md5 `b0987604cfa1a8aab9aa2041a68cd626`) — STANDALONE, NÃO integrado ao pipeline.
  Transição de luz (blend=screen) no boundary A→B sem tocar áudio. Demo em _testes/STYLED_TRANS_ffmpeg_screen_20260630.mp4.
- `assets/overlays/transitions/_MAP.json` — catálogo: os 9 MP4 são LUZ sobre PRETO (não alpha), precisam blend=screen.
- Projeto PARALELO **D:\hipercool-hyperframes** (framework HTML→MP4 alpha real da HeyGen). Demo: _testes/HYPERFRAMES_overlay_demo_20260630.mp4.
- AGUARDANDO aprovação visual da usuária: qual estilo de transição seguir (HyperFrames alpha vs ffmpeg screen). Detalhes em logs/night-shift.md.

## 🌐 RENDER DISTRIBUÍDO (worker remoto) — adicionado 2026-06-30
Orquestração entre 2 PCs no `queue-runner.py`. NÃO mexeu nos 3 .py do snapshot (md5 acima intactos).
- `bin/queue-runner.py` md5 = `870912d8f3244e71d4aa5a3a978b47f9` (era `940b0ecf375852382fbead16d6d4ed0d`). Aditivo: flag `--workers {local,remote}`, default **local** = comportamento idêntico ao de antes.
- NOVOS: `bin/worker_client.py` (transporte HTTP, md5 `21130c8e3ac566a4d690cb9a33c5c4ba`) + `workers.json` (config de máquinas + faixas de chave Gemini por máquina).
- Worker validado: PC2 = **192.168.18.7:8771** (4 cores). Health por HTTP/`/health`, NUNCA ping (firewall Windows bloqueia ICMP).
- Medidor "vale a pena" roda ANTES de gerar: carga = nº caps × (2 se dual). < min_caps (2) → tudo local. Worker offline → fallback local sem travar.
- **PENDENTE pra funcionar de verdade** (precisa do PC2, não dá pra testar daqui): (1) PC2 precisa enxergar painéis+cache — `workspace/` é junction local p/ D:\hipercool-materiais; compartilhar via SMB ou sincronizar. (2) daemon do PC2 precisa do endpoint `POST /run-chapter` (hoje só tem `/health`+`/echo` de teste). (3) separar faixas de chave Gemini reais por máquina. Até lá, `--workers remote` cai no fallback local.
- Runbook de setup de worker: `C:\Users\Haylla\.claude-vscode\WORKER_SETUP.md`.

## 📋 CONVENÇÃO DE VERSIONAMENTO (seguir SEMPRE — a usuária faz vídeos novos toda hora)
1. ANTES de editar: `md5sum bin/*.py` e comparar com a tabela acima. Não bateu = outro agente mexeu → PARE e alinhe.
2. DEPOIS de mudança estável/aprovada, congelar snapshot datado:
   ```bash
   SNAP="bin/_VERSAO_CORRENTE_AAAAMMDD"   # ex: _VERSAO_CORRENTE_20260701
   mkdir -p "$SNAP"; cp bin/effects_engine.py bin/hiper-pipeline.py bin/edge_tts_engine.py "$SNAP/"
   md5sum bin/effects_engine.py bin/hiper-pipeline.py bin/edge_tts_engine.py > "$SNAP/_MD5.txt"
   ```
3. Atualizar a data do topo + a tabela md5 + apontar o snapshot novo. O `_VERSAO_CORRENTE_AAAAMMDD` de DATA MAIOR é sempre a verdade. Snapshots antigos = histórico, NÃO apagar.
4. NUNCA renomear o diretório (quebra venv/junction/scripts). Versionar por SNAPSHOT DATADO dentro de `bin/`.
5. NUNCA deletar `.meta.json`/logs de vídeos gerados — são a ferramenta de análise da usuária.

## ATENÇÃO: COORDENAÇÃO ENTRE AGENTES
- `workspace/` é JUNCTION pra D:\hipercool-materiais (compartilhado). Só `bin/` é por-cópia.
- SEM git commit separando versões → editar mesmo .py simultâneo = um sobrescreve o outro.
- ANTES de editar qualquer .py: rodar `md5sum bin/*.py` e comparar com a tabela acima.
  Se não bater, PARAR e alinhar (alguém editou).

## SNAPSHOT ESTÁVEL (reverter aqui se algo quebrar)
`bin/_SNAPSHOT_V6MULTIAG_HAIKU_estavel/` = esta versão (multi-agente + Haiku helpers,
validada: compila, Haiku ON ok, falha proposital HAIKU_HELPERS=0 cai no fallback sem quebrar).
Base do vídeo MULTIAG_ULTIMO (muito bom). Reverter = copiar os 6 .py de volta pra bin/.

## ARQUITETURA MULTI-AGENTE (narração) + HAIKU HELPERS
- Ensemble: lê balões por painel (N leitores) → merge_balloons une sem perder → auditor
  escolhe melhor + coverage check → placar → AUTO-TUNE reescreve pior prompt. Haiku faz
  leitura/auditoria; Opus SÓ no auto-tune. Tudo com fallback (claude_client.is_available).
- haiku_helpers.py: decisões reforçadas por Haiku, SEMPRE com fallback ao código (regra:
  se Haiku falhar/off, retorna None e o caller usa heurística atual). HAIKU_HELPERS=0 desliga.
  Integrados: detect_mood, classify_action(impacto/tensão), is_onomatopoeia(_tts_filter),
  sfx_fits(veto SFX que não cabe), is_cover_or_credit(skip por visão, opt-in HAIKU_COVER_SKIP=1),
  viral_title. persona_gender NÃO ligado (já resolvido por visão no ensemble — seria redundante).

## BUGS PENDENTES (relatados pelo usuário no vídeo MULTIAG, ainda NÃO corrigidos)
1. Transições MODERNAS (queimar/rasgar/congelar/molhar — ref: youtube shorts/wdSHuT6XyG4)
   não aparecem/não visíveis. MAIS CRUCIAL. Há 19 assets em assets/overlays/transitions/.
2. Legenda só aparece no COMEÇO; nas narrações seguintes some.
3. Painéis da ENTREVISTA com vários balões: nem todos os balões são falados.
4. Primeira fala saiu em INGLÊS (devia ser pt-BR).


## O QUE JÁ FOI FEITO E VALIDADO
1. Gap híbrido (mín 0.5s + dinâmico até teto 1.2s) — CLIP_GAP_S / CLIP_GAP_MAX / CLIP_GAP_DYNAMIC
2. SFX loudnorm (resolve mudos -77dB) + teto play 1.5s (SFX_PLAY_MAX)
3. re:zero na abertura, tela preta estilo Return by Death (INTRO_BLACK_HOLD=0.8 / INTRO_REVEAL=1.0)
4. Concat em LOTES (XFADE_BATCH=8) — resolve OOM em 30+ painéis. NÃO usar lote >8 (mata por RAM).
5. Onomatopeias filtradas (prompt visão + _strip_onomatopoeia no _tts_filter + legenda usa texto limpo)
6. TIMING DA LEGENDA na raiz (agente 2): concat_with_xfade grava posições reais de cada clip em
   effects_engine._CLIP_ABS_STARTS; a legenda usa isso (não mais fator linear) → não "desanda" aos 30s.
   + SYNC FIX no áudio: cada clip forçado a durs_eff exato (apad+atrim) → drift de centenas de ms → ~15ms.
   VALIDADO: V5TIMING usou offsets reais, sync 160.9s, 91 cards. AGUARDANDO confirmação VISUAL do usuário.

## VÍDEOS DE TESTE (em workspace/videos/_testes_espacamento/)
- V5TIMING (mais recente) — timing legenda corrigido, aguardando aprovação visual
- V4ONOMA — sem onomatopeia (era o "último bom" antes do timing)
- V3CLEAN — gap híbrido + lotes (antes da onomatopeia)

## RESTORE seguro (último ponto estável conferido por md5)
`bin/_SNAPSHOT_V5_CENSURA_COR/` = versão V5 CENSURA COR (Censura iterativa + Total Blur, Timing fixado, + hyperframes):
- effects_engine.py = d831cff640076653a20f77cd3b6e5e32
- hiper-pipeline.py = 3f1055812c4eeca986dffe91e31980ff
- _tts_filter.py    = ca70df0d77a40af2f4c1997bab339202
Reverter = copiar os 3 de _SNAPSHOT_V4ONOMA_bom/ pra bin/. (NÃO inclui o timing fix.)

## PENDENTE (lista do agente 2 — ele pode reassumir)
- [x] Censura v2 (Total Blur Baseado em Cor) implementado e Cap06 de The Meek Cat gerado 100% completo (Normal, Censurado, Hyperframes).
- [ ] Confirmação VISUAL do usuário: legenda V5TIMING acompanha até o fim, amarelo acende, não some.
- [ ] Balões longos da entrevista: prompt já ampliado p/ 40 palavras, mas precisa REGERAR narração
      via Gemini (--force-llm). Quota estava 429 em 29/06 ~11h. Rodar quando voltar.
- [ ] Transição especial por keyword (fogo→fogo): NÃO implementado ainda (grep "fogo" = 0).
      Assets de transição já existem: 19 .mp4 em workspace/assets/overlays/transitions/.
- [ ] Auditar dinamismos não-fixos + inteligência das keywords.
- [ ] Gerar capítulo COMPLETO (54 painéis), apagar antigos com defeito, deixar só os novos.

## Comando de teste (cache, sem quota, ~5min p/ 30 painéis)
```
cd /d/hipercool-inferior-fix
taskkill //F //IM ffmpeg.exe   # matar zumbis antes; NUNCA usar & com run_in_background
CLIP_GAP_DYNAMIC=1 XFADE_BATCH=8 SUB_SHORT=1 TEST_MODE=1 PYTHONUTF8=1 GEMINI_TTS_PROXY_ENABLED=0 TTS_ENGINE=edge XFADE_TRANSITIONS=1 \
  /d/hipercool-videos/venv/Scripts/python.exe bin/hiper-pipeline.py \
  --panels-dir workspace/panels/perverts-daily-life-cap01 --titulo "Teste" \
  --max-panels 30 --subtitles --skip-notify --output-suffix _TESTE
```
