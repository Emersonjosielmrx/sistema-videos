# 05 — Cortes do longo para os canais de cortes
> **PROJETO: LONGOS** — recap longo de anime/manhwa do recapd (`D:\recapd-ambientes\producao`, linha `D:\video-fila\linhas\LONGOS`). Escrito pela sessão Opus da linha LONGOS em 28/10/2026.

**Objetivo:** dos longos, tirar os trechos com mais chance de viralizar como Shorts e aprender com o resultado.

**Onde olhar**
- `D:\recapd-ambientes\producao\bin\melhores_cortes.py` (novo, 28/10): a IA (gemini-fila) lê o roteiro numerado com os
  tempos e escolhe 3–6 trechos de 35–90 s; corta do longo FINAL em 9:16 (`shorts_from_deitado.make_vertical_short`).
  Chamado no fim de `anime-pipeline.py` (só deitado); o trabalhador do Kaggle sobe `cortes_longo\` junto.
- Teste num roteiro real: `D:\video-fila\linhas\LONGOS\bench\teste_cortes.py` (5 trechos, notas 8–10).
- Linha CORTES (Shorts de parceiro): `D:\video-fila\linhas\CORTES\ESTADO.md` (legenda de impacto, tarja, júri).

**Limites conhecidos:** a escolha é só pelo TEXTO (não vê imagem nem ouve a energia); o Short é o recorte do longo com
enquadramento de fundo borrado (legenda do longo fica pequena; mascote de tela cheia pode cortar); sem gancho escrito
na tela no 1º segundo; a postagem NÃO está ligada (falta a dona dizer os canais). Nada aprende com as views dos cortes.

**Ideias para avaliar:** pontuar por sinais do vídeo (cortes de cena/min, pico de áudio, SFX de impacto); refazer a
legenda para 9:16 em vez de reaproveitar a do longo; gancho na tela; laço com o longo ("vídeo completo no canal").

**Como medir:** views/retenção dos Shorts por trecho × nota dada; quantos viram inscritos.

## Fable — resultado
**29/10 (Fable).** Aplicar o que o ER_01 provou nos Shorts de parceiro antes de ligar a postagem dos cortes do longo:
1. **Tamanho:** 35–90 s é a faixa que para no platô de ~1.200 (44% assistido). Os que passaram têm 13–24 s e são
   assistidos inteiros. `melhores_cortes.py` deveria pedir trechos de **15–25 s** (1 acontecimento, 1 frase de impacto)
   e fechar em loop (final que emenda no início). Dá para manter 1 trecho de 45–60 s por longo como braço B do teste.
2. **Escolha pelo vídeo, não só pelo texto (barato, sem IA):** `D:\video-fila\engenharia_reversa\medir.py` já mede
   cortes/s, 1º corte, volume dos 2 s iniciais e silêncio inicial por ffmpeg; rodar nos candidatos e descartar trecho
   com silêncio inicial > 0,5 s ou volume 2 s abaixo do resto (os dois sinais que mais pesaram contra o % assistido
   nos nossos: −0,48 e −0,24, n pequeno). Picos de áudio (ebur128 momentâneo) e trocas de cena (`fx_detect`) já
   existem no pipeline.
3. **Canal de destino decide tudo:** cortes de manhwa postados em canal de manhwa/dorama não recebem o lote do
   feed (ER_01/ER_04). Postar nos canais que recebem (fatos/filme/esportes "Noturno") só se o conteúdo couber no
   nicho; senão o corte do longo vai medir zero como o hipercool. O laço "vídeo completo no canal" só vale depois que
   o corte passa do 1º lote.
4. Legenda refeita em 9:16 e gancho na tela: sim, mas custo de CPU no PC1 — fazer no Kaggle junto com o corte
   (`cortes_longo\` já sobe de lá).

**29/10 tarde (sessão LONGOS) — aplicado o item 1:** `melhores_cortes.py` agora pede 15–25 s (1 acontecimento, 2–4 frases, fecho que emenda no começo). Itens 2–4 não feitos; postagem dos cortes segue DESLIGADA (falta a dona dizer os canais).
