# Argon puro no Claude Code — tirar as limitações (pedido da dona 27/10)

Retomável: cada item marcado quando feito E testado. Proxy = D:\gemini-argo\proxy_argon.mjs (VPS hermes-bloqueio
/opt/antigravity-cc-proxy/proxy.mjs, porta 20133); Argon HTTP = gemini_http.py + gemini_http_proxy.py (PC1 :20141,
túnel até a VPS).

| # | Item | Como | Estado |
|---|---|---|---|
| 1 | Simultâneos | VAGAS do gemini_http_proxy = nº de contas (mín. 6) | feito 27/10 (vale ao reiniciar o :20141) |
| 2 | Monitoramento de erros | proxy grava cada turno em /opt/antigravity-cc-proxy/argon_turnos.jsonl; `python -X utf8 argon_relatorio.py [horas]` resume e sugere | feito e testado 27/10 |
| 2b | 1º achado do monitor | 33% dos turnos "só texto": o Argon explicava o conserto sem fazer (calc.py 40 min, nada editado) -> instrução "FAÇA até o fim, old_string exato" | feito 27/10 11:30; testado: calc.py consertado e testes passando (antes: só explicava), mas 40 min/6 turnos. Dona 27/10: Argon NÃO é usado para vibe code, só dentro dos pipelines de vídeo por HTTP |
| 3 | tool_choice forçado | se o pedido obriga ferramenta e ele só escreveu texto: pede de novo 1x com a ordem explícita | feito (não testado ao vivo) |
| 4 | Saída em formato fixo | output_format/response_format: valida o JSON; inválido = pede de novo 1x com o erro | feito (não testado ao vivo) |
| 5 | Contagem de tokens | usage estimado (caracteres/4) pro auto-compactar funcionar | feito (não testado ao vivo) |
| — | Achados | cota volta em < 1 h (descanso 45 min); Argon real leva 2–9 min por turno com o prompt do Claude Code (mediana 146 s) | |
| 6 | Testar ferramentas | Agent/subagente, WebFetch, MCP, TodoWrite, AskUserQuestion, Skill, ExitPlanMode | |
| 7 | WebSearch | pedido com server tool web_search -> o Argon pesquisa (Gemini tem busca Google) e o proxy devolve no formato | |
| 8 | Imagem e PDF | capturar o upload do Gemini web (content-push) e mandar os anexos | |
| 9 | Texto aos poucos | stream do texto antes do 1º bloco tool_call | |
| 10 | Mais contas | classificar_pro.py | 29 Pro em 27/10 ~13h; bug achado: sync_cookies misturava cookies de .google.com.br (mesmo nome) e a conta ficava "deslogada" -> corrigido, refazendo as 30 não-Pro |
| 11 | Raciocínio ALTO de verdade | o navegador manda 99 campos no f.req (o nosso: 3) e mais posições no cabeçalho jspb; confirmado (captura Baixo/Médio/Alto no app novo, processSession campo 18: Baixo 3, Médio 0, Alto 2) -> gemini_http._pedido manda f.req[68]=2 e jspb[11]=2 em TODA chamada do Argon (ARGON_NIVEL muda). Medido: ~2,4x mais tempo (10->25 s), mais raciocínio | FEITO 27/10 ~15:50 (antes disso o Argon rodava no nível padrão, mais raso) |
| 12 | Prompt-base p/ pensar mais | depois do 11: testar com/sem preâmbulo no mesmo pedido | a fazer |
| 13 | Combinações p/ CÓDIGO | dona: dupla só vale se ganhar do reserva sozinho; Opus vale se igualar gastando menos Opus. Prioridade Gemini: agy/gemini-3.8-flash-high x hx-{socorro,maos,plano,revisor,erro}-gemini x argon-flash no hibridos_real.py (3 tarefas reais) | a fazer depois do 11 |
| 13b | Resultado código (Gemini) | hx-maos-gemini 37/37 559 s · socorro 37/37 · Argon puro 36/37 · Gemini sozinho 22/37 · argon-flash 16/37 (detalhe no COMPARACAO_MODELOS.md) -> argon_pro.txt = hx-maos-gemini | FEITO 27/10 ~18h |
| 15 | Fila de contas (dona: "como o OmniRoute") | proxima_conta = 1ª pronta da fila (não rodízio); sem cota sai com hora de volta (espera 15 min, dobra até 3 h, zera quando responde) e só é testada de novo nessa hora; fila vazia = erro na hora; corte no 1º pedaço quando não é o Argon (antes esperava o Flash-Lite responder inteiro); conta ocupada vai pro fim. Proxy :20141 agora sobe com Start-Process (sobrevive ao chat reiniciar) | FEITO 27/10 ~17:50, testado |
| 16 | Aviso de cota no Telegram | `monitor_argon.py` (tarefa MonitorArgon a cada 10 min, molde do monitor_opus.py): todas sem cota -> hora estimada da 1ª volta (só repete se a previsão mudar > 30 min); voltou -> confirma com 2 respostas reais do 4 Argon e avisa; "argon" no Telegram responde na hora (notificar_telegram.py) | FEITO 27/10 ~19h, testado (simulação + confirmação real) |
| 14 | Seletor | todas as variantes hx-* (Gemini, Opus, Kiro) no settings.json p/ os chats testarem | feito 27/10 |
