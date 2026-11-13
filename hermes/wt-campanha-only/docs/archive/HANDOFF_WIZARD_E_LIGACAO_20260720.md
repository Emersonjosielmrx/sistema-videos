# Handoff — Hermes Call (2026-07-20, madrugada)

Para o próximo agente. Sessão longa da dona (Haylla). Backend Go em `cmd/server`,
front React em `client/src`. Go **não roda local** — só compila/testa na VPS via
`deploy/compile_check.js` (build) e `deploy/_run_test.js` (go test). Deploy: `deploy/deploy-beta.js`.
Beta no ar em https://hermescall.opus-sem-limites.com.br (build atual 20260720-0055).

## JÁ FEITO E DEPLOYADO (validar com a dona antes de promover a stable)

1. **Sistema de campanha v2** — 3 modos: imediato / paced (ao longo do dia, X/dia+X/min+horário,
   continua amanhã) / multi-linha (divide entre linhas, atrela nº→linha, redistribui se cai).
   Cadenciador em `campaign_scheduler.go` (ticker 1min). Config salva em `settings` (CampaignDefaults)
   + painel na aba Campanhas + pré-preenche MassCallPage. Botão obrigatório de modo ao disparar.
2. **Tipo A Telegram** — rajada: 3+ números seguidos em tempo curto viram campanha; bot pergunta
   modo por botões (paced/enfileirado/multi/single). `telegram.go` accumulateBurst/askBurstMode/runBurstCampaign.
3. **Tela preta** — ErrorBoundary (`client/src/components/ErrorBoundary.tsx`). Mostra erro em vez de apagar.
4. **Apagar campanha** — bug do user_id NULL (campanhas do sistema não apagavam) + front engolia erro. Corrigido.
5. **Aba Instâncias (TelephonyPage)** — era mock (Vapi/Camila); agora mostra linhas WhatsApp REAIS.
6. **Wizard Grupo 1** — data/hora do Brasil no prompt, ouvir áudio (Whisper) no chat, "digitando...",
   atraso humano, quebrar mensagem (autoreply_delivery.go). 4 toggles que morriam no front agora vão ao backend.
7. **Wizard Grupo 2** — temperature CHEGA na IA (era fake) + fallback de modelo real (agent_engine_extras.go).
8. **Handoff ligação AMBOS** — admin fixo + telefone do contato + adminNumber do perfil (handoff_smart.go).
9. **FIX CRÍTICO da linha** — `info()` reportava Connected sempre false (comparava com "connected", estado
   real é "open"). Isso fazia campanha abortar "linha caiu" mesmo conectada. Corrigido + reconecta antes de abortar.
10. **Botões de confirmação Telegram** — eram texto "/confirmar <código>" (dava erro); agora botões clicáveis.
11. **Amnésia do número** — número solto no Telegram agora vira memória da conversa (rememberMentionedNumber).
12. **Detecção inteligente de ligação** — regex flexível: sinônimos (disca/chama/telefona), substantivos
    (ligação/chamada), miolo variável, e "liga" sozinho usa o último número. Bateria call_intent_test.go 4/4 PASS.
13. **RAG híbrido** — vetor + full-text português (RRF) em Go/pgvector, SEM GraphRAG/Python (decisão da dona).
    rag_store.go SearchHybrid/SearchByUserHybrid, ligado em ragContextForUser + chat de teste.

14. **Binding de instância** (FEITO, build 0113) — perfil com instance_name SÓ ativa na linha
    que recebeu (session.go matchesInstance: casa por id/nome/número). Perfil sem instância = qualquer linha.
15. **Auto-treino reflexivo** (FEITO, build 0113) — ao CONVERTER (interested) numa ligação com
    autoTrain ligado, salva a transcrição no RAG do agente (source "auto-train"). broadcast.go maybeAutoTrain.

16. **Otimizar Prompt** (FEITO, build 0132) — botão do wizard agora chama /api/agents/refine (IA real
    reescreve o prompt); antes era setTimeout com texto fixo. EasyAgentWizard onClick.
17. **Formulários reais** (FEITO, build 0132) — aba "Dados Coletados" (CollectedDataTab) agora lê
    /api/contacts/collected (campos custom que a IA coletou, agrupados por contato) + busca + export CSV;
    era mockData. Backend: ContactExtrasStore.ListCollected + coluna updated_at em contact_custom_fields.

## PENDENTE (as peças grandes — a dona pediu "faz todas"; deixei pra fazer acordada por risco/dependência)

- **Upload de arquivo REAL no wizard etapa 4** — hoje é setTimeout fake. Precisa: endpoint que recebe o
  arquivo, chunka, embeda, grava no RAG. **PDF** exige lib Go nova (ex: ledongthuc/pdf) — não testei de
  madrugada. Escopo por agent_id.
- **Central de RAG estilo Dify** (GlobalRagManager.tsx é ~95% mock) — listar documentos, deletar, ver
  chunks, reindexar. Backend RAG existe (rag_api.go), falta os endpoints de listagem/chunks e ligar no front.
- **Webhook dinâmico (etapa 7)** — hoje vira só texto no prompt. Fazer: o agente chama o webhook, injeta
  o RESULTADO no prompt ANTES de responder (não depois). Ver agent_refine.go automations.
- **Formulários reais** — CollectedDataTab usa mockData. Fazer entidade de formulário + listagem real na
  subaba de Gestão de Leads. Toggles extractToForm/mandatoryCollection ainda são ignorados.
- **Binding de instância** — instance_name salva mas NÃO roteia. Fazer autoreply escolher o agente pela
  linha que recebeu, não só por trigger de texto.
- **Auto-treino reflexivo** — toggle autoTrain não faz nada. Fazer: ao converter, salvar o "golden argument"
  no RAG vinculado ao agente.
- **Ligação leve (RAG gracioso)** — a dona quer que na ligação, quando precisar buscar, a IA diga "só um
  momento, vou conferir" e busque async (Gemini), em vez de RAG síncrono pesado. Hoje: com Anthropic a
  ligação usa caminho não-streaming COM RAG (latência); com OpenAI-compat streaming pula RAG.
- **Otimizar Prompt (etapa 8)** — botão é setTimeout fake; o refine real só roda no save. Ligar ao endpoint real.

## COMO A DONA TRABALHA
- Português BR, direto. Modo autônomo de madrugada: continuar sozinho, testar, deployar isolado por lote.
- Cada lote: compile_check.js → deploy-beta.js → confirmar /api/version. Validar com ela antes de promote-stable.js.
- NÃO usar GraphRAG/Python (ela colou um prompt enterprise mas recusamos — Go single-binary, pgvector já basta).
- Confirmações/UX sempre por BOTÃO, nunca pedir código digitado.

## PRA TESTAR (dona) — build 0055
- Telegram: manda um número, depois só "liga" / "pode ligar" / "telefona pra ele" → deve ligar sem exigir formato.
- Ação sensível → toca no botão ✅ Confirmar (não digitar código).
- Linha está `connected:true` (JID 559184698653). Ligação testada = completed.
