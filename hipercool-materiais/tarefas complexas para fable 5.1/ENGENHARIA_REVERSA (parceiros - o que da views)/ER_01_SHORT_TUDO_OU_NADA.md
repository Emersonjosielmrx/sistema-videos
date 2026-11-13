# ER_01 — Short "tudo ou nada": ~1.200 views ou 0–10

## Fato (29/10, 275 Shorts de parceiro, views de 48–96 h)
Faixas: 0 = 62 | 1–9 = 104 | 10–99 = 23 | 100–499 = 18 | 500–1.999 = 63 | 2.000+ = 5.
Quase ninguém fica no meio. Os que pegam param perto de 1.200 (esportenoturno med 1.272, filmenoturno 1.212,
dicasfinanceirasdaia 1.324, fiodameada 1.285). Só 1 passou de 5.000 (6.674, curiosidadesnoturnas, parceiro
carlosmerchanat, "O PODER OCULTO DA MOELA...").

## É por VÍDEO, não por canal
Em 17 canais há, no mesmo canal, Short com mais de 500 e Short com menos de 10 (filmenoturno 13 altos/3 baixos;
curiosidadesnoturnas 6/6; manhwanoturno 1/8; cenareact 2/12). Canal e nicho mudam a chance, mas quem decide é o vídeo.

## O que JÁ foi descartado como causa
- Reuso da mesma fonte em outro idioma: em pt não muda (29% contra 32% acima de 500). Ver ER_00.
- Estilo de título (provocacao/curiosidade/busca): medianas 8/3/4, sem separação clara.
- Narrador clonado: n pequeno demais (2–4 por voz); "sem clone" = 222 vídeos, mediana 3.
- Título do PARCEIRO (29/10, `D:\video-fila\engenharia_reversa\titulos_parceiros.py`, 57 parceiros, 35.326 Shorts):
  nenhum traço (tamanho, maiúsculas, ?, !, emoji, número, "você", hashtags) separa os 10% de cima dos 10% de baixo do
  mesmo canal — quase sempre meio a meio entre parceiros. O que decide está no VÍDEO.

## Hora DENTRO do mesmo canal (29/10, `hora_mesmo_canal.py`)
Taxa de >=500 da faixa menos a taxa do próprio canal: 19–21 h −21 pts e pior em 6 de 6 canais; 22–23 h +21 (4 de 5);
6–10 h +14 (3 de 3). n pequeno (16–26 vídeos por faixa). SUPOSIÇÃO: 19–21 h é o pico de concorrência no feed BR.
Quem decide a hora: `pol.horario_publicacao` chamado em `D:\recapd-ambientes\producao\bin\parceiro_diario.py` ~928.

## Sinal novo: views da fonte (29/10, `fonte_x_nosso.py`)
Fonte com < 100 mil views → 12% dos nossos passam de 500 (n 60). Fonte 100 mil–1 mi → 28%, 1–5 mi → 29%, 5 mi+ → 25%.
Fonte no top 5% do canal do parceiro: 20% (n 143); entre 50% e 80%: 40% (n 25, pequeno). Misturado com nicho
(kaijinre tem fontes menores?) — falta separar por parceiro.

## O que tem sinal mas ainda está misturado
- Hora (BR): 12–13 h e 22–23 h com 31–44% acima de 500; 3–6 h e 11 h com 0–6%. CUIDADO: cada canal posta em
  hora fixa, então hora e canal andam juntos. Precisa comparar hora DENTRO do mesmo canal.
- Nicho: esportes (med 1.130), fatos (54), filme_sem_voz (111) bons; manhwa (med 1, 43% zero), dorama (2) ruins.
- Parceiro: futtres, xiuliamelo, canalutopia, papodebixo, andreu_edit1 med ~1.200; kaijinre (79 vídeos) med 1.

## SUPOSIÇÃO a provar (o que a sessão não consegue sozinha)
O YouTube mostra cada Short a um lote de teste (~1.000 pessoas). Se a taxa de "assistiu em vez de deslizar" fica
boa, entrega ~1.200; se não, para. Os 0–10 talvez nem tenham recebido o lote (conteúdo marcado como reaproveitado,
ou canal sem confiança). Sem as impressões do Studio (ER_02) não dá para separar "foi mostrado e perdeu" de "nem
foi mostrado". E por que os bons PARAM em ~1.200 em vez de ir para o 2º lote?

## Tarefa para o Fable
1. Desenhar o teste que separa as duas hipóteses (mostrado e perdeu x nem mostrado) com o que temos.
2. Achar o que faz um Short sair dos ~1.200 (2º lote). O único caso: 6.674 views, vídeo
   `D:\postador-de-videos` ledger, curiosidadesnoturnas, 28/10. Comparar com os ~1.200 do mesmo canal.
3. Montar o modelo de "o que separa alto de baixo no mesmo canal" com duração, gancho 2 s, cortes/s, legenda,
   título, hora. Esta sessão vai medir essas variáveis (ER_05/ferramenta em `D:\video-fila\engenharia_reversa\`);
   o Fable decide a estatística (n pequeno por canal: ~10–20 vídeos).

## Medidas do VÍDEO dos nossos (sessão ER, 29/10 03:55) — confirma a tarefa 2 do Fable
`D:\video-fila\engenharia_reversa\comparacao_nossos.md` (refeito de hora em hora pela tarefa EngenhariaReversaMedir;
ffmpeg: duração, cortes/s, 1º corte, maior plano, volume 2 s; usa a régua de elegível do Fable). Com 135 medidos:
2º lote x só 1º lote no MESMO canal (5 canais): duração −15 s em 5/5, % assistido +53 em 5/5; cortes/s e 1º corte sem
sinal. Elegível x não elegível: nenhuma medida do vídeo separa (bate com "é canal/upload"). Por duração: 30–45 s 64%
elegíveis, 60–90 s 22%; % assistido 89% (20–30 s) → 30% (60 s+).

## Fable — resultado
**29/10 02:20 — Tarefa 1 (separar "mostrado e perdeu" de "nem mostrado") RESPONDIDA com o dado que já existe.**
O ER_02 está desatualizado num ponto: desde 23/10 o `retencao_lista` (modo avançado do Studio, tabela por vídeo) grava
em `metricas_studio.json` os campos `continuaram` (= % que NÃO deslizou no feed), `dur_media` e `pct_media` — 367/413
vídeos têm. O que falta mesmo é só `impressoes` ("mostrado no feed", 2 de 595). Script novo, só arquivos:
`python D:\video-fila\engenharia_reversa\continuaram_x_views.py [--csv]` (279 Shorts de parceiro, views 48–96 h).

| views 48 h | n | com "continuaram" | mediana continuaram | dur_media | pct_media |
|---|---|---|---|---|---|
| 0 | 62 | 11 | 100% | 12 s | 31% |
| 1–9 | 106 | 86 | **100%** | 29 s | 60% |
| 10–99 | 23 | 21 | 60% | 21 s | 41% |
| 100–499 | 19 | 19 | 32% | 18 s | 37% |
| ≥500 | 69 | 69 | 56% | 27 s | 47% |

1. **Os 0–10 não perderam o teste: nem receberam.** "Continuaram" é calculado sobre quem viu no feed; 100% com 2–5
   views = 2–5 pessoas viram e nenhuma deslizou. Se tivessem recebido o lote (~1.000), a taxa estaria em 40–70% como
   nos ≥500. Em 15 canais com os dois grupos, o baixo tem continuaram MAIOR que o alto em 13 (artefato da amostra
   mínima). Logo: a hipótese "YouTube mostra a um lote e mata se deslizam" NÃO explica os 0–10; eles ficam fora do lote.
2. **Entre os que receberam o lote, deslizar quase não separa.** Com views_periodo ≥ 20 (n 98): Spearman continuaram ×
   views = +0,23. Tercil de continuaram 10–42% → mediana 678 views, 53% ≥500; 43–59% → 1.226, 81%; 59–90% → 1.247, 71%.
   Ou seja, um Short que segura só 30% ainda chega aos ~1.200. O teto ~1.200 é o tamanho do lote + um pouco; sair
   dele é o 2º lote (tarefa 2), não o gancho.
3. **Consequência para as linhas CORTES/LONGOS/CCV:** melhorar gancho/retenção (júri, T1–T7, "movimento") não move
   os 62+106 vídeos de 0–9: eles não são vistos. A alavanca nº 1 é a ELEGIBILIDADE do upload para o lote de teste
   (quem decide é o canal/upload: conteúdo reaproveitado, canal sem confiança, metadados, frequência). Nenhum de
   <10 views em 48 h passou de 100 depois (views_periodo de 4 semanas): o que não entra no lote não entra nunca.
4. **O que medir agora (ER_02, em andamento):** "Mostrado no feed" (`SHORTS_FEED_IMPRESSIONS`) na mesma tabela do modo
   avançado. Com impressões, o diagnóstico vira exato: impressões < 50 = não elegível (problema de canal/upload);
   impressões ≥ 500 e views baixas = perdeu o teste (problema do vídeo). Até lá, use `continuaram == 100 and
   views_periodo < 10` como marcador de "não elegível".
5. Para a tarefa 3 (modelo alto × baixo no mesmo canal): só vale comparar vídeos que RECEBERAM o lote (views_periodo ≥
   20 ou impressões ≥ 200). Misturar os não elegíveis é o que fez título/narrador/hora darem "sem sinal".

**29/10 02:40 — Tarefa 2 (o que sai dos ~1.200 = 2º lote).**
- O platô é real e estreito: entre 500 e 3.000 views, 49 de 67 Shorts param em 1.000–1.500 (faixas de 250: 500→2,
  750→7, 1000→23, 1250→26, 1500→5, 1750→1, 2000→1, 2250→2). A tabela de 4 semanas confirma que não crescem depois
  (ex.: 1.204 em 48 h → 1.206 em 16 dias). O 1º lote é ~1.000–1.500 pessoas e acaba.
- O que separa quem passou de 2.000 (n 5) dos que ficaram em 800–1.600 (n 59): **porcentagem assistida média 72%
  contra 44%** (dur_media 18 s × 27 s; continuaram 57% × 54% — igual). Entre todos os que receberam o lote (n 67):
  Spearman pct_media × views +0,33; ≥65% assistido: 3/4 dos ≥2.500, 5/9 dos 1.500–2.500, 10/54 dos <1.500.
  Os 5 que saíram: 6.674 (89% assistido, 24 s), 3.686 (76%, 20 s), 2.386 (64%, 13 s), 2.309 (72%, 17 s), 2.071
  (71%, 18 s) — todos "fatos"/esportes, 13–24 s, assistidos quase inteiros (o 6.674 passa de 100% = looping).
- Regra para testar (T8 nos Cortes): **Short de 15–25 s que o público assiste inteiro e repete** (final que emenda no
  início). Medida: pct_media ≥ 65% na tabela do Studio. Hoje os nossos têm 50–75 s (CORTES_02) e pct_media mediana
  44%: o lote assiste metade e o YouTube não dá o 2º lote.
- Bug achado de passagem: o campo `views` do metricas() por vídeo está 10× maior que a tabela e que as 48 h em pelo
  menos 7 vídeos (ex.: VYUORRjhTe4 views 13.000, tabela 1.285, 48 h 1.286; iFZftj2HFZk 12.000 × 1.206). Quem decide
  por `views` do metricas_studio (decidir() do metricas_rede) pode estar lendo o cartão errado da Visão geral;
  medidas_48h e `ret_lista.views_periodo` são os confiáveis. Conferir no print `metricas_<id>` na próxima leitura.
