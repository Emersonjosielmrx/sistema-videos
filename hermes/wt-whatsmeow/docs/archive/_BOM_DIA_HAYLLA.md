# ☀️ Bom dia, Haylla — resumo do trabalho noturno (2026-07-26)

Trabalhei a noite via cron na reconstrução da v0.2.1. Aqui está tudo, curto e direto.

## ✅ O que foi CORRIGIDO (branch `reconstrucao-v0.2.1`, tudo commitado, NADA no ar)

1. **BUG-7** — Motor de Ligação pedia API Key mesmo com credencial vinculada. Agora usa a credencial (o backend já sabia; o front não passava). Fiel ao golden.
2. **BUG-1** — Erro "voz incompatível com nome" aparecia como toast técnico 500. Agora é mensagem clara + leva de volta ao passo do nome.
3. **Vozes do Funcionário Fácil** — tinha 4 vozes (uma, "Manuela", nem existe na versão boa). Agora as 6 corretas do golden (Francisca, Antonio, Thalita, Aria-EN, Guy-EN, Elvira-ES).
4. **Chat religado no menu** — estava pronto no código, só desconectado.

Validação: `vite build` OK, `go build` OK, `tsc` = 283 erros vs 285 no main (não introduzi erro, reduzi 2 — o resto é legado pré-existente).

## 🔍 O que DESCOBRI (importante)

- **Os docs de erro antigos são trabalho JÁ FEITO, não pendências.** Verifiquei os 25 bugs (5 backend do QA_STATE + 20 P-bugs) contra o fonte: TODOS já corrigidos. Detalhe em `_VERIFICACAO_DOCS_ERRO.md`. Você estava certa em desconfiar deles.
- **BUG-2 (dados simulados em Meus Funcionários)** existe IDÊNTICO no golden — não é regressão, é bug real da v0.2.1. Corrigir precisa de endpoint de vendas-por-agente que não existe.
- O "placar de 178 regressões" que eu tinha montado é ENGANOSO — mistura textos de telas diferentes. Muita coisa que parecia "faltando" é mock hardcoded (ex: "Ranking Global de Provedores") ou está em tela que já funciona.

## ⏳ O que FALTA — precisa de você ao vivo (não fiz no escuro de propósito)

| Item | Por quê precisa de você |
|------|------------------------|
| **Billing/Asaas** (SubscriptionTab regrediu) | Tela de PAGAMENTO — reconstruir e você testar o fluxo Asaas no navegador |
| **BUG-3 parte 2** (chat de teste: falha de inferência) | Precisa credencial real + ver ao vivo. (A parte 1 — puxar agentes reais — o local JÁ resolve, está à frente do golden) |
| **BUG-4** (não responde após finalizar wizard) | Precisa ver o estado do agente no backend após criar |
| **BUG-5** (wizard de ligação não pede Whisper/voz) | Confirmar comportamento esperado com você |
| **BUG-6** (tema fica preto) | Runtime/CSS — só reproduzindo no navegador. Código de tema = idêntico ao golden |
| **RAG "Ver chunks/Reindexar" + Estúdio de Voz preview** | Precisam de endpoints backend novos (`/rag/.../chunks`, `/reindex`, `/tts/preview`) que não existem |
| **Dívida de teste** | `sessionmanager_test.go` usa tipo antigo (sqlite) — precisa Postgres de teste. Não afeta produção |

## 🛟 Se algo der errado — a versão boa está preservada em 4 lugares
Imagem `fabricadeautomacoesia/hermes-call:v0.2.1` (Docker Hub, 2 tags + rodando na VPS + cópia local em `_GOLDEN_v0.2.1/`). Rollback completo em `_ULTIMA_IMAGEM_FUNCIONAL.md`.

## ⚠️ Sobre o cron
O cron `aa2ab271` rodou 6 ciclos. Os últimos 4 não produziram código novo — não há mais tarefa segura pra fazer sozinha (tudo que resta precisa de você ou de backend novo). **Recomendo pausar:** `CronDelete aa2ab271` (ou me peça pra parar). Deixei rodando porque você pediu, mas está só gastando chamadas de API.

## 👉 Por onde retomar (sugestão)
1. Pausar o cron.
2. Abrir a branch `reconstrucao-v0.2.1` no navegador (rodar local) e validar as 4 correções.
3. Atacar billing/Asaas juntos (é o de maior valor e precisa de você).
4. Depois os bugs de runtime (BUG-3/4/5/6) com o navegador aberto.
