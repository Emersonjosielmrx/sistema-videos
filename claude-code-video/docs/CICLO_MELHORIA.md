# Ciclo de produção + melhoria (Gemini multiagentes) — retomar daqui

Pedido do dono (26/10 ~04:20): "analise tudo que podemos melhorar usando o Gemini e teste até termos o melhor
resultado possível, e vá fazendo vídeos dos produtos (não perder os vídeos gerados): ciclo de produção e melhora".

## Como roda
- Roteiro: Opus 5.5 (único uso do Claude Pro, ~4 pontos). Edição + lapidação: `agy/gemini-3.8-flash-high`.
- `etapa_lapidar` (gerar.py): 4 verificadores em paralelo (legibilidade, movimento, roteiro_marca, diretor) ->
  corretor -> re-render; até média >= 9 sem grave ou 4 rodadas; fica a melhor versão. Notas em
  `trabalhos/<id>/estado.json` -> `lapidar[]`.
- Tarefa `ClaudeCodeVideo` (20 em 20 min) emenda os vídeos, 1 por vez (trava), até `videos_por_dia` = 6.
- Cada ciclo: ler as notas/problemas dos vídeos novos -> defeito que se repete vira regra no
  `remotion/EDITOR.md` (seção "Aprendido dos verificadores") -> conferir se a nota da rodada 1 sobe.

## Histórico de notas (rodada 1 = como o editor entregou; última = depois do corretor)
| vídeo | editor | regras EDITOR.md | rodada 1 | final | rodadas |
|---|---|---|---|---|---|
| futebolcom_ia2_20261026_030812 (Cardápio) | gemini tiered | antigas | 5.62 (8 graves) | 7.62 (r6) | 6 |
| disparoemmassa_ia_20261026_040320 (Disparo) | gemini high | EDITOR.md novo | 6.25 (6) | 6.55 | 3 |
| sintetizerisada_20261026_122049 (Agenda IA) | gemini high | + APRENDIDO.md (21 regras) | 6.5 (5) | … | |

13:55 movimento medido: diferença de imagem 20%→80% da cena (MOV_MIN 4%). Calibrado: cenas que os verificadores
chamaram de paradas deram 2.2–2.8%; cenas vivas 7–9%. Vai para verificadores + corretor; EDITOR.md manda conferir.

Júri igual (4 verificadores Gemini) nos vídeos do Claude Opus 5.5: Cardápio 5.75 (10 graves), Hermes Call 6.25 (6).
Contagem completa de cada vídeo em `estado/evolucao.jsonl`. Crons "continue" de hora em hora (min 37) até 28/10 13:41.

## Diagnóstico 26/10 05:20
O corretor estaciona (~+0.1 por rodada): conserta uns e cria defeitos novos (inventou "24h"/"30 min", scroll
cortando item, legenda de 2 linhas abaixo de 1580). Feito: corretor recebe os fatos permitidos + "não estrague"
(scroll inteiro, legenda pela base, letra/zona) + graves da rodada anterior ("mude a abordagem"); até 6 rodadas,
para se 2 rodadas seguidas não superam a melhor; EDITOR.md ganhou essas regras + 2 camadas de leitura no máximo +
cartão final enxuto. Vale a partir do Disparo em Massa (o Cardápio roda o código antigo, já carregado).

## Feito
- 26/10 04:25 regras novas no EDITOR.md: gancho 0–2 s, nada parado > 1,5 s, variar layout, rostos livres, letra
  ≥ 32 px, zona segura p/ cabeçalho, karaokê com espaço, mockup com fotos reais, foto coerente com a fala, CTA =
  ação da fala final (antes mandava "Link no perfil" e a voz dizia "chame no direct"), cartão final com foto.
- feitos_hoje não conta mais os trabalhos de comparação.

- 05:35 corretor estourou 60 turnos ("MotorErro: None None" = error_max_turns) e derrubou a etapa. Agora: editor e
  corretor com aceitar_limite (o que mudou já está no disco), corretor 90 turnos, e a lapidação renderiza antes de
  verificar se o código é mais novo que o vídeo (retomada). Cardápio retomado com código novo às 05:36.

- 08:45 dono: "era pra fazer vídeos DIFERENTES dos produtos, melhorando a cada vídeo, não o mesmo repetido".
  Mudou: lapidação máx 3 rodadas; `_aprender` no fim de cada vídeo -> Gemini reescreve `remotion/APRENDIDO.md`
  (lido pelo editor) com os defeitos da 1ª versão; `estado/evolucao.jsonl` = nota da 1ª versão por vídeo (a métrica
  do ciclo); roteiro com reserva Gemini (`roteiro_reserva`) quando falta cota do Claude — produção não para mais.
  Roteiro Gemini precisava de max_turnos 8 (com 2 dava error_max_turns: era o "falhou" da comparação).

- 13:25 dono: "continue os ciclos até ficar bom para todos os cenários de todos os produtos, sem atrapalhar os
  outros". Feito: 7 produtos na rodízio (+ vpsblindada.ia, fabricademarketing.ia); gerar.py em prioridade baixa
  (filhos herdam), render --concurrency=2, vídeo novo só com RAM livre >= 3 GB; EDITOR.md exige plano.md com
  composição por cena (8 tipos, sem repetir seguidas, >= 4 diferentes) para atacar o "diretor" travado em 6.

- 26/10 14:59–17:20 PRODUÇÃO PARADA: o Chrome do Remotion travou no render da correção da Agenda; o timeout de
  3600 s matou só o npx e os netos (node/chrome) seguraram o pipe -> gerar.py preso em communicate() 2h20.
  Conserto: motor.executar (saída em arquivo + mata a árvore no timeout), usado no claude.exe e no render; render
  20 min com 2ª tentativa. Retomado 18:00 pela tarefa. Crons de "continue" recriados (a sessão reiniciou).

## Meta de "bom" (para encerrar o ciclo)
Os 7 produtos com 1ª versão >= 7,5 e final >= 8, diretor >= 7, sem grave no final. Até lá: cada vídeo novo -> ler
evolucao.jsonl + graves que se repetem -> ajustar EDITOR.md/verificadores/corretor.

## Próximas frentes
1. Ver nota final do Cardápio (antes = `saida/futebolcom.ia2/futebolcom_ia2_20261026_030812_ANTES_multiagentes.mp4`).
2. Disparo em Massa (disparoemmassa_ia_20261026_040320) retoma sozinho (parou em roteiro+narração) — 1º com regras novas.
3. Comparar rodada 1 dos vídeos com regras novas x 5.62. Se o corretor não subir a nota entre rodadas, mudar a
   estratégia do corretor (ex.: 1 corretor por cena, em sequência).
4. Opus 4.6 antigravity: 403 "conta não elegível" — fora da comparação até alguém liberar.
