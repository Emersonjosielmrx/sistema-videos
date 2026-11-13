# Registro de correções do Telegram e do painel (31/10/2026)

Para o agente revisor: cada entrada diz o que mudou, em qual arquivo, por quê, como conferir e o que NÃO foi provado.
Pedido original da dona: ver `TELEGRAM_MUDANCAS_31_10.md` (lista de 13 frentes).
Regra: toda correção nova a partir daqui entra neste arquivo ANTES de seguir para a próxima.

Estados: FEITO-TESTADO (rodou de verdade) | FEITO-SINTAXE (só compilou/montou mensagem) | PARCIAL | DIAGNOSTICO (sem código) | PENDENTE

## Situação em 01/11 ~11:30 (ler primeiro)
| Frente | Estado | Onde está a entrada |
|---|---|---|
| 1 bot geral filtrado | FEITO; medido: 1 aviso no geral de 00h a 07h de 01/11 | 1, C3 |
| 1b PC desconectado só após 1 h | FEITO-SINTAXE | 1b |
| 2 comentários no bot de comentários | FEITO-SINTAXE | 2 |
| 3 comentários da conta pessoal | FEITO (@ciano001ofc: dona não respondeu se é dela) | 3 |
| 4 contas deslogadas | FEITO; avisos falsos da 1ª noite corrigidos | 4, C1, C2 |
| 5 limite de postagem nosso mudo | FEITO-TESTADO | 5 |
| 6 longos em destaque | FEITO-SINTAXE | 6 |
| 7 Argon/Sonnet no bot do Opus | FEITO (rota) | 7 |
| 8 erros de produção | NÃO FEITO — frase cortada na mensagem da dona | — |
| 9 ficha do longo (tempo, onde, atualizações) | FEITO-TESTADO (texto real), não visto num longo novo | C4 |
| 10 painel de views | FEITO-TESTADO; painel :8790 reiniciado e respondendo 30 canais | 10, C5, C6 |
| 11 aprendizado aprova sozinho + IA | FEITO-SINTAXE | 11 |
| 12 interessados no produto | só o prompt (projeto de outro agente); outra sessão já ligou o bot (aviso "produto-lead" 01/11 07:02) | — |
| 13 duplicados do Studio | aviso foi para o resumo; regra de reaproveitar fonte NÃO mudada | 13, Correção 13 |

Todos os 14 arquivos tocados compilam (conferido 01/11).

## Modelo de entrada
- Frente / estado
- Arquivos
- O que mudou
- Por quê (pedido da dona)
- Como conferir
- Não provado / risco

## Entradas já feitas (antes deste registro)

### 1. Bot geral recebia tudo — FEITO-SINTAXE
- Arquivo: `D:\video-fila\avisos.py` (ROTA, SO_RESUMO, SO_REGISTRO)
- Mudou: argon/sonnet/troca-modelo vão ao bot opus; melhorador, eng. reversa, máquinas, longo vão a produção; banimento, nsn, telão, vigia desktop, instagram login, credenciais vão a pendências humanas. Rotina que se resolve sozinha só vai ao resumo/registro.
- Conferir: `python D:\video-fila\avisos.py` (contagem por origem nas últimas 24 h); o bot geral deve cair muito.
- Não provado: um dia inteiro real após a mudança.

### 1b. PC desconectado — FEITO-SINTAXE
- Arquivo: `D:\video-fila\vigia_desktop.py`
- Mudou: só avisa se ficou mais de 1 h fora sem voltar; avisa "voltou" só se avisou a queda.

### 2. Comentários no bot de comentários — FEITO-SINTAXE
- Arquivo: `D:\postador-de-videos\bin\notificar_telegram.py` (enviar(coment=True), `_responder_bot`)
- Risco: outra sessão também edita este arquivo; reler do disco antes de mexer.

### 3. Filtro dos comentários da conta pessoal — FEITO-TESTADO (lógica)
- Arquivos: `D:\postador-de-videos\config\comentarios_proprios.json`, `notificar_telegram.py`, `D:\postador-de-videos\bin\sem_token.py`
- Mudou: @Fabricadeautomacoesia (17 de 17 comentários dela eram do telão) não vira aviso nem auto-resposta.
- Em aberto: `@ciano001ofc` (11 comentários) — perguntar à dona se é conta dela.

### 4. Contas "deslogadas" — PARCIAL
- Arquivos: `D:\projeto-navegador-sem-navegador\tools\manter_cookies.py`, `tools\saude.py`
- Mudou: saude.py não avisa CAIU/VOLTOU a cada checagem; só conta morta há mais de 24 h, uma vez, no resumo. manter_cookies tenta recopiar o cookie do Chrome do cofre.
- Achado: 13 de 30 canais YouTube "mortos" são só a cópia de cookie vencida; os vídeos saem normalmente.
- Não provado: o teste em `animescomia` falhou (sem SAPISID; pasta do cofre ocupada). Um aviso de teste pode ter saído em pendências humanas ~23:20 e pode ser falso. Flow: 68 de 215 mortos nas máquinas, não mexi.

### 5. Ritmo de postagem / rampa de canais mudos — FEITO-TESTADO
- Arquivo: `avisos.py`. Motivo: dona só quer limite do próprio YouTube.

### 6. Longos em destaque — FEITO-SINTAXE
- Arquivo: `notificar_telegram.py` (constante LONGOS: completo/longo/compilado)
- Mudou: lista de postagens com bloco "VÍDEOS LONGOS" no topo; aviso "no ar longo" com som. Título do longo vem do YouTube quando a pasta já foi limpa (antes saía "video.mp4").

### 7. Bot do Opus com Argon e Sonnet web — FEITO via rota (item 1).

### 10. Painel de mais vistos — PARCIAL
- Arquivos: `D:\video-fila\vitrine_painel.py` (corte 30 → 300), `D:\video-fila\videos_canais.py` (MAX_POR_CANAL).
- Resultado: 161 vídeos com 1.000+ views na lista (antes 30).
- Falta: `vitrine\painel.html` ainda usa `m.slice(0, 5)` (confirmar se a página rotativa entrou); conferência soma-dos-vídeos x total do canal; 11 canais Noturnos fora da tabela do painel :8790; coleta dos `inovare_*` parou em 12–13/10 (causa desconhecida).

### 11. Aprendizado — FEITO-SINTAXE
- Arquivo: `D:\video-fila\aprendizado.py`
- Mudou: o que vai ao Telegram (nota >= 7, até 5/dia) é aprovado sozinho e a mensagem diz qual IA achou; responder NÃO reprova.
- IA usada: Claude Sonnet 4.5 via Kiro (só se o Kiro estiver liberado) com reserva Gemini 3.8 Flash (Antigravity); mais o Gemini direto (gemini-3.1-flash-lite).
- IA do vigia (`D:\hipercool-videos\bin\vigia_geral.py`): Gemini 3 Flash (Antigravity), reserva Gemini 3.8 Flash.

### 13. Aviso de vídeo duplicado no bot do Studio — DIAGNOSTICO
- O aviso NÃO repete: `avisos_studio_duplicados.json` está gravando (35 ids). São vídeos diferentes.
- Causa provável: 37 fontes usadas 2+ vezes em 7 dias em canais/línguas diferentes (ex.: `vw5vR0ca0ck` em thai, hindi e russo no mesmo dia). `parceiro_diario.py` só barra a mesma fonte dentro da mesma língua.
- Sem explicação: `TALF2NyIfzk` e `uX7RoxrvbeU` não estão no ledger; `lYIp7r5XY48` (CenaReact) sem mesma obra em outro canal.
- Decisão pendente da dona: barrar a mesma fonte em qualquer língua, ou aceitar e só registrar sem avisar.

## Alertas para o revisor
- `politica.garantir_1080` precisa continuar existindo (outra sessão já restaurou a trava de 1080p uma vez).
- Nenhuma das mudanças foi observada num dia real de produção; tarefas agendadas só recarregam o código na próxima execução.

## Correções novas (a partir de agora)
(nenhuma ainda)

## Atualização (31/10, fim da sessão)
- Item 10: telão agora pagina os "mais vistos" de 5 em 5 (vitrine/painel.html ~linha 212); lista backend subiu de 30 para 161 (vitrine_painel.py ~linha 280); MAX_POR_CANAL em videos_canais.py ajustado. Falta: conferir soma de views com o total do canal (channels.list) e os 11 canais Noturnos fora da tabela do painel :8790.
- Item 11: aprendizado.py aprova sozinho o que manda ao Telegram e mostra o nome da IA; resposta NÃO reprova.
- Item 13: só diagnóstico. Aviso não repete (35 ids em avisos_studio_duplicados.json). Causa provável: mesma fonte usada em canais/línguas diferentes (37 fontes em 7 dias); parceiro_diario.py só barra repetição dentro do mesmo idioma. Nenhum código mudado. Decisão da dona pendente.
- Item 4 (contas): manter_cookies.py relogar() escrito, teste em animescomia falhou (cofre sem sessão / pasta ocupada); 1 aviso de teste pode ter saído falso em pendências humanas. Flow 68/215 mortos nas máquinas: não mexido.
- Itens 8, 9, 12: NÃO feitos. 8 chegou cortado na mensagem da dona. 9 exige ler logs de longos (Kaggle) e criar previsão/tempo. 12 é só um prompt (abaixo no chat).
- Avisos ao revisor: outra sessão também edita notificar_telegram.py; politica.garantir_1080 tem de continuar existindo; nada foi testado num dia real de produção, só sintaxe e montagem de mensagem.

## Correção 13 (aplicada 31/10, FEITO-SINTAXE)
- Arquivo: D:\postador-de-videos\bin\avisos_studio.py (linhas ~116-120 e ~220)
- Mudou: _avisar(texto, chave, importante=True) agora aceita importante; o aviso "Short(s) parecido(s)" (duplicado) passa importante=False e vai só para o resumo 9h/14h/21h. Bloqueios e causa de bloqueio seguem na hora.
- Por quê: dona recebia muito aviso de duplicado; o aviso não repetia (35 ids gravados), eram vídeos diferentes. Decisão assumida sem resposta da dona: NÃO barrar fonte reaproveitada entre línguas (isso é decisão de produção, parceiro_diario.py só barra dentro da mesma língua).
- Conferir: python -m py_compile avisos_studio.py; depois de um dia, python D:\video-fila\avisos.py deve mostrar origem "studio" duplicado como "resumo", não "enviado".
- Não provado: rodada real. Se a dona quiser barrar a mesma fonte em qualquer língua, alterar parceiro_diario.py (FONTES_POSTADAS).

## 2026-10-31 — avisos.py: prioridade() respeita em_uso
- **Arquivo:** D:\video-fila\avisos.py (função prioridade, ~linha 287)
- **Motivo:** prioridade() mandava para todos os bots de telegram_bots.json sem olhar "em_uso". O integracao_produto (em_uso: false) recebia o aviso "PRIORIDADE" do vigia mútuo (vitrine\vigia_mutuo.py:76) mesmo desligado. Bots sem o campo em_uso continuam recebendo (padrão True).
- **Como conferir:** python -c "import sys; sys.path.insert(0, r'D:\video-fila'); import avisos" deve passar sem erro; o próximo aviso de prioridade não deve chegar no @int_produto_emerson_bot, só nos bots com em_uso true.
- **Pendente (não feito):** achar o remetente das demais mensagens do bot, classificar lead/teste/ruído e rotear leads reais por avisos.enviar com chave única. Falta o conteúdo do chat e a varredura do n8n (VPS 209 e 157). Token do integracao_produto aparece solto em D:\opus-gratis-v2-desktop\ultimo_pedido.json: remover essa cópia e revogar no BotFather se vazou.
## Correções de 01/11 (depois de medir a primeira noite com as mudanças)

Medição 01/11 00h–07h (`estado/avisos.jsonl`): bot geral recebeu 1 aviso (antes ~75/dia). Pendências humanas recebeu 7, dos quais 5 eram falsos (abaixo).

### C1. Aviso falso de "canal deslogado" — FEITO-TESTADO (lógica)
- Arquivo: `D:\projeto-navegador-sem-navegador\tools\manter_cookies.py` (nova `_postou(slug, horas)`, LEDGER, MAPA; `timedelta` importado)
- Problema: meu `relogar()` de 31/10 mandou 5 avisos "deslogado" de madrugada (animescomia, cenareact, esportenoturno, filmenoturno, inovaremanhwabr, inovareu8b, inventoreact). Todos postaram nas últimas horas: quem posta são os notebooks/PC2, logados; só o Chrome do cofre do PC1 está sem login.
- Mudou: só avisa se o cofre está sem login em 2 rodadas E o canal não postou em 48 h (ledger, casando nome/credencial do youtube_navegador.json).
- Conferido: `_postou` = True nos 7 canais reais, False num slug inexistente.
- Risco: se o ledger parar de ser gravado, `_postou` dá False e volta a avisar (falha para o lado de avisar, o que é aceitável).

### C2. "Contas que voltaram" e linhas duplicadas — FEITO-SINTAXE
- Arquivo: `D:\postador-de-videos\bin\notificar_telegram.py` (`checar_logs`)
- Mudou: linhas repetidas removidas (parceiro_postar.log e parceiro_postar_auto.log davam a mesma conta 2×, ex.: "InventoReact / InventoReact"); "voltaram a postar" vai só para o resumo (dona: "se voltarem não precisa notificar").

### C3. Aviso que diz "não precisa fazer nada" — FEITO-TESTADO (regex)
- Arquivo: `D:\video-fila\avisos.py` (`NADA_A_FAZER`, bloco depois de `simplificar`)
- Mudou: se a reescrita do aviso concluir "O que fazer: não precisa fazer nada", ele vai para o resumo em vez de tocar o celular.
- Conferido: casa "O que fazer: não precisa fazer nada."; não casa "O que fazer: abrir o Studio".
- Origem nova `instagram auto` (conta Instagram suspensa) roteada para pendências humanas (antes caía no bot geral).

### C4. Item 9 — ficha do vídeo longo — FEITO-TESTADO (texto montado com dados reais, não enviado)
- Arquivo novo: `D:\video-fila\linhas\LONGOS\ficha_longo.py`. Sem IA, só arquivos existentes:
  - tempo: 1ª data do `pipeline.log` (UTC do Kaggle) até `render.json["fim"]`; em produção, previsão pela média dos últimos 8;
  - onde: `colab\longos_postados.json` (canal + link) ou o próximo canal da lista do `postar_longos.py`;
  - atualizações: `melhorador_estado.json["mudancas"]` até 4 dias antes do início = entraram; depois do início + `propostas` não aplicadas = próximo vídeo.
- Ligado em: `conferir_pedidos.py` (aviso "longo pronto", origem `longo` → bot de produção) e `colab\postar_longos.py` (depois de postar, "VÍDEO LONGO AGENDADO", origem `no ar longo` → bot de postagem). Os dois em try/except: aviso nunca derruba a postagem.
- `longo` entrou em SEM_SIMPLIFICAR (horas e links não podem ser reescritos).
- Teste: `python ficha_longo.py LAeiXj2Qmlg` → levou 5 h 00 min, 1 h 34 min de vídeo, postado em Assist-IA Investimentos com link, 1 atualização que entrou, 6 para o próximo.
- Não provado: um longo real passando por conferir_pedidos/postar_longos depois da mudança. Shorts seguem nos avisos de produção como antes (não há ficha de Short).
- Limite: "entrou neste vídeo" é por data da mudança x início do render; não confere se o pacote do Kaggle já tinha o arquivo novo.

### C5. Item 10 — views do painel x total do canal — FEITO-TESTADO
- Arquivo: `D:\video-fila\videos_canais.py` (MAX_POR_CANAL 300→1000; `conferencia` gravada em `estado\videos_canais.json`)
- Resultado real 01/11 09:49: 30 canais, lista de vídeos completa em todos (diferença de 0–5 vídeos = privados/agendados). A soma das views dos vídeos fica 0–15% ACIMA do total do canal em todos (o total do canal no YouTube atualiza com atraso; Mistérios Noturnos, canal novo, 24.432 x 9.087). Nenhum canal com soma abaixo do total = nenhum vídeo faltando.
- Conclusão para a dona: os vídeos de 1,4–1,8 mil não faltavam nos dados; sumiam pelo corte em 30 (`vitrine_painel.py`) e pelo telão mostrando só 5 (`vitrine\painel.html`, agora pagina). Para previsão, a soma por vídeo é o número mais atual.
- Regra `bate` = soma >= total − 5%.
- Não feito: os 11 canais Noturnos fora da tabela `api_canais_views` do painel :8790 (ela lê `painel\historico.jsonl`); a coleta dos `inovare_*` nesse histórico parou em 12–13/10 — causa não investigada.

### C6. Tabela de canais do painel :8790 com os 30 canais — FEITO-TESTADO
- Arquivos: `D:\video-fila\videos_canais.py` (grava `estado\canais_views_hist.jsonl`: 1 linha por canal por coleta com inscritos/views/vídeos de channels.statistics, mesma chamada da conferência, sem cota extra); `D:\video-fila\painel_controlador.py` (`api_canais_views`).
- Problema: a tabela lia só `D:\postador-de-videos\painel\historico.jsonl` (painel_canais.py), que tem 12 canais; os 11 Noturnos não apareciam e os 7 `inovare_*` estavam parados em 12–13/10 (3.461 views no ru de verdade x 584 na tabela).
- Mudou: canal ausente no histórico antigo vem do novo; canal cujo histórico antigo está parado há mais de 3 dias usa o novo.
- Conferido 01/11 11:25 (função isolada, sem subir o painel): 30 canais, todos com data de hoje; inovare_ru 3.465 views (bate com o total do canal).
- Não provado: a tela do painel com o servidor rodando (precisa reiniciar o processo do painel :8790 para carregar o código). O "ganho no período" dos canais novos só fica certo depois de alguns dias de histórico novo (hoje começa em 01/11).
- Não investigado: por que o painel_canais.py parou de gravar os inovare_* em 12–13/10.

## Respostas da dona 01/11 e correções que vieram delas

- @ciano001ofc NÃO é conta dela: comentários dele continuam chegando (nada a mudar).
- Item 8 era "dividir mais as mensagens em outros bots que ela cria" — ver C8.

### C7. Vídeo único: a mesma fonte nunca em 2 canais nossos — FEITO-TESTADO (dados reais, sem postar)
- Pedido: "cada vídeo é pra ser único; não pode ser o mesmo vídeo indo pra mais de um canal nosso".
- Causa dos avisos "Short parecido" do bot do Studio: o parceiro_diario fazia o Short pt + até 3 versões traduzidas da mesma fonte (linguas_por_fonte=3) e só barrava repetição dentro da mesma língua; mais os virais refeitos para canais fracos.
- Arquivos:
  - `D:\recapd-ambientes\producao\bin\parceiro_diario.py`
    - postar: fonte já postada em outro canal de QUALQUER língua = SEGURADO (antes: só a mesma língua). Exceção dos virais removida.
    - postar: a versão pt espera se a mesma fonte tem versão de língua pronta/esperando.
    - `_linguas_para`: no máximo 1 língua por fonte e só uma língua com fila 0 (nunca sem postagem; as línguas também têm o hipercool).
  - `D:\recapd-ambientes\producao\config\parceiro.json`: `virais_fracos.modo` ligado → desligado (com nota).
- Conferido: sintaxe ok; `postar --ensaio` roda sem erro (lento, um canal por vez); nos dados de 01/11 12:40, de 145 vídeos prontos, 8 são segurados pela regra nova (7 antes passariam, ex.: larissa-manoela_..._hi, já postado no Bicho Noturno); 5 versões pt esperam a da língua.
- Risco / não provado: (1) vídeos de língua já produzidos ficam "reprovado (segurado)" e o render deles é perdido; (2) se uma língua ficar com fila zerada E o parceiro for a única fonte dela, a versão de língua tem a preferência e a pt da mesma fonte não sobe — é a troca correta pela regra, mas o canal pt pega o próximo vídeo; (3) o hipercool não passa por essa checagem (ele usa capítulos próprios por língua, não fonte de parceiro).
- Memória: `feedback_video_unico_por_canal.md`.

### C8. Item 8 — dividir as mensagens em mais bots — FEITO-TESTADO (rota simulada; depende da dona criar os bots)
- Medido 29/10–01/11 (3 dias, enviado+resumo): postagem 388 (272 "no ar"), producao 292 (83 melhorador central, 72 hipercool), opus 261 (187 argon), pendencias_humanas 242 (103 banimento, 57 nsn).
- Arquivo: `D:\video-fila\avisos.py` — `ROTA_NOVA` + `_rota(origem)`; `_bot`, `_mandar` e `despachar_resumo` usam `_rota`.
- Regra: a origem vai para o bot novo SÓ quando a chave existe em `D:\postador-de-videos\config\telegram_bots.json` com `bot_token` e `chat_id` (e `em_uso` diferente de "False"). Sem isso, segue na ROTA de sempre — nada muda até a dona criar.
- Bots planejados (chave → o que sai do bot atual):
  - `no_ar` ← "no ar", "no ar longo" (tira 272 de 388 do bot de postagem)
  - `melhorador` ← melhorador central, vigia de melhorias, engenharia_reversa, supervisor_melhorador, painel ia (do bot de produção)
  - `longos` ← longo, recap-longo (do bot de produção)
  - `modelos` ← argon, argon-monitor, sonnet-monitor, sonnet-web, troca-modelo (o bot do Opus fica só com o Opus)
  - `contas` ← banimento, nsn, instagram login/auto, telao, checar_canais (pendências humanas fica com o que é ação dela: limite do YouTube, Kaggle, trechos)
- Conferido: hoje `_rota` devolve as rotas antigas; com uma chave `no_ar` simulada numa cópia do arquivo, "no ar" e "no ar longo" vão para `no_ar` e o resto não muda.
- Para ligar cada bot: criar no @BotFather, mandar /start para ele, e adicionar no telegram_bots.json: `"no_ar": {"bot_token": "...", "nome": "@...", "chat_id": "7911666809", "em_uso": "True"}`. Se ela não apertar Iniciar, o `_mandar` detecta "chat not found" e cai no bot de sempre (_SEM_CHAT).
- Não provado: envio real por um bot novo (não existe ainda).

### C9. Melhorias extras medidas na manhã de 01/11 — FEITO-TESTADO (regex e lógica)
- **Longos em rajada:** de 08h às 14h chegaram 9 fichas "VÍDEO LONGO PRONTO" na hora (conferir_pedidos.py --novos varreu fichas antigas). Agora MAX_AVISOS=3 por rodada: os 3 primeiros tocam o celular, os demais vão para o resumo. Arquivo: conferir_pedidos.py.
- **"Voltou ao normal":** o monitor do anime mandou 4 avisos de "voltou" na hora (PC2 voltou, anime voltaram). SO_REGISTRO agora apanha "voltou ao normal/voltaram a ser produzidos/voltou a responder" e manda direto para o registro (sem resumo nem celular). Arquivo: avisos.py.
- **Registro do resumo:** a operação de log `_registro("resumo", ...)` ficava com origem "resumo" → bot geral; trocou para a chave do bot real (postagem, opus, etc.). Não mudou o envio (já ia para o bot certo).
- Conferido: regex casa "voltou ao normal", "voltaram a ser produzidos normalmente", "voltou a responder"; não casa "Falha ao postar".

### C10. Pedido da dona 01/11 tarde: bots existentes + Funcionário de Plantão — FEITO-TESTADO
- "no_ar" e "modelos" NÃO viram bots novos: "no ar" fica no bot de postagem que já existe; argon/sonnet/troca-modelo vão para o bot do Opus que já existe (ROTA_NOVA mudada; chaves no_ar/modelos/melhorador removidas).
- **Bot de postagem** (`notificar_telegram.py`):
  - `avisar_no_ar`: longo = 1 mensagem própria "🎥🎥 VÍDEO LONGO NO AR" (com som, origem "no ar longo"); Shorts = 1 mensagem por canal ("🎬 N Shorts no ar — Canal" com hora e link de cada); 1 Short sozinho = "🎬 Short no ar".
  - `avisar_postagens` (resumo 9/14/21h): blocos separados com marca — 🎥🎥 longos (hora, canal, título, link), 📱 YouTube Shorts (por canal: quantos e as horas), 🎵 TikTok e 📸 Instagram (por conta: quantos e as horas), ☀️ MS Energy.
  - Conferido: montagem com dados reais das últimas 12 h (102 postagens: 5 longos, 55 Shorts, 24 TikTok...), sem enviar.
- **Funcionário de Plantão** (@plantao_emerson_bot, chave `plantao` em telegram_bots.json, criado pela dona):
  - Avisos: melhorador central, vigia de melhorias, engenharia_reversa, supervisor_melhorador, painel ia → plantão (ROTA_NOVA; `_rota` já devolve "plantao").
  - Conversa: `notificar_telegram._responder_plantao` lê o bot (offset `tg_update_id_plantao`) a cada rodada da NotificarTelegram (5 min) e grava na fila do vigia com `bot="plantao"`; `vigia_telegram.py` responde pelo mesmo bot (`_BOT_ATUAL`).
  - Passos ao vivo: `vigia_agente.chamar_agente(progresso=...)` roda o claude em `--output-format stream-json --verbose` e manda os passos ("💬 texto", "🔧 lendo/rodando comando: ...") no máximo 1 mensagem a cada 20 s, juntando os do meio. Só no plantão; o vigia automático e o bot geral seguem no modo antigo.
  - Conferido: getChat ok; mensagem de boas-vindas enviada (ok=true); `_rodar_com_progresso` com um agente falso que imprime stream-json → 3 passos enviados e a resposta final certa.
  - Não provado: uma conversa real com o claude headless pelo plantão (o modelo do agente é o do proxy do vigia; se o Kiro/Sonnet estiver sem cota, vai a reserva Gemini). Demora até 5 min para ler a mensagem (ciclo da NotificarTelegram).
  - Risco: `--verbose` + stream-json depende da versão do claude.exe em `D:\hipercool-videos\tools\claude\`; se o formato não vier JSON, o texto bruto vira a resposta (cai no `textos`).

### C11. Rodada das 15h (01/11) — FEITO-TESTADO
- Medido 14:15–15:00: 20 registros, só 5 tocaram o celular (3 "no ar" agrupados, 1 conta do TikTok deslogada, 1 longo italiano não postado). Ninguém escreveu no plantão ainda.
- `troca-modelo` (troca automática Opus 5.5 ↔ 4.6 do chat) entrou em MUDO: 11 registros em 45 min, nada para a dona. Arquivo: avisos.py (outra sessão já tinha posto produto-ruido/teste/conversa no mesmo MUDO; mantidas).
- Conferido: enviar(..., "troca-modelo") registra "mudo". Um item de teste que caiu no resumo antes da mudança foi tirado da fila.

### C12. PC fora só após 1 h + Shorts só no relatório + formato por canal — FEITO-TESTADO
- **PCs caindo/voltando no bot geral:** vinham do `D:\video-fila\vitrine\vigia_mutuo.py`, que roda no PC1 E nos 2 notebooks (Acer, X200MA). Nos notebooks ele manda direto pela API do bot geral (`~/vitrine/telegram.json`), sem passar pelo portão — por isso não aparecia no avisos.jsonl.
  - Mudou: `AVISO_TELEGRAM_S = 1 h` (antes 6 min; PC2 15 min) — só avisa quem está fora há 1 h sem voltar; o "VOLTOU" só sai se a queda foi avisada (já era assim). Lembrete do PC2 fora: 30 min → 3 h. O telão continua mostrando a máquina fora a partir de 6 min.
  - `vitrine.py instalar()`: o telegram.json dos notebooks agora leva o bot de PENDÊNCIAS HUMANAS (não o geral).
  - Aplicado já: copiado vigia_mutuo.py + telegram.json (bot pendências) nos 2 notebooks por ssh (rc 0) e reiniciado o player.py; conferido PLAYER_ON e o código novo (`AVISO_TELEGRAM_S`) lá.
  - O vigia_desktop.py (desktop) já tinha 1 h desde 31/10 (entrada 1b).
- **Shorts chegando 1 por 1** (dona: "continua chegando individual e não agrupado"): `avisar_no_ar` não manda mais Short na hora — só o longo continua com mensagem própria. Os Shorts entram só no relatório 9/14/21h agrupados por canal.
- **Relatório** (`avisar_postagens`): cada canal mostra quantos e de qual forma ("ManhwaReact-ia: 4 — 2 Veo + 2 Short parceiro — horas"); o bloco de longos aparece sempre ("nenhum neste período" quando não houve). Formatos em `FORMATOS` (tipo+projeto do ledger).
  - Conferido com o dia 01/11 (123 postagens, sem enviar): 5 longos no topo (ForjaReact, ind, thai, viet, AssistIA), 56 Shorts por canal com formato, 25 TikTok.
  - Observação para a dona: os 5 longos de hoje já estavam no resumo das 14h, só que no formato antigo.
- Não provado: o próximo relatório real (21h) e um PC realmente fora por 1 h.
- O plantão recebeu o primeiro "Olá" às 15:14 e foi respondido às 15:15 (saudação, sem chamar o agente).

### C13. Plantão não respondeu o "Oi" — FEITO (prova abaixo)
- Causa: o plantão era lido pela rodada do `notificar_telegram.py` (NotificarTelegram, 5 min). A rodada das 15:14 travou ~40 min esperando um `rclone lsjson -R` do Drive inteiro (`etapas.listar`, timeout 900 s) e a tarefa está em IgnoreNew: nenhuma rodada nova começou, o "Oi" das 15:42 ficou parado no bot. (O "Olá" das 15:14 foi respondido.)
- Ação na hora: matei o rclone travado e a rodada; disparei a NotificarTelegram de novo.
- Correção: `D:\video-fila\plantao.py` (novo) + `plantao.bat` + tarefa **PlantaoTelegram** (a cada 1 min, wscript+rodar_oculto.vbs, IgnoreNew, limite 5 min, mesma conta da VigiaDesktop). Só fala com o Telegram — nada de Drive/YouTube.
  - "oi/olá/ping/tá aí" → responde na hora, sem IA, com o que está desligado agora.
  - "status" → `vigia_telegram.status()` na hora.
  - "liga X" / "desliga X" [produção|postagem] → `controle.py ligar|desligar <projeto> <etapa> "pelo plantão (Telegram)"`; sem etapa = as duas; apelidos manhwa→hipercool, cortes, tudo...; mostra o painel do controle e avisa se outro botão antigo ainda segura.
  - Resto → fila do vigia com bot="plantao" (agente responde e vai contando os passos — C10).
  - Offset próprio em `estado\plantao.json` (1ª vez herda `tg_update_id_plantao` do telegram_estado.json, não perde nem repete). Log: `estado\plantao.log`.
- `notificar_telegram.responder` NÃO lê mais o plantão (dois leitores roubam mensagens).
- Conferido: `plantao.py --uma oi` → "Estou aqui, de plantão. Desligado agora: hipercool produção…"; "--uma liga" → pede o projeto; pergunta livre → agente.
- Não provado: "liga/desliga" de verdade pelo Telegram (não rodei para não mexer na produção); o agente respondendo uma pergunta real pelo plantão.
- 15:54: o "Oi" das 15:42 (message_id 5) foi respondido pelo plantão (log "respondi (ok)"). A tarefa com wscript+.bat ficava presa no cmd (python não subia); trocada para `D:\veo\venv\Scripts\pythonw.exe -X utf8 D:\video-fila\plantao.py` direto (pythonw já não abre janela). `enviar` agora registra "respondi (ok/recusado)" no plantao.log.
- Pendente (não mexi): a NotificarTelegram segue podendo travar no rclone do Drive (listar com timeout 900 s) — atrasa comentários/inscritos. Sugestão: timeout menor ou listagem fora dessa rodada.
- 16:00: uma rodada pela tarefa ficou parada (pythonw, CPU 0, sem conexão) segurando a trava → as seguintes não rodavam. `plantao.py` agora tem `socket.setdefaulttimeout(20)` e `_vigia_tempo(50)` (encerra a rodada que passar de 50 s e solta a trava); trava vale 60 s (antes 120). Processos presos encerrados e trava apagada.
