# 🎬 RUNBOOK — Produzir Shorts por nicho (canais não-mangá) com Veo 3.1

> Objetivo: gerar shorts 9:16 (~8s, COM áudio, falas em **PT-BR**) pra abastecer os
> canais que NÃO são de mangá (comédia, música, curiosidades, terror, motivação,
> espaço, satisfatório...). Usa o Google Flow/Veo via `gera_auto.py`.
> Leia junto: `COMO_GERAR_VIDEO_VEO_PASSO_A_PASSO.md` (o passo-a-passo base).

---

## REGRAS DESTE PROJETO (decore)
1. **Falas SEMPRE em português.** No prompt, dar a fala exata entre aspas +
   `spoken in Brazilian Portuguese` (ou `says in Brazilian Portuguese: "..."`).
   O Veo respeita muito mais quando a fala é curta e literal.
2. **Todo vídeo é short 9:16, ~8s, com áudio.** `gera_auto.py` já fixa isso.
3. **NUNCA dar "pronto" sem ffprobe.** Bom = h264 720x1280 8s + aac. Ruim = mjpeg
   512x512 sem áudio (Nano Banana → jogar fora e refazer).
4. **ffprobe não ouve o idioma.** Ele confirma que TEM áudio, não que a fala saiu
   em PT-BR. A conferência do idioma é de ouvido (a dona valida no fim).
5. Usar os créditos do Flow ao máximo (há várias contas). Um nicho por vez, valida, próximo.

---

## PILOTOS JÁ VALIDADOS (03/07/2026) ✅
Todos h264 720x1280 (9:16) 8s + aac estéreo:

| Nicho | Arquivo | Tamanho | Fala PT-BR |
|---|---|---|---|
| Comédia | `videos/nichos/comedia/v1.mp4` | 4.27 MB | "Não fui eu, juro." |
| Música (lofi) | `videos/nichos/musica/v1.mp4` | 3.86 MB | (sem fala, só música) |
| Curiosidades | `videos/nichos/curiosidades/v1.mp4` | 2.78 MB | "Você sabia? O fundo do mar..." |
| Terror | `videos/nichos/terror/v1.mp4` | 4.21 MB | "Tem alguém na sua casa." |

Prompts completos de cada nicho: **`PROMPTS_NICHOS_PT.md`**.

---

## 🖼️ IMAGE-TO-VIDEO — animar uma FOTO (validado 03/07/2026) ✅
Dá pra partir de uma imagem (ex: uma foto da dona) e o Veo anima ela em short 9:16
com áudio. Basta passar o caminho da imagem como **3º argumento**:
```bash
cd D:/hipercool-inferior-fix/roteador-veo-api-fake
PYTHONUTF8=1 D:/hipercool-videos/venv/Scripts/python.exe -u gera_auto.py \
  "Animate this image: gentle camera push-in, subtle motion, cinematic depth. Vertical 9:16, ambient sound." \
  videos/teste_img/v1.mp4 \
  "D:/caminho/para/a/foto.jpg" > logs/img2vid.log 2>&1
```
- Formatos aceitos: jpg/png (input `accept=image/*`).
- No log tem que ver `[img] imagem enviada: ...`.
- **Gotcha resolvido:** o thumbnail da imagem enviada aparece como "poster novo" e
  antes era baixado por engano (falhava no CDN). Agora o script TENTA baixar cada
  poster novo; se não tiver `<video>` (é só a imagem), ele loga
  `(nao era video; ignorando esse poster)` e segue esperando o vídeo REAL. Não mexer.
- Piloto validado: `videos/teste_img/v1.mp4` = h264 720x1280 8s + aac (1.71 MB).

---

## PASSO A PASSO (produzir 1 short de um nicho)

### 1. Chrome CDP de pé (uma vez por sessão)
```bash
cd D:/hipercool-inferior-fix/roteador-veo-api-fake
PYTHONUTF8=1 D:/hipercool-videos/venv/Scripts/python.exe -c "from playwright.sync_api import sync_playwright;p=sync_playwright().start();b=p.chromium.connect_over_cdp('http://127.0.0.1:9222');print([pg.url for pg in b.contexts[0].pages])"
```
Se `ECONNREFUSED` → `python chrome_cdp.py open` e logar (ver `COMO_LOGAR_LEIA_PRIMEIRO.md`).

### 2. Gerar (background — leva ~1 a 15 min)
Copie um prompt de `PROMPTS_NICHOS_PT.md`, troque `<nicho>`:
```bash
cd D:/hipercool-inferior-fix/roteador-veo-api-fake
mkdir -p videos/nichos/<nicho>
PYTHONUTF8=1 D:/hipercool-videos/venv/Scripts/python.exe -u gera_auto.py \
  "<PROMPT EM INGLES COM A FALA PT-BR ENTRE ASPAS>" \
  videos/nichos/<nicho>/v1.mp4 > logs/<nicho>.log 2>&1
```

### 3. Acompanhar
```bash
grep -E "modelo selecionado|Veo visivel|video novo|OK video" logs/<nicho>.log
```
Tem que ver `modelo selecionado: Veo 3.1 - Fast`, `Veo visivel=True`, `OK video salvo`.

### 4. VALIDAR (obrigatório)
```bash
F="videos/nichos/<nicho>/v1.mp4"
ffprobe -v error -select_streams v:0 -show_entries stream=codec_name,width,height,duration -of default=noprint_wrappers=1:nokey=1 "$F"
ffprobe -v error -select_streams a:0 -show_entries stream=codec_name,channels,duration -of default=noprint_wrappers=1:nokey=1 "$F"
```
Esperado: `h264 / 720 / 1280 / 8.0` e `aac / 2 / 8.0`. Se `mjpeg 512x512` → refazer.

---

## GOTCHAS APRENDIDOS (03/07/2026) — não repetir os erros

- **Tela `/edit/` trava o painel `tune`.** Se o Chrome parou numa URL com `/edit/`
  (editor de imagem Nano Banana), `garantir_modo_veo()` não acha o `tune` e sai
  imagem. **Fix aplicado:** `gera_auto.py` agora renavega pro projeto se a URL tiver
  `/edit/`. Sintoma no log: `[click 'tune'] falhou` + `Veo visivel=False`.
- **`[click 'Omni Flash'] falhou: TimeoutError` seguido de `modelo selecionado: Veo 3.1`
  é NORMAL** — ele já estava em Veo, então o texto do dropdown não era "Omni Flash".
  Só se preocupe se vier `Veo visivel=False`.
- **Task de background pode congelar num poll** (raro). Sintoma: log para em
  "prompt enviado" e NUNCA loga "...aguardando". Se ficar minutos assim, matar e
  re-disparar (o Chrome geralmente já voltou pra tela limpa, então a 2ª tenta funciona).
- **Nem sempre demora:** se a página já está quente e o render foi rápido, o script
  baixa em ~30-60s. Rápido demais + arquivo pequeno (KB) = desconfiar (pode ser imagem);
  sempre confirmar no ffprobe.

---

## PRÓXIMO (ainda não feito)
- **Mapear qual canal recebe qual nicho.** Os 12 canais não-mangá ("IA/automação")
  hoje não têm nicho fixo definido no disco. Definir isso com a dona.
- **Postagem:** os shorts entram no fluxo de `_LEIA_POSTAR_VIDEOS` /
  `youtube_poster.py` (ver `POSTAGEM_YOUTUBE_PLAYBOOK.md`). Postar de verdade só com OK.
- **Escalar:** rodar N por nicho usando as várias contas do Flow (créditos).
- **Legenda queimada opcional:** se quiser legenda PT-BR no short, passar pelo
  pipeline de legendas do hipercool depois.
