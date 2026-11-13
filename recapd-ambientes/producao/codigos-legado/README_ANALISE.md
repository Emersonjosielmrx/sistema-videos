# Código Legado N8N — Análise de Reaproveitamento

## Origem
Workflow n8n "ORGANIZA + EDITA IMAGENS V11 — VIRAL ENGINE" + "PROCESSA RESPOSTA DO AGENTE V10"

## O que contém de útil pro hipercool-inferior:

### 1. Filtros Virais por Emoção (7 filtros FFmpeg)
Já parcialmente implementado no effects_engine.py, mas os filtros do n8n são mais elaborados:

- **HYPE (Dopamina)**: saturação alta, nitidez, cores vivas → comédia, vitória, feliz
- **DEEP (Imersão)**: contraste alto, escurece, vinheta, ruído filme → terror, tensão, mistério
- **IMPACT (Ação)**: nitidez extrema, contraste, sombra → luta, raiva, impacto
- **NOSTALGIA (Sépia)**: tom sépia, suavidade, cores lavadas → flashback, tristeza, memória
- **LOVE (Bloom)**: tom rosado, brilho, suavidade → romance, amor, timidez
- **STANDARD (Polido)**: tratamento profissional neutro → cenas normais
- **CENSURA (Safe)**: escurece, dessatura → imagens censuradas

### 2. Mapeamento Emoção → Filtro
```
romance/amor/paixão → LOVE
tensão/medo/horror → DEEP
ação/raiva/luta → IMPACT
flashback/tristeza → NOSTALGIA
comédia/vitória → HYPE
neutro → STANDARD
censura → CENSURA
```

### 3. Sistema de Estado/Checkpoint
- Salva progresso por página (pode retomar de onde parou)
- Backups com timestamp
- Evita reprocessamento

### 4. Detecção de Emoção por Palavras-chave
Dicionário extenso de palavras → emoção (português) que pode ser integrado no `detect_mood_from_text()` do effects_engine.

## Status: SALVO PARA REFERÊNCIA. Implementar filtros virais no effects_engine numa próxima sessão.
