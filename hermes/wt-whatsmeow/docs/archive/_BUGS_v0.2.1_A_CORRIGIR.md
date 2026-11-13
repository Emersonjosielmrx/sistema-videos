# Bugs confirmados na versão v0.2.1 (a que roda na VPS opus-sem-limites)

## STATUS DA RECONSTRUÇÃO (atualizado 2026-07-26 ~02:20, branch reconstrucao-v0.2.1)
- **BUG-7 — CORRIGIDO** (commit d0548be): motor de ligação usa credencial vinculada. Build ok.
- **BUG-1 — CORRIGIDO** (front): erro voz/nome vira mensagem amigável + volta ao Passo 2. Build ok.
- **Vozes Funcionário Fácil — CORRIGIDO**: 6 vozes do golden (tinha 4, com Manuela inexistente).
- **Chat religado no menu** (era desconexão, não bug da lista).
- **BUG-3 parte 1 — JÁ OK no local**: ChatMonitor busca /api/agent-profiles (local está À FRENTE do golden, que ainda tem mock hardcoded). Parte 2 (falha de inferência) PRECISA VALIDAR AO VIVO com credencial real.
- **BUG-6 — PRECISA BROWSER**: store de tema local é IDÊNTICO ao golden (não regrediu). O "fica preto" é runtime/CSS, só diagnostica reproduzindo. NÃO mexer no escuro.
- **BUG-2, BUG-4, BUG-5 — PENDENTES**: precisam análise + validação ao vivo.
- **Billing/Asaas — PENDENTE (crítico)**: reescrever SubscriptionTab (regrediu p/ versão magra) SÓ com a dona validando o fluxo de pagamento no navegador.

Placar objetivo: 11/22 features-chave do golden presentes no build atual (era 8/22).

---


> Registrados por Haylla em 2026-07-26. São bugs REAIS observados na versão
> correta (v0.2.1, build 20260723-2224) rodando em
> `hermescall.opus-sem-limites.com.br`. Corrigir DEPOIS de recuperar/reconstruir
> o código-fonte. Ver `CLAUDE.md` (seção anti-contaminação) e memória
> `project_hermes_versao_limpa_v021`.
>
> IMPORTANTE: os testes/documentos feitos de 24→25/07 foram na VERSÃO ERRADA
> (contaminada). Antes de corrigir qualquer bug daqueles documentos, VERIFICAR
> se o bug existe nesta v0.2.1 — muitos podem já estar corrigidos ou serem
> diferentes. Esta lista abaixo são os confirmados nesta versão.

## BUG-1 — Erro ao finalizar "Funcionário Fácil" mal apresentado
- **Onde:** Wizard Criar Funcionário Fácil → botão Finalizar.
- **Sintoma:** toast de erro cru `/api/agents 500 {"error":"Voz pt-br-franciscaneural incompatível com o nome do agente (Rafael). Troque a voz ou renomeie o agente — evita parecer trote (lead desconfia de voz feminina em agente com nome masculino).","success":false}`.
- **Diagnóstico:** a validação em si está CORRETA (voz feminina "franciscaneural" x nome masculino "Rafael"). O problema é UX: aparece como erro 500 técnico em vez de uma mensagem clara/amigável no campo certo. Deveria explicar melhor e idealmente validar ANTES de mandar pro backend (validação inline no passo da voz).
- **Fix provável:** front trata esse erro específico com card amigável; ou back retorna 422 com campo `field:"voice"` e o wizard destaca o passo.

## BUG-2 — Estimativas em "Meus Funcionários" são dados simulados
- **Onde:** Funcionários IA → Meus Funcionários (card do agente) e "Gamificação: Performance dos IAs".
- **Sintoma:** "RECEITA (ESTIMADA) R$ 79.096,5", gráfico de barras Seg–Sex, "MVP DA SEMANA" — tudo mockado, não reflete dados reais.
- **Fix provável:** ligar esses widgets a métricas reais (ligações/vendas/receita do agente) ou, se ainda não há dados, deixar explícito "sem dados ainda" em vez de números falsos.

## BUG-3 — Chat de Teste não puxa agentes reais e falha na inferência
- **Onde:** Funcionários IA → Chat / Teste (Sandbox).
- **Sintoma 1:** em "Funcionários Disponíveis" só aparece "Agente de Teste (UI M...)" — não lista os agentes reais criados pela dona.
- **Sintoma 2:** ao mandar mensagem → "Falha crítica no motor de inferência" / "[FALHA] Timeout ou API Key inválida".
- **Fix provável:** o dropdown de agentes do sandbox não busca os agentes reais do usuário; e a chamada de inferência do teste não usa a credencial correta do agente (usa uma key vazia/placeholder). Ligar o sandbox à lista real de agentes + à credencial vinculada de cada um.

## BUG-4 — Após finalizar Funcionário Fácil (conversa/híbrido), não responde
- **Onde:** depois de concluir o wizard para um bot de conversa ou híbrido.
- **Esperado:** o agente já deveria sair respondendo mensagens automaticamente.
- **Sintoma:** não responde.
- **Fix provável:** ao finalizar, o agente não fica `enabled`/`mode` correto para autoreply, ou não é vinculado à sessão de WhatsApp. Verificar o autoreply e o estado salvo ao concluir o wizard.

## BUG-5 — Funcionário Fácil de ligação/híbrido não pede Whisper + voz
- **Onde:** wizard Criar Funcionário Fácil, quando o tipo é ligação ou híbrido.
- **Esperado:** deveria pedir para configurar Whisper (STT) e a voz (TTS).
- **Sintoma:** não pede esses passos.
- **Fix provável:** o wizard só mostra o fluxo de mensagem; falta ramificar os passos por tipo (ligação/híbrido → incluir passo de STT/voz).

## BUG-6 — Tema quebra (fica preto) ao abrir Configurações
- **Onde:** ao clicar em Configurações (às vezes).
- **Sintoma:** o tema buga e a tela fica preta.
- **Fix provável:** intermitente; investigar classe `dark` / store de tema / algum componente de Settings que zera CSS. Reproduzir e ver console.

## BUG-7 — Motor de Ligação pede API Key mesmo com credencial vinculada
- **Onde:** Configuração do agente → Ativação da Inteligência Separada → Motor Ligação.
- **Sintoma:** com "Credencial Vinculada" selecionada (ex: `aulacomia@gmail.com · gemini`), ao clicar em "Buscar modelos" / "Testar chave" / "Salvar Motor Ligação" aparece "Preencha a API Key primeiro". Não busca o modelo usando a credencial já selecionada.
- **Fix provável:** a tela exige o campo API Key manual e ignora a credencial vinculada. Deveria usar a key da credencial selecionada para buscar modelos/testar/salvar. Ligar o fluxo de "Buscar modelos" à credencial vinculada.
