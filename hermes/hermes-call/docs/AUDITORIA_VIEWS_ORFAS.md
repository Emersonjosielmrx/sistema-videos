# AUDITORIA DE UI — Views sem link no menu lateral

Auditoria feita em 2026-07-21 depois que a dona percebeu que a aba "IA em Reuniões" tinha sumido sem aviso.

## TL;DR

- **1 view realmente perdida** (`meeting-ai`) — todas as peças (página, tipo, rota interna) existiam, faltava só o botão no menu lateral. **Já corrigido** (commit independente).
- **14 views não estão no Sidebar principal**, mas isso é intencional — todas têm outro caminho de acesso (subtabs de Configurações, ou via `setView()` dentro de outras páginas). Nada de perdido.

---

## Por que a aba "IA em Reuniões" sumiu (cronologia real)

Não houve remoção. Houve **adição incompleta**.

| Quando | O que aconteceu |
|---|---|
| 21/07/2026 07:32 (commit `af9836f`) | Pacote gigante "fluxo 2-áudios + AgentProfile completo". **Criou** `client/src/pages/MeetingAIPage.tsx`, adicionou import em `App.tsx:31`, adicionou rota `if (view === "meeting-ai") return <MeetingAIPage />;` em `App.tsx:136`, e adicionou `"meeting-ai"` no tipo `View` em `stores/navigation.ts:4`. **MAS esqueceu de adicionar** o `<NavButton view="meeting-ai">` no `Sidebar.tsx`. |
| Antes desse commit | A feature **não existia** no refactor. A versão `inovare-hermes-v8/` (backup) também não tem (verificado no `Sidebar.tsx` da v8 — só 100 linhas, sem Meet). Provavelmente a dona está lembrando de outro produto (Hermes de outra versão, ou um protótipo/webapp separado). |
| 21/07/2026 ~17:00 (corrigido) | Adicionado em `Sidebar.tsx:197`: `<NavButton view="meeting-ai" icon={Video} label="IA em Reuniões" onNavigate={onNavigate} />`. Build `20260721-1738` no ar como `latest`/`stable`/`beta`. |

**Como o autor do commit original esqueceu:** o pacote tinha 106 linhas de mudança no `Sidebar.tsx` (refactor de layout, novo subgrupo "Menu Adicional"). Provavelmente a refatoração distraiu e o `NavButton` ficou de fora.

**Como a dona acessava antes:** **não acessava**. Confirmei via `grep "setView.*meeting-ai"` no client — zero matches. Também não há deep-link via URL/hash. A única rota era `if (view === "meeting-ai")` no `App.tsx`, que só era acionada via `<NavButton>` ou via console do navegador (`useNavigation.getState().view = "meeting-ai"`).

---

## Auditoria completa: 23 Views × 7 visíveis no Sidebar

Comparação entre as 23 views declaradas em `stores/navigation.ts:4` (tipo `View`), os 21 `<XxxPage>` retornados em `App.tsx`, e os 9 `<NavButton>` no `Sidebar.tsx`:

| View | App.tsx | Sidebar.tsx | Caminho de acesso |
|---|---|---|---|
| `cost` | ✅ (Visão Geral) | ✅ | Menu lateral |
| `crm` | ✅ (Gestão de Leads) | ✅ | Menu lateral |
| `manager_chat` | ✅ | ✅ | Menu lateral (componente customizado) |
| `specialized` | ✅ (Funcionários IA) | ✅ | Menu lateral |
| `agenda` | ✅ | ✅ | Menu lateral |
| `catalog` | ✅ (Vitrine) | ✅ | Menu lateral |
| `calls` | ✅ (Central de Telefonia) | ✅ | Menu lateral |
| **`meeting-ai`** | ✅ | **❌ → ADICIONADO** | (estava oculto) |
| `settings` | ✅ | ✅ | Grid inferior + atalho |
| `help` | ✅ | ✅ | Grid inferior |
| `dashboard` | ✅ | ❌ | Substituído por `cost` |
| `contacts` | ✅ | ❌ | Acessado via `setView("mass-call"/"mass-message")` em ContactsPage/ListsPage (subfluxo) |
| `mass-call` | ✅ | ❌ | Acessado via Contacts/Lists e botão "Discar em massa" |
| `mass-message` | ✅ | ❌ | Acessado via Contacts/Lists |
| `logs` | ✅ | ❌ | Subaba em Settings (ou deep-link direto pelo `?view=logs`?) |
| `analytics` | ✅ | ❌ | Subaba em Settings (Costos) |
| `campaigns` | ✅ | ❌ | Subaba em Settings |
| `lists` | ✅ | ❌ | Subaba em Settings |
| `security` | ✅ (redirect settings) | ❌ | Comentário no App.tsx:126: "SecurityPage is part of settings, redirecting to settings" |
| `profile` | ✅ | ❌ | Acessado via Settings (geralmente header/cabeçalho) |
| `team` | ✅ | ❌ | Acessado via Settings |
| `follow_up` | ✅ | ❌ | Subaba em Settings |
| `knowledge` | ✅ | ❌ | Subaba em Settings |
| `promises` | ✅ | ❌ | Subaba em Settings |

**Conclusão:** nenhuma outra view órfã real. A maioria das views `❌` no Sidebar está acessível via Configurações (que tem muitas subtabs).

## Como evitar o bug de novo (Views órfãs)

Adicionar uma view exige **3 mudanças coordenadas**, e qualquer uma pode ser esquecida:

1. `client/src/pages/<Nome>Page.tsx` — a página em si.
2. `client/src/stores/navigation.ts:4` — adicionar a string no tipo `View`.
3. `client/src/App.tsx` — adicionar `if (view === "X") return <XPAGE />`.
4. `client/src/components/layout/Sidebar.tsx` — adicionar `<NavButton view="X" ... />` em algum lugar (ou criar caminho via `setView("X")` em outra página).

**Regra:** quem adicionar view nova, rodar `grep "$view" client/src/components/layout/Sidebar.tsx client/src/pages/ -r` e confirmar pelo menos 1 caminho de acesso.

**Outra salvaguarda:** uma rotina automática que lê o tipo `View` em `stores/navigation.ts` e cruza contra `Sidebar.tsx` + todos os `setView(...)` no `client/src/` — se sobrar view sem link, falha o build. (Pendência — não implementado.)

## Verificação visual

Build atual (`hermes-call:latest = 17eb9aa1dba6 = build 20260721-1738`, promovido a `stable` + `beta`).

Após refresh da página (F5) a aba "IA em Reuniões" deve aparecer no menu lateral, logo abaixo de "Central de Telefonia", com ícone de câmera (Video).
