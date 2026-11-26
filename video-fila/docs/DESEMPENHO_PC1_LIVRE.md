# PC1 livre pro VS Code — o que foi feito (24/11/2026)

Pedido da dona: o PC1 só faz o que SÓ ele pode fazer (conta logada / IP fixo). Todo o resto que gasta CPU
(render, ffmpeg, whisper, demucs, treino, teste) roda nos outros PCs do sistema. Fora da fila por serem fracos:
x200ma e asus-eepc.

## Medida
- Início (24/11 ~00:00): RAM livre 1,6 GB de 15,8; CPU 100%; 59 PowerShell, 257 conhost, 13 Chromes de automação.
- Depois (24/11 ~15:40): RAM livre 6,7 GB; 13 PowerShell, 142 conhost, 5 Chromes. CPU continua 100% (renders ainda no PC1).

## O que existe agora

| Peça | Onde | O que faz |
|---|---|---|
| Liberar RAM | `D:\video-fila\liberar_ram.ps1`, atalho "Liberar RAM" no Desktop, tarefa `LiberarRamVigia` (2/2 min) | Fecha Chrome de automação esquecido (>3 h) e ffmpeg parado (>1 h), mata árvore de .bat/bash/powershell sem CPU há 45 min, esvazia memória parada (como o Wise). Nunca toca VS Code, claude, Chrome pessoal, pontes, painel. Dispara sozinha com RAM livre < 1,2 GB (ou CPU >= 95% e RAM < 2,4 GB), no máx. 1x/15 min; varredura completa só a cada 10 min. `-Simular` não grava a hora da última limpeza. Log: `logs\liberar_ram.log`; estado: `estado\liberar_ram.json`. |
| Portão do PC1 | `C:\Users\Haylla\.claude-vscode\hooks\portao_pc1_pesado.py` (PreToolUse Bash/PowerShell no settings.json) | Bloqueia nos chats: ffmpeg (menos `-version` e tirar 1 quadro), whisper, demucs, treino/finetune, `remotion render`. Exceção: `#PC1_OK` no comando + avisar a dona. ffprobe liberado. Não vale para tarefa agendada. |
| Painel sem PowerShell | `painel_controlador.py` `_lista_processos` | Lista processos por psutil (2,4 s contra 22 s) em vez de abrir PowerShell a cada 20 s. Se o psutil falhar, volta ao PowerShell (`_lista_processos_ps`). |
| Verificador de alarmes | `painel_ia.py` linha ~686 (`ABAIXO_NORMAL`) | O `claude -p` e o `rg` dele abrem em prioridade abaixo do normal. |
| Fila invisível | `D:\video-fila\despacho.py` | Escolhe a máquina livre que sabe fazer o trabalho (CAPAZ por máquina: ffmpeg, python, remotion). Para trabalho de conta só vai para PC onde a conta já está logada (lê `maquina_remota`). `python despacho.py estado` mostra tudo. |
| Render das solares fora | `D:\claude-code-video\gerar.py` `_render_fora` | O render Remotion vai para asusx ou itau; se nenhum estiver livre ou falhar, renderiza no PC1 como antes. `RENDER_FORA=0` desliga. |
| Remotion nos notebooks | asusx e itau: `~/claude-code-video/remotion` | Instalado por `D:\tmp\remotion_asusx\instalar.sh` + `base.tar.gz` (sem node_modules; `npm ci` com versões fixas). |

ffmpeg e whisper NÃO foram apagados do PC1: a produção agendada (ClaudeCodeVideo, Kit3d, Comentários, capas, Mascote) usa.

## Verificado
- Portão: 5 casos de teste no hook (-version e ffprobe passam; ffmpeg com filtro e whisper bloqueados; #PC1_OK libera).
- Painel: reiniciado, HTTP 200, 0 PowerShell filhos em 6 amostras.
- Vigia leve: com estado recente e RAM normal saiu sem varrer. `-Simular` não regrava `ultima`.
- Render real: vídeo da MS Energy (`msenergycap_20261124_005025`) no asusx em 2047 s, 28,6 MB, h264 1080x1920 30 fps + aac, 28,5 s; quadro do meio conferido.

## NÃO verificado / pendente
- itau: Remotion instalado, mas nenhum render feito lá ainda.
- Desktop: não respondeu ao ssh (porta 2223, timeout). Não sei se ele tem ffmpeg.
- pc2: ffmpeg não confirmado (a checagem voltou vazia). Desktop e pc2 foram listados como capazes de ffmpeg sem prova — conferir antes de confiar.
- sti e hp: ffmpeg está em `~/bin` (não no PATH); node/chromium presentes mas Remotion não instalado.
- Notificação (toast) do botão "Liberar RAM": rodou sem erro, mas ninguém viu aparecer na tela.
- `painel_ia`: nenhum pedido rodou ainda com a prioridade baixa.
- Só a etapa Remotion do `gerar.py` saiu do PC1. Ainda no PC1: capas (CaparShorts), Kit3d, Comentários, Mascote, o resto do render ffmpeg (separar render de postagem em cada uma).
- Verificador de alarmes NÃO foi para outra máquina: depende de `D:\video-fila\logs` e da API 127.0.0.1:8790.
- O render Remotion no asusx leva ~34 min (no PC1 ~5 min): compensa para liberar o PC1, não para velocidade.

## Erro meu a não repetir
- 24/11 ~00:08: matei por engano um ffmpeg recém-iniciado (o número de processo anotado já tinha sido reaproveitado). Sempre conferir o PID e a hora de abertura juntos.

## Regras que continuam
- Nunca duas contas pelo mesmo IP; tudo que fala como conta fica no PC1 / saída fixa da conta.
- Máquina de teste: `python D:\video-fila\teste_remoto.py --tipo render|python|pesado -- <comando>`.
- Memória: `project_liberar_ram.md`, `project_despacho_fila_invisivel.md`, `feedback_pc1_livre_testes_fora.md`.
