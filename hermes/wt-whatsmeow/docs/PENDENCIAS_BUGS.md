# Pendências de bugs: inventário consolidado

Revisão de **todos** os relatórios de bugs do projeto (lista das fontes no fim), conferindo
cada item no código. Atualizado em 24/09/2026, na v0.5.0; seção 6 em 04/10/2026.

Legenda: ✅ resolvido · 🟠 aberto · 🟡 menor/aceito · 👤 depende da dona · ℹ️ não era bug

## 1. Segurança

| Item | Estado |
|---|---|
| Produção sem `HERMES_JWT_SECRET` (login forjável) | ✅ segredo definido na VPS (drop-in `/etc/systemd/system/hermes-call.service.d/10-segredos.conf`). O servidor recusa subir sem ele |
| Apagar/deslogar/parear linha de outro cliente | ✅ v0.5.0 |
| Entrar na ligação de outro cliente (ponte) | ✅ v0.5.0 |
| Vitrine pública vazando erro do Postgres | ✅ v0.5.0 |
| Cadastro criando conta com plano pago de graça | ✅ v0.5.0 (sempre nasce em teste) |
| Porta 8080 aberta na internet (sem TLS, fora do Traefik) | ✅ fechada no ufw (backup das regras em `/opt/hermes-call/releases/config-backups/`) |
| `X-Forwarded-For` falsificável | ✅ resolvido com a porta fechada (o Traefik sobrescreve o cabeçalho) |
| Lista de IPs: salvar apagava, e nunca era aplicada | ✅ v0.5.0 (aplicada por conta; lista vazia = desligada) |
| Conta "desativada" continuava entrando | ✅ v0.5.0 |
| Agenda: JSON montado à mão com a chave da URL; status livre | ✅ v0.5.0 |
| Webhook do Asaas aceita sem token (`HERMES_ASAAS_WEBHOOK_TOKEN` vazio) | 👤 definir o token na VPS **e** no painel do Asaas, juntos |
| Tokens e senhas escritos em docs e colados no chat (GitHub, Docker Hub, senha root, token Telegram, chave Groq) | 👤 revogar e trocar |
| JWT na URL do áudio e do canal de eventos | 🟡 limitação do navegador (só cookie resolveria) |
| `/recordings/{id}` público (o id funciona como senha) | 🟡 aceito |
| CORS `*`, sem HSTS/nosniff | 🟡 baixo risco (autenticação por token, não por cookie) |

## 2. Cobrança

| Item | Estado |
|---|---|
| Cadastro não gerava cobrança | ✅ gera, se o Asaas estiver configurado |
| Pagamento não aplicava o plano | ✅ webhook e "verificar" aplicam |
| Start virava teste de 10h mesmo pago | ✅ |
| Cobrança vencida não bloqueava | ✅ bloqueia após 5 dias (contas sem assinatura são isentas) |
| Tela de teste vencido apontava para domínio fora do ar | ✅ assina dentro do app |
| **Asaas não configurado na produção** (`HERMES_ASAAS_API_KEY` ausente) | 👤 sem a chave, ninguém consegue pagar online; a tela avisa "indisponível" |
| Assinaturas de contas de teste continuam cobrando no Asaas | 👤 cancelar no painel do Asaas. As 166 contas de teste foram desativadas no app |

## 3. Ligações e voz (relatório de 28/ago)

| # | Item | Estado |
|---|---|---|
| 1 | Ligações agendadas 100% falhando (voz) | ✅ |
| 1b | Promessas criadas de qualquer mensagem e com LID | ✅ |
| 1c | Retorno de ligação perdida com a mesma falha de voz | ✅ |
| 2 | Eco da IA transcrito como cliente | ℹ️ já existia proteção (fator 3.5 + cauda de 300 ms). Validar numa ligação real |
| 3 | Agente nunca dava preço | ✅ preços oficiais na base do agente "Vendas Hermes Call" |
| 4 | 286 números presos na fila | ✅ rotina fecha os de campanha encerrada |
| 5 | Abertura longa, conversas curtas | 👤 texto de abertura é escolha comercial |
| 6 | Bitrate baixo das gravações | 🟡 |
| 8 | Classificação contraditória | ✅ |
| — | Limite anti-ban é só aviso | ✅ decisão mantida + piso de 20s em rajada |
| — | Discador "sempre sem gravar" | ℹ️ o servidor ignora o campo; a gravação segue a linha (ligada) |

## 4. Painel

| Item | Estado |
|---|---|
| Correções de 02/ago (menos as 5 perdidas) | ✅ |
| 5 perdidas na junção (#6, #8, #10, #14; #16 não se perdeu) | ✅ recuperadas |
| Visão Geral com 0 fixo | ℹ️ já era real; ✅ removidos a curva inventada e os 6 min fixos |
| Copiloto com texto fixo | ✅ vira "em breve" |
| Garimpo: Sincronizar / Marcar como lido | ✅ |
| Bloqueio com prazo; desbloquear sem confirmação | ✅ |
| Agenda: conflito ao editar, calendário, Dossiê IA, link /book | ✅ (link público marcado "em breve") |
| Duplicar agente; "reverter versão" falso | ✅ |
| Roteamento Nível 1 | ✅ mensagens · ✅ ligações recebidas (agente das ligações, desde a v0.6.0; sem agente, recepcionista padrão na v0.8.0) · ℹ️ na campanha quem escolhe o agente é a campanha |
| Logo trocando o papel | ✅ |
| Canal de eventos sem reconexão | ✅ |
| Esqueci minha senha | ✅ via suporte no WhatsApp · 🟠 automático exige e-mail/linha de envio |
| Base de conhecimento global (RAG) com dados de exemplo | 🟠 |
| CRM: valor por etapa, presença, Lead Score decorativos | 🟡 |
| Superpoderes/ferramentas do Gestor sem comportamento real | 🟠 feature grande |
| ≈150 itens menores (acessibilidade, performance, textos) do `docs/archive/_ACHADOS_NOTURNOS.md` | 🟡 triagem em 05/10: `docs/archive/ACHADOS_JULHO_TRIAGEM_2026-10-05.md`. Os de gravidade alta conferidos à mão já estavam corrigidos; os médios e baixos precisam ser conferidos um a um antes de mexer |
| Testes Go antigos que não compilam | 🟠 |

## 5. Incidente de 24/09

Ao reiniciar para aplicar o segredo JWT, o programa antigo **apagou os bancos de 3 linhas de
WhatsApp desconectadas** (inclusive a linha admin 559184074247) e com eles o histórico de
mensagens. CRM, contatos, campanhas e transcrições ficam no banco principal e não foram
afetados. A v0.5.0 arquiva em vez de apagar. Ao reconectar a linha, o WhatsApp reenvia parte do
histórico (HistorySync, que agora é importado).

## 6. Achados de 04/10 e 05/10 (v0.8.0/v0.8.1, no ar desde 05/10)

| Item | Estado |
|---|---|
| Salvar Voz / IA / IA da ligação / Gestor apagava credenciais do cofre, "interromper a IA" e "só ativo" | ✅ `058a563` (leitura completa + servidor só troca o que veio) |
| Botão "Modo Retorno de Campanha" não fazia nada (opção desconhecida do servidor) | ✅ `8dc6b08` virou aviso no Telegram quando o lead responde |
| "Exportar CSV" dentro da campanha baixava o resumo de todas as campanhas | ✅ `8dc6b08` exporta os contatos com o filtro da tela |
| 4 vazamentos entre contas (diagnósticos, envio em massa, Chatwoot, chaves ElevenLabs) | ✅ `accb782`, `c987889` |
| IA reagia a som antes do aceite da ligação | ✅ `2f1154c` · 👤 confirmar numa ligação real |
| CI falhando "de vez em quando" (chave primária conferida no banco inteiro) | ✅ `0819cdd` |
| Aceite da ligação RECEBIDA não reconhecido pelo WhatsApp | 🟠 captura de um celular feita em 05/10 (`docs/ensaios/2026-10-05_1138_ligacao-humana.md`); peças novas 8/16/32 na bancada (`2e96eaf`); falta testar com a dona ligando de um celular para o 8288 |
| Depois de interrompida, a IA recomeçava a resposta (preço dito 3 vezes, 05/10) | ✅ no código (memória guarda o que foi ouvido inteiro; `TestTurno_BargeInGuardaOQueFoiOuvidoInteiro`) · 👤 confirmar numa ligação |
| "Qualidade do áudio" dizia "com cortes" em ligação boa (silêncio do cliente e fim de fala contavam) | ✅ no código (`Verdict()`, limite do envio 400 ms) |
| Ligação não atendida que termina sem aviso ao aparelho do servidor fica "tocando" até o vigia de 6 min (sem retorno) | 🟠 visto 5 vezes em 05/10 (quem desistiu foi a bancada ou o celular chamado); não acontece com cliente de verdade ligando |
| **A VPS da produção engasga**: pausa qualquer processo por 100–250 ms várias vezes por segundo (as outras duas VPS não). É o hospedeiro, não o Hermes | 🔴 medido em 06/10 (`docs/ensaios/2026-10-06_1246_ligacao-picotada.md`). Decisão da dona: reclamar com o provedor ou mudar o Hermes de máquina |
| Fala e gravação picotadas quando o servidor engasga (ligação de 06/10 12:46) | ✅ no código (ritmo por prazo, silêncio de manutenção com 300 ms, gravação montada em sequência); **falta ligação de verdade e publicar** |
| Resposta à isca perdida quando o Whisper inventa texto (descartado → vazio) e a oferta de 23 s toca assim mesmo | 🟡 visto 1 vez em 05/10 |
| O RESUMO do `ensaio.sh` conta como "latência" o tempo em que a isca e a oferta tocam | 🟡 ler as linhas, não a média |
| Tempo de resposta ~3,0 s (meta 2,5 s) | 🟡 medido em ligação real (05/10): 3,3 s na 1ª resposta, depois 1,7 a 2,1 s. Falta só a 1ª resposta |
| `promises_api.go`, `promises_cron.go`, `rag_api_extras.go` desligados (`// +build ignore`) | 🟡 extração de promessas e lacunas da base não roda; usam o modelo `llama-3.1-8b-instant`, que o Groq aposentou. Revisar antes de religar |

## Fontes lidas
`RELATORIO_ANALISE_HERMES_2026-08-28.md`, `HISTORICO_CONVERSA_COMPLETO_2026-08-28.md`,
`docs/archive/CORRECOES_PENDENTES_2026-08-01.md`, `docs/archive/CORRECOES_2026-07-27.md`,
`docs/archive/CORRECOES_2026-07-28.md`, `docs/archive/RELATORIO_NOTURNO_2026-07-31.md`,
`docs/archive/_CORRECOES_AUDITORIA_2026-07-29.md`, `docs/archive/_ACHADOS_NOTURNOS.md`,
`docs/archive/_PLANO_CORRECOES_2026-07-25.md`, `docs/archive/_CORRECOES_LOG.md`,
`docs/archive/_BUGS_v0.2.1_A_CORRIGIR.md`, `docs/archive/BOTOES_MORTOS_E_DADOS_FAKE_2026-07.md`,
`docs/QA_PAINEL_E_METRICAS.md`, `docs/archive/RELATORIO_QA_12H.md`, `docs/archive/FIX-FRONT-1.md`,
`docs/AUDITORIA_VIEWS_ORFAS.md`, `RELATORIO_HERMES_2026-07-22.md`,
`CORRECOES_HERMES_2026-07-22_v2.md`, `docs/archive/STATUS_E_PROBLEMAS.md`.
