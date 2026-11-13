# Robustez do recap longo — plano e estado (retomável)

Pedido do dono (25/10 ~07:30): "baseado em todos os problemas que tivemos, faça o máximo de melhorias pra ter o mínimo
de problemas e ser viável usar". Sistema: producao/COLAB_RECAP_LONGO.md. Marcar [x] ao terminar cada frente.

ATENÇÃO: outra sessão editou cliente.py / trabalhador.py / kaggle_trabalhador.py em 25/10 07:18–07:26 (pegada dupla,
original quebrado, pasta órfã). Editar sempre por cima da versão atual (Edit), nunca reescrever o arquivo inteiro.

## Problemas vistos (causa → frente)
1. Google Drive 403 "Quota exceeded ... defaultPerMinutePerProject" = cota GLOBAL da chave pública do rclone (todo
   mundo que usa rclone). Derrubou o preparo da Colab (25/10 03:40) e provavelmente travou o Kaggle. Chave própria
   está PROIBIDA pelo dono (memória feedback_google_sem_api). → F1, F2
2. Kaggle e VPS pegaram o mesmo pedido (corrigido pela outra sessão: marca própria + desempate). → conferir em F3
3. Original quebrado (download interrompido) → 2 h de render jogadas fora (corrigido: ffprobe no preparar). → ok
4. Trabalhador que morre no meio deixa o pedido preso; só o mesmo nome solta ao voltar. → F3
5. Sem sinal de vida durante o render (só entre vídeos): alimentador conta trabalhador vivo errado. → F3
6. Ninguém religa nada fora da sessão do Claude (crons morrem com a sessão; Monitor dura 30 min). → F4
7. Alimentador faz tudo numa linha só: preparo (15–45 min) segura o recolhimento. → F5
8. Falha apaga o original do Drive → nova tentativa baixa de novo do YouTube (bloqueio). Log completo some. → F6
9. Nenhuma conferência do vídeo pronto antes de publicar (duração/áudio/silêncio). → F7
10. Atualizar código = subir à mão em 3 VPS + Kaggle + reabrir Colab. → F8
11. YouTube "not a bot"/429 (ytdlp_vez já integrado). Compilados > 2h30 (153) esperando decisão do dono (cortar).

## Frentes
- [ ] F1 rclone resistente: toda chamada com nova tentativa e espera crescente (cota/5xx/rede), nunca derruba o loop.
- [ ] F2 Menos chamadas ao Drive: 1 `lsjson -R` por rodada (fila + datas), sinal de vida pela data do arquivo,
      cache do pedido.json, intervalos maiores com variação.
- [ ] F3 Sinal de vida durante o render (thread renova a marca a cada ~10 min); marca parada > 45 min = pedido solto
      pra outro pegar; nome único por sessão do Kaggle.
- [ ] F4 Vigia fora do Claude (tarefa agendada do Windows, a cada 15 min): alimentador e token_loop vivos, Kaggle
      `manter`, Colab sem sinal → reabrir, VPS (docker) parada → religar, disco da 157; aviso só pelo portão
      D:\video-fila\avisos.py e só o que o dono precisa ver.
- [ ] F5 Alimentador em 2 linhas (recolher separado do preparar).
- [ ] F6 Falha: guarda log e erro em colab\erros\, mantém o original no Drive por vídeo e reenvia sem baixar de novo
      (até 2 tentativas), depois avisa.
- [ ] F7 Conferência do vídeo pronto antes de publicar (ffprobe: duração mínima, tem áudio, não está mudo).
- [ ] F8 Trabalhador se atualiza sozinho (versão no Drive; troca quando está parado).
- [ ] F9 Colab: preparo com nova tentativa longa (não morre no 403); trabalhador não morre por exceção.
- [ ] F10 Revisão independente + teste com fila local (rclone aceita pasta local) antes de pôr no ar.

## Estado / log
- 25/10 08:20: plano escrito. Colab parada desde 03:40 (403 no preparo). Kaggle sem sinal há 2 h. VPS ok. Fila vazia
  (alimentador rebaixando o vMyOmvaaFIk). 4 prontos no Drive (yKfgs7, 3h0M55, bXe7, 76SYvC).
