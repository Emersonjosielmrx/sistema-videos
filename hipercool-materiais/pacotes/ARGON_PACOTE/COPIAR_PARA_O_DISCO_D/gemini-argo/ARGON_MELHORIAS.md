# Argon puro no Claude Code — tirar as limitações (pedido da dona 27/10)

Retomável: cada item marcado quando feito E testado. Proxy = D:\gemini-argo\proxy_vps.mjs (cópia fiel do que roda na VPS hermes-bloqueio desde 30/10; as cópias velhas estão em arquivo\)
(VPS hermes-bloqueio
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

## 29/10 03:55 (Fable) — Argon caído desde 28/10 20:46 sem ninguém ver; agora inicia sozinho
- Causa: o `gemini_http_proxy.py` (:20141) e o túnel `ssh -R` morreram no PC1 (sessão que os lançou fechou/reiniciou);
  a VPS :20133 (node) continuou no ar e passou a responder **502**. O `MonitorArgon` só mede as contas (dizia "28
  prontas, funcionando") — não via o proxy. Todas as linhas caíram no Gemini 3.8 em silêncio.
- Correção: `argon_manter.py` (sobe o proxy escondido se :20141 não responde; recria o túnel se a VPS não escuta a
  20141; grava `argon_manter.json`; avisa no Telegram só quando relança). Tarefas `ArgonManter` (5 min) e
  `ArgonManterLogon` (ao iniciar). Teste ponta a ponta 03:55: "ok" em 66 s e 44 s pelo :20133, modelo gemini-4-argon.
- Status: `python D:\gemini-argo\argon_manter.py --status`. O `manter_tunnel.py` antigo fica como referência.

## 29/10 19:15 (sessão PRODUTOS) — pensamento MÁXIMO em todos (dona)
- `gemini_http._pedido`: o nível de raciocínio Alto (f.req[68] / jspb[11] = ARGON_NIVEL) ia só no "argon"; o "pro"
  (gweb/gemini-3.1-pro) ia no padrão da conta. Agora vai nos dois. Proxy :20141 reiniciado; teste ok (19 s, certo).
- argon-pro / argon-flash: o Argon já ia no Alto; a reserva é agy/gemini-3.8-flash-HIGH (o maior que existe).
- Sonnet web (cw/claude-sonnet-5-5): os sufixos -max/-xhigh existem no OmniRoute mas NÃO mudam nada (mesma resposta,
  0 tokens de pensamento, 3 s): o claude-web não manda nível de pensamento ao claude.ai. Anotado em
  `D:\sonnet web\PROGRESSO.md` para quem cuida dele.

## 29/10 14:08 (sessão PRODUTOS) — túnel "de pé" que não entregava nada
- Sintoma: argon-pro / argon-gemini / gweb/gemini-3.1-pro = 502 "Argon proxy unreachable: socket hang up" em 3 s,
  com 28 contas prontas no :20141 e `argon_manter --status` dizendo tunnel=true. Na VPS a 20141 escutava, mas
  `curl 127.0.0.1:20141/health` lá voltava VAZIO.
- Causa: o túnel era `-R 20141:localhost:20141`; o proxy escuta só em 127.0.0.1 e "localhost" no PC1 foi para ::1.
  O manter só olhava se a porta escutava na VPS (`ss`), não se a resposta passava.
- Conserto (`argon_manter.py`): `-R 20141:127.0.0.1:20141`; `tunnel_ativo()` pede `/health` pela VPS (porta aberta
  e mudo = recria). Testado: túnel recriado 14:08, health ok pela VPS, os 3 modelos responderam (28–46 s).

## 29/10 ~18:50 — REUSO DE CONVERSA (dona: "não mandar a conversa toda de novo"; ideia copiada do Sonnet web)
- Antes: todo turno abria conversa nova no Gemini com o histórico inteiro (248 turnos em 2 dias pelo Claude Code,
  208 no argon-gemini, 2–9 min cada). O `_parse` já lia `cid, rid, rcid` e jogava fora.
- Agora: `gemini_http._pedido(..., meta)` põe `[cid, rid, rcid]` em `inner[2]` (continua a conversa); `ULTIMA`
  (thread-local) guarda conta+ids da última resposta. `gemini_http_proxy._gerador`: chave = hash das mensagens
  (role + texto normalizado); se o histórico novo começa com uma conversa guardada (até o `assistant`), manda SÓ do
  assistant em diante, mesma conta, `tentativas=1`; falhou antes do 1º pedaço = histórico inteiro como antes (pior
  caso = igual a hoje). Guarda 60 min, até 400 conversas. Não-stream agora usa o mesmo gerador (stream por baixo).
- Pipelines de vídeo (`gemini_http.perguntar(prompt)` direto) NÃO mudam (sem `meta`).
- Teste (`teste_reuso.py <porta>`): turno 2 sem o número no texto respondeu "4817" do turno 1 = continuou a conversa;
  7.555 caracteres poupados. Feito na porta de teste 20142 e depois na produção 20141 (18:51), túnel e :20133 ok.
- Medir: `curl 127.0.0.1:20141/cota` → `reuso: {acertos, erros, chars_poupados, conversas}`; log "reuso:" no
  gemini_http_proxy.err.log.
- Desfazer (os .bak estão em `arquivo\` desde 30/10): `copy arquivo\gemini_http.py.bak_antes_reuso_29out gemini_http.py` + `copy arquivo\gemini_http_proxy.py.bak_antes_reuso_29out
  gemini_http_proxy.py`, matar o pid da :20141 e rodar `python argon_manter.py`.
- Risco a observar: nos híbridos a resposta do assistant pode ter vindo do reserva — ela vai junto no turno novo, então
  o Gemini vê o que foi de fato executado. Conversa muito longa no Gemini pode encher; aí cai no histórico inteiro.

## 29/10 (Fable) — gerenciamento fora do pedido + zelador
- Ver D24 em `D:\hipercool-materiais	arefas complexas para fable 5.1\FABLE_DECISOES.md`. Resumo: cookie morto não trava
  mais o pedido (próxima conta na hora; `argon_zelador.py` renova em segundo plano, tarefa ArgonZelador 5 min), stream
  tenta a próxima conta, desbloqueio gravado, 1 Session por conta, prazo 580 s, `/cota` com cookies_mortos, `mcp_argon`
  na porta certa (20141), `argon_manter` confere /health e o :20133 da VPS.
- Regra da dona: conta que volta da cota recebe um "oi" individual (zelador) antes de voltar à fila.
- Dado novo: "cota volta em < 1 h" estava errado; a hora que o Google manda foi de 2 h a 4 h45 depois de esgotar (log 28/10).

## 29/10 ~20:45 — cota do Pro, Sonnet no lugar e mais chamadas de ferramenta
- A cota do Argon e a do 3.1 Pro são A MESMA (testado: conta sem Argon pedindo Pro = "3.5 Flash Lite, limite atingido").
- `gemini_http._conferir_servido` agora confere o Pro também (servido "3.1 Pro"): Flash-Lite no lugar do Pro = conta sai
  da fila e a próxima responde (antes o Flash respondia calado como se fosse o Pro).
- Proxy :20133: Argon/Pro sem cota em TODAS as contas (429 "Nenhuma conta com cota") -> `cw/claude-sonnet-5-5` responde
  com "[AVISO: ... Quem responde abaixo e o Sonnet 5.5 web.]" na 1ª linha (`sonnetNoLugar`). Testado com ponte falsa
  devolvendo 429, com e sem stream/ferramentas. Backup `proxy.mjs.bak-antes-semcota-29out`.
- Proxy: queda de conexão da ponte (socket hang up/ECONNRESET, 27% dos turnos do Argon puro) repete até 2x
  (`argonTexto`). Backup `proxy.mjs.bak-antes-repetir-29out`.
- Mais ferramentas: instrução nova ("nunca responda de memória; em vez de anunciar 'vou ler', chame") e, se a resposta
  só em texto anunciar ação ("vou rodar", "let me check"), o proxy pede de novo 1x cobrando o bloco (`PROMETEU_ACAO`,
  aparece como refeito=prometeu_acao no argon_turnos.jsonl). Só no Argon/Pro puros; os híbridos não mudaram.

## 30/10 ~12h — revisão geral (robustez)
Achado ao vivo 11:26–12:29: PC a 100% de CPU e 1,8 GB de RAM livre; o `/health` do :20141 levava 25 s. O `argon_manter`
(1 tentativa de 8 s) matou o proxy SÃO, subiu outro que levou 15 min para importar (`import requests` = 15 s) e, na
passada seguinte, subiu um TERCEIRO: dois proxies escutando a mesma :20141 (o SO_REUSEADDR do ThreadingHTTPServer
deixa no Windows) e os pedidos caindo no que ainda subia. Argon fora ~1 h.
- `gemini_http_proxy.py`: porta EXCLUSIVA (SO_EXCLUSIVEADDRUSE; o 2º processo sai com código 3); cliente que fecha a
  conexão vira 1 linha no err.log (antes traceback de 20 linhas, 15× por dia); JSON inválido = 400; o reuso não tenta mais
  a conta da conversa se ela já está sem cota/cookie morto (`reuso.pulados` no `/cota`; antes 28 pedidos/dia jogados fora).
- `argon_manter.py`: 3 tentativas de `/health` de 20 s antes de dar o proxy por morto; acha TODOS os
  `gemini_http_proxy.py` (não só o pid guardado); proxy com menos de 5 min de vida = "subindo", não sobe outro em cima;
  duplicado sobrando é derrubado (fica o dono da porta); espera até 2 min o proxy novo; gira o err.log em 5 MB.
- `gemini_http.py`: o stream fecha a resposta HTTP em qualquer saída (SemCota no 1º pedaço, cliente que desistiu, erro);
  antes a conexão ficava presa na Session da conta. URL/cabeçalhos do StreamGenerate num lugar só (`_url_headers`).
- `argon_zelador.py`: os "oi" de confirmação rodam 4 por vez (a passada com 15 contas aguardando passou de 26 min).
- `monitor_argon.py`: conta com cookie morto não conta mais como "pronta" (dizia "funcionando" com a fila vazia).
- `youtube_http.py`: cookies com domínio (o Set-Cookie do Studio criava 2ª cópia; SAPISID duplicado =
  CookieConflictError), gravação atômica (JSON cortado deixava o canal falhando até sync à mão; agora ressincroniza),
  erro claro para período inválido e página do Studio sem INNERTUBE_*.
- VPS `proxy.mjs` (fonte local: `proxy_vps.mjs`; backup na VPS `proxy.mjs.bak-antes-robustez-30out`): texto do stream
  decodificado direito (acento partido entre pacotes virava "��"); erro da ponte no meio da resposta vai como
  `event: error` (antes virava end_turn e a resposta cortada passava por completa); stream sempre fecha com
  message_stop; `return await` nos handlers + guarda de cabeçalho já enviado + `unhandledRejection` (antes 1 erro solto
  derrubava o node de TODOS os modelos).
- Testado: porta de teste 20142 (2º processo recusado, JSON ruim 400, Argon "391" em 38 s, stream ok, /cota ok);
  produção :20141 reiniciada 12:52 com túnel e :20133 ok.

## 30/10 ~13:45 — segunda rodada
- Renovar cookies pelo cofre tinha prazo nenhum: o Chrome da conta_exemplo travou 3818 s e a passada do zelador levou
  75 min. Agora `gemini_http._sync_com_prazo` roda o `sync_cookies.py` num processo à parte com prazo de 240 s
  (`ARGON_RESYNC_PRAZO_S`); estourou = derruba o processo e o Chrome filho. Testado (prazo 8 s: cortou, 0 Chrome aberto).
  `sync_cookies.py` agora sai com código 1 quando alguma conta falha.
- Esc no Claude Code agora CANCELA o Argon: na VPS, cada pedido tem um AbortController (AsyncLocalStorage `PEDIDO`) que
  chega a todas as chamadas à ponte e ao reserva (ferramentas, hx, híbridos, Sonnet no lugar); no PC, o
  `gemini_http_proxy` confere a cada pedaço se o cliente ainda está lá e corta o Gemini (libera a conta e a vaga).
  Testado na cópia :20199 da VPS: curl desistiu em 5 s -> VPS "cliente desistiu do pedido" -> PC "Argon cortado".
- Ponte que cai NO MEIO da resposta (túnel caiu) não deixa mais o pedido pendurado para sempre: vira "socket hang up"
  e entra na repetição que já existia (`seCairNoMeio`).
- 429 da ponte: o "Nenhuma conta com cota" depois do caractere 200 agora também liga o Sonnet no lugar.
- VPS publicada 17:46 (hora da VPS), backup `proxy.mjs.bak-antes-cancelar-30out`; :20133 testado de ponta a ponta.
- .bak e cópias velhas do proxy foram para `arquivo\`.
- Ainda pendente, decisão da dona: o :20133 escuta em 0.0.0.0 sem chave (qualquer um que alcance a porta usa a cota).
  Não mexi: o firewall da VPS já bloqueia 1080/1081/12346/20160 no eth0, mas NÃO a 20133, e há fluxos no PC que chamam
  pelo IP público (IP_DA_SUA_VPS:20133 em workflows do .claude e .claude-vscode). Bloquear = trocar esses para o
  túnel/Tailscale antes; a outra saída é exigir uma chave no cabeçalho.

## 30/10 ~14h — chave na :20133 (dona: "pode melhorar a segurança, mas que não quebre nada")
- Teste de fora (PC pelo IP público): Argon SEM chave respondia, e o `cw/claude-sonnet-5-5` sem chave também deu 200
  (o OmniRoute só pede chave no /v1/models). Ou seja: a :20133 inteira estava aberta.
- `proxy.mjs`: todo pedido de chat confere a MESMA chave do OmniRoute que os clientes já mandam (`x-api-key` ou
  `Authorization: Bearer`; validada pedindo /v1/models ao OmniRoute com ela, cache 10 min). VPS local e Tailscale
  (100.64/10) passam sem chave. Se o OmniRoute falhar, deixa passar (não quebra).
- Publicado em `MODO_CHAVE=observar`: NÃO bloqueia nada, só registra quem seria barrado. Backup
  `proxy.mjs.bak-antes-chave-30out`. Testado com `exigir` na cópia :20199: de fora sem chave/chave falsa = 401; de
  dentro = passa.
- Ver quem seria barrado (o proxy grava em arquivo, NÃO no journal):
  `ssh hermes-bloqueio "grep '\[CHAVE\]' /opt/antigravity-cc-proxy/proxy.log | tail -30"`.
  Conferido 30/10 18:11 (hora da VPS): pedido de fora sem chave foi ATENDIDO e registrado "seria barrado" (como deve).
  Se aparecer cliente legítimo com "chave invalida", a validação pelo /v1/models não serve para a chave dele: corrigir
  ANTES de exigir.
- 30/10 14:10: o zelador das 13:08 (ainda no código SEM prazo, abriu antes da correção) ficou 1 h preso num Chrome
  da conta_exemplo; a tarefa tinha limite de 72 h e IgnoreNew, então nenhuma passada nova rodava. Derrubado; limite da
  tarefa ArgonZelador baixado para 1 h (com os prazos novos uma passada cabe folgada).
- 30/10 14:20 — FILA CAIU A 1 CONTA. Causa medida: o cookie que o Chrome entrega morre ~2 h depois (290 casos no
  argon.log: mín 1,9 h, mediana 2,1 h, máx 4,5 h). A página do Gemini volta deslogada, mas o login da conta continua vivo
  (RotateCookies responde `identity.hfcr`) e há cookies `__Secure-1PSIDRTS`: é a sessão presa ao Chrome (DBSC) — o HTTP
  não consegue renovar sozinho, só o Chrome. Rodar RotateCookies por HTTP NÃO resolve (testado: 200 sem PSIDTS novo).
  E com 2,1 GB de RAM livre o zelador não renovava nada (mínimo 3 GB).
  Conserto (`argon_zelador.py`): renova ANTES de morrer — conta com cota cujo cookie tem 1,6 h (`cookies_novos_em`,
  gravado a cada renovação) entra na fila de renovação; mortas com cota primeiro; conta sem cota só perto da volta (30
  min). RAM abaixo de 3 GB: primeiro libera (chrome_conta._liberar_ram) e, com menos de 4 prontas, aceita 1,5 GB.
- 30/10 14:45 — zelador: 1ª passada nova renovou 6 contas (82–144 s cada) e confirmou as 6 com "oi"; fila 1 -> 7.
  Ajustes: conta já sabida morta vai direto à renovação (não reconfere por HTTP antes); só 1 zelador por vez (trava
  `argon_zelador.lock`; o agendado e um rodado à mão renovavam juntos); meta de `ARGON_ALVO_PRONTAS`=10 prontas — com a
  fila cheia só a preventiva do que falta para 10 (~6 Chromes/h em vez de ~18 para manter as 29).
- `monitor_argon.py`: a mensagem diz "cookie morto (zelador renovando)" quando é isso, não "sem cota".
- `gemini_http`: Gemini que reescreve o texto no meio do stream não duplica mais o começo para o cliente (manda só o
  que vem depois do começo em comum) e fica registrado ("reescreveu o texto") para saber quanto acontece.
- `argon_relatorio.py`: usava o ssh do Windows (travava 60 s e caía) e baixava o arquivo inteiro; agora ssh do Git +
  só as últimas 20 000 linhas. 1º relatório de 48 h: 535 turnos, 20% erro (43 ECONNREFUSED na :20141, 35 socket hang
  up — a queda de hoje), mediana 22 s, WebFetch voltou com erro 136× ("Credit balance is too low", problema do WebFetch).
- VPS `proxy.mjs` (backup `proxy.mjs.bak-antes-pontefora-30out`): ponte do PC fora mesmo depois das repetições = o
  Sonnet responde no lugar com "[AVISO: ... fora do ar agora ...]" (antes: erro); instrução nova "ferramenta que voltou
  com erro não se repete do mesmo jeito; WebFetch falhou = curl pelo Bash"; "(empty response)" do Sonnet sai da
  resposta; `ARGON_PORT` configurável (só para teste). Testado em cópias :20198 (ponte num porto fechado: Sonnet
  respondeu nos 2 caminhos) e :20199 (normal: acentos e ferramentas ok); produção conferida depois.
- Ligar o bloqueio (só depois de alguns dias de log limpo): `systemctl edit antigravity-cc-proxy` ->
  `[Service]` `Environment=MODO_CHAVE=exigir`, depois `systemctl restart antigravity-cc-proxy`. Desfazer = apagar a linha.
