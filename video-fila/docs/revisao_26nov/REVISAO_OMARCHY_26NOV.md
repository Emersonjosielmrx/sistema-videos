# D:\video-fila\docs\revisao_26nov\REVISAO_OMARCHY_26NOV.md
# Revisão (só leitura) do pacote LEIA_REVISAO.md — feita pelo agente do Omarchy em 26/11/2026 ~07:40

Arquivos lidos (cópias de 26/11 07:35): despacho.py, despacho_corrigido.py, liberar_ram.ps1, limpeza_chrome.ps1,
portao_pc1_pesado.py, gerar.py. Nada foi alterado no PC1.

## 1. Achados da seção 6 conferidos no código

| Achado | Real? | Onde | Observação |
|---|---|---|---|
| despacho manda trabalho de conta para máquina "logada" | REAL na versão em uso | despacho.py `candidatas()` (filtra por `onde(conta)`) | corrigido no _corrigido (devolve []) |
| render órfão se o ssh cai | REAL | despacho.py: `pkill -f 'remotion render'` só no `TimeoutExpired` | corrigido no _corrigido |
| mp4 aceito com > 10 KB | REAL | despacho.py `st_size < 10000` | corrigido (tamanho lá = aqui) |
| gerar.py timeout 2400 x render 2047 s | REAL | gerar.py:1027 `timeout=2400` | e o _corrigido ainda gasta até 600 s no `flock` FORA desse prazo (ver 2.a) |
| liberar_ram mata produção que só espera rede | REAL | liberar_ram.ps1:63-69 | "parado" = CPU da árvore mudou < 0,3 s em 45 min. Um gerar.py esperando render no asusx (34 min de ssh parado) + etapas paradas chega perto; python/ssh esperando rede não gastam CPU |
| kill por PID sem rechecar abertura | REAL | liberar_ram.ps1:100-101 (`taskkill /PID`, `Stop-Process` por Id) | a lista vem do WMI tirado antes; entre ele e o kill roda a limpeza_chrome inteira (minutos) |
| rodadas que não terminam | NÃO CONFERIDO | log/tarefa | linha 22-23 mata liberar_ram com > 6 min, o que pode esconder isso |
| ffmpeg "parado" morto com 1 h | REAL, risco menor que o dito | liberar_ram.ps1:89 `-HorasFfmpeg 1` | limpeza_chrome.ps1:123-131 só fecha se 0 CPU em 30 s, então só pega ffmpeg de fato parado (ex.: esperando entrada de pipe) |
| portão: encoding cp1252 libera tudo | REAL | portao:37 `json.load(sys.stdin)` sem UTF-8; erro -> `return 0` | trocar por `json.loads(sys.stdin.buffer.read().decode("utf-8","replace"))` |
| portão: `teste_remoto.py` em qualquer parte libera tudo | REAL | portao:41 | `x; ffmpeg -i ...; echo teste_remoto.py` passa |
| portão: crase/$(...) | REAL | portao:44 | parte que começa com `ls`/`echo`/`cat` é pulada inteira: `ls $(ffmpeg -i a b)` passa |
| portão: `&` | NÃO é furo | regra 1 já aceita `&` antes de ffmpeg | |
| desktop/pc2 nunca escolhidos | REAL | `h in celulares.HOSTS` em candidatas() | |

## 2. despacho_corrigido.py pode substituir? Sim, depois de 3 ajustes

a) Prazo: o remoto faz `flock -w 600` e só DEPOIS começa `timeout limite` (limite = timeout-60). Com a fila ocupada, o
   local (`p.wait(timeout)`) mata no meio do render. Sugestão: `timeout -k 20 {limite} flock -w 600 ...` (o prazo
   cobre a espera) ou `flock -w` pequeno e devolver "ocupada" para tentar outra máquina.
b) **itau mudou (26/11):** formatado com Linux Mint, novo acesso `emerson-itau@100.90.133.57`, SEM Remotion, SEM node,
   SEM postador; e o `Host itau` do ~/.ssh/config do PC1 ainda aponta o IP antigo (100.100.73.28, fora do ar).
   `CAPAZ["itau"]` diz remotion: tirar "remotion" do itau até reinstalar (D:\tmp\remotion_asusx\instalar.sh).
   Ele também desligou sozinho 3x depois da troca da pasta térmica: não mandar trabalho até conferir.
c) Filhos do Chromium: o `pkill -f '[j]obs/{job}/'` pega flock/sh/timeout/npx, e o `timeout` (sem --foreground)
   repassa o sinal ao grupo, então deve pegar o Chromium; não testado. Conferir com `pgrep -f chrom` depois de uma falha.
Conferido OK: validação de id/args (impede injeção no `sh -c '...'`), conta nunca sai, tamanho conferido, limpeza em
qualquer falha, `[j]` evita o pkill se matar.

## 3. Correção proposta (não aplicada)

- liberar_ram.ps1: (1) não contar como travada árvore que tem `ssh`, `rclone`, `python` com conexão TCP aberta
  (Get-NetTCPConnection -OwningProcess) — está esperando rede; (2) antes do kill, reler `Get-Process -Id` e comparar
  `StartTime` com `CreationDate` guardado; (3) `-HorasFfmpeg 3`. Testar com `-Simular` e um `ssh pc1 sleep 3600` falso.
- portão: as 3 linhas acima (UTF-8, `teste_remoto.py` só no início do comando, não pular parte com `$(`/crase).
- gerar.py: `timeout=3600` enquanto o render no asusx levar ~2047 s.

## 4. O que não consegui conferir
Logs reais das rodadas presas, tarefas agendadas e o comportamento com o PC1 a 100% (só leitura de código).
`celulares.py`/`_rota` (não li): se `_rota("itau")` usa o ~/.ssh/config, a fila tenta o IP antigo e perde 15 s.
