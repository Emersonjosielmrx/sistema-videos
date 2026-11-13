# Modo Produção 10h — Anime Deitado (2026-07-27 → 2026-07-28)

> Documento de AUDITORIA pro agente da manhã. Explica cada cron ativo, o que
> monitora, o que corrige sozinho, e o estado esperado ao acordar.
> Iniciado ~22:12 UTC (19:12 local BR) de 2026-07-27. Janela: ~10h → termina ~08:00 UTC / 05:00 local.

---

## Contexto: o que aconteceu antes (resumo pro auditor)

Passamos o dia corrigindo o pipeline de recap **deitado** (1h+) que nunca tinha
gerado um vídeo íntegro. Bugs corrigidos e CONFIRMADOS nesta sessão:

1. **Fórmula de duração**: `target_lines = round(orig_dur / 3.8)` (SEM ×0.99).
   Decisão da dona: cobrir 100% da duração; efeitos esticam o vídeo, e maior/diferente
   do original é melhor pro anti-ban. Confirmado: source 78min → 1258 frases.
2. **Daemon real é `C:\recapd-e-animes\bin\anime_worker_daemon.py`** (o watchdog roda
   esse, NÃO a cópia da raiz). Perdi horas editando o arquivo errado. Se for editar o
   daemon, edite o de `bin/` e apague `bin\__pycache__\*.pyc`.
3. **Pillow (PIL) instalado** — faltava e quebrava a queima de legenda (`pipeline_failed`
   DEPOIS do concat).
4. **`--max-panels 0`** no modo deitado — desliga o teto de 1000 frases que truncava.
5. **Lock anti-render-concorrente** — daemon recusa POST duplicado (HTTP 409) +
   lockfile `workspace\render.lock`. Antes, N POSTs viravam N renders no mesmo workdir
   e travavam tudo.

### Fato importante sobre a INFRA
- **A rede do PC2 oscila muito.** edge-tts (TTS) depende de rede à Microsoft; quando a
  rede cai, o TTS fica lento mas NÃO trava de vez (reintenta). Sintoma paralelo: SSH ao
  PC2 cai a cada 1-2 comandos. Por isso todo comando SSH usa retry 6x.
- **Dispatch SEMPRE via task agendada `AnimeDispatchDeitado`**, nunca via Start-Process
  desacoplado (esses morrem silenciosamente por algum motivo no PC2). A task roda em
  sessão estável — foi ela que sustentou o render de 2h da tarde.
- **A árvore de ~4 processos `python anime-pipeline` é NORMAL** (cadeia pai→filho:
  daemon→pipeline→re-exec ANIME_ORIENT→run_one→ffmpeg). NÃO é duplicação. Conferir por
  ParentProcessId antes de matar achando que é duplicado.

### Estado no início do modo produção (~22:12 UTC)
- 1 render de VALIDAÇÃO rodando: source espanhol "Despierta 200 años" (JiJ2mbS9S2Q),
  4706s (78min), 1258 frases. Clipes prontos (1283), na fase de concat (xfseg~74).
- Falta: concat completo → música → legendas → RESULTADO com dur_ok/dur_ratio.
- Este é o PRIMEIRO teste end-to-end de todos os fixes juntos.

---

## Acesso ao PC2 (pro auditor)
- SSH: `ssh -i ~/.ssh/id_rsa_pc2 Emerson-IA@100.125.7.77`
- Flags recomendadas: `-o ConnectTimeout=30 -o ServerAliveInterval=15 -o ServerAliveCountMax=8`
- SEMPRE retry até 6x (rede oscila).
- Projeto no PC2: `C:\recapd-e-animes` (NÃO é repo git). Daemon porta 8772.
- Logs-chave em `C:\recapd-e-animes\workspace\`:
  - `dispatch_deitado.log` — o dispatcher (discover + POST). Procure "RESULTADO".
  - `dispatch_deitado_result.json` — JSON do último resultado (ok, dur_ok, dur_ratio, video_path).
  - `anime_worker_daemon.log` — o daemon (target_lines, roteiro, health).
- Vídeos prontos aprovados vão pra `D:\hipercool-materiais\animes recap\videos laterais\` (via anime_publish.py).

---

## OS CRONS (todos session-only, expiram em 7 dias, mas a sessão dura ~10h)

### CRON 1 — Monitor + auto-retry (a cada 23 min)
**ID/agendamento:** `23,46 * * * *` aprox (ver CronList).
**O que faz:**
1. Testa a rede (2 echos). Se ambos caem → "rede instável, aguardando", não faz nada.
2. Se há RESULTADO com dur_ok no dispatch_deitado.log:
   - dur_ok=True e dur_ratio>=0.85 → SUCESSO. Reporta números, avisa que dá pra publicar,
     e DISPARA O PRÓXIMO vídeo (limpa done.json, Start-ScheduledTask) pra manter produção.
   - dur_ok=False → reporta que saiu curto, registra pra investigar, mas segue produção.
3. Se NÃO há resultado E não há render ativo (sem anime-pipeline, sem clips crescendo):
   rede boa mas parado → verifica 1 daemon saudável, limpa render.lock antigo + done.json,
   redispara a task. Confirma que wavs/clips voltam a crescer.
4. Se há render ativo → só reporta progresso (ex: "620/1258 clips") e não mexe.

**Por que 23 min:** render deitado leva 2-4h; checar mais cedo é desperdício. O minuto :23
evita bater no :00 junto com outros crons do mundo.

### CRON 2 — Guarda de saúde do daemon (a cada 37 min)
**O que faz:** verifica que o daemon responde em http://127.0.0.1:8772/health. Se NÃO
responder (e não houver render ativo pra não matar job no meio), reporta e deixa o
watchdog resubir; se após checagem seguir morto, sobe manualmente
`pythonw bin\anime_worker_daemon.py`. NÃO reinicia daemon se houver render rodando
(regra de ouro — mataria o job).

**Por que separado do CRON 1:** monitoramento de progresso e saúde de infra são
preocupações diferentes; se o daemon cair, quero saber independente do ciclo de render.

### CRON 3 — Diário de bordo / heartbeat (a cada 1h07)
**O que faz:** grava uma linha de status em `workspace\producao_10h.log` no PC2 com
timestamp, fase atual (clips X/Y ou concat ou legenda), nº de vídeos concluídos na noite,
e dur_ratio do último. Serve de trilha de auditoria contínua pro agente da manhã ver a
evolução sem precisar reconstruir dos logs crus.

**Por que 1h07:** heartbeat não precisa ser frequente; 1h dá granularidade suficiente
pra reconstruir a noite. Minuto :07 evita colisão com os outros dois crons.

---

## O que o auditor da manhã deve verificar
1. Ler `workspace\producao_10h.log` (diário do CRON 3) — visão geral da noite.
2. Quantos vídeos concluíram? Ver `dispatch_deitado.log` (cada "RESULTADO") e a pasta
   de saída. Cada RESULTADO tem dur_ratio — todos >=0.85?
3. Algum dur_ok=False? Investigar o roteiro daquele (condensou demais? source ruim?).
4. O daemon ficou de pé a noite toda? (CRON 2 teria reportado quedas.)
5. Vídeos prontos e bons → publicar seguindo `docs/POSTAGEM_YOUTUBE_PLAYBOOK.md` e o
   padrão de postagem (PADRAO_DOC_POSTAGEM.md).

## LIÇÃO APRENDIDA (madrugada 2026-07-28 ~02:00 UTC)
- **NÃO limpar workdir nem render.lock de um job em ROTEIRIZAÇÃO.** A roteirização (LLM
  em blocos) roda DENTRO do daemon, sem subprocess `anime-pipeline` e SEM wavs/clips.
  Então "0 render procs + 0 wavs + lock=True" NÃO significa travado — pode ser um job
  gerando roteiro (dura 1-3min, ou mais se a rede/LLM engasgar). Apaguei o workdir
  `js2cwcrt` nesse estado e causei `FileNotFoundError: roteiro.txt` (dur_ok=False falso).
- **Regra corrigida:** antes de declarar um job "travado/parado", cheque o
  `anime_worker_daemon.log` — se a última linha é recente (< 5 min) e menciona
  "[script]"/"blocos"/"roteiro"/"fetch", ele está ROTEIRIZANDO, deixe quieto. Só considere
  parado se o daemon log estiver estagnado há >10min E não houver render procs E lock
  antigo (>1h).
- O 1º vídeo BOM (dur_ratio 1.055, 82.7min, source "Despierta 200 años" JiJ2mbS9S2Q) foi
  BAIXADO e VERIFICADO (675MB, dur 4964s íntegra) em:
  `D:\hipercool-materiais\animes recap\videos laterais\despierta-200-anos_cap1_20260727\final_anime_deitado.mp4`
  — AINDA NÃO PUBLICADO no YouTube. Publicar com anime_publish.py + PADRAO_DOC_POSTAGEM.md.
  (roteiro ainda no temp do PC2 anime_worker_8c9p0g0h se precisar de título/descrição.)

## ARQUITETURA RESILIENTE (add 2026-07-28 ~07:45 UTC) — LER
A produção NÃO depende mais de sessão externa/crons. Agora é autônoma no PC2:
- `_pc2_autoloop.py` (loop infinito) + tarefa `AnimeAutoLoop` (trigger AtLogOn, restart 3x) = sobe no boot.
- Vídeos prontos → pasta ESTÁVEL `C:\recapd-e-animes\saida\<id>_<data>\final_anime_deitado.mp4` (fora do %TEMP%).
- Autoloop varre órfãos do temp a cada ciclo e arquiva (nada se perde no restart).
- Task antiga `AnimeDispatchDeitado` = DESABILITADA. Só o autoloop orquestra.
- Os 3 crons de monitoramento foram ENCERRADOS (redundantes com o autoloop).
- **RESSALVA:** autoloop e watchdog sobem por trigger de LOGON. Se PC2 reinicia sem login automático da conta Emerson-IA, NÃO sobem — alguém precisa logar. Confirmar se há autologon.
- **Pro agente da manhã:** vídeos prontos ficam em `saida\` no PC2 E os 4 primeiros já em `D:\hipercool-materiais\animes recap\videos laterais\`. Buscar o resto de `saida\` via scp. Log do autoloop: `workspace\autoloop.log`.

## Riscos conhecidos / o que pode dar errado à noite
- **Rede muito ruim por horas** → TTS lento, poucos vídeos. Aceitável; não é falha.
- **Watchdog sobe daemon duplicado** → tolerável (lock impede render duplo); só atrapalha
  /health. Se 2 daemons, deixar quieto se há render rodando.
- **Cache de roteiro**: cada source gera 1 roteiro cacheado. Re-render do mesmo source
  reusa (rápido). Sources novos = LLM roda de novo.
- **YouTube upload limit**: se for publicar em lote, cuidado com uploadLimitExceeded.
