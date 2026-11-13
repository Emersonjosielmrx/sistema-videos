# Correções — 28/07/2026 (Hermes Call)

Continuação da lista B do doc de 27/07 (as pendências que estavam documentadas pra fazer hoje).
Versão no ar: **v0.3.0** (build 20260728-1104). Código: branch `versao-final-bd24` = commit `4a66959` nas 2 contas GitHub. Docker Hub/VPS: `stable`/`latest`/`v0.3.0`/`BASE-UNICA` = imagem `68a87717adbe`.

---

## FEITO HOJE (verificar no navegador)

### 1. Funcionário Gestor — agora SALVA tudo (era a causa raiz)
- **O que era:** o backend que salvava a config completa do Gestor (`easy_manager_settings.go`) estava **desligado do build** (`+build ignore`) desde 24/07, porque a struct `EasyManagerWizardConfig` tinha sido removida. Por isso o wizard só salvava 5 campos e tudo mais (canais, telegram, ferramentas, superpoderes) sumia no reload.
- **Como foi feito:** recriei a struct `EasyManagerWizardConfig` no pacote `internal/settings` com TODOS os campos do wizard; adicionei ao `UserSettings` e ao carregamento; reativei o `easy_manager_settings.go` (removido do build-ignore e do .gitignore); registrei as rotas `GET/PUT /api/easy-manager/wizard`. O wizard agora carrega e salva o estado rico completo.

### 2. Gestor — prompt padrão da conta
- **Como foi feito:** o prompt do Gestor, se vazio, agora cai no prompt padrão da conta (bloco `attendant.system_message`) em vez de um texto genérico placeholder.

### 3. Gestor — Telegram (credencial + testar)
- **Como foi feito:** na etapa 2 (Comunicação), quando "Notificar no Telegram" está ligado, aparece painel com **Token do Bot + Chat ID + botão "Testar Telegram"** (usa `/api/settings/telegram/test`). Persiste no config rico.

### 4. Gestor — removida a "Árvore de Agentes"
- **Como foi feito:** a etapa 4 "Árvore de Agentes / Orquestrador de Fluxo" era de atendimento, não do Gestor. Removi (183 linhas); Superpoderes virou a etapa 4. Navegação renumerada (4 etapas agora).

### 5. Teste final do wizard (Chat de Simulação) — funciona com prompt em construção
- **O que era:** o Chat de Simulação era 100% fake (conversa hardcoded, input morto, botão não fazia nada).
- **Como foi feito:** criei endpoint `POST /api/ai/simulate` (aceita system_prompt cru + message + history, reusa `ProcessConversation`). O chat do wizard agora monta o prompt a partir do estado atual (nome/função/tom/conhecimento/regras/etapas) e conversa de verdade. Tem modo "Cliente Grosseiro" que injeta contexto de teste.

### 6. Encadeamento das 3 abas fáceis (não volta mais ao início)
- **O que era:** ao terminar o Configura Fácil, o botão fazia `window.location.reload()` e caía no começo.
- **Como foi feito:** troquei por `setView("specialized")` (navegação real). O EasyAgentWizard ganhou callback `onComplete` — ao finalizar o Funcionário Fácil, encaminha pra aba "Gestor Fácil". Fluxo: Configura → Funcionário → Gestor, sem reload.

### 7. Toasts movidos pra cima
- **Como foi feito:** `<Toaster position="top-center">` (era bottom-right, tapava os botões "Delegar para IA"/"Próxima Etapa"/"Instalar app").

### Verificado — já funcionava:
- **Configura Fácil / Cofre de Chaves:** já tem dropdown de provider + campo de chave + persiste. Não era falha.

---

## PENDENTE (o item mais pesado — precisa de vários dias)

### Runtime real dos Superpoderes e Ferramentas do Gestor
- **Status atual:** os 13 superpoderes (Halt Override, Modo Sombras, Multi-Agent Swarm, Clustering de Memória, Shell Access, etc.) e as 9 ferramentas **agora SALVAM/PERSISTEM** (a fundação foi feita hoje). Mas o **comportamento real de cada um no runtime ainda não existe** — são flags que ficam gravadas, sem código que as faça acontecer.
- **Por quê não hoje:** cada superpoder é uma feature própria e grande (ex: "Multi-Agent Swarm" = orquestração de múltiplos agentes numa thread; "Shell Access" = executar comandos no servidor; "Clustering de Memória" = ML sobre histórico). Implementar de verdade é trabalho de vários dias, e fazer às pressas junto com o resto entregaria coisa quebrada.
- **Próximo ciclo:** priorizar quais superpoderes realmente vão ser usados e implementar o runtime um a um, testando cada um.

### "Simular Chamada" (voz) na etapa final do wizard
- O Chat de texto foi ligado (item 5). O **teste por VOZ** ("Iniciar Teste de Voz") ainda só pede permissão de microfone — o streaming de voz em tempo real (como na landing) é mais complexo e ficou pra depois.

---

## Segurança (não esquecer)
- **Revogar os 2 tokens do GitHub** colados no chat (fabricadeautomacoesia + Emersonjosielmrx).
- Quando validar tudo no navegador, rodar `node deploy/promote-stable.js`.
