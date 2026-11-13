# Roadmap Hermes Call v3 — Backlog de Melhorias

Documento vivo. Marcado: ✅ feito · 🔨 em andamento · ⬜ pendente.
Prioridade: P0 (pedido explícito da dona) · P1 (alto valor) · P2 (nice-to-have).

---

## 0. JÁ FEITO
- ✅ Merge upstream AstraCalls v0.0.4 + fix 2 rotas duplicadas (panic no boot)
- ✅ openapi.yaml completo (156 rotas, 72 SaaS documentados)
- ✅ Stack paralelo hermes3 (sem tocar hermes2), STT fix (HERMES_STT_MODEL=base)
- ✅ Branding: removida logo ASTRA e refs visíveis WaCalls/Astra
- ✅ Backend analytics de campanha: persistência + % de escuta + endpoints

---

## 1. CAMPANHAS / DISPARO (núcleo do negócio)
- 🔨 **P0** UI painel: histórico de campanhas (lista + agregados + % escuta)
- ⬜ **P0** Métricas separadas POR campanha (comparar campanha A vs B)
- ⬜ **P0** Ver quem ouviu a mensagem toda — por segundos E por %
- ⬜ **P0** Filtrar/ordenar resultados (escuta desc, duração, status, interesse)
- ⬜ **P0** Config anti-bloqueio por campanha: horário início/fim, delay entre ligações, simultâneas, se sequencial ou paralelo
- ⬜ **P0** Criar campanha nova A PARTIR de contatos selecionados de outra (listas personalizadas)
- ⬜ **P1** Agendar campanha pra rodar em data/hora futura (scheduler)
- ⬜ **P1** Pausar / retomar / cancelar campanha em andamento
- ⬜ **P1** Retry automático de no-answer/failed (N tentativas, intervalo)
- ⬜ **P1** Warm-up do número novo (rampa: começa com poucas/dia e sobe) — anti-ban
- ⬜ **P1** Rotação de múltiplos números na mesma campanha (distribui carga/risco)
- ⬜ **P1** Detectar secretária eletrônica / caixa postal e não gastar áudio
- ⬜ **P1** DTMF / IVR: cliente aperta 1 pra falar com humano, 2 pra sair
- ⬜ **P2** A/B testing de áudios (2 versões, mede qual retém mais)
- ⬜ **P2** Blocklist global (opt-out): quem pediu pra sair nunca mais recebe
- ⬜ **P2** Limite diário por número (guard-rail de segurança)
- ⬜ **P2** Preview/estimativa antes de disparar (custo, tempo, nº válidos)

## 2. TRANSCRIÇÃO / IA NAS CHAMADAS
- ⬜ **P0** Transcrever a resposta falada do cliente (STT) durante/após o áudio
- ⬜ **P0** Detectar intenção positiva ("eu quero", "tenho interesse") → tag interesse
- ⬜ **P1** Sentimento da resposta (positivo/neutro/negativo) via IA
- ⬜ **P1** Resumo automático da chamada (o que o cliente falou)
- ⬜ **P1** Agente conversacional real: cliente fala, IA responde ao vivo (já tem infra STT+TTS+LLM, falta ligar no fluxo de campanha)
- ⬜ **P1** Palavras-chave configuráveis por campanha (opt-out: "não perturbe", "descadastrar")
- ⬜ **P2** Classificação automática do lead pela resposta (quente/morno/frio)
- ⬜ **P2** Transferir pra humano quando detecta interesse forte

## 3. CONTATOS / CRM
- 🔨 **P0** Mais filtros: por tag, por lead stage, por última interação, por % escuta histórica
- ⬜ **P0** Listas personalizadas (criar, nomear, salvar seleção de contatos)
- ⬜ **P0** Exportar lista selecionada → campanha nova
- ⬜ **P1** Importar contatos via CSV/Excel/vCard
- ⬜ **P1** Exportar contatos/resultados (CSV/Excel)
- ⬜ **P1** Deduplicação de contatos
- ⬜ **P1** Campos customizados por contato (já tem tabela contact_custom_fields)
- ⬜ **P1** Histórico unificado por contato (chamadas + mensagens + notas + tags)
- ⬜ **P2** Segmentos dinâmicos (regra salva: "todos DDD 91 que ouviram ≥80%")
- ⬜ **P2** Validar número no WhatsApp antes de discar (economiza chamada)
- ⬜ **P2** Enriquecimento (foto, nome business, status)

## 4. ANALYTICS / DASHBOARD
- ⬜ **P0** Métricas por campanha isoladas (taxa atendimento, escuta média, interesse)
- ⬜ **P1** Funil: enviados → atenderam → ouviram tudo → responderam → interessados
- ⬜ **P1** Gráficos temporais (dia/hora), heatmap de melhor horário
- ⬜ **P1** Comparativo entre campanhas (tabela lado a lado)
- ⬜ **P1** Melhor horário de atendimento (data-driven, do histórico)
- ⬜ **P2** Exportar relatório (PDF/CSV)
- ⬜ **P2** Custo por lead / ROI se houver preço configurado
- ⬜ **P2** Alertas (ex: taxa de falha alta = risco de ban)

## 5. ANTI-BLOQUEIO / SAÚDE DO NÚMERO
- ⬜ **P0** Perfil de comportamento configurável (delays, jitter, simultâneas, horário)
- ⬜ **P1** Health score do número (baseado em falhas, bloqueios, denúncias)
- ⬜ **P1** Circuit breaker: pausa automática se detecta padrão de bloqueio
- ⬜ **P1** Respeitar janela de horário comercial por timezone do DDD
- ⬜ **P2** Rotação inteligente de proxy por número
- ⬜ **P2** Detecção de shadowban (mensagens não entregam)

## 6. AGENTE IA / VOZ
- ⬜ **P1** Escolher voz TTS no painel (várias vozes PT-BR edge-tts)
- ⬜ **P1** Preview do áudio TTS antes de disparar
- ⬜ **P1** Base de conhecimento (RAG) pro agente responder sobre o negócio
- ⬜ **P1** Múltiplos agentes/personas por campanha
- ⬜ **P2** Clonagem de voz (ElevenLabs) opcional
- ⬜ **P2** Interrupção natural (barge-in): cliente fala e IA para

## 7. TELEGRAM BOT
- ⬜ **P1** Fluxo "manda áudio → manda número → liga tocando" (plano pure-fluttering-wadler)
- ⬜ **P1** Notificações de campanha no Telegram (progresso, interessados)
- ⬜ **P1** Comandos: /campanhas, /status, /interessados
- ⬜ **P2** Disparar campanha pelo Telegram

## 8. INTEGRAÇÕES
- 🔨 **P0** n8n: workflow de exemplo testando cada endpoint (pedido da dona)
- ⬜ **P1** Webhook de eventos rico (campanha, resposta, interesse) — já tem base
- ⬜ **P1** Chatwoot: empurrar interessados como conversa/contato
- ⬜ **P1** Zapier/Make via webhook genérico
- ⬜ **P2** CRM externo (HubSpot/RD Station/Pipedrive)
- ⬜ **P2** Google Sheets sync (resultados em planilha ao vivo)

## 9. SAAS / MULTI-TENANT / BILLING
- ⬜ **P1** Onboarding melhor (primeiro login guiado)
- ⬜ **P1** Planos/limites por tenant (nº chamadas/mês, campanhas)
- ⬜ **P1** Billing (Stripe/Mercado Pago) — cobrança recorrente
- ⬜ **P1** Uso/consumo por tenant (dashboard de billing)
- ⬜ **P2** White-label (cada cliente com sua marca/logo/domínio)
- ⬜ **P2** Convites/equipe (múltiplos usuários por tenant, papéis)

## 10. UX / PAINEL
- 🔨 **P0** Melhorar visual (tema preto atual fica estranho)
- ⬜ **P1** Tema claro/escuro polido + acessibilidade
- ⬜ **P1** Responsivo mobile de verdade
- ⬜ **P1** Player de áudio inline (ouvir gravações no painel)
- ⬜ **P1** Loading/empty/error states consistentes
- ⬜ **P2** i18n (PT/EN/ES)
- ⬜ **P2** Notificações in-app (toast de campanha concluída)

## 11. INFRA / QUALIDADE
- ⬜ **P1** Deploy incremental do client (não rebuildar tudo sempre)
- ⬜ **P1** Healthcheck endpoint + monitor
- ⬜ **P1** Backup automático do Postgres (campanhas, contatos)
- ⬜ **P1** Logs estruturados por tenant + retenção
- ⬜ **P2** Testes automatizados dos endpoints SaaS
- ⬜ **P2** Rate limit por tenant no gateway
- ⬜ **P2** Registro Docker interno (evitar rebuild por nó)

## 12. COMPLIANCE / LEGAL (importante p/ não tomar processo)
- ⬜ **P0** Opt-out obrigatório e persistente (LGPD/Anatel)
- ⬜ **P1** Registro de consentimento por contato
- ⬜ **P1** Aviso legal no áudio ("para sair diga...")
- ⬜ **P2** Retenção/expurgo de dados configurável (LGPD)
- ⬜ **P2** Termos de uso / política no cadastro

---

## Ordem de execução escolhida (autônoma, "faça tudo")
Blocos que se reforçam, do que já tem base pro que é novo:
1. **Fase 3b** — UI de campanhas (backend já pronto) ← AGORA
2. **Fase 2** — filtros de contatos + listas personalizadas + exportar p/ campanha
3. **Fase 5** — config anti-bloqueio por campanha (horários/delays/simultâneas) + opt-out
4. **Fase 4** — transcrição da resposta + tag interesse (STT já no ar)
5. **Fase 8** — workflow n8n testando cada endpoint
6. **Fase 1b** — polimento visual
7. **Fase 6** — teste ponta-a-ponta com o número 559184698653
Demais (billing, RAG, white-label, importar CSV) ficam no backlog P1/P2 pra depois.

## 13. ONBOARDING / TUTORIAIS (pedido 2026-07-11 — P0)
- ⬜ **P0** Abas/página de Tutoriais no painel (texto + passo-a-passo)
- ⬜ **P0** Tooltips (hover) explicando cada campo/botão pra leigo
- ⬜ **P0** Guia passo-a-passo "até a primeira ligação" (wizard: conectar WhatsApp → importar/selecionar contatos → subir áudio → disparar)
- ⬜ **P1** Banner/checklist de primeiros passos no Dashboard (some quando completo)
- ⬜ **P1** Tour guiado interativo (destaca elementos na tela)
- ⬜ **P1** Textos de ajuda contextuais em cada aba (o que é, pra que serve)
- ⬜ **P2** Vídeos curtos embutidos

## 14. TUTORIAL GUIADO INTERATIVO (pedido 2026-07-11 — P0, refina o item 13)
A página Ajuda atual é estática. A dona quer:
- ⬜ **P0** WIZARD de config inicial (setup passo-a-passo que puxa o usuário): 1) conectar número (QR) → 2) colocar chave da IA + escolher provider/modelo → 3) escolher/ativar os bots (WhatsApp/Telegram) → 4) primeira campanha. Aparece no 1º login, com estado de progresso salvo.
- ⬜ **P0** TOUR guiado POR TELA (overlay tipo driver.js/intro.js): destaca cada elemento na própria página com balãozinho explicando ("este botão conecta seu WhatsApp"). Um tour por aba.
- ⬜ **P1** Botão "?" em cada tela reabre o tour daquela tela.
- ⬜ **P1** Tooltips (hover) nos campos técnicos.
- Notas técnicas: avaliar driver.js (leve, sem dep de framework) para o overlay; estado do wizard/onboarding por-tenant (nova coluna ou settings key onboarding_done + steps).
