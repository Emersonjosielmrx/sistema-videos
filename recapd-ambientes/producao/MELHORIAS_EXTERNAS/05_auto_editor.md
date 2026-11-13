# 05 — auto-editor (⭐4.5k) → cortar silêncio/pausa morta da narração

Clone: `D:\outros projetos para extrair melhorias\auto-editor`
Veredito: 🟢 **ALTO (conceito).** Pode deixar a narração mais "apertada" cortando pausas longas.
O código é Nim/Python misturado e a estrutura é grande (`src/analyze`, `src/cmds`) — extrair o
CONCEITO, não importar o pacote.

## O conceito
auto-editor analisa o LOUDNESS do áudio, marca trechos abaixo de um threshold como "silêncio"
e os corta, com uma `--margin` (padding) ao redor pra não cortar abrupto. Resultado: vídeo mais
dinâmico, sem dead space.

## Onde isso encaixa no nosso pipeline
NÃO no vídeo final concatenado (cortar lá quebraria o sync legenda/elementais que custou caro).
O lugar certo é ANTES, no CLIP de cada painel:
- Cada locução vira um .wav (edge-tts). Às vezes a voz tem silêncio no fim/começo.
- Já temos `CLIP_GAP_S`/`CLIP_GAP_DYNAMIC` (gap híbrido) controlando respiro ENTRE clips.
- Oportunidade: aparar silêncio DENTRO do .wav de cada locução antes de montar o clip, pra a
  legenda não ficar "esperando" voz que não vem.

## PLANO DE IMPLEMENTAÇÃO (simples, sem importar auto-editor)
1. Usar o filtro nativo do ffmpeg `silenceremove` (não precisa do auto-editor):
   `silenceremove=start_periods=1:start_threshold=-40dB:stop_periods=1:stop_threshold=-40dB:detection=peak`
   Aplicar no .wav da locução logo após gerar (em `edge_tts_engine` ou no ponto que monta o clip).
2. Manter uma margem (ex: 80ms) pra não cortar respiração natural — equivalente ao `--margin`.
3. Como o doc 01 nos dá WordBoundary, dá pra ser ainda mais preciso: cortar só o silêncio APÓS
   a última palavra (trailing) e ANTES da primeira (leading), preservando pausas internas.
4. VALIDAR: a duração do clip encurta → recalcular gaps/offsets (já é dinâmico). ffprobe no fim.

## ⚠️ ARMADILHAS
- NÃO cortar silêncio do vídeo MONTADO (destrói sync). Só do .wav por locução, ANTES de montar.
- Não exagerar no threshold: voz baixa de personagem pode ser confundida com silêncio.
- Reavaliar o gap híbrido depois — talvez fique redundante com o trailing trim.

## O que NÃO copiar
- O pacote auto-editor inteiro (Nim, exports pra Premiere/Resolve, timeline). Só o conceito +
  `silenceremove` do ffmpeg que já temos.
