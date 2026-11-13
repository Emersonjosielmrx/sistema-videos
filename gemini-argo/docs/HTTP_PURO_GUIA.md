# HTTP Puro em vez de Navegador — Guia para Outros Projetos

## O que fizemos

Substituímos o Playwright (abre Chrome, clica, digita, espera) por uma chamada HTTP direta
ao endpoint interno do Google. O resultado:

- **12.6× mais rápido** (9s vs 115s)
- **25× menos RAM** (~20 MB vs ~500 MB)
- **6× mais concorrência** (6 vs 2 simultâneas)
- **Streaming real** (token a token)

## Como funciona

1. **Pegar cookies UMA vez** pelo navegador (CDP `Network.getAllCookies`)
2. **GET na página** pra extrair tokens da sessão (`SNlM0e`, `cfb2h`, `FdrFJe`)
3. **POST direto** no endpoint interno com os cookies + headers de seleção de modelo
4. **Parsear** a resposta (formato `wrb.fr` com JSON aninhado)
5. Os cookies se **auto-renovam** pelo Set-Cookie de cada chamada
6. **Mas morrem em horas** se o Chrome do cofre abrir a mesma conta (ele gira o `__Secure-1PSIDTS` e a cópia
   fica inválida — visto em 27/10: as 6 contas Argon caíram ~6 h depois). Por isso o cliente tem que se
   **ressincronizar sozinho**: `gemini_http._abrir()` detecta o login perdido, pega cookies novos pelo cofre
   (~15–150 s, navegador invisível) e repete a chamada. Copie esse padrão em qualquer cliente HTTP novo.

## Receita passo a passo (para qualquer serviço Google)

### 1. Capturar o protocolo

```python
# Abra o navegador, faça a ação manualmente e capture TODOS os requests
from playwright.sync_api import sync_playwright

requests_capturados = []
def on_req(req):
    if req.method == "POST" and req.post_data:
        requests_capturados.append({
            "url": req.url,
            "headers": dict(req.headers),
            "post": req.post_data[:5000],
        })
pg.on("request", on_req)

# ... faça a ação (postar vídeo, upload, etc) ...
# Salve em JSON e analise: qual POST faz a ação real?
```

### 2. Identificar o endpoint real

Procure o POST que contém o payload da ação. Exemplos:

| Serviço | Endpoint interno | O que faz |
|---------|-----------------|-----------|
| Gemini chat | `/_/BardChatUi/data/.../StreamGenerate` | Enviar prompt |
| YouTube Studio | `https://studio.youtube.com/youtubei/v1/upload/...` | Upload de vídeo |
| YouTube Studio | `https://studio.youtube.com/youtubei/v1/video_manager/metadata` | Título, desc, agendar |
| TikTok | `https://www.tiktok.com/api/v1/item/create/` | Postar vídeo |
| Google Veo | Endpoint de geração dentro do AI Studio | Gerar vídeo |

### 3. Extrair os tokens anti-CSRF

Todo serviço Google tem tokens na página HTML. Padrão:

```python
import re

html = session.get("https://SERVICO.google.com/...").text

# Gemini: SNlM0e (token CSRF "at")
at = re.search(r'"SNlM0e":"([^"]+)"', html).group(1)

# YouTube Studio: INNERTUBE_API_KEY e SAPISIDHASH
api_key = re.search(r'"INNERTUBE_API_KEY":"([^"]+)"', html).group(1)

# Genérico Google: procure por tokens em window.__INITIAL_DATA__ ou WIZ_global_data
```

### 4. Montar a sessão HTTP

```python
import requests

# Cookies extraídos do CDP UMA vez
cookies = json.load(open("cookies/conta.json"))

s = requests.Session()
s.cookies.update(cookies)
s.headers.update({
    "User-Agent": "Mozilla/5.0 ...",  # MESMO do Chrome real
    "Origin": "https://SERVICO.google.com",
    "Referer": "https://SERVICO.google.com/",
    "x-same-domain": "1",  # Google exige em vários serviços
})
```

### 5. Fazer a chamada

```python
r = s.post(ENDPOINT, data=payload, headers=headers_especificos)
# ou para upload:
r = s.post(ENDPOINT, files={"file": open("video.mp4", "rb")}, ...)
```

### 6. Renovar cookies automaticamente

```python
# Depois de cada chamada, salve os cookies atualizados
cookies_atuais = json.load(open("cookies/conta.json"))
cookies_atuais.update(s.cookies.get_dict())
json.dump(cookies_atuais, open("cookies/conta.json", "w"))
```

## Projetos candidatos (ordem de impacto)

### 1. Google Veo (MAIOR ganho)
- **Atual**: abre Chrome, navega pro AI Studio, clica em gerar, espera
- **HTTP**: POST direto no endpoint de geração, poll no status
- **Ganho esperado**: elimina ~30s de setup por geração + libera RAM dos notebooks
- **Onde**: `D:\flow-imagens\cliente.py`, notebooks x200ma/acer
- **Cuidado**: upload de imagem/vídeo pode precisar de endpoint separado (resumable upload)

### 2. YouTube Studio (postagem)
- **Atual**: Playwright abre Studio, preenche campos, seleciona playlist, agenda
- **HTTP**: `youtubei/v1` API interna com SAPISIDHASH auth
- **Ganho esperado**: ~20s por vídeo postado, sem Chrome ocupando RAM
- **Onde**: `D:\video-fila\` (postador), `anime_publish`, `story_pipeline`
- **Cuidado**: upload usa protocolo resumable do Google (Scotty); metadata é JSON simples

### 3. TikTok (postagem)
- **Atual**: navegador com login por cookies
- **HTTP**: API interna do TikTok Creator
- **Ganho esperado**: ~15s por post + elimina suspensões por "aparelho novo"
- **Onde**: `D:\projetos-navegador\postador\`
- **Cuidado**: TikTok tem anti-bot forte (X-Bogus, msToken); pode precisar de lib como `tiktok-signature`

### 4. Instagram (postagem)
- **Atual**: API oficial via n8n + navegador para algumas ações
- **HTTP**: Instagram Private API (headers X-IG-App-ID, X-CSRFToken)
- **Onde**: `D:\projetos-navegador\postador\`, n8n VPS 209
- **Cuidado**: Instagram bane hard por API não-oficial; talvez não valha o risco

### 5. Kwai (postagem)
- **Atual**: ainda sem postador (59/60 contas logadas)
- **HTTP**: investigar API interna antes de construir o postador com Playwright
- **Onde**: novo, ainda não existe

## Feito: métricas do YouTube sem navegador (`youtube_http.py`, 27/10)

| O quê | Endpoint | Login | Tempo |
|---|---|---|---|
| Inscritos, views totais, views de cada vídeo/Short | `www.youtube.com/youtubei/v1/browse` | não | ~1,5 s/canal |
| Views, horas, inscritos, impressões, CTR, duração média (7/28/90/365 dias ou tudo) + top vídeos com CTR | `studio.youtube.com/youtubei/v1/yta_web/get_cards` | sim | ~2,5 s |
| Uploads: privacidade, agendado_para, views, likes, comentários, engaged views, reivindicação de terceiros, restrição, monetização | `studio.youtube.com/youtubei/v1/creator/list_creator_videos` | sim | ~0,5 s |

- Cookies: `python youtube_http.py sync <slug|--todos>` abre o cofre 1× e salva `cookies_youtube/<slug>.json`
  (precisa ser do domínio `.youtube.com`; os do `.google.com` não servem). Conta→canal vem de
  `postador-de-videos\config\youtube_navegador.json`.
- Chave/versão/canal saem do HTML de `studio.youtube.com/` (`INNERTUBE_API_KEY`, `INNERTUBE_CLIENT_VERSION`, `CHANNEL_ID`).
- Cabeçalhos: `Authorization: SAPISIDHASH ...` com origin `https://studio.youtube.com`, `X-Origin`, `x-goog-authuser: 0`;
  `context.client.clientName = 62`.
- Campos do `mask` que funcionam: `publicMetrics`, `privateMetrics`, `claimDetails`, `monetization`,
  `allRestrictions`, `scheduledPublishingDetails` (`metrics` NÃO existe, volta vazio).
- O corpo das chamadas do Studio vai em gzip; ao capturar use `req.post_data_buffer` + `gzip.decompress`.
- Substitui os tokens OAuth dos canais (que vencem) sem chave de API no Google Cloud.

## Headers que o Google sempre pede

```
x-same-domain: 1                    — obrigatório em quase tudo
x-goog-ext-525001261-jspb: [...]   — seleção de modelo (Gemini)
SAPISIDHASH                         — auth derivada do cookie SAPISID
x-goog-authuser: 0                 — qual conta do Google (multi-login)
x-origin: https://...              — igual ao Origin
```

### Como calcular o SAPISIDHASH (YouTube Studio, Drive, etc.)

```python
import hashlib, time

def sapisidhash(sapisid, origin):
    ts = int(time.time())
    raw = f"{ts} {sapisid} {origin}"
    h = hashlib.sha1(raw.encode()).hexdigest()
    return f"SAPISIDHASH {ts}_{h}"

# Uso: headers["Authorization"] = sapisidhash(cookies["SAPISID"], "https://studio.youtube.com")
```

## Quando NÃO funciona

- **Captcha/verificação**: se o Google pedir captcha, precisa do navegador naquele momento
- **JavaScript obrigatório**: se o token anti-CSRF é gerado por JS complexo (não está no HTML)
- **Mudança frequente**: endpoints internos mudam sem aviso; ter fallback pro navegador
- **Upload com DRM/fingerprint**: TikTok e Instagram podem fingerprint o upload

## Padrão recomendado

```
cookies/         <- cookies cacheados por conta (JSON)
sync_cookies.py  <- pega cookies via Chrome 1× por conta
cliente_http.py  <- faz a ação via HTTP puro
cliente_nav.py   <- fallback com Playwright (manter!)
proxy.py         <- OpenAI-compatible se precisar de interface padronizada
```

Sempre manter o fallback com navegador. O HTTP é o caminho rápido; o navegador é o seguro.
