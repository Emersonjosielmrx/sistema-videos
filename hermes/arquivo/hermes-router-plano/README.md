# Hermes Router - Roteador de Números para Ligações em Massa

Sistema de roteamento inteligente de números para campanhas de divulgação do Hermes Call.

## Visão Geral

O Hermes Router é um sub-projeto do Hermes Call focado em **roteamento otimizado de números** para ligações em massa, especialmente para divulgação do próprio sistema Hermes.

## Objetivo

Distribuir ligações de divulgação de forma inteligente entre múltiplas linhas WhatsApp, otimizando:
- Taxa de sucesso de conexão
- Evitar bloqueios
- Balanceamento de carga
- Rastreamento de resultados

## Arquitetura Planejada

```
┌─────────────────────────────────────┐
│      Hermes Router                  │
│   (Roteador Inteligente)            │
└──────────┬──────────────────────────┘
           │
    ┌──────┴───────┐
    │   Regras de  │
    │   Roteamento │
    └──────┬───────┘
           │
    ┌──────▼────────────────────┐
    │  Distribuição por:        │
    │  - DDD                    │
    │  - Operadora              │
    │  - Horário                │
    │  - Taxa de sucesso        │
    └──────┬────────────────────┘
           │
    ┌──────▼────────────────────┐
    │  Múltiplas Linhas WA      │
    │  (Hermes Call)            │
    └───────────────────────────┘
```

## Features Planejadas

### Core
- [ ] Importação de listas de números (CSV, Excel, Google Sheets)
- [ ] Roteamento inteligente por DDD
- [ ] Balanceamento entre linhas WhatsApp
- [ ] Controle de ritmo (rate limiting)
- [ ] Blacklist/DNC (Do Not Call)

### Analytics
- [ ] Dashboard de acompanhamento
- [ ] Taxa de sucesso por DDD/operadora
- [ ] Histórico de tentativas
- [ ] Relatórios de performance

### Integração
- [ ] API REST para Hermes Call
- [ ] Webhooks de status
- [ ] Sincronização com CRM

## Stack Tecnológica (Proposta)

### Backend
- **Linguagem:** Go (mesmo do Hermes Call)
- **Banco:** PostgreSQL
- **Cache:** Redis (opcional)

### Frontend
- **Framework:** React + TypeScript (mesmo do Hermes)
- **UI:** Radix UI + Tailwind CSS

## Estrutura de Diretórios (Proposta)

```
hermes-router/
├── cmd/
│   └── server/          # Servidor principal
├── internal/
│   ├── router/          # Lógica de roteamento
│   ├── campaign/        # Gerenciamento de campanhas
│   ├── analytics/       # Analytics e relatórios
│   └── integration/     # Integração com Hermes Call
├── web/                 # Frontend React
├── docs/                # Documentação
├── deploy/              # Scripts de deploy
└── tests/               # Testes
```

## Casos de Uso

### 1. Divulgação Hermes Call
- **Cenário:** Ligar para empresas divulgando o Hermes
- **Volume:** 1000-10000 números/dia
- **Mensagem:** Pitch do Hermes Call
- **Objetivo:** Agendar demonstrações

### 2. Campanhas Regionais
- **Cenário:** Focar em regiões específicas
- **Roteamento:** Por DDD (ex: SP 11, RJ 21)
- **Personalização:** Mensagem adaptada por região

### 3. Re-engajamento
- **Cenário:** Retomar contato com leads antigos
- **Filtros:** Último contato > 30 dias
- **Estratégia:** Mensagem diferente

## Roadmap

### Fase 1 - MVP (Semana 1-2)
- [ ] Estrutura básica do projeto
- [ ] Importação de números (CSV)
- [ ] Roteamento simples por DDD
- [ ] Integração básica com Hermes Call API

### Fase 2 - Core Features (Semana 3-4)
- [ ] Dashboard web
- [ ] Controle de ritmo
- [ ] Blacklist/DNC
- [ ] Analytics básico

### Fase 3 - Otimizações (Semana 5-6)
- [ ] Roteamento inteligente (ML)
- [ ] A/B testing de mensagens
- [ ] Relatórios avançados

## Questões para Definir

1. **Roteamento:** Baseado em quais critérios principais?
   - DDD?
   - Operadora?
   - Histórico de sucesso?
   - Horário?

2. **Integração:** Como se comunica com Hermes Call?
   - API REST do Hermes?
   - Banco compartilhado?
   - Message queue?

3. **Deploy:** Onde vai rodar?
   - Mesma VPS do Hermes?
   - VPS separada?
   - Serverless?

4. **Escalabilidade:** Volume esperado?
   - Quantas ligações/dia?
   - Quantas linhas WhatsApp?
   - Quantas campanhas simultâneas?

## Próximos Passos

1. Definir especificações técnicas
2. Criar estrutura inicial do projeto
3. Implementar MVP de roteamento
4. Integrar com Hermes Call
5. Deploy em ambiente de teste

---

**Data de criação:** 03/10/2026  
**Versão:** 0.1.0 (Planejamento inicial)  
**Projeto pai:** Hermes Call
