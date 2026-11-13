# 02 — captacity (⭐138) → agrupamento word-level que cabe na tela

Clone: `D:\outros projetos para extrair melhorias\captacity`
Veredito: 🟢 **ALTO VALOR (lógica, não código).** Resolve "como agrupar palavras em cards"
de forma robusta. Pequeno e 100% legível (4 arquivos py).

## A peça a copiar: `captacity/segment_parser.py` (58 linhas, leia inteiro)
Função `parse(segments, fit_function, allow_partial_sentences)`:
- Recebe palavras com `{word, start, end}` (timing real).
- Vai juntando palavras num caption ENQUANTO `fit_function(text)` disser que cabe na tela.
- Quando não cabe (ou quebraria frase no meio), fecha o caption e começa outro.
- Resultado: cada caption tem `start/end` corretos e um conjunto de `words` com timing individual.

Por que importa pra nós: hoje em `effects_engine.render_subtitles_short` agrupamos por
`SUB_WORDS_PER_CARD` (nº FIXO de palavras, ex: 2). Isso ignora o tamanho da palavra/tela —
"explosão" e "eu" ocupam slots iguais. O `fit_function` do captacity agrupa pela LARGURA REAL.

## Também útil: `captacity/text_drawer.py`
- Classes `Word`/`Character` + `create_text_ex` permitem highlight POR PALAVRA dentro do card
  (a palavra atual numa cor, as outras em branco) — exatamente o efeito karaokê.
- Renderiza via MoviePy. NÓS renderizamos legenda como PNG (`_render_caption_png`). Não trocar
  pro MoviePy — só copiar a IDEIA de pintar a palavra ativa e medir largura real com
  `ImageFont.truetype(font).getlength(texto)` pra decidir quebra de card.

## PLANO DE IMPLEMENTAÇÃO
Depende do doc 01 (precisamos do timing real por palavra primeiro). Ordem: 01 → depois 02.
1. Adaptar a ideia do `parse()`: em `render_subtitles_short`, trocar o agrupamento fixo
   `words[g:g+words_per_card]` por agrupamento por largura: medir cada palavra com Pillow
   (`ImageFont.getlength`) e fechar o card quando passar de X% da largura do vídeo (ex: 80%).
2. Manter o highlight amarelo por palavra que já temos (`highlight_idx`), mas usando os
   start/end REAIS de cada palavra (do doc 01) em vez do proporcional.
3. `fit_function` no nosso caso = "largura do PNG renderizado < 0.8 * 1080".

## O que NÃO copiar
- Dependência de MoviePy/Whisper do captacity (`transcriber.py`). Já temos texto e (com doc 01) timing.
- `cli.py` inteiro — é o wrapper de linha de comando deles.
