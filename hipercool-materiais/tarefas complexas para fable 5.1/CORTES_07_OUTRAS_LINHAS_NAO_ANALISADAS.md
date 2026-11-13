# CORTES — 07 — Onde esta sessão NÃO olhou (varredura do Fable vale mais aqui)

> **Projeto: linha CORTES** — Shorts de canais parceiros (recapd, `D:\recapd-ambientes\producao\bin`; estado em
> `D:\video-fila\linhas\CORTES`). Escrito pela sessão da linha CORTES em 28/10/2026.

Esta sessão só trabalhou na linha CORTES. Abaixo, o que está escrito como pendente nas outras — não conferido.

## LONGOS (`D:\video-fila\linhas\LONGOS\ESTADO.md`, recap longo, Kaggle/VPS)
- Pendente escrito lá: "atacar as 4 propostas (gancho fora do rosto, plano parado, balão em inglês, karaokê)";
  conferir render curto no PC1 -> pacote -> 1º longo real no Kaggle; falta a dona dizer os canais para postar.
- Mascote viva do longo (memória `project_mascote_viva.md`): Veo já baixou vídeo de OUTRO robô uma vez
  (`D:\hipercool-materiais\mascote_waifu_v2\_errados_veo\`) — falta trava automática de "é ela mesma?".

## PRODUTOS (`D:\video-fila\linhas\PRODUTOS\ESTADO.md`, vídeos de produto/clientes)
- Escrito lá como FALTA: CTA no meio; voz clonada (hoje Edge Thalita/Francisca); curva de locutor; APRENDIDO
  reescrito a cada vídeo e medida de movimento por cena; produção fora do PC1 (caiu por "Cannot allocate memory");
  instalação no PC2 (C:\produto-pc2, ffmpeg, node_modules do Remotion).
- Leitura de views do Instagram parada por risco de conta.

## hipercool (`D:\hipercool-videos`, o projeto com "mais potencial" segundo a dona)
- Ler `CLAUDE.md` e `docs\correcoes_pendentes.md` de lá. Melhorias entre projetos:
  `D:\hipercool-videos\docs\MELHORIAS_PARA_TODOS_OS_PROJETOS.md`.

## manhwa-react (o que tem "mais views" segundo a dona) e Veo
- Objetivo da dona: cruzar o melhor de cada projeto. Pergunta para o Fable: o que o manhwa-react faz que o faz ter
  mais views e ainda não foi copiado para os Cortes/hipercool? (Esta sessão só copiou o divider.py.)
- Veo: `D:\veo`, placar de temas em `D:\postador-de-videos\_analise\placar_veo_temas.json`.

## Fable — resultado
**29/10 (Fable).** O que foi olhado de cada linha está nos próprios arquivos desta pasta (LONGOS_02/07/09/10/11/12,
PRODUTOS item 1, ER_01–06, CORTES_01–08) e em `FABLE_DECISOES.md` (D1–D10).
- **manhwa-react "tem mais views":** pelo ledger (ER_06) são 24 vídeos com mediana 5 e **um** de 10.789 (inventoreact,
  20/10, "Ninguém reparou no detalhe da pizza que a IA criou") e um de 1.219. Ou seja, a reputação vem de 1 vídeo —
  não é um método que o manhwa-react tem e os Cortes não. O que ele tem de diferente e que o dado do ER_01 apoia:
  vídeo gerado (Veo) é conteúdo ORIGINAL, não reaproveitado — e é o reaproveitado que não entra no lote do feed
  (manhwa/dorama de parceiro, hipercool, idiomas). Primeira coisa a copiar não é efeito: é testar nos canais mortos
  1 Short/dia com imagem original (Veo/Flow) por cima da mesma história, e ver se o feed dá o lote (continuaram < 90%
  com ≥ 50 views). O `divider.py` (choque) já foi copiado (T6) e ainda não provou nada.
- **Veo:** `placar_veo_temas.json` segue a mesma régua de "views brutas"; vale aplicar D1 (excluir não elegíveis,
  usar % assistido) antes de confiar no Thompson de temas.
- **hipercool:** ER_03 — 0 de 40 passou de 10 views; o feed não mostra nenhum (18 de 19 com continuaram 100% e < 10
  views). Teste proposto lá (2 Shorts sem censura/mosaico no manhwanoturno) antes de qualquer melhoria de vídeo.
- **PRODUTOS:** ciclo de medição fechado (D9), 10 Reels com 0–2 views — alcance zero, mesmo diagnóstico.
- **Mascote viva "é ela mesma?":** o produto já usa YuNet+SFace para conferir rosto (memória `project_veo_foto_funil`:
  "rosto revisado (YuNet+SFace)"); é a mesma trava a chamar no download do Veo da mascote — comparar o embedding
  SFace do 1º quadro com a foto-base e recusar < 0,6. Não implementei (é da linha LONGOS e o fluxo da mascote está
  em mudança).
