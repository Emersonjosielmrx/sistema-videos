# CORTES — Tarefas complexas para o Fable 5.1 — leia primeiro

> **Projeto: linha CORTES** — Shorts de canais parceiros (recapd, `D:\recapd-ambientes\producao\bin`; estado em
> `D:\video-fila\linhas\CORTES`). Escrito pela sessão da linha CORTES em 28/10/2026.

Escrito em 28/10/2026 pela sessão Claude (Opus) que cuida da linha CORTES (Shorts de parceiros). A dona quer que o
Fable 5.1 olhe onde esta sessão já chegou no limite — ou não está enxergando — e ache melhorias que tragam mais
**views, likes e qualidade**. Os tokens do Fable são caros: cada arquivo aponta o LUGAR exato (caminho, linha,
dado) para ele não gastar varrendo às cegas. Aqui só tem fato conferido; o que é suposição está escrito "SUPOSIÇÃO".

## Ordem (maior retorno em views primeiro)
1. `CORTES_01_CICLO_VIEWS_DECISAO.md` — os testes A/B existem, mas o sistema quase não sabe o que rende (dado furado).
2. `CORTES_02_FORMATO_E_RETENCAO_DO_SHORT.md` — duração, gancho, ritmo e final contra o que estoura nos parceiros.
3. `CORTES_05_JURI_X_VIEWS.md` — o júri automático nunca foi conferido contra as views reais.
4. `CORTES_03_VOZ.md` — a voz é o que a dona mais reclama; a configuração é frágil.
5. `CORTES_06_RECURSOS_NOVOS.md` — Remotion, mascote, choque/fogo: o que vale a pena ampliar.
6. `CORTES_04_ARQUITETURA_FRAGIL.md` — acoplamentos escondidos que hoje causaram 3 defeitos.
7. `CORTES_07_OUTRAS_LINHAS_NAO_ANALISADAS.md` — LONGOS, PRODUTOS, hipercool, Veo: onde esta sessão não olhou.
8. `CORTES_08_MAQUINAS_E_DESEMPENHO.md` — disputa de CPU entre produção e testes.

## Outras linhas
O índice de todos os projetos é o `LONGOS_00_LEIA_PRIMEIRO.md` desta pasta (seção "Arquivos por linha"). Ligações
com os daqui: CORTES_01 complementa `LONGOS_01_retencao_real_youtube.md` e `LONGOS_04_melhorador_ab_estatistica.md`;
CORTES_05 e CORTES_03 complementam `CLAUDE-CODE-VIDEO_onde_parei_e_o_que_nao_vejo.md`; CORTES_08 complementa
`LONGOS_09_capacidade_render.md`; CORTES_06 (mascote nos Shorts) conversa com `LONGOS_06_mascote_viva.md`.

## Mapa rápido
- Produção dos Cortes: `D:\recapd-ambientes\producao\bin\` (anime_auto.py orquestra -> anime-pipeline.py ->
  anime_publish.py, cada um em processo separado). Ajustes vivos: `bin\cortes_ajustes.json`.
- Estado e memória da linha: `D:\video-fila\linhas\CORTES\` (ESTADO.md, DECISOES.md, TESTES.md, LICOES.md,
  APRENDIDO.md, REFERENCIA_NERDCF.md). As outras linhas: `D:\video-fila\linhas\{LONGOS,PRODUTOS,CLAUDE-CODE-VIDEO}`.
- Métricas reais: `D:\postador-de-videos\_analise\` (metricas_studio.json, placar_*.json, aprendizado_global.json);
  quem mede e alimenta os placares: `D:\postador-de-videos\bin\notificar_telegram.py` (~linhas 1060-1135).
- Máquinas: PC1 (este), PC2 (`ssh pc2`, C:\recapd-e-animes; é do hipercool: nunca matar pythonw lá), notebooks.
- Painel: http://localhost:8790. Liga/desliga: `D:\video-fila\controle.json`.

## Regras da casa que NÃO podem quebrar (decididas pela dona)
- Pipelines usam só Argon (prazo curto) com reserva Gemini 3.8 — nunca Opus/Kiro/Fable dentro da produção.
- Voz Edge PURA proibida; sempre clone por cima. Antonio proibida. Francisca sozinha é considerada ruim.
- Nunca postar público direto: sempre agendado (publishAt). Nenhum canal fica 1 dia sem postar.
- yt-dlp sem rajada (bloqueia o IP da casa). Login Google/Instagram: regras próprias na memória — não improvisar.
- Tarja branca sobre a legenda da fonte: PROIBIDA (delogo). Censura só na parte, nunca tela inteira.
- Toda mudança visível ao público entra como teste A/B (TESTES.md) e é medida.
- Memória completa da dona: `C:\Users\Haylla\.claude-vscode\projects\d--\memory\MEMORY.md`.

## Como devolver
Para cada tarefa: o que achou (com prova: log, número, quadro), o que mudou, como mediu. Escreva no próprio arquivo
da tarefa (seção "Fable — resultado") e nas DECISOES.md da linha afetada.
