# 🎬 COMO GERAR UM VÍDEO VEO — PASSO A PASSO (para agente simples)

> **LEIA ISTO PRIMEIRO. Siga na ordem. Copie e cole os comandos exatamente.**
> Este é o guia definitivo. Se algo der errado, veja a seção "SE DER ERRADO" no fim.
> Última validação: 03/07/2026 (funcionou: h264 720x1280 9:16 8s COM áudio).

---

## O QUE ISTO FAZ
Gera um vídeo de ~8 segundos, formato 9:16 (vertical), COM áudio, usando o
Google Flow / Veo 3.1 — de forma 100% automática. Salva um arquivo `.mp4`.

## REGRA DE OURO (decore)
1. **NUNCA** confie que "deu certo" só porque o script imprimiu "OK". **SEMPRE**
   valide o arquivo com `ffprobe` (passo 4). Vídeo bom = mp4 grande (vários MB) com
   áudio. Vídeo ruim = 1.8 KB, mjpeg 512x512, SEM áudio (isso é imagem, jogue fora).
2. Trabalhe SEMPRE nesta pasta: `D:\hipercool-inferior-fix\roteador-veo-api-fake`
3. Use SEMPRE este Python: `D:/hipercool-videos/venv/Scripts/python.exe`
4. Use SEMPRE `PYTHONUTF8=1` antes do comando (senão o console Windows quebra).

---

## PASSO 1 — O Chrome real precisa estar aberto e logado

O bot controla um **Chrome REAL** (não o do Playwright) pela porta 9222.
Verifique se está de pé:

```bash
PYTHONUTF8=1 D:/hipercool-videos/venv/Scripts/python.exe -c "from playwright.sync_api import sync_playwright;\
import sys;\
p=sync_playwright().start();\
b=p.chromium.connect_over_cdp('http://127.0.0.1:9222');\
print('abas:', [pg.url for pg in b.contexts[0].pages])"
```

- **Se listar uma aba com `labs.google/.../flow`** → ótimo, pule pro PASSO 2.
- **Se der erro `ECONNREFUSED`** → o Chrome não está aberto. Rode:

```bash
cd D:/hipercool-inferior-fix/roteador-veo-api-fake
D:/hipercool-videos/venv/Scripts/python.exe chrome_cdp.py open > logs/chrome_open.log 2>&1
```

Um Chrome vai abrir apontando pro Flow. **Se pedir login**, faça o login normal
(email + senha da conta `fabricadeautomacoesia@gmail.com`). Espere ver a caixa de
escrever prompt. (Detalhes de login: `COMO_LOGAR_LEIA_PRIMEIRO.md`.)

---

## PASSO 2 — Gerar o vídeo (UM comando faz tudo)

O comando é: `gera_auto.py "PROMPT EM INGLÊS" caminho/de/saida.mp4`

**Rode em background** (a geração leva ~8 a 15 minutos — é vídeo com áudio real):

```bash
cd D:/hipercool-inferior-fix/roteador-veo-api-fake
PYTHONUTF8=1 D:/hipercool-videos/venv/Scripts/python.exe -u gera_auto.py \
  "A cute orange cat playing in a sunny garden, birds chirping, cheerful sound." \
  videos/saida/meu_video.mp4 > logs/gera.log 2>&1
```

- Troque o texto do prompt pelo que quiser (**escreva em inglês**, funciona melhor).
- Troque `videos/saida/meu_video.mp4` pelo caminho de saída desejado.
- O script sozinho: garante o modo Veo (não Nano/imagem), fixa 9:16, escreve o
  prompt, aprova o popup, espera renderizar e baixa o mp4 via CDN.

---

## PASSO 3 — Acompanhar o progresso

Enquanto roda, veja o log:

```bash
cat D:/hipercool-inferior-fix/roteador-veo-api-fake/logs/gera.log | tail -n 15
```

O que você DEVE ver, em ordem:
```
[veo] modelo selecionado: Veo 3.1 - Fast     <- entrou no modo VÍDEO (bom!)
[veo] painel salvo
[veo] estado: Veo visivel=True
prompt: ... (make it a 8-second video; 9:16 ...; use the Veo 3.1 model; include audio)
posters antes: N
prompt enviado (Enter)
[aprovacao] clique robusto: ok               <- aprovou o popup
...aguardando (1013s) / (1006s) / ...         <- renderizando, é normal demorar
video novo: <id-grande>                       <- render terminou!
CDN: https://flow-content.google/video/...     <- pegou o link do vídeo
OK video salvo: ...\meu_video.mp4              <- baixou!
```

---

## PASSO 4 — VALIDAR (obrigatório, nunca pule)

```bash
F="D:/hipercool-inferior-fix/roteador-veo-api-fake/videos/saida/meu_video.mp4"
echo "=== VIDEO ==="; ffprobe -v error -select_streams v:0 \
  -show_entries stream=codec_name,width,height,duration \
  -of default=noprint_wrappers=1:nokey=1 "$F"
echo "=== AUDIO ==="; ffprobe -v error -select_streams a:0 \
  -show_entries stream=codec_name,channels,duration \
  -of default=noprint_wrappers=1:nokey=1 "$F"
```

**RESULTADO BOM (aceite):**
```
=== VIDEO ===        === AUDIO ===
h264                 aac
720                  2
1280                 8.000000
8.000000
```
h264, 720x1280 (9:16), ~8s, e áudio aac. Arquivo tem vários MB. ✅

**RESULTADO RUIM (rejeite e refaça):**
```
mjpeg
512
512
N/A
(áudio vazio)
```
Isso é uma IMAGEM do Nano Banana, não vídeo. Arquivo tem ~1.8 KB. ❌
→ Refaça do PASSO 2. Se repetir, veja "SE DER ERRADO".

---

## PASSO 5 — Abrir o vídeo pra assistir (opcional)

```bash
powershell.exe -Command "explorer.exe 'D:\hipercool-inferior-fix\roteador-veo-api-fake\videos\saida'"
```
Abre a pasta no Explorer; dê duplo-clique no mp4. (Ou abra no Chrome:
`file:///D:/hipercool-inferior-fix/roteador-veo-api-fake/videos/saida/meu_video.mp4`.)

---

## SE O DOWNLOAD FALHAR MAS O VÍDEO EXISTE

Às vezes o vídeo renderiza mas o download engasga (o log mostra `video novo: <id>`
mas termina com erro). Nesse caso, baixe manualmente com o script dedicado, passando
o id que apareceu no log:

```bash
cd D:/hipercool-inferior-fix/roteador-veo-api-fake
PYTHONUTF8=1 D:/hipercool-videos/venv/Scripts/python.exe baixa_veo.py <ID-DO-VIDEO> videos/saida/meu_video.mp4
```
(Ou use `auto` no lugar do id pra pegar o último vídeo da grade.) Depois valide (PASSO 4).

---

## SE DER ERRADO — diagnóstico rápido

| Sintoma no log / arquivo | Causa | O que fazer |
|---|---|---|
| `ECONNREFUSED 127.0.0.1:9222` | Chrome fechado | PASSO 1 (rodar `chrome_cdp.py open`) |
| "navegador não é seguro" ao logar | logou no Chrome errado | Ver `COMO_LOGAR_LEIA_PRIMEIRO.md`, usar só o Chrome da porta 9222 |
| arquivo 1.8KB / mjpeg 512x512 / sem áudio | caiu no modo IMAGEM (Nano Banana) | Refazer PASSO 2. `garantir_modo_veo()` deve corrigir; se não, abra o painel manual e escolha "Omni Flash → Veo 3.1 - Fast" |
| `timeout sem video novo` | render demorou > ~17 min | Refazer. Pode ser fila/cota do Google; espere um pouco |
| `HTTP 400` no download | tentou baixar pelo jeito antigo (trpc) | Usar `baixa_veo.py` (baixa via CDN) — já é o padrão no gera_auto.py |
| `nao capturei URL do CDN` | o vídeo não tocou pra revelar o link | Refazer download; garantir que a aba do Flow está visível/ativa |

---

## POR QUE FUNCIONA (resumo técnico, pra quem quiser entender)

- **Modo Veo:** o painel de config (ícone `tune`) tem 2 dropdowns de modelo. O
  "🍌 Nano Banana" é de IMAGEM. O **"Omni Flash"** é o de VÍDEO — abrindo ele
  aparecem `Veo 3.1 - Lite/Fast/Quality`. A função `garantir_modo_veo()` seleciona
  Veo 3.1 - Fast + 9:16 + Salvar antes de cada geração, usando clique de MOUSE REAL
  do Playwright (mais confiável que `.click()` JS no React).
- **Download:** o botão da UI e o endpoint `trpc getMediaUrlRedirect` NÃO funcionam
  de fora (400/CORS). A solução: dar `video.play()` e interceptar a resposta de rede
  cuja URL contém `flow-content.google/video/` (link assinado do CDN), baixando com
  `ctx.request.get(url)` (usa os cookies do contexto).

Detalhes completos: `GUIA_AUTOMACAO_FLOW_VEO.md` (Regra #0). Histórico: `ESTADO_DO_PROJETO.md`.
