# 05 — KnowledgeGaps + fill-gap + Auto-Evolução RAG (Shadowing)

**Esforço:** médio. **Impacto:** médio-alto (a base de conhecimento cresce sozinha).
**Depende do doc 02** (worker assíncrono). **Verificado:** `knowledge_gap`/`fill-gap`/`shadow_mode`
NÃO existem no código. O RAG base (pgvector, upload/search/ingest) JÁ existe (`rag_api.go`,
`rag_store.go`) — reusar, NÃO trocar por Pinecone/Qdrant (decisão firme: sem infra externa).

## Parte 1 — KnowledgeGaps (lacunas de conhecimento)
Quando o agente não soube responder algo (cliente perguntou preço que não está na base), o
sistema registra a lacuna e pergunta ao dono; a resposta vira conhecimento.

### Passo 1 — Tabela
Novo `cmd/server/knowledge_gaps_store.go`:
```sql
CREATE TABLE IF NOT EXISTS knowledge_gaps (
  id UUID PRIMARY KEY,
  user_id UUID NOT NULL,
  agent_id TEXT,
  question TEXT NOT NULL,       -- o que o cliente perguntou e a IA não soube
  context TEXT,                 -- trecho da conversa
  status TEXT NOT NULL DEFAULT 'open', -- open | filled | dismissed
  answer TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  filled_at TIMESTAMPTZ
);
```

### Passo 2 — Detecção (no worker do doc 02)
Na análise pós-conversa (mesmo gatilho da extração de promessas), pedir ao LLM: "Houve alguma
pergunta do cliente que o atendente não soube responder por falta de informação? Retorne JSON
`[{question, context}]` ou `[]`." Salvar cada uma em `knowledge_gaps` com `status='open'`.

### Passo 3 — Rotas
Registrar em `httpapi.go`:
- `GET /api/rag/gaps?status=open` → lista lacunas (handler novo em `rag_api.go`).
- `POST /api/rag/fill-gap` → `{gap_id, answer}`: pega a resposta, gera embedding e ingere no
  VectorDB do agente (REUSAR a função de ingestão que já existe em `rag_store.go`), marca
  `status='filled'`.

### Passo 4 — Frontend
"Card de Pergunta Pendente" (o mapa cita KnowledgeManagerTab/AgentRagPanel). Lista `/api/rag/gaps`;
input de resposta → `POST /api/rag/fill-gap`.

## Parte 2 — Auto-Evolução (Shadowing)
Flag no agente: quando uma conversa fecha como sucesso, extrai o melhor argumento e ingere no RAG.

### Passo 1 — Coluna no agente
`agentprofiles.go`: `ADD COLUMN IF NOT EXISTS auto_evolve BOOLEAN NOT NULL DEFAULT false`.
(O switch "Auto-Evolução" do AgentRagPanel — ver doc 01 item 7 — persiste aqui.)

### Passo 2 — No worker (doc 02)
Se `auto_evolve=true` e a conversa fechou com sucesso (venda/conversão), o worker:
1. Puxa o histórico da conversa.
2. LLM leve extrai "qual argumento converteu?" (destilação).
3. Chunk + embedding + ingestão no namespace do agente (`tenant_{id}_agent_{id}`), tag
   `golden_arguments` — REUSAR o pipeline de `/api/rag/ingest-conversations` que já existe.

### Passo 3 — RAG Reverso (correção do dono) — opcional
No painel, dono clica numa resposta errada e fornece a certa → ingere com peso alto no RAG do
agente. Rota `POST /api/rag/correct` `{agent_id, wrong, right}`.

## Verificação
- Rodar conversa onde a IA não sabe um preço → aparece card em `/api/rag/gaps`.
- Responder o card → `search` no RAG daquele agente retorna a resposta; próxima conversa a IA
  já sabe.
- Ligar `auto_evolve`, fechar uma venda → conferir chunk novo `golden_arguments` no RAG.

## Trade-offs
- Detecção custa tokens: rodar no worker async, LLM barato, só em conversas fechadas.
- Auto-evolução pode ingerir ruído — limitar a conversas marcadas sucesso e revisar
  periodicamente (o dono pode deletar chunks ruins via `/api/rag/documents`).
