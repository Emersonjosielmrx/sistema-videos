# CORTES — 01 — O sistema quase não sabe o que rende (prioridade máxima)

> **Projeto: linha CORTES** — Shorts de canais parceiros (recapd, `D:\recapd-ambientes\producao\bin`; estado em
> `D:\video-fila\linhas\CORTES`). Escrito pela sessão da linha CORTES em 28/10/2026.

## O que existe
- 7 testes A/B rodando nos Cortes (`D:\video-fila\linhas\CORTES\TESTES.md`, T1-T7). O sorteio é md5(id) 50/50 fixo
  em `D:\recapd-ambientes\producao\bin\anime_auto.py` (procure `gancho_meio`, `gancho_remotion`, `fx_choque`,
  `mascote` ~linhas 638-675). A versão usada vai para o `postar.json` (`anime_publish.py` ~linha 450) — para T5/T6/T7
  via `_testes_usados.json` na pasta do vídeo.
- Medição: `D:\postador-de-videos\bin\notificar_telegram.py` ~1079: "vitória" = views do vídeo contra a MEDIANA do
  canal (precisa de >= 4 vídeos no canal), binária (empate 0,5). Alimenta placares `D:\postador-de-videos\_analise\
  placar_*.json` (fontes, nicho_canal, capas, narradores, voz_base, testes_voz, palavras, tags).
- Em 28/10 esta sessão acrescentou o placar `placar_cortes_testes.json` (mesmo arquivo, logo depois de
  `testes_voz`): antes disso NENHUM código cruzava os testes dos Cortes com as views. Só conta vídeos medidos daqui
  em diante.
- Quem usa placar para decidir: só `bin\anime_testes.sortear` (Thompson sobre `testes_voz`) e o seo_generator
  (palavras/tags). Os testes dos Cortes continuam 50/50 para sempre — ninguém promove o vencedor.
- O melhorador (`bin\cortes_melhorador.py`) está DESLIGADO/sombra e decide por NOTA DO JÚRI, não por views.

## O dado está furado (medido em 28/10 22h, `metricas_studio.json`)
- 591 vídeos: 65 com `erro` (TargetClosedError do navegador que lê o Studio), 198 com views 0, **retenção (ret30) em
  só 21**, **CTR em 0**, `continuaram`/`intencionais` quase sempre null.
- Para Shorts, o que o YouTube usa é "continuaram assistindo" x "deslizaram" e duração média — justamente o que não
  está sendo lido. Hoje tudo é decidido por views brutas contra a mediana do canal.

## O que esta sessão não consegue resolver bem (para o Fable)
1. **Leitura do Studio confiável** (retenção, continuaram/deslizaram, duração média por Short). Onde: quem gera o
   metricas_studio.json (procure "metricas_studio" em `D:\postador-de-videos\bin`). Regra: Google só pelo navegador,
   sem API nova (tokens OAuth de leitura dos 7 canais morrem ~29/10).
2. **Desenho estatístico**: 7 testes simultâneos e independentes (fatorial) + confusão por canal, horário, fonte,
   nicho, idade do vídeo. A "vitória contra a mediana" binária desperdiça informação. Qual a métrica certa, quantos
   vídeos por versão, como tratar interação (ex.: mascote x choque/fogo no mesmo Short)?
3. **Fechar o ciclo**: transformar `placar_cortes_testes.json` em decisão automática (promover/pausar versão, como
   o `anime_testes.sortear` faz com Thompson), com proteção contra decidir com amostra pequena.
4. **Achar o que nem está sendo testado**: cruzar metricas_studio x postar.json (todos os campos: fonte, nicho,
   duração, narrador, horário, título, capa) e dizer quais fatores explicam mais views. `aprendizado_global.json`
   tem top/piores por origem/canal — nunca foi analisado a fundo por esta sessão.

## Fable — resultado
**29/10 03:15 (Fable 5.1).** Antes de tudo, o achado que muda o desenho (detalhe e números em
`ENGENHARIA_REVERSA\ER_01_SHORT_TUDO_OU_NADA.md`, script `D:\video-fila\engenharia_reversa\continuaram_x_views.py`):
- 60% dos nossos Shorts (0–9 views) **nunca entram no lote de teste do feed** ("continuaram" = 100% com 2–5 views).
  Nenhum teste de formato (T1–T7) muda isso: eles não são vistos. Qualquer placar que misture esses vídeos mede ruído.
- Quem entra no lote para em 1.000–1.500 views; o que leva ao 2º lote é **% assistido ≥ 65%** (vídeos de 13–24 s),
  não "continuaram" (deslizou), que é igual (54–57%) nos dois grupos.

1. **Leitura do Studio** — feita no lote (`youtube_studio_extras.retencao_lista` + `metricas_rede.coletar_lote`):
   a tabela do modo avançado agora traz, por vídeo e numa página por canal, views do período, continuaram, duração
   média, % assistido, **impressões de miniatura, CTR e visualizações intencionais** (antes só o metricas() de 1 em 1
   lia, 3 por hora, e caía). "Mostrados no feed" o YouTube devolve "—" por vídeo nessa tabela (fica o campo
   `feed_impressoes` para quando mostrar). Espera de 90 s + 1 recarga (às 00:50 o Studio demorava e o lote saía sem
   retenção) e rolagem tolerante. Bug visto de passagem: `views` do metricas() por vídeo está 10× (13.000 × 1.285)
   em pelo menos 7 vídeos — use `ret_lista.views_periodo`/medidas_48h, não `views`.
2. **Desenho estatístico** (o que fazer com 8 testes 50/50 ao mesmo tempo):
   - Unidade = vídeo; **excluir os não elegíveis** (`ret_lista.views_periodo < 20`): eles não receberam o lote e
     entram como "A perdeu/B perdeu" por acaso. Só isso já tira ~60% do ruído.
   - Métrica primária contínua, não a vitória binária: `log(views_periodo / mediana do canal nas 4 semanas)` (a
     mediana por canal controla canal/nicho/idade; o log tira o peso dos 6.674). Secundária: `pct_media` (é a porta
     do 2º lote) e `continuaram`. Guardar as três por vídeo no placar, não só "ganhou".
   - Testes independentes sorteados por md5 separado são um fatorial balanceado: o efeito de cada um sai da média
     marginal (B − A) sem precisar cruzar; interação (mascote × choque) só com 4× a amostra — não olhar antes de
     n ≥ 30 por braço. Com a variância que temos (desvio do log ≈ 1,2), detectar +40% de views pede ~25 vídeos
     elegíveis por braço por canal-tipo; com pct_media (desvio ≈ 18 pts, efeito esperado +15 pts) bastam ~10.
     **Ou seja: decida por pct_media primeiro, views depois.**
   - Hora: separar por canal (cada canal posta em hora fixa). Já medido em ER_01: 19–21 h é a pior faixa em 6 de 6.
3. **Fechar o ciclo** — regra para o `anime_testes.sortear`/melhorador aplicar ao `placar_cortes_testes.json`:
   Thompson por chave do teste sobre o sucesso binário "elegível E (pct_media ≥ 65 OU views_periodo ≥ 1.500)", prior
   Beta(2,2); promover (fixar B ou A no `cortes_ajustes.json`) só com n ≥ 12 elegíveis por braço e P(B > A) ≥ 0,95
   em 1.000 sorteios; pausar o teste (voltar a "ab" com 20% B) se P(B < A) ≥ 0,95; registrar no `historico` do
   ajustes com os números. Nunca promover por nota de júri (CORTES_05: ainda sem prova).
4. **O que explica mais views** (metricas_studio × postar.json, 279 Shorts): 1º elegibilidade (canal/upload: manhwa,
   dorama e línguas it/id/ru/th/hi quase nunca entram; fatos/esportes/filme entram); 2º, entre os elegíveis, %
   assistido (+0,33) ≈ continuaram (+0,34) > duração (−0,04 em views, mas −0,43 em pct_media: curto assiste-se
   inteiro) > título (sem sinal, 35 mil Shorts de parceiros) > narrador (n pequeno). `aprendizado_global.json`
   não foi usado: mistura não elegíveis. **Aberto o T8 (Short curto 4–5 frases) com base nisso** — ver TESTES.md.
