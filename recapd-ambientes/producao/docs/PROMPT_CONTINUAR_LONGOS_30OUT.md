# Prompt pra continuar (sessão de 30/10, longos + postagem + painel)

Continue o trabalho nos vídeos LONGOS do recap (D:\recapd-ambientes\producao). Leia antes: CLAUDE.md do projeto,
docs\MELHORIAS_LONGO_ANDAMENTO.md (seção "30/10 tarde"), D:\video-fila\linhas\LONGOS\LICOES.md e o topo do
D:\video-fila\linhas\MURAL.md.

## URGENTE (estava no meio quando parei)
1. (ATUALIZAÇÃO: depois de uns minutos o painel respondeu — ranking 30 dias com 907 vídeos, 123 "fora do postador".
   Só confirmar que segue no ar após a 2ª reinicialização.) PAINEL :8790 FORA. Reiniciei a tarefa PainelVideos (pythonw D:\video-fila\painel_controlador.py) pra pegar o código
   novo; o processo sobe, o socket fica "Bound" em 127.0.0.1:8790 mas nunca "Listen" (CPU quase zero). Rodando no
   console (`python painel_controlador.py --port 8799`) sobe normal. Descobrir por que pela tarefa trava, pôr de volta e
   conferir `curl http://127.0.0.1:8790/api/ranking?dias=30` (deve dar ~906 vídeos, ~123 "fora do postador"). O telão,
   o melhorador_longo e outros dependem dele.
2. Rodada de postagem em andamento (comecei 14:44 com `postar_longos.py --primeiro u7tN75GsgZw`): o ForjaReact estava
   preparando o u7tN. Conferir em colab\postar_longos.log se subiu; mandar o link pra dona. A rodada das 14:40 da tarefa
   RecapPostarLongos e a minha anterior foram interrompidas no meio — o CCJQvNP-23Y pode ter deixado rascunho no Studio
   do Fio da Meada (conferir).

## Já feito hoje (não refazer)
- politica.postar_youtube: canal já em "limite diário" não chama o poster nem re-marca +24 h (o defeito prendia 14 canais
  pra sempre). Limites soltos às 14:05 (backup config\limite_diario.json.bkp_*_remarcacao).
- Regra "vídeo decolando": rampa_canais.segurar_viral + politica.segurando_viral (no checar_upload e na rodada dos
  longos). Testado: Animescomia e HistoriasEmFrames seguravam. Ajustar VIRAL_X/VIRAL_MIN/VIRAL_MAX_H se precisar.
- D:\video-fila\videos_canais.py: todos os vídeos dos 30 canais (lista de uploads do YouTube, cache 1 h em
  estado\videos_canais.json). Telão (vitrine_painel.mais_vistos, até 30 itens) e painel (api_ranking) usam ele.
- postar_longos: ForjaReact primeiro na lista; teto 6 cortes/canal/dia; vid[:11]; chama longo_para_conferir no fim.
- colab\longo_para_conferir.py: mantém 1 longo recente não postado em D:\hipercool-materiais\LONGO_PARA_CONFERIR
  (agora o u7tN); troca quando ele é postado.
- Mascote escolhe gravação pelo ponto do vídeo; pausa no fim não congela; fila_dona copia capítulos e move o pronto no
  Drive; tipo manhwa pela descrição/tags (sem espelho). Pacote --codigo enviado ao Kaggle às ~13:40.

## Pendente / ideias
- Rampa: os canais "liberados" sobem 1 degrau/dia (rampa_canais --status); conferir que voltou a subir sem o defeito.
- Painel de canais (painel\historico.jsonl) não tem dados de vários canais (Noturnos, Dorama...): a regra viral não age
  neles. Ligar a coleta desses canais.
- Disco D: com ~3 GB livres.

## 30/10 18:30 (chat da mascote/rondas) — URGENTE resolvido
- Painel :8790 no ar (200; /api/ranking?dias=30 = 926 vídeos).
- Postados à tarde: u7tN no ForjaReact https://youtu.be/9TclD-ENfSo (15:53), CCJQ no Fio da Meada
  https://youtu.be/G7o6IgysNIk (16:45), 2jtdp (Sand) no CenaReact https://youtu.be/JnYuAbj0Kwk (17:45); P-dj sendo
  preparado pro inovare manhwa br. Rascunho do CCJQ da rodada interrompida das 13:59 no Studio do Fio da Meada: não conferido.
- Mascote: nome = MARIA (fala "maria1" na mascote_producao); 20 fantasias novas; reações primeiro em cada roupa.
- 19:10: VgQU — render PRONTO 13:57 UTC, mas o envio do final (~1 GB) pro Drive falhou 1x e derrubou o kernel (sem
  pronto.json; marcas soltas = vai renderizar de novo sozinho). kaggle_trabalhador: envio do final com 5 tentativas
  (espera crescente), copiado pras 4 centrais (backup .bak_30out_envio).
- KaggleBaixador: já existia, mas rodava no PC1 com a conta 649 (saída hermes-prod) = MISTURA. Desligada; agora cron
  /etc/cron.d/kaggle-baixador na hermes-prod (baixador_manter.sh, 20 min); kaggle_baixar._kg recusa no Windows.
