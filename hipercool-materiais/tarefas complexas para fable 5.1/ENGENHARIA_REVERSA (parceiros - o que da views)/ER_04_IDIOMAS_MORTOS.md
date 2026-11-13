# ER_04 — Canais em it/id/ru/th/hi: mediana 0

## Fato (29/10, Shorts de parceiro)
| idioma | n | mediana | % zero |
|---|---|---|---|
| vi | 8 | 568 | 25% |
| pt | 212 | 8 | 14% |
| it | 10 | 0 | 60% |
| hi | 13 | 1 | 38% |
| id | 12 | 0 | 58% |
| ru | 10 | 0 | 70% |
| th | 8 | 0 | 75% |

Os canais inovare_ita/ind/ru/thai/hindi recebem a MESMA fonte traduzida (25 das 29 fontes repetidas). Hipercool
também posta nesses canais (ER_03). O vietnamita é a exceção (med 568).

## Pergunta que a sessão não resolve sozinha
Parar, mudar o que vai para lá, ou insistir? É decisão de negócio + causa técnica: tradução/voz ruim no idioma?
canal sem público inicial? horário errado do país? (postagem deve ser no pico de cada país — memória
feedback_producao_postagem). Ver `D:\recapd-ambientes\producao\bin\parceiro_diario.py` ~linha 909 (regra "nunca o
mesmo vídeo em 2 canais da mesma língua" — entre línguas é permitido) e `pol.horario_publicacao`.

## Tarefa para o Fable
1. Conferir o horário de publicação desses canais no fuso do país (ledger `publish_at`).
2. Ouvir/ver 2 Shorts de cada idioma morto e do vi: a voz e a legenda estão certas no idioma?
3. Propor: o que muda, e como medir em 7 dias. Regra: nenhum canal fica 1 dia sem postar; canal pausado pode ter
   advertência (nunca despausar sem Studio).

## Fable — resultado
**29/10 02:30 — Tarefa 1 (hora local) feita: não é a hora.** `python D:\video-fila\engenharia_reversa\hora_idiomas.py`
(ledger publish_at → fuso do país; it +1, id/th/vi +7, ru +3, hi +5:30):
- Hora local mediana: hindi 14 h, indo 16 h, ita 15 h, ru 11 h, thai 11 h, viet 11 h — tudo em horário de dia,
  nada absurdo. E a mediana de views é 0 em TODAS as faixas de hora (3–5 h, 9–11 h, 15–17 h, 18–20 h, 21–23 h:
  mediana 0–1, ≥100 só 4 de 99, todos às 9–11 h). Mudar o horário não resgata esses canais.
- Coerente com o ER_01: os Shorts desses canais têm "continuaram" 100% com 2–5 views = o feed não dá o lote de
  teste. É elegibilidade do CANAL (conteúdo traduzido/reaproveitado + canal sem histórico), não do vídeo nem da hora.
- O vietnamita (viet) recebe lote (ER_02 mostrou 1.418 e 1.226 views com impressões de miniatura e intencionais
  normais), então "canal novo de língua" sozinho não mata; o que difere do viet precisa ser visto (tarefa 2: voz e
  legenda no idioma; e se o canal viet tem algo que os outros não têm — verificação, idade, Shorts próprios).
- Proposta de medida em 7 dias sem parar canal (regra "nenhum canal 1 dia sem postar"): nos 5 canais mortos, trocar
  1 dos Shorts do dia por um NÃO traduzido de outro canal (conteúdo sem fala, ou fala original + legenda no idioma)
  e comparar `continuaram`/views_periodo dos dois tipos na tabela do Studio. Se o não traduzido também fica em 100%
  com <10 views, é o canal; aí vale conferir no Studio se há aviso de "conteúdo reutilizado" (Monetização/Avisos).
