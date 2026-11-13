# OmniRoute — Combos de Mídia (Áudio + Imagem)

## Resumo

O OmniRoute (`157.173.207.22:20128`) agora tem combos separados por modelo de mídia, cada um com fallbacks automáticos. Isso permite que qualquer script/pipeline chame um modelo específico pelo nome e, se falhar, ele tenta o próximo silenciosamente.

---

## Combos de Áudio (4 combos)

Cada modelo de áudio tem seu combo dedicado pra poder escolher a "voz" desejada:

| Combo | Modelo #1 (prioridade) | Fallbacks | Tipo |
|---|---|---|---|
| `lyria-3-pro` | `openrouter/google/lyria-3-pro-preview` [FREE] | lyria-clip → gpt-audio-mini → gpt-audio | Música (geração) |
| `lyria-3-clip` | `openrouter/google/lyria-3-clip-preview` [FREE] | lyria-pro → gpt-audio-mini → gpt-audio | Música curta (clipes) |
| `gpt-audio-mini` | `openrouter/openai/gpt-audio-mini` [PAGO] | gpt-audio → lyria-pro → lyria-clip | Chat com voz (TTS) |
| `gpt-audio` | `openrouter/openai/gpt-audio` [PAGO] | gpt-audio-mini → lyria-pro → lyria-clip | Chat com voz (TTS best) |

### O que cada um faz:

- **Lyria 3 Pro** — Gera **música/trilhas** a partir de texto. Ex: "Uma trilha épica de batalha com tambores japoneses". Retorna áudio inline. GRÁTIS.
- **Lyria 3 Clip** — Idem mas pra **clipes curtos** (~30s). GRÁTIS.
- **GPT Audio Mini** — Chat que responde em **voz humana**. Aceita áudio como input também. PAGO.
- **GPT Audio** — Versão premium do GPT Audio Mini, melhor qualidade de voz. PAGO.

### Como chamar (Python):

```python
import urllib.request, json, base64

def gerar_audio(prompt, modelo="openrouter/google/lyria-3-pro-preview"):
    """Gera áudio via OmniRoute. O combo faz failover automático."""
    url = "http://157.173.207.22:20128/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer <SEGREDO_REMOVIDO>"
    }
    body = json.dumps({
        "model": modelo,
        "messages": [{"role": "user", "content": prompt}],
        "modalities": ["audio"],  # IMPORTANTE: pedir output audio
    }).encode()
    
    req = urllib.request.Request(url, data=body, headers=headers)
    resp = urllib.request.urlopen(req, timeout=180)
    data = json.loads(resp.read())
    
    # O áudio vem em base64 no campo audio
    audio_b64 = data["choices"][0]["message"].get("audio", {}).get("data")
    if audio_b64:
        return base64.b64decode(audio_b64)
    return None

# Exemplos de uso:
# Trilha épica
audio = gerar_audio("Compose an epic battle soundtrack with Japanese drums, 30 seconds", 
                     modelo="openrouter/google/lyria-3-pro-preview")

# Clipe curto de suspense  
audio = gerar_audio("A short suspenseful music clip for a manhwa reveal scene",
                     modelo="openrouter/google/lyria-3-clip-preview")

# Voz narrada (TTS via GPT)
audio = gerar_audio("Leia em português brasileiro com voz dramática: 'Ele nunca imaginou que aquele seria seu último dia.'",
                     modelo="openrouter/openai/gpt-audio-mini")
```

---

## Combo de Imagem (1 combo único)

| Combo | Modelos (prioridade) | Tipo |
|---|---|---|
| `image-gen` | Gemini Flash Lite Image → Flash Image → 2.5 Flash Image → Pro Image → Flash Preview → Pro Preview → GPT-5.4 Image → GPT-5 Mini Image → GPT-5 Image | Geração de imagem |

### Como chamar (Python):

```python
def gerar_imagem(prompt, modelo="openrouter/google/gemini-3.1-flash-lite-image"):
    """Gera imagem via OmniRoute. Qualquer modelo de imagem funciona (failover automático)."""
    url = "http://157.173.207.22:20128/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer <SEGREDO_REMOVIDO>"
    }
    body = json.dumps({
        "model": modelo,
        "messages": [{"role": "user", "content": prompt}],
        "modalities": ["image"],  # IMPORTANTE: pedir output imagem
    }).encode()
    
    req = urllib.request.Request(url, data=body, headers=headers)
    resp = urllib.request.urlopen(req, timeout=180)
    data = json.loads(resp.read())
    
    # Imagem vem em base64
    for part in data["choices"][0]["message"].get("content", []):
        if isinstance(part, dict) and part.get("type") == "image_url":
            img_b64 = part["image_url"]["url"].split(",")[-1]
            return base64.b64decode(img_b64)
    return None
```

---

## Integração com hipercool-fix

### Áudio (NÃO substitui TTS narração!)

Os modelos de áudio do OmniRoute **NÃO são TTS de narração** — são geradores de música (Lyria) e chat com voz (GPT Audio). O pipeline hipercool-fix já tem 3 engines de narração:

| Engine | Var de ambiente | Uso |
|---|---|---|
| edge-tts | `TTS_ENGINE=edge` (default) | Grátis, sem API, vozes Microsoft |
| ElevenLabs | `TTS_ENGINE=eleven` | Vozes masculinas premium |
| Gemini TTS | `TTS_ENGINE=gemini` | Melhor qualidade, com quota |

**Onde os modelos OmniRoute servem:**
1. **Lyria** → Gerar **trilhas sonoras/moods** sob demanda (ex: mood "batalha" gera música épica)
2. **GPT Audio** → Gerar **voiceover em inglês** ou **efeitos de voz** que edge-tts não faz

### Imagem

O combo `image-gen` pode ser usado pra:
1. Gerar **thumbnails** de capítulos automaticamente
2. Gerar **assets visuais** (backgrounds, overlays)
3. Gerar **mascotes/poses** sob demanda

---

## Mappings do OmniRoute

```
openrouter/google/lyria-3-pro-preview    →  combo lyria-3-pro     (prio 8)
openrouter/google/lyria-3-clip-preview   →  combo lyria-3-clip    (prio 8)
openrouter/openai/gpt-audio-mini         →  combo gpt-audio-mini  (prio 8)
openrouter/openai/gpt-audio              →  combo gpt-audio       (prio 8)
openrouter/google/gemini-*-image*        →  combo image-gen       (prio 8)
openrouter/openai/gpt-*-image*           →  combo image-gen       (prio 8)
openrouter/google/nano-banana*           →  combo image-gen       (prio 8)
```
