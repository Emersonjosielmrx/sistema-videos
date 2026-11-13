# 09 — Capacidade de render (quantos vídeos saem por dia)
> **PROJETO: LONGOS** — recap longo de anime/manhwa do recapd (`D:\recapd-ambientes\producao`, linha `D:\video-fila\linhas\LONGOS`). Escrito pela sessão Opus da linha LONGOS em 28/10/2026.

**Fatos:** Kaggle com 0 de 4 GPUs com cota (semanal); 19 contas sem telefone verificado. Longo de 75 min ≈ 4,4 h só
CPU; os efeitos aprovados em 28/10 somam ~+35% (tabela medida em `D:\video-fila\linhas\LONGOS\EFEITOS_LISTA_DONA.md`,
benchmark `bench\bench_efeitos.py`). AV1 na montagem custa +46% de CPU (agora baixa H.264). PC1: memória reservada
quase toda (29,5 de 31,8 GB em 28/10; `produto.diario` 4,8 GB e `gerar.py --auto` 4,5 GB) → rembg/whisper falham por
falta de memória.

**Onde olhar:** `D:\recapd-ambientes\producao\colab\vps_central.py`, `kaggle_trabalhador.py`, `cliente.py`
(fila), `bin\fx_clips.py` (`build_clip_from_video`: 1 ffmpeg por frase, libx264 ultrafast), `bin\anime-pipeline.py`
(concat, legenda, master em passadas separadas = recodificações), memória "Kanban das máquinas", "Ociosidade nos 3 PCs".

**Ideias:** NVENC no Kaggle; juntar passadas (mascote + legenda + master) numa só; cache de trechos; render
distribuído por capítulo entre máquinas; achar o vazamento de memória dos processos do PC1.

**Como medir:** horas de render por minuto de vídeo; longos prontos por dia.

## Fable — resultado
**29/10 (Fable) — não medi render; o que fiz que toca aqui:** `D:\video-fila\baixa_prioridade.py` (D8) tira os
testes/análises da frente da produção no PC1; o `qa_video` (D10) custa 7 s por Short e ~2–4 min por longo de 75 min
(320 px) — cabe. Das ideias listadas, a única com ganho certo e sem GPU é **juntar passadas** (mascote + legenda +
master num `filter_complex` só: cada recodificação a mais de um longo de 75 min é ~1 h de CPU); NVENC no Kaggle não
existe sem cota de GPU. A memória do PC1 (29,5 de 31,8 GB) é o gargalo que derruba rembg/whisper: `produto.diario`
4,8 GB parado e `gerar.py --auto` 4,5 GB são de outras linhas — ponto único para a dona decidir o que roda no PC1.
