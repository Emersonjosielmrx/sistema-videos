# Verificação de Correlação (15/10/2026 23:38)

## Contexto
Durante a análise de vídeos Veo limpos, 3 vídeos apresentaram correlação início/fim muito baixa (< 0.10), indicando possíveis montagens.

## Vídeos Verificados

### 1. danca_e_musica__20260729_175614.mp4
- **Correlação**: 0.094
- **nota_tiktok**: 0.457
- **Duração**: 8.0s
- **Resultado**: ✓ MONTAGEM confirmada (2 cenas: homem com óculos → palco com robô)
- **Logo TikTok**: ✗ NÃO detectado
- **Marca**: Grok (ambas as cenas)

### 2. segredos_do_oce_20260726_023126.mp4
- **Correlação**: 0.030
- **nota_tiktok**: 0.424
- **Duração**: 8.0s
- **Resultado**: ✓ MONTAGEM confirmada (2 cenas: balão de ar → tubarão)
- **Logo TikTok**: ✗ NÃO detectado
- **Marca**: Grok Veo (ambas as cenas)

### 3. robos_20260725_190200.mp4
- **Correlação**: 0.545
- **nota_tiktok**: 0.421
- **Duração**: 8.0s
- **Resultado**: ✗ Cena única (mesmo personagem segurando lanterna)
- **Logo TikTok**: ✗ NÃO detectado
- **Marca**: Grok Veo

## Conclusões

1. **Correlação baixa detecta montagens**: 2 de 3 vídeos com corr < 0.10 são montagens confirmadas
2. **Sem logo TikTok**: NENHUM dos 3 tem logo TikTok (notas 0.42-0.46, bem abaixo do limiar 0.57)
3. **Origem**: As montagens são junção de 2 cenas Veo limpas (só marca Grok/Grok Veo)
4. **Segurança**: Todas as 3 são LIMPAS para postagem (sem propaganda, sem logo TikTok)

## Decisão: NENHUMA AÇÃO NECESSÁRIA

**Motivo**: 
- O detector de logo TikTok já funciona (limiar 0.57 calibrado)
- As montagens detectadas por correlação baixa NÃO têm logo TikTok
- Já estão aprovadas e são limpas (apenas Grok Veo, sem propaganda)
- Adicionar regra de correlação bloquearia vídeos limpos desnecessariamente

## Recomendação
Manter sistema atual:
- Detector logo TikTok (opencv, limiar 0.57) continua como filtro principal
- Correlação baixa é informativa, mas não requer ação
- Conferência visual de amostra já é feita antes de aprovar lotes

---
**Verificado por**: Modelo Sonnet 4  
**Data**: 15/10/2026 23:38  
**Método**: Extração de quadros (início/meio/último) + inspeção visual
