# Relatório de Hand-off: Hermes Call (D:\hipercool-refactor)
**Data:** 2026-07-16 | **VPS Produção:** 62.171.128.241

Este relatório documenta o estado atual do sistema após a maratona de correções e o que falta implementar para atingir o nível comercial desejado pelo dono.

## 1. O que JÁ ESTÁ FUNCIONANDO (Deployado e Validado)

- **Isolamento Multi-tenant Real:** bots do Telegram agora são deduplicados por token (evita vazamento de mensagens entre contas que clonaram o token) e o trial expirado desativa o bot e a sessão automaticamente a cada 10 min.
- **Gate de Linha:** quando o cliente tem 2+ linhas conectadas, o agente *pergunta* qual usar antes de qualquer ação (ligação, mensagem, áudio), respeitando a escolha.
- **Veracidade da Chamada:** o sistema distingue "tocou e não atendeu" de "nem conectou" (ex: número inválido sem WhatsApp).
- **Watchdog Anti-bloqueio:** chamadas que travam no envio da oferta (sem resposta do WA) são derrubadas após 6 minutos, liberando o slot e impedindo que o sistema inteiro pare de ligar.
- **STT Robusto (Whisper Local):** o sistema auto-detecta o modelo carregado no servidor local (atualmente `Systran/faster-whisper-tiny`), acabando com o erro 500 por nome de modelo fixo no código.
- **IA de Ligação por Dono:** a ligação rápida usa o modelo e a credencial do dono da sessão (ex: Gemini Flash-Lite direto), não um agente global.
- **Áudio Gravado Conversacional:** enviar um áudio + número agora toca o áudio e a IA *continua* atendendo a ligação (não desliga no fim do áudio). A chamada só cai se o cliente desligar ou após 1 minuto de silêncio de ambos os lados.
- **Agente Opera o Painel:** o agente do Telegram consegue criar/apagar agentes especializados, conectar número (gerando código de pareamento no chat), ver status de campanha e mudar config de voz/IA.
- **CRM Kanban (Base):** aba CRM no painel com etapas customizáveis e drag-and-drop nativo HTML5.
- **Esteira de Leads:** toda ligação de campanha atualiza o lead no banco. "Não atendeu" agora é separado em 1x, 2x e 3x+ automaticamente.
- **PWA e Listas:** botão "Instalar app" no painel. Aba Listas permite colar números ou subir .txt/.csv.

---

## 2. O QUE FALTA COMEÇAR (Lista Revisada pro Próximo Agente)

### A. Visuais / UI (Painel)
1. **Aba Única de Credenciais (Estilo n8n):**
   - *O que é:* O usuário cria credenciais nomeadas (Nome + Chave + Base URL) e apenas as *seleciona* em dropdowns nas outras abas (IA Padrão, Voz, Ligação).
   - *Por que:* Hoje a chave fica mascarada e espalhada. O dono quer centralizar pra poder reusar a mesma chave em funções diferentes.
2. **Agrupar Abas no CRM:**
   - *O que é:* Mover as abas "Contatos", "Campanhas" e "Listas" para *dentro* da aba CRM.
   - *Por que:* O dono quer tudo relacionado a clientes num lugar só.
3. **Chat Web Mobile + Áudio:**
   - *O que é:* Melhorar a responsividade do chat web no celular, adicionar nome/instruções claras e permitir gravar/enviar áudio pelo navegador (como no Telegram).
4. **Vozes LLM Dinâmicas:**
   - *O que é:* Dropdown dinâmico que busca as vozes disponíveis de ElevenLabs, Gemini e GPT via API, sem o usuário precisar digitar o nome da voz.

### B. Funcionais / Backend
1. **CRM Avançado (Tags, Prompts e Transferência):**
   - *O que é:* (1) Permitir criar tags no CRM. (2) Cada etapa do Kanban ter um *system prompt* específico que instrui o agente sobre como levar o lead pra próxima etapa. (3) Etapa "Atendimento Humano" que transfere a chamada/conversa pro dono (investigar viabilidade de callback reverso no whatsmeow).
2. **Notificação por Gatilho (Agentes Especializados):**
   - *O que é:* Quando um agente especializado é acionado (ex: lead chegou na etapa X), o dono recebe uma notificação automática no Telegram.
3. **Webhooks Expandidos:**
   - *O que é:* Disparar webhooks em mudança de etapa do CRM e quando a IA detectar campos customizados (ex: "quer falar com humano").
4. **Monitorar Áudio das Chamadas:**
   - *O que é:* Gravar e analisar o áudio real de cada chamada (não só a transcrição) para alimentar a IA de diagnóstico com dados sobre cortes, latência e qualidade da voz.
5. **Agente WhatsApp Mudo (Investigação Profunda):**
   - *O que é:* O agente cria o grupo mas não responde no PV nem no grupo. O fix inicial (ativar enabled+mode ao criar grupo) foi feito, mas precisa validar se resolveu todos os cenários.

### C. Ocultas / Sistema
1. **IA de Diagnóstico (Evolução):**
   - *O que é:* O módulo já coleta erros e anota, mas precisa ser expandido para rodar a LLM do cliente em background analisando ativamente os logs e sugerindo correções no painel.
2. **Integração Open Claw / Hermes Agent:**
   - *O que é:* Definir e implementar como o sistema dá acesso e instruções aos clientes que possuem essas ferramentas externas.

---

## 3. Sugestões para Produção a Nível Comercial

1. **Migração de VPS (Urgente):** A VPS atual (62.171.128.241) é CPU-only com ~3GB de RAM livre. O `edge-tts` já sofreu OOM (Out of Memory) e o Whisper roda no limite. Para escala comercial, é imperativo migrar para uma máquina com mais RAM e, idealmente, uma GPU básica para o Whisper, garantindo latência baixa nas ligações.
2. **Isolamento de Banco de Dados:** Atualmente, o multi-tenant é lógico (coluna `user_id`). Para segurança comercial B2B, avaliar a separação física dos dados sensíveis (leads, conversas) por schema ou banco.
3. **Rate Limiting e Faturamento:** O sistema de custos foi corrigido, mas precisa de uma UI clara para o cliente acompanhar o gasto em tempo real e bloqueios automáticos (hard limits) para evitar prejuízos com a API da OpenAI/Anthropic se um cliente abusar das ligações.