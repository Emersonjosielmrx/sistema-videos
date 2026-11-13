# ANÁLISE — fluxo n8n "4-cria videos grandes compilados" vs nosso landscape-compiler

> Doc de CONTEXTO (não é tarefa). Fonte: `D:\downloads\fabrica de animes-4-cria videos grandes compilados.json`.
> É **1 nó `code` com 4183 linhas de JS** (134 KB), "junta videos Will_Protect". Extraído 2026-06-30.
> Tarefas derivadas: `TAREFA_10..13_*.md`. A TAREFA 10 é a IDEIA PRINCIPAL DA USUÁRIA.

## O QUE ESSE FLUXO FAZ
Pega os vídeos de capítulo JÁ prontos (`video_pag_N_sem_trilha.mp4`) e os COMPILA num vídeo
grande (ex: páginas 1-50), com trilha, capítulos de YouTube e CTAs. O foco do código NÃO é
efeito visual — é **robustez operacional** pra merge de muitos arquivos sem corromper.

## NÓS JÁ TEMOS: `bin/landscape-compiler.py` (435 linhas)
Compilação CRESCENTE em paisagem 1920×1080 (v1=cap1, v2=cap1+2, ...). Hoje ele:
- Concatena os vídeos VERTICAIS já prontos (concat demuxer).
- Põe o vídeo vertical no CENTRO e preenche as laterais com **blur fixo do próprio vídeo**
  + vinheta (filter_complex hardcoded, linha ~226-240). Trilha + upscale + validação + checkpoint.

## ⭐ IDEIA DA USUÁRIA (vira TAREFA 10 — a mais importante)
> "usar os painéis pra fazer só que em modo paisagem, pq aí ele vai ter novos efeitos que vai
>  poder usar, ou até colocar 2 painéis um do lado do outro"

Hoje o landscape parte do VÍDEO vertical pronto → laterais borradas é o único efeito possível.
A ideia é partir dos **PAINÉIS originais** (as imagens) na versão paisagem. Isso destrava:
1. **Os ~59 filtros visuais 16:9 do fluxo 3** (`ANALISE_fluxo3_efeitos.md`): eles são feitos
   EXATAMENTE pra imagem retrato dentro de quadro 16:9 (split bg/fg + blur + overlay). No vertical
   não serviam; na PAISAGEM servem perfeitamente. Vira o banco de fundos/atmosfera real.
2. **2 painéis lado a lado**: 16:9 tem largura sobrando. Dá pra mostrar painel[i] e painel[i+1]
   lado a lado (ou painel + zoom de detalhe), preenchendo o quadro com CONTEÚDO em vez de blur.
3. Efeitos de movimento, color grading e legenda do fluxo 3 também passam a caber.

## O QUE VALE A PENA DO FLUXO 4 (robustez) — tarefas menores
| Classe/bloco | Linha | O que faz | Vira |
|---|---|---|---|
| Merge HIERÁRQUICO | 3328/3437 | junta em árvore (grupos de 30→merge→merge) em vez de 1 concat gigante; com retry que REDUZ o batch a cada falha (30→15→...→5) | TAREFA 11 |
| CheckpointManager | 1316 | resume por NÍVEL (já temos checkpoint simples; o deles é por nível da árvore) | TAREFA 11 |
| DiskMonitor + CRF adaptativo | 825/236 | se disco enche, sobe o CRF (comprime mais) pra não falhar | TAREFA 12 |
| QuarentenaManager | 1379 | isola vídeo que falhou 2× pra não travar a fila inteira | TAREFA 12 |
| GapDetector | 1562 | detecta páginas faltando na sequência antes de compilar | TAREFA 12 |
| CTAGenerator + FRASES_ENGAJAMENTO | 2719/471 | intercala cards curtos de "deixa o like/inscreve" com anti-repetição e pesos | TAREFA 13 |
| capitulos (YouTube chapters) | 180 | gera arquivo de timestamps "Páginas 1-50" pra descrição do YT | TAREFA 13 |

## NÃO PORTAR
- Caminhos `/tmp/youtubevideos`, `/root/...`, multi-idioma (PT/EN/ES/FR) — ambiente do n8n dele.
- `crf: 40` do merge intermediário (é proposital: qualidade baixa nos níveis e upscale no fim;
  nós já temos nossa política de CRF — não copiar cegamente).
- O sistema todo de webhook/dashboard/SystemMonitor (é telemetria do n8n dele).

## DEPENDÊNCIA ENTRE TAREFAS
- TAREFA 10 (painel→paisagem) é grande e independente; é o coração.
- TAREFAS 11/12/13 melhoram o compilador SEM depender da 10 — podem ser feitas antes/depois.
