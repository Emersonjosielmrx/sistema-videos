# Pacote de revisão — "PC1 livre pro VS Code" + fila invisível de render (24 a 26/11/2026)

Para: agente revisor independente. Objetivo: conferir se o que foi feito está certo, achar bugs/riscos e propor
melhorias. Só leitura até a dona autorizar; nada de render/ffmpeg/whisper no PC1.

## 1. Pedido da dona (palavras dela, resumidas)
- "Analise o que podemos parar pra liberar CPU e RAM desse PC que não seja o VS Code."
- "Faça e crie um script que ao sobrecarregar faça isso; coloque um botão no Desktop e uma notificação como a do Wise."
- "Crie uma regra de não usar esse PC pra testes; sempre que possível rodar em um dos PCs do sistema."
- "Tudo que consumir CPU e der pra mandar pra outro PC da rede deve ser feito no outro. O que só está logado nesse
  (navegador com conta) ou teste muito rápido fica aqui."
- "Deve haver uma fila invisível que distribui pros PCs considerando as contas que eles têm logadas."
- "Todos, tirando o acer x200ma e o asus-eepc (fracos), devem ser capazes de fazer os Shorts, longos, Insta etc."

## 2. Máquinas
- PC1: Windows, `ssh pc1` (100.118.234.102). Tem todas as contas logadas; roda o VS Code. Pastas: D:\video-fila,
  D:\claude-code-video, D:\postador-de-videos, D:\hipercool-materiais.
- Omarchy (100.123.60.57): só central de comando (chats). Nada pesado aqui.
- asusx, itau: notebooks Omarchy/Arch, i5, 11 GB, ffmpeg+node+chromium. Remotion instalado nos dois.
- sti, hp: Mint; ffmpeg em ~/bin (fora do PATH); sem Remotion. sti esquenta (97-100 °C).
- s20, s20ultra, g20: celulares Termux, só ffmpeg.
- desktop, pc2: Windows. desktop NÃO respondeu ao ssh (porta 2223); ffmpeg do pc2 NÃO confirmado.
- Fora: x200ma, acer, asus-eepc (fracos; só navegador).

## 3. Regras invioláveis
- NUNCA duas contas pelo mesmo IP (Kaggle/Google/TikTok/Instagram/YouTube). Ler antes:
  D:\hipercool-materiais\comum\kaggle_gerente\INCIDENTE_BANIMENTO_02NOV.md. Conta viva do Kaggle só pelo
  `cofre.saida_kaggle(email)`. Trabalho que fala como conta fica no PC1/saída fixa dela.
- Nunca matar pythonw nem produção em andamento. Nunca git reset na produção.
- No PC1: começar só lendo; nunca apagar/sobrescrever sem a dona autorizar. PowerShell 5: `;`, nunca `&&`.
- Uma conexão ssh por vez (rajada trava o desktop).

## 4. O que foi feito (arquivos no PC1)

| # | Arquivo | O que faz | Estado |
|---|---|---|---|
| 1 | D:\video-fila\liberar_ram.ps1 + atalho "Liberar RAM" no Desktop + tarefa LiberarRamVigia (2/2 min) | Fecha Chrome de automação esquecido (via limpeza_chrome.ps1 -Horas 3 -HorasFfmpeg 1), mata árvore .bat/bash/powershell sem CPU há 45 min e com 60+ min, EmptyWorkingSet em tudo menos Code/claude, toast. Dispara com RAM < 1,2 GB (ou CPU >= 95% e RAM < 2,4 GB), 1x/15 min. | ATIVO no PC1. Revisão achou riscos ALTOS (seção 6). |
| 2 | C:\Users\Haylla\.claude-vscode\hooks\portao_pc1_pesado.py (PreToolUse Bash/PowerShell no settings.json do VS Code) | Bloqueia nos chats do PC1 ffmpeg (menos -version e 1 quadro), whisper, demucs, treino, `remotion render`; exceção `#PC1_OK`. | ATIVO. Revisão achou furos e falsos positivos (seção 6). |
| 3 | D:\video-fila\painel_controlador.py `_lista_processos` (~179-215) | psutil em vez de PowerShell a cada 20 s (2,4 s x 22 s); fallback `_lista_processos_ps`. | ATIVO, revisado OK (formato igual). |
| 4 | D:\video-fila\painel_ia.py (~43 e ~686) | `claude.exe` do verificador de alarmes com prioridade ABAIXO_NORMAL. | ATIVO; nenhum pedido visto rodando assim. |
| 5 | D:\video-fila\despacho.py (NOVO) | Fila invisível: CAPAZ por máquina, vez = a mesma de celulares.py (estado\celulares), medida de celulares.medir; `remotion()` leva src/lib+src/videos/<id>+public por tar no ssh, renderiza lá e traz o mp4. | ATIVO no PC1 na versão ANTIGA. Versão corrigida em despacho_corrigido.py (desta pasta), NÃO aplicada. |
| 6 | D:\claude-code-video\gerar.py `_render_fora` (~1012) + `_render` | Render Remotion das solares tenta o despacho; falhou/nenhuma livre = renderiza no PC1. `RENDER_FORA=0` desliga. timeout=2400. | ATIVO. |
| 7 | asusx e itau: ~/claude-code-video/remotion | Instalado com D:\tmp\remotion_asusx\instalar.sh + base.tar.gz (77 KB, sem node_modules; `npm ci`). | asusx provado; itau sem render. |
| 8 | D:\video-fila\docs\DESEMPENHO_PC1_LIVRE.md | Documento do que foi feito. | Parcialmente divergente do código (revisão item 10). |
| 9 | Memórias em C:\Users\Haylla\.claude-vscode\projects\d--\memory: project_liberar_ram.md, project_despacho_fila_invisivel.md, feedback_pc1_livre_testes_fora.md; regra no C:\Users\Haylla\.claude-vscode\CLAUDE.md | Registro. | — |
| 10 | Omarchy ~/.claude/settings.json | 26/11 (dona pediu "pra não ficar pedindo"): modo bypassPermissions + additionalDirectories "/" + regras extras. Backup: settings.json.bak-20261126-0717. | Feito. |

ffmpeg/whisper NÃO foram apagados do PC1 (produção agendada usa: ClaudeCodeVideo, Kit3d, Comentários, capas, Mascote).

## 5. Provas que existem
- RAM livre do PC1: 1,6 GB (24/11 00h) -> 6,7 GB (24/11 15h40). CPU segue 100% (renders ainda no PC1).
- Render real: msenergycap_20261124_005025 no asusx em 2047 s, 28,6 MB, h264 1080x1920 30 fps + aac, 28,5 s;
  quadro do meio conferido. No PC1 leva ~5 min.
- Painel reiniciado: HTTP 200, 0 PowerShell filhos em 6 amostras.
- Portão: só 5 casos testados (pouco).

## 6. Achados das 2 revisões (25-26/11) — conferir
ALTO
- despacho `candidatas()`: mandava trabalho de CONTA pra máquina onde a conta só está "logada" (login ≠ IP fixo; foi
  a causa do 3º banimento). Nenhum chamador usa hoje. CORRIGIDO na versão nova (conta = sempre PC1).
- despacho: render órfão se o ssh cai (pkill só no timeout; padrão 'remotion render' casava com o próprio shell).
  CORRIGIDO: `timeout -k 20` lá, `flock jobs/.lock`, pkill por nome do job em qualquer falha.
- despacho: mp4 aceito com >10 KB sem conferir. CORRIGIDO: tamanho medido lá = tamanho chegado.
- gerar.py: timeout 2400 s com render real de 2047 s (17% de folga). NÃO corrigido.
- liberar_ram.ps1: pode matar produção que só espera rede (python/ssh/rclone esperando o asusx). NÃO corrigido.
- liberar_ram.ps1: kill por PID sem rechecar a hora de abertura (mesmo erro de 24/11). NÃO corrigido.
- liberar_ram.ps1: rodadas começam e não terminam (log 25/11 00:51 e 07:07; tarefa PT10M + IgnoreNew; 0x800710E0).
  NÃO corrigido.
- liberar_ram.ps1 / limpeza_chrome.ps1: ffmpeg "parado" morto com 1 h (padrão era 6 h). NÃO corrigido.
MÉDIO
- portão: json.load com cp1252 libera tudo com "Á"/emoji; falsos positivos (git commit, escrever .md, Test-Path em
  pasta whisper, pip/winget); furos (`teste_remoto.py` em qualquer parte libera tudo; `&`; crase/$(...);
  remotion.cmd; treinar_voz.py). Revisor 1 propôs reescrita (58 casos, 0 erros) — NÃO aplicada.
- EmptyWorkingSet sem ganho medido (2,67->2,55; 6,34->6,52 GB) e pode gerar page faults: sugerido só no botão.
- painel_ia prioridade baixa + SEM_LINHA_MIN 12 pode dar falso "travado" com PC1 a 100%: subir pra ~25.
- desktop/pc2 nunca escolhidos (não estão em celulares.HOSTS e medir é Linux). CAPAZ deles é só rótulo.
- despacho ignora `lento` (hp 267 s x s20ultra 36 s) e a regra sti_short do celulares._escolher.
- Duas políticas de escolha (despacho x celulares x fila_render/maquinas.py).
BAIXO: toast conta bytes x caracteres; botão -Agora pode ser morto pela vigia; árvore por ParentProcessId sem data;
FreePhysicalMemory x Available; vigia pesada a cada 2 min; hook só vale pro VS Code do PC1.

## 7. O que ainda roda no PC1 (candidatos a migrar)
CaparShorts (15 min), CapasDepois (10 min), Kit3dDiario, ComentariosProducao, MascoteProducao, anime_auto
--engine local, produto.diario, reel_advance. Cada um mistura render e postagem: separar (render sai, postagem fica).
Ferramentas já prontas: celulares.rodar_ffmpeg (ffmpeg com rodízio), despacho.remotion, teste_remoto.py.

## 8. Pedido ao revisor
1. Conferir os achados da seção 6 no código (arquivo:linha), dizer o que é real e o que não é.
2. Revisar despacho_corrigido.py (diff contra D:\video-fila\despacho.py) e dizer se pode substituir.
3. Propor a correção exata de liberar_ram.ps1 / limpeza_chrome.ps1 / portão, com testes.
4. Dizer o que NÃO conseguiu conferir.
