# ER_03 — Hipercool: 40 vídeos medidos, nenhum passou de 8 views

## Fato (29/10, ledger com projeto=hipercool, views de 48–120 h)
- hipercool/short: 27 vídeos, mediana 1, máximo 3. Faixas: 0 = 4, 1–9 = 23, nada acima de 9.
- hipercool/completo (longo): 13 vídeos, mediana 1, máximo 8.
- Canais: novo_manhwanoturno (8 shorts med 2 + 3 longos med 2), GtuH5ezUK8eBaC60, 7zpNZNll2jlBnQ0J,
  nYsAKUb3DbR1QOEm, TkfzifstYEoG4jKg, 8ROQmZVjbpwiwMoX, q3mik36FjtTgFkNC (it/id/ru/th/vi/hi: ver ER_04).
- No MESMO canal manhwanoturno, Short de parceiro já teve 1 acima de 500 (de 9). O hipercool nunca chegou a 10.

## Contraste
Na mesma janela, Short de parceiro: 25% passam de 500. Hipercool: 0 de 40 passou de 10. A diferença é grande demais
para ser título ou hora: é algo do próprio vídeo ou de como o YouTube o classifica.

## SUPOSIÇÕES (não provadas)
- Conteúdo de manhwa adulto/censurado (mosaico) cai em "não recomendável" e nem entra no lote de teste.
- Narração/estrutura de recap longo cortada vira Short sem gancho nos 2 s.
- Os canais estrangeiros do hipercool já estão sem confiança (ver ER_04).

## Tarefa para o Fable
1. Com ER_02 resolvido, ver impressões dos Shorts do hipercool: 0 impressões = não recomendável (classificação);
   impressões e "deslizou" alto = gancho.
2. Comparar 3 Shorts do hipercool com 3 Shorts de parceiro do mesmo canal manhwanoturno que pegaram (quadros dos
   2 primeiros segundos, legenda, ritmo). Ferramenta: `D:\claude-code-video\referencia.py` (adicionar e analisar).
3. Projeto: `D:\hipercool-videos` (ler CLAUDE.md e docs/correcoes_pendentes.md). Regras: censura só na parte,
   capa estilo Porão, Manhwa Noturno exclusivo do hipercool (memórias feedback_censura_partes, feedback_capas).

## Fable — resultado
**29/10 03:35 — Tarefa 1 respondida com o dado que já existe (impressões do feed não vêm por vídeo, ver ER_02):**
dos 55 vídeos do hipercool no `metricas_studio.json`, 19 têm "continuaram" lido: **18 em 100% e os 19 com menos de
10 views no período** — o padrão exato de "o feed não deu o lote" (ER_01). Não é gancho nem "deslizou": ninguém
foi mostrado. Ou seja, SUPOSIÇÃO 1 (classificação "não recomendável": manhwa adulto/censura/mosaico, ou canal sem
confiança) é a que sobra; SUPOSIÇÃO 2 (gancho) está descartada porque não há teste de gancho sem público.
- O que testar (7 dias, sem parar canal): no manhwanoturno, que recebe lote para Short de parceiro (1 de 9 ≥500),
  postar 2 Shorts do hipercool SEM nenhuma cena censurada/mosaico (capítulo "limpo", só diálogo/ação) e comparar
  `continuaram`/`views_periodo` com os censurados da mesma semana. Se o limpo receber lote (continuaram < 90% com
  ≥ 50 views) e o censurado não, a causa é a classificação do conteúdo; aí vale tirar o mosaico da área visível e
  deixar o tema implícito (regra da dona: censura só na parte — mas o YouTube pode estar lendo a parte censurada
  como sinal). Se nem o limpo receber, é o canal/upload (conteúdo reaproveitado de manhwa já postado por outros).
- Tarefa 2 (comparar quadros com Shorts de parceiro que pegaram) não vale a pena antes desse teste: compara-se
  vídeo que nunca foi mostrado com vídeo mostrado; a diferença visual não explica o que o feed decidiu antes de
  mostrar.
