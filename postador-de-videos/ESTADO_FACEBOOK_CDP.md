# Estado do Facebook CDP Poster — FUNCIONANDO (2026-08-25)

## Status: COMPLETO E VALIDADO

Postagem de Reels no Facebook via Playwright CDP está 100% funcional.
Teste real postou com sucesso na página `mundosolarenergia`.

## O que funciona (fluxo completo)
1. **Conexão CDP** porta 9401 (Chrome + perfil `msenergypara`)
2. **Navegação** para página → /reels/ → "Criar Reel"
3. **Upload** via `expect_file_chooser` + clique no botão "Carregar" (intercepta diálogo nativo)
4. **Navegação multi-tela** — Reel Studio tem 3 telas:
   - Upload → clica "Avançar" #1
   - Edição/trim (com "Encurtar vídeo", "Legendas ocultas") → clica "Avançar" #2
   - Descrição + "Publicar"
5. **Caption** preenchida via contenteditable fallback
6. **Publicar** clicado (botão aparece como "Postar")
7. **Confirmação** detectada automaticamente

## Método de upload que FUNCIONA
**Playwright `expect_file_chooser`** — intercepta o file dialog nativo quando se clica "Carregar".

## Métodos de upload que NÃO funcionam (testados e descartados)
1. `DOM.setFileInputFiles` — `files.length` fica 0, React ignora
2. `element.click()` JS — evento "untrusted", Chrome recusa file picker
3. `Input.dispatchMouseEvent` + FileChooser — FileChooser nunca dispara
4. `Input.dispatchDragEvent` — drop executa mas files=0
5. `set_input_files` no input[type=file] — UI não muda
6. JS DataTransfer drop — não efetivo

## Arquivo principal
- `D:\postador-de-videos\bin\facebook_cdp_poster.py` (~340 linhas, Playwright)

## Uso
```bash
cd /d/postador-de-videos
PYTHONUTF8=1 /d/hipercool-videos/venv/Scripts/python.exe bin/facebook_cdp_poster.py \
  --video "D:/ms-energy/videos/shorts_veo/video.mp4" \
  --caption "Texto #hashtags" \
  --port 9401 \
  --page "https://www.facebook.com/mundosolarenergia/"
```

## Chrome CDP
- BAT: `D:\postador-de-videos\bin\start_cdp_instagram.bat`
- Perfil: `D:\logins-google\chrome-profiles\msenergypara`
- Logado no Facebook como MS Energy (página `mundosolarenergia`)
