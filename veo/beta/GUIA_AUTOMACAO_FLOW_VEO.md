# Guia de Automação do Google Flow (Veo)

Este documento sumariza os aprendizados cruciais para contornar as proteções do React/Google no Labs (Flow) ao automatizar gerações de vídeo, focado para agentes de IA operando este repositório.

---

## ⛔⛔ REGRA #0 — NUNCA CAIR NO NANO BANANA (MODO IMAGEM) ⛔⛔

**Este é o erro que mais quebrou vídeos aqui. Leia ANTES de tudo.**

O Flow tem DOIS compositores no mesmo projeto:
- **Veo** = geração de **VÍDEO** (é o que queremos: mp4, com áudio, 8s, 9:16).
- **🍌 Nano Banana / Nano Banana Pro** = geração/edição de **IMAGEM** (NÃO é vídeo).

### Como reconhecer que você caiu no Nano Banana (modo imagem) — SINTOMAS
Se QUALQUER um destes aparecer, você está no modo ERRADO e o resultado será lixo:
- A saída "renderiza" em **poucos segundos** (vídeo Veo leva ~8-15 min).
- O arquivo baixado tem nome tipo **`test_img.png_...jpeg`** (imagem, não mp4).
- `ffprobe` mostra **`mjpeg`, 512x512, sem stream de áudio, `duration=N/A`** e ~1.8KB.
- A URL da aba vira **`.../edit/<uuid>`** (tela de edição de mídia).
- A tela mostra **`🍌 Nano Banana Pro`**, `O que você quer mudar?`, e botões
  `Cortar` / `Selecionar` / `Desenhar` (isso é editor de IMAGEM).

### Por que isso acontece (causa raiz confirmada em 03/07/2026)
- **Clicar em QUALQUER radio do painel de Configurações** (aspect ratio, duração,
  OU o "Nunca perguntar") **switcha o compositor pro Nano Banana (imagem)** e o
  botão de submit de vídeo (`arrow_forward Criar`) some. Por isso o código PULA
  `_set_settings()` de propósito — NÃO reative isso.
- Abrir **"Nova conversa"** também navega pro modo Nano Banana. NÃO clique.
- As dicas de texto no prompt (`8-second video; include audio`) **NÃO salvam** você:
  se a UI está em modo imagem, o agente do Flow obedece o TOGGLE da interface e
  ignora o texto → sai imagem quadrada sem áudio.

### REGRAS DE OURO PARA FICAR NO VEO (vídeo)
1. **NUNCA** clique em radios do painel `tune`/Configurações.
2. **NUNCA** clique em "Nova conversa" / "Nano Banana" / "Nano Banana Pro".
3. **SEMPRE valide o resultado com `ffprobe` ANTES de dizer que deu certo:**
   ```bash
   ffprobe -v error -select_streams v:0 -show_entries stream=codec_name,width,height,duration \
     -of default=noprint_wrappers=1:nokey=1 SAIDA.mp4
   # BOM (Veo):  h264/vp9, 720x1280 (ou 1080x1920), duração ~8s
   # RUIM (Nano): mjpeg, 512x512, duration=N/A, sem áudio  ← JOGUE FORA, refaça
   ```
4. Se o download vier `test_img.png...jpeg` ou `mjpeg 512x512` → **é imagem do
   Nano Banana. NÃO é o vídeo. Descarte e gere de novo garantindo o modo Veo.**
5. Confira que o compositor está em Veo (não `/edit/`, sem 🍌 na tela) ANTES de
   submeter o prompt.

### ✅ COMO TROCAR PRO MODO VEO (solução validada 03/07/2026)
O painel `tune` (Configurações) tem **DOIS dropdowns de modelo**:
- **🍌 Nano Banana** = dropdown de **IMAGEM** (Nano Banana Pro / 2 / 2 Lite). NÃO mexer.
- **"Omni Flash"** = dropdown de **VÍDEO**. Abrindo ele aparecem: `Veo 3.1 - Lite`,
  `Veo 3.1 - Fast`, `Veo 3.1 - Quality`. **É AQUI que se ativa o Veo.**

Passos (função `garantir_modo_veo()` no `gera_auto.py`):
1. Clicar em `tune` pra abrir o painel.
2. Clicar no dropdown **"Omni Flash"** (ou já "Veo 3.1 ...") → escolher `Veo 3.1 - Fast`.
3. Clicar na tab de aspecto `9:16`.
4. Clicar em **Salvar**.
5. Confirmar que "Veo" aparece na barra e "Nano" sumiu.

**Use clique de MOUSE REAL do Playwright, não `.click()` JS:**
```python
loc = page.locator("text=Omni Flash").last
box = loc.bounding_box()
page.mouse.click(box["x"]+box["width"]/2, box["y"]+box["height"]/2)  # abre dropdown
```
O `page.mouse.click` no centro do bounding box é mais confiável que JS pra dropdowns.

### ✅ COMO BAIXAR O MP4 (solução validada 03/07/2026)
O botão "Baixar" da UI e o endpoint `trpc getMediaUrlRedirect` **NÃO funcionam** de
fora (HTTP 400 / CORS / download vai pra pasta do Chrome real e some). O que FUNCIONA:
1. Abrir a view do vídeo (clicar no poster).
2. `page.evaluate("()=>{const v=document.querySelector('video');v.play();}")` — dar play.
3. Interceptar a resposta de rede cuja URL contém **`flow-content.google/video/`**
   (é a URL assinada do CDN, com `?Expires=...&KeyName=...`).
4. Baixar essa URL com `ctx.request.get(url)` (usa os cookies do contexto) e salvar `.body()`.

Ver `baixa_veo.py` para o script standalone. Resultado validado: h264, 720x1280, 8s, **com áudio aac estéreo**.

---

## 1. O Problema do Botão "Aprovar e não perguntar de novo"
Durante a geração ou envio do prompt, o Google frequentemente levanta um modal de consentimento.
- **O que NÃO funciona**: `.click()` padrão do Playwright (Playwright tenta clicar e o React ignora, pois o SVG/Span engole o evento ou o React exige a cadeia completa de `pointer`).
- **A Solução (Clique Robusto)**: É obrigatório simular toda a cadeia de eventos de ponteiro no centro do target. Use o script JS abaixo injetado via `page.evaluate()`:
```javascript
(needle) => {
  let alvo = null;
  document.querySelectorAll('*').forEach(e => {
    const t = (e.innerText || e.textContent || '').trim();
    if (t === needle && e.children.length <= 1) alvo = e;
  });
  if (!alvo) return 'nao-achei';
  let cur = alvo;
  while (cur && !cur.onclick && getComputedStyle(cur).cursor !== 'pointer') cur = cur.parentElement;
  const target = cur || alvo;
  const r = target.getBoundingClientRect();
  const x = r.x + r.width / 2, y = r.y + r.height / 2;
  const opts = {bubbles:true, cancelable:true, clientX:x, clientY:y, view:window, button:0};
  for (const type of ['pointerover','pointerenter','pointerdown','mousedown','pointerup','mouseup','click']) {
    const E = type.startsWith('pointer') ? PointerEvent : MouseEvent;
    target.dispatchEvent(new E(type, opts));
  }
  return 'ok';
}
```

## 2. Parâmetros 9:16, Duração e Áudio
O botão físico de "Settings" (ícone de tune) **NÃO PODE SER USADO**: clicar nos radios dele chaveia o compositor pro Nano Banana (imagem). Ver **Regra #0** acima.
- **A Solução**: O agente conversacional do Flow suporta instruções no final do prompt do usuário. Adicione os parâmetros explícitos entre parênteses.
- Exemplo: `A cute cat (make it a 8-second video; 9:16 vertical portrait aspect ratio; use the Veo 3.1 model; include audio)`
- **ATENÇÃO**: essas dicas de texto só funcionam se a UI JÁ estiver no modo Veo (vídeo). Se estiver no Nano Banana, o texto é ignorado e sai imagem. Sempre valide com `ffprobe`.

## 3. Como detectar que o vídeo ficou pronto?
Painéis do Flow são difíceis de rastrear porque as divs mudam de classe dinamicamente.
- **A Solução**: Monitore as imagens de *poster* (`thumbnail`). Cada vídeo/imagem renderizada expõe uma tag `<img>` cujo `src` possui a rota mágica `getMediaUrlRedirect` com o ID (`name=XXXX`), mesmo antes de o vídeo estar completamente 100% visível/clicável.
- Código para monitorar IDs (guarde o "antes" e pesquise "novos" no loop):
```javascript
Array.from(document.querySelectorAll('img[src*=getMediaUrlRedirect]'))
  .map(i => { const m = i.src.match(/name=([0-9a-f-]+)/i); return m ? m[1] : null; })
  .filter(Boolean)
```

## 4. Como baixar o MP4?
O botão físico de Download no Flow é instável (várias divs de overlay).
- **A Solução**: Escale para chamadas diretas (bypass de UI) via API TRPC!
- Uma vez obtido o `new_id` com a técnica (3) acima, baixe o arquivo via Python (requests) passando os cookies obtidos do browser.
```python
endpoint = f"https://labs.google/fx/api/trpc/media.getMediaUrlRedirect?name={new_id}"
```

## 5. Falhas de Login (Aba Fechando ou Bloqueando)
- **NUNCA** logue ou acesse pelo Playwright nativo abrindo chrome temporário. O Google bloqueia OAuth acusando "O navegador não é seguro".
- Veja `COMO_LOGAR_LEIA_PRIMEIRO.md`. Use **SEMPRE** o Chrome real anexado à porta 9222.
