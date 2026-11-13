# HANDOFF COMPLETO - Roteador HeyGen API (Preview sem creditos)

Data: 2026-07-04
Projeto em: D:/hipercool-inferior-fix/roteador-heygen-api/
---

## 1. OBJETIVO EXATO (palavras da dona)

A ideia e ir no AI Studio deles [HeyGen] e enviar um prompt pra ver a cena.
Ao lado do botao GERAR tem um botao de PLAY. Clicando nele e possivel abrir
um rascunho previo. Se clicar F12 e inspecionar, da pra baixar o video SEM
clicar em gerar. (ou seja, sem gastar creditos de geracao)

Conta: fabricadeautomacoesia@gmail.com

O produto final e uma API HTTP identica a do Veo (POST /v1/jobs {prompt} ->
poll -> download mp4) que um workflow n8n remoto pode chamar.

---

## 2. COMO FUNCIONA O TRUQUE DO PREVIEW (manual humano)

1. Abrir https://app.heygen.com/ai-studio (logado)
2. Digitar um prompt na caixa de texto
3. AO LADO do botao Generate existe um botao PLAY (triangulo/preview)
4. Clicar no PLAY abre um rascunho/preview do video
5. O preview carrega um elemento video no DOM ou faz request HTTP pra URL de midia
6. Abrir DevTools (F12) > Network > filtrar media ou video
7. A URL do video aparece la - copiar e baixar

IMPORTANTE: o PLAY/PREVIEW nao gasta creditos. So o Generate gasta.
E isso que queremos automatizar via Playwright.

---

## 3. ARQUITETURA (identica ao Veo, portas diferentes)

    Cliente HTTP (n8n, curl)
        |  POST /v1/jobs {prompt}
        v
    heygen_api.py (porta 8798)
        |  thread com lock (1 job por vez)
        v
    heygen_auto.py (Playwright CDP -> Chrome porta 9225)
        |  1. Navega pro AI Studio
        |  2. Digita prompt
        |  3. Clica PLAY (preview, nao Generate)
        |  4. Intercepta URL do video (network listener + DOM video)
        |  5. Baixa o mp4
        v
    videos/api_jobs/{job_id}.mp4

---

## 4. LICOES DO PROJETO VEO (o que deu certo e errado)

### O QUE DEU CERTO (replicar no HeyGen):

1. CHROME REAL VIA CDP - unica forma de nao ser bloqueado pelo Google/OAuth.
   Abrir Chrome com --remote-debugging-port=9225, logar manualmente 1 vez,
   depois Playwright conecta via connect_over_cdp(). O Google (e provavelmente
   o HeyGen) detecta Chromium de automacao e bloqueia. Chrome real = livre.

2. RETRY COM RELOAD - quando a UI fica travada (modal, estado sujo), a unica
   solucao confiavel e recarregar a pagina (page.goto(URL)). Tentamos
   page.click(), dispatchEvent, force=True - NADA fecha modais React stubborn.
   O reload resolve 100%% dos casos.

3. NETWORK INTERCEPTION pra capturar video - registrar page.on(response)
   filtrando por content-type video ou extensao .mp4. Funciona melhor que
   tentar achar botao de download ou usar APIs internas.

4. DOM POLLING como fallback - alem do listener de network, checar
   periodicamente se apareceu um video src=... no DOM. Os dois juntos
   cobrem todos os cenarios.

5. DOWNLOAD VIA CONTEXT AUTENTICADO - usar context.request.get(url) do
   Playwright (carrega os cookies da sessao). Funciona pra CDN que exige auth.

6. LOCK DE CONCORRENCIA - Chrome e recurso unico. Nunca rodar 2 jobs ao mesmo
   tempo. O _gen_lock no servidor garante sequencialidade.

7. VALIDACAO COM FFPROBE - nunca confiar que gerou sem validar. No Veo, o
   script baixava imagens PNG de 1.8KB achando que era video. Sempre checar
   tamanho (>10KB) e idealmente rodar ffprobe pra confirmar codec/duracao.

### O QUE DEU ERRADO (evitar no HeyGen):

1. MODO ERRADO DA UI - no Veo, caiu no Nano Banana (modo imagem) em vez de
   video. Perdi horas gerando PNGs achando que era video. SOLUCAO: ter uma
   funcao garantir_modo_X() que valida/configura o modo ANTES de submeter.
   No HeyGen, verificar que estamos no AI Studio correto, nao em outro editor.

2. SELETORES GENERICOS QUEBRANDO - textarea, button[aria-label*=play] etc
   sao frageis. O site muda, React reusa classes dinamicas. SOLUCAO: ao
   inspecionar pela primeira vez, mapear MULTIPLOS seletores (aria-label,
   data-testid, class parcial, texto visivel) e tentar em cascata.

3. TIMEOUT CURTO DEMAIS - render do Veo levava 8-10 min com audio. Comecamos
   com 480s e perdiamos por timeout. SOLUCAO: timeout generoso (300s pro
   HeyGen deve bastar pra preview, mas ajustar se necessario).

4. DOIS PROCESSOS NA MESMA PORTA CDP - ao subir 2 instancias do servidor,
   ambas conectam no mesmo Chrome e corrompem estado. SOLUCAO: checar se ja
   tem processo rodando antes de subir outro.

5. ASPECTO/CONFIG SAINDO ERRADO - no Veo havia 2 grupos de botao identicos
   (imagem vs video), clicava no errado. SOLUCAO: se houver ambiguidade,
   usar coordenadas (bounding box) ou filtrar por posicao Y no DOM.

6. MODAL DE CREDITOS BLOQUEANDO - apos gerar, Veo mostrava Isso custa N
   creditos que bloqueava .type() do proximo job. SOLUCAO: reload no inicio
   de cada job (ja implementado no heygen_auto.py).

---

## 5. TAREFA DO PROXIMO AGENTE (passo a passo)

### Fase 1: Mapear a UI do HeyGen AI Studio

1. Rodar chrome_cdp.py pra abrir Chrome com CDP na porta 9225
2. Logar com fabricadeautomacoesia@gmail.com
3. Navegar pra https://app.heygen.com/ai-studio
4. Abrir DevTools (F12) e inspecionar:
   - A CAIXA DE PROMPT: qual o seletor? (textarea? contenteditable? input?)
     Anotar: tag, classe, placeholder, data-testid
   - O BOTAO PLAY/PREVIEW: qual o seletor exato?
     Anotar: tag, aria-label, classe, icone, posicao relativa ao Generate
   - O ELEMENTO DE VIDEO que aparece apos clicar Play:
     E um video tag? Um iframe? Um canvas? Qual URL carrega?
5. Testar manualmente: digitar prompt, clicar play, ver no Network tab
   qual request traz o video (URL, headers, content-type)

### Fase 2: Atualizar heygen_auto.py com seletores reais

Editar as funcoes:
- digitar_prompt(): atualizar lista de selectors
- clicar_play(): atualizar lista de selectors do botao play
- capturar_video_url(): ajustar filtros de URL/content-type

### Fase 3: Testar end-to-end

1. Subir API: python -u heygen_api.py
2. Mandar job via curl POST http://127.0.0.1:8798/v1/jobs
   Body: {"prompt": "A woman presenting a product"}
   Header: Authorization: Bearer df0d96157b8b4da29ac552e9aa715450
3. Poll: curl http://127.0.0.1:8798/v1/jobs/JOB_ID
4. Validar: ffprobe videos/api_jobs/JOB_ID.mp4

### Fase 4: Conectar n8n (opcional)

Copiar _criar_workflow_n8n.py do projeto Veo, trocar porta/path, rodar.

---

## 6. ARQUIVOS DO PROJETO

| Arquivo | Status | Funcao |
|---------|--------|--------|
| config.py | PRONTO | Portas, URLs, timeouts |
| chrome_cdp.py | PRONTO | Abre Chrome com CDP porta 9225 |
| heygen_auto.py | SELETORES GENERICOS | Motor Playwright (precisa ajustar) |
| heygen_api.py | PRONTO | Servidor HTTP jobs async |
| .api_token | PRONTO | Token: df0d96157b8b4da29ac552e9aa715450 |
| videos/api_jobs/ | PRONTO | Pasta de saida |

---

## 7. COMO SUBIR DO ZERO

### Pre-requisito: Chrome + Login (1 vez so)

    cd D:/hipercool-inferior-fix/roteador-heygen-api
    D:/hipercool-videos/venv/Scripts/python.exe chrome_cdp.py

- Chrome abre na porta CDP 9225
- Logar com fabricadeautomacoesia@gmail.com
- Navegar ate o AI Studio e deixar la
- Chrome fica rodando (nao fechar)

### Subir a API (Windows cmd)

    cd D:/hipercool-inferior-fix/roteador-heygen-api
    set PYTHONUTF8=1
    set HEYGEN_CDP_PORT=9225
    set HEYGEN_API_PORT=8798
    D:/hipercool-videos/venv/Scripts/python.exe -u heygen_api.py

### Subir a API (bash/git-bash)

    cd D:/hipercool-inferior-fix/roteador-heygen-api
    PYTHONUTF8=1 HEYGEN_CDP_PORT=9225 HEYGEN_API_PORT=8798       D:/hipercool-videos/venv/Scripts/python.exe -u heygen_api.py

### Tunnel (se precisar acesso remoto via n8n)

    D:/hipercool-inferior-fix/roteador-veo-api-fake/bin_tunnel/cloudflared.exe tunnel --url http://127.0.0.1:8798 --no-autoupdate

Anotar URL gerada e setar HEYGEN_PUBLIC_URL.

---

## 8. ENDPOINTS DA API

    POST /v1/jobs
      Body: {"prompt": "..."}
      Headers: Authorization: Bearer TOKEN (se .api_token existir)
      Resposta 202: {"job_id": "abc123", "status": "queued", "status_url": "..."}

    GET /v1/jobs/{id}
      Resposta: {"status": "queued|running|done|error", "video_url": "...", "error": "..."}

    GET /v1/jobs/{id}/video
      Resposta: binary mp4

    GET /health
      Resposta: {"ok": true, "jobs_total": N}

---

## 9. DIFERENCAS VS VEO

| Aspecto | Veo | HeyGen |
|---------|-----|--------|
| Porta CDP | 9224 (seebotsia) | 9225 (fabricadeautomacoesia) |
| Porta API | 8799 | 8798 |
| Site | labs.google/fx | app.heygen.com/ai-studio |
| Captura | CDN intercept apos click poster | Network listener ao clicar Play |
| Custo | Creditos Flow | ZERO (preview nao gasta) |
| Tempo render | 8-10 min | Segundos (preview pre-existente) |
| Modelo | Veo 3.1 Fast | N/A (preview do draft) |
| Validacao | ffprobe obrigatorio | ffprobe obrigatorio |

---

## 10. DICAS DE DEBUGGING

- Se Playwright nao conecta: verificar Chrome rodando com --remote-debugging-port=9225
  Testar: curl http://127.0.0.1:9225/json/version (deve retornar JSON)

- Se login falha: NUNCA usar Chromium do Playwright pra logar. Usar Chrome real.
  Mesmo principio do COMO_LOGAR_LEIA_PRIMEIRO.md do projeto Veo.

- Se seletor nao acha elemento: abrir DevTools Console e testar:
  document.querySelectorAll(SEU_SELETOR) - se retornar vazio, seletor errado.

- Se video nao aparece apos Play: pode ser blob: URL (nao interceptavel via
  network). Nesse caso usar page.evaluate() pra extrair src do video element
  ou usar page.on(request) pra ver URLs pedidas.

- Se arquivo baixado e muito pequeno (<10KB): provavelmente e thumbnail/poster.
  Verificar content-type e tamanho antes de salvar.

- PYTHONUTF8=1 sempre no Windows (evita UnicodeEncodeError).

---

## 11. CONTEXTO DO ECOSSISTEMA

Este projeto faz parte de um conjunto de automacoes:

- D:/hipercool-inferior-fix/roteador-veo-api-fake/ - Veo/Flow (PRONTO, funcional)
- D:/hipercool-inferior-fix/roteador-heygen-api/ - HeyGen (ESTE, em andamento)
- n8n remoto: https://n8n6.inovareinteligenciaartificial.com
- Proxy LLM: http://157.173.207.22:20128 (aceita auto/best-chat, antigravity/*, kr/*)
- Venv: D:/hipercool-videos/venv/Scripts/python.exe (tem Playwright instalado)
- Cloudflared: D:/hipercool-inferior-fix/roteador-veo-api-fake/bin_tunnel/cloudflared.exe

O objetivo maior e ter multiplas fontes de video IA (Veo, HeyGen, etc) todas
expostas como APIs locais que o n8n orquestra pra gerar shorts automaticamente.

---

## 12. REGRAS ABSOLUTAS

1. NUNCA clicar em Generate/Gerar - so no Play/Preview
2. NUNCA confiar que gerou sem ffprobe (licao Veo: PNG de 1.8KB parecia video)
3. NUNCA usar Chromium do Playwright pra logar - so Chrome real via CDP
4. NUNCA rodar 2 instancias na mesma porta CDP
5. SEMPRE reload no inicio de cada job (limpa estado sujo)
6. SEMPRE PYTHONUTF8=1 no Windows
7. SEMPRE testar seletores no Console antes de por no codigo
