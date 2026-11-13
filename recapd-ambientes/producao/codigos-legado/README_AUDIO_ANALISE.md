# Código Legado N8N — Sistema de Áudio TTS

## Origem
Workflow n8n de geração de áudio com Gemini TTS + ElevenLabs + controle de qualidade.

## O que contém de útil pro hipercool-inferior:

### 1. Sistema de Seleção de Voz (node "define voz")
- Fila GLOBAL masculina (nunca reseta entre obras = variedade)
- Fila LOCAL feminina (reseta por obra = prioriza vozes "jovens anime")
- Anti-repetição: nunca usa mesma voz duas vezes seguidas
- Memória por personagem via Redis (no nosso caso, usamos hash determinístico — similar)
- **STATUS: JÁ IMPLEMENTADO** no nosso edge_tts_engine.py (via hash por persona)

### 2. Rotação de Chaves Inteligente (node "roteador")
- 3 modos: sequencial, random, balanceado
- Pool embaralhado por execução
- Contador de chamadas por chave
- Marca chave com erro + timestamp
- **STATUS: PARCIALMENTE IMPLEMENTADO** — nosso gemini_tts.py já rotaciona, mas sem modo random/balanceado

### 3. Multi-idioma (node "separa vozes")
- Detecta lang_code (PT_BR, EN, ES, etc.)
- Pasta destino por idioma
- Valida se áudio saiu na língua certa (QA)
- **STATUS: NÃO IMPLEMENTADO** — estrutura pronta pra adicionar (desligado por enquanto)

### 4. Consolidação de Falas
- Junta falas consecutivas do mesmo personagem num único áudio
- Evita clips muito curtos (< 2 chars)
- Monólogo detection (ajusta palavras por tela)
- **STATUS: JÁ IMPLEMENTADO** parcialmente no hiper-pipeline (clean_for_tts)

### 5. Geração de Legendas SRT
- Timing por bloco de palavras (8 palavras/tela, 10 pra monólogos)
- Velocidade diferente: narrador 0.40s/palavra, personagem 0.34s/palavra
- Pausa extra em pontuação
- UTF-8 BOM pra compatibilidade
- **STATUS: IMPLEMENTADO** no hiper-pipeline (sistema de karaokê/legendas)

### 6. Controle de Qualidade de Áudio (node "controle de qualidade")
- Usa Gemini pra ouvir o áudio gerado e verificar:
  - Se leu metadados/tags por engano
  - Se a língua está correta
  - Se a voz travou/falhou
  - Se há erros graves de pronúncia
- Feedback loop: reprovar → re-gerar com instrução de correção
- **STATUS: NÃO IMPLEMENTADO** — requer IA, guardar pra futuro

### 7. Palavras Proibidas
- Extrai [tags de emoção] do texto e verifica se a IA não as leu em voz alta
- **STATUS: IMPLEMENTADO** — nosso _tts_filter.py já limpa tags antes de mandar pro TTS

## Implementações prioritárias (sem IA):
1. ✅ Filtros virais por emoção — FEITO
2. ✅ Dicionário expandido de moods — FEITO
3. ⬜ Multi-idioma (estrutura desligada) — FUTURO
4. ⬜ QA de áudio com Gemini — FUTURO (requer quota)
5. ⬜ Rotação balanceada/random de chaves — MELHORIA MENOR
