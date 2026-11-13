# Trabalho em andamento

19/10 ~15:05 — demora na resposta. Causa achada: a fila de webhook do Hermes (`webhook_queue.go`) só entregava a cada
30 s (o "oi" entrou na fila 14:44:26.988 e chegou ao FluxIA ~14:44:56). Correção = Hermes v0.15.1 (entrega na hora
por sessão, fila no banco continua de garantia), commit `9c12a07` no pc-base, testada com Postgres descartável na 209
(apagado) e conferido que o teste falha no código antigo. Compilada na produção como `20261019-1452_9c12a07`,
**NÃO ativada**: esperando o OK do dono (ativar = pausar a campanha 8843 só na troca, avisar o claude-01, conferir
linhas/0fcd550f/pré-filtro/enabled, religar com o mesmo next_slot_at, enviar tag).
Fluxo 3 da papelaria segue em botões em blocos de 3 (funcionando, só lento por causa da fila).
