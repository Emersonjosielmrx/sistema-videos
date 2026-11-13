# Correções — 27/07/2026 (Hermes Call)

Documento simples pra verificar amanhã. Duas partes:
**A) O que JÁ foi feito hoje** (pra você validar) e **B) O que ainda falta** (pendências que você listou no fim do dia).

Versão no ar hoje: **v0.3.0** (build 20260728-0112) em `hermescall.opus-sem-limites.com.br`.
Código: branch `versao-final-bd24` = `main`/`versao-boa` nas 2 contas GitHub. Docker Hub: `stable`/`latest`/`v0.3.0`/`BASE-UNICA-20260727` (todas a mesma imagem).

---

## A) O QUE JÁ FOI FEITO HOJE (verificar se ficou bom)

### 1. Versão base consolidada (v0.3.0)
- **O que era:** existiam dezenas de versões misturadas (23→27/07), tags `stable/latest/golden` apontando pra versão velha → todo rollback ressuscitava versão errada. Dias perdidos por isso.
- **Como foi feito:** montei a base = **frontend do commit `bd24aef`** (painel completo: CRM com Funil/Taxa de Vitória/Receita/Garimpo) + **backend da `versao-boa`** (sem a regressão do bd24aef) + **landing oficial "Hermes Call"**. Apaguei TODAS as versões entre 23/07 e hoje (local + VPS + Docker Hub + tags GitHub das 2 contas). Fixei v0.3.0 como única base em todo lugar.
- **Verificar:** `/api/version` mostra v0.3.0; rollback/pull latest sempre traz a versão certa.

### 2. Landing page oficial
- **O que era:** aparecia a landing velha "Inovare AI".
- **Como foi feito:** coloquei a landing "Hermes Call - Atendimento IA por Voz e Texto no WhatsApp" (133KB, com menu hambúrguer) em `client/public/landing/`. Backup em `_LANDING_OFICIAL/`.
- **Verificar:** abrir `hermescall.opus-sem-limites.com.br` → deve mostrar a landing Hermes Call.

### 3. Chat (Conversas WhatsApp) ligado
- **Como foi feito:** `ChatPage.tsx` existia mas nunca foi roteado. Liguei: view `chat` no navigation, rota no App.tsx, botão "Chat" no Sidebar.
- **Pendência conhecida:** botão "Carregar mensagens antigas" chama rota que não existe no backend (não trava o resto).

### 4. Os 7 fixes do Funcionário Fácil (commit c53c932 incorporado)
- **Como foi feito:** esses fixes tinham ficado de fora da base. Trouxe os 8 arquivos (merge 3-way pra não perder melhorias do bd24aef):
  - Auto-atendimento: criar agente já liga o autoreply (responde texto do cliente sozinho).
  - Takeover: dono manda 2+ msgs em 30s → IA pausa naquela conversa até fim do dia.
  - Voz local sem chave: semeia whisper local (STT) + edge-tts (TTS) quando não há credencial.
  - Fallback whisper local no `settings.go` (ligação não fica muda só tocando "ok/entendo").
  - `credential_id` server-side nos endpoints de voz (não pede mais api key ao testar voz).
- **Verificar:** criar agente → mandar texto de outro número → deve responder.

### 5. Menu reorganizado em sub-abas
- **Como foi feito:** removi do menu lateral itens que já eram sub-aba da Gestão de Leads (Contatos, Campanhas, Listas, Follow-Up, Relatórios). Movi pra sub-abas da Gestão de Leads: Promessas, Chamada em Massa, Mensagem em Massa. Removi do menu Gravações/Transcrições (já em Central de Telefonia) e Base de Conhecimento (já nos agentes).

### 6. Bug do tema (claro trava no escuro)
- **O que era:** entrar em Configurações forçava fundo escuro e não voltava ao tema claro.
- **Como foi feito:** o `AppearanceSettings.tsx` e `EasySettingsWizard.tsx` aplicavam a cor de fundo default (`#09090b`) como inline style no `<html>`, vencendo a classe do tema. Corrigi: com a cor default, remove o inline e deixa o CSS do tema mandar.
- **Verificar:** Config → tema claro → não deve travar no escuro.

### 7. Analytics do funil (dados reais em vez de mock)
- **O que era:** mostrava R$45.000 fixo, heatmap aleatório (`Math.random()`), "Origem do Fechamento" e Copilot com texto fixo.
- **Como foi feito:** removi todos os mocks; liguei aos endpoints reais (`/api/analytics/crm/kpis`, `/funnel`, `/win-loss`). Sem dados = mostra zeros honestos, não inventa números. Copilot insight agora é dinâmico (baseado no maior motivo de perda real).
- **Verificar:** Gestão de Leads → Analytics → deve mostrar seus dados reais (ou zeros).

### 8. Botão "Buscar" modelos no wizard
- **Como foi feito:** o wizard tinha a função de GET real de modelos, mas sem botão visível. Adicionei botão "Buscar" ao lado do dropdown de Modelo (faz GET `/api/ai/models` da credencial).

### Verificados — JÁ eram reais (não são "figurativo"):
- **Feed de Auditoria & Compliance:** puxa `/api/transcripts` — são transcrições reais das suas ligações.
- **Provedores Ativos:** mostra STT/LLM/TTS reais das suas settings.
- **Captação:** backend real (Nominatim + Overpass, sem chave). Se "trava", é dado-dependente (cidade/ramo sem resultado ou timeout), não bug de código.
- **Ollama:** não é figurativo — em Credenciais de IA tem "Outro / Proxy (Ex: OmniRoute, Ollama)" com base_url + api_key.

---

## B) PENDÊNCIAS PRA AMANHÃ (o que você listou hoje à noite)

### FUNCIONÁRIO GESTOR (Configuração Fácil do Gestor)
1. **Não funciona / falta onde colocar credencial e chave.** Deveria configurar o Gestor mas não tem campo de credencial/chave real funcional. (Na tela tem "Chave de API (Opcional)" e Motor Principal/Fallback, mas parece não salvar/aplicar.)
2. **Prompt padrão errado.** O prompt do Gestor deveria ser o **prompt padrão da conta principal**, escondendo só o que precisa ser padrão pra eles (ex.: as ferramentas). Hoje mostra um prompt genérico ("Você é o Hermes...").
3. **Falta opção do Telegram no Gestor:** não tem onde falar com ele pelo Telegram, colar as credenciais do Telegram e testar. (No wizard do agente normal existe "Notificar no Telegram" — o Gestor precisa disso também, com campo de credencial + botão testar.)
4. **Verificar se todas as ferramentas do Gestor realmente existem e funcionam** (Pesquisa Web, Leitura de Site, Análise de Imagens, Consultar Clima, Gestor de CRM, Agenda, Code Interpreter, Webhook Autônomo, Criador de Conteúdo).
5. **Árvore de Agentes no Gestor está errada:** o Gestor NÃO deveria ter "Árvore de Agentes" — isso é só pra gente de atendimento (agente normal). Remover/ajustar a etapa 4 do wizard do Gestor.
6. **Verificar se todos os Superpoderes funcionam** (Pausar Agentes, Acesso ao Cofre, Relatório de Fechamento, Cobrança de Promessas, Alertas Críticos, Modo Sombras, Clustering de Memória, Multi-Agent Swarm).

### CONFIGURA FÁCIL (wizard geral de setup)
7. **Também não tem onde colocar credencial/chave de verdade** (mesma falha do Gestor).
8. **Ao clicar "Criar Funcionário Fácil" no final, volta pro começo** em vez de encaminhar pra aba "Criar Funcionário Fácil". As 3 abas fáceis (Configura Fácil, Funcionário Fácil, Gestor Fácil) **deveriam encaminhar entre si** até completar as 3, independente da ordem em que começar — em vez de "botar em ação"/voltar ao início.

### CRIADOR DE FUNCIONÁRIO FÁCIL — etapa final (Testes, Otimização & Deploy)
9. **O teste do final não funciona:** nem o **Chat de Simulação** (texto) nem o **Simular Chamada** (voz). Deveria funcionar como na landing page, só que usando o **prompt que está sendo feito ali na hora** (o agente em construção no wizard).

### UI GERAL
10. **Notificações (toasts) aparecem embaixo, em cima dos botões** ("Delegar para IA", "Próxima Etapa", "Instalar app") — não dá pra ler. **Mover as notificações pra parte de cima da tela.**

---

## Notas de segurança (não esquecer)
- **Revogar os 2 tokens do GitHub** que foram colados no chat hoje (fabricadeautomacoesia + Emersonjosielmrx) — trocar nos Settings das 2 contas.
- Quando validar tudo, rodar `node deploy/promote-stable.js`.
