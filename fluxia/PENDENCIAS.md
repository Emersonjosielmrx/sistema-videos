# FluxIA: pendências

Situação em 16/10/2026: versão 2 no ar em https://fluxia.157-173-207-22.sslip.io (VPS 157), atualizada em 16/10 ~10:30.
Versão anterior em `/opt/fluxia/src.prev` (para voltar: `mv src src.bad && mv src.prev src`, `docker build` e `service update`).

Pronto e testado (Hermes simulado + IA real do OmniRoute, 52 verificações; prints de desktop e celular):
editor visual em blocos com o caminho de cada execução aceso; fluxos criados a partir de 4 modelos com todas
as opções editáveis (prompt, regras de áudio/imagem/PDF, horário, pausa, agrupar mensagens, botões, avisos);
botões pelo WhatsApp (enquete); modo administrador pelo seu número (ensinar, simular, reiniciar, desfazer,
ligar/desligar, status, também por áudio); transcrição de áudio; IA lendo imagem/comprovante; comprovantes
guardados e visíveis para a loja; pausa quando a loja responde à mão e quando o cliente pede atendente;
horário de funcionamento; histórico de versões com desfazer; tela da loja no visual do Hermes (horário,
avisos, comprovantes, conversas assumidas, trocar senha); editar cliente e trocar senha; limite de tentativas
de login; login de cliente apagado deixa de valer na hora; apagar fluxo com execuções; aviso aos admins
quando a IA falha; cópia diária do banco.

## 000. Incidente 06-07/11: bot mandou "This version of Antigravity is no longer supported" aos clientes

- [x] Desde 06/11 ~19h o Antigravity do OmniRoute (agy/, antigravity/, gemini-fila e também kr/haiku-fila, que cai
      nele) responde **200 com o aviso de versão** como se fosse a resposta. O FluxIA mandou isso em 11 conversas
      (9 Globo, 2 papelaria) e a transcrição de áudio também virou esse texto.
- [x] 07/11 15:45: modelo de todos os fluxos = `cw/claude-sonnet-5-5`; reservas `cc/claude-haiku-5-5`,
      `gemini/gemini-2.5-flash`, `cc/claude-sonnet-5-5`; imagem e áudio = `gemini/gemini-2.5-flash` (o Sonnet não
      ouve áudio). Env na VPS por `--env-add`. Backup `/data/fluxia-backup-20261107-antes-sonnet.db`.
- [x] Trava: `agent.is_bad_reply` (texto de aviso de erro/limite/chave) = resposta descartada e tenta o próximo
      modelo; vale também para a transcrição. Antes do envio nunca sai aviso de provedor para o cliente.
- [x] Conversa "Meta Business Agent" (1807055946647698, o robô de IA do WhatsApp Business conversando com o nosso, 211
      trocas) com IA desligada de vez.
- [x] 09/11 (dono: "tem que funcionar tudo com Gemini"): modelo = `gemini/gemini-2.5-flash-lite` (AI Studio; texto,
      imagem e áudio em 1-5 s). `gemini-2.5-flash` ficou sem cota (429 billing, o OmniRoute ainda desviava para
      nvidia/gpt-oss) e os 3.x do AI Studio levavam 60-150 s. Reservas no `agent.py`: agy/gemini-3.8-flash-high,
      gemini-2.5-flash, gemini-3.6-flash e por último cw/claude-sonnet-5-5 (só emergência); reserva com prazo de 25 s.
- [x] 09/11 13:46: principal agora `gemini/gemini-3.5-flash-lite` (texto 1,4 s, áudio 3 s, imagem 2,6 s). Os Flash
      completos do AI Studio (3.5, 3.6, 3.7, 3.8) não respondem: o Google dá 502 em cada chave e o OmniRoute fica
      girando entre as 72 conexões até estourar o prazo; os Lite (2.5 e 3.5) respondem. Uma chave isolada estava
      em 429 por minuto (outros robôs usando ao mesmo tempo).
- [x] 09/11 (dono: "às vezes o 3.5 responde lento, tem que ter o 2.5 de reserva"): 1ª reserva =
      `gemini/gemini-2.5-flash-lite`. Prazo por modelo (`FLUXIA_FIRST_TIMEOUT` 15 s, +10 s só no principal com
      imagem; `FLUXIA_FALLBACK_TIMEOUT` 15 s; áudio `FLUXIA_TRANSCRIBE_TIMEOUT` 20 s); lento = passa direto, sem
      repetir. Simulado com o 3.5 Lite travado: resposta do 2.5 Lite em ~17 s (texto) e ~27 s (imagem).
- [x] **Vigia do modelo** (`deploy/vigia_modelo.py`, cron `/etc/cron.d/fluxia-vigia-modelo` a cada 10 min,
      `/opt/fluxia/vigia_modelo.sh`, log `/data/vigia_modelo.log` no volume): testa os Gemini na ordem
      (agy 3.8 → 2.5-lite → 2.5 → 3.6 → 3.5), descarta aviso de erro e põe o 1º que responde em todos os fluxos;
      volta sozinho para o agy/3.8 quando o Antigravity voltar. `--simular` só mostra.
- [ ] **Antigravity fora no OmniRoute inteiro** (não só o FluxIA; o Opus `antigravity/claude-opus-5-5-high` dos chats
      também recebe o aviso desde 08/11). A conta Pro do `agy` (felipeaguiar) está `banned` pelo Google desde 05/11.
      O OmniRoute (imagem `v3.8.51-custom-fix2`, 23/10) declara `antigravity/ide/2.1.1`; o instalador oficial diz
      2.0.6, então não é só o número: precisa atualizar o OmniRoute (serviço central, fazer no chat do OmniRoute).
- [ ] Sem resposta de verdade (loja não atendeu): Globo — Chicao. Produtos E Cesta (105472032039154, 13:39) e
      Jrtech (249984477827200, 14:36). Dono decide se o bot manda resposta.
- [ ] Ideia: ignorar contatos que são robôs (Meta Business Agent) automaticamente.

## 00. Gemini 3.8 em tudo + áudio voltou + fluxo da Globo Solar (01/11)

- [x] **Áudio não funcionava desde ~27/10**: a conta do Groq (Whisper) foi bloqueada ("Organization has been
      restricted", 400 em `/v1/audio/transcriptions`) e todo áudio caía em "não consigo ouvir". Agora `media.transcribe`
      manda o áudio direto ao Gemini (`/v1/chat/completions`, `input_audio`, formato ogg/mp3/aac/wav), modelos em
      `FLUXIA_TRANSCRIBE_MODEL` (padrão `agy/gemini-3.8-flash-high,antigravity/gemini-3.8-flash-tiered`). ~5-9 s.
- [x] Áudio é transcrito ANTES do menu (`engine._transcribe_items`): a resposta falada vale como opção/resposta das
      perguntas do menu de botões, e o que não é opção vai para a IA como "[Áudio do cliente, transcrito]".
- [x] **Todos os modelos = Gemini 3.8** (`agy/gemini-3.8-flash-high` → fila gemini-fila do OmniRoute; reserva
      `antigravity/gemini-3.8-flash-tiered`): texto, imagem, ensinar. Haiku do cc dava 429. Na VPS: `.env` e
      `docker service update --env-add FLUXIA_MODEL=...` (o `update --force` NÃO relê o `.env`); `model` dos fluxos
      1-4 trocado no banco (versão no histórico). Backup: `/data/fluxia-backup-20261101-antes-gemini-globo.db`, `.env.bak_antes_gemini_01nov`.
- [x] Menu com final sem Pix (`menu.done_text`) e texto próprio da opção de informações (`menu.table_text`).
- [x] **Fluxo 5 "Advance Solar (menu)"** (mesmo menu, Castanhal, sem endereço nem "financiamos" porque não está no
      Instagram dela), LIGADO, login `luiz` / senha `luiz`; QR e conversa testados. Falta a loja ler o QR e mandar o endereço.
- [x] **Fluxo 4 "Globo Solar (menu)"** — os dois saem de `deploy/criar_fluxo_solar.py globo|advance --gravar`
      (cria ou atualiza o fluxo e o login): botões Orçamento solar / Financiamento / Empresa ou rural / Limpeza-manutenção / Como funciona /
      Consultor; perguntas nome, cidade, conta de luz (botões), foto da conta, telhado, pagamento → resumo →
      "um consultor vai te chamar" + pausa 120 min. Sem preço nem "% de economia" (a dona não confirmou valores).
      Testado local (conversa completa com resposta por áudio) e na produção (teste do painel).
- [x] Globo: fluxo 4 LIGADO, login da loja `globo` / senha `globo` (pedido do dono; tela de login aceita login sem @).
      QR testado pela URL pública (gera e cria a conexão sozinho). [ ] Falta só a loja abrir /cliente e ler o QR com
      o WhatsApp (91) 99394-9409; depois: `notify_phone` e horário.
- [x] 04/11: **Globo e Advance sem botões**: conversa curta e humana (`PROMPT_CONVERSA` em `deploy/criar_fluxo_solar.py`,
      `menu_enabled=False`; o menu fica guardado em `config.menu`). Pega nome, cidade e conta de luz na conversa e
      passa para o consultor com [ATENDENTE] (pausa 24 h + aviso). Rodar o script de novo preserva avisos, horário,
      regras ensinadas e admins (`PRESERVAR`).
- [x] 04/11: **admins por fluxo** (`config.admin_phones`, aceita número como a loja digita e LID): dono da Globo
      `91 98246-9729` = LID `6451208650994` (achado em `whatsmeow_lid_map` do banco da linha; o Hermes não devolveu
      porque o WhatsApp deu 429 rate-overlimit nas consultas da linha da Globo logo depois da troca de versão).
      Admin geral continua em Configurações. Aviso ao dono agora completa o 55 e tenta com/sem o 9.
      [ ] Conferir o aviso da Globo chegando no 98246-9729 quando o limite passar.
- [x] 04/11 09:21: **resolvido no Hermes v0.21.3** (`20261104-0911_1da58cd`, ramo `hotfix/v0.21.3-whatsmeow-atual`,
      worktree `D:\hermes\wt-whatsmeow-atual`): whatsmeow 30/06 → 02/11/2026. Na troca a Globo recebeu 413 eventos
      presos e a Advance 295, SEM parear de novo. Volta: `ops/reverter.sh` (→ v0.21.2). Falta `ops/marcar-estavel.sh`
      depois de 1-2 dias bom. Lição: linha "conectada" que envia mas não recebe = biblioteca do WhatsApp velha.
- [ ] 03/11: **Globo e Advance pararam de RECEBER** desde 02/11 ~20:15 (Hermes: aviso `client_outdated` 405 em todas
      as linhas; depois do reinício de 21:29 com a versão nova do WhatsApp Web, papelaria e as outras voltaram, mas
      essas duas nunca completaram o `OfflineSyncCompleted` e não gravaram nenhuma mensagem recebida em `wacalls_main.messages`;
      enviar continuava funcionando e o painel mostrava "conectado"). Reiniciar o Hermes de novo (03/11 19:55) não
      resolveu. Desconectei as duas (`/logout`) para parear de novo: **falta a Globo e o Luiz lerem o QR em /cliente**.
      A senha `globo` não entra mais (a loja deve ter trocado; não mexi). Ideia: alerta quando uma linha "conectada"
      fica horas sem receber nada (o FluxIA não percebe isso hoje).
- [x] 02/11: **pausa não valia na conversa com o número admin** (Emerson ↔ Luiz na Advance): o admin é atendido como
      cliente na conversa `sim:<lid>`, mas `_owner_replied` ignorava a resposta do dono quando o contato era admin e o
      filtro de pausa só olhava o modo `live`. Agora a resposta do dono pausa a `sim:` por 24 h e o filtro vale em
      `live` e `sim` (todas as linhas: papelaria, Globo, Advance). Testado local. Backup `/data/fluxia-backup-20261102-antes-pausa-admin.db`.
- [x] **Pausa por interação de 24 h** (dono, 01/11): cada resposta da loja à mão pausa a IA 1440 min naquela conversa
      e renova a cada resposta; `owner_off_two_messages` desligado (padrão e fluxos 3/4). Motivo: com 120 min a IA
      voltava e respondia conversa pessoal do dono (contato 27629558194237, 26/10). Os 13 contatos que estavam
      desligados de vez na papelaria viraram "última resposta da loja + 24 h" (a maioria já voltou para a IA).
      O interruptor manual em Contatos continua desligando de vez. Backup: `/data/fluxia-backup-20261101-antes-pausa24h.db`.

## 0. Cyber no lugar da hamburgueria (16/10 ~23:30)

- [x] Fluxo 2 **"Cyber (impressões e serviços)"** criado com o modelo novo `servicos` ("Serviços com tabela de preços"),
      preços e Pix tirados do bot antigo (`D:\downloads\cyber bot`, Playwright no WhatsApp Web). A conexão 1 (a linha do
      Hermes que era do Castanhal Burger, número 5591985645632 = a mesma chave Pix da cyber) passou para ele. O fluxo 1
      (Castanhal Burger) está **guardado e desligado**, sem conexão. O login da loja (`castanhalburger@fluxia.local`) agora
      vê só a cyber. Backup do banco antes: `/data/fluxia-backup-20261016-antes-cyber.db`.
- [x] Novo tipo para PDF/documento: `file` ("Arquivo do cliente"): guarda, e a IA sabe o nome e quantas páginas tem
      (`pageCount` do WhatsApp ou contagem no PDF, `media.pdf_pages`) para orçar impressão. Testado local e na produção (modo teste).
- [ ] **A linha está desconectada** desde 16/10 ~18h (o dono desconectou ou caiu): o dono precisa entrar em `/cliente` e
      conectar pelo **QR code** (o código dá `bad-request` nesse número).
- [x] Nome da loja: **Jhonatas Papelaria** (fluxo, conexão e login da loja renomeados em 16/10).
- [ ] Faltam na config da papelaria: endereço e horário. Dá para ensinar pelo WhatsApp no modo admin.
- [x] 17/10: fluxo 3 **"Jhonatas Papelaria (menu)"** (modelo `servicos_menu`, `backend/menu_flow.py`) é o ATIVO na
      conexão 1; fluxos 1 e 2 guardados e desligados. Funciona como o bot antigo/imagem do usuário: menu → submenu →
      perguntas do serviço uma a uma (texto, enquete ou arquivo) → resumo + enquete Confirmar/Corrigir/Cancelar → Pix e
      atendente (pausa 120 min). A IA (`PROMPT_MENU`) só responde o que não é opção nem resposta (dúvida no meio do
      formulário volta para a pergunta pendente). O menu fica em `config.menu` (vazio = `PAPELARIA_MENU` no código).
      Testado local (conversa de contrato e impressão com PDF) e na produção em modo teste. Backup: `/data/fluxia-backup-20261017-antes-menu.db`.
- [x] 18/10: **botões e lista clicáveis de verdade** (no lugar da enquete), copiados do AstraCalls para o Hermes.
      FluxIA publicado em 18/10 ~18h: bloco Botões → "Como as opções aparecem" (`button_style`: `enquete` | `botoes`,
      padrão enquete). Com `botoes`: até 3 opções de até 20 letras = botões; até 10 = lista "Ver opções"; mais que
      isso ou Hermes recusando = enquete (404 = Hermes antigo, sem aviso; outro erro vira evento `envio`). O id de
      cada opção é o próprio texto; o toque volta no webhook `message` com `buttonReply.messageId` e entra pelo mesmo
      caminho do voto (`webhook._choice`, tabela `polls`). e2e 61/61. Backup: `/data/fluxia-backup-20261018-antes-botoes.db`.
- [x] **Hermes v0.15.0** no ar desde 19/10 10:19 (`20261019-1010_19d42b8`): `/messages/buttons|list|interactive`.
- [x] 19/10 12:50: teste de botões e lista mandado da linha da papelaria ao admin: **aparecem** (dono confirmou) e o
      toque chegou ao FluxIA. Atenção: o WhatsApp do admin é 559184698653 (sem o 9); envio por número com 9 dá 200 e
      não chega (o bot não sofre disso: responde ao `chat` do webhook).
- [x] 19/10 ~13:15: **fluxo 3 em botões de verdade** (`button_style = botoes`, versão "botões de verdade no lugar da
      enquete" no histórico; prompt sem "enquete"). Menus = lista "Ver opções"; perguntas de entrega e o resumo
      (Confirmar/Corrigir/Cancelar) = botões. Rótulos de entrega encurtados para ≤20 letras ("🛵 Entrega motoboy",
      "📲 PDF no WhatsApp", "🏪 Buscar na loja"), taxa no texto da pergunta. Modelo `servicos_menu` já nasce com botões.
      e2e 68/68 (seção 11 = menu completo com botões). Backup: `/data/fluxia-backup-20261019-antes-botoes-fluxo3.db`.
      Voltar: bloco Botões → Enquete (ou desfazer a versão).
- [ ] **19/10 13:03: o menu em LISTA não apareceu** no celular do dono (mandou "oi", recebeu só as boas-vindas; o Hermes
      aceitou a lista `3EB05ED084…` para `132250784018630@lid`). Da lista de teste das 12:50 também nunca chegou toque;
      os botões aparecem. Teste 13:06 no LID: tocou em "B aparece" (botões) e não na lista curta (A) → **a lista
      nativa (single_select) não aparece nesse WhatsApp, nem com nomes curtos**; os botões aparecem (PN e LID).
- [x] 19/10 ~13:40: FluxIA sem lista. `button_style = botoes` = só botões, em blocos de 3 ("Mais opções 👇" nos
      seguintes; cada bloco registrado em `polls`); opção com mais de 20 letras → enquete. Rótulos do menu da
      papelaria e dos botões dos modelos encurtados para ≤20 (ex.: "🖨️ Impressão/cópia", "🙋 Atendente"). e2e 68/68.
      Fluxo 3 de volta em `botoes`. Backup: `/data/fluxia-backup-20261019-antes-blocos-botoes.db`.
- [ ] Conferir o menu em blocos no celular do dono e depois numa conversa real de cliente. Depois: mandar teste para o número do admin, conferir que aparece no
      celular (Android, iPhone, Web) e que o toque chega; só então `button_style = botoes` no fluxo 3.
- [ ] Editor visual do menu (hoje só liga/desliga no bloco Botões; opções e perguntas mudam no código ou no JSON `config.menu`).
- [ ] Ensinar pelo WhatsApp ainda não mexe no menu (só preços/infos via `business_info`, que aparecem na "Tabela de preços").
- [ ] Para voltar a hamburgueria: no banco, `UPDATE flows SET connection_id=1, active=1 WHERE id=1` e `connection_id=NULL, active=0` no 2.

## 1. Depende de você (bloqueia o uso real)

- [x] **Chave de API do Hermes** (15/10): criada a conta própria `fluxia@inovareinteligenciaartificial.com` no Hermes
      (plano enterprise, sem senha de login, Agente de IA desligado) com a chave "FluxIA", já salva nas Configurações do
      FluxIA. As linhas de WhatsApp das lojas ficam nessa conta. Para entrar no painel do Hermes com ela, use "esqueci a senha".
      Se ligar o Agente de IA nessa conta, os clientes recebem resposta dupla.
- [ ] Mandar para a loja o endereço, o email (`castanhalburger@fluxia.local`) e a senha.
- [ ] Domínio próprio (opcional): criar `fluxia.inovareinteligenciaartificial.com` → 157.173.207.22 (o curinga
      aponta para a 209), trocar o `Host(...)` no `fluxia-stack.yml` e o `FLUXIA_PUBLIC_URL` no `.env`, e
      registrar de novo o webhook das conexões existentes.

## 2. Só dá para conferir com WhatsApp de verdade

- [ ] Código de pareamento real e a primeira mensagem chegando pelo webhook. Em 15/10 o código falhou para a loja
      (motivo não registrado na época). Agora: o motivo vai para o log `[FLUXIA-ERRO]`, para a tabela `events`
      (painel → Visão geral → Eventos recentes) e aparece na tela da loja. O Hermes sempre coloca o 9 em celular
      de 12 dígitos; se o WhatsApp do número estiver cadastrado sem o 9 (comum no DDD 91) o código dá `bad-request`
      e a loja deve usar **Conectar com QR code** (tela aberta no computador). Correção de verdade seria no Hermes
      (`normalizePhone` em `handleSessionPairCode`), não mexido.
- [ ] O Hermes apaga linhas ainda não pareadas quando reinicia; o FluxIA recria a linha sozinho ao parear (evento `AVISO`).
- [x] 15/10 ~19:36: Castanhal conectado pelo **QR code**. Confirmado: o WhatsApp da loja está cadastrado **sem o 9**
      (559185...), por isso o código dava `bad-request`.
- [x] 15/10: a IA (Haiku pelo OmniRoute) devolveu 429 duas vezes e a cliente recebeu "problema técnico". Agora tenta de
      novo e cai para `cc/claude-sonnet-5-5` e depois `gemini/gemini-2.5-flash` (`FLUXIA_FALLBACK_MODELS`).
- [x] 15/10: respostas curtas (`reply_length`, padrão "curta") e IA desligável por contato (pausa sem prazo
      `9999-12-31`): interruptor em Contatos (tela da loja) e em Conversas (admin), e automático quando a loja manda
      2 mensagens para o mesmo contato com menos de 1 min (`owner_off_two_messages`). 1 mensagem só = pausa de 60 min.
- [ ] Castanhal sem horário e sem informação de entrega na config: a IA responde "vou verificar com a loja".
- [x] 16/10 "não responde todas as mensagens": conferido mensagem a mensagem (Hermes × execuções do FluxIA, script
      `D:\temp\fluxia_diag\diag3.py`): **nenhuma mensagem se perdeu**. Só o contato Neto Silva ficou sem resposta, e por
      regra: o celular da loja escreveu para ele à mão ("Manda msg ai praga", 15/10 20:18) → IA pausada 60 min; depois a
      loja mandou áudio + foto em 6 s → `owner_off_two_messages` desligou a IA para ele de vez. O dono concluiu errado que
      "o bot não responde conta comercial". IA do Neto religada em 16/10 ~10:15. Para testar, a loja **não pode escrever à
      mão para o contato de teste**. Diagnóstico rápido: tabela `executions` com `status='skip'` mostra o motivo na etapa `filter`.
- [x] 16/10 ~10:30 publicado (pedido de 15/10): modo admin não manda mais "⏳ Entendi, ajustando..." nem o eco do
      áudio transcrito; **tempo de resposta** (`metadata.response_ms`, da última mensagem do cliente até a resposta sair,
      inclui o `buffer_seconds`) aparece em Execuções e > 30 s vira evento `lento` (`SLOW_REPLY_MS` em `engine.py`);
      **histórico anterior**: na 1ª mensagem de um contato ao FluxIA, `engine.previous_history` busca no Hermes
      (`GET /api/sessions/{sid}/chats/{chat}/messages`, devolve lista da mais nova para a mais antiga, campos `body`,
      `fromMe`, `timestamp` em ms) as últimas 20 e usa só as **anteriores à criação da conexão** (`whatsapp_connections.created_at`),
      para não trazer de volta respostas do próprio bot depois de um "reiniciar". Cliente = `user`, loja =
      `assistant` com "[Resposta da equipe da loja]:". Etapa "Conversa anterior no WhatsApp: N mensagens" em Mensagem recebida.
      Testado no e2e (4 verificações novas) e conferido com os dados reais do Hermes (quase todos os chats da loja têm
      histórico de antes). [ ] Falta ver numa conversa real nova.
- [x] O Hermes não devolve o LID do número do admin; o LID fica em Configurações (`admin_lids`). Para descobrir o LID
      de um número: tabela `whatsmeow_lid_map` do banco da linha (`wacalls_<sessão>`) no Postgres da produção do Hermes.
- [ ] **Mídia real**: baixar e decifrar áudio/imagem/PDF de `mmg.whatsapp.net`. O esquema foi conferido com o
      código do whatsmeow e testado com arquivo cifrado do mesmo jeito, mas não com uma mensagem real. Se falhar,
      o áudio cai na resposta fixa ("pode escrever?") e a imagem vira "possível comprovante" sem ser vista.
- [ ] Voto na enquete chegando como `poll_vote` (o Hermes decifra o voto; formato conferido no código).
- [ ] Seu número no formato novo (LID): o FluxIA pergunta ao Hermes o LID do seu número; conferido só com Hermes simulado.
- [ ] Mensagem que o próprio FluxIA envia não pode voltar como "loja respondeu" (os IDs enviados são ignorados; conferido só no simulado).
- [ ] Números do Pará sem o 9º dígito: o modo admin aceita as duas formas; o pareamento depende do Hermes.

## 3. Produto (ideias e melhorias)

- [x] 17/10: modo admin agora só com a palavra *admin* e cai sozinho após 15 min parado (`ADMIN_IDLE_MINUTES`);
      fora disso o número do admin é atendido como cliente (simulação, conversa `sim:`). *sair* volta a cliente.
      Motivo: às 06:38 o usuário escreveu "Botão só está funcionando na Api oficial" e o modo admin respondeu como
      "ensinar", parecendo que o fluxo estava errado (linha e fluxo 3 estavam certos).
- [x] (antigo) **Modo admin intercepta conversa pessoal**: tudo que o número do admin (5591984698653 / LID 132250784018630) manda
      para o WhatsApp da loja vira comando/ensino. Em 16/10 09:18 o usuário escreveu "E pra responder" para o dono e o bot
      respondeu "Não entendi bem o que você quer mudar..." no WhatsApp da loja. Ideia (não feita, decidir com o usuário):
      só entrar no modo admin com uma palavra (ex. *admin*/*menu*) e sair sozinho depois de alguns minutos parado.

- [ ] Comprovante em PDF: hoje é guardado e agradecido, mas a IA não lê o conteúdo do PDF.
- [ ] Avisos para o dono saem do próprio número da loja (para o `notify_phone`); se a loja quiser receber num grupo, falta.
- [ ] Mais de um fluxo no mesmo número (hoje cada número atende um fluxo).
- [ ] Instagram e Telegram.
- [ ] Mais de um admin: cada admin já só vê os próprios fluxos, mas clientes e configurações são globais.

## 4. Infraestrutura

- [ ] O backup semanal das VPS (roda na produção, `backup-vps.sh`) leva o volume `fluxia_fluxia_data` para o Drive aos
      domingos, com as 7 cópias diárias que o FluxIA faz em `/data/backups`. Não foi feito restore de teste.
      Em 14/10 esse backup teve falha num banco da VPS de teste (209), sem relação com o FluxIA.
- [ ] Cópia do código antigo em `/opt/fluxia/src.v1` e do banco antes da v2 em `/data/fluxia-backup-20261015-v1.db`: podem ser apagadas depois que a v2 rodar com clientes.

## 5. Como atualizar a versão na VPS

```bash
# do PC, na pasta D:\fluxia (envia para uma pasta limpa: sobras de versões antigas podem quebrar a build)
ssh hermes-bloqueio 'cd /opt/fluxia && rm -rf src.new && mkdir src.new'
tar -czf - --exclude=frontend/node_modules --exclude=frontend/dist --exclude=__pycache__ --exclude=tsconfig.tsbuildinfo \
  backend frontend Dockerfile .dockerignore deploy | ssh hermes-bloqueio 'tar -xzf - -C /opt/fluxia/src.new'
ssh hermes-bloqueio 'cd /opt/fluxia && docker build -t fluxia:latest src.new && rm -rf src.prev && mv src src.prev && mv src.new src && docker service update --force fluxia_fluxia'
```

A senha do admin fica só na VPS, em `/opt/fluxia/.env` (`FLUXIA_ADMIN_PASSWORD`).
