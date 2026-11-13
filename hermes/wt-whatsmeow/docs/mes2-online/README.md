# Mês 2 online — plano, histórico e o que falta (salvo em 05/10/2026)

> Pasta criada a pedido da dona para não perder nada quando os tokens da sessão online acabarem.
> **Próximo agente (online ou PC): leia este arquivo inteiro antes de mexer.** Ramo de trabalho:
> `claude/gallant-mendel-f1xney` (em cima de `pc/v0.8.0`). Divisão PC × online: `docs/DIVISAO_TRABALHO_PC_ONLINE.md`.
> Pedidos ao PC: `docs/PEDIDOS_AO_PC.md`. Resumo das mudanças para a dona: `CHANGELOG.md`, seção "Próxima versão".

## 1. Estado em uma frase

17 achados graves/altos da auditoria de 04/10 verificados; 16 corrigidos com teste e enviados (falta só o painel do F15).
Dos 17 médios/baixos, 11 verificados (todos reais) e 6 não verificados (a verificação caiu por limite de sessão).
A investigação "gravação + resumo não chega na ligação recebida e no retorno" terminou (seção 4) e foi corrigida (05/10:
online + PC). **05/10 (PC, ramo `pc/achados`):** gravação (uma linha por ligação), F30, F32, F33 e F34 corrigidos.

## 2. Arquivos desta pasta

| Arquivo | O que tem |
|---|---|
| `README.md` | este resumo: estado, histórico, achados, gravação, próximos passos |
| `dados/auditoria_achados_e_veredictos.json` | os 34 achados (F01–F34) como o auditor escreveu + o veredicto do verificador (motivo, evidência com arquivo:linha, plano de correção, plano de teste) |
| `dados/investigacao_gravacao.json` | os 4 rastreios (saída manual, recebida, retorno, histórico) e as 5 hipóteses H1–H5 com evidência |

## 3. Histórico (commits do online neste ramo, mais novo em cima)

| Commit | Data | O que |
|---|---|---|
| `553cbde` | 2026-10-05 | fix(agentes): salvar agente não perde transbordo, som de fundo, extras nem voz |
| `7e2c675` | 2026-10-05 | chore: tira do git o binário server gerado por engano e ignora /server |
| `5c09b8d` | 2026-10-04 | fix(configura-fácil): o assistente aplica as chaves escolhidas (id real do cofre) |
| `f841b97` | 2026-10-04 | fix(gestor): salvar pelo Gestor Fácil não desliga o aviso no Telegram nem o OpenClaw |
| `bc61013` | 2026-10-04 | fix(perfil): Meu Perfil salva preferências e cargo sem quebrar nem apagar a foto |
| `5a52715` | 2026-10-04 | fix(chatwoot): webhook Chatwoot → WhatsApp funciona, com token secreto por linha |
| `a34e1d6` | 2026-10-04 | fix(segurança): follow-up só aceita etapa e contato na campanha da própria conta |
| `4c323da` | 2026-10-04 | fix(agentes): criar agente com nome repetido não apaga mais o agente existente |
| `d022c57` | 2026-10-04 | fix(segurança): motores globais e chaves ElevenLabs só da dona |
| `ee63842` | 2026-10-04 | fix(segurança): ligações e avisos de ligação só para a conta dona da linha |
| `e95307a` | 2026-10-04 | fix(segurança): apagar imagem do catálogo não apaga mais arquivo fora dos uploads |
| `d2c88da` | 2026-10-04 | fix: itens da revisão do PC (CSV, banco de teste, senha em URL, CRLF, CI) |
| `f8efae5` | 2026-10-04 | feat(ligação): variantes do aceite atrás de HERMES_ACEITE_VARIANTE (só bancada) |
| `346d99d` | 2026-10-04 | feat(ligação): chaves de teste do aceite para o ensaio IA × IA (só bancada) |

⚠️ **Erro meu a resolver com a dona:** os commits `4c323da`..`5c09b8d` levaram por engano o binário `server` (46 MB,
gerado por `go build ./cmd/server` na raiz). O commit `chore: tira do git o binário server` tirou do índice e pôs
`/server` no `.gitignore`, mas o histórico do ramo ainda guarda 5 versões (~46 MB cada). Limpar exige reescrever o ramo
(`git filter-repo --path server --invert-paths` + `push --force`) — **só com a confirmação da dona**. Não tem segredo
dentro (é o código compilado). Para não repetir: compile com `go build ./...` ou `go build -o /dev/null ./cmd/server`
e nunca use `git add -A` (adicione os arquivos pelo nome).

## 4. Investigação: gravação + resumo não chegam na ligação recebida e no retorno

Relato da dona (04/10): "me envia a gravação e o resumo quando EU ligo usando o Hermes, mas quando ELE ATENDE ou quando
ele RETORNA a ligação, não envia". Rastreio completo em `dados/investigacao_gravacao.json`. Conclusões (os verificadores
adversariais caíram por limite de sessão — confira no código antes de afirmar):

- **H1 (alta) — ligação recebida:** na produção o Hermes **não aceita** a ligação recebida (o aceite automático só liga com
  `HERMES_AUTO_ANSWER_ACEITAR=true`, e o WhatsApp não reconhece o aceite do Hermes — `docs/REGRESSOES_LIGACAO.md` §5,
  tarefas A2/A3). Sem aceite não chega áudio; o gravador fica vazio e `recorder.finish()` devolve ok=false **sem nenhum
  log** (`session.go` finalizeRecording, `recorder.go:216`). Ou seja: hoje a recebida só toca; quem conversa é o retorno.
  Correção de verdade = descobrir o aceite (A2/A3 com o PC).
- **H2 (média):** quando há aceite (bancada/botão Atender), o MP3 só é enviado **se o STT devolver texto**
  (`recording.go` transcribeAndSummarize faz `return` antes do envio; log só em Debug). Quem liga não fala → nada chega.
- **H3 (média) — retorno:** o código do retorno é **o mesmo** do "liga pra X" (maybeCallback → runCampaign →
  broadcastOne → finishConversationCall → removeCall/finalizeRecording → onRecordingReady). Não há desvio que pule a
  gravação. O que não entrega é o retorno que não vira conversa (não atendeu, caiu no aquecimento, < 3 s de áudio).
- **H4 (média):** a entrega tem várias saídas **caladas** (finish ok=false, conta sem store/dono, STT vazio em Debug,
  sem bot do Telegram para a conta, legenda cortada por byte em `telegram.go` ~2891 podendo partir acento).
- **H5 (baixa):** retorno e recebida entregam ao bot do **dono da linha que recebeu**; se a linha estiver pareada em outra
  conta (ou conta sem bot), vai para outro Telegram ou para ninguém. **Não** redirecionar para outra conta (vazaria dados).

**Feito em 05/10 (commit "fix(gravação)…"):** itens 1–4 abaixo, com o teste `TestDB_Gravacao_AudioVaiMesmoSemTranscricao`.
Falta: o item 5 (PC, pedido 6) e o 6 (explicar à dona — já explicado no chat).

**✅ corrigido (05/10, PC)** — achado do PC: no período do relato os retornos **não foram atendidos** (sem atendimento
não há gravação). Mesmo assim, no ramo `pc/achados` (`cmd/server/gravacao_entrega.go`):
- toda ligação deixa **uma linha** no registro com o `call_id` e onde a entrega parou: `entrega=sem_gravacao`,
  `nao_atendida` ("sem gravação: ligação não atendida", não é perda), `sem_audio`, `encode_falhou`, `sem_dono`,
  `sem_telegram`, `telegram_falhou` ou `entregue` — mais `registro=`, `transcricao=`, `resumo=`, `chats=`/`chats_falhos=`
  e `erros=` quando algo falhou no caminho. Achar: `journalctl -u hermes-call | grep "entrega=" | grep <call_id>`.
  (As linhas antigas `recording encode failed`, `falha ao persistir gravação`, `telegram sendAudio failed` e
  `gravação descartada…` viraram atributos desta linha.)
- ligação não atendida não gera MP3 (o gravador é descartado);
- o áudio vai mesmo sem transcrição/resumo, com a legenda dizendo que o resumo falhou e por quê.
Testes: `TestDecidirGravacao`, `TestEtapaDaEntrega_MP3ETelegram`, `TestLegenda_DizQueOResumoFalhou`,
`TestConcluirGravacao_*`, `TestEntrega_LinhaSemDonoDeixaAviso`, `TestDB_Gravacao_UmaLinhaPorLigacao`.
**Falta (teste real):** um retorno ATENDIDO na produção deve chegar ao Telegram e deixar `entrega=entregue`.

**Correção recomendada (pequena, a fazer primeiro):**
1. `recording.go`: se o STT falhar ou vier vazio, **mandar o MP3 mesmo assim** com legenda "🎙️ Ligação X (sem transcrição)";
   trocar o Debug por Warn.
2. Logar em Info/Warn cada saída calada: finalizeRecording (gravação descartada: segundos, motivo), onRecordingReady
   (sem store/sem dono), sem bot do Telegram para a conta (recording.go e notifyTelegram em broadcast.go).
3. Cortar a legenda do áudio por rune, não por byte (`telegram.go` sendAudioFile).
4. Gravar `Direction` real (inbound/outbound) em vez de "outbound" fixo (`recording.go`).
5. Pedir ao PC: no journal da produção, na hora de um retorno relatado, procurar `callback: retornando ligação perdida`,
   `ligação não atendida`, `recording encode failed`, `falha ao persistir gravação`, `stt`, `telegram sendAudio failed`;
   e conferir no banco se o user_id da linha que recebe as ligações é o da conta que tem o bot.
6. Explicar à dona: a recebida só vai gravar quando o aceite funcionar (A2/A3).

## 5. Achados da auditoria de 04/10 (F01–F34)

| Id | Achado | Gravidade (verificador) | Situação |
|---|---|---|---|
| F01 | Canal de eventos (SSE) entrega a lista de ligações ativas de TODAS as contas | high | ✅ corrigido (ee63842) |
| F02 | Apagar imagem do catálogo apaga arquivo de outra conta ou qualquer arquivo do servidor | critical | ✅ corrigido (e95307a) |
| F03 | Salvar 'Voz e Transcrição' em qualquer conta troca a transcrição (STT) e o motor de voz de TODAS as contas | critical | ✅ corrigido (motores globais) |
| F04 | Chaves ElevenLabs da dona são usadas por qualquer conta e enviadas para a URL que a conta escolher | high | ✅ corrigido (motores globais) |
| F05 | Salvar 'IA' ou 'IA da ligação' de uma conta troca os agentes globais usados pelas outras contas | high | ✅ corrigido (motores globais) |
| F06 | Criar agente com nome que já existe apaga o agente inteiro (upsert por nome grava todas as colunas) | high | ✅ corrigido (4c323da) |
| F07 | Desligar/recusar chamada na própria linha remove do broker a ligação de outra conta e derruba a conversa da ca | medium | ✅ corrigido (ee63842) |
| F08 | Follow-up: dá para criar etapa e inscrever contato na campanha de outra conta | low | ✅ corrigido (a34e1d6) |
| F09 | Webhook do Chatwoot sempre responde 404: respostas do atendente não chegam ao WhatsApp | medium | ✅ corrigido (5a52715) |
| F10 | Eventos de ligação vão para o usuário vazio e nunca chegam ao painel (popup de recebida e status somem) | medium | ✅ corrigido (ee63842) |
| F11 | Perfil da empresa: campo 'extra' vai como texto dentro de texto (CNPJ e preferências nunca voltam) e cada tela | medium | ✅ corrigido (bc61013) |
| F12 | 'Configuração Fácil do Gestor' apaga o aviso no Telegram e o OpenClaw do agent_chat ao salvar | medium | ✅ corrigido (f841b97) |
| F13 | Assistente 'Configura Fácil': chave escolhida no cofre para IA/STT/TTS nunca é aplicada (id não vai ou é id in | medium | ✅ corrigido (5c09b8d) |
| F14 | Funcionário Fácil: palavras de transbordo, mensagem de transferência e som ambiente são descartados pelo /api/ | medium | ✅ corrigido (553cbde) |
| F15 | Editar agente no Funcionário Fácil zera todas as configurações avançadas (extras) | high | ✅ corrigido (553cbde servidor + painel em 05/10) |
| F16 | Salvar no Laboratório Avançado troca a voz por "alloy", reseta o motor reserva e quebra todas as regras de com | medium | ✅ corrigido (553cbde) |
| F17 | Perfil da conta: campo extra é gravado como texto duplamente codificado e "Salvar preferências" apaga a foto | medium | ✅ corrigido (bc61013) |
| F18 | Ligação em massa (/api/mass-call) tem uma vaga só para o servidor inteiro | medium | ✅ corrigido (05/10) |
| F19 | Laboratório Avançado: lê/grava campos com nome errado e, ao salvar, troca o motor reserva do agente por groq/l | medium | ✅ corrigido (F16 em 553cbde + criatividade do Lab em 06/10, PC: lê e grava `extras.temperature`; o "Max Tokens", que ninguém lia, saiu) |
| F20 | Botão 'Testar' do TTS não funciona com chave do cofre: /api/tts/test não aceita credential_id | low | ✅ corrigido (05/10) |
| F21 | 'Gerar áudio por IA' da Ligação em Massa ignora a credencial TTS do cofre e falha para ElevenLabs/OpenAI | medium | ✅ corrigido (05/10) |
| F22 | Assistente 'Configura Fácil' testa a chave de STT no endpoint de chat (/api/ai/test) | medium | ✅ corrigido (05/10) |
| F23 | Desligar o som ambiente global não fica salvo: a leitura religa "office" | medium | ✅ corrigido (05/10) |
| F24 | Ligação de campanha sobrescreve as "Notas do Vendedor" do contato | medium | ✅ corrigido (05/10) |
| F25 | Chave "Responder só quem eu já liguei" reenvia um agent_chat velho e desfaz o Roteamento Nível 1 e o Gestor Fá | medium | ✅ corrigido (05/10) |
| F26 | "Testar Telegram" do Gestor Fácil troca a lista de chats autorizados por um só e revoga os outros | medium | ✅ corrigido (05/10) |
| F27 | Funcionário Fácil mostra e manda som ambiente e palavras de transferência, mas o servidor descarta | medium | ✅ mesmo defeito do F14 (553cbde) |
| F28 | Salvar o Chatwoot pelo painel desliga grupos, canais, assinatura, sempre online e leitura automática | low | ✅ corrigido (05/10) |
| F29 | Status/pausar/retomar campanha não confere a linha nem o dono quando a campanha não tem UserID | none | não é defeito explorável; ✅ reforço feito (05/10, PC) |
| F30 | Etiqueta de contato aceita tag_id de outra conta e devolve o nome dela | low | ✅ corrigido (05/10, PC) |
| F31 | Qualquer conta apaga campanhas antigas sem dono (user_id NULL) de outra conta | none | não é defeito explorável; ✅ reforço feito (05/10, PC): dono da linha preenchido ao subir, órfã só o admin apaga |
| F32 | Funil (CRM): botões 'Mover para...' e 'Disparo em Massa' da seleção múltipla não fazem nada | low | ✅ corrigido (05/10, PC) |
| F33 | Contatos: quando não há histórico, o painel mostra interações inventadas como se fossem reais | low | ✅ corrigido (05/10, PC) |
| F34 | Concluir o Configura Fácil apaga o som ambiente do agente mais antigo | low | ✅ corrigido (05/10, PC) |

**Outros itens feitos pelo PC (05/10, lista da dona, item 4):**
| Item | Situação |
|---|---|
| CSV do painel fora da `lib/csv` (Listas, Dados coletados, Captação de leads; Contatos é gerado no servidor e passou a sair no mesmo formato; "Exportar CSV" das Transcrições não fazia nada) | ✅ corrigido (05/10, PC) |
| `GET /api/easy-manager/wizard` devolvia o `telegram_token` sem máscara | ✅ corrigido (05/10, PC): só o fim na leitura; no salvar a máscara vale "não mudou" (teste `TestDB_GestorFacil_TokenDoTelegramMascarado`) |

Planos de correção de cada um (com arquivo:linha e teste) em `dados/auditoria_achados_e_veredictos.json` → `veredictos.Fxx.fix_plan`.

## 6. Próximos passos, em ordem

1. ~~Gravação/resumo (seção 4, itens 1–4)~~ — feito em 05/10.
2. ~~**F15 no painel:**~~ feito em 05/10 (`client/src/lib/agent-extras.ts`). `client/src/components/settings/EasyAgentWizard.tsx` lê `initialProfile.extras.*` mas o extras chega
   como TEXTO; criar `parseExtras` compartilhado (copiar de `SpecializedAgents.tsx:77` para `client/src/lib/`) e preencher
   todos os campos avançados com `??` (temperatura, reserva, pressão, desconto, empatia, gatilhos, handoffAdminNumber…).
3. ~~Corrigir F18, F20–F26, F28~~ (feito em 05/10). ~~Faltam F30, F32, F33, F34~~ (feitos em 05/10 pelo PC, ramo `pc/achados`). ~~F19: conferir só a temperatura do Lab~~ (feito em 06/10: teste `TestLabTemperatura_ValePeloExtras`). **Os 34 achados estão fechados.**
4. ~~Verificar F29–F34~~ (feito em 05/10; veredictos no JSON). (rodar de novo o workflow `verificar-achados` com `{"ids":["F29","F30","F31","F32","F33","F34"]}`;
   o script fica em `~/.claude/projects/.../workflows/scripts/verificar-achados-*.js` na sessão online; se não existir,
   verificar à mão lendo o achado no JSON).
5. Itens da revisão do PC ainda abertos (`docs/REVISAO_RAMO_ONLINE_2026-10-04.md`): lead quente com ponte silenciosa,
   filtro de confiança do Whisper (verbose_json), busca do Chatwoot só nas linhas da conta (`chatwoot.go` ~884/901),
   painel reenviando default/voice_profile_id velhos e "API Key Manual" do agente, latência, IA×IA barge-in.
6. A3: comparar o aceite com a captura de um celular de verdade quando o PC gravar em `docs/ensaios/`.
7. Frentes da auditoria ainda não rodadas: concorrência, SQL, telas mortas, privacidade, ops, telegram, cobrança/auth,
   campanhas, agente IA, voz, integrações, frontend (rodar em lotes pequenos — lotes grandes estouram o limite da sessão).
8. Documentação de fechamento: plano do mês (seção "mês 2"), `docs/PENDENCIAS_BUGS.md`, `CONTINUAR_DAQUI.md`, VERSION
   (o número da versão quem decide é o PC na publicação).

## 7. Como trabalhar aqui (lições desta sessão)

- Validar: `CGO_ENABLED=0 go build ./... && go vet ./... && go test ./...` (com `HERMES_TEST_PG` apontando para um banco
  com "test" no nome; na nuvem: `pg_ctlcluster 16 main start`, criar papel e banco `hermes_teste`) e
  `cd client && npx tsc --noEmit -p . && npx vite build`. Voz: `go test ./internal/voice/ -run Simulador`.
- Mexeu na voz/ligação → só fica "pronto" depois de ligação real (PC + dona); registrar em `docs/PEDIDOS_AO_PC.md`.
- Repositório PÚBLICO: nada de segredo nem telefone completo em arquivo novo.
- Cada correção: teste que falha sem ela, linha no CHANGELOG (seção "Próxima versão"), commit com o achado no título.
