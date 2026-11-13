# Argon (Gemini web) x Sonnet web (claude.ai) — como cada um funciona e o que um pode dar ao outro

29/10/2026. Fontes: `D:\gemini-argo\proxy_argon.mjs`, `gemini_http.py`, `ARGON_MELHORIAS.md`; OmniRoute
`/app/open-sse/executors/claude-web.ts` + chunk `32948.js`; testes reais desta pasta (`PROGRESSO.md`).

## Os dois chamam ferramentas? SIM — os dois por EMULAÇÃO (nenhum tem ferramenta nativa no site)
- **Argon:** o `proxy_argon.mjs` ensina no prompt um protocolo de texto: o modelo escreve um bloco
  ```` ```tool_call {"name","input"} ```` e o proxy converte em `tool_use` do Claude Code; o resultado volta como texto.
- **Sonnet web:** o OmniRoute faz a mesma coisa por dentro (o catálogo diz `toolCalling: false`, mas testamos: devolveu
  `tool_use` certo pra `ler_arquivo`, com um texto "(empty response)" junto).
- Diferença: o Sonnet obedece o formato muito melhor que o Argon (Argon: 33% dos turnos "só texto" — explicava em vez
  de fazer; precisou de "tool_choice forçado" e do modelo híbrido "Argon pensa, outro executa").

## Tabela
| | Argon (Gemini web) | Sonnet web (claude.ai) |
|---|---|---|
| Onde roda | proxy próprio no PC1 (:20141) + túnel + proxy da VPS (:20133) | provedor `claude-web` DENTRO do OmniRoute (VPS) |
| Ferramentas | emuladas (bloco tool_call), falha muito → híbrido | emuladas pelo OmniRoute, obedece bem (1 teste) |
| Velocidade | 2–9 min por turno com prompt do Claude Code (mediana 146 s) | pergunta pequena 1–7 s; prompt grande = 429 |
| Reenvia o histórico todo? | SIM, sempre (`_pedido(prompt,...)` não guarda conversa) | NÃO precisa: já reaproveita a conversa (`prefixHash`) — mas se perde quando o rodízio troca de conta |
| Contas | ~28 Pro (Google One) | 48 grátis (claude.ai Free) |
| Cota acaba | silenciosa (vira Flash-Lite) → detectado pelo "4 Argon" na resposta | 429 explícito "Rate limited" |
| Hora de volta | EXATA (lê do Google; 2 h–4h45) | não lê; regra fixa de 10 min |
| Cookie morto | zelador renova sozinho em 2º plano + "oi" individual antes de voltar | nada automático; health check da VPS dava "expired" FALSO (desligado) |
| Fila | 1ª pronta (não rodízio), fica até esgotar | rodízio do OmniRoute (espalha → perde o reuso) |
| Monitoramento | `argon_turnos.jsonl` + `argon_relatorio.py` + aviso no Telegram (monitor_argon) | usage_history NEM registra o claude-web; só `docker logs` |
| Se cair | `argon_manter` (5 min) religa proxy/túnel | dentro do OmniRoute, cai junto com ele |

## O que o Argon pode dar ao Sonnet web
1. **Fila "1ª pronta até esgotar" (não rodízio)** — é exatamente a afinidade que falta pro reuso de conversa do
   claude-web funcionar. O Argon já prova que funciona. Maior ganho.
2. **Hora real de volta da cota** — o Argon lê a hora do Google; o claude.ai manda `retry-after`/mensagem de limite
   (o executor já repassa `Retry-After` quando vem). Usar isso em vez dos 10 min fixos.
3. **Zelador de cookie** — renovar o sessionKey antes de vencer (25/11) sem a dona, com "oi" de teste antes de voltar.
4. **Monitor + Telegram** — relatório de turnos (só texto, erro, tempo) e aviso quando todas esgotam / voltam.
5. **tool_choice forçado** — se o Sonnet devolver só texto quando era obrigado a usar ferramenta, pedir de novo 1x.

## O que o Sonnet web pode dar ao Argon
1. **Reuso de conversa** — o Gemini web também tem id de conversa (`cid, rid, rcid` já são lidos no `_parse`, mas
   jogados fora). Continuar a mesma conversa e mandar só o turno novo cortaria os 2–9 min por turno e a cota gasta.
   É o maior ganho do lado do Argon.
2. **Morar dentro do OmniRoute** — sem túnel PC1↔VPS (que caiu 2x em 28–29/10). O OmniRoute já tem `gemini-web`
   com 2 contas; ver se o executor dele aguenta o Argon com o nível Alto.
3. **Erro explícito** — o claude.ai responde 429 claro; o Gemini troca de modelo calado. Já resolvido no Argon pela
   conferência do "4 Argon", então aqui é só manter.

## Resumo
- Os dois chamam ferramenta do mesmo jeito (emulação); o Sonnet obedece melhor e é muito mais rápido.
- O Argon é melhor em GERENCIAR contas (fila, hora de volta, zelador, monitor).
- O Sonnet web é melhor em GASTAR menos por turno (reuso de conversa já embutido).
- Juntar: fila do Argon no Sonnet web (reuso passa a funcionar) e reuso de conversa no Argon.
