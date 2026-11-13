# 🚨 LEIA OBRIGATÓRIO — FLUXO DE PRODUÇÃO, CENSURA E RE-TRABALHO

Atualizado: **2026-07-02** (censura agora é VISUAL NA IMAGEM do painel — EXODIA_FOSCO/TOTAL_BLUR).
Cópia certa: **`D:\hipercool-inferior-fix`** (edge-tts). Confira sempre `_VERSAO_CORRENTE_LEIA.md`.

> 🔴 **MUDANÇA IMPORTANTE (2026-07-02) — A CENSURA MUDOU DE MÉTODO.**
> Antes: tarja/cor por JANELA DE TEMPO no vídeo pronto (`effects_engine.censurar_video`).
> **Agora: censura na IMAGEM do painel** via `censura_visual.censurar_imagem`, com 2 níveis:
> **NIVEL1_EXODIA_FOSCO** (leve — borra o fundo mas preserva balões/onomatopeia nítidos) e
> **NIVEL2_TOTAL_BLUR** (forte — GaussianBlur 251 derrete tudo). O `hiper-pipeline.py` detecta
> os painéis +18, **reconstrói só esses clips a partir da imagem censurada** e monta a derivada
> `_CENSURADO_ULTIMO.mp4`. O vídeo principal continua LIMPO. **`effects_engine.censurar_video`
> (tarja) e os modos `CENSURA_MODO`/`CENSURA_FORTE_MODO` NÃO valem mais** no fluxo do pipeline —
> viraram código legado. Ver seção 1.

> ⛔ **POR QUE ESTE DOC EXISTE:** em 2026-07-01 um agente gastou HORAS pra chegar num resultado de
> censura que outro agente já tinha alcançado antes. O erro foi tratar sintoma (limiar, método de
> tarja/blur) em vez de achar a CAUSA RAIZ. Se você vai mexer em censura, produção, ou re-gerar
> um capítulo, **leia este doc inteiro primeiro**. Não repita o desperdício.

---

## 0. REGRA DE OURO AO DEBUGAR (não pule)
Quando um painel/cena está errado na censura, **NÃO comece mexendo em limiar nem no método visual**.
Siga esta ordem de diagnóstico (foi ela que resolveu de vez):

1. **Isole o clip**: descubra o tempo (t) do problema no vídeo. Ache o clip pelo `.timing.txt`
   (dump gerado com `DUMP_SUBS_TIMING=1`, fica ao lado do mp4 final). `clipNN start=… dur=…`.
2. **Mapeie clip → painel**: no log (`logs/cap05_recensuraN.log`) a linha `Clip NN/…  painel=panel_XXX.jpg`.
   ⚠️ O log de "marcado +18/LEVE" usa índice 0-based do loop (painel 10 = `panel_011.jpg`). Não confunda.
3. **Cheque a DETECÇÃO daquele painel** (é quase sempre aqui que está o bug):
   ```bash
   cd D:/hipercool-inferior-fix/bin
   PYTHONUTF8=1 D:/hipercool-videos/venv/Scripts/python.exe -c "
   import censura_visual as cv, json
   det = cv.detectar_score('../workspace/panels/<obra>/panel_XXX.jpg')
   print('score composto:', det[0]); print(json.dumps(det[1], indent=1, ensure_ascii=False))"
   ```
   - Se o **score composto** está baixo mas o dict tem `erotica` alto ou `nudity.none` baixo (=muita
     nudez) → é bug de FÓRMULA (veja seção 1). NÃO é limiar.
   - Se o score está certo mas a tarja cai no tempo errado → é bug de TIMING (`_CLIP_ABS_STARTS`,
     ver `BUGS_CENSURA_DIAGNOSTICO.md`).
   - Se o score está certo e o tempo certo, mas a tarja/borrão está feio → aí sim é método visual.
4. **Confirme com frames** antes e depois (prova objetiva, não confie no olho):
   ```bash
   for t in 36 38 40 42; do ffmpeg -y -ss $t -i CENSURADO.mp4 -frames:v 1 /tmp/f$t.png 2>/dev/null; done
   python -c "from PIL import Image;
   [print(t,'tarja' if max(Image.open(f'/tmp/f{t}.png').convert('RGB').getpixel((360,960)))<25 else 'LIMPO') for t in [36,38,40,42]]"
   ```

---

## 1. CENSURA — como funciona (estado 2026-07-02, censura na IMAGEM)

### Fórmula de score (CAUSA RAIZ dos dois bugs históricos) — `bin/censura_visual.py`, `_score_ponderado`
O Sightengine `nudity-2.0` devolve vários sinais. Arte de manhwa com nu à mostra pontua **ALTO em
`erotica`** e **BAIXO em `sexual_activity/sexual_display`** — ignorar `erotica` (bug de 2026-07-01)
deixava painel explícito passar batido.

Mas o oposto também era bug (2026-07-02): `suggestive` e `1 - none` disparavam com **QUALQUER**
personagem feminina vestida/atraente (violão, notebook, amiga) → tarja preta em cena INOCENTE.
O Sightengine derruba `none` quando marca "suggestive", então tanto `suggestive*0.5` quanto o
`1 - none` inflavam o score de cenas sem nudez nenhuma.

**Fórmula CORRETA (atual, 2026-07-02):**
```python
score = activity*2.0 + display*1.5 + erotica*1.2   # SÓ sinais de nudez real
```
> ⚠️ NUNCA reintroduza `suggestive` nem `1 - none` sem override manual — foram a causa dos
> falso-positivos. `erotica` já pega o nu ESTÁTICO (peito à mostra sem ato), que era o motivo
> original de usar `1-none`, então nada de explícito passa batido.
> ⚠️ NUNCA volte a ignorar `erotica` — é o que pega nudez de manhwa.

### Limiares (níveis) — constantes de `bin/censura_visual.py`
- `score >= LIMIAR_NSFW` (**default 1.15**, env `CENSURA_LIMIAR_NSFW`) → **NIVEL2_TOTAL_BLUR (forte)**.
- `LIMIAR_DUVIDA <= score < NSFW` (**default 0.45**, env `CENSURA_LIMIAR_DUVIDA`) → **NIVEL1_EXODIA_FOSCO (leve)**.
- `score < LIMIAR_DUVIDA` → **intacto** (painel passa limpo).

### Os 2 métodos VISUAIS (na IMAGEM do painel) — `censura_visual.censurar_imagem`
Estas são as funções que a usuária validou (referências geradas por `processar_painel` em
`teste_real_cap06.py`, guardadas em `D:\downloads\will_protect_NOVOS_NIVEIS\TESTE_DO_BOT_DA_SILVA\`).

- **NIVEL1_EXODIA_FOSCO (leve):** borra o FUNDO forte mas **preserva os balões e a onomatopeia
  nítidos por cima**. Receita (4 passos, NÃO altere sem regenerar as referências):
  1. FFmpeg base: `negate` → downscale pixelado (`scale=iw/25` e volta `neighbor`) → `hue=s=0` (cinza)
     → `noise=alls=60` → mescla 70% branco (`drawbox ... white@0.7`).
  2. Lumakey: extrai os balões da original por luminância (~85%) e sobrepõe.
  3. OpenCV: `GaussianBlur (251,251)` no cenário borrado.
  4. Máscara final: máscara exata dos balões na original (`threshold>240`, dilata/erode) e mistura
     de volta → texto perfeito por cima, fundo distorcido.
  > Nota: o passo 1 usa `noise` sem semente → o leve NÃO é bit-a-bit reproduzível (varia ~2%). Se
  > precisar travar, `noise=...:seed=42`. Visualmente é idêntico.
- **NIVEL2_TOTAL_BLUR (forte):** sem refinamento, sem preservar balões: `GaussianBlur((251,251))` na
  cor bruta (BGR) → flash amorfo onde NADA (texto/cena/personagem) é reconhecível.

### Como está PLUGADO no pipeline (2026-07-02) — `bin/hiper-pipeline.py`
Só com `--censura`. NÃO usa mais janelas de tempo nem `effects_engine.censurar_video`:
1. **Detecta** cada painel com `censura_visual.detectar_score` (Sightengine, cache md5). +18 = score ≥ 0.45.
2. Num passo pós-loop **reconstrói SÓ os clips +18** a partir da imagem censurada (`censurar_imagem`),
   com os MESMOS efeitos/duração do clip limpo → timeline idêntica.
3. Monta a derivada `_CENSURADO_ULTIMO.mp4`: concat dos clips (com os +18 trocados) + MESMA trilha +
   **MESMAS legendas do principal** (timeline igual) + upscale. **O vídeo principal fica LIMPO.**
4. Log por painel: `panel_XXX → forte|leve (score=…)`. Se sair `0/N censurados`, deu erro no rebuild.

> ⚰️ **LEGADO (não é mais chamado no pipeline):** `effects_engine.censurar_video` (tarja/cor por
> janela), e os envs `CENSURA_MODO`/`CENSURA_FORTE_MODO`, `LIMIAR_NSFW`/`LIMIAR_DUVIDA` (do fluxo de
> janela). O `_negativo_pele` e o lumakey também não entram no fluxo atual. Ficam como referência.

### Cache de detecção recalcula sozinho (zero tokens)
`detectar_score` guarda o **dict cru** do Sightengine em `workspace/censura_cache/<md5>.json` e
**recalcula o score na leitura**. Logo, mexer na fórmula/limiar NÃO re-chama a API — os painéis já
cacheados pegam a regra nova de graça. **Re-rodar `--censura` num capítulo já detectado = zero tokens.**
(Detalhes de TODOS os caches na seção 1.5.)

---

## 1.5 COMO APROVEITAR O CACHE (regra: re-render ≈ zero tokens)

A parte CARA é a IA (visão Gemini + TTS + Sightengine). **Tudo isso é cacheado em disco.** Re-rodar
um capítulo que já foi gerado uma vez reaproveita quase tudo → **quase zero tokens/quota**. Só regera
o que realmente mudou. NÃO apague estas pastas de `workspace/`:

| Cache | Pasta / arquivo | Chave | Quando regenera | Custo |
|---|---|---|---|---|
| **Narração / roteiro (visão IA)** | `narration_cache/<obra>_<N>panels.json` | obra + nº de painéis | só com `--force-llm` ou se mudar nº de painéis | Gemini |
| **Áudio / TTS** | cache do `bin/tts_cache.py` (por voz) | texto + voz + engine | muda o TEXTO ou a VOZ/engine daquele clip | edge=grátis, gemini/eleven=$ |
| **Detecção +18 (Sightengine)** | `censura_cache/<md5>.json` | md5 do painel | só se a IMAGEM do painel mudar (md5) | Sightengine (free tier) |
| **Classe/scene do painel** | `panel_class_cache/`, `content_analysis_cache/`, `nsfw_image_cache.json` | md5/painel | idem | IA leve/local |
| **Direção de movimento** | `motion_direction_cache/` | painel | idem | local |

**Regra de ouro:** mesma pasta de painéis + mesmo `--titulo` + mesma voz ⇒ narração, censura e TTS
vêm do cache. Um re-render (mexeu em efeito/censura/transição/legenda) é **só CPU de ffmpeg** — não
gasta token. Foi assim que o teste do cap06 com `--censura` rodou (todo TTS `[CACHE]`, Sightengine
`[CACHE]`, narração `[CACHE]`).

**Forçar regeneração (use com parcimônia, gasta):**
- `--force-tts` → regera os WAVs (útil se um áudio saiu quebrado). Em `TTS_ENGINE=edge` é grátis.
- `--force-llm` → ignora o cache de narração e re-chama o Gemini. Só se o roteiro precisa mudar.
- Trocar `--titulo` ou o nº de painéis MUDA a chave do cache de narração → regera (evite sem querer).

**Sightengine:** `detectar_score` salva o dict cru e recalcula o score na leitura — mexer na fórmula
ou nos limiares NÃO re-chama a API. Os painéis do cap06 já estão cacheados (gerados pelos testes de
censura), então re-detectar é instantâneo e grátis.

> ⚠️ Nunca delete `workspace/narration_cache`, `workspace/censura_cache` nem o cache de TTS pra
> "limpar espaço" — é o que evita gastar token. São OURO. (Ver `workspace/CACHES_LEIA.md`.)

---

## 2. FLUXO PADRÃO: TESTE → APROVAÇÃO → VERSÃO FINAL

### Passo A — Gerar prévia de TESTE (edge-tts, barata, valida efeitos/censura)
```bash
cd D:/hipercool-inferior-fix
PYTHONUTF8=1 TTS_ENGINE=edge ENSEMBLE_NARRATION=0 NSFW_VISION=1 \
ELEMENTAL_TRANS=1 MASCOTE_OVERLAY=1 MASCOTE_MAX=5 CONTENT_ADAPT=1 \
SUB_CONTEXT=1 CONTEXT_MOTION=1 PANEL_FX=1 TRIM_SILENCE=1 \
SFX_MODE=gap CLIP_GAP_DYNAMIC=1 DUMP_SUBS_TIMING=1 \
D:/hipercool-videos/venv/Scripts/python.exe bin/hiper-pipeline.py \
  --panels-dir workspace/panels/<obra>-capNN --titulo "<Obra> — Capítulo N" \
  --max-panels 120 --subtitles --karaoke --censura --skip-notify \
  --output-suffix _TESTE > logs/capNN_teste.log 2>&1
```
(ffmpeg é pesado → SEMPRE em background task.)

### Passo B — VALIDAR de verdade antes de mostrar (regra CLAUDE.md: nunca dizer "pronto" sem ffprobe)
```bash
ffprobe -v quiet -show_entries format=duration -show_entries stream=codec_type,width,height,duration \
  -of json CENSURADO.mp4
```
- Áudio e vídeo com duração ~igual (diferença de áudio >5s = QUEBRADO).
- Se mexeu em censura: rode o check de FRAMES da seção 0.4 nos pontos suspeitos.

### Passo C — Mostrar pra usuária e AGUARDAR aprovação
Abra a versão censurada (`start "" caminho.mp4`) e peça conferência. **NÃO poste sem OK.**
Postar é ação externa/irreversível — só com confirmação explícita (ver seção 4).

### Passo D — Versão FINAL "gemini" com APROVEITAMENTO de voz (só depois de aprovado)
A versão final usa voz premium (`TTS_ENGINE=gemini` ou `eleven`), mas **reaproveita o que já existe**:
- **Narração/roteiro (visão IA)**: fica em `workspace/narration_cache/…json` → **NÃO regerar**.
- **Censura (scores Sightengine)**: cache por md5 → **NÃO re-paga**.
- **Áudio TTS**: o cache é POR VOZ/engine (`bin/tts_cache.py`). Se a voz final é diferente da de
  teste (gemini ≠ edge), o TTS **precisa** ser gerado nessa voz — isso é esperado e é a única parte
  cara. Mas visão e censura continuam vindo do cache.
```bash
PYTHONUTF8=1 TTS_ENGINE=gemini GEMINI_TTS_PROXY_ENABLED=1 NSFW_VISION=1 \
ELEMENTAL_TRANS=1 MASCOTE_OVERLAY=1 CONTENT_ADAPT=1 SUB_CONTEXT=1 \
CONTEXT_MOTION=1 PANEL_FX=1 TRIM_SILENCE=1 SFX_MODE=gap CLIP_GAP_DYNAMIC=1 \
DUMP_SUBS_TIMING=1 \
D:/hipercool-videos/venv/Scripts/python.exe bin/hiper-pipeline.py \
  --panels-dir workspace/panels/<obra>-capNN --titulo "<Obra> — Capítulo N" \
  --max-panels 120 --subtitles --karaoke --censura --skip-notify \
  --output-suffix _FINAL > logs/capNN_final.log 2>&1
```

---

## 3. RE-TRABALHO: quando é "só código" e quando precisa RE-GERAR VOZ

Antes de re-rodar qualquer coisa, decida a MENOR intervenção que corrige o problema:

| Problema | Regerar voz? | O que fazer |
|---|---|---|
| Censura errada (vazou / cobriu demais / método) | ❌ NÃO | Corrigir `censura_visual.py`/`effects_engine.py` e re-rodar com `--censura` e cache. **Zero tokens.** |
| Legenda dessincronizada | ❌ Quase nunca | WordBoundary já resolve na raiz (ver `_VERSAO_CORRENTE_LEIA.md`). Se faltar sidecar, `--force-tts` uma vez em **edge** (grátis). |
| Transição/efeito/trilha/mascote | ❌ NÃO | Só código + re-render, tudo do cache. |
| Texto do roteiro/narração errado (frase, nome, ordem) | ⚠️ SÓ os afetados | Editar a narração e regerar **apenas** os painéis mudados (o cache guarda por texto; muda o texto → aquele clip regenera). |
| Voz errada (gênero/persona/engine) | ✅ os afetados | Trocar a voz e regerar os clips daquela persona. |
| Áudio cortado/estourado (defeito no wav em si) | ✅ os afetados | Regerar só os wavs quebrados. |

> Princípio: **persistir etapas caras (visão/TTS)**; nunca regerar áudio à toa. Só regere voz se a
> SUSPEITA for que o problema está na própria voz/texto. Na dúvida, primeiro cheque se dá pra
> resolver só no código (é o caso da MAIORIA dos ajustes visuais).

---

## 3.5 DECISÃO DE POST — quando NÃO postar (censura demais mata o vídeo)

Censura protege de bloqueio, mas em excesso destrói o vídeo: se quase tudo está tarjado, não tem o
que ver → não viraliza E ainda arrisca bloqueio por ser "só censura". Antes de postar, avalie a
**proporção de conteúdo censurado**.

### Regra do CAPÍTULO INTEIRO
- Se o capítulo tem **quase todas as cenas censuradas** (ex.: cap05 — a maioria dos painéis +18),
  **NÃO postar como capítulo avulso**. É pura tarja, não engaja, e pode dar bloqueio.
- Esse capítulo **NÃO é descartado**: guarda pra entrar num **COMPILADO GRANDE de vários capítulos**
  (`bin/landscape-compiler.py` / Grupo C das tarefas do n8n). No compilado ele é só uma fração pequena
  do todo, então a censura pesada dele se dilui e não domina o vídeo.
- Heurística prática: contar quantos painéis viraram FORTE/LEVE vs. total. O log de censura já diz
  `(N trechos censurados)`. Se a fração de censura for alta a ponto de o vídeo ser majoritariamente
  tarja, trate como "capítulo de compilado", não como post avulso. (Sem número mágico fixo — use bom
  senso: se ao assistir a impressão é "isso é só censura", não posta avulso.)

### Regra dos CORTES (shorts)
- Ao gerar shorts (`bin/split-shorts.py`), **descartar os cortes que ficarem só com cenas censuradas**.
  Um short que é quase todo tarja não faz sentido — não vê nada, não engaja, e chama bloqueio.
- Ou seja: dá pra postar shorts das partes NÃO/pouco censuradas do capítulo, mas **pula o corte** cujo
  trecho caiu majoritariamente em cima de janelas de censura.
- Como checar: cruze o intervalo do corte (start/end no `meta_shorts.json`) com as janelas de censura
  (os tempos FORTE do capítulo). Se o corte é dominado por censura, não posta esse.

> Resumo: **quanto mais censura, menos vale postar avulso** (capítulo OU corte). O destino do material
> muito censurado é o COMPILADO, onde vira parte pequena do todo.

---

## 4. ALTA PRODUÇÃO — paralelismo correto (IA em fila, código em paralelo)

Objetivo: usar o máximo da máquina SEM estourar as chaves de IA. A restrição dura é:
> ⛔ **NUNCA 2 capítulos usando IA ao mesmo tempo** (protege chaves Gemini/Sightengine).
> Mas a parte SEM IA (render ffmpeg) pode rodar em paralelo à vontade.

### Pipeline de produção (o que deve rodar simultâneo e o que não)
Pense em 2 estágios com naturezas diferentes:

- **Estágio IA (SERIAL, 1 por vez):** visão (Gemini) + TTS (voz). É o gargalo e o que consome
  chave/quota. Só UM capítulo pode estar nesse estágio de cada vez.
- **Estágio CÓDIGO (PARALELO):** montar clips, efeitos, transições, concat, legenda, censura,
  render ffmpeg. Não usa IA → pode rodar vários ao mesmo tempo, usando todos os núcleos.

### Fluxo alvo (pipeline / esteira)
```
cap A: [IA: visão+voz] ──► [CÓDIGO: render vídeo] 
cap B:        └──────────► [IA: visão+voz] ──► [CÓDIGO: render vídeo]
cap C:                            └──────────► [IA: visão+voz] ──► …
```
Ou seja: **assim que o cap A termina o estágio de IA, o cap B JÁ começa a IA** (a fila de IA nunca
fica ociosa), **enquanto o cap A está sendo renderizado pelo código** (em paralelo). Quando a IA do
B acabar, começa a do C, e o B vai pra render junto com o A se o A ainda estiver renderizando.

### Como está hoje e o que falta
- `bin/queue-runner.py` = fila serial de capítulos. `bin/night-shift-driver.py` (cron a60b88ab,
  :13/:43) roda **1 cap/vez** com guarda por PID → garante "nunca 2 simultâneos". Isso protege as
  chaves, mas é serial TOTAL (não separa IA de render).
- **Melhoria a implementar (não feito ainda):** separar os dois estágios pra que a fila de IA
  (serial) e os renders (paralelos) andem sobrepostos como no diagrama. Enquanto não existir,
  o modo seguro é o serial do driver — que já cumpre a regra de ouro.
- ⚠️ Ao paralelizar renders: cada processo ffmpeg é pesado (RAM/CPU). Nunca use `&` do shell com
  background=true (cria zumbi). Use tarefas de background controladas e limite quantos renders
  simultâneos conforme a RAM.

---

## 5. CHECKLIST antes de dizer "pronto" (obrigatório)
- [ ] Rodei ffprobe: áudio ≈ vídeo (sem gap >5s), resolução esperada, moov OK.
- [ ] Se mexi em censura: conferi FRAMES nos pontos suspeitos (tarja presente onde deve, limpo onde não deve).
- [ ] Reaproveitei visão + censura do cache (não gastei token à toa); voz só regerada se necessário.
- [ ] Copiei pra pasta organizada `workspace/videos/<obra>/capNN/{normal,censored,shorts}/vN.mp4`.
- [ ] NÃO postei sem aprovação. NÃO fiz commit/push sem confirmação.
- [ ] Avaliei proporção de censura (seção 3.5): capítulo majoritariamente tarjado → NÃO posto avulso
      (vai pra compilado); cortes dominados por censura → descartados, não postados.
- [ ] Atualizei snapshot datado + `_VERSAO_CORRENTE_LEIA.md` se mudei .py de forma estável.
