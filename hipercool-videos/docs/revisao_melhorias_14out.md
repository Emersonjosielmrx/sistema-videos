# Revisão de melhorias — hipercool (14/10/2026, Opus)

Para quem for conferir: este documento lista TODAS as mudanças feitas nesta sessão.
Cada item tem: o que mudou, em qual arquivo, e o que verificar.

---

## 1. Dicionário de segurança de anúncios + engajamento narrador

**Arquivo criado:** `config/dicionario_seguro.json`

**O que faz:**
- `proibidas`: palavras proibidas no título/descrição/tags/narração do NARRADOR → eufemismos seguros
- `engajamento_narrador`: ganchos, reações, chamadas ao espectador, bordões, humor, transições, risadas — estilo MomoManhwa/oporaodacidadela/KkVirjao/mikemanhwa
- `idiomas`: eufemismos por idioma (en, hi, id, it, ru, th, vi)

**Verificar:**
- [ ] Abrir o JSON e conferir se os eufemismos fazem sentido e são seguros pro YouTube
- [ ] Completar idiomas faltantes (fr, es) quando for necessário
- [ ] As substituições são por regex de palavra inteira (\b), case-insensitive — testar edge cases

---

## 2. Detecção de propaganda do scan melhorada

**Arquivo:** `bin/fx_detect.py` (linhas ~230-248)

**O que mudou:**
- Adicionou keywords: "early access", "read ahead", "support us", "patreon", "ko-fi", "buymeacoffee", "grupo de tradução"
- Adicionou regex `_PROPAGANDA_RE` com padrões mais amplos: `.com` seguido de "leia/read/join", "tradução por/de", "scanlation", etc.
- `is_propaganda()` agora checa keywords E regex

**Verificar:**
- [ ] Rodar `is_propaganda` nas descrições em cache dos caps 1-3 e conferir falsos positivos (painel de história com placa de rua, URL no balão de fala, etc.)
- [ ] A propaganda do cap 2 (0:31–0:40 "Blackout Comics") deve ser pega agora

---

## 3. Tremor substituído por movimento real

**Arquivo:** `bin/fx_parallax.py` (linhas ~477-487)

**O que mudou:**
- **tensão**: o tremor contínuo de 3 px a ~11 Hz foi substituído por balanço lento ±4 px a 0.5 Hz + balanço vertical ±2.5 px a 0.35 Hz. Suave, sem vibração.
- **impacto**: tremor agora é um tranco de 0.12 s (era 0.45 s) com amplitude de 8 px (era 11 px). Acaba rápido, fica firme depois.
- tensão ganhou zoom mais forte no personagem: z_fg = 0.22 (era 0.17)

**Verificar:**
- [ ] Renderizar 1 painel de tensão e 1 de impacto e comparar com antes
- [ ] Com balão de fala, a legenda do balão deve ser legível (o impacto com balão é limitado a 5 px / 0.3 s)

---

## 4. Prompt de narração estilo viral

**Arquivo:** `bin/narration.py` (linhas ~340-420)

**O que mudou:**
- Prompt reescrito para imitar MomoManhwa, oporaodacidadela, KkVirjao, mikemanhwa
- Adicionou regras de engajamento: falar COM o espectador ("você"), reagir com "EITA", "mano...", etc.
- Humor: piadas rápidas, comparações engraçadas
- Ganchos obrigatórios a cada 5-7 painéis
- Lista de palavras proibidas direto no prompt (morte→eliminar, etc.)
- Adicionou exemplo de narrador reagindo no estilo viral

**Verificar:**
- [ ] Deletar cache de narração do cap 4 (`workspace/narration_cache/`) e gerar de novo
- [ ] Comparar o resultado com os caps anteriores — deve ter mais humor e engajamento
- [ ] As falas de personagens (balões) NÃO devem ser suavizadas

---

## 5. Sanitização do narrador pelo dicionário seguro

**Arquivo:** `bin/narration.py` (linhas ~101-127, linha ~525)

**O que mudou:**
- Função `_sanitizar_narrador(locucoes)`: troca palavras do dicionário seguro nas falas do narrador (NÃO de personagens)
- Chamada após o parse do JSON, antes de salvar

**Verificar:**
- [ ] Se o LLM gerar "ele matou o cara", o narrador deve dizer "ele eliminou o cara"
- [ ] Se o LLM gerar uma fala de personagem com "matar", essa deve ficar intacta
- [ ] Conferir que a regex funciona com maiúsculas/minúsculas

---

## 6. SEO com dicionário de segurança

**Arquivo:** `bin/seo.py`

**O que mudou:**
- Função `_sanitizar_seo(pacote_dict, idioma)`: troca palavras proibidas no título, descrição e tags
- Regras do prompt incluem lista de palavras proibidas
- `pacote()` e `pacote_longo()` aplicam `_sanitizar_seo` no resultado
- Suporte a dicionários por idioma

**Verificar:**
- [ ] Deletar cache de SEO de algum capítulo (`workspace/cache/seo/`) e gerar de novo
- [ ] O título não deve conter "morte", "matar", "sangue", etc.
- [ ] Os eufemismos devem ser naturais (não truncados ou sem sentido)

---

## 7. Legendas maiores estilo viral

**Arquivo:** `bin/fx_acabamento.py` (linha ~783)

**O que mudou:**
- Fonte Cap: 78 → 110 (aumento de ~41%)
- Outline: 6 → 7, Shadow: 2 → 3 (mais legibilidade com fonte maior)

**Verificar:**
- [ ] Renderizar 30 s e conferir que a legenda não corta na borda (margem L/R = 40)
- [ ] Comparar com o Laestro — deve estar no tamanho parecido

---

## 8. Saída em 30fps fixos

**Arquivo:** `bin/fx_acabamento.py` (linha ~880)

**O que mudou:**
- Adicionou `fps=30` no início do grafo de filtros do passe_final
- Antes: o vídeo de entrada (~26.7 fps variável) era upscalado sem normalizar o FPS

**Verificar:**
- [ ] `ffprobe -v error -select_streams v:0 -show_entries stream=nb_frames,r_frame_rate,duration -of json` no vídeo de saída
- [ ] Esperar ~30 fps e nb_frames ≈ duração × 30

---

## 9. Profundidade parallax (modo novo no fx_parallax)

**Arquivo:** `bin/fx_parallax.py` (várias adições)

**O que foi adicionado:**
- `_sessao_depth()`: sessão ONNX do Depth Anything V2 Small (fp32)
- `profundidade(img_path)`: inferência + cache PNG 16-bit em `workspace/cache/profundidade/`
- `profundidade_vale(img_path)`: verifica se p95-p5 > 0.25
- `_render_profundidade(img_path, out_mp4, duration, panel_idx)`: render por remap (objetos perto movem mais)
- Integração no `build_clip_parallax`: modo "profundidade" despacha para `_render_profundidade`

**Arquivo:** `bin/hiper-pipeline.py` (linha ~493)

- Quando painel não é elegível (sem personagem detectado) e não é sugestivo e tem profundidade suficiente → modo "profundidade"
- Modo "profundidade" conta como 2.5D para tracking

**Verificar:**
- [ ] O modelo existe em `D:\hipercool-materiais\models\depth-anything-v2-small\model.onnx`
- [ ] Renderizar painel de cenário (prédio, cidade) e conferir que o movimento é suave e crível
- [ ] Painéis "esfumaçados" (degradê) devem ser rejeitados por `profundidade_vale` (p95-p5 < 0.25)
- [ ] O cache funciona (segundo render do mesmo painel não recalcula a profundidade)

---

## 10. Memes visuais (figurinha + reação tela cheia)

**Arquivo criado:** `bin/fx_memes.py`

**O que faz:**
- Carrega catálogo de `config/memes_catalogo.json` (fallback: historias-em-frames)
- `escolher_memes(palavras_tempo, total_dur, config)`: seleciona memes por gatilhos de emoção nas palavras
- Gatilhos: choque, confusão, deboche, alegria, tristeza, raiva
- Intervalos configuráveis: figurinha_s (25s), tela_cheia_s (60s)
- Retorna lista de {t, dur, estilo, arquivo, has_audio}

**Arquivo:** `bin/fx_acabamento.py`

- `passe_final()` agora aceita `memes=()` e adiciona como overlays ffmpeg
- Figurinha: 280px no canto superior direito, com bounce de entrada
- Tela cheia: cobre tudo (cover crop)
- `finalizar()` chama `fx_memes.escolher_memes` e passa para `passe_final`
- Config: `fila.json` → `memes: {ligado: true, figurinha_s: 25, tela_cheia_s: 60}`

**Verificar:**
- [ ] Copiar `memes_catalogo.json` de historias-em-frames para `config/` OU conferir que o fallback funciona
- [ ] Renderizar um capítulo e verificar que os memes aparecem nos momentos certos
- [ ] Figurinha deve ficar no canto, não sobrepor a legenda
- [ ] Tela cheia: narração continua por baixo (áudio não é cortado)
- [ ] Áudio dos memes: NÃO foi integrado neste passe (seria no `masterizar_audio`). Para V2.
- [ ] Desligar: `fila.json` → `memes: {ligado: false}`

---

## O que NÃO foi feito (fora do escopo desta sessão)

1. **Marca d'água do scan** (P2): precisa de OCR ONNX + inpaint — mais complexo
2. **Living character** (P2): protótipo funciona mas precisa otimizar de 240ms→60ms
3. **SEO multiagente com aprendizado histórico** (P1 grande): precisa de coleta de métricas + agente analista
4. **Completar acervo de memes** (P2): +40-60 memes raiva/reviravolta/romance
5. **Outro PC** (P3): depende do dono configurar chave SSH
6. **Áudio dos memes** no masterizar_audio: V2

---

## Correções pós-implementação

### Bug: smart quotes em narration.py (corrigido)
- Linhas 100-130 tinham curly/smart quotes (U+201C, U+201D, U+2018, U+2019) em vez de aspas ASCII retas
- Causava `SyntaxError: invalid character` ao importar o módulo
- **Corrigido**: todas as smart quotes substituídas por aspas retas via byte replacement
- **Verificado**: `python -c "import narration; narration._carregar_dicionario(); print('OK')"` passa

### Config memes em fila.json (adicionado)
- Adicionado `"memes": {"ligado": true, "figurinha_s": 25, "tela_cheia_s": 60}` em fila.json

---

## Como testar TUDO de uma vez

```bash
# 1. Limpar caches dos efeitos que mudaram (narrativa + SEO do cap 4 em diante)
# NÃO precisa limpar: cache de profundidade, cache de clipes 2.5D, cache de máscaras

# 2. Verificar imports
cd D:\hipercool-videos\bin
python -c "import fx_memes; print('fx_memes OK')"
python -c "import narration; narration._carregar_dicionario(); print('dicionário OK')"
python -c "import fx_parallax; print('depth model:', fx_parallax.MODELO_DEPTH.exists())"
python -c "import seo; seo._dic_seguro(); print('seo dicionário OK')"

# 3. Render de teste (cap 4 quando as melhorias estiverem prontas)
# Voltar adiantado para 6 em fila.json
```
