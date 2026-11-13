# MUDANCA: Cache HuggingFace movido de C: para D:

## O que mudou
O cache do HuggingFace (`C:\Users\Haylla\.cache\huggingface`) foi movido para `D:\.cache\huggingface`.
- **Liberados ~3 GB em C:** (de 13.6 GB para 16.6 GB livres)
- **HF_HOME** agora aponta permanentemente para `D:\.cache\huggingface`

## Como isso afeta os agentes
- **depth-anything** (parallax 2.5D) ja esta no D: — funciona normalmente
- **musicgen** e **faster-whisper** vao baixar novamente na primeira vez que forem usados (HF_HOME baixa automatico)
- Se o agente usa `transformers`, `musicgen_local`, ou qualquer lib HuggingFace — nao precisa mudar nada, HF_HOME esta configurado no sistema

## Como verificar
```bash
# Linux/Mac
echo $HF_HOME

# Windows PowerShell
echo $env:HF_HOME
# Deve retornar: D:\.cache\huggingface
```

## Onde estao os modelos agora
- `D:\.cache\huggingface\hub\models--depth-anything--Depth-Anything-V2-Small-hf` (95 MB)
- `D:\.cache\huggingface\hub\models--facebook--musicgen-small` (vai baixar 2.5 GB na primeira execucao)
- `D:\.cache\huggingface\hub\models--Systran--faster-whisper-small` (vai baixar 464 MB na primeira execucao)
- `D:\.cache\huggingface\hub\models--Systran--faster-whisper-tiny` (vai baixar 75 MB na primeira execucao)

## Se precisar forcar HF_HOME em um script
```python
import os
os.environ['HF_HOME'] = r'D:\.cache\huggingface'
```
