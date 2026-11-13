# Prompt para o próximo agente — continuar as melhorias dos Shorts (30/10/2026)

## PROMPT

Você vai continuar as melhorias dos Shorts do projeto `D:\recapd-ambientes\producao`. Pedido da dona: "analise
profundamente e faça todas as melhorias possíveis, principalmente nos vídeos curtos que saem; não me pergunte nada".

Leia primeiro:
1. `D:\recapd-ambientes\producao\docs\MELHORIAS_SHORTS_2026-10-30.md`: o que já foi feito, provas, backups e
   pendências. Os dois agentes de hoje acrescentam no fim as seções "Variantes (A/B/C/D)" e "Virais nos canais fracos".
2. `D:\tmp\analise_shorts_20261030\`: análises completas.
   - `pendencias.md`
   - `videos.md`
   - `views.md`
   - `falhas.md`
   - `bugs.md`
3. `D:\hipercool-materiais\tarefas complexas para fable 5.1\FABLE_DECISOES.md`: decisões D1, D3, D6 e D43.
4. `D:\video-fila\linhas\CORTES\DECISOES.md`: mais nova em cima.

Já feito em 30/10 (cada mudança tem comentário `30/10` no código):
- Short não sai mais quebrado. Antes saía:
  - sem legenda;
  - com frases faltando;
  - com a @ do parceiro;
  - com o fim repetido.
- Corrigidos também:
  - gancho que caía sobre a legenda;
  - delogo gigante (teto 12%);
  - instrução da IA que era narrada;
  - saudação de enchimento no começo;
  - mascote fora da área segura.
- Duração: teto de 10 frases no braço A e roteiro respeitando o máximo de frases.
- Falhas de produção:
  - `source.f*` parcial não vira fonte;
  - Whisper acha o modelo em qualquer pasta;
  - stderr inteiro do Whisper no log.
- Views:
  - piso de 100 mil views na fonte;
  - 15–21 h vão pro fim da fila nos canais pt;
  - títulos sem a fórmula "NINGUÉM ESPERAVA";
  - testes A/B fora das alavancas do melhorador.
- Fontes dos parceiros SEMPRE do mais visto pro menos visto (`anime_discover.discover_canal`, inclusive o cache).
- Kaggle (outro IP) ligado no PC1 (`anime_fetch.download_video` e o laço do `anime_auto.main`) quando o IP de casa
  está barrado ou a espera passaria de 5 min. Tarefa agendada `KaggleBaixador` (a cada 20 min, `kaggle_baixar.py manter`)
  criada.
- Postagem manual rodada às 14:33. Agendou Forja, Cartucho e Dicas Financeiras hoje, mais thai e viet.

O que falta, em ordem:
1. **Conferir o resultado dos 2 agentes de hoje e validar o trabalho deles** (o relato de outro agente é alegação:
   abra os arquivos, rode `py_compile`, confira as datas e os backups `.bak_20261030_variantes` / `.bak_20261030_virais`):
   - **Variantes A/B/C/D:**
     - helper de N braços (provável `bin\variantes.py`);
     - variantes da saudação, do "NINGUÉM ESPERAVA" e do horário;
     - placar `D:\video-fila\linhas\CORTES\placar_cortes_testes.json` com a régua D1.
   - **Virais nos canais fracos:**
     - números de produção × postagem;
     - versão nova de um viral para os canais fracos;
     - cortes só de tipo ou parceiro sem views.
2. **Teste de render de um Short com o código novo:**
   - pasta `D:\tmp\teste_render_20261030\` (`rodar.sh`, `render.log`, saída `final_anime_short.mp4` ou similar);
   - às 15:08 tinha só 1 de 5 clipes (máquina ocupada pela produção);
   - quando sair, validar:
     - ffprobe: 720x1280, duração de vídeo e de áudio iguais;
     - LUFS ~-14;
     - frames em 0,3 s, 1,5 s, 3 s, meio e fim (legenda, gancho, nada repetido no fim);
   - os tempos do roteiro forçam o caso do fim repetido: os cortes devem sair sem plano repetido.
3. **Conferir nos logs `D:\hipercool-materiais\anime\_parceiro_<data>.log` os primeiros Shorts da produção real
   depois das mudanças:**
   - procurar "Short incompleto não sai", "legenda falhou de novo", "cobertura falhou", "baixando pelo KAGGLE",
     "piso de", "saudação tirada", "roteiro com tempo cortado";
   - conferir que nada novo quebrou, olhando também `workspace\pipeline_metrics.jsonl` (taxa de FALHA dos Shorts e
     duração final).
4. **Pendências que ainda não foram feitas** (detalhes em `MELHORIAS_SHORTS_2026-10-30.md` e `bugs.md`):
   - selo ou logo em IMAGEM do canal original escapa da detecção (VORIN, Maresia, KAIJINRE);
   - `anime_health_monitor` diz "Tudo OK" porque não lê os `_parceiro_*.log` nem o `pipeline_metrics.jsonl`;
   - B1/B2: com cobertura "tarja" a nossa legenda cai em cima da tarja (dormente enquanto for "delogo");
   - fonte horizontal dentro do 9:16 do parceiro (faixas pretas, caso c5a42e): recortar o miolo;
   - tela final do canal de origem no fim do nosso Short ("SE INSCREVE");
   - tags na língua errada ou de nicho errado no `postar.json` (GTA com tags de anime, tag em indonésio no pt);
   - legenda do YouTube morta desde 22/10 (disjuntor com 80 falhas): todo Short cai no Whisper do PC1;
   - falta de RAM no PC1 derruba o clone de voz: não rodar Whisper, clone e render ao mesmo tempo.
5. **Qualquer mudança SUBJETIVA nova vira VARIANTE** (A/B/C/D), registrada no `postar.json`, e quem decide é o
   placar. Correção de defeito objetivo não vira variante.
6. Atualizar `MELHORIAS_SHORTS_2026-10-30.md`, uma linha em `D:\video-fila\linhas\CORTES\DECISOES.md` e uma linha em
   Novidades de `D:\hipercool-videos\docs\MELHORIAS_PARA_TODOS_OS_PROJETOS.md` se servir a outro projeto.

Python: `D:\recapd-ambientes\producao\venv\Scripts\python.exe` (render/pipeline) e `D:\veo\venv\Scripts\python.exe`
(postagem, Kaggle). Sempre com `PYTHONUTF8=1`.

## RESTRIÇÕES (o que não fazer)

```
- NÃO perguntar nada à dona: ela pediu "não me pergunte nada". Decida pelo dado e documente.
- NÃO matar processos de produção (recapd/hipercool, pythonw, ffmpeg da produção) nem de outras sessões do Claude:
  há várias no PC; confira o processo pai antes de mexer em qualquer coisa pendurada.
- NÃO postar público direto: todo upload sai AGENDADO (proteção de direitos autorais) e só pelo NAVEGADOR (postar
  por API é proibido). Postagem só pelo fluxo existente (parceiro_diario.py postar), respeitando cotas, limite
  diário do YouTube e o intervalo de 45 min por canal.
- NÃO apagar canal, caches (audio_cache, narration_cache, tts_cache), celulares\ ou arquivos de outros projetos.
  Cortes só reversíveis no config, com backup e motivo anotado.
- NÃO decidir teste A/B por nota do júri (D6); só por views dos ELEGÍVEIS (D1/D3). NÃO mudar T8/T9 sem ler D3/D16.
- NÃO desfazer mudanças de outros agentes; arquivo "mudou no disco" = estado atual. Se parecer errado, anote.
- Antes de editar: backup .bak_<data>_<motivo> no mesmo lugar; depois: py_compile. Edições pequenas, com
  comentário "dd/mm (motivo)" no estilo do código.
- Nada no disco C (nem temporário): use D:\tmp\... . Medir antes de baixar algo grande; D: anda com ~7-10 GB livres.
- RAM baixa (~2 GB livres): um ffmpeg de análise por vez, leve. Se travar por memória, ver o Wise Memory
  Optimizer e fechar só Chrome de teste/cofre e processos órfãos (nunca produção).
- NÃO editar bin\_SNAPSHOT_* nem as cópias velhas em D:\postador-de-videos\bin.
- NÃO dizer "pronto" sem provar (ffprobe + frames + log). Relato de outro agente é alegação até conferir.
- Commit/push: não (o projeto não está em git; e push só com OK da dona).
```
