# Código Legado N8N — Effects Engine V5.1 Ultimate

## O que contém (MASSIVO):
- 60 filtros visuais (Tier 1-4: backgrounds suaves, clarity, atmosphere, impacto)
- 80+ transições (fade, wipe, slide, glitch, manhwa action, wind, spiral)
- 85+ movimentos (vertical pan, zoom facial, Ken Burns, drift, shake)
- Sistema de áudio profissional (LUFS normalization, ducking, de-esser, compression)
- SFX por emoção com ducking inteligente
- Legendas .ass com estilos por contexto (whisper, shout, thought)
- Configurações de performance (GPU auto-detect, cache, memory management)

## Melhorias prioritárias pra portar:

### 1. TRANSIÇÕES (80+ vs nossas ~20)
Adicionar ao effects_engine: glitch, wind, spiral, crosswarp, mosaic, hextile
→ Especialmente as estilo manhwa: hlwind, vuwind, glitchmem

### 2. MOVIMENTOS (85 vs nossos ~15)
- Vertical pan com DRIFT lateral suave (sin/cos) ← MUITO BOM
- Zoom com DELAY/SUSPENSE (pausa antes de zooar)
- Zoom com EASING (ease-in, ease-out, smooth)
- Ken Burns com crop + movimento

### 3. ÁUDIO PROFISSIONAL
- Ducking: reduzir música quando narração fala (0.08 durante fala, 0.12 normal)
- Normalização LUFS -16 (padrão YouTube)
- De-esser (remove sibilância)
- SFX com volume 0.35 e fade in/out

### 4. SFX POR EMOÇÃO
- Cada emoção tem SFX específico (impacto, whoosh, riser, etc.)
- Volume reduzido (0.35) pra não sobrepor narração
- Ducking na narração durante SFX

### 5. SYSTEM DE MEMÓRIA
- Trackeia color grading entre páginas (continuidade visual)
- Trackeia direção de movimento (não repetir mesmo movimento 2x seguidas)
- Smoothing window de 3 páginas

## Status: SALVO. Implementar incrementalmente nas próximas sessões.
