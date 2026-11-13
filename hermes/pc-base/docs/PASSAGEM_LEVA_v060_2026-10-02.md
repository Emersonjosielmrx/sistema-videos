# Passagem: leva de correções v0.6.0 (02/10/2026, noite)

> Escrito para qualquer agente ou conta que continue este trabalho.
> Leia junto: `CONTINUAR_DAQUI.md` e `docs/ANALISE_MELHORIAS_2026-10-02.md` (a análise que originou a leva).
> Histórico completo da conversa: `D:\hermes-call\_arquivo\historico_conversas\` (pasta fora do git, porque contém
> trechos com tokens). Sessão original: `C:\Users\Haylla\.claude\projects\C--Users-Haylla\ab1d2c29-c437-4b16-814e-ca38dd13ee83.jsonl`.

## 1. O que a dona pediu

1. "Analise tudo que pode ser melhorado em todas as áreas." Feito: `docs/ANALISE_MELHORIAS_2026-10-02.md`.
2. "Corrija todas." Em andamento, conforme este documento.
3. Regras de sempre: correção em cima do que está no ar; publicar só com `ops/publicar.sh` (com volta por
   `ops/reverter.sh`); ensaiar antes na VPS de teste; não dizer "pronto" sem verificar; português simples.

## 2. O que JÁ foi feito na PRODUÇÃO (62.171.128.241) em 02/10

| Ação | Como desfazer |
|---|---|
| Cancelado o agendamento falso "Caetano" de 03/10 09:00 (id `53cae5a3-6532-4a5f-a002-246eb52f8296`) | `UPDATE scheduled_calls SET status='pending' WHERE id='53cae5a3-...'` |
| Agente "e" (id `3336f7c3-87f3-4ecf-9a3d-3e101cb0808d`) renomeado para "Teste E (renomeado 02-10)": evitava ligações acidentais pelo Telegram | renomear de volta |
| Backup manual de TODOS os bancos `wacalls_*` em `/opt/hermes-call/backups-manuais/20261002-2105-antes-v060/` (425 MB) | só leitura |
| Cópia desse backup neste PC: `D:\hermes-call-backups\20261002-2105-antes-v060\` (sha256 conferido) | — |

**Nenhum código novo foi publicado ainda.** A produção continua na v0.5.0 (build `20260925-0158_29e4e85`).

## 3. Decisões da dona nesta sessão

- **Login SSH por senha na produção:** fica LIGADO (ela não quis desligar). Pendência dela: trocar a senha root,
  porque a atual está escrita na VPS 209, que está comprometida.
- **Cópia do código na VPS 209 (`/opt/hermes-call-fonte`, com histórico e senhas antigas):** trocar por uma
  **cópia limpa** (só o código atual, sem `.git` e sem segredos), DEPOIS da limpeza dos docs (já feita na leva).
  Ajustar também o `ops/enviar-fonte.sh` para mandar à 209 só a cópia limpa (na produção pode continuar com git). **Ainda não feito.**
- **Horário comercial:** quem nunca configurou continua com o padrão LIGADO (seg–sex 9–18, sáb 9–13), como sempre
  foi. A frente de ligações tinha invertido; o coordenador desfez (commit `57a4b7b` na integração).

## 4. Como o trabalho está organizado (git)

Repositório: `D:\hermes-call` (branch `main` = v0.5.0 + 2 commits de doc/teste). Cinco frentes em **git worktrees**,
cada uma no seu branch, mais um ramo de integração:

| Pasta | Branch | Conteúdo | Estado em 02/10 ~23h |
|---|---|---|---|
| `D:\hermes-wt\voz-audio` | `fix/voz-audio` | motor da ligação: oferta interrompível, resposta à isca, barge-in, streaming em paralelo, cache de TTS, ElevenLabs PCM, VAD, ambiente | ✅ concluída + revisão corrigida; integrada |
| `D:\hermes-wt\voz-conversa` | `fix/voz-conversa` | prompt/preço na ligação avulsa, respostas curtas, falhas da IA, motor reserva, RAG no streaming, RAG global, classificação/nota, **allowlist de ações na voz**, IA sem poder de dona em textos de terceiros | ✅ concluída + 2 rodadas de revisão; integrada |
| `D:\hermes-wt\seguranca` | `fix/seguranca` | /api/logs só admin, máscara de segredos, limites de login, sessão revogada, 2FA no login, esqueci a senha, cobrança (cupom, webhooks, troca/cancelamento, CPF/CNPJ alfanumérico), cabeçalhos, gravações fora do /tmp, backup/alertas em `ops/vps/`, limpeza do repo e dos docs | ✅ concluída (3 rodadas); integrada em `a2849fe` |
| `D:\hermes-wt\ligacoes` | `fix/ligacoes` | retorno de ligação perdida (LID), telefone oficial do contato, detector de promessas com confirmação, Telegram (agente certo, bot privado), "tocou" corrigido, agendadas (resultado/nova tentativa/limpeza), horário no fuso, alertas de linha | ✅ concluída (2 rodadas + callID na recebida); integrada em `38d3a3f`; revisão de confirmação dos críticos em andamento |
| `D:\hermes-wt\painel` | `fix/painel` | painel: telas sem dados falsos, lazy loading (2,3 MB → 0,47 MB), checkout em nova aba, CPF/CNPJ, esqueci a senha, 2FA, trocar/cancelar plano, primeiros passos, agente padrão, agendadas | 🔄 2ª rodada (contratos e robustez) em andamento; rodada 1 integrada |
| `D:\hermes-wt\integracao` | `integracao/v0.6.0` | junção de tudo | compila, `go vet` e `go test ./...` passam, `vite build` passa (em `e14dc10`) |

Para ver o que cada frente fez: `git -C D:/hermes-wt/<frente> log --oneline main..HEAD`.
Todas as frentes fazem commits pequenos; se uma rodada foi interrompida, o que estiver commitado no branch é aproveitável.

### Rodadas que estavam em andamento (se a sessão caiu, conferir/terminar)

**Ligações, 2ª rodada:** ✅ CONCLUÍDA e integrada (`38d3a3f`). Falta a REVISÃO DE CONFIRMAÇÃO dos críticos (passo 2 da seção 5). Itens que foram corrigidos:
- C1: o retorno automático NÃO pode ligar quando a dona atendeu ou recusou no celular, nem no fim por watchdog.
  Só retornar chamada que tocou e ninguém atendeu.
- C2: "não liga pra ele", "qual o telefone dele?", "a ligação caiu" NÃO podem discar. Tratar negação, só verbo
  imperativo, prazo de 10 min para o último número, e "IA narrou que ligou" vira pergunta.
- A1: o retorno respeita lista de acesso, admins, linhas próprias, grupos; não entra na repescagem e não cria CRM se não atendeu.
- A2: ignorar ofertas antigas/offline após restart.
- A3: lista de admins vazia não pode liberar solicitante externo; a dona continua admin.
- A4: CRM com card do LID e do telefone (atendimento humano não pode ser ignorado; sem card duplicado).
- A5: bot do Telegram privado. Chats já conhecidos continuam; chat novo só com aprovação. Último commit visto: `a02d0a6`.
- M1-M5: timeout/recover no despacho de agendadas, rodízio, `confirmed_at`, /agentepadrao na conta certa, validade da escolha de linha.
- Extra: registrar o callID também na ligação RECEBIDA (para "chamar humano" funcionar nela).

**Segurança, 3ª rodada:** ✅ CONCLUÍDA e integrada (`a2849fe`). Itens abaixo resolvidos:
- "esqueci a senha" não pode deixar conta legítima sem código (gravar IP no cadastro; critério mais amplo). Último commit visto: `23e4692`.
- plano `start_voz` com acesso à aba de agentes (`tabAgents`).
- lista de IPs não pode trancar o dono (recusar lista sem o IP atual).
- CORS com PATCH; nomes de plano oficiais (Start/Pro/Scale); rotas `/api/rag/upload|correct`.

**Painel, 2ª rodada:**
- CNPJ alfanumérico (sem `inputMode=numeric`/`onlyDigits` no CNPJ); rótulos claros dos 2 seletores de agente.
- 2FA ligar/desligar pede a senha atual; ler `?2fa_challenge=`/`?token=` do Google.
- `change-plan`: respeitar `effective` (`on_payment`/`next_cycle`) e mostrar `message`.
- "Sair" chama `/api/auth/logout`; só deslogar em 401 (não em 502/503).
- Textos do horário; ErrorBoundary no lazy + `vite:preloadError`; tela de admin para desligar 2FA de uma conta.
- Itens baixos: `register()` preserva message/field, `apiDelete` com mensagem, chunk do React separado,
  `/api/models` → `/api/ai/models`, rota certa do histórico do chat.


## 4b. Atualização 03/10 ~00h: tudo integrado, falta a 3ª rodada das ligações

- **Ramo `integracao/v0.6.0`** (`D:\hermes-wt\integracao`): as 5 frentes estão juntas (painel e segurança concluídos).
  Já tem `VERSION`=0.6.0 + `CHANGELOG` (commit `5894d7d`) e o `ops/enviar-fonte.sh` mandando cópia LIMPA para a 209 (`8645214`).
  Compila; `go vet` e `go test ./...` passam; `vite build` passa.
- **A revisão de confirmação das ligações** achou C1, M3 e voz FECHADOS, mas ainda há itens. **Não publicar antes de terminar:**
  - frente **ligações** (3ª rodada):
    - negação no fim ("liga pra ele não") ainda disca;
    - número vindo do histórico deve sempre pedir confirmação com botões;
    - "repete"/"de novo" não podem rediscar sozinhos;
    - retorno automático: não ligar para contatos salvos na agenda (exceto leads), botão "Cancelar retorno" e espera de 45 s, respeitar IA pausada/humano;
    - prazo de 8 min que cancela de verdade;
    - CRM limpando `deleted_at`;
    - revogação de chats do Telegram (`/acessos`);
    - "sim" de envio não vira ligação;
    - relógio/fila offline;
    - recover por número;
    - `DueCalls` exigindo `confirmed_at`.
  - frente **voz-conversa** (rodada curta):
    - REGRESSÃO: cliente no WhatsApp que pede atendente fica sem resposta (`request_human`/`ask_admin` barrados com a lista de admins fail-closed). Liberar essas duas presas ao próprio contato e nunca devolver vazio;
    - bloquear ações de LEITURA para contatos externos no chat (vazamento de dados);
    - ação "call" para a dona com número vindo do histórico pede confirmação.
- Depois dessas rodadas: integrar (`git merge` dos 2 branches na integração), nova revisão rápida dos itens, e seguir a seção 5 a partir do passo 3 (VERSION/CHANGELOG já feitos; só ajustar o CHANGELOG se algo mudar).
- **Notas da versão para a dona:** comandos pelo WhatsApp do número PESSOAL dela agora exigem cadastrá-lo com `/addadmin` (lista de admins vazia não libera mais ninguém).

## 4c. Atualização 03/10 ~09h: 3ª rodada FEITA e v0.6.0 no `main`

Todos os itens da 4b foram feitos direto em `integracao/v0.6.0` (commits `6671a24`..`6eee601`) e o ramo
foi juntado no `main` (merge `0230603`). Passos 1–4 da seção 5 estão concluídos.
- Ligações: "não" no fim, pedido pra depois ("amanhã", "às 14h"), "ele liga", "chama no zap" não discam (as
  regras olham só o pedido, não o recado depois de "e fala…"); número do histórico sempre confirma com o
  número na tela; "de novo"/"repete" soltos pedem botão; "sim" pra ligar só em resposta de até 4 palavras;
  "sim" a confirmação de ENVIO é tratado antes da detecção de ligação; ação `call` da IA pra dona confirma
  quando o número não estava na mensagem dela (botões `pcall:yes/no`).
- Retorno automático: pula contato salvo na agenda (exceto lead), IA pausada e atendimento humano; aviso
  com botão "Cancelar retorno" (`cbcancel:`) e 45 s; filtros conferidos de novo depois da espera.
- Agendadas: prazo de 8 min cancela a campanha (não disca depois) e encerra a ligação viva; recover por
  número; `DueCalls`/`MarkDispatched` exigem `confirmed_at` nas detectadas.
- CRM: `MoveLead`/`SetLead`/`SetLeadDeal` limpam `deleted_at`. Pausa manual da IA normaliza o JID (WhatsApp Web).
- Telegram: `/acessos` (revogar/autorizar), chat que sai da config é revogado (só com a config lida),
  erro de banco não rebaixa chat aprovado.
- Relógio/fila offline: regra de 60 s só durante a entrega da fila offline (`OfflineSyncCompleted`, máx. 90 s);
  ao vivo só ignora > 10 min; relógio da produção conferido: NTP sincronizado.
- Chat (voz-conversa): `request_human`/`ask_admin` liberados pro contato; leitura bloqueada pra externo;
  ação negada nunca volta vazia; gate de admin antes dos de modo/toggles.
- **Volta segura:** `hermes-release.sh` ganhou ESTAVEL/PROTEGIDA (`marcar-estavel`, `voltar-estavel`); o
  `publicar.sh` marca a versão no ar como estável antes da troca; `ops/voltar-estavel.sh`,
  `ops/marcar-estavel.sh` e `ops/VOLTAR-VERSAO-ESTAVEL.bat` (dois cliques, pede "SIM").
- `ops/.gitattributes`: tudo de `ops/vps/` com LF (o CRLF do Windows quebraria os `.env` no Linux).
- Ainda não feito (MÉDIO/BAIXO da revisão, não bloqueiam): "canal livre" das promessas com maxCalls > 1;
  rodízio por conta; cards do telefone e do LID que já existem os dois não são fundidos; mesma pessoa ligando
  pra duas linhas recebe dois retornos; `maybeCallback` sem prazo nas consultas.

## 5. Próximos passos, em ordem

1. **Terminar e integrar** as 3 rodadas acima. Em `D:\hermes-wt\integracao`: `git merge --no-edit fix/ligacoes fix/seguranca fix/painel`
   (uma de cada vez), depois `CGO_ENABLED=0 go build ./... && go vet ./... && go test ./...` e `cd client && npx vite build`.
2. **Revisão independente rápida** dos críticos da Ligações (C1, C2, A1-A5) no código integrado.
3. **Versão:** `VERSION` → `0.6.0`; `CHANGELOG.md` com os textos de cada frente (estão nos relatórios das frentes,
   resumidos na seção 7); `docs/VERSOES.md` e `CONTINUAR_DAQUI.md` atualizados.
4. **Juntar no `main`:** `git -C D:/hermes-call merge --no-ff integracao/v0.6.0` (o `publicar.sh` exige git limpo e
   que o commit contenha a versão no ar).
5. **Ensaio na VPS de teste (209):** `bash ops/publicar-teste.sh`. Conferir `/api/version`, login, telas, migrações
   (colunas novas, `daily_retries_v2`, `login_known_ips`, `hermes_data_migrations`). A 209 está comprometida:
   não colocar segredos novos lá.
6. **Compilar na produção sem publicar:** `bash ops/publicar.sh --so-compilar` (roda `go vet -tags mlow` na VPS
   pela primeira vez).
7. **Antes de publicar, na VPS de produção:**
   - `apt-get install -y rsync` (o backup novo usa; não há rsync nem rclone hoje).
   - Em `/etc/systemd/system/hermes-call.service.d/10-segredos.conf`:
     - `HERMES_PLATFORM_ADMINS=admin@hermescall.com`; sem isso, o "admin da plataforma" cai no enterprise mais antigo.
     - `HERMES_MONITOR_BOT_TOKEN` e `HERMES_MONITOR_CHAT_ID`, para os avisos.
     - Asaas continua sem chave: os webhooks passam a responder 503 até a dona configurar
       `HERMES_ASAAS_API_KEY` e `HERMES_ASAAS_WEBHOOK_TOKEN`. Hoje ninguém paga online de qualquer jeito.
   - Conferido em 02/10: nenhuma conta com 2FA ligado; as 30 com cupom `TESTE_GRATIS` são todas de teste;
     o domínio aponta direto para a VPS (sem Cloudflare), então os limites por IP funcionam; o Go 1.26.4 já está baixado na VPS.
8. **Publicar:** `bash ops/publicar.sh`, com backup do banco e volta automática. Conferir:
   - `/api/version` com `"channel":"producao"`;
   - os cabeçalhos de segurança;
   - `/uploads/` dando 404;
   - nenhum `api.telegram.org/bot<número>` no journal.
9. **Operação na VPS:**
   - `scp -r ops/vps hermes-prod:/tmp/hermes-ops && ssh hermes-prod 'bash /tmp/hermes-ops/instalar-operacao.sh'`;
   - preencher `/etc/hermes-call/alertas.env` e testar `/opt/hermes-call/ops/hermes-alerta.sh "teste"`;
   - rodar um backup (`systemctl start hermes-backup.service`);
   - desligar o cron do `monitor_registrations.sh`, que falha sempre e tem token dentro (fazer backup do crontab antes);
   - as gravações agora vão para `/var/lib/hermes-call/recordings`.
   - O journald NÃO deve ser reiniciado sem a dona decidir (o teto de 2G vale no próximo reinício).
10. **Ligação de teste com a dona.** Celular 91 99243-8288; pedir pelo Telegram, antes definindo `/agentepadrao Vendas Hermes Call`. Conferir:
    - preço na 1ª frase;
    - oferta interrompível e resposta à isca;
    - sem silêncio longo;
    - classificação certa;
    - logs `voice latência real`, `filler pré-gerado … cache_hits`, `voice: resumo do gate do fundo`.
11. **Cópia limpa na 209** e ajuste do `ops/enviar-fonte.sh` (decisão da seção 3).
12. Push do `main` e das tags para os 2 GitHubs (origin e emerson).

## 6. Pendências que só a dona resolve

- Trocar a senha root da produção e as senhas/tokens que estavam em docs e no histórico do git:
  Postgres, token do Telegram, chaves de IA/Groq, PAT do Docker Hub, `WACALLS_API_KEY`, tokens do GitHub.
- Configurar o Asaas: chave + token do webhook (e o mesmo token no painel do Asaas). Cancelar no Asaas as assinaturas de contas de teste.
- Conta de nuvem para o backup fora da VPS (`rclone`, ex.: Google Drive/Backblaze). Até lá o backup diário fica só na VPS.
- Decidir se reescreve o histórico do git para apagar os segredos antigos (`git filter-repo` + push forçado).
- Limpar a VPS 209 comprometida (cron do pastefy, chaves sem nome, usuário duc).
- Tamanho da oferta gravada e duração do teste grátis: decisões comerciais.

## 7. Resumo para o CHANGELOG da v0.6.0 (textos das frentes)

**Ligação mais natural e certa**
- A ligação pelo Telegram/painel segue o roteiro do agente; a IA diz o preço na 1ª frase e responde em até 2 frases curtas.
- O cliente pode interromper a oferta gravada; a resposta ao "alô" é ouvida (se perguntar "quem fala?" ou recusar, a IA responde na hora).
- Frases sem buracos, a linha nunca fica muda enquanto a IA pensa, e o fim da fala é detectado mais cedo.
- Se a IA falhar, entra um motor reserva; nunca é falado erro técnico ao cliente.
- Na ligação, quem liga não consegue mandar a IA executar ações (só chamar humano/perguntar ao dono/transferir).
- "Interessado" agora depende da análise da IA; a duração gravada é a real.
- ElevenLabs gasta menos (as palavrinhas de apoio entram em cache) e responde mais rápido; o som de fundo abaixa sob a voz.

**Retornos, agendamentos e Telegram**
- O retorno automático de ligação perdida liga para o telefone real; não liga se a dona atendeu/recusou no celular.
- O Telegram não escolhe o agente errado nem liga por mensagens curtas ou negativas; bot privado; novo `/agentepadrao`.
- Pedidos de retorno detectados nas conversas esperam confirmação no Telegram e entendem o horário pedido.
- Agendadas mostram o resultado, tentam de novo sozinhas e são feitas uma de cada vez; "tocou mas não atendeu" correto.
- Aviso no Telegram quando a linha do WhatsApp cai/é bloqueada.

**Segurança e cobrança**
- A tela Logs é só da administração; senhas e tokens aparecem escondidos nos registros.
- "Esqueci a senha" com código pelo WhatsApp; 2FA de verdade no login; sair encerra a sessão.
- Proteção contra tentativas de senha e cadastros em massa.
- Trocar de plano e cancelar pelo painel; CPF/CNPJ válido (inclusive CNPJ com letras); cupom estende o teste.
- Backup diário automático, alertas de queda e de disco; gravações fora da pasta temporária.

**Painel**
- 5× mais leve no primeiro carregamento; pagamento em nova aba com conferência automática; "Primeiros passos" no Painel.
- Sem números e nomes de exemplo que pareciam reais; recursos que ainda não funcionam aparecem como "em breve".
