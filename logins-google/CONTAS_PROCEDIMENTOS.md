# Procedimentos de contas (feitos em 23/10/2026, para refazer quando precisar)

Regras de sempre:
- Senha e código só a dona digita.
- Conta nova só a dona cria.
- Nunca copiar cookies entre máquinas.
- Não entrar com conta que não seja da dona.
- Desktop: nada com OBS aberto ou câmera/microfone em uso.

## 1. Lista ÚNICA de contas: `kiro_contas_unica.json`
- Uma entrada por conta Google: em que máquina e perfil ela está (`pc1_cofre`, `pc1_chrome`, `desktop_chrome`, `pc2_chrome`), a situação no Kiro e se está no Antigravity do OmniRoute (`antigravity_omniroute`).
- O OmniRoute não mostra o e-mail das contas Kiro, então ESTA lista é a referência.
- Contas com Google morto foram tiradas em 23/10 (campo `removidas_mortas_23out`).
- **Para achar as contas de cada máquina** (só leitura do `Local State` do Chrome):
  - PC1: ver o comando em `KIRO_PROCEDIMENTO.md`, passo 4.
  - Desktop (shell PowerShell): `ssh desktop "$ls = Get-Content \"$env:LOCALAPPDATA\Google\Chrome\User Data\Local State\" -Raw | ConvertFrom-Json; $ls.profile.info_cache.PSObject.Properties | % { $_.Name + '|' + $_.Value.user_name }"`
  - PC2 (shell cmd): o mesmo comando dentro de `powershell -NoProfile -Command "..."`. O ssh pede `-o LogLevel=ERROR`.

## 2. Kiro (créditos, criar, conectar no OmniRoute)
Tudo em **`KIRO_PROCEDIMENTO.md`** (script `kiro_creditos.py`: `--abrir`, `--fila`, `--so-sem-kiro`, `--fechar-todas`).

## 3. Antigravity no OmniRoute: quem falta conectar
- Aqui o OmniRoute GUARDA o e-mail. Listar (só leitura, na VPS `ssh hermes-bloqueio`):
  ```
  python3 -c "import sqlite3; db=sqlite3.connect('file:/opt/omniroute/data/storage.sqlite?mode=ro', uri=True); print(sorted({(a or b or c).lower() for a,b,c in db.execute(\"select coalesce(email,''),coalesce(name,''),coalesce(display_name,'') from provider_connections where provider='antigravity'\") if '@' in a+b+c}))"
  ```
- Cruzar com a lista única. As que faltam: abrir no perfil/máquina delas na página do painel
  `http://157.173.207.22:20128/dashboard`, e a dona conecta.
- Abrir no Chrome normal: `chrome.exe --profile-directory="Profile N" --new-window <url>`.
- No desktop e no PC2: um `.bat` com os comandos `start "" chrome.exe ...`, rodado pela tarefa `KiroAbrir` (`schtasks /it`; abre na tela da dona).
- 23/10: 95 contas na lista, 77 já no Antigravity, 18 abertas para conectar.

## 4. TikTok nos notebooks
Em `D:\postador-de-videos\docs\NETBOOKS_POSTAGEM.md`, seção "Login do TikTok nos notebooks" ("Continuar com Google" com o Google que já está no notebook; script `bin\netbooks\tiktok_notebooks.py`).

## 5. Canais do YouTube ainda não usados
Resultado em `YOUTUBE_CANAIS_LIVRES.md`.
- **Contas do cofre:** `python yt_canais_livres.py`. Lê "All channels" em youtube.com/channel_switcher, vê na página pública se o canal está banido e compara @ e nome com o cadastro do postador. Canais pessoais da dona ficam em `PESSOAIS` no script.
- **Chrome normal (disco C) do PC1 ou do desktop:** `python print_perfis_chrome.py https://www.youtube.com/channel_switcher "Profile N=nome" ...`. Abre cada perfil, tira print só da janela e fecha.
  - No desktop: rodar pela tarefa `KiroAbrir` (`.bat` com `set PRINT_SAIDA=C:\postador-worker\yt_prints` e `set PRINT_PREFIXO=desk_`) e trazer os prints por scp.
  - Com a dona usando o PC, o Windows não deixa a janela vir para a frente e o print sai errado: rodar com o PC parado.
  - Conta "desconectada" (pede login) não serve até a dona logar.

## 6. Espaço em disco e mapa do Drive
- O que roda sozinho, o que volta do Drive e as medidas de aperto: `D:\video-fila\ESPACO_EM_DISCO.md`.
- Mapa do Drive (pegar algo à mão): `D:\video-fila\MAPA_DRIVE.md` (refazer: `python D:\video-fila\mapa_drive.py`).
