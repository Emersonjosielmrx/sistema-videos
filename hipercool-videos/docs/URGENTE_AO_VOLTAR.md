# URGENTE: fazer assim que o hipercool voltar a produzir

Deixado em 28/10/2026. O hipercool está parado; isto é a primeira coisa a ver quando religar.
Análise completa: `D:\hipercool-materiais\novas_tecnologias_analise.md`.

## 1. Legenda agrupada por sentido (do Hypit)
Hoje a legenda corta em N palavras fixas. O Hypit (`D:\caches\hypit\skills\hypit\references\playbooks\craft\captions.md`)
agrupa por sentido: nunca separar artigo+substantivo, negação+verbo, nome próprio, número+unidade,
preposição+objeto; frase de impacto ganha cartão próprio. Aplicar no gerador de legenda do hipercool.

## 2. Corte na troca de cena (do Hypit)
`D:\caches\hypit\packages\media-local\src\files.ts` função `visualBoundaries` (linha ~470): ffmpeg reduz cada
quadro a 32x32, mede a diferença média com o anterior e marca troca quando passa de 0,1 (12 amostras/s).
São ~20 linhas, fáceis de portar para Python. Serve para o corte de Short/compilado cair na troca de painel/cena.

## 3. Método de engenharia reversa de vídeo (do Hypit)
`D:\caches\hypit\skills\hypit\references\creation\reference-video.md`: ler um vídeo que estourou (ex.: compilado
do Porão) e anotar ANALYSIS.md (por que funciona) + TIMELINE.md (o que entra/sai em cada segundo). Usar para
copiar a estrutura dos compilados que dão mais views.

## 4. Voz nova: narrador_chris
Narrador de Todo Mundo Odeia o Chris (RVC v2) em `D:\hipercool-materiais\models\rvc\vozes\narrador_chris\`.
`voz_clonada.py converter narrador_chris <narracao.wav> <saida.wav>`. Ainda não ouvida pela dona.

## Não serve pro hipercool
GSAP, PixiJS e Three.js (são JavaScript de navegador; o hipercool é Python + ffmpeg).
