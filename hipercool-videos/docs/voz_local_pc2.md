# Voz local de RESERVA no PC2 — levantamento, conta e passo a passo

> Escrito em 16/10/2026. **Nada foi instalado**: este documento é o levantamento + a receita.
> Responde ao item 11 de `docs/PEDIDOS_DO_DONO_PENDENTES.md` ("Local SÓ como reserva, no PC2").
> Todos os números abaixo foram medidos no PC2 e nos logs de produção, não estimados de cabeça —
> as duas exceções estão marcadas com **(estimativa)** e têm a conta à vista.

## Resposta curta

**Vale a pena, e o motor é o Supertonic-3.** No pior caso que a conta admite, o PC2 gera a voz de um
capítulo em **11 min**; o edge de hoje leva **17–27 min** para o mesmo capítulo. Ou seja, a reserva não
é só "não atrasa a produção" — ela é **mais rápida que o motor principal**, roda em máquina ociosa, sem
cota, sem rede e sem gastar a banda da Webshare (~1 MB por fala = ~100 MB por capítulo hoje).

Ressalva: o Supertonic **não fala tailandês**. O `th` continua no edge/Gemini.

---

## 1. Terreno do PC2 (saída real dos comandos, 16/10/2026)

Levantado por `ssh pc2`:

| Item | Valor medido |
|---|---|
| Python | `3.13.14 (tags/v3.13.14:fd17997, Jun 10 2026) [MSC v.1944 64 bit (AMD64)]`, já no PATH |
| CPU | `Intel(R) Core(TM) i3-7100U CPU @ 2.40GHz` — `NumberOfCores=2`, `NumberOfLogicalProcessors=4`, clock fixo (Kaby Lake U, sem turbo) |
| RAM | `TotalPhysicalMemory=12613070848` = **11,7 GiB** |
| Disco C: | `FreeSpace=22140030976` de `Size=119479406592` = **20,6 GiB livres** de 111,3 GiB |
| GPU | `onnxruntime.get_available_providers()` → `['AzureExecutionProvider', 'CPUExecutionProvider']` — confirmado: **sem NVIDIA, só CPU** |
| Já instalado | `onnxruntime 1.27.0`, `numpy 2.4.6`, `soundfile`, `torch`, `edge_tts` |
| Falta | só o pacote `supertonic` e os pesos do modelo |
| Projeto no PC2 | `C:\hipercool-videos` (não existe `D:\tools` lá — a bancada de teste é só do PC1) |
| Cache HuggingFace | `C:\hf_cache`, hoje `99.175.425 bytes` (~95 MB) em 4 arquivos |

## 2. Quanto custa em disco e memória

Medido na cópia que o PC1 **já baixou** em `C:\Users\Haylla\.cache\supertonic3` (385 MB na pasta):

| Arquivo | Tamanho |
|---|---|
| `onnx/vector_estimator.onnx` | 244,7 MB |
| `onnx/vocoder.onnx` | 96,7 MB |
| `onnx/text_encoder.onnx` | 34,7 MB |
| `onnx/duration_predictor.onnx` | 3,5 MB |
| **soma dos pesos** | **379,6 MB** |
| pacote `supertonic 1.3.1` (código) | 328 KB |
| `onnxruntime` + `numpy` | 41 MB + 34 MB — **já estão no PC2**, não baixa de novo |

- **Download: ~390 MB. Ocupa 1,9% dos 20,6 GiB livres.** Folga de sobra.
- **RAM (estimativa):** os 4 grafos somam 380 MB em disco; com as ativações, contar 1,0–1,5 GB de pico.
  Cabe nos 11,7 GiB com folga grande, mesmo com o Chrome aberto.

## 3. Quanto tempo de voz um capítulo precisa (medido)

**Duração média de uma fala** — 400 `.wav` sorteados de `D:\hipercool-materiais\tts_cache` (3.591 arquivos):

```
amostra 400   media 4.16 s/fala   formatos {(24000, 2, 1): 284, (44100, 2, 2): 116}
```

**Falas por capítulo** (`logs/fila_the-inheritor-cap*.log`): cap08 = 107, cap09 = 103, cap11 = 90,
cap10 = 79 → **média ~95 falas**.

> **95 falas × 4,16 s = 395 s = 6,6 min de voz por capítulo.**

## 4. Quanto o edge custa hoje (medido na produção, não no papel)

Cuidado com o jeito óbvio de ler o log: **no log as falas aparecem intercaladas com o render dos clips.**
No `fila_the-inheritor-cap09.log`, entre a primeira e a última linha `TTS[edge]` há **924 linhas, e só 103
são TTS** — as outras 821 são ffmpeg. Então o span bruto de 26,5 min **não é tempo de voz**.

Para isolar o edge, comparei a mediana do intervalo entre falas que vieram do **CACHE** (= só o render do
clip) e entre falas **NOVAS** (= render do clip + edge), no mesmo capítulo e na mesma contenção de CPU:

| Log | fala do CACHE (mediana) | fala NOVA (mediana) | **edge sozinho** |
|---|---|---|---|
| `fila_the-inheritor-cap10.log` (30 cache / 48 novas) | 7 s | 23 s | **16 s/fala** |
| `fila_the-inheritor-cap11.log` (61 cache / 28 novas) | 3 s | 13 s | **10 s/fala** |

> O edge entrega 4,16 s de áudio em 10–16 s → **0,26x a 0,42x do tempo real (mais LENTO que tempo real).**
> Um capítulo de ~100 falas novas: **1.000 a 1.600 s = 17 a 27 min só de voz.**
> Confere com o cap09: 101 falas novas, trecho inteiro de 26,5 min com o render junto.

(Isso corrige o "~5 s por fala" que está no `CLAUDE.md` — na produção real, com o render disputando a
máquina, são 10–16 s.)

## 5. A conta do Supertonic-3 no PC2

Ponto de partida medido no PC1 (i5-8365U, **com render rodando junto**): **1,3–1,5x tempo real**
(`D:\tools\testar_vozes.py` imprime `dur/gasto`, então 1,4x = gera 1,4 s de áudio por segundo de CPU).

- No PC1 o capítulo sairia em `395 s ÷ 1,4 = 282 s = 4,7 min`.
- **Escala para o PC2 (estimativa):** o PC2 tem metade dos núcleos e clock menor —
  `2 × 2,4 GHz` contra `4 × ~2,7 GHz` sustentados ≈ **0,44x do PC1**. Mas o número do PC1 foi tirado
  disputando CPU com o render, e o **PC2 está ocioso**, o que devolve boa parte. Faixa conservadora:
  **0,6x a 1,2x tempo real**.

> **PC2 ocioso: `395 s ÷ 1,2 = 5,5 min` (otimista) a `395 s ÷ 0,6 = 11 min` (pessimista) por capítulo.**

Essa é a única estimativa que sobra, e é por isso que a seção 7 manda **medir antes de ligar**.

## 6. Ranking dos motores locais

| Motor | Tempo real (PC1, com render) | Capítulo de 6,6 min no PC2 | Línguas | Veredito |
|---|---|---|---|---|
| **Supertonic-3** | **1,3–1,5x** | **5,5–11 min** (estimativa) | 31 línguas — **sem `th`** | **escolhido** |
| Kokoro | 0,3x | `395÷0,3 = 22 min` no PC1 → **50–80 min** no PC2 | pt, hi, it | descartado: mais lento que o edge |
| VieNeu | 0,5x | — | só `vi` | descartado: uma língua só |
| edge (motor de hoje) | 0,26–0,42x (medido na produção) | 17–27 min | todas, inclusive `th` | referência |

A lista de línguas saiu do próprio pacote (`supertonic 1.3.1`,
`D:\tools\tts-teste\Lib\site-packages\supertonic\config.py`, `SUPPORTED_LANGUAGES`) — são **31**:

```
en ko ja ar bg cs da de el es et fi fr hi hr hu id it lt lv nl pl pt ro ru sk sl sv tr uk vi
```

**Cobre 6 das 7 línguas do projeto** (pt, hi, id, it, ru, vi). **`th` (tailandês) não está na lista** —
o tailandês continua no edge/Gemini, sempre. O pacote tem ainda um código `"na"` ("unknown"), que embrulha
o texto em `<na>...</na>` e sintetiza assim mesmo; **não usar isso para o `th`** — é o modelo chutando a
pronúncia de uma língua que ele não viu no treino.

Os modelos que o item 11 mandou pesquisar: **OmniVoice e VoxCPM2 exigem GPU NVIDIA** — o PC2 confirmou
`['AzureExecutionProvider', 'CPUExecutionProvider']`, sem NVIDIA, então estão fora desta máquina. MOSS-TTS-Nano,
Qwen3-TTS e Chatterbox não foram medidos aqui e só entram na conversa se o Supertonic reprovar na medição da
seção 7 — pelo número que já existe, não há motivo para gastar tempo com eles agora.

---

## 7. Instalação no PC2 — comandos exatos (NÃO rodados ainda)

Rodar com a produção parada ou fora do horário de render. Tudo em `ssh pc2`.

### 7.1 Criar o venv da voz (separado do Python do sistema)

```bat
ssh pc2
cd C:\
python -m venv C:\tts-local
C:\tts-local\Scripts\python.exe -m pip install --upgrade pip
```

### 7.2 Instalar o pacote

Mesma versão que foi medida no PC1, para o número valer:

```bat
C:\tts-local\Scripts\python.exe -m pip install supertonic==1.3.1 soundfile numpy
```

(`onnxruntime` entra como dependência do `supertonic`; é o build de CPU — **não** instalar
`onnxruntime-gpu`, o PC2 não tem NVIDIA.)

### 7.3 Baixar os pesos (~390 MB)

Os pesos caem sozinhos em `%USERPROFILE%\.cache\supertonic3` na primeira execução. Para não baixar na
hora do uso, puxar antes:

```bat
C:\tts-local\Scripts\python.exe -c "from supertonic import TTS; TTS(model='supertonic-3', intra_op_num_threads=2)"
dir %USERPROFILE%\.cache\supertonic3\onnx
```

Esperado: os 4 `.onnx` da tabela da seção 2, somando ~380 MB.

> Alternativa sem baixar de novo: copiar do PC1, que já tem.
> `scp -r C:/Users/Haylla/.cache/supertonic3 pc2:C:/Users/<usuario>/.cache/`

### 7.4 Medir (este passo é obrigatório antes de ligar)

`intra_op_num_threads=2` — **2**, não 4: o PC2 tem 2 núcleos físicos, e 4 threads só disputam entre si.

```bat
C:\tts-local\Scripts\python.exe -c "import time; from supertonic import TTS; t=TTS(model='supertonic-3', intra_op_num_threads=2); txt='Joo Inhyuk achava que a vida dele era comum... ate o dia em que recebeu uma heranca inesperada do pai.'; t0=time.time(); w,_=t.synthesize(txt, voice_style=t.get_voice_style('M1'), lang='pt'); g=time.time()-t0; d=len(w)/44100; print('audio %.1fs em %.1fs = %.2fx tempo real' % (d, g, d/g))"
```

**Critério de aprovação:** `>= 0,6x tempo real`. Nesse patamar o capítulo sai em 11 min ou menos, ou seja,
ainda ganha do edge (17–27 min). Abaixo de 0,6x, a reserva não compensa e o assunto morre aqui — anote o
número neste arquivo e feche o item.

Repetir trocando `lang=` por `hi`, `id`, `it`, `ru`, `vi` e ouvir, para saber quais línguas prestam.
**Não testar `th`: o modelo não tem.**

---

## 8. Como ligar como RESERVA depois (ainda NÃO fazer)

A regra do dono não mudou: **local é só reserva, e o personagem não troca de voz no meio do
capítulo/série.** Então a chave é por CAPÍTULO, nunca por fala.

Onde encostar, sem reescrever nada:

1. `bin/elenco.py` linha 66 — `MOTORES = ("edge", "misto", "gemini")`. A função `motor()` devolve
   `"gemini"` para qualquer valor fora dessa tupla, então um motor `"local"` precisa entrar ali **e**
   ganhar um ramo dentro de `elenco.falar()`.
2. `bin/hiper-pipeline.py` linha 397 — é o **único** ponto de entrada da voz em português:
   `elenco.falar(obra_elenco, text_to_narrate, wav_path, persona, tts_gender, force_tts)`.
   As outras línguas passam pela linha 395, `idiomas.falar(...)`.
3. **Chave por capítulo, não por fala:** decidir o motor uma vez, no começo do capítulo (Gemini → edge →
   local), e segurar essa decisão até o fim. Se cair no meio, o capítulo inteiro vai para o degrau
   seguinte e refaz — nunca metade numa voz e metade noutra.
4. **Mapa de vozes:** o Supertonic usa `voice_style` (`M1`, `F1`, …), não os nomes do edge. O de-para
   tem que ficar gravado em `config/elenco/<obra>.json`, ao lado dos nomes edge e dos nomes Gemini
   antigos, para o personagem manter a voz quando a reserva entrar.
5. **`th` nunca cai no local** — o Supertonic não fala tailandês; para `th` a cadeia termina no edge.
6. Mexeu em `bin/`? Copiar para o PC2, como manda o `CLAUDE.md`:
   `scp bin/<arquivo> pc2:C:/hipercool-videos/bin/`
7. Ponto de entrada novo que rode escondido tem que importar `bin/sem_janela.py`, senão abre janela de
   console na tela da tarefa agendada.

## 9. O que ficou sem medir

- A velocidade real **no PC2** (seção 7.4) — é a estimativa da seção 5 e o único número que falta.
- A **qualidade** das vozes Supertonic em pt comparada à edge Thalita/Andrew: o dono tem que ouvir.
  Gerar as amostras e pôr em `Área de trabalho\Hipercool\AMOSTRAS DE VOZ`, como foi feito com o elenco edge.
