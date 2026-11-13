# QA Hermes Call — simulação de cliente na UI

Suite que **simula um cliente real** no painel do Hermes Call: cria conta, loga, navega por todas as abas, clica nos botões principais e usa um modelo de **visão (Gemini)** pra julgar se cada tela/ação fez de fato o que deveria — não só se o elemento existe.

Projeto isolado, fora dos apps de produção. Nada aqui escreve em produção além de **criar contas trial descartáveis** (marcadas `qa_*@qa-hermes.test`) pelo fluxo público de cadastro.

## Stack (por que cada peça)

- **Playwright** (`@playwright/test`) — dirige o Chrome de verdade, clica/preenche como cliente, tira screenshot de cada passo, roda headless. Reaproveita os browsers já em cache em `%LOCALAPPDATA%\ms-playwright` (não baixa de novo).
- **Verificação semântica via Gemini** — Playwright puro só checa mecânica (elemento existe, texto bate). Pra julgar *"esse botão fez o certo?"* mandamos o screenshot + a expectativa pro Gemini e ele responde pass/fail. Ver `lib/vision.ts`.

Pesquisei alternativas com IA embutida (Midscene.js, Stagehand, browser-use). Midscene seria o encaixe "puro", mas exige chave de modelo com visão e adiciona dependência. Optamos por **Playwright + chamada direta ao Gemini** porque reaproveita o que já existe na máquina e mantém a parte mecânica determinística (grátis), usando IA só onde precisa julgar.

## Como rodar

```bash
cd D:/qa-apps/hermes-call
npm install                 # instala @playwright/test (browsers já em cache)
npx playwright test         # headless, gera reports/html
npm run report              # abre o relatório HTML
npx playwright test --headed  # ver o robô clicando ao vivo
```

Variáveis (opcionais):

| Env | Default | Pra quê |
|-----|---------|---------|
| `HERMES_QA_URL` | `https://hermescall.inovareinteligenciaartificial.com` | URL do painel |
| `HERMES_QA_VISION` | `1` | `0` desliga a IA (só checagem mecânica) |
| `HERMES_QA_VISION_MODEL` | `antigravity/gemini-2.5-flash` | modelo de visão |
| `HERMES_QA_VISION_URL` | `http://157.173.207.22:20128/v1` | endpoint do proxy |

## Escopo de contas (importante)

O cadastro **público** só deixa criar conta **trial**:
- `start_texto` / `start_voz` → o backend rebaixa pra `trial` calado;
- `pro` / `scale` → exigem CPF e mandam pro checkout do Asaas (pagamento real);
- há **rate-limit** de cadastro por IP ("aguarde alguns minutos").

Como o **trial libera TODAS as abas**, a suite cobre a navegação inteira mesmo só com trial. Testar o *gating* específico de cada plano pago exigiria semear contas no banco de produção — decisão do dono foi **não tocar produção**, então isso fica de fora.

A conta trial criada é cacheada em `.account-cache.json` e reusada entre runs (evita bater no rate-limit toda hora). Se o token expirar (trial dura 10h), a suite cria outra.

## Dependências externas (documentado caso algo suma)

- **Proxy OmniRoute** — `http://157.173.207.22:20128/v1`, OpenAI-compat, **sem auth**, responde em SSE. Modelos de visão: `antigravity/gemini-2.5-flash`, `antigravity/gemini-3.1-pro-low`, `auto/pro-vision`. Servidor: VPS `157.173.207.22:20128` (ver `D:\informacoes_omniroute\relatorio_omniroute.md`).
  - **Se o proxy cair:** apontar `HERMES_QA_VISION_URL` pra outro endpoint OpenAI-compat com visão, ou usar as chaves Gemini diretas de `D:\credenciais-canais\todas_credenciais.json` (bloco `googlePalmApi`) contra `https://generativelanguage.googleapis.com` — mas hoje a maioria dessas chaves está estourada (429) ou inválida; o proxy é o caminho vivo.
  - **Se quiser rodar sem IA:** `HERMES_QA_VISION=0` — só checagem mecânica.

## Suites

**`tests/qa-ui.spec.ts` — navegação (12 testes):** login+dashboard, as 9 abas do trial (cada uma julgada pela visão "carregou sem erro?"), botão Sair (desloga de verdade) e toast (aparece top-center, fix #7).

**`tests/qa-func.spec.ts` — funcional (7 testes):** não só "a aba abre", mas "o botão FAZ o que promete". Estratégia: clicar a ação e confirmar via `lib/api-capture.ts` que o endpoint `/api/*` certo dispara com 2xx (robusto, não depende de dirigir wizards multi-step). Cobre:
- Abrir o wizard de criar agente (Funcionário Fácil) — a visão confirma que é um assistente de criação.
- Voz/TTS: "Testar voz TTS" (chama `/api/tts` **ou** valida pedindo a API key) e "Salvar Motor de Voz" (`PUT /api/settings/voice`).
- Configurações: salvar prompt (`PUT /api/settings/ai`), abrir dialog de Nova Credencial IA, abrir dialog de Nova Chave de API.
- Gestor Fácil: wizard de 4 etapas navega e mostra "Salvar Gestor".

### Descobertas / divergências que a suite pegou

- Produção roda um **binário mais novo** que o fonte local (`D:\hermes-call`): rótulos e estrutura divergem. Sempre valide seletores ao vivo.
- Em Funcionários IA, "Criar Funcionário Fácil" e "Criar Gestor Fácil" são **abas (`role=tab`)**, não botões.
- O `<Toaster>` só existe dentro da área logada; o sonner só injeta `[data-sonner-toast]` **quando um toast dispara**.
- "Testar voz TTS" **sem API key configurada** valida e mostra toast "Preencha a API Key primeiro" (comportamento correto) — é aqui que as chaves Gemini entram (ver `lib/gemini-keys.ts`).
- Conta trial vazia esconde botões que dependem de dados (Copiar link, produtos, leads).

## Suites E2E — "do começo ao fim" (criar → verificar no backend → limpar)

Os testes E2E não confiam só na UI: criam o dado, **releem no backend** com o token do usuário pra confirmar que persistiu, e **deletam** no fim (a conta trial fica limpa). Multi-tenant: o token só vê/apaga o próprio dado.

- **`tests/e2e-agents.spec.ts`** — cria agente (`POST /api/agent-profiles`), confirma nome+voz em `GET /api/agent-profiles`, deleta; preview de voz real (`/api/tts/preview`, edge-tts, grátis) retorna `audio_base64`.
- **`tests/e2e-settings.spec.ts`** — salvar prompt/voz/budget e reler em `GET /api/settings`; TTS test (edge-tts); Telegram test (**manda msg real**, aceita ok/503/400); criar Credencial IA com chave Gemini (`type:"llm"`) → GET → delete; gerar Chave de API → GET → delete.
- **`tests/e2e-wizards.spec.ts`** — Gestor Fácil (`PUT /api/easy-manager/wizard` → GET confirma `name/systemPrompt/provider`); Follow-up (criar → GET → delete); Base de Conhecimento (mapeia se é cosmético, sem verde falso).
- **`tests/e2e-data.spec.ts`** — CRM etapa, Agenda evento, Vitrine produto: cada um criar → confirmar no GET → deletar.
- **`tests/e2e-guarded.spec.ts`** — WhatsApp/ligação/massa: prova que o backend **recusa** sem linha pareada (404 "no such session"), **nunca envia**.
- **`tests/e2e-zzz-clean.spec.ts`** — roda por último; varre e remove qualquer resíduo `QA_*` e confirma conta zerada.

Payloads/endpoints validados ao vivo: credencial exige `type:"llm"`; follow-up exige `name`+`trigger_value`; agenda exige `name`+`start_at` ISO.

## Arquivos

- `config.ts` — URL, planos×abas (espelha `plan_features.go`), rótulos da sidebar, config de visão.
- `lib/session.ts` — cria/cacheia conta trial, injeta sessão (pula onboarding), helpers `navTab`/`openSettings`.
- `lib/vision.ts` — chama o Gemini (proxy) e faz assert semântico do screenshot.
- `lib/api-capture.ts` — captura chamadas `/api/*` disparadas por uma ação (prova que o botão faz o que promete).
- `lib/backend.ts` — cliente HTTP autenticado (GET/POST/PUT/DELETE) + helpers de read-back pra verificação no backend.
- `lib/cleanup.ts` — registra ids criados e apaga no fim (mesmo se o teste falhar), garante conta limpa.
- `lib/gemini-keys.ts` — expõe as chaves Gemini de `D:\credenciais-canais` pra preencher campos de API key.
- `tests/qa-ui.spec.ts` (navegação) · `tests/qa-func.spec.ts` (funcional) · `tests/e2e-*.spec.ts` (ponta a ponta).
- `reports/` — HTML + JSON de cada run. `test-results/` — screenshots/traces por teste.
