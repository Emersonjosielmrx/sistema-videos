# LEIA PRIMEIRO — historias-em-frames

Voce e um agente IA trabalhando no projeto "historias-em-frames".
Este arquivo existe pra voce nao se perder. Leia ANTES de fazer qualquer coisa.

## O que e este projeto?

Um pipeline Python que gera videos FACELESS (sem rosto humano) automaticamente:
1. Gera um roteiro original via Gemini (nenhum conteudo copiado)
2. Gera imagens via IA (OmniRoute/Pollinations)
3. Narra com TTS gratuito (edge-tts)
4. Monta video com efeitos cinematicos (parallax, transicoes, memes, trilha)
5. Valida e exporta MP4 pronto pra YouTube

## Regras ABSOLUTAS (quebre qualquer uma = trabalho perdido)

- DIRETORIO CERTO: D:\historias-em-frames (SOMENTE ESTE)
- PYTHON CERTO: D:\historias-em-frames\venv\Scripts\python.exe
- ENV VAR OBRIGATORIA: PYTHONUTF8=1
- NAO APAGUE CACHES (workspace/cache, workspace/images, workspace/narration_cache)
- NAO TRABALHE EM OUTRO PROJETO (hipercool, hermes, n8n = OUTRO projeto)
- VALIDE COM FFPROBE antes de dizer que terminou

## Comando rapido pra testar se esta tudo OK

```bash
PYTHONUTF8=1 "D:/historias-em-frames/venv/Scripts/python.exe" D:/historias-em-frames/bin/story_pipeline.py \
  --genero superacao --tema "garoto pobre que virou chef" --preset teste --output-suffix _SMOKE
```

Se rodar sem erro e gerar um MP4 em workspace/videos/ = ambiente OK.

## Onde continuar o trabalho?

Leia logs/night-shift.md — la tem o historico do que ja foi feito e o que falta.

## Documentacao completa

Leia CLAUDE.md (mesmo diretorio) pra detalhes de todos os comandos, env vars, presets, e arquitetura.
