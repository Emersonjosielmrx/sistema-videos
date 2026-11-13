# ⛔ LEIA ANTES DE CRIAR OU MEXER EM QUALQUER TELA (Agente Frontend)

> Este arquivo é OBRIGATÓRIO pro agente que faz o frontend. Se você vai criar uma tela,
> um botão, um wizard ou qualquer coisa que precise de dado do servidor, **você tem que
> deixar o backend documentado e pronto pra implementar** — do jeito que está descrito aqui.
> Um front bonito com botão que só dá `toast` é DÍVIDA, não entrega. A dona vê "dado falso"
> e perde a confiança. Cada tela que você entrega tem que vir com o "pedido de backend" pronto.

---

## A REGRA DE OURO
**Nunca finja que funciona.** Se o dado não vem do backend ainda, uma das duas:
1. Mostra estado vazio HONESTO ("sem dados ainda") — nunca número inventado.
2. Marca como "em breve" (botão desabilitado) — nunca botão que só dá toast fingindo salvar.

E SEMPRE registra o que o backend precisa fazer, no formato deste guia.

---

## POR QUE (o problema que já aconteceu neste projeto)
- Dashboard mostrava sentimento 40/35/15/10 **fixo** — mas o backend JÁ mandava o dado real,
  o front só ignorava. (ver `docs/impl/01-easy-wins-frontend.md`)
- EasyManagerWizard tem **588 linhas** e o `handleSave` só faz `toast.success` — a config do
  gestor **nunca** foi salva. O usuário preenche e perde tudo ao recarregar.
- Vários docs de backend viraram MENTIRA porque a feature mudou de nome/lugar e ninguém
  atualizou. **Doc que não bate com o código é pior que doc nenhum.**

Essas três coisas custaram dias de retrabalho. Este guia existe pra não repetir.

---

## AS 8 REGRAS

### Regra 1 — Antes de criar, CONFIRA se o backend já existe
Não invente rota nova sem checar. O backend tem ~300 rotas — a que você precisa talvez já exista.
- Como: procure a rota em `cmd/server/httpapi.go` e o contrato em `docs/_MAPA_BACKEND_EXISTENTE.md`.
- Se existe → só consuma. Se não existe → você vai documentar o pedido (regra 3).
- ❌ Errado: criar `/api/minha-tela/dados` sem olhar que já existe `/api/dashboard`.

### Regra 2 — Toda tela declara suas rotas no topo do arquivo
No comentário de cabeçalho do componente, liste as rotas que ele consome e o status de cada:
```tsx
// ProdutosPage.tsx
// Backend consumido:
//   GET  /api/catalog/products        🟢 existe
//   POST /api/catalog/products        🟢 existe
//   POST /api/catalog/ai-description  🟢 existe
//   GET  /api/catalog/insights        🔴 NÃO EXISTE — pedido em docs/impl/06-catalog-insights.md
```
Legenda: 🟢 existe e ligado · 🟡 existe mas ainda não liguei · 🔴 falta backend.

### Regra 3 — Rota que falta vira um "Pedido de Backend" (arquivo em docs/impl/)
Se a sua tela precisa de algo que o backend não tem, crie/edite um doc em `docs/impl/`
seguindo EXATAMENTE este template (foi assim que os docs 01-05 foram feitos):

```markdown
# NN — Título curto da feature

**Esforço:** baixo|médio|alto. **Impacto:** ... **Depende de:** (outro doc, ou "nada").
**Verificado no código:** (o que você confirmou que NÃO existe — cole o grep que provou).

## Onde no front
- Arquivo:linha do componente que vai consumir.

## Contrato do endpoint (o que o front manda e espera)
- MÉTODO /api/rota
- Request body (JSON com exemplo real):
- Response esperada (JSON com exemplo real):
- Erros: {error:"..."} + status.

## Schema (se precisa tabela/coluna nova)
```sql
CREATE TABLE IF NOT EXISTS ... (aditivo)
ALTER TABLE ... ADD COLUMN IF NOT EXISTS ...
```

## Passo a passo backend (Go)
1. store novo em cmd/server/xxx_store.go (espelhe crm_store.go)
2. handler em cmd/server/xxx_api.go (espelhe crm_api.go)
3. registrar a rota em cmd/server/httpapi.go
4. ...

## Como testar (pronto quando)
- Critério objetivo de aceite.
```

### Regra 4 — Dê o CONTRATO com exemplo real, não descrição vaga
O backend não pode adivinhar. Sempre JSON de exemplo dos dois lados.
- ❌ Errado: "endpoint que retorna as métricas do lead".
- ✅ Certo:
  ```
  GET /api/contacts/leads/{jid}/timeline
  Response: {"events":[{"type":"call","status":"completed","at":"2026-07-21T10:00:00Z","note":"..."}]}
  ```

### Regra 5 — Aponte o arquivo/linha exatos (do front E do backend a espelhar)
Uma IA menos capaz precisa de âncora concreta, não de "em algum lugar do broadcast".
- ✅ "consumir em `DashboardPage.tsx:415-431`", "espelhar o store de `crm_store.go:63`",
  "registrar rota em `httpapi.go` junto das outras `/api/crm/*`".

### Regra 6 — Reusar > criar. Diga o que reaproveitar.
Se já existe pipeline/store/pattern parecido, mande o backend REUSAR e cite o arquivo.
- Ex.: "pra ingerir no RAG, REUSE a função de `/api/rag/ingest-conversations` (rag_store.go),
  não escreva embedding do zero." · "migrations aditivas, padrão dos `ADD COLUMN IF NOT EXISTS`
  em agentprofiles.go." · "cron novo? espelhe scheduled_calls_cron.go."

### Regra 7 — Honestidade sobre "persistir ≠ executar"
Se o backend vai só GUARDAR a config mas o motor ainda não USA, diga isso no doc E no UI.
- Ex. real: os toggles Deep Tech do wizard do gestor — persistir o valor, mas marcar "em breve"
  no UI enquanto o motor não executa. Nunca um toggle ligado que não faz nada.

### Regra 8 — Atualize o doc quando MUDAR (senão ele vira mentira)
Se você renomear a rota, mudar o payload ou mover a tela, **atualize o doc na mesma hora**.
Doc desatualizado foi a causa raiz do retrabalho neste projeto. Se removeu a feature, apague
o doc dela (ou marque `[REMOVIDO]` no topo).

---

## CHECKLIST DE ENTREGA (antes de dizer "terminei a tela")
- [ ] `cd client && npx vite build` passou.
- [ ] Nenhum dado inventado na tela (ou é vazio honesto / "em breve").
- [ ] Nenhum botão que só dá `toast` fingindo ação.
- [ ] Cabeçalho do componente lista as rotas consumidas com 🟢🟡🔴 (regra 2).
- [ ] Toda rota 🔴 tem um doc em `docs/impl/NN-*.md` com contrato + exemplo + schema + passo a passo.
- [ ] Docs que eu mexi hoje batem com o código (regra 8).
- [ ] Atualizei o índice `docs/impl/00-INDICE.md` se criei um doc novo.

---

## MODELO MENTAL
Você (frontend) é o cliente do backend. Entregue um "pedido" que qualquer dev — ou uma IA
mais simples — consiga cumprir sem te perguntar nada: **o quê, onde, com que dado, espelhando
o quê, e como saber que ficou pronto.** Se o seu pedido gera dúvida, ele está incompleto.

> Exemplos reais de pedidos bem-feitos: leia `docs/impl/02-worker-promessas.md` e
> `docs/impl/05-knowledge-gaps-rag.md`. Copie aquele nível de detalhe.
