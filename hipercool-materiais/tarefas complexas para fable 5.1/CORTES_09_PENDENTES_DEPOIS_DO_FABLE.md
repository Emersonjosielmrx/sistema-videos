# CORTES — 09 — O que apareceu depois da 1ª passada do Fable (29/10)

> **SUBSTITUÍDO por `CORTES_10_NOVO_29-10_PENDENTES.md`** (mesmo conteúdo com números atualizados). Responda lá.

> **Projeto: linha CORTES** — Shorts de canais parceiros (recapd, `D:\recapd-ambientes\producao\bin`; estado em
> `D:\video-fila\linhas\CORTES`). Escrito pela sessão da linha CORTES em 29/10/2026, depois de ler FABLE_DECISOES.md.

## 1. Testes T5, T6 e T7 abertos em 28/10 batem de frente com a regra D3 (prioridade alta)
- Fato: no mesmo dia em que o T8 (Short curto) foi aberto, estavam rodando juntos T4 (expectativa no meio),
  T5 (gancho no Remotion), T6 (choque/fogo), T7 (mascote) — todos "ab" em `bin\cortes_ajustes.json`, sorteio
  independente por md5 em `anime_auto.fazer_short`. A D3 diz "não abrir T9 antes do T8 fechar: cruzar fatores de
  tela/duração com n pequeno mata os dois".
- Interação concreta: o T8 corta o Short para 4-5 frases (~20-27 s). Com isso o T7 quase não acha pausa
  (`cortes_mascote.momentos`: depois de 3,5 s, 10 s entre aparições, 2 s antes do fim) e o T6 tem no máximo 1-2
  impactos/trocas. Os braços B de T6/T7 ficam diferentes nos Shorts curtos e nos longos.
- **Atualização 29/10 07:15:** o próprio Fable abriu o T9 (`fala_rapida` "ab", `fala_delta` 15) depois da D3 — agora
  são T4, T5, T6, T7, T8 e T9 sorteados juntos e independentes em cada Short. Com ~40-80 Shorts/dia e só parte deles
  elegível (D1), quantos dias até cada teste ter >= 6 elegíveis por braço por canal? Vale a pena?
- Pergunta: fixar T4-T7 em A (ou em B) até o T8 fechar, ou estratificar a análise por `curto`? Só a pessoa que
  desenhou a régua D1 deve decidir. Os registros já existem: postar.json (`gancho_meio`, `gancho_remotion`,
  `fx_choque`, `mascote`, `curto`) e `D:\postador-de-videos\_analise\placar_cortes_testes.json`.

## 2. Nicho decidido pela FONTE, não pelo assunto do vídeo (views: público errado)
- Fato (29/10): Short da Larissa Manoela (FLwt7xPmfmY, "Larissa Manoela's rules", pasta
  `animes recap\shorts\larissa-manoela_cap1_20261028`) foi destinado ao **Bicho Noturno** (nicho animais), porque a fonte
  `papodebixo` está cadastrada com `nichos: ["animais","curiosidades"]` em `producao\config\parceiro.json`.
- Onde: escolha do canal/nicho em `bin\parceiro_diario.py` (`_escolher_fonte`, `_nicho_do_canal`, ~303-360) e a
  vitória por `nicho_canal` em `D:\postador-de-videos\bin\notificar_telegram.py` ~1102.
- Para o Fable: medir quantos Shorts dos canais de nicho (Bicho, Esporte, Game, Curiosidades, Dorama, Filme Noturno)
  estão fora do assunto do canal; se for relevante, classificar o assunto POR VÍDEO (título + roteiro, Argon/Gemini,
  barato) antes de escolher o canal. Canal de nicho que recebe vídeo fora do nicho pode ser o motivo de canais que não
  ganham lote (D5).

## 3. Disco do PC1 quase parou a produção (29/10 ~00:30: D: com 1,3 GB livre)
- Causas achadas e já corrigidas por esta sessão:
  (a) Short de parceiro postado ficava 3 dias no PC (`D:\postador-de-videos\config\etapas.json`, parceiro
  `sai_apos_dias` 3 -> 0.01; 241 vídeos/4,7 GB presos); (b) reprovados nunca saíam (`backup_drive.parceiro_reprovados`);
  (c) com internet lenta a rodada do backup passava de 1 h e a tarefa horária empilhava 2-3 rodadas subindo os
  mesmos arquivos (trava `logs\backup_drive.lock` em `D:\manhwa-react\scripts\backup_drive.py`).
- O que não está resolvido (para o Fable): não há orçamento de disco nem alarme ANTES de encher. Pesos medidos 29/10
  (sem contar junções): hipercool-materiais 91 GB (videos 18,2 parado, models 17,5, animes recap 8,1, assets 7,4, veo
  5,8, python 4,4, _longos_postar 3,1), logins-google 26 GB (perfis do Chrome: nunca apagar, regra da dona), caches
  8,6, claude-code-video 4,5 (+1,5/dia). Produção dos Cortes ~2 GB/dia. Perguntas: o que de 18 GB em
  `hipercool-materiais\videos` e 3 GB em `_longos_postar` ainda precisa estar no PC? Produção deve desacelerar sozinha
  perto do limite (regra existente: disco cheio já quebrou lote em 12/10 e fez fonte sair em 2 canais em 20/10)?

## 3b. "Cannot allocate memory" com RAM sobrando: limite de COMMIT, não de RAM (29/10 madrugada)
- Fato (29/10 ~07:10): RAM física livre 8,5 de 15,8 GB, mas memória reservável (commit) livre só 2,0 GB de 31,8.
  O `D:\pagefile.sys` é gerenciado pelo Windows (16 GB alocados, pico 12 GB) e fica no D:, que chegou a 1,3 GB livre
  na madrugada -> o arquivo de paginação não tinha como crescer. Efeitos no log `D:\hipercool-materiais\anime\
  _parceiro_20261029.log`: ffmpeg "Cannot allocate memory" (04:1x e ~05:20), cobertura do parceiro com BrokenPipe,
  `[short] subprocesso falhou (rc=1073807364)` às 04:32; o rclone do backup caindo com dump de Go (05:20). Só 5 Shorts
  de 00h às 07h (normal de madrugada: 4-7 por HORA).
- Quem reserva memória (commit privado, 07:10): `produto.diario` (PRODUTOS) 4,9 GB e `gerar.py --auto`
  (CLAUDE-CODE-VIDEO) 3,5 GB, os dois rodando desde 04:40; ~30 processos `claude` (chats abertos) 7,6 GB; VS Code 3,3.
- Para o Fable: (a) o disco do D: e o commit são o MESMO problema (pagefile no D:) — qual é o piso de espaço livre
  que a produção precisa respeitar e quem garante? (b) por que `produto.diario` passa de 4 GB e roda 2,5 h? (vazamento
  ou carga normal?) (c) `maquinas.py`/`ocioso.py` medem "RAM livre" (física) para liberar render — deviam medir commit
  livre? Esta sessão NÃO mexeu em nada disso (outras linhas e configuração do Windows).

## 4. O melhorador central conhece os testes dos Cortes?
- O `D:\video-fila\melhorador_central.py` (D12) foi feito depois do placar `cortes_testes` e das alavancas `mascote`,
  `fx_choque`, `gancho_remotion`, `curto` em `bin\cortes_melhorador.json`. Conferir se o brief da linha CORTES lê
  esse placar com o filtro de elegíveis da D1 — esta sessão não conferiu.

## Fable — resultado
(preencher)
