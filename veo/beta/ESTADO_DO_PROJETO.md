# Estado do Projeto - Integração Google Flow (Veo)

## O que foi Concluído ✅
1. **Automação Estável do Google Flow (`gera_auto.py`)**:
   - Desenvolvemos um script que usa o Playwright via CDP para interagir com uma aba de Chrome Real (única forma de não cair na "boca do leão" dos bloqueios de segurança do Google em contas OAuth).
   - Resolvemos o bloqueio de "Aprovar e não perguntar de novo" injetando um clique simulado robusto.
   - Encontramos um jeito indireto de forçar formato `9:16`, `duração: 8S` e `audio` sem depender do botão "Settings" do Flow (que buga). Passamos essas diretrizes como system prompt embutido no final da mensagem do usuário.
   - O detector de vídeo pronto parou de se perder nas dezenas de divs não identificadas do DOM do Google, passando a checar arrays de _posters_ (as tags `<img>` e conexões ao serviço `getMediaUrlRedirect`).
   - Implementado o baixe `_download_via_button()` e também fallback para requisição direta HTTP pela API interna (`trpc`) enviando os cookies do Playwright.
   - Documentamos tudo isso em um guia: `GUIA_AUTOMACAO_FLOW_VEO.md`.

2. **Como Logar Corretamente (`COMO_LOGAR_LEIA_PRIMEIRO.md`)**:
   - Escrito roteiro claro do porquê `p.chromium.launch()` falha para sempre e como fazer o login abrindo a porta de debug 9222.

## Dificuldades e Limitações (o que falta / para o próximo dev)
1. Atualmente o processo de geração é muito longo; a página principal recarrega com timeout de OOM (Out Of Memory) muito rápido ou o Playwright perde o handle. O timeout padrão está configurado para 10 a 15 minutos em script porque os vídeos com áudio do Veo levam cerca de 8 minutos.
2. O script de geração avulso que _reutilizaria abas_ (`gera_reusando_aba.py`) ainda não teve todos os seus event handlers unificados com o `gera_auto.py`.
3. Integração desse fake-api de Flow `/generate_veo` com a Pipeline principal de Shorts ainda tem que ser feita. Isso permitirá a criação original de *memes autossuficientes* em MP4 no formato 9:16 gerado pelo Google Veo 3 / 3.1.

### Atualização Importante (03/07/2026)
Rodamos o `gera_auto.py` pela última vez. Foi testado com `A cute orange cat walking slowly through a sunny garden, cinematic, high detail. (make it a 8-second video; 9:16 vertical portrait aspect ratio; use the Veo 3 model; include audio)`.
Infelizmente ele sofreu `timeout sem video novo` (esperou por 10 minutos (600s) e não completou o download/geração). Isto evidencia a limitação documentada acima no item 1, pois renderizações longas com áudio no lado do Google costumam ter demoras severas (maiores que 10 minutos).

No próximo dev-cycle, será preciso aumentar o timeout para ex. 1200 segundos nas renderizações de 8s+ com áudio, ou fazer o script encerrar educadamente e rodar um outro processo em background que fica em polling checando o DOM uma vez a cada 30 segundos, ao invés de se prender via Playwright sincronizado.

### ⛔ CAUSA RAIZ DESCOBERTA (03/07/2026) — NANO BANANA (modo imagem)
Depois de vários runs, o problema real NÃO era só timeout: o compositor do Flow
estava caindo no **🍌 Nano Banana (modo IMAGEM)** em vez do **Veo (vídeo)**.
- Sintoma: baixava `test_img.png...jpeg` — arquivo de **1.8KB, mjpeg 512x512, SEM
  áudio, duration=N/A**. Confirmado 2x com `ffprobe`. Não é vídeo nenhum.
- Aumentei `GEN_TIMEOUT_S` de 480 → 900 em `config.py` (bom pra render longa),
  mas isso NÃO resolve o Nano Banana — apenas evita timeout prematuro.
- **Documentei a Regra #0 no `GUIA_AUTOMACAO_FLOW_VEO.md`**: como reconhecer o
  Nano Banana pelos sintomas, por que acontece (clicar radios do painel `tune`
  ou "Nova conversa" switcha pra imagem) e a regra de SEMPRE validar com `ffprobe`
  antes de dar qualquer vídeo como pronto.
- **PENDENTE p/ próximo agente**: garantir programaticamente que a UI está em modo
  Veo antes de submeter (detectar `/edit/` na URL ou 🍌 na tela e corrigir), e só
  então enviar o prompt. Sem isso, o resultado continua saindo como imagem.

### 🎉 RESOLVIDO (03/07/2026) — PIPELINE VEO FUNCIONANDO END-TO-END
As duas pendências foram resolvidas e o fluxo completo foi validado:

1. **Trocar pro modo Veo** — a solução é o dropdown **"Omni Flash"** no painel `tune`
   (é o seletor de modelo de VÍDEO; abrindo mostra `Veo 3.1 - Lite/Fast/Quality`).
   O outro dropdown (🍌 Nano Banana) é o de IMAGEM. Função `garantir_modo_veo()`
   adicionada ao `gera_auto.py`: abre `tune`, seleciona `Veo 3.1 - Fast`, fixa `9:16`,
   salva. Usa clique de mouse REAL (`page.mouse.click` no bounding box) que é mais
   confiável que `.click()` JS pra dropdowns do React.

2. **Baixar o mp4** — botão UI e trpc não funcionam (400/CORS). A solução: abrir a
   view do vídeo, dar `video.play()`, interceptar a URL do CDN
   (`flow-content.google/video/...?Expires=...&KeyName=...`) e baixar com
   `ctx.request.get(url)` (usa cookies do contexto). Integrado no `gera_auto.py` e
   também no script standalone `baixa_veo.py`.

**Validação (ffprobe) do vídeo gerado `videos/teste_veo/dog_veo.mp4`:**
- Vídeo: **h264, 720x1280 (9:16), 8.0s** ✅
- Áudio: **aac, 2 canais (estéreo), 8.0s** ✅ ← TEM ÁUDIO!
- Tamanho: 5.8 MB (vs 1.8 KB da imagem Nano — diferença gritante).

**Próximo passo (integração):** plugar `gera_auto.py` no pipeline de shorts do
hipercool pra gerar memes/clipes originais 9:16 com áudio via Veo 3.1.
