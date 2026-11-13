# Desktop: pôr pra trabalhar e, se precisar, virar o PC principal (29/10/2026)

> Para a dona e para a IA que for rodar NO desktop. Decisão completa: D38b em
> `D:\hipercool-materiais\tarefas complexas para fable 5.1\FABLE_DECISOES.md`. Guia técnico de cada máquina:
> `D:\projeto-navegador-sem-navegador\IMPLANTAR_MAQUINA.md`.

## Onde estamos

- O sshd do desktop (OpenSSH 10.4) **aceita a chave e derruba a sessão** em boa parte das conexões, também pela rede de
  casa (192.168.18.45), então não é a Tailscale; `PerSourcePenalties` já está `no`. Comando curto passa às vezes; scp
  e comando grande quase nunca. A causa está no Windows do desktop (antivírus? processo `sshd-session` caindo?): olhar
  **no desktop** o Visualizador de Eventos → Aplicativos e Serviços → OpenSSH → Operational e Logs do Windows →
  Aplicativo (erros com "ssh").
- Por isso existe a **vigia** no PC1: tarefa `DesktopVigia` (a cada 10 min, sem janela) = `D:\video-fila\desktop_vigia.py`.
  Ela tenta 1 conexão por rodada e, quando entra, faz 1 passo por vez: telão + medidor → conferir → chave própria do
  desktop → worker do navegador-sem-navegador → cookies do Flow de cada perfil (só com a câmera desligada) → saúde.
  Os arquivos vão por HTTP (o desktop puxa do PC1), nunca por scp.
  - Ver como está: `D:\veo\venv\Scripts\python.exe D:\video-fila\desktop_vigia.py --status` e `D:\video-fila\logs\desktop_vigia.log`
  - Telegram: cada passo concluído, ssh voltando depois de 3 h fora, e **24 h sem conseguir entrar** (= plano B abaixo).
- 29/10 23:51: telão + medidor **instalados** (arquivos em `C:\vitrine`, tarefa `Desktop_Telao`, atalhos
  **DESLIGAR TELAO** / **LIGAR TELAO** na área de trabalho). O telão só aparece com câmera e microfone livres, sem OBS.

## Passo 1 (a dona, no PC1): dar ao desktop acesso às outras máquinas

Quando a vigia avisar "chave ssh própria criada lá" (ou existir `D:\video-fila\estado\desktop_chave.pub`), abrir
**PowerShell como administrador** no PC1 e rodar:

```powershell
powershell -ExecutionPolicy Bypass -File D:\video-fila\autorizar_desktop.ps1
```

Isso liga o servidor ssh do Windows **no PC1** (hoje o PC1 não tem) e autoriza a chave do desktop no PC1, PC2, x200ma
e acer. O desktop já recebe o `~\.ssh\config` com `pc1`, `pc2`, `x200ma`, `acer`. Teste no desktop:
`ssh pc1 hostname`, `ssh pc2 hostname`, `ssh x200ma hostname`, `ssh acer hostname`.

## Plano B: o desktop vira o PC principal (se em 24 h o ssh não estabilizar)

Na máquina do desktop, abrir o Claude Code / a IA e dar este arquivo para ela ler. Ordem:

1. **Pegar os arquivos do PC1** (depois do passo 1; do desktop puxando, que é o sentido que funciona):
   ```powershell
   scp -r pc1:"D:/video-fila" pc1:"D:/postador-de-videos" pc1:"D:/projeto-navegador-sem-navegador" D:/
   scp -r pc1:"D:/veo" pc1:"D:/flow-imagens" pc1:"D:/hipercool-materiais/tarefas complexas para fable 5.1" D:/
   ```
   (outros projetos — `D:\hipercool-videos`, `D:\manhwa-react`, `D:\recapd-ambientes` — só se forem rodar lá.) Sem o
   passo 1: pendrive, ou o Drive (`D:\tools\rclone.exe` no PC1, remoto `manhwa-drive:`).
   **Nunca** copiar `cookies\` nem perfis do Chrome entre máquinas (cada máquina usa os cookies dela; regra fixa).
2. Ler antes de mexer: `FABLE_DECISOES.md` (decisões e o que NÃO fazer), `IMPLANTAR_MAQUINA.md`, o `CLAUDE.md` de cada
   projeto e `D:\video-fila\linhas\tarefas_pc1\LISTA.md` (as 106 tarefas agendadas do PC1, com o XML de cada uma).
3. Python: o do desktop é `C:\Program Files\Python311` (caminho com espaço — tarefa agendada por `Register-ScheduledTask`,
   não `schtasks /tr`). Criar um venv igual ao `D:\veo\venv` do PC1 e instalar as libs que cada projeto pede.
4. Tarefas: importar só as que vão rodar no desktop
   (`Register-ScheduledTask -Xml (Get-Content <arq>.xml -Raw) -TaskName <nome>`), trocando os caminhos se mudarem.
   **Desligar a mesma tarefa no PC1** antes (duas postando ao mesmo tempo = post em dobro).
5. Regras que continuam: tarefa agendada nunca abre janela (pythonw, `sem_janela`); pythonw não tem stdout; câmera
   fixa ter/qui 10–12 h e sex 16–18 h (`D:\video-fila\maquinas.py AGENDA_CAMERA`): nada de navegador nesses horários.

## Interruptores

- Parar a vigia: `schtasks /change /tn DesktopVigia /disable`.
- Tirar o telão da tela sem desinstalar: atalho DESLIGAR TELAO (cria `C:\vitrine\desligado.txt`).
- Refazer um passo: apagar a chave dele em `D:\video-fila\estado\desktop_vigia.json` (ex.: `"nsn"`).
