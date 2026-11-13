# 03 — ShortGPT (⭐7.5k) → getCaptionsWithTime + arquitetura de engine

Clone: `D:\outros projetos para extrair melhorias\ShortGPT`
Veredito: 🟡 **MÉDIO.** Boa lógica de captions e arquitetura limpa de "engine", mas mais
genérico que o nosso. Extrair peças, não adotar o framework.

## Peça 1: `shortGPT/editing_utils/captions.py` (107 linhas, leia inteiro)
- `getCaptionsWithTime(transcriptions, maxCaptionSize=15)`: agrupa palavras com timing em
  captions de até N caracteres, quebrando em pontuação e a cada ~5 palavras. Alternativa ao
  `parse()` do captacity (doc 02) — comparar os dois e escolher o mais simples de portar.
- `getTimestampMapping` / `interpolateTimeFromDict`: mapeiam posição de caractere → tempo.
  Útil se quiser highlight por caractere em vez de por palavra.
- `splitWordsBySize(words, maxCaptionSize)`: quebra por tamanho com regra de "meia-tela".

## Peça 2: arquitetura de engine (referência de organização, não copiar literal)
- `shortGPT/engine/abstract_content_engine.py` + `content_short_engine.py`: padrão de "steps"
  com estado persistido em `content_database.py`. O nosso pipeline é mais procedural.
  NÃO refatorar o nosso pra isso agora (risco alto, ganho baixo), mas é boa referência se um
  dia quiser retomar pipeline interrompido do meio.

## Peça 3: `shortGPT/engine/content_translation_engine.py` + `multi_language_translation_engine.py`
- Dublagem/legenda multi-idioma. RELEVANTE SE um dia quiser exportar EN/ES do mesmo cap.
  Guardar pra roadmap; não é dor atual.

## Peça 4: `shortGPT/audio/edge_voice_module.py`
- Confirma o jeito simples de gerar edge-tts via `communicate.stream()` (linhas 42-52).
  NÃO captura WordBoundary (usa só audio chunks) — o MoneyPrinterTurbo (doc 01) é melhor ref pra timing.

## PLANO
- Quando for mexer no agrupamento de legenda (doc 02), comparar `getCaptionsWithTime` vs `parse()`
  lado a lado e portar o mais enxuto. Não precisa dos dois.
- Multi-idioma: anotar no roadmap, fora do escopo das 4 queixas atuais.

## O que NÃO copiar
- `content_database.py` (TinyDB), API keys db, Gradio UI — peso morto pra nós.
- Não adotar o framework de engine inteiro: refatoração grande sem resolver as queixas.
