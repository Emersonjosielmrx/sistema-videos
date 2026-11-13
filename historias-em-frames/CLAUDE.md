# CLAUDE.md — historias-em-frames

> **OBRIGATÓRIO ANTES DE MELHORAR QUALQUER VÍDEO (dona, 01/11):** rode `python D:\video-fila\aprendizado.py aprovados`,
> leia `D:\video-fila\aprendizado\PARA_IMPLEMENTAR.md` (todos os aprovados + os candidatos do tipo que você vai mexer) e
> marque cada um aplicado/reprovado. Ninguém mais implanta isso — se você pular, fica parado. Passo a passo:
> `D:\video-fila\aprendizado\LEIA_ANTES_DE_MELHORAR.md`. Mexeu em LONGO? Mesma obrigação em
> `D:\video-fila\linhas\LONGOS\LONGOS_MELHORIAS.md` (A FAZER / JÁ FEITO / DESCARTADO — não refazer o que já está lá).

> ESTE E O PROJETO CORRETO. Diretorio: D:\historias-em-frames.
> NAO confundir com D:\hipercool-videos, D:\hipercool-inferior-fix, D:\historias-originais.
> Se voce foi invocado de outro workspace (ex: hipercool-videos), MUDE pra ca antes de fazer qualquer coisa.

Pipeline Python de videos faceless com imagens geradas por IA (Gemini/OmniRoute/Pollinations).
Multi-genero: superacao, terror, misterio, motivacional, curiosidades, religioso, romance, comedia, drama, fantasia.
Parallax 2.5D, efeitos cineticos, memes inteligentes, elemental transitions, TTS edge-tts (keyless).

**LEITURA OBRIGATORIA (dono, 15/10): `LEIA_MELHORIAS_HIPERCOOL.md`** (fonte oficial e mais nova:
`D:\hipercool-videos\docs\MELHORIAS_PARA_TODOS_OS_PROJETOS.md`). Ao mexer neste projeto, aplique aqui o que vale pra ele:
- titulo/descricao/tags com provocacao + palavras buscadas do genero (pesquisa no autocompletar do YouTube);
- capas em rodizio com teste A/B (inclusive capas de batalha/fantasia para historias de fantasia);
- extras do Studio (`D:\postador-de-videos\bin\youtube_studio_extras.py`);
- estrutura/retencao, efeitos 2.5D.

Copie o codigo do hipercool em vez de reinventar.

**VOZES (dono, 15/10), vale aqui porque este projeto usa edge-tts:**
- `pt-BR-AntonioNeural` é PROIBIDA (Francisca e Isabella liberadas pelo dono em 16/10; Francisca = base da voz clonada).
  Hoje Antonio ainda esta em `bin/edge_tts_engine.py` (e nas copias de beta/, prod/, teste/).
- Trocar pelas Multilingual aprovadas: Thalita, Ava, Emma, Seraphina, Vivienne / Andrew, Brian, William, Florian,
  Remy, Giuseppe, Hyunsu, com variacoes de velocidade/tom.
- Voz fixa por personagem: o `edge_tts_engine.py` daqui escolhe a variacao por `hash(persona)`, que MUDA a cada
  execucao do Python. Usar md5 ou um elenco fixo, como `D:\hipercool-videos\bin\elenco.py`.
- Processos agendados nao podem abrir janela na tela: importar o equivalente de `D:\hipercool-videos\bin\sem_janela.py`.
- **Microcortes (dona, 22/10)**: em Short as pausas entre as falas saem (`narracao_curva.microcortes`, comum: pausa
  > 0,07 s vira 0,07 s, a fala NAO acelera). LIGADO aqui desde 23/10 (a dona ouviu o teste A/B e aprovou):
  `HISTORIAS_MICROCORTES` padrao 1 (`=0` desliga; corta numa copia em workspace/tmp/microcortes, nunca no
  narration_cache). Teste A/B so com cache: `_testes\teste_microcortes.py` (saida em `_testes\terror_71f9eff998_teste_microcortes\`,
  fora das pastas que o postador/rede varrem). Sobre o corte dos Shorts: quem roda e o `split_shorts.py` (etapa 11, so
  video > 90 s; com `cenas: 8` os videos tem ~57 s e nem sao cortados), que corta a cada 55 s FIXOS, nao no silencio.
  O `split-shorts.py` (hifen, corta no silencio) e herdado do manhwa e ninguem chama. `HISTORIAS_SHORTS_POR_CENA=1`
  (padrao 0) faz o `split_shorts.py` cortar nas trocas de cena (inicio de cada fala).

Detalhes: secao 4b do `LEIA_MELHORIAS_HIPERCOOL.md`.

---

## GUARDRAILS (leia SEMPRE)

1. Trabalhe SOMENTE em D:\historias-em-frames. Nunca edite arquivos de hipercool-* ou historias-originais.
2. Python SEMPRE: D:\historias-em-frames\venv\Scripts\python.exe. Desde 17/10 vira junction para o Python UNICO
   D:\hipercool-materiais\python\venv (tarefa TrocarVenvUnico troca sozinha quando o projeto esta parado e o venv
   unico tem todos os pacotes; o antigo fica em venv_antigo). prod/beta/teste\venv sao junctions para a raiz.
   Nunca criar venv proprio de novo.
2b. Fila de render entre projetos (D:\video-fila, prioridade "historias" = 4, a ultima): story_pipeline pede a vez
   na etapa RENDER e segura ate o fim. Os botoes ligam a producao; ela so renderiza quando a fila libera.
3. SEMPRE exportar PYTHONUTF8=1 antes de qualquer comando Python.
4. NAO apague caches (workspace/cache, workspace/narration_cache, workspace/images). Sao o que evita gastar tokens.
5. NAO rode 2 pipelines ao mesmo tempo (protege chaves Gemini).
6. NUNCA diga pronto sem validar com ffprobe (duracao + audio presente).
7. Imagens sao geradas por IA — censura e no-op aqui (diferente do hipercool que usa manga real).
8. NAO mexa em outro projeto. Se o prompt menciona hipercool/hermes/n8n, IGNORE ou pergunte.
9. Video ja postado (caminho em logs/videos_postados.json) sai do PC 3 dias depois e vai para o Google Drive `manhwa-drive:videos-backup/historias-em-frames/` (tarefa BackupDriveVideos, fora deste projeto). Onde esta cada video e onde ja foi postado: `D:\postador-de-videos\bin\catalogo.py`. Nao conte com o arquivo postado no disco.

---

## Ambiente

- SO: Windows 10, Git Bash
- Python: D:\historias-em-frames\venv\Scripts\python.exe
- ffmpeg: disponivel no PATH
- Proxy modelo: ANTHROPIC_BASE_URL=http://157.173.207.22:20128 (aceita antigravity/*)
- Assets: workspace\assets e junction para D:\hipercool-materiais\assets (trilhas, sfx, overlays, memes)
- Watermark: @InovareStories (env STORIES_WATERMARK)

---

## Pipeline (12 estagios)

```
[1] Roteiro (Gemini LLM)
[2] Imagens IA (OmniRoute/Pollinations, lotes de 10)
[3] Pre-scan censura (no-op neste projeto)
[4] Judge (Gemini Vision seleciona melhor variacao)
[5] TTS (edge-tts keyless, 8 workers paralelos)
[6] Render clips (parallax 2.5D + panel effects + shake + overlays + memes)
[7] Intro + Outro
[8] Concat (xfade entre clips)
[9] Pos-processamento (elemental transitions, trilha, legendas, watermark, upscale)
[10] Validacao automatica (ffprobe + quarentena se quebrado)
[11] Auto-split Shorts (corta em partes por silencio)
[12] Compilado 16:9 (converte pra paisagem em cache — compilado_longo.py)
```

Metricas: metricas_historias.py roda 1x/dia dentro do auto_producer.py.
Le views no Studio (navegador, nunca API Google) e fecha o loop A/B das capas:
views acima da mediana do canal = vitoria da pose (capa_ia_historias.registrar_resultado).
Titulos NAO sao medidos (a rede reescreve todos por canal).

Compilado crescente: `python bin/compilado_longo.py --genero terror --compilar`
junta todos os videos 16:9 num arquivo so (como os compilados de 1-4h do Porao).

---

## Comandos de producao

### Gerar 1 video (teste rapido, 6 cenas, 720p):
```bash
PYTHONUTF8=1 "D:/historias-em-frames/venv/Scripts/python.exe" D:/historias-em-frames/bin/story_pipeline.py \
  --genero superacao --tema "garoto surdo que virou DJ famoso" \
  --preset teste --output-suffix _TESTE
```

### Gerar 1 video (producao final, 30 cenas, 1080p):
```bash
PYTHONUTF8=1 "D:/historias-em-frames/venv/Scripts/python.exe" D:/historias-em-frames/bin/story_pipeline.py \
  --genero superacao --tema "menina cega que virou pianista" \
  --preset final --output-suffix _FINAL
```

### Gerar 1 video (modo noturno/autonomo, 20 cenas):
```bash
PYTHONUTF8=1 "D:/historias-em-frames/venv/Scripts/python.exe" D:/historias-em-frames/bin/story_pipeline.py \
  --genero terror --preset night --output-suffix _NIGHT
```

### Fila automatica (gera varios videos sequencialmente):
```bash
PYTHONUTF8=1 "D:/historias-em-frames/venv/Scripts/python.exe" D:/historias-em-frames/bin/queue_runner.py \
  --auto --n-per-genero 2 --preset final
```

### Fila a partir de arquivo JSON:
```bash
PYTHONUTF8=1 "D:/historias-em-frames/venv/Scripts/python.exe" D:/historias-em-frames/bin/queue_runner.py \
  --queue workspace/queue.json
```

---

## Presets disponiveis

- teste: 6 cenas, 720p, 2 workers (validar mudancas rapido)
- night: 20 cenas, 720p, 4 workers (modo autonomo)
- final: 30 cenas, 1080p, 8 workers (producao real)
- audio_only: 30 cenas, sem render, 8 workers (so gera audio)

---

## Generos disponiveis

superacao, terror, misterio, motivacional, curiosidades, religioso, romance, comedia, drama, fantasia

---

## Env vars de controle

- PYTHONUTF8=1 (OBRIGATORIO)
- TTS_ENGINE=edge (default) ou eleven (ElevenLabs pra vozes masc)
- PARALLAX=1 (efeito 2.5D profundidade)
- PANEL_FX=1 (43+ efeitos cineticos)
- ELEMENTAL_TRANS=1 (transicoes elementais alpha)
- MASCOTE_OVERLAY=1 (mascote nos cantos)
- MOTION_DIRECTOR=0 (movimento por emocao do texto)
- TEST_MODE=0 (1 = pula upscale, fica 720p)
- TTS_WORKERS=8 (paralelismo do TTS)
- STORIES_WATERMARK=@InovareStories (handle no watermark)

### Raiz x pistas (IMPORTANTE)
- A RAIZ (D:\historias-em-frames) e onde se desenvolve e testa. Os botoes da area de trabalho
  (LIGAR Prod/Beta/Teste) rodam as PISTAS prod/, beta/, teste/ — copias com venv e codigo PROPRIOS.
- Depois de mexer na raiz e testar: `venv\Scripts\python.exe sincronizar_pistas.py` (copia bin/,
  configs e a chave do gateway, conserta os assets e roda o doctor de cada pista). Sem isso a
  producao continua rodando o codigo antigo.

### Novos (2026-10-02) — todos LIGADOS por padrao; =0 desliga
- DIRETOR_CENA=1 — bin/diretor_cena.py planeja o efeito de CADA cena do video inteiro (gancho forte,
  impacto, virada de tempo com transicao de 2 imagens, ~35% recorte, giro ~1 a cada 4, nada repete
  em 6 cenas). Lista FORA = efeitos reprovados no QA visual de 7s (cor estragada, ficam pretos...).
- RECORTE_FUNDO_LIMPO=1 — recorte de personagem anima sobre o fundo SEM o personagem (inpainting).
  Sem isso aparecia rosto duplicado (charturn, charorbit, parallaxtilt...).
- DIVISORIA=1 — bin/fx_divisoria.py: "rasgo" com raio/fogo/glitch (porte do manhwa-react) no fim de
  1-2 cenas; estilo/cor por genero em ESTILO_GENERO.
- LEGENDA_ASS=1 — bin/fx_legendas_ass.py: legenda palavra a palavra com pop (tempo REAL do edge-tts),
  barra de progresso, marca d'agua e palavras de impacto num unico ASS (1 re-encode).
- AUDIO_FINAL=1 (GATILHOS_PALAVRA, SFX_CENA, LUFS_ALVO=-14) — bin/fx_audio_final.py: som por palavra
  (config/gatilhos_palavras.json, liberado por genero), som de ambiente do `sfx_hint` do roteiro e
  volume final em -14 LUFS (video copiado).
- MEMES=1 — bin/memes_catalogo.py: meme que COMBINA com a fala (config/memes_catalogo.json), so em
  genero leve.
- STORY_MODEL=<modelo> — modelo do roteiro (padrao gemini-3.5-flash-high, reservas 2.5-flash e flash-lite).
- INTRO_BLACK_HOLD=0.15 (era 0.8s de tela preta no inicio — ruim pra retencao de Shorts).
- Imagens: pedidas em 9:16 (768x1376); as antigas quadradas viram _916.png (recorte no rosto).
- Trilhas: a blocklist de copyright (hipercool-materiais/_curadoria/copyright_blocklist.json) e
  aplicada sempre (~metade das faixas por mood estava bloqueada).
- Chave do gateway: SO em secrets/omniroute.json (lida por bin/gateway_cfg.py). Nao escrever chave em codigo.
- _ULTIMO (o que o postador sobe) e criado no FIM da etapa 10 (antes saia sem upscale/mascote).

---

## Arquivos-chave

- bin/story_pipeline.py — Orquestrador principal (987 linhas)
- bin/queue_runner.py — Fila serial de videos
- bin/story_writer.py — Gera roteiro por genero via Gemini
- bin/image_generator.py — Gera imagens em lotes via OmniRoute
- bin/image_judge.py — Multi-agente seleciona melhor imagem
- bin/character_bank.py — Banco de personagens pra coerencia visual
- bin/edge_tts_engine.py — TTS keyless (edge-tts + roteamento ElevenLabs)
- bin/parallax_engine.py — Efeito 2.5D depth-based
- bin/effects_engine.py — Motor de efeitos central
- bin/fx_clips.py — Montagem ffmpeg + Ken Burns + shake
- bin/fx_music.py — Trilha dinamica por mood
- bin/fx_subtitles.py — Legendas karaoke + watermark
- bin/fx_detect.py — Deteccao de mood/impacto/tensao
- bin/elemental_transitions.py — Transicoes alpha (fogo/agua/raio)
- bin/panel_effects.py — 43+ efeitos de painel
- bin/mascote_overlay.py — Overlay da mascote
- bin/auto_validate.py — Validacao ffprobe + quarentena
- bin/omniroute_image.py — API de geracao de imagens
- bin/viralizador.py — Titulos virais + SEO
- bin/hp_common.py — Constantes e paths do projeto

---

## Estrutura de saida

Os VIDEOS PRONTOS saem SEMPRE em hipercool-materiais (cada projeto grava os videos la, nunca
dentro da propria pasta). Caminho = `<materiais_dir do settings.json>\videos\<pista>`:
```
D:\hipercool-materiais\historias-em-frames\videos\
  prod\<genero>\<story_id>\vN_FINAL.mp4 + vN_FINAL_ULTIMO.mp4 (o que o postador sobe) + thumb/json
  prod\_quarantine\      <- videos que falharam validacao
  prod\_shorts\          <- shorts cortados (videos > 90s)
  beta\ teste\           <- saida das outras pistas
  dev\                   <- testes feitos na RAIZ (pista "dev")
```
Dentro do projeto ficam so os caches de trabalho (workspace/):
```
workspace/
  cache/           <- roteiros em cache (nao apagar)
  images/          <- imagens geradas (nao apagar)
  narration_cache/ <- TTS em cache (nao apagar)
  stories/         <- roteiros salvos
  tmp/             <- temporarios (pode limpar)
```

---

## Command Files (controle manual)

Criar estes arquivos na raiz do projeto pra controlar o pipeline em execucao:
- COMMAND_STOP.txt -> aborta imediatamente
- COMMAND_PAUSE.txt -> pausa ate o arquivo ser removido
- COMMAND_SKIP.txt -> pula o video atual e vai pro proximo

---

## Validacao de video (OBRIGATORIO antes de dizer pronto)

```bash
ffprobe -v error -select_streams v:0 -show_entries stream=duration -of csv=p=0 "workspace/videos/ARQUIVO.mp4"
ffprobe -v error -select_streams a:0 -show_entries stream=duration -of csv=p=0 "workspace/videos/ARQUIVO.mp4"
```
Se audio >5s menor que video = QUEBRADO (vai pra quarentena).

---

## Diferencas vs hipercool-fix (NAO CONFUNDIR)

- historias-em-frames: imagens IA geradas, censura no-op, roteiro gerado por Gemini, TTS keyless
- hipercool-fix: manga real scaneado, censura obrigatoria, roteiro extraido por visao, TTS Gemini

---

## Modo autonomo (pra crons e loops)

1. Usar preset night (equilibra qualidade e velocidade).
2. Gerar 1 video por vez (nunca paralelo).
3. Registrar resultados em logs/night-shift.md.
4. Se falhar, registrar o erro e tentar o proximo genero.
5. NUNCA commit/push sem confirmacao da dona.
6. NUNCA sair deste projeto pra trabalhar em outro.
