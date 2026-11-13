# Plano de testes MAIS detalhados — Hermes Call (rodada 4)

Base: rodadas 1-3 cobriram CRUD, concorrência, planos, segurança (SQLi/XSS/IDOR/mask), fuzzing, consistência back↔front. Achados corrigidos: #N4 (crítico, v0.3.2), #R1/#R2 (preço, v0.3.3), #R6 (id UUID, v0.3.4). Esta rodada vai FUNDO em fluxos compostos, estados intermediários e integração real.

## Bloco H — Fluxos compostos multi-etapa (state machines)
Não só endpoints isolados — sequências onde o estado de um passo afeta o próximo.
- [ ] Agente completo: criar → anexar RAG doc → configurar voz → testar → editar → arquivar. Verificar que cada passo vê o estado do anterior.
- [ ] Campanha: criar lista → adicionar contatos → criar campanha da lista → checar status → pausar → retomar → arquivar.
- [ ] CRM funil: criar etapa → mover lead A→B→C → verificar histórico → converter lead → checar métricas.
- [ ] Agenda: criar profissional → criar horário → agendar → remarcar → cancelar → verificar disponibilidade liberada.
- [ ] Onboarding: registro → wizard setup → primeiro agente → primeira config. Cada etapa persiste?

## Bloco I — Consistência de dados / integridade referencial
- [ ] Deletar agente que tem RAG docs → os docs somem junto (cascata) ou viram órfãos?
- [ ] Deletar lista usada por campanha ativa → o que acontece com a campanha?
- [ ] Deletar credencial usada por agente → agente quebra ou faz fallback?
- [ ] Deletar etapa CRM com leads dentro → leads vão pra onde?
- [ ] Deletar produto referenciado como upsell de outro → dangling reference?
- [ ] Contadores (total_count, pending_count) batem com a realidade após create/delete?

## Bloco J — Idempotência e reprocessamento
- [ ] Salvar settings 2x seguidas com mesmo payload → sem efeito duplicado
- [ ] Aplicar cupom 2x → segunda vez rejeita ou é idempotente?
- [ ] Reenviar webhook test em sequência → sem acúmulo
- [ ] Toggle liga/desliga rápido (agent_chat.enabled) → estado final consistente

## Bloco K — Limites reais de plano (enforcement de quantidade, não só tabs)
- [ ] start_texto: MaxAgents=3 → criar 4º agente deve bloquear (403/400)?
- [ ] MaxInstances por plano → criar linha além do limite
- [ ] MonthlyTokens → o que acontece ao estourar (bloqueia/avisa)?
- [ ] trial 10h → simular expiração e ver se bloqueia

## Bloco L — Formato/encoding de dados
- [ ] Telefones: com/sem +55, com espaços, com traços, formato E.164 → normalização consistente?
- [ ] Datas: timezones diferentes, DST, ISO vs timestamp → agenda mostra hora certa?
- [ ] Moeda: centavos, vírgula vs ponto, arredondamento
- [ ] Arrays (tags, chat_ids, events): duplicatas, vazios, ordem preservada?
- [ ] Campos JSONB (extras do agente, custom_alerts) → round-trip preserva estrutura?

## Bloco M — Erros e recuperação
- [ ] Requisição que falha no meio (timeout simulado) → estado parcial ou atômico?
- [ ] Token expira DURANTE uma sessão longa → renova ou erro limpo?
- [ ] Backend reinicia com sessões ativas → recupera estado (sessions restored)?
- [ ] Payload que passa validação mas falha no banco → erro tratado, não 500 cru?

## Bloco N — Auditoria de código (padrões repetidos)
Buscar sistematicamente os padrões de bug já achados em TODO o código:
- [ ] Outras colunas nullable escaneadas em string (como #N4) — com sintoma real
- [ ] Outros erros de DB vazando como 500 (como #R6) em queries com cast
- [ ] Outros handlers `, _ :=` que engolem erro relevante
- [ ] Validação de range faltando (como #R1/#R2) em outros campos numéricos

## Bloco F (pendente da rodada 3) — E2E pela UI (Playwright + visão)
- [ ] Onboarding visual completo, wizard 9 etapas, navegação 24 views, toasts

## Dependências
- Chave Gemini COM cota desbloqueia: RAG real, simulação IA, embeddings, e vários fluxos do Bloco H/I.
- WhatsApp pareado (impossível em trial) limita: envio real, campanhas de verdade — só testar guards.

## Log de execução
(preenchido conforme roda)
