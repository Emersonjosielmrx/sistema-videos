# TAREFA 10 ⭐ — Compilado PAISAGEM a partir dos PAINÉIS (efeitos 16:9 + 2 painéis lado a lado)

STATUS: [~] PARCIAL 2026-06-30 — banco de fundos 16:9 FEITO (LS_FILTERS=1, landscape_filters.py); 2-painéis-lado-a-lado e re-render dos painéis (A) PENDENTES
PRIORIDADE: ALTA — é a ideia central da usuária pra versão compilada.

> Leia antes: `_LEIA_PRIMEIRO.md` + `ANALISE_fluxo4_compilado.md` + `ANALISE_fluxo3_efeitos.md`.
> Não mexer em censura. Não rodar 2 pipelines (checar processo antes de qualquer render).

## A IDEIA (palavras da usuária)
> "usar os painéis pra fazer só que em modo paisagem, pq aí ele vai ter novos efeitos que vai
>  poder usar, ou até colocar 2 painéis um do lado do outro"

Hoje `bin/landscape-compiler.py` pega o VÍDEO VERTICAL já pronto e só borra as laterais
(filtro fixo, linha ~226-240). Isso desperdiça o quadro 16:9. A versão nova parte dos
**PAINÉIS originais** (imagens), o que destrava:
1. **Os ~59 filtros visuais 16:9 do fluxo 3** (que NÃO cabiam no vertical) — eles são desenhados
   exatamente pra imagem retrato centralizada em quadro 16:9 com fundo desfocado. Na paisagem
   funcionam de verdade.
2. **Layout 2 painéis lado a lado** — preencher a largura com CONTEÚDO (painel[i] + painel[i+1],
   ou painel + recorte de detalhe) em vez de só blur.

## PASSO 0 — OBRIGATÓRIO: analisar os 2 JSON originais
1. Fluxo 3 (`fabrica de animes-3-cria video pequeno copy.json`, nó único `aplica efeitos`):
   o catálogo `VISUAL_FILTERS` (~linhas 234-379) tem os filtros 16:9 prontos. AGORA SIM dá pra
   reusar os filter-strings quase direto (são 1280×720 → adapte pra 1920×1080).
2. Fluxo 4 (`fabrica de animes-4-cria videos grandes compilados.json`, nó `junta videos`):
   leia o `CONFIG` (encoding/upscale/trilha) e como ele faz capítulos.
```python
import json
js3 = json.load(open(r"D:\downloads\fabrica de animes-3-cria video pequeno copy.json", encoding="utf-8"))["nodes"][0]["parameters"]["jsCode"]
print("\n".join(js3.split("\n")[233:379]))   # VISUAL_FILTERS (rode com PYTHONUTF8=1 → arquivo)
```
Também leia nosso `bin/landscape-compiler.py` inteiro (435 linhas) e `bin/effects_engine.py`
(funções de build de clip e de leitura de painéis).

## DECISÃO DE ARQUITETURA (definir e me reportar no doc antes de codar)
O compilado paisagem pode ser construído de 2 formas — escolha e justifique:
- **(A) RE-RENDER dos painéis em paisagem** (mais poder, mais custo): para cada painel, gerar
  um clip 1920×1080 com filtro 16:9 do fluxo 3 + movimento, reusando o MESMO áudio/narração já
  existente do capítulo (NÃO regerar TTS — regra do projeto: reusar etapas caras). Concatena tudo.
- **(B) PÓS sobre o vídeo vertical pronto** (mais barato, menos poder): manter o que o
  landscape-compiler já faz, mas trocar o "blur fixo" por: escolher um dos filtros 16:9 do
  catálogo por cena + opção de 2-up quando houver 2 painéis no mesmo trecho.
> Recomendação inicial: começar por (B) pro "2 painéis lado a lado" + banco de fundos 16:9
> (ganho rápido, baixo risco), e deixar (A) como evolução. Mas decida com base no código real.

## O QUE IMPLEMENTAR (modo incremental, atrás de flags)
1. **Banco de fundos 16:9**: portar VISUAL_FILTERS do fluxo 3 pra um catálogo no landscape-compiler,
   adaptando 1280×720→1920×1080. Trocar o filtro fixo atual por seleção (com anti-repetição;
   reusar a lógica de memória da TAREFA 4 se já existir). Flag `LS_FILTERS=1`.
2. **2 painéis lado a lado** (`LS_SIDE_BY_SIDE=1`): quando fizer sentido (ex: páginas de
   diálogo curto, ou para "antes/depois"), compor dois painéis verticais lado a lado dentro do
   1920×1080 (cada um ~860px de largura + faixa central). ffmpeg `hstack` ou overlay duplo.
   Heurística simples pra decidir quando usar 2-up (ex: a cada N, ou quando 2 painéis curtos
   seguidos) — começar conservador, sem forçar em cena de ação.
3. **Manter compatível**: sem as flags, o landscape-compiler se comporta IGUAL a hoje.

## CUIDADO
- **Áudio/sincronia**: o compilado tem que bater com a narração existente. Se for caminho (A),
  reusar os tempos reais (mesma lógica `_CLIP_ABS_STARTS` do effects_engine). NÃO regerar TTS.
- **9:16 vs 16:9**: aqui é o ÚNICO lugar onde os filtros 16:9 do fluxo 3 se aplicam. Não confundir
  com o pipeline vertical (que continua 9:16).
- **2-up + legenda**: a legenda do narrador precisa continuar legível; definir onde ela fica no
  layout 2-up (provavelmente faixa inferior central, não sobre os painéis).
- **Custo/tempo**: compilado é vídeo longo. Usar perfil de qualidade (TAREFA 9 se já feita) e
  background task pra ffmpeg (regra 11). Validar com ffprobe (duração/áudio/moov) — regra 5.
- **Junction de vídeos**: lembrar que `workspace/videos` é junction compartilhada (vale pras 3 cópias).

## VALIDAR (com cuidado — checar render antes)
1. Confirmar que NÃO há render rolando (PowerShell Get-CimInstance — ver _LEIA_PRIMEIRO).
2. Gerar um compilado CURTO de teste (ex: caps 1-2, TEST_MODE/perfil draft) com `LS_FILTERS=1`
   e depois com `LS_SIDE_BY_SIDE=1`. Comparar visualmente com o landscape atual.
3. ffprobe: duração do áudio não pode ficar >5s menor que o vídeo (regra de QC do projeto).

## RESULTADO (preencher)
- [ ] decisão de arquitetura (A) ou (B) + justificativa:
- [ ] banco de fundos 16:9 portado (LS_FILTERS)
- [ ] layout 2 painéis lado a lado (LS_SIDE_BY_SIDE)
- [ ] landscape sem flags == comportamento atual
- [ ] compilado de teste validado (ffprobe ok)
- Observações / amostras:
