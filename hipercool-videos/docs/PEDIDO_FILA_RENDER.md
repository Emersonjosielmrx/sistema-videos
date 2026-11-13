# Pedido: hipercool entrar na fila de render entre projetos (claude-05, 17/10/2026 07:15)

**FEITO 17/10 ~08:20 (sessão do hipercool):** `hiper-pipeline.py` (`_vez_na_fila`, rótulo "<pasta> <idioma>") e
`hiper-longo.py` entram em `fila_render.vez("hipercool", ...)` no `__main__` — cobre fila.py, refazer_caps e
corrigir_pendentes, que chamam o pipeline como processo. Vale do próximo render em diante (os que estavam rodando
carregaram o código antigo). Vigia: tarefa `HipercoolVigia` criada (20 em 20 min) e o regex do STATUS agora aceita
markdown/"CONCLUÍDO".

Dono: "fazer uma filinha pros projetos não se atrapalharem entre si". Em 17/10 às 7h o PC estava com 1,1 GB de RAM
livre: hipercool, anime longo, postagem e Shorts do parceiro renderizando juntos.

- Fila: `D:\video-fila\fila_render.py` + `fila.json` (1 render pesado por vez; prioridade hipercool=1, parceiro=2,
  anime=3, historias=4; vez de processo morto/esquecido é liberada sozinha; se a fila falhar, o render segue).
- Já ligada: recapd (`anime-pipeline.py`) e historias (`story_pipeline.py`). **Falta o hipercool**, onde começa o
  hiper-pipeline (fila.py / refazer_caps):
  ```python
  sys.path.insert(0, r"D:\video-fila"); import fila_render
  with fila_render.vez("hipercool", f"{obra} cap{n} {lang}"):
      ...  # o render
  ```
  `python D:\video-fila\fila_render.py` mostra quem está renderizando e quem espera.
- Achados no `bin/vigia_agente.py` (não mexi): não há tarefa agendada `HipercoolVigia` (só rodou à mão 17/10 00:26);
  o regex do STATUS não pega `STATUS:` em negrito/markdown → aquela rodada virou "sem STATUS" mesmo tendo devolvido.
- Fora do hipercool há o `D:\video-fila\vigia_geral.py` (tarefa `VigiaVideos`, 20 em 20 min): recap de anime,
  parceiro, historias e a fila. Ele NÃO mexe em D:\hipercool-videos.
