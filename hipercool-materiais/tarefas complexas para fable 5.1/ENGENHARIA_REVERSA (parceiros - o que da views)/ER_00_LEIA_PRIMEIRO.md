# ENGENHARIA REVERSA — o que faz um Short pegar views — leia primeiro
> **29/10 — decisões do Fable (D1–D6):** `..\FABLE_DECISOES.md`. Resumo: 60% dos Shorts nem entram no lote do feed;
> a régua é elegibilidade + % assistido; T8 (Short curto) aberto; Studio em lote com impressões/CTR. Ler antes de mudar.

> **Projeto: engenharia reversa dos parceiros** (vale para TODOS os projetos de vídeo: Cortes/recapd, hipercool,
> manhwa-react, historias-em-frames, Claude Code Video, postador). Escrito pela sessão de engenharia reversa
> (Opus 5.5) em 29/10/2026. Código e dados desta sessão: `D:\video-fila\engenharia_reversa\`.

A dona quer saber o que os vídeos com muitas views fazem de diferente e transformar isso em regra/código. Esta
sessão vai rodando as análises e passa para cá o que é complexo demais para ela. Aqui só tem fato conferido com
número; suposição está marcada "SUPOSIÇÃO". Cada arquivo aponta o lugar exato para o Fable não varrer às cegas.

## Ordem (maior retorno em views primeiro)
1. `ER_01_SHORT_TUDO_OU_NADA.md` — os nossos Shorts dão ~1.200 ou 0–10, quase nada no meio. Por quê?
2. `ER_02_METRICAS_STUDIO_VAZIAS.md` — sem impressões/"deslizou" não dá para provar nada; 593 de 595 vazios.
3. `ER_03_HIPERCOOL_ZERO.md` — 40 Shorts/longos do hipercool medidos, nenhum passou de 8 views.
4. `ER_04_IDIOMAS_MORTOS.md` — canais it/id/ru/th/hi em mediana 0: gastam produção sem retorno.
5. `ER_05_ACHADOS_SEM_VIEWS.md` — o aprendizado gera 564 sugestões que ninguém liga a views.
6. `ER_06_POR_PROJETO.md` — números e pendências de cada projeto num lugar só.

## Como rodar os números (todos leves, sem yt-dlp, sem IA)
- `python D:\video-fila\diagnostico_alcance.py` — Shorts de parceiro por canal/nicho/parceiro/narrador/idioma.
- `python D:\video-fila\engenharia_reversa\alcance_projetos.py` — todos os projetos, faixas, hora, reuso;
  grava `alcance_projetos.json` ao lado.
- `python D:\video-fila\engenharia_reversa\_reuso.py` — reuso da mesma fonte (conferido só em pt).
- Fontes dos dados: `D:\postador-de-videos\config\telegram_estado.json` (medidas_48h),
  `D:\postador-de-videos\_analise\metricas_studio.json`, `D:\postador-de-videos\logs\uploads_ledger.jsonl`,
  e o `postar.json` ao lado de cada vídeo (caminho no ledger).

## Erros já descobertos nesta análise (não repetir)
- 28/10 eu disse "fonte repetida mata o vídeo" (mediana 1 contra 8). FALSO: 25 das 29 fontes repetidas foram
  traduzidas para it/id/ru/th/hi, que dão zero de qualquer jeito. Só em pt: fonte única 29% passa de 500,
  repetida 32%. Sempre separar por idioma/canal antes de concluir.
- O ledger antigo não tem `projeto` em 128 uploads (aparecem como None/None): são de 18–19/10, misturam
  hipercool e parceiro. Não usar esses como grupo.

## Regras da casa que NÃO podem quebrar
- Pipelines: só Argon com reserva Gemini 3.8 — nunca Opus/Kiro/Fable dentro da produção.
- yt-dlp só pela vez única `D:\hipercool-materiais\comum\ytdlp_vez.py` (o YouTube barra o IP da casa; 2 bloqueios
  em 28/10). Preferir o que o Cortes já baixou (`D:\recapd-ambientes\producao\workspace\anime\<id>_<título>\source.mp4`);
  `--flat-playlist` pesa bem menos que baixar.
- Nenhuma janela na tela da dona (`import sem_janela` + CREATE_NO_WINDOW). Nada no disco C.
- Parceiros já autorizaram: copiar a ESTRUTURA, nunca marca nem texto.
- Sempre agendado (publishAt). Nenhum canal 1 dia sem postar. Mudança visível = teste A/B medido.
- MURAL.md e MELHORIAS_PARA_TODOS_OS_PROJETOS.md: só Edit, nunca Write.

## Como devolver
Para cada tarefa: o que achou (com prova: log, número, quadro), o que mudou, como mediu. Escreva no próprio arquivo
(seção "Fable — resultado") e anote em `D:\video-fila\linhas\MURAL.md`. Se virar regra, marcar no aprendizado:
`python D:\video-fila\aprendizado.py marcar <ids> aplicado --motivo "..."`.
