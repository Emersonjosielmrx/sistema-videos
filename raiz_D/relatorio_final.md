# Diagnóstico: OmniRoute Opus 4.6 (2026-10-18)

## Problema Inicial
- Opus 4.6 retornava 403 após testar apenas 8 contas
- OmniRoute parava sem tentar as outras 61 contas ativas

## Descobertas

### 1. Sistema de Priorização NÃO Funciona
Testei modificar todos os campos possíveis:
- ❌ `priority` — ignorado
- ❌ `global_priority` — ignorado  
- ❌ `created_at` — ignorado
- ❌ `id` (UUID) — ignorado

**Conclusão:** OmniRoute v3.8.51 tem ordenação hardcoded no código.

### 2. Sistema "Quota-Aware" com Cache
- OmniRoute mantém cache em memória de quais contas têm quota
- Cache baseado em tentativas recentes (últimos ~5 min)
- Quando todas falham, retorna: "All accounts exhausted (cached quota state)"
- Cache expira após 5 minutos da última tentativa

### 3. Fallback Limitado
- Após um 403/429, OmniRoute bloqueia aquela conta por 5s para o modelo
- NÃO tenta automaticamente as outras 60+ contas na mesma requisição
- Cliente precisa retentar para forçar próxima conta

### 4. Estado Real das Contas (18/10 01:46 UTC)
Testei as 14 contas com menos tentativas históricas:
- **Todas retornaram 429 "Resource exhausted"**
- Nenhuma tem quota de Opus 4.6 disponível no momento

## Ações Tomadas

1. ✅ Reativadas todas as 130 contas Antigravity
2. ✅ Criado script de teste: `/d/testar_opus.py`
3. ✅ Documentado comportamento do sistema quota-aware

## Recomendações

**Curto prazo:**
- Aguardar ~1h e tentar Opus 4.6 novamente
- Google pode resetar quotas de algumas contas nesse período

**Médio prazo:**
- Implementar retry automático no cliente (3-5 tentativas com 2s entre cada)
- Cada retry força OmniRoute a testar próxima conta disponível

**Longo prazo:**
- Atualizar OmniRoute para versão que respeita campos de priorização
- Ou: patch no código para ordenar por `global_priority DESC, created_at ASC`

## Estado Final

- **130 contas ativas** (todas Antigravity reativadas)
- OmniRoute testará amplamente quando houver nova requisição
- Sistema quota-aware funcionando (cache limpa em 5 min)

---
**Data:** 2026-10-18 01:49 UTC
**Resultado:** Problema diagnosticado. Todas as contas Opus 4.6 estão sem quota no momento.
