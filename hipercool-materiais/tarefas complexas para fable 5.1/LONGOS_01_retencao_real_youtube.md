# 01 — Retenção real do YouTube → o que cada trecho/efeito faz com a audiência
> **PROJETO: LONGOS** — recap longo de anime/manhwa do recapd (`D:\recapd-ambientes\producao`, linha `D:\video-fila\linhas\LONGOS`). Escrito pela sessão Opus da linha LONGOS em 28/10/2026.

**Objetivo:** ligar a curva de retenção (segundo a segundo) e as fontes de tráfego de cada vídeo publicado aos eventos
da linha do tempo dele (gancho, resumo, cortes de cena, efeitos, CTA da mascote, troca de narrador, capítulos, memes),
e daí tirar regras que melhoram os próximos vídeos.

**Por que importa:** hoje o melhorador decide com views totais e notas de um júri de IA. A curva mostra *onde* o
público sai — é a informação que mais converte em views (retenção alta = o YouTube recomenda mais).

**Onde olhar**
- Views/ranking: painel `D:\video-fila\painel_controlador.py` (`/api/ranking`, `/api/desempenho`, `/api/canais_views`).
- Melhorador do longo: `D:\recapd-ambientes\producao\colab\melhorador_longo.py` + `.json` (função `desempenho`).
- Júri de IA do longo: `colab\juri_longo.py`; Cortes: `D:\video-fila\linhas\CORTES\juri\`.
- Linha do tempo de cada longo: o pipeline sabe os tempos de cada frase (`fx_clips._CLIP_ABS_STARTS`), capítulos
  (`capitulos.json`), CTAs da mascote (`ANIME_MASCOTE_FALAS`), resumo (`ANIME_RESUMO_N`). Hoje NADA disso é salvo
  num arquivo de linha do tempo por vídeo — primeiro passo provável.
- Regra: Google só pelo navegador (sem API do Cloud). Studio → Análise → Retenção fica no navegador logado (cofre:
  `D:\logins-google\cofre.py`, perfis em `config\youtube_navegador.json`).

**O que já se sabe:** referência do Porão Manhwa (`D:\video-fila\linhas\LONGOS\referencias\1TXD66c_ofg\ANALISE.md`):
abertura com ~50 cortes no 1º minuto, reengajamento a cada 15–20 min. Não sabemos como os NOSSOS longos retêm.

**Onde parei / limite:** não construí leitura da retenção do Studio nem o cruzamento com a linha do tempo; exige
scraping robusto do Studio pelo navegador e um modelo de "queda de retenção × evento" que eu não validei.

**Como medir:** retenção média e % aos 30 s / 1 min / 10 min dos longos antes × depois das regras aprendidas.

## Fable — resultado
**29/10 03:35 — a curva segundo a segundo agora é lida (FABLE_DECISOES.md D11).** O modo avançado do Studio não dá
curva por tempo (testei `ELAPSED_VIDEO_TIME_RATIO`: sem tabela), mas a aba Engajamento de cada vídeo — que o
`metricas()` já abre na 1ª leitura de 48 h — desenha a curva "Retenção de público" como SVG com eixos "0% … 120%" e
"0:00 … dur". `youtube_studio_extras._curva_retencao(pg)` pega o `path` mais longo, converte pelos ticks e devolve
50 pontos (fração do vídeo → % assistindo); `metricas()` grava `curva`, `dur_video`, `ret30`, `ret60`, `ret10min`,
`ret_meio`, `ret_fim`. Teste real (TY0C2PNEaXs, 33 s, 1.418 views): começa em 117,6% (gente repetindo), 30% do vídeo
→ 64%, metade → 48%, fim → 18%. Custo: zero páginas a mais.
- O que fazer com isso (quem cuida da linha): gravar por vídeo a linha do tempo (frase → segundo; `roteiro_tempos`,
  capítulos, CTAs da mascote, resumo) num `linha_tempo.json` ao lado do `render.json` — hoje não é salvo — e cruzar
  com `curva`: queda > 10 pontos em < 5% do vídeo = evento a investigar; subida (acima de 100% ou pico) = trecho que
  o público repete/pula para. O cruzamento é só arquivo (sem IA): o `melhorador_longo.analisar` pode fazer.
- Cuidado: curva só existe para vídeo que RECEBEU impressões (ER_01); nos não elegíveis a página diz "Retenção média
  indisponível" e a curva vem de 2–5 views (lixo). Filtrar por `views_periodo ≥ 50` antes de aprender regra.
