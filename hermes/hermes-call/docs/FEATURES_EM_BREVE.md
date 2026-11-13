# Features marcadas "Em breve" — backlog de implementação

Levantado no QA de fluxo de 2026-07-24. São telas/botões que hoje mostram dados ou
controles que **não fazem nada** (mock hardcoded, sem backend). Foram marcados com selo
"Em breve" + desabilitados na UI pra não enganar cliente em demo. Aqui fica o que falta
pra cada um funcionar de verdade.

## Prioridade ALTA (o cliente espera que funcione)

### 1. Versionamento de agentes ("Reverter Versão")
- **Onde:** `client/src/components/settings/SpecializedAgents.tsx` (botão Reverter + dropdown v1.4/v2.1).
- **Estado hoje:** 100% mock — só `setTimeout` + toast "Restaurado (Mock)". Os números de versão são hardcoded.
- **Falta no backend:** tabela de snapshots de `agent_profiles` (ex.: `agent_profile_versions` com `profile_id, version, snapshot_json, created_at`). Endpoints `GET /api/agent-profiles/{id}/versions` e `POST /api/agent-profiles/{id}/revert/{version}`.
- **Esforço:** médio (nova tabela + 2 rotas + gravar snapshot a cada save).

### 2. Base de Conhecimento global (KnowledgeManagerTab)
- **Onde:** `client/src/components/settings/KnowledgeManagerTab.tsx` (view "knowledge").
- **Estado hoje:** 100% estático — "142 páginas indexadas", site `www.hipercool.com.br` fixo, botões Salvar/Sincronizar/Forçar Re-leitura/Remover sem ação.
- **Nota:** é DIFERENTE do `GlobalRagManager` (a aba "Base de Conhecimento" dentro de Funcionários IA, que usa RAG real). Este é um segundo componente órfão.
- **Falta no backend:** decidir se reaproveita o RAG existente (`/api/rag/*`) ou cria crawler de site. Se for só crawler de URL → ingestão no RAG, dá pra ligar no que já existe.
- **Esforço:** médio-alto (crawler) ou baixo (se só plugar no RAG existente).

### 3. Radar Ao Vivo / Copiloto (Modo Fantasma) na Telefonia
- **Onde:** `client/src/pages/TelephonyPage.tsx` (painel Radar + botão "Assumir/Handoff").
- **Estado hoje:** latência "120ms" hardcoded, transcrição/sugestão de IA fixas, botão Handoff sem ação.
- **Falta no backend:** stream de transcrição ao vivo da chamada em andamento + endpoint de handoff (assumir a chamada do agente IA). Depende da infra de chamadas (outro agente está mexendo em `internal/voip/call`).
- **Esforço:** alto (tempo real, depende do pipeline de voz).

## Prioridade MÉDIA

### 4. Listas Dinâmicas (Smart Lists)
- **Onde:** `client/src/pages/ListsPage.tsx` (modo "Lista Dinâmica").
- **Estado hoje:** seletor de regras ("Leads com Tag X", "inativos 30d") sem ação; cria lista vazia estática; promessa de "atualizada diariamente" é falsa.
- **Falta no backend:** conceito de lista por regra (query salva) + cron diário que reavalia. Tabela `contact_lists` precisa de coluna `rules_json` + motor de avaliação.
- **Esforço:** médio.

### 5. Regra de auto-tag por IA
- **Onde:** `client/src/pages/TagsPage.tsx` (campo `newTagRule`).
- **Estado hoje:** a instrução de IA digitada é descartada — `contact_tags` não tem coluna de regra; `CreateTag` ignora.
- **Falta no backend:** coluna `ai_rule TEXT` em `contact_tags`; estender `CreateTag(...,rule)` e `handleCreateTag` (features_api.go) pra ler `body.rule`; consumir a regra no motor de auto-tag (quando a IA classifica lead).
- **Esforço:** baixo-médio (coluna + leitura; o consumo no motor é a parte maior).

### 6. Usuário gestor / login de funcionário no Workspace
- **Onde:** `client/src/components/settings/WorkspaceSettings.tsx` (campos Email/Senha do gestor).
- **Estado hoje:** front manda `managerEmail`/`managerPassword`, backend (`projects_api.go`) ignora. Nenhum login com permissão reduzida é criado.
- **Falta no backend:** modelo de sub-usuários/permissões por workspace (RBAC). É uma feature de produto inteira (multi-usuário por conta). Relacionado ao pedido do dono sobre "endpoints de acesso pra configurar tudo no painel".
- **Esforço:** alto (auth multi-usuário + escopo de permissão).

### 7. Config rica do Gestor Fácil (superpoderes / árvore de agentes / openclaw)
- **Onde:** `client/src/components/settings/EasyManagerWizard.tsx` (etapas 3-5).
- **Estado hoje:** o núcleo (nome/prompt/motor/chave) agora carrega e salva de verdade via `/api/settings` (corrigido no QA). Mas os campos avançados (superpoderes, árvore de agentes, openclaw) não têm coluna no `AgentConfig`.
- **Falta no backend:** recompor `internal/settings.EasyManagerWizardConfig` (existe `cmd/server/easy_manager_settings.go` mas está com `+build ignore`), remover o build-ignore, e registrar `GET/PUT /api/easy-manager/wizard` no httpapi.go.
- **Esforço:** médio.

### 8. "Auto-Corrigir Guardrails" no Treinador
- **Onde:** `client/src/components/settings/AgentTrainerPanel.tsx`.
- **Estado hoje:** botão sem ação; o diff exibido é hardcoded ("frete grátis Norte/Nordeste"). O resto do Treinador (estimate/jobs/prompts) é real.
- **Falta no backend:** endpoint que roda análise dos guardrails e sugere correção. 
- **Esforço:** médio (depende de definir o que "auto-corrigir" faz).

---

## Já CORRIGIDO no QA de 2026-07-24 (não é backlog, só registro)
- Chat/Teste agora lista agentes reais (era mock "Agente de Teste UI").
- Meus Funcionários mostra lista real (era fallback de 3 mocks fixos).
- Gestor Fácil carrega e edita/substitui o gestor atual (era só toast).
- Base de Conhecimento (GlobalRagManager) popula o seletor de funcionários (lia campo errado da API).
- Filtro "Híbridos" corrigido (usava "hybrid", kind real é "both").
- Horário comercial, testar credencial IA, brand color, reset de sub-abas — ver rodada de fixes.
