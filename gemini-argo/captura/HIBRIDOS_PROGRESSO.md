# Híbridos Argon + reserva — progresso (27/10)

Pedido da dona: testar todas as formas de o Argon trabalhar junto com outro modelo (Kiro Sonnet 4.5, Gemini 3.8 Flash,
Opus 4.6 Antigravity), achar a melhor e deixar NO SELETOR SÓ UM "Argon Pro" (atualizado a cada vencedor), sem encher
o seletor de modelos de teste.

## Modos (nome do modelo no proxy: `hx-<modo>-<reserva>`, reserva = kiro | gemini | opus)
- `socorro`: Argon faz tudo (ferramentas pelo protocolo de texto); reserva só quando o Argon não chama ferramenta. (= argon-kiro/gemini/opus)
- `maos`: Argon decide a próxima ação em texto; o reserva SEMPRE executa as chamadas de ferramenta.
- `plano`: reserva trabalha com ferramentas nativas; Argon escreve o plano no 1º turno (vai no system do reserva).
- `revisor`: reserva trabalha; quando ele diz que acabou, o Argon revisa; se reprovar, o reserva continua com a crítica.
- `erro`: reserva trabalha; quando uma ferramenta volta com erro/teste falhando, o Argon diagnostica e o diagnóstico vai pro reserva.
- bases: `gemini-4-argon` sozinho e cada reserva sozinho.

## Tarefas (captura/hibridos_bench/) — nota = testes passando, conferidos fora do agente
## Placar: captura/hibridos_placar.json (gravado a cada rodada)

## Banco de brinquedo (hibridos_bench.py) — PARADO no meio, a dona pediu tarefas reais
Kiro sozinho 29/30 (148 s) = plano/revisor (29/30); socorro 30/30 (1303 s), mãos 30/30 (640 s), erro 30/30 (187 s).
Argon sozinho: calc 8/8, loja 4/12. Conclusão: nessas tarefas o Argon quase não muda nada → não serve pra decidir.

## Banco REAL (hibridos_real.py, placar hibridos_real_placar.json, log hibridos_real.log)
Tarefas do nosso código: fila_agendado (bug 22/10 da fila do hipercool, 11 testes), numero_yt (bug 27/10 do
youtube_http, 15), microcortes (melhoria 22/10 dos Shorts, 11). Referência do Opus 5.5 em hibridos_real_ref/
(nota cheia; código com bug 5/11, 11/15, 0/11). CRITÉRIO: dupla só vale se ganhar do Kiro sozinho.

## ATENÇÃO (27/10 ~10h): o "Argon" respondia com Flash-Lite em silêncio
A resposta do Gemini traz o modelo servido (`"<hash>",null,null,"4 Argon",true`). As 5 contas do rodízio estavam com
"Limite atingido. Continuando com o Flash-Lite." -> testes desta tarde com Argon (brinquedo e real) rodaram pelo
menos em parte com Flash-Lite e NÃO valem como nota do Argon. Cota do Argon por conta = poucas perguntas.
Conserto: gemini_http._conferir_servido + SemCota (conta descansa 3 h, próxima responde); classificar_pro.py acha as Pro.
Kiro também caiu (401 No active credentials) às ~10h: duplas com Kiro paradas até a dona ligar contas novas.
Refazer o banco real com Argon de verdade (só quando houver muitas contas Pro com cota).

## Estado
- [x] modos no proxy + deploy (VPS /opt/antigravity-cc-proxy/proxy.mjs; backup proxy.mjs.bak-hx)
- [x] tarefas: calc (8 testes), loja (12, multi-arquivo + recurso novo), relatorio (10, achar bug com Grep + opção --json);
      testes escondidos validados (bugado 3/1/2, solução de referência cheia)
- [x] Argon Pro no seletor (`argon-pro`); o vencedor fica em /opt/antigravity-cc-proxy/argon_pro.txt (lido a cada
      pedido, sem reiniciar). Começou com hx-socorro-kiro.
- [ ] rodada completa: `python hibridos_bench.py` (retoma sozinho, pula o que já tem nota); log em hibridos_bench.log
- [ ] escolher vencedor (maior nota; empate = menor tempo) -> `ssh hermes-bloqueio 'echo <modelo> > /opt/antigravity-cc-proxy/argon_pro.txt'`
      e atualizar a descrição do Argon Pro no settings.json
