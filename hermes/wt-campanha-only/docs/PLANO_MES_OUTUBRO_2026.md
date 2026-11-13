# Plano do mês: 04/10 a 03/11/2026

> Pedido da dona (04/10): "analise todo o projeto e faça um planejamento extenso pra trabalhar o próximo mês
> todo, 24 h, melhorando o projeto como um todo, priorizando as coisas mais importantes."
>
> **Todo agente (na nuvem ou no PC) segue esta lista.** Antes de começar: `CONTINUAR_DAQUI.md`, este arquivo e,
> se for mexer na voz, `docs/REGRESSOES_LIGACAO.md`. Ao terminar um item, marque `[x]`, anote a data e o commit,
> e registre no fim deste arquivo (seção 9).

---

## 1. Retrato do projeto em 04/10 (conferido, não copiado)

| O quê | Situação |
|---|---|
| Produção | v0.7.0, build `20261003-2306_af7413e` (systemd na VPS 241), 2 linhas conectadas |
| Código Go | 72 mil linhas; **64 mil num pacote só** (`cmd/server`, 276 arquivos). Maiores: `telegram.go` 3.187, `broadcast.go` 2.682, `voiceagent.go` 2.552, `aiagent.go` 2.284 |
| Testes Go | `go build`, `go vet` e `go test ./...` **passam** (CGO desligado, como no CI). 76 arquivos de teste. **11 pacotes com 0 testes**, entre eles cobrança (`internal/billing`), configurações (`internal/settings`) e campanhas (`internal/whatsapp_campaigns`, 928 linhas) |
| Painel | `vite build` passa. **205 erros de tipo** no TypeScript (o CI não bloqueia). Sem ESLint. 5 assistentes de configuração diferentes (o maior, `EasyAgentWizard.tsx`, com 2.523 linhas) |
| Configuração | **99 variáveis de ambiente** diferentes (`HERMES_*`/`WACALLS_*`), sem lista única |
| Biblioteca do WhatsApp | `whatsmeow` de 30/06/2026 (3 meses sem atualizar) |
| GitHub | **`Emersonjosielmrx/hermes-call` é PÚBLICO.** O próprio CHANGELOG diz que o histórico do git ainda contém senhas e tokens antigos |
| Ligação (medido em 03/10) | Resposta em 2,4 a 4,3 s (média ~3,0 s; meta 2,5 s) = fim de fala 0,84 s + transcrição 0,2–0,75 s + IA 0,73–0,91 s + voz 0,38–1,84 s |
| Pendências abertas | interromper a oferta (corrigido, falta ligação real), aceite da ligação recebida, IA reagindo antes do aceite, som "cortando", Groq pela VPS 53 (falta o proxy), senhas, Asaas |

## 2. Quem faz o quê (isso decide a ordem)

| Quem | Pode | Não pode |
|---|---|---|
| **Nuvem** (Claude Code online, este ambiente) | ler e mudar o código, rodar build e testes, enviar ao GitHub | entrar nas VPS (sem chave e a porta 22 é bloqueada daqui), publicar, fazer ligação |
| **PC** (Claude Code no `D:\hermes-call`, com a chave) | tudo da nuvem + publicar (`ops/publicar.sh`), olhar os registros da produção, usar a bancada, disparar ligação de teste | trocar senhas e mexer em segurança do servidor sem a dona |
| **Dona** | senhas, chaves, pagamentos, decisões comerciais, ligação de validação, deixar o repositório privado | — |

**Ritmo:** a nuvem trabalha sem parar na lista; **uma publicação por semana** (sexta) feita pelo PC, com a ligação de
validação da dona. Correção urgente pode ser publicada no meio da semana.

**Como o código anda:** a nuvem trabalha num branch (`claude/...`), um item por commit, sempre com `go build/vet/test`
e `vite build` verdes. Na quinta, o pacote da semana vira um pull request para o `main`. O PC publica o `main`.

**Regra da voz (vale acima de pressa):** mudança em `internal/voice/`, `broadcast.go`, `session.go` ou no codec só
fica "pronta" depois de uma ligação real e com o teste correspondente em `docs/REGRESSOES_LIGACAO.md`.

## 3. Prioridades

1. **P0 — Segurança que pode causar prejuízo já** (dados e contas expostos).
2. **P1 — A ligação** (é o produto): interromper, atender, responder rápido, som limpo e **não deixar os problemas voltarem**.
3. **P2 — Confiabilidade**: testes, avisos, backup fora da VPS, publicação mais segura.
4. **P3 — Receita**: dar para pagar, cadastro mais fácil, tela honesta.
5. **P4 — Crescimento**: a campanha da dona e os agentes por segmento.

---

## 4. Semana 1 (04 a 10/10): segurança e diagnóstico da ligação

### P0 — Segurança
- [x] **S1. Repositório público com segredos no histórico.** *(05/10: a dona privou os dois; conferido sem login: 404 nos dois. Os segredos antigos do histórico continuam precisando ser trocados)* *Dona, 1 minuto.* GitHub › repositório › Settings ›
  General › Danger Zone › *Change visibility* › **Private**, nos dois (`Emersonjosielmrx` e `fabricadeautomacoesia`).
  O Claude Code online funciona com repositório privado, desde que o app do Claude esteja instalado nele
  (https://github.com/apps/claude/installations/select_target). Não precisa abrir e fechar a cada sessão.
  Depois disso, tudo que já esteve no git precisa ser trocado (S2, S3 e a lista do `CONTINUAR_DAQUI.md`: senha root,
  Postgres, token do Telegram, Groq, Docker Hub, tokens do GitHub). Limpar o histórico (reescrever o git) só com OK
  explícito da dona, porque muda todos os commits.
- [x] **S2. Senha root da produção (241) é a mesma da 209 invadida.** *(trocada em 03/10 nas duas, conferido em 05/10 pelo `chage`; o login por senha continua LIGADO nas duas, com milhares de tentativas erradas por dia: falta desligar)* *Dona.* Trocar a senha e, se nada depender
  dela, desligar o login por senha (`PasswordAuthentication no`). O PC prepara o passo a passo; a dona roda.
- [ ] **S3. omniroute aberto sem senha** (`157.173.207.22`, portas 20128 e 20133): qualquer um que achar o endereço
  usa as contas pagas. *Dona + PC:* colocar chave de acesso ou liberar só os IPs das 3 VPS no firewall.
- [ ] **S4. Chaves em texto no PC:** apagar `deploy/add_openrouter_keys.py` e `deploy/add-openrouter-keys.sh` depois
  de cadastrar as chaves no cofre do painel. *PC.*
- [ ] **S5. Script `monitor_registrations.sh` na VPS** (falha sempre e tem token dentro): desligar o cron. *PC.*
- [x] **S6. Verificação automática de falhas conhecidas** *(04/10, `947abf3`: job "Falhas conhecidas" no CI)* nas bibliotecas: `govulncheck` e `npm audit` no CI
  (avisando, sem travar no começo). *Nuvem, P.*

### P1 — Ligação: medir antes de mexer
- [x] **L1. Confirmar a correção de "falei e ela não parou".** *(05/10 11:38: a dona interrompeu duas respostas e a IA parou em menos de 1 s nas duas, `voice barge-in`; a oferta não chegou a ser interrompida nessa ligação. `docs/ensaios/2026-10-05_1138_ligacao-humana.md`)* *Dona: 1 ligação. PC: conferir no registro*
  `voice barge-in` durante a oferta e `áudio 2 (oferta) tocado … interrompida=true`. Antes, conferir que a bancada
  está **sem** aceite automático (incidente de 03/10, `REGRESSOES_LIGACAO.md` §6).
- [x] **L2. A IA não reage antes da ligação ser aceita.** *(04/10, `2f1154c`)* Ignorar áudio recebido antes de "remote accepted" e de a
  persona estar carregada. Teste novo em `internal/voice` e linha nova em `REGRESSOES_LIGACAO.md`. *Nuvem, P.*
- [x] **L3. Medir o "som cortando".** *(04/10, `ffe5a3e`; como ler: `docs/COMO_DEBUGAR.md` cenário 5. Falta a parte do PC: 2 ligações reais)* Hoje não há número: registrar por ligação perda de pacotes, jitter, pacotes
  fora de ordem e vezes em que faltou áudio pra tocar (buffer vazio), dos dois lados. Uma linha de resumo no fim da
  ligação e o mesmo dado salvo junto da transcrição. *Nuvem, P.* Depois: 2 ligações reais (PC + dona) pra ver se o
  corte é rede, codec ou o nosso envio.
- [x] **L4. Aceite da ligação recebida (fase 1: descobrir o formato certo).** *(parte da nuvem feita 04/10, `8b56e52`: registro `sinalização da ligação`; captura feita pelo PC em 05/10 11:38: `relaylatency` antes do accept, accept sem `<enc>`, `medium=2`)* *Nuvem, P:* registrar no log (com a
  chave escondida) as mensagens `<preaccept>`, `<accept>`, `<transport>` e `<relaylatency>` que um **celular de
  verdade** manda quando atende uma ligação do Hermes. *PC:* 1 ligação do Hermes pro celular da dona e copiar o
  registro. Diferenças suspeitas no `BuildAcceptStanza` (`internal/voip/signaling/signaling_build.go:80`), a
  confirmar com esse registro:
  - o `<preaccept>` vai pro aparelho exato de quem liga, mas o `<accept>` vai pro número sem o aparelho (`CleanJID`);
  - anuncia só áudio 16 kHz, sem 8 kHz, e sem o bloco `<capability>`;
  - não manda `<relaylatency>`/`<transport>` depois do aceite, como faz na ligação que o Hermes origina.
- [x] **L5. Simulador de ligação (a defesa contra "corrige e volta").** *(04/10, `3282cf5`; 8 cenários em `internal/voice/simulador_test.go`, cada um conferido recolocando o defeito antigo)* *Nuvem, G, começa nesta semana e termina na
  próxima.* Um teste Go que roda o agente de voz inteiro sem WhatsApp: STT, IA e voz falsos com atrasos
  programados, e um "cliente" feito de áudio sintético (fala com pausas entre sílabas, "uhum", falar por cima,
  silêncio, ruído). Ele confere, a cada push, no CI:
  - a oferta para em menos de 1 s quando o cliente fala;
  - um "uhum" não corta;
  - dois áudios nunca se intercalam;
  - nada é respondido antes do aceite;
  - o tempo do fim da fala até a 1ª voz fica dentro do orçamento quando os serviços estão rápidos;
  - nenhuma frase interna (prompt, contexto do Whisper) vai pra voz.

  Cada problema novo que voltar vira um caso no simulador.

### P2 — Base
- [x] **E1. Documentação que confunde agentes.** *(04/10, `cc58a98`)* O `CLAUDE.md` ainda tem os avisos de julho sobre Docker, e o
  "Registro de projetos" aponta `D:\hipercool-refactor`. `BOTOES_MORTOS_E_DADOS_FAKE.md`, `ROADMAP_HERMES_CALL.md`,
  `ROADMAP_MELHORIAS.md` e `PROXIMA_RODADA.md` são de julho. Mover pra `docs/archive/` e deixar este plano como o
  roteiro único. *Nuvem, P.*
- [x] **O1. Teste rápido depois de publicar** *(04/10, `f9ca166`: confere linhas reconectadas via `/saude-local` e pânico no registro; volta sozinho. Falta o PC testar numa publicação de verdade)* dentro do `ops/publicar.sh`: `/api/version` com o build certo, login da
  conta de teste, `/api/sessions` com as linhas conectadas, e erro no registro nos primeiros 60 s. Se falhar, volta
  sozinho, como já faz quando o serviço não sobe. *Nuvem, P; PC testa.*
- [x] **O2. A bancada no repositório.** *(05/10: scripts copiados para `ops/bancada/`, sem senha nem telefone)* *(parte da nuvem feita 04/10, `f9ca166`: o `publicar.sh` atualiza a bancada e avisa se o aceite automático estiver ligado; falta o PC copiar os scripts)* `/root/lab-bancada.sh`, `/root/bateria-texto.sh` e `/root/ligacao-teste.sh`
  existem só na VPS. *PC:* copiar pra `ops/bancada/` (sem senhas). *Nuvem:* o `publicar.sh` passa a atualizar a
  bancada sozinho, com o aceite automático desligado (evita o incidente de 03/10).

**Publicação 1 (sexta 10/10, PC):** L2, L3, L4 (só o registro), O1, S6 e E1. Ligação de validação da dona: L1 + L3.

---

## 5. Semana 2 (11 a 17/10): ligação mais rápida e aceite funcionando

- [x] **L5. Simulador de ligação: terminar** e ligar no CI (ver semana 1). *(04/10: roda no CI junto com `go test`)*
- [ ] **L6. Tempo de resposta: de ~3,0 s pra ≤ 2,5 s.** *(05/10, `99f5208`: conexões reabertas antes da 1ª resposta; medir na próxima ligação)* *(04/10, `0e68370`: b feito (transcrição antecipada) e c em parte (conexões aquecidas). **Medido em ligação real em 05/10 11:38: 3,3 s na 1ª resposta e 2,1 / 1,9 / 1,9 / 1,7 s nas seguintes**, com fim de fala em 600 ms. Falta decidir o a e ver a 1ª resposta)* Cada passo só entra com o número antes e depois (simulador
  + `voice latência real` na bancada):
  - a. **Fim de fala:** a produção espera 840 ms de silêncio (configurado no painel ou no ambiente; o padrão do
    código é 500). Testar 550–650 ms na bancada, sem cortar quem faz pausa. *PC mede; dona decide.*
  - b. **Começar antes:** no silêncio curto (240 ms, quando hoje só toca o "ahã"), já transcrever e chamar a IA; se a
    pessoa voltar a falar, descartar. Ganho esperado de 0,3 a 0,5 s. *Nuvem, M, com testes no simulador.*
  - c. **1ª voz da ElevenLabs** (até 1,84 s na 1ª fala): abrir a conexão com a ElevenLabs no começo da ligação e
    mantê-la aberta; mandar primeiro uma frase curta; tocar o MP3 enquanto chega, sem arquivo temporário. Avaliar o
    modo de envio contínuo (websocket). *Nuvem, M.*
  - d. **Transcrição:** testar `whisper-large-v3-turbo` no Laboratório de pronúncia; se errar menos ou igual, trocar.
    *PC.*
- [ ] **L4. Aceite da ligação recebida (fase 2).** *(05/10, `2e96eaf`: peças 8/16/32 do `HERMES_ACEITE_VARIANTE` prontas e na bancada; falta a dona ligar de um celular para o 8288 com `/root/bancada-aceite.sh ligar 57`)* *Nuvem:* montar o aceite igual ao do celular (registro da
  semana 1), com teste que compara a estrutura. *PC:* testar na bancada (8288 → 8653) **com a dona avisada**. Se
  funcionar, ligar `HERMES_AUTO_ANSWER_ACEITAR` na bancada e depois na produção.
- [ ] **L7. Groq pela VPS 53** (pedido da dona). *Dona:* `ssh hermes-staging 'bash -s' < ops/vps/rede-vps53-squid.sh`.
  *PC:* testar da produção (deve dar 401), criar o `30-rede-vps.conf` com `HERMES_GROQ_VPS_PROXY` e reiniciar.
  *Dona:* ligar o botão em Configurações › Rede / VPS.
- [x] **O3. Tela "Saúde das ligações"** *(04/10, `2f6d1b3`: Configurações › Saúde das ligações; tabela `call_health`)* (só pra dona): últimas ligações com tempo de resposta por etapa,
  interrupções, cortes (L3), quedas, falhas de IA e se o reserva entrou. Assim ninguém precisa abrir o registro do
  servidor pra saber se piorou. *Nuvem, M.*
- [x] **E2. CI mais rigoroso:** *(04/10, `947abf3`: `go test -race ./...` no CI inteiro; 1 corrida achada e corrigida)* `go test -race` nos pacotes de voz e de chamada; relatório de cobertura. *Nuvem, P.*

**Publicação 2 (sexta 17/10, PC):** L6 (o que passou na bancada), O3, E2 e, se a bancada aprovar, L4. Ligação da dona
pra ouvir a velocidade.

---

## 6. Semana 3 (18 a 24/10): conversa melhor e base sólida

- [x] **L8. Quem atende a ligação recebida:** *(04/10, `7c77b9c`: recepcionista padrão; a dona ainda pode escolher um agente)* hoje, sem agente escolhido, atende o assistente da dona ("posso
  disparar campanhas..."). Usar um agente de atendimento por padrão e avisar no painel se nenhum estiver escolhido.
  *Dona escolhe o agente; Nuvem, P.*
- [x] **L9. Roteamento Nível 1 nas ligações recebidas** *(já existia desde a v0.6.0: `applyInboundVoiceProfile` usa o agente escolhido pras ligações; o plano estava desatualizado)*
- [x] **L10. Memória entre ligações:** *(04/10, `503b660`)* ligou de novo pro mesmo número, a IA sabe o resumo da última conversa e o que
  foi combinado. *Nuvem, M, testado no Laboratório.*
- [x] **L11. Marcar horário durante a ligação:** *(04/10, `bcdbd30`: fica PENDENTE na Agenda; a dona confirma)* "pode ser terça às 10?" vira compromisso na Agenda e aviso no
  Telegram. *Nuvem, M.*
- [x] **L12. Passar pra humano com a ligação quente:** *(04/10, `d32f445`: aviso de lead quente ligado por padrão, só avisa; botão "Entrar na ligação" no painel)* o lead pediu, ou a IA percebeu interesse alto → aviso imediato
  no Telegram com resumo e botão "ligar agora". *Nuvem, M.*
- [x] **E3. Testes onde não há nenhum:** *(04/10, `7a87366` + `6f33776`: Postgres de verdade num schema descartável, `HERMES_TEST_PG`; o CI sobe um postgres:16. Cobertos: cobrança, campanhas, login, configurações e os bancos do servidor. Falta o Asaas falso ponta a ponta, que fica pro P1)* cobrança (`internal/billing`, `billing_api.go`, com um Asaas falso), cadastro
  e login (`internal/auth`), campanhas (`internal/whatsapp_campaigns`: retomar sem repetir número, limite diário),
  configurações. *Nuvem, M.*
- [x] **E4. Painel sem erros de tipo:** *(04/10, `9847006`, `f76dc7c`, `f1a699d`: 205 → 0, com defeitos reais corrigidos no caminho (ver Registro); `tsc --noEmit` trava o CI)* zerar os 205 erros (os maiores: `SpecializedAgents.tsx` 42, `Sidebar.tsx` 22,
  `EasyAgentWizard.tsx` 19) e passar o `tsc` a travar o CI. *Nuvem, M.*
- [ ] **O4. Atualizar a biblioteca do WhatsApp (`whatsmeow`).** Uma atualização por vez, testada na bancada com
  ligação feita e recebida antes da produção. *Nuvem, P; PC testa.*
- [x] **O5. As 99 variáveis de ambiente:** *(04/10, `728abdd`: são 102; `.env.example` + teste que trava se faltar; tela "Configuração do servidor" que avisa de nome digitado errado)* um `.env.example` com cada uma (o que faz, padrão, onde se usa) e uma tela
  de leitura "configuração em uso" pra administradora (segredos escondidos). *Nuvem, M.*
- [ ] **O6. Backup fora da VPS e avisos.** *Dona:* escolher onde guardar (Google Drive ou Backblaze B2) e passar o
  token do bot de avisos. *PC:* preencher `RCLONE_REMOTE` e `/etc/hermes-call/alertas.env` e fazer um teste de
  restauração do backup na bancada.

**Publicação 3 (sexta 24/10, PC):** L8–L12, E3, E4, O5 e, se a bancada aprovar, O4.

---

## 7. Semana 4 (25/10 a 03/11): receita e campanha

- [ ] **P1. Dar pra pagar.** *Dona:* `HERMES_ASAAS_API_KEY` e `HERMES_ASAAS_WEBHOOK_TOKEN` (na VPS e no painel do
  Asaas), cancelar no Asaas as assinaturas das contas de teste. *PC:* um pagamento de teste ponta a ponta.
- [ ] **P2. Um só caminho até a 1ª ligação.** *(05/10, PC, 1ª parte: o cartão "Primeiros passos" do início já é o roteiro curto; o tour de 8 telas deixou de abrir sozinho por cima dele e virou um link do cartão; visto no navegador numa cópia local. Falta decidir com a dona se os assistentes de Configurações (Configura Fácil, Gestor, Follow-up) se juntam ou só somem do caminho)* Hoje há 5 assistentes sobrepostos (`SetupWizard`, `EasyAgentWizard`,
  `EasySettingsWizard`, `EasyManagerWizard`, `EasyFollowUpWizard`). Juntar num roteiro curto: conectar o WhatsApp →
  escolher um agente pronto → ouvir uma ligação de teste no próprio celular. *Nuvem, G.* A dona decide o tempo do
  teste grátis (hoje 10 horas).
- [x] **P3. Telas que prometem o que não existe** *(05/10, PC, a dona mandou esconder as quatro: cartão "God Mode" reduzido ao controle de gasto; "Superpoderes" do Gestor fora do assistente e da tela; opção "Transferir ligação SIP" fora; "Equipe" já estava fora do menu)* (Equipe, Telefonia SIP, "God Mode" da IA, superpoderes do Gestor):
  esconder até existirem. *Dona decide quais; Nuvem, P.*
- [x] **P4. Anti-bloqueio visível:** *(04/10, `fad763d`: o aquecimento e a parada já existiam no código; agora ficam registrados por linha e aparecem em Campanhas › "Proteção das linhas")* aquecimento automático por número (o teto sobe dia a dia), parada automática
  quando muitas ligações caem seguidas (já existe `HERMES_RISK_CONSEC_FAILS`) e um painel que mostra isso por linha.
  *Nuvem, M.*
- [x] **P5. Preparar a campanha da dona** *(04/10, parte do Hermes: `8dc6b08`. Aviso no Telegram quando lead de campanha responde (novo); exportar interessados (o botão exportava outra coisa, corrigido); o funil do CRM pela ligação e o chat único (aba Chat, com ligações) já existiam. Falta o PC copiar o `D:\campanha-hermes\README.md` e conferir se falta algo)* (`D:\campanha-hermes\README.md`; *PC copia pra `docs/campanha/`*): no
  Hermes, o que a campanha precisa:
  - resposta de lead vira aviso no Telegram na hora;
  - resultado da ligação alimenta o funil do CRM sozinho;
  - um chat só com todos os atendimentos;
  - exportar a lista de interessados.

  A captação das empresas e os agentes por segmento vêm **depois da 1ª rodada**, como a dona pediu.
- [ ] **E5. Dividir o pacote gigante** (`cmd/server`, 64 mil linhas) aos poucos, começando pelo Telegram
  (`telegram*.go`). Só partes cobertas por teste e sem mudar comportamento. **Nunca a parte da voz antes do
  simulador (L5) estar pronto.** *Nuvem, G, contínuo.*
- [ ] **Fechamento (01 a 03/11):** nova análise geral (como a de 02/10), comparar os números da seção 1, atualizar este
  plano e o `CONTINUAR_DAQUI.md`, e marcar a versão aprovada como ESTÁVEL (`ops/marcar-estavel.sh`).

**Publicação 4 (sexta 31/10, PC):** P2–P5 e a parte de E5 que estiver pronta.

---

## 8. Decisões que só a dona toma (sem elas o item espera)

| # | Decisão | Item |
|---|---|---|
| 1 | Deixar os repositórios privados e trocar as senhas e tokens | S1, S2 |
| 2 | Pôr senha ou firewall no omniroute | S3 |
| 3 | Quanto silêncio esperar antes de a IA responder (rapidez × cortar quem pausa) | L6a |
| 4 | Qual agente atende as ligações recebidas | L8 |
| 5 | Onde guardar o backup fora da VPS | O6 |
| 6 | Chave e token do Asaas; cancelar as assinaturas de teste | P1 |
| 7 | Tempo do teste grátis | P2 |
| 8 | Quais telas "em breve" esconder | P3 |
| 9 | Plano pago do Groq/Gemini, se a ligação passar a depender deles (o Groq de hoje é gratuito: 1.000 pedidos/dia por chave) | L6, L7 |

## 9. Fora deste mês (anotado pra não perder)

IA em reuniões do Google Meet; voz clonada; ligação de vídeo; "peraí que vou verificar" com subagente consultando a
base; vozes alternando por ligação; emoção na voz; base de conhecimento global com conteúdo real; esqueci a senha por
e-mail; tela de equipe de verdade.

## 10. Registro do mês

| Data | Item | Commit / publicação | Observação |
|---|---|---|---|
| 04/10 | Plano criado | — | análise: build/vet/test verdes, vite ok, 205 erros de TS, repositório público |
| 04/10 | L2 a IA só ouve depois do aceite | `2f1154c` | teste `TestAceite_*`; REGRESSOES §7 |
| 04/10 | L3 qualidade do áudio por ligação | `ffe5a3e` | log `qualidade do áudio da ligação`; diagnóstico `call_audio_cortes` |
| 04/10 | L4 (nuvem) registro da sinalização | `8b56e52` | log `sinalização da ligação`; passo a passo em REGRESSOES §5 |
| 04/10 | L5 simulador de ligação | `3282cf5` | 6 cenários (8 depois do L6), ~22 s, roda no CI |
| 04/10 | S6 + E2 CI com -race e falhas conhecidas | `947abf3` | corrida corrigida no teste do keep-alive |
| 04/10 | E1 docs | `cc58a98` | CLAUDE.md atual; 5 roteiros de julho no arquivo |
| 04/10 | O1 + O2 (nuvem) publicação mais segura | `f9ca166` | `/saude-local`; bancada sincronizada pelo `publicar.sh` |
| 04/10 | L6 b + c | `0e68370` | simulador: 1,73 s → 1,23 s com o fim de fala da produção |
| 04/10 | O3 Saúde das ligações | `2f6d1b3` | testada no navegador (computador e celular) com dados de exemplo |
| 04/10 | Segurança: 4 vazamentos entre contas | `accb782`, `c987889` | `/api/diagnostics`, envio em massa, Chatwoot resolve, chaves ElevenLabs (varredura das 395 rotas) |
| 04/10 | L8, L10, L11, L12 | `7c77b9c`, `503b660`, `bcdbd30`, `d32f445` | L9 já existia |
| 04/10 | Testes com Postgres de verdade | `7a87366` | `HERMES_TEST_PG`; o CI sobe um postgres:16 |
| 04/10 | E3 testes de cobrança, campanhas, login e configurações | `6f33776` | com banco de verdade: retomar campanha sem religar ninguém, 10 disparos ao mesmo tempo e só 1 liga, limite diário, trava de login por conta, custos de IA por conta |
| 04/10 | E4 painel sem erros de tipo | `9847006`, `f76dc7c`, `f1a699d`, `1e5c11c` | 205 → 0; defeitos reais: botão de enviar do teste do agente, salvar o Gestor desligava o "só ativo", lista de chaves vazia no assistente do Gestor, campos de agente especializado que não salvavam, seções do assistente que nunca apareciam |
| 04/10 | O5 catálogo das variáveis | `728abdd` | 102 variáveis; `go test ./cmd/server -run TestEnvCatalog -atualizar-catalogo` depois de mudar o `.env.example` |
| 04/10 | P4 proteção das linhas | `fad763d` | tabela `line_risk_events`; quadro em Campanhas; testado no navegador |
| 04/10 | Configurações que se apagavam ao salvar | `058a563` | a leitura não trazia credenciais do cofre, "interromper a IA" e "só ativo"; teste trava se faltar campo |
| 04/10 | P5 (parte do Hermes) | `8dc6b08` | aviso de retorno de campanha no Telegram; o botão "Modo Retorno" era morto; exportar interessados |
| 04/10 | CI instável: chave primária | `0819cdd` | `settings` e `ai_cost` conferiam a chave no banco inteiro; era a causa das falhas "aleatórias" |
| 04/10 | Fechamento da leva da nuvem | v0.8.0 | `VERSION`, `CHANGELOG`, passagem no `CONTINUAR_DAQUI.md`; publicar é com o PC |
| 05/10 | v0.8.0 publicada (PC) | `b9bf587`, build `20261005-1058_b9bf587` | com OK da dona; ensaio com a versão no ar em `docs/ensaios/2026-10-05_1109.md` |
| 05/10 | Item 4 da lista da dona (PC): F31, planilhas CSV, token do Telegram | `c1b300a`, `6dc0569`, `9454e4a` | v0.8.1 |
| 05/10 | v0.8.1 publicada (PC) + ligação de verdade aprovada pela dona | `f28526a`, build `20261005-1148_f28526a` | `docs/ensaios/2026-10-05_1138_ligacao-humana.md`; aceite de celular capturado |
| 06/10 | Conferência do trabalho de outro agente (PC) + fim do F19 | `5b04840` | ele refez no `main`, sem commit, 6 correções que já estavam neste ramo; guardado em patch e desfeito. Dos "34 achados pendentes" faltava só a Criatividade do Lab; `QA_PAINEL_E_METRICAS.md` e `BACKLOG_DX.md` marcados como históricos |
| 07/10 | v0.9.0 publicada (PC) + bancada na VPS de teste | `cdad439`, build `20261007-1425_cdad439` | correção do picote no ar; bancada movida para a 209 com banco próprio (ligação limpa: `tx_buracos=0`); Hermes e bancada nas duas VPS: `docs/PLANO_DUAS_VPS.md` |
| 08/10 | v0.10.0 publicada (PC): aba "Por código" na tela de conectar | `b0605a3`, build `20261008-1541_b0605a3` | feita no PC do Emerson e trazida por patch; tela conferida no painel local antes; foram junto `3865ba6` (colar `telefone,Nome` no Disparo em Massa) e `a96ef05` (roteiro de vendas); cópias igualadas (`ops/atualizar-copias.sh`). Falta gerar um código de verdade no painel |
