# ARQUIVOS PARA APAGAR — D:\recapd-e-animes

> **Data:** 2026-07-25
> **Escopo:** manter SÓ o pipeline de **recap de anime YouTube** (definido em `LEIA_PRIMEIRO_ANIME.md`).
> Apagar tudo do pipeline **manhwa/hipercool** (imagens → vídeo) que está copiado aqui mas não é usado.
>
> ⚠️ **NADA FOI APAGADO AINDA.** Este doc é a proposta. Você precisa revisar e confirmar antes de qualquer `rm`.
>
> **Regra:** se tem dúvida se X é usado pelo pipeline anime → marcar como **DÚVIDA**, não apagar.
>
> Última checagem: rodei `anime-pipeline.py` em modo deitado com source.mp4 existente → renderizou OK em 11.27s, 1280×720, áudio 11.26s. Pipeline anime confirmado funcional.

---

## 🚨 ACHADO CRÍTICO: JUNCTIONS COMPARTILHADAS

**Os 42 GB NÃO são cópias reais** — são **5 junctions** que apontam pra um único lugar: `D:\hipercool-materiais\`.

| Pasta (em `recapd-e-animes\workspace\`) | Aponta pra | Tamanho aparente |
|---|---|---|
| `assets` | `D:\hipercool-materiais\assets` | 6.4 GB |
| `narration_cache` | `D:\hipercool-materiais\narration_cache` | 2 MB |
| `panels` | `D:\hipercool-materiais\panels` | 11.7 GB |
| `tts_cache` | `D:\hipercool-materiais\tts_cache` | 6.6 GB |
| `videos` | `D:\hipercool-materiais\videos` | 17 GB |

**As MESMAS 5 junctions existem em TODAS as 5 cópias do projeto:**
- `D:\recapd-e-animes`
- `D:\hipercool-inferior-fix`
- `D:\hipercool-producao`
- `D:\hipercool-videos`
- `D:\hipercool-fix2` (tem +1: `workspace/depth` → `D:\hipercool-motionframes\cache\depth`)

**O espaço real vive UMA VEZ em `D:\hipercool-materiais\`** (~42 GB ali). Apagar via `recapd-e-animes\workspace\videos\the-meek-cat\` = apagar do `D:\hipercool-materiais\videos\the-meek-cat\` também = afeta as 5 cópias.

**Anime pipeline NÃO USA essas junctions** — ele escreve em `workspace/anime/<video_id>/` (pasta real, não-junction). Confirmado rodando o pipeline.

### Implicações pra limpeza

- ✅ Pode apagar **as junctions** de `recapd-e-animes\workspace\` se quiser limpar o acesso daqui (os arquivos continuam em `D:\hipercool-materiais\` pra outras cópias usarem). Mas **NÃO apague os arquivos de dentro das junctions** sem pensar — quebra pras outras cópias.
- ✅ Pode apagar `D:\hipercool-materiais\videos\the-meek-cat\` (16.9 GB) **se você não precisa mais** dele em nenhum dos projetos — mas é a única pasta "real" desse tamanho.
- ⚠️ Os scripts do pipeline anime **não usam** essas junctions, mas o `anime-pipeline.py:87` ainda referencia `D:/hipercool-inferior-fix/workspace/assets/trilhas` (legado).

---

## 🟢 ATIVO DO PIPELINE ANIME (NÃO APAGAR)

### Scripts `bin/anime_*.py` (entry points)
- `anime_auto.py`, `anime-pipeline.py`
- `anime_discover.py`, `anime_fetch.py`, `anime_probe.py`
- `anime_script.py`, `anime_tts.py`, `anime_captions.py`
- `anime_compose.py`, `anime_segments.py`, `anime_metrics.py`
- `anime_night_shift.py`, `anime_worker_client.py`, `anime_worker_loop.py`, `anime_worker_daemon.py`
- `anime_post_history.py` (verificar uso)

### Módulos de suporte USADOS pelos `anime_*`
- `claude_client.py` — usado por `anime_script.py`
- `viralizador.py` — usado por `anime_tts.py`, `anime_script.py` (anti-ban)
- `edge_tts_engine.py` — usado por `anime_tts.py`
- `fx_assets.py` — usado por TODOS (W/H, ANIME_ORIENT)
- `fx_clips.py` — usado por `anime_segments.py` + `anime-pipeline.py` (motor)
- `fx_detect.py` — usado por `anime_segments.py`
- `fx_subtitles.py` — usado por `anime_captions.py`

### Documentação ativa do pipeline anime
- `LEIA_PRIMEIRO_ANIME.md` ← entrada oficial
- `INDEX.md` (índice geral)
- `POSTAGEM_YOUTUBE_PLAYBOOK.md` (postagem)
- `COMO_POSTAR_CAPITULO_NOVO.md`
- `GUIA_OPERACAO_SCRAPE_SPLIT.md`
- `COMO_SALVAR_VERSAO.md`
- `SINTOMA_CAUSA_FIX.md`
- `CHECKLIST_VIDEO.md`
- `INSTRUCOES_PC2_WORKER.md`
- `INSTRUCOES_PC2_WORKER.md`
- `requirements.txt`

### Snapshots oficiais (manter como backup)
- `bin/_SNAPSHOT_ANIME_20260712_2200/` ← ÚNICO snapshot do anime (referência)

### Configs/secret
- `secrets/`
- `workers.json` (config worker)

### Workspace anime (dados do pipeline YouTube)
- `workspace/anime/` ← 218 MB, saídas do pipeline anime

### Output postado
- `postados/anime/` ← vídeos já postados no YouTube
- `postados/_INDEX.csv`

### venv
- `venv/` ← usado pelo Python do pipeline

---

## 🔴 LIXO ÓBVIO (pipeline manhwa — não usado pelo anime) — APAGÁVEL

### Total estimado: ~17 GB (workspace) + ~6 MB (backups)

### A. Pasta raiz — scripts `.py` soltos do pipeline manhwa

Estes são do pipeline **manhwa/imagens** (`hiper-pipeline.py`, `effects_engine.py`, `panel-splitter.py`, etc.) — **não usados** pelo pipeline anime:

```
agy_video_bridge.py
amostra_overlay_censura.py
audio_factory.py
auto-validate.py                # validador manhwa
batch-post-shorts.py            # postagem manhwa
batch_image_gen.py
batch_image_stress.py
censura_visual.py
classificar_copyright.py
compile_guards.py
config.py
content_analyzer.py
contextual_motion.py
curadoria.py
doctor.py                       # raio-x manhwa
dual-pipeline.py
duracao_protegidos.py
duracao_sfx.py
effects_engine.py               # 1.6 KB stub; o real é fx_clips.py
effects_memory.py
elemental_transitions.py
elevenlabs_tts.py
fix_hiper_pipeline.py
fix_indent.py
fx_music.py                     # música dinâmica (manhwa); só se anime usa, verificar
fx_foley.py                     # foley (manhwa); NÃO usado pelo anime
gemini_llm.py
gemini_tts.py
gem_audio.py
gerar_blocklist.py
gerar_obra.py
haiku_helpers.py
hiper-fetcher.py                # downloader manhwa
hiper-pipeline.py               # pipeline principal manhwa
hp_common.py
hyperframes-from-normal.py
landscape-compiler.py
landscape_filters.py
listar_protegidos.py
mascote_overlay.py
master_loudness.py
montar-fila-tutoriais.py
montar-fila.py
motion_director.py
musicgen_local.py
narration.py
narration_ensemble.py
night-shift-driver.py
omniroute_image.py
omniroute_music.py
omniroute_tts.py
organizar_videos.py
painel-progresso.py
panel-splitter.py               # corta painéis
panel_classifier.py
panel_effects.py
panel_effects_ext.py
panel_fx_auto.py
parallax25d.py
parallax_engine.py
postagem_meta.py
postar-fila.py
preview_config.py
proxy_router.py
queue-runner.py
separar_trilha.py
sfx_categorizer.py
smoketest.py
split-shorts.py
status.py
styled_transitions.py
sync_obras.py
tia-fetcher.py
tts_cache.py
tts_stage.py
video_factory.py
viralizador_backup_20260705.py  # backup velho do viralizador (manter ATUAL `viralizador.py`)
worker_client.py
youtube_poster.py               # postagem geral — DÚVIDA: pode ser usado pelo anime_post
```

### B. Pasta raiz — `.sh` / `.bat` / scripts de orquestração manhwa

```
download-caps.sh
patch_painel_final.py
rebuild-no-ai.sh
run-chapters.sh
run-gemini-v1.sh
run_cap.bat
run_cap01.bat
run_cap05.bat
run_painel_html.bat
run_patch.py
run_infinite_shorts.sh
separa_combo.py
start_painel.bat
veja_o_log.bat
```

### C. Pasta raiz — testes/debug one-off

```
test_ascii.py
test_effects.py
test_effects2.py
test_effects3.py
test_lumakey.py
test_lumakey2.py
test_lumakey3.py
test_mascara_balao.py
testa_will_divisao.py
testa_will_protect.py
testa_will_tudo.py
teste_cap6.py
teste_imagens.py
teste_real_cap06.py
test_all_voices.py
test_discover_shorts.py
test_lyria_musicas_18plus.py
test_lyria_openings_obras.py
test_lyria_vocal.py
test_lyria_vocal_only.py
test_omniroute_all.py
test_omniroute_complete.py
test_omniroute_voices.py
test_retry_failed.py
test_vozes_fala_pura.py
patch_auto.py
patch_auto_metrics.py
patch_discover.py
patch_discover2.py
descobrir_animes_shorts_na_cota.py
audit_orientacao_short.py
```

### D. Pasta raiz — arquivos `_b64_*.txt` (basename64 de backups antigos)

Estes são cópias base64 de scripts antigos (não usados — os reais são os `anime_*.py`):

```
_b64_bin__whisper_sub.py.txt
_b64_bin_anime_auto.py.txt
_b64_bin_anime_discover.py.txt
_b64_bin_anime_fetch.py.txt
```

### E. Pasta raiz — scripts `_check_*.py` / `_clear_attempted.py` / `_drives.py`

```
_check_attempted.py
_check_mods.py
_check_mtimes.py
_check_now.py
_check_pc2.py
_check_uCJ.py
_check_venv.py
_check_whisper.py
_check_worker.py
_check_worker2.py
_check_worker3.py
_clear_attempted.py
_d_out_local.txt
_drives.py
_feitos_attempted.txt
_tg_safe.py
_tts_filter.py
_whisper_sub.py                 # versão `_` (whisper inline); o real tá em bin/_whisper_sub.py
_noona_scrape_split.py
_scrape_split_obra.py
_sync_bin.py
_sync_script.py
_build_template.py
fix.py
fix_blur.py
fix_indent_painel.py
fix_painel_end.py
fix_painel_html.py
fix_painel_loop.py
fix_painel_syntax.py
fix_syntax.py
gen_antigos.py
gen_antigos_real.py
gen_bateria.py
gen_combo.py
gen_combo_niveis.py
gen_combo_niveis_blur.py
gen_combo_niveis_blur_fix2.py
gen_combo_niveis_blur_real.py
gen_combo_niveis_fix.py
gen_comparativo_final.py
gen_comparativo_final_fix.py
gen_exodia_fix.py
```

### F. Pasta raiz — snapshots/versões velhas do manhwa (`*.bak`)

```
bin/_PRE_PIPESPLIT_hiper-pipeline.py.bak   # 110 KB
bin/_PRE_SPLIT_effects_engine.py.bak       # 173 KB
bin/_PRE_SPLIT_hiper-pipeline.py.bak       # 105 KB
bin/_reference_n8n_effects_FULL.js         # 287 KB
bin/_reference_n8n_effects_V2.js           # 283 KB
```

### G. Pasta `bin/_BACKUP_20260707/` (6.7 MB)

Backup inteiro do projeto manhwa em 2026-07-07. Se o snapshot atual (`bin/_SNAPSHOT_ANIME_20260712_2200/`) cobre o anime, **este backup inteiro é apagável**.

### H. Pasta `bin/_snapshots/` (15 subpastas — todas do manhwa)

`_bkp_cron_0557`, `_estavel_20260629`, `_ESTAVEL_20260629_1751`, `_PRE_PARALLAX_20260630_1707`,
`_SNAPSHOT_ENSEMBLE_HAIKU`, `_snapshot_pre_haylla_1132`, `_SNAPSHOT_V4ONOMA_bom`,
`_SNAPSHOT_V5_CENSURA_COR`, `_SNAPSHOT_V6MULTIAG_HAIKU_estavel`,
`_VERSAO_CORRENTE_20260630`, `_VERSAO_CORRENTE_20260630_efeitos21`,
`_VERSAO_CORRENTE_20260630_ELEMENTAL`, `_VERSAO_CORRENTE_20260630_parallax`,
`_VERSAO_CORRENTE_20260701_FIXCENSURA`, `_VERSAO_CORRENTE_20260701_FIXSYNC`,
`_VERSAO_CORRENTE_20260702_V7CENSURACOR`, `_VERSAO_CORRENTE_20260703_V8OFICIAL`

TODOS são snapshots do pipeline **manhwa**. Apagáveis se você não precisar voltar a versões antigas dele.

### I. Pasta raiz — logs / txt / tmp / json de debug

```
all_img_tags.txt
cap11.txt
help.txt
img_tags.txt
temp_analyze_scores.py
temp_copy_censura.py
temp_copy_censura_unica.py
temp_list_censura.py
tmp_ex_censurado.jpg
tmp_ex_hyperframes.jpg
tmp_template.html
tmp_template_v3.html
update_versao.tmp
update_versao2.tmp
xfade_debug_full.txt
logs/                           # logs do manhwa
```

### J. Pasta raiz — docs do manhwa (não se aplicam ao anime)

```
_ANIME_REGRAS_BANIMENTO.md? (verificar)
ANALISE_BANIMENTO_LINHA_2026-07-22.md
AUDITORIA_REFACTOR_E_FABRICAS.md
CHAT_INCIDENTE_E_LIMITE_2026-07-22.md
CLAUDE.md
CORRECOES_HERMES_2026-07-22_v2.md
HANDOFF-AGENTE-FALHA-CENSURA.md
HANDOFF-AGENTE-MAC-INOVARE-CLAW.md
HANDOFF_PROXIMO_AGENTE.md
INSTRUCOES_WORKER.md
INOVARE-CLAW-V2-PLANO.md
LEIA_PRIMEIRO.md                # LEIA do manhwa, IGNORAR (o do anime é LEIA_PRIMEIRO_ANIME.md)
LEIA_PRIMEIRO_ANIME.md          # MANTER
MONETIZACAO_OST_INFO.md
PEDIDO-SOURCE-PRO-MAC.md
PENDENCIAS_CACHE_AUDIO_E_TTS.md
PLANO_AGENTE_PARALLAX_MOVIMENTO_REAL.md
PONTOS_CHAMADA_HERMES_CALL.md
PROMPT_CHAT2_CONTAS_GOOGLE.md
PROMPT_DEPLOY_AGENTE.md
PROMPT_DEPLOY_CHAMADA_FULLDUPLEX.md
PROMPT_FINAL_v5.md
PROMPT_NOVO_AGENTE.md
PROMPT_OUTRO_AGENTE.md
PROMPT_PC2.txt
PROMPT_WORKER_ANIME_PC2.md     # MANTER (relacionado ao anime)
REGRAS_LOWERTHIRD_E_MASCOTE.md
ROTEIRO_DEMONSTRACAO_HERMES.md
TAXONOMIA_EFEITOS_3_CATEGORIAS.md
_LEIA_FLUXO_PRODUCAO_E_CENSURA.md
_VERSAO_CORRENTE_LEIA.md
```

### K. Workspace — junctions compartilhadas (NÃO apagar o conteúdo sem pensar!)

```
# Estas pastas em recapd-e-animes\workspace\ são JUNCTIONS pra D:\hipercool-materiais\
# O conteúdo mora em D:\hipercool-materiais\ (fonte da verdade das 5 cópias).
# Anime pipeline NÃO USA essas pastas — usa workspace/anime/ (real).
workspace/videos/                 # → D:\hipercool-materiais\videos        (17 GB)
workspace/panels/                 # → D:\hipercool-materiais\panels        (11.7 GB)
workspace/tts_cache/              # → D:\hipercool-materiais\tts_cache     (6.6 GB)
workspace/assets/                 # → D:\hipercool-materiais\assets        (6.4 GB)
workspace/narration_cache/        # → D:\hipercool-materiais\narration_cache (2 MB)

# Pastas REAIS do workspace (não-junction) — também não usadas pelo anime:
workspace/depth_layers_cache/
workspace/clipes/
workspace/panel_class_cache/
workspace/dashboard/
workspace/factory_state/
workspace/silence_cache/
workspace/tmp/
workspace/motion_direction_cache/
workspace/postagem/
workspace/content_analysis_cache/
workspace/tmp_frames/
```

### L. Diretórios de trabalho / cache one-off

```
_amostras_overlay_censura/
_censura_especial/
_fetch_test/
_HANDOFFS_FEITOS/
_testes/
_test_pipeline/
_test_short_work/
melhor_censura_backup/
TAREFAS_AGENTE/
material/
codigos-legado/
docs/
fabrica-viral/                 # pipeline de imagens (geração de painéis virais) — MANHWA
MELHORIAS_EXTERNAS/
models/
```

---

## 📋 RESUMO DE TAMANHOS (REVISADO pós-junction)

**Espaço real ocupado pelo projeto inteiro:**

| Local | Tamanho real | Natureza |
|---|---|---|
| `D:\hipercool-materiais\` | ~42 GB | Materiais centrais (fonte da verdade — usado pelas 5 cópias) |
| `D:\recapd-e-animes\` (excluindo workspace) | ~300 MB | Scripts + venv + workspace/anime + postados |
| `D:\hipercool-materiais\videos\the-meek-cat\` | **16.9 GB** | O grandão real — pipeline manhwa |

**O que está em `recapd-e-animes\workspace\videos\` (17 GB aparente) = é `D:\hipercool-materiais\videos\`. Não tem cópia extra.**

### Lotes de limpeza propostos (recapd-e-animes específico)

| Lote | O que apaga | Tamanho liberado | Risco |
|---|---|---|---|
| **1** | Scripts `.py`/`.sh`/`.bat` raiz do manhwa (A+B) | ~9 MB | ZERO (anime não importa nenhum) |
| **2** | Tests/debug/scripts `_check_*/patch_*/fix_*/gen_*` (C+D+E) | ~1 MB | ZERO |
| **3** | `bin/_BACKUP_20260707/` (G) | 6.7 MB | ZERO (existe snapshot anime) |
| **4** | `bin/_snapshots/` 15 subpastas manhwa (H) | ~5 MB | BAIXO se não for voltar versões antigas |
| **5** | Docs .md/.txt/.json manhwa na raiz (J) | ~200 KB | ZERO (anime tem LEIA_PRIMEIRO_ANIME.md) |
| **6** | One-off: `_amostras_/`, `_censura_/`, `_fetch_test/`, `_test*`, `TAREFAS_AGENTE/`, `MELHORIAS_EXTERNAS/`, `melhor_censura_backup/` (L) | ~5 MB | MÉDIO (pode ter handoffs do anime) |
| **7** | `bin/_PRE_*.bak`, `_reference_n8n_*.js` (F) | ~1 MB | ZERO |
| **8** | **JUNCTIONS** `workspace/{assets,panels,tts_cache,videos,narration_cache}` | 0 bytes (libera acesso) | MÉDIO — afeta as 5 cópias |
| **9** | `D:\hipercool-materiais\videos\the-meek-cat\` (16.9 GB) | **16.9 GB reais** | ALTO — só se não precisa mais em nenhum projeto |

**Total seguro pra apagar DE `recapd-e-animes`:** ~25 MB (lotes 1-7).

**Se quiser recuperar espaço REAL:** lote 9 (16.9 GB no `hipercool-materiais`) — mas exige você confirmar que the-meek-cat não é mais usado.

---

## ⚠️ PONTOS DE DÚVIDA (NÃO APAGAR SEM CHECAR)

1. **`fx_music.py`** — importado indiretamente via `effects_engine.add_dynamic_music` (chamado pelo `anime-pipeline.py:98`). **MANTER** se a música dinâmica for desejada no anime.
2. **`viralizador_backup_20260705.py`** — `viralizador.py` é o ativo; backup é descartável.
3. **`postar_animes.py` vs `postar_animes_ate_bloquear.py`** — ambas anime. Ver qual é a ativa.
4. **`anime_post_history.py`** — confirmar se ainda é usado pelo `postar_animes`.
5. **`youtube_poster.py`** — postagem geral. Se o anime usa o próprio `postar_animes.py`, pode apagar.
6. **`MELHORIAS_EXTERNAS/`, `TAREFAS_AGENTE/`, `_HANDOFFS_FEITOS/`** — podem ter histórico de decisões do anime; vale conferir antes de apagar.
7. **`secrets/`** — chaves de API, manter SEMPRE.
8. **`models/`** — se tem modelo local (Whisper?), manter.
9. **`postados/_INDEX.csv`** — manter (índice de vídeos postados).

---

## ✅ PRÓXIMOS PASSOS

1. Você revisa este doc.
2. Marcamos juntos o que vai e o que fica.
3. Apago em **lotes** (não em massa) — workspace, depois bin/, depois raiz — com confirmação sua antes de cada um.
