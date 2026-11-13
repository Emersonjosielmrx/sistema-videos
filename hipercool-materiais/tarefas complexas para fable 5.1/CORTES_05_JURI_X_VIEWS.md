# CORTES — 05 — O júri automático nunca foi conferido contra as views

> **Projeto: linha CORTES** — Shorts de canais parceiros (recapd, `D:\recapd-ambientes\producao\bin`; estado em
> `D:\video-fila\linhas\CORTES`). Escrito pela sessão da linha CORTES em 28/10/2026.

## Fatos
- `D:\recapd-ambientes\producao\bin\cortes_juri.py` (tarefa Cortes_Juri): movimento em todo Short + 4 verificadores
  Gemini (legibilidade, movimento, história, retenção) em 1 a cada 4 -> `D:\video-fila\linhas\CORTES\evolucao.jsonl`
  e `juri\<pasta>\juri.json`; o aprendiz generaliza regras em `APRENDIDO.md`.
- Em 28/10 o júri errava CONTRA decisões da dona (1ª pessoa, final em loop, legenda palavra por palavra) e uma regra
  do APRENDIDO mandava o contrário dela — corrigido com `DECISOES_DONO` no prompt. Ou seja: o júri pode empurrar o
  sistema na direção errada sem ninguém perceber.
- O melhorador (`cortes_melhorador.py`, desligado) usaria a NOTA DO JÚRI para decidir.

## O ponto cego
Ninguém mediu se nota alta do júri = mais views/retenção. Se não houver correlação, o melhorador vai otimizar a
coisa errada.

## Para o Fable
1. Cruzar `juri.json` (notas por dimensão) com `D:\postador-de-videos\_analise\metricas_studio.json` (views,
   ret30) pelo vídeo (a ligação pasta -> video_id está no ledger que o notificar_telegram.py usa, `led[vid]["caminho"]`).
2. Quais dimensões preveem resultado? Reescrever o prompt do júri para prever o que o público faz, não o gosto
   genérico de um modelo.
3. Decidir se o melhorador pode ser ligado e com que métrica (júri, views, ou as duas).

## Fable — resultado
**29/10 02:50 — cruzamento montado; dado ainda não existe.** `python D:\video-fila\engenharia_reversa\juri_x_views.py`
liga `evolucao.jsonl` (115 vídeos com nota) → ledger (pasta → video_id; uma pasta vai a vários canais, o script
escolhe a postagem medida) → medidas_48h + metricas_studio, e imprime Spearman de nota/legibilidade/movimento/
história/retenção/graves/movimento medido × views 48 h, × continuaram e × % assistido, separando quem recebeu o
lote (views_periodo ≥ 20 — ver ER_01: sem isso o júri "erra" por causa dos vídeos que o feed nem mostrou).
- Hoje: 65 dos 115 estão no ledger, todos agendados entre 27/10 19:15 e 04/11 (publishAt), e a última medida de
  48 h é de vídeo publicado em 27/10 04:30. Ou seja, **0 com views**. O 1º lote de pares chega na noite de 29/10 e
  uns 30–40 pares até 1/11: rodar o script de novo aí (está na lista de frentes do `engenharia_reversa\PROGRESSO.md`).
- O que já dá para dizer sem esperar: (a) o júri julga 1 em 4 vídeos; para ter n ≥ 30 pares por canal vai levar
  semanas — se a nota for usada para decidir, passar o júri para 1 em 2 nos canais que recebem lote (esporte, filme,
  fatos, dicas) e deixar 1 em 4 nos mortos (manhwa, dorama, línguas), onde a nota não tem contra o que ser medida;
  (b) pelo ER_01, a métrica-alvo do júri deve ser **% assistido ≥ 65% e duração 15–25 s**, não "gancho/movimento"
  genérico: dos 5 Shorts que passaram do 1º lote, todos têm 13–24 s e 64–89% assistido; os do platô, 44%.
  O verificador "retenção" do júri deveria perguntar "quantos segundos até alguém sair?" e penalizar vídeo acima de
  30 s sem motivo, em vez de nota de gosto; (c) decisão sobre ligar o melhorador: NÃO antes do cruzamento, e nunca
  por nota sozinha — a régua primária é views_periodo/pct_media da tabela do Studio (agora lida em lote, ER_02).
