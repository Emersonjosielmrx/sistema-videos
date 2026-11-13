# Campanha Hermes - Sistema Completo de Captação e Gestão

**Sub-projeto do Hermes Call para captação inteligente de clientes**

---

## 🎯 Visão Geral

Sistema integrado ao Hermes Call focado em **captação massiva e inteligente de clientes**, com segmentação por potencial de contratação e ticket médio, gestão completa do funil e agentes IA especializados por segmento.

## 📋 Escopo Completo

### Não é Apenas Roteamento
É um **sistema completo de captação**, desde a prospecção até o fechamento:

1. **Segmentação Inteligente**
2. **Ligações em Massa**
3. **Centralização de Atendimento**
4. **Gestão do Funil**
5. **Agentes IA Especializados**
6. **Analytics e Otimização**

---

## 🎭 Segmentação de Público

### Critérios de Segmentação

#### 1. Potencial de Contratação (Prioridade ALTA)
**Grupos com maior chance de contratar:**

**Grupo A - Alta Propensão:**
- Empresas já usando automação (n8n, Zapier, Make)
- Equipes de vendas estruturadas (5+ vendedores)
- E-commerce com volume (100+ pedidos/mês)
- SaaS B2B (precisam de atendimento escalável)
- Agências de marketing (revendem soluções)
- Empresas com SAC terceirizado (dor forte)

**Grupo B - Média Propensão:**
- Clínicas/consultórios (agendamento)
- Imobiliárias (qualificação de leads)
- Escolas/cursos (matrículas/suporte)
- Restaurantes/delivery (pedidos)
- Prestadores de serviço (agendamento)

**Grupo C - Exploração:**
- Segmentos não testados
- Empresas em crescimento
- Nichos específicos

#### 2. Ticket que NÃO Reclame do Valor

**Perfil ideal (ticket > R$ 500-1000/mês):**
- Faturamento mensal > R$ 50k
- Já paga por ferramentas SaaS
- Possui equipe de tecnologia
- Investe em marketing digital
- Empresas com > 10 funcionários
- Usa CRM pago (Pipedrive, RD Station, HubSpot)

**Indicadores de poder aquisitivo:**
- Escritório em região nobre
- Site profissional
- Presença digital forte
- Anúncios pagos (Google Ads, Meta Ads)
- Certificações/parcerias

---

## 🔄 Fluxo Completo de Captação

```
┌─────────────────────────────────────────────────────────┐
│ 1. PROSPECÇÃO & QUALIFICAÇÃO                           │
│    - Scraping LinkedIn/Google                           │
│    - Enriquecimento de dados (faturamento, segmento)    │
│    - Scoring automático (A/B/C)                         │
│    - Análise de poder aquisitivo                        │
└────────────────┬────────────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────────────┐
│ 2. PRIMEIRA ABORDAGEM (Ligação em Massa)               │
│    - Agente IA faz pitch inicial                        │
│    - Qualifica interesse (quente/morno/frio)            │
│    - Agenda demonstração (quentes)                      │
│    - Coleta objeções (mornos)                           │
└────────────────┬────────────────────────────────────────┘
                 │
        ┌────────┴────────┐
        │                 │
┌───────▼──────┐  ┌──────▼─────────────────────────────┐
│ 3A. QUENTES  │  │ 3B. MORNOS/FRIOS                   │
│              │  │                                     │
│ - Demo       │  │ - Sequência WhatsApp (follow-up)   │
│   agendada   │  │ - Conteúdo educativo               │
│              │  │ - Casos de sucesso                 │
│ - WhatsApp   │  │ - Re-engajamento (30/60/90 dias)   │
│   pessoal    │  │                                     │
│   admin      │  └─────────────────────────────────────┘
│              │
│ - CRM        │
│   atualizado │
└───────┬──────┘
        │
┌───────▼────────────────────────────────────────────────┐
│ 4. DEMONSTRAÇÃO                                         │
│    - Admin faz demo pessoal                             │
│    - Proposta customizada                               │
│    - Negociação                                         │
└────────────────┬────────────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────────────┐
│ 5. FECHAMENTO                                           │
│    - Contrato assinado                                  │
│    - Onboarding                                         │
│    - Cliente ativo                                      │
└─────────────────────────────────────────────────────────┘
```

---

## 🤖 Agentes IA Especializados

### Estrutura de Agentes

#### 1. Agente Qualificador (Primeira Ligação)
**Função:** Fazer pitch inicial e qualificar
**Persona:** Consultora de negócios
**Objetivo:** Identificar dor e agendar demo

**Variações por segmento:**
- **E-commerce:** Foco em automação de pedidos
- **Clínicas:** Foco em agendamento
- **Agências:** Foco em revendas/white label
- **SaaS:** Foco em redução de CAC

#### 2. Agente de Follow-up (WhatsApp)
**Função:** Nutrir leads mornos
**Persona:** Consultor de vendas
**Objetivo:** Re-engajar e agendar demo

**Estratégias:**
- Enviar casos de sucesso do segmento
- Compartilhar ROI calculado
- Oferecer trial gratuito
- Criar urgência (vagas limitadas)

#### 3. Agente de Suporte Pré-venda
**Função:** Responder dúvidas técnicas
**Persona:** Especialista técnico
**Objetivo:** Remover objeções

#### 4. Agente de Onboarding
**Função:** Integrar novo cliente
**Persona:** Gerente de sucesso
**Objetivo:** Garantir go-live rápido

### Aprendizado Contínuo

**Sistema de feedback:**
```
Ligação → Transcrição → Análise → Refinamento do Prompt
   ↓
Resultado (fechou/não fechou) → Machine Learning
   ↓
Ajuste automático do agente por segmento
```

**Métricas por agente:**
- Taxa de agendamento
- Taxa de conversão
- Tempo médio de ligação
- Objeções mais comuns
- Palavras-chave que convertem

---

## 💬 Centralização de Conversas

### Chatwoot Integrado

**Todos os números de campanha → Chatwoot único**

```
┌──────────────────────────────────────────┐
│  Múltiplos Números WhatsApp              │
│  (Linhas de campanha)                    │
└──────────────┬───────────────────────────┘
               │
               │ Todas mensagens centralizadas
               ▼
┌──────────────────────────────────────────┐
│         Chatwoot Hermes                  │
│                                          │
│  - Inbox único                           │
│  - Tags por segmento                     │
│  - Atribuição automática                 │
│  - SLA tracking                          │
└──────────────┬───────────────────────────┘
               │
       ┌───────┴────────┐
       │                │
┌──────▼──────┐  ┌─────▼──────────┐
│ Notificação │  │ Notificação    │
│ WhatsApp    │  │ Telegram       │
│ Admin       │  │ Equipe         │
└─────────────┘  └────────────────┘
```

### Fluxo de Notificações

**Lead Quente (agendou demo):**
1. WhatsApp admin pessoal: "🔥 Demo agendada - [Nome] - [Segmento] - [Data/Hora]"
2. Telegram admin: Mesma mensagem + link CRM
3. Chatwoot: Conversa aberta + tag "demo-agendada"

**Lead Morno (interessado):**
1. Chatwoot: Tag "morno" + atribuir a agente de follow-up (IA)
2. Telegram: Resumo diário de leads mornos
3. Sem notificação WhatsApp (evita spam)

**Lead Frio (não interessado):**
1. Chatwoot: Tag "frio" + sequência de re-engajamento 60 dias
2. Sem notificações

---

## 📊 Sistema de Gestão (Painel)

### Dashboard Principal

**KPIs Principais:**
- Ligações realizadas hoje
- Taxa de conversão (ligação → demo)
- Taxa de fechamento (demo → cliente)
- Ticket médio
- CAC (Custo de Aquisição)
- ROI da campanha

**Por Segmento:**
- Qual segmento converte melhor?
- Qual tem maior ticket?
- Qual tem menor CAC?
- Objeções mais comuns por segmento

### Funil Visual

```
1000 ligações
  ↓ 15%
150 demos agendadas
  ↓ 30%
45 propostas enviadas
  ↓ 40%
18 clientes fechados

Conversão total: 1.8%
Ticket médio: R$ 850/mês
CAC: R$ 250
LTV estimado: R$ 10.200 (12 meses)
ROI: 40x
```

---

## 🧪 Pesquisa e Testes

### Grupos de Teste

**Teste A/B/C por segmento:**

**Variável 1: Mensagem**
- Pitch A: Foco em automação
- Pitch B: Foco em redução de custos
- Pitch C: Foco em escalabilidade

**Variável 2: Horário**
- Manhã (9-12h)
- Tarde (14-17h)
- Noite (18-20h)

**Variável 3: Abordagem**
- Direta (logo menciona Hermes)
- Consultiva (identifica dor primeiro)
- Educativa (oferece conteúdo antes)

**Variável 4: Agente**
- Voz feminina vs masculina
- Tom formal vs casual
- Velocidade de fala

### Análise de Resultados

**Por segmento:**
```
E-commerce:
  Melhor pitch: A (automação)
  Melhor horário: Manhã
  Melhor agente: Feminino/casual
  Taxa conversão: 3.2%

Clínicas:
  Melhor pitch: C (escalabilidade)
  Melhor horário: Tarde
  Melhor agente: Feminino/formal
  Taxa conversão: 2.8%
```

---

## 🗂️ Estrutura do Projeto

### Diretório Técnico

```
campanha-hermes/
├── README.md                 # Este arquivo
├── RESEARCH.md              # Pesquisas e análises
├── PLAYBOOK.md              # Playbook de vendas
│
├── cmd/
│   └── server/              # API servidor
│
├── internal/
│   ├── prospecting/         # Prospecção e scraping
│   │   ├── linkedin.go
│   │   ├── enrichment.go
│   │   └── scoring.go
│   │
│   ├── segmentation/        # Segmentação inteligente
│   │   ├── rules.go
│   │   └── ml_scoring.go
│   │
│   ├── campaign/            # Gestão de campanhas
│   │   ├── manager.go
│   │   ├── scheduler.go
│   │   └── rate_limiter.go
│   │
│   ├── agents/              # Agentes IA especializados
│   │   ├── qualifier.go     # Primeira ligação
│   │   ├── followup.go      # WhatsApp follow-up
│   │   ├── presales.go      # Suporte pré-venda
│   │   └── onboarding.go    # Onboarding
│   │
│   ├── integration/         # Integrações
│   │   ├── hermes_api.go    # Hermes Call
│   │   ├── chatwoot.go      # Chatwoot
│   │   └── telegram.go      # Notificações
│   │
│   ├── analytics/           # Analytics e ML
│   │   ├── metrics.go
│   │   ├── ab_testing.go
│   │   └── learning.go
│   │
│   └── crm/                 # CRM/Funil
│       ├── pipeline.go
│       └── notifications.go
│
├── web/                     # Frontend
│   ├── dashboard/
│   ├── campaigns/
│   ├── analytics/
│   └── agents/
│
├── data/
│   ├── segments/            # Definições de segmentos
│   ├── pitches/             # Scripts de pitch
│   └── research/            # Dados de pesquisa
│
├── docs/
│   ├── SEGMENTATION.md      # Guia de segmentação
│   ├── AGENTS.md            # Documentação dos agentes
│   └── INTEGRATION.md       # Como integrar com Hermes
│
└── deploy/
    └── setup.sh
```

---

## 🎬 Fases de Implementação

### Fase 1: Fundação (Semana 1-2)
- [ ] Estrutura do projeto
- [ ] Integração com Hermes Call API
- [ ] Importação de listas (CSV)
- [ ] Scoring básico de leads
- [ ] Agente qualificador v1

### Fase 2: Segmentação (Semana 3-4)
- [ ] Sistema de segmentação
- [ ] Pesquisa de mercado (grupos A/B/C)
- [ ] Enriquecimento de dados
- [ ] 3 agentes especializados (e-commerce, clínicas, SaaS)

### Fase 3: Gestão (Semana 5-6)
- [ ] Integração Chatwoot
- [ ] Notificações WhatsApp/Telegram
- [ ] Dashboard analytics
- [ ] Funil visual

### Fase 4: Otimização (Semana 7-8)
- [ ] A/B testing automatizado
- [ ] Machine learning (scoring)
- [ ] Aprendizado contínuo dos agentes
- [ ] Relatórios avançados

### Fase 5: Escala (Semana 9+)
- [ ] Multi-campanha simultânea
- [ ] Mais agentes especializados
- [ ] Integração com mais canais
- [ ] White label para revenda

---

## 📈 Métricas de Sucesso

### KPIs Primários
- **Taxa de Conversão L→D:** Ligação → Demo agendada (meta: >10%)
- **Taxa de Conversão D→C:** Demo → Cliente (meta: >25%)
- **Conversão Total:** Ligação → Cliente (meta: >2.5%)
- **Ticket Médio:** (meta: >R$ 700/mês)
- **CAC:** Custo de Aquisição (meta: <R$ 300)
- **LTV/CAC:** (meta: >30x)

### KPIs Secundários
- Tempo médio de ciclo (ligação → fechamento)
- Taxa de churn primeiros 3 meses
- NPS de clientes captados
- Melhor segmento por ROI

---

## 🚀 Próximos Passos

1. **Definir primeiro segmento de teste** (e-commerce? clínicas?)
2. **Criar primeiro agente qualificador**
3. **Importar lista de 1000 números do segmento**
4. **Rodar campanha piloto (100 ligações)**
5. **Analisar resultados e ajustar**
6. **Escalar**

---

**Início do projeto:** 03/10/2026  
**Projeto pai:** Hermes Call  
**Uso:** Exclusivo conta do dono (pode disponibilizar features após validação)
