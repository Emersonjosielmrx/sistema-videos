# Automação via navegador → endpoints API

Padrão geral: abrir o navegador com `cofre.py`, automatizar a interface com
Playwright, e expor como endpoint HTTP (proxy OpenAI-compatible) ou MCP tool.

## O que já funciona (Gemini Argon)

- `gemini_argon.py` — script standalone, abre Chrome via cofre, navega no
  gemini.google.com, seleciona modelo, envia pergunta, coleta resposta
- `gemini_proxy.py` — HTTP server na porta 20140, formato OpenAI `/v1/chat/completions`
- `mcp_argon.py` — MCP server com tool `ask_argon` direto no Claude Code
- `extrair_cookies.py` — extrai cookies do navegador pra usar no OmniRoute gemini-web
- Rotação de contas via `contas_argon.json`, bloqueio automático após 3 erros

## Aplicar o mesmo padrão para:

### 1. Veo (gerar vídeos)
**Onde:** veo.google.com ou labs.google (ImageFX/VideoFX)
**Ação:** enviar prompt de texto → gerar vídeo → baixar o resultado
**Como:**
- Cofre abre a conta Pro no Chrome
- Playwright navega até Veo, digita o prompt, clica gerar
- Espera o vídeo carregar (polling do DOM ou do botão de download)
- Baixa o vídeo via `page.download()` ou CDP `fetch`
- Endpoint: `POST /v1/generate-video {prompt, duration?, style?}`
- Retorno: path do arquivo baixado
**Desafios:** tempo de geração longo (1-5 min), pode ter fila, quota diária
**Código base:** `gemini_argon.py` (navegação, cofre, rotação de contas)
**Já existe:** `D:\flow-imagens` faz algo similar com imagens; ver `bin/veo_gerar.py`

### 2. YouTube (postar vídeos)
**Onde:** studio.youtube.com
**Ação:** upload de vídeo → preencher título/descrição/tags → agendar
**Como:**
- Cofre abre a conta do canal
- Playwright: clicar "Criar" → "Enviar vídeo" → input file → preencher campos
- Definir visibilidade: "Programar" com data/hora (publishAt)
- Aguardar processamento do upload
- Endpoint: `POST /v1/upload-youtube {video_path, title, description, tags, publishAt, channelAccount}`
- Retorno: URL do vídeo, videoId
**Desafios:** upload grande (timeout longo), verificações de direitos autorais
automáticas, popup de monetização, categorias e playlists
**Vantagem sobre API:** sem quota da YouTube Data API v3 (10k unidades/dia)
**Já existe:** `postador\bin` usa web poster; expandir pra endpoint

### 3. TikTok (postar vídeos)
**Onde:** tiktok.com/upload ou TikTok Creator Portal
**Ação:** upload de vídeo → legenda → agendar
**Como:**
- Cofre abre a conta TikTok (login via "Continuar com Google")
- Playwright: ir ao upload, setar arquivo, preencher legenda/hashtags
- Agendar com data/hora ou postar direto
- Endpoint: `POST /v1/upload-tiktok {video_path, caption, hashtags, publishAt, account}`
**Desafios:** TikTok muda UI frequentemente, captcha, verificação por telefone,
limite de uploads por conta/dia, ban detection
**Já existe:** `postador\bin\postar_tiktok.py`; 50 contas no cofre

### 4. Instagram (postar Reels/Stories/Carrossel)
**Onde:** instagram.com (web) ou app via emulador
**Ação:** upload de vídeo/imagem → legenda → postar/agendar
**Como:**
- Cofre abre conta Instagram (1 login por vez, `instagram_local.py`)
- Playwright: ir ao Creator Studio ou feed → criar post → upload → legenda
- Para Reels: upload de vídeo, capa, áudio
- Para Carrossel: múltiplas imagens
- Endpoint: `POST /v1/upload-instagram {media_paths[], caption, type: reel|story|carousel, account}`
**Desafios:** Instagram detecta automação agressivamente, suspensões frequentes,
aparelho novo suspende conta (ver memory), limite por sessão
**Já existe:** `instagram_local.py` loga; `postador\bin` tem lógica parcial

### 5. Kwai (postar vídeos)
**Onde:** kwai.com (web) ou kwai/kuaishou upload
**Ação:** upload + legenda + publicar
**Como:** similar ao TikTok, mesmo padrão
**Status:** 59/60 contas logadas, falta postador (ver PLATAFORMAS_NOVAS_PENDENTE.md)

### 6. Facebook Reels
**Onde:** facebook.com/reels/create
**Ação:** upload de vídeo → descrição → postar
**Como:** Playwright no Facebook web, mesmo padrão
**Status:** planejado em `PLATAFORMAS_NOVAS_PENDENTE.md`

### 7. Dailymotion (recap longo)
**Onde:** dailymotion.com/upload
**Ação:** upload de vídeo longo → título/descrição → publicar
**Como:** mais simples, menos detecção anti-bot
**Vantagem:** aceita vídeos muito longos sem problemas de direitos

## Arquitetura do sistema de endpoints

```
cofre.py (gerenciador de perfis Chrome)
    ↓
automacao_*.py (Playwright por plataforma)
    ↓
proxy_*.py (HTTP server, formato OpenAI ou REST)
    ↓
Claude Code (MCP tools) ou OmniRoute (via SSH tunnel)
```

Cada plataforma segue o padrão:
1. `automacao_<plataforma>.py` — funções de automação (abrir, navegar, agir, coletar)
2. `proxy_<plataforma>.py` — HTTP endpoint REST
3. `mcp_<plataforma>.py` — MCP tool pro Claude Code (opcional)
4. `contas_<plataforma>.json` — estado de rotação das contas

## Prioridade (sugestão)

1. **Veo** — já precisa e as contas Pro já estão logadas
2. **YouTube** — maior impacto, web poster já existe parcialmente
3. **TikTok** — 50 contas prontas, postador existe
4. **Instagram** — mais frágil, mas carrossel dá views
5. **Kwai** — contas prontas, só falta o postador
6. **Facebook/Dailymotion** — menor urgência
