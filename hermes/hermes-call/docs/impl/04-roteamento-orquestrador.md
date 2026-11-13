# 04 — Roteamento por Níveis (1/2/3) + Orquestrador Executor

**Esforço:** ALTO (feature grande, arriscada — mexe no coração do atendimento). **Impacto:** alto.
**Fazer por último.** Dividir em fases; validar cada uma ao vivo.

## Estado REAL hoje (verificado no código)
- **Roteamento de texto:** `autoreply.go:349-394` faz um match SIMPLES — procura um agente
  especializado cujo `trigger` (texto ou etapa do funil) bate na mensagem. Não há os níveis
  1/2/3 do doc, nem `logic_type`, nem `priority`, nem triador por IA.
- **Swarm na ligação:** `transfer_to_agent` JÁ EXISTE e funciona (`aiagent.go:1028`,
  `doTransferToAgent` troca o perfil da ligação ativa via `SetProfile`). Ou seja, o hot-swap
  de agente na voz é real.
- **Orquestrador (canvas):** `orchestrator_api.go` guarda SÓ o desenho (nodes/edges em
  `orchestration_flows`). O próprio arquivo diz "ESCOPO HONESTO: persistimos o DESENHO... a
  EXECUÇÃO do fluxo [não está aqui]". **Não há motor que execute o grafo.**

## Colunas/campos que faltam (spec BACKEND_ROUTING_SPECS)
Em `agent_profiles` (migrations aditivas em `agentprofiles.go`, padrão dos `ADD COLUMN IF NOT EXISTS`):
```sql
ADD COLUMN IF NOT EXISTS logic_type TEXT NOT NULL DEFAULT 'none';  -- none|tag|stage|time|contains|exact|similar
ADD COLUMN IF NOT EXISTS ai_trigger TEXT NOT NULL DEFAULT '';       -- instrução semântica pro triador
ADD COLUMN IF NOT EXISTS priority TEXT NOT NULL DEFAULT 'rule_first'; -- rule_first|ai_first
```
Já existe `trigger` (o valor da regra). No settings do tenant (bloco novo `routing`):
```
default_voice_agent_id, default_text_agent_id, single_agent_mode(bool),
routing_level(1|2|3), routing_hierarchy[] (ex.: ['time','stage','tag','exact','contains','similar'])
```

## Fase A — Nível 1 (Direct Mapping) — MENOR risco, fazer primeiro
- Settings: `default_voice_agent_id`, `default_text_agent_id`, `single_agent_mode`.
- No `autoreply.go` (texto) e no início da ligação (broadcast.go): se `routing_level==1`,
  roteia direto pro agente default do canal. Fim.
- **Pronto quando:** dá pra escolher no painel 1 agente pra voz e 1 pra texto, e o sistema respeita.

## Fase B — Nível 2 (Regras / Kanban) — médio
- Implementar o engine de decisão (novo `cmd/server/routing.go`):
  1. Varre agentes ativos do tenant.
  2. Para cada um, avalia `logic_type` contra o contexto:
     - `time` → hora do servidor vs `trigger` (ex.: "08:00-18:00").
     - `tag`/`stage` → consulta `contact_leads`/tags do lead.
     - `contains`/`exact`/`similar` → compara com a última mensagem.
  3. Respeita a ordem de `routing_hierarchy`.
- Integrar em `autoreply.go` (substituir o match simples atual quando `routing_level>=2`).
- **Pronto quando:** um lead com tag "vip" cai no agente configurado pra "vip", etc.

## Fase C — Nível 3 (Triador IA + conflito) — maior
- Triador: manda a mensagem + os `ai_trigger` dos agentes pro LLM (Groq/Gemini), pede JSON
  com o `agent_id` ideal (padrão de chamada LLM já existe em agent_wargame.go).
- Resolução de conflito: se regra estática e IA divergem, usa `priority` (`rule_first`/`ai_first`).
- **Orquestrador executor:** ligar o grafo salvo em `orchestration_flows` a este engine —
  cada node = um agente/condição, cada edge = transição. Estado de execução por conversa
  (nova tabela `orchestration_runs` se precisar). Reusar `transfer_to_agent` que já existe.
- **transfer_mode** (`full_memory`|`summary`) e **modo silencioso/explícito**: já há base no
  swarm da ligação; estender pro texto.

## Trava de segurança (regra de ouro do doc)
Só UM nível ativo por tenant/canal por vez — o backend impõe. Sem isso, múltiplos agentes
respondem a mesma mensagem (loop). Guardar `routing_level` no settings e checar no topo do
roteador.

## Verificação
- Fase A: configurar default e ver 1 agente atender tudo.
- Fase B: criar 2 agentes com tags diferentes, mandar msg de leads distintos → cada um no seu.
- Fase C: cenário onde regra e IA divergem → confirmar que `priority` decide; testar hot-swap
  no meio da conversa sem perder contexto.

## Trade-offs / riscos
- É o ponto mais sensível do sistema (todo atendimento passa por aqui). Fazer atrás de flag
  `routing_level` — nível 1 é o default seguro; 2 e 3 opt-in.
- Não quebrar o match por `trigger` atual enquanto `routing_level` não for setado.
- Triador IA custa tokens e latência — cachear decisão por conversa quando possível.
