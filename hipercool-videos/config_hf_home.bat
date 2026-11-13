#!/bin/bash
# Configura HF_HOME para usar D: em vez de C:
# Executar ANTES de qualquer script Python que use HuggingFace/transformers/MusicGen/Whisper

mkdir -p "D:/modelos_cache/huggingface"

# Windows: definir permanentemente via setx (seta pra sessão atual + futuras)
setx HF_HOME "D:/modelos_cache/huggingface"

# Ou exportar só pra sessão atual
export HF_HOME="D:/modelos_cache/huggingface"

echo "HF_HOME agora: $HF_HOME"
echo "Cache HuggingFace move para: D:/modelos_cache/huggingface"
echo ""
echo "Para mover o cache EXISTENTE:"
echo "  1. Copiar: xcopy /E /I /Y 'C:\\Users\\Haylla\\.cache\\huggingface' 'D:\\modelos_cache\\huggingface\\'"
echo "  2. Apagar do C: após confirmar que funciona"
