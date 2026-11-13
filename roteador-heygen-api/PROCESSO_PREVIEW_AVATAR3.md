# PROCESSO CORRETO: Render Scene -> Download Video (SEM CREDITOS)

Data: 2026-07-05 (atualizado com descobertas reais)
**ESTE DOCUMENTO E A VERDADE ABSOLUTA. NAO PODE SER PERDIDO NEM CONTRADITO.**

---

## RESUMO EM 1 FRASE

Entrar no editor create-v4, digitar o roteiro, clicar **Render Scene** (NAO
Generate), esperar ~23s, o video aparece como <video src=scene_previews...>
no DOM, baixar essa URL diretamente. Produz WebM completo (video+audio).

---

## REGRAS ABSOLUTAS

1. **NUNCA** clicar em Generate/Gerar - PROIBIDO (gasta creditos)
2. **USAR** Render Scene - gera preview completo sem gastar creditos
3. O video final e um **WebM COMPLETO** (audio + video juntos)
4. **PROIBIDO** usar screencast + ffmpeg + frames + audio separado
5. A URL do video fica em: resource2.heygen.ai/scene_previews/...
6. O botao correto tem texto "Render Scene" com icone SVG #render-up

---

## PASSO A PASSO

### 1. Entrar na pagina de criacao
- URL: https://app.heygen.com/create-v4 (editor de video)
- Conta: fabricadeautomacoesia@gmail.com
- Chrome real via CDP (porta 9225)
- Esperar carregar (contenteditable aparece)

### 2. Digitar o roteiro/texto
- Campo: .tiptap.ProseMirror[contenteditable="true"]
- Ctrl+A > Delete > digitar texto

### 3. Clicar "Render Scene"
- Botao com texto "Render Scene" (parte inferior direita do painel)
- NAO e o botao "Generate" (PROIBIDO - gasta creditos)
- O Render Scene faz uma renderizacao de preview

### 4. Esperar video aparecer no DOM (~23s)
- Monitorar: document.querySelectorAll('video')
- Quando um <video> ganha src contendo "scene_previews"
- Esse e o video pronto

### 5. Baixar o video
- GET na URL com cookies da sessao (context.request.get)
- Formato: WebM (VP9 + Opus)
- Tamanho tipico: 500KB-2MB
- Resolucao: ~888x784 (preview quality)

### 6. Validar com ffprobe
- Confirmar codec_type video + audio
- Se tiver ambos = SUCESSO

---

## DESCOBERTAS TECNICAS (2026-07-05)

- O botao #preview-button (SVG play no topo) NAO gera video baixavel
- O "Preview" do editor moderno (Avatar IV) renderiza em WebGL/canvas em tempo real
- **Render Scene** e o que realmente produz um arquivo de video no servidor
- URL padrao: resource2.heygen.ai/scene_previews/{account}/{draft}-{hash}-{timestamp}.webm
- O video pode ser baixado com cookies do contexto Playwright
- Audio TTS disponivel separadamente em resource2.heygen.ai/text_to_speech/...wav
- "Avatar 3" mencionado pela usuaria = provavelmente "Avatar IV" (motor atual)

---

## DIFERENCAS DO QUE A USUARIA DESCREVEU vs REALIDADE

| Usuaria disse | Realidade atual |
|---|---|
| Selecionar "Avatar 3" | Motor atual = Avatar IV (sem selecao necessaria) |
| Clicar PLAY superior direito | Isso ativa WebGL, nao baixa video |
| Tela mostra "Preview" | Preview e renderizacao em tempo real |
| Video fica no F12/HTML | SIM! Mas apos "Render Scene", nao apos Play |
| MP4 | WebM (VP9+Opus) - funciona igual |

---

## FLUXO DE AUTOMACAO (Playwright CDP)



---

## REFERENCIAS

- Conta: fabricadeautomacoesia@gmail.com
- Porta CDP: 9225
- Editor: https://app.heygen.com/create-v4/
- Pasta de saida: D:/roteador-heygen-api/videos/api_jobs/
- Script: D:/roteador-heygen-api/preview_avatar3.py
- Validacao: ffprobe confirma VP9 video + Opus audio
- Video existente validado: preview_scene.webm (897KB, 888x784)
