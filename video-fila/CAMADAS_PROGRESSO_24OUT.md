# Progresso das correções dos 31 achados (24/10) — TERMINADO ~11:10
Backups: *.bak_20261024_achados (video-fila, config, testes, D:\monitor_opus.py)

## Feitos (todos)
- Guarda (painel_ia.py + config\melhoria_guarda.json via testes\_ajuste_guarda_24out.py):
  - 11: shell dentro de shell (powershell -Command, bash -c, cmd /c, iex, Start-Process) é aberto e conferido; -EncodedCommand barrado
  - 12: heredoc gravado em arquivo (não VIGIA_DIARIO) é conferido; Write de script NOVO/temp passa pelo 'bloquear'
  - 14: regra de env ampliada; _cmd_curto mascara sk-/Bearer/x-api-key/30+ caracteres
  - 15: .jsonl do painel em segredos; grep -r/rg/findstr /s/Select-String -Recurse e Grep sem glob seguro numa raiz com secrets/cookies = barrado (Glob liberado: só lista nomes)
  - 17: Edit/Write no NÚCLEO e .claude\settings barrado; config ilegível = exit 2
  - 18: pergunta/propor também com bloquear_aplicar; robocopy /MOVE|/MIR|/PURGE e git rm/mv/checkout/restore/stash barrados
  - 19: POST nas APIs do painel :8790 barrado
  - 21: lookaheads ancorados (\A); timeout 90 s no hook
  - 22: hook_backup não copia o que a guarda barra
- Motor (melhoria_continua.py): 6 (0 aprovações → crítico C → dúvida pra dona; revisores sem veredito → dúvida), 7 (reserva não zera a espera), 9 (quem no desfazer), 10 (prompt 700 caracteres + [PERGUNTA] antes do CHECK; painel corta o meio), 13 (grava depois do ciclo), 16 (_sem_segredo nos comandos), 25 (DIFF antes das lições), 28 (parou no meio com comandos → aviso + P0)
- Auditoria (auditoria_final.py): 1 (enviado=False), 2 (REFAZER sempre no topo do backlog), 3 (teto do refazer), 4 (reserva também sem pendente + aviso de P0 nao_auditado), 5 (confiança tolerante + except vai pra dona com aviso), 7 (reserva só ligada), 8 (parse de log:), 16 (_limpo no dossiê/doc/trechos; PRECISO_VER só manifesto/backup/logs), 23 (ver não-lista; lote zerado antes; try por veredito), 24 (cota por item), 26 (último modelo, leitura reversa), 29 (append no VIGIA/leitura não vira P0), 30 (quem por parâmetro), 31 (sem manifesto → dona)
- bots_conversa.py: 1 (reabre o aviso da auditoria uma vez por motivo, registro em est["auditoria_enviada"]); 9 (quem="dona (Telegram)")
- camada_opus.py: 20 (botão vale sem stream; lock marca sem_stream; mensagem certa)
- D:\monitor_opus.py: 27 (os.replace com 20 tentativas)

## De fora
- 17: "VIGIA_DIARIO único alvo" nos permitir
- 12: Edit de código existente não é conferido (tem shutil/os.replace legítimo)
- 2: parte opcional (mover o e['refazer'] ocupado pro backlog)

## Efeito a observar
- Buscas recursivas nas raízes de hipercool-videos/postador/veo/recapd sem --include=*.py agora são barradas (o agente recebe a dica). Se atrapalhar demais, afrouxar em _grep_recursivo_em_segredo.
