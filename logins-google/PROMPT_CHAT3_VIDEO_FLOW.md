# PROMPT — CHAT 3: VÍDEO (Roteador VEO / Google Flow)

> Cole isto num chat novo pra trabalhar SÓ na geração de vídeo IA via Google Flow.
> Autossuficiente.

---

Você é meu parceiro técnico no projeto **Roteador VEO** — um wrapper que transforma o
Google Flow (labs.google/fx, codinome interno "PINHOLE") numa API REST de geração de
vídeo IA. Trabalho local, commit/push só com minha confirmação. Responder em pt-BR.

## Onde mora
- Código: `D:\hipercool-inferior-fix\roteador-veo-api-fake\`
- Doc completa: `D:\roteador-veo-docs\` (00_INDICE … 05_CAPACIDADES_FLOW)
- Python: `D:\hipercool-videos\venv\Scripts\python.exe` (sempre `PYTHONUTF8=1`). Playwright + ffmpeg ok.

## Como funciona (essencial)
- Flow é um **AGENTE CONVERSACIONAL**: não tem seletor de modelo. Ele lê o prompt e decide
  modelo (Omni Flash / Veo 3.1), se gera imagem ou vídeo, e formato. Endpoint interno:
  `aisandbox-pa.googleapis.com/v1/flowCreationAgent/sessions/{id}`.
- Forçar modelo/áudio via TEXTO do prompt ("8-second video with audio using Veo 3.1").
- Ratio (16:9/9:16) + duração (1x-4x) via painel Configurações (ícone `tune`). Botão gerar = ícone `arrow_forward`.
- Setting "Confirmar antes de gerar = Nunca" → gera automático.
- Login: Chrome REAL via CDP (`--remote-debugging-port`) porque Google barra Chromium de automação.

## Estado atual (2026-07-01)
- `flow_bot.py` já aceita: `aspect_ratio`, `duration`, `model`, `audio`, `image` (image-to-video), `auto_confirm`.
- `api_server.py` (porta 8790) repassa todos esses params no POST `/v1/videos/generations`.
- **5 sessões locais capturadas e ativas** em `roteador-veo-api-fake\sessions\`: fabrica,
  mundosolar1995, canalalucinaai, seebotsia, emersonjosiel649.
- fabrica: conta com 970 créditos, Veo 3.1.

## Regras fixas do pipeline (do CLAUDE.md hipercool)
- Sempre validar vídeo com `ffprobe` antes de dizer "pronto" (áudio >5s menor que vídeo = quebrado).
- ffmpeg sempre em background task. Nunca 2 capítulos simultâneos.

## Tarefas possíveis
1. **PRIORIDADE — validar áudio + vertical:** os 3 vídeos já gerados estão em 1920x1080 SEM
   áudio (bot antigo, confirmado por ffprobe — é a origem da queixa "não tem áudio"). O flow_bot
   NOVO aceita aspect_ratio/duration/audio mas isso NÃO foi testado com geração real. Gerar 1 vídeo
   `{"account":"fabrica","aspect_ratio":"9:16","duration":"8S","audio":true,"model":"Veo 3.1"}` e
   validar com ffprobe que saiu 1080x1920 COM áudio. Se vier mudo, desativar o toggle
   "Retornar vídeos sem áudio" nas Settings do Flow via automação.
2. Testar image-to-video (animar uma foto).
3. Implementar rotação entre as 5 contas no api_server (proteger de rate-limit).
4. Explorar mais capacidades do Flow (ver 05_CAPACIDADES_FLOW.md: characters, tools, etc).

Comece pela tarefa 1: subir o api_server e gerar o vídeo de teste 9:16 com áudio, depois valida com ffprobe.
