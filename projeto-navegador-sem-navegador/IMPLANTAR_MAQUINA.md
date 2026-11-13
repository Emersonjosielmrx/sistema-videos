# Implantar o "navegador sem navegador" numa máquina (desktop, PC2, notebooks, PC novo)

> Escrito em 29/10/2026 depois de implantar no x200ma, acer e PC2 (D23, D30, D31 em
> `D:\hipercool-materiais\tarefas complexas para fable 5.1\FABLE_DECISOES.md`). Serve para o **desktop** (que ficou
> pela metade por causa do ssh) e para qualquer PC novo. Tudo é comandado do PC1; nada se digita na máquina, exceto o
> login das contas (que só a dona faz) e o que está marcado como "na máquina".
>
> Regra fixa (dona 29/10): **cada máquina usa os próprios cookies; nunca copiar `cookies/` entre máquinas.**

## 0. O que fica em cada máquina (resultado final)

| Item | Linux (notebooks) | Windows (PC2, desktop) |
|---|---|---|
| Chrome das contas (1 por vez) | `~/postador-worker/chrome_conta.py`, perfis em `~/postador-worker/perfis/<perfil>` | `C:\postador-worker\chrome_conta.py`, perfis em `C:\postador-worker\perfis\<perfil>` |
| Worker do nsn (código + cookies DA máquina) | `~/postador-worker/nsn/` | `C:\postador-worker\nsn\` com venv próprio em `nsn\venv` |
| Entrada/saída de arquivos | `~/postador-worker/entrada/`, `~/postador-worker/nsn/saida/` | `C:\postador-worker\entrada\`, `C:\postador-worker\nsn\saida\` |
| Porta do Chrome | 9460 (só localhost; o PC1 chega por túnel ssh) | 9460 |

O PC1 fala com a máquina só por ssh com chave (`~/.ssh/config`: hosts `x200ma`, `acer`, `pc2`, `desktop`). A tabela
`MAQUINAS` em `D:\postador-de-videos\bin\maquina_remota.py` é a lista oficial (nome, usuário@ip, porta ssh, `win`,
python do Windows). **PC novo = acrescentar uma linha lá** e no `~/.ssh/config`.

## 1. Pré-requisitos (uma vez por máquina)

1. **ssh com chave, sem senha.** No PC1: `ssh -o BatchMode=yes <host> "echo OK"` tem de imprimir `OK`.
   - Windows: serviço OpenSSH (`sshd`) instalado e iniciado; a chave pública do PC1 em
     `C:\ProgramData\ssh\administrators_authorized_keys` (usuário administrador) ou `~\.ssh\authorized_keys`.
   - O shell do ssh no Windows pode ser `cmd` (PC2) ou PowerShell (desktop): o `maquina_remota` já lida com os dois;
     nunca escreva comando novo com `cd /d … &&` (PowerShell não entende) — use `powershell -NoProfile -Command "…"`
     ou chame o python pelo caminho completo do script.
2. **Google Chrome** instalado. Linux sem sudo: `python bin\maquina_remota.py preparar-chrome <maq> --dona-autorizou`
   (baixa o .deb oficial e extrai em `~/.local/chrome`).
3. **Python 3.11+** que o ssh enxergue:
   - Linux: `python3` do sistema (3.12 nos notebooks). Sem pip (Ubuntu sem ensurepip): as libs entram descompactando
     wheels no user-site (já feito; para máquina nova, repetir: `curl_cffi` cp312 manylinux + `websocket-client` +
     `requests` + `Pillow`).
   - Windows: um python qualquer para o `chrome_conta.py` (só biblioteca padrão) — no PC2 é o do pgAdmin,
     `"C:\Program Files\PostgreSQL\16\pgAdmin 4\python\python.exe"` (campo `python` em `MAQUINAS`); no desktop é o
     Python 3.11 do usuário. E um **venv do worker** (passo 3).
4. **Tailscale/rede**: ping e porta 22 abertos a partir do PC1.

## 2. chrome_conta.py (o "1 Chrome por vez" da máquina)

No PC1:
```bash
python D:\postador-de-videos\bin\maquina_remota.py instalar
```
Copia `bin\netbooks\chrome_conta.py` para todas as máquinas da tabela e cria `perfis/` e `entrada/`. Conferir:
```bash
python D:\postador-de-videos\bin\maquina_remota.py estado
```
Cada máquina responde um JSON com `"aberto": null`, a lista de perfis, RAM livre e o caminho do Chrome.
Sem Chrome encontrado → voltar ao passo 1.2.

## 3. Worker do nsn

### 3a. Windows: criar o venv UMA vez (na máquina ou por ssh)
```powershell
cd C:\postador-worker
mkdir nsn ; cd nsn
<python 3.11+ da máquina> -m venv venv
.\venv\Scripts\python.exe -m pip install curl_cffi websocket-client requests pillow
```
O `instalar-nsn` exige que `C:\postador-worker\nsn\venv\Scripts\python.exe` exista; ele **não** cria o venv.
(29/10: PC2 e desktop estavam sem o Pillow, que o `postar.py` do Instagram importa — por isso o pip acima tem `pillow`.)

### 3b. Instalar/atualizar o código (todas as máquinas, do PC1)
```bash
python D:\postador-de-videos\bin\maquina_remota.py instalar-nsn            # todas
python D:\postador-de-videos\bin\maquina_remota.py instalar-nsn desktop    # só uma
```
Empacota `tools\empacotar_worker.py` (código + `modelos_ig.json`, **sem** cookies) e copia preservando `cookies/`,
`saida/` e `venv/` de lá. Resposta esperada: `<maq>: nsn ok N cookies`. Rode de novo **toda vez que o nsn mudar**.

## 4. Logar as contas na máquina (só a dona)

```bash
python D:\postador-de-videos\bin\maquina_remota.py proxima            # qual e-mail falta logar
python D:\postador-de-videos\bin\maquina_remota.py logar <perfil>     # abre o Chrome NA TELA das máquinas p/ entrar
python D:\postador-de-videos\bin\maquina_remota.py ativar <perfil>    # confere o login e liga a máquina pra conta
```
`perfil` = parte do e-mail antes do `@` (Google) ou `ig_<conta>` (Instagram). O `ativar` grava em
`config\netbooks_logins.json` onde cada conta está logada; é essa tabela que diz ao Veo, ao Instagram e ao YouTube
em quais máquinas a conta pode rodar.

## 5. Colher os cookies na máquina (a partir daí tudo é HTTP)

- Instagram: a tarefa `NSN_ColherNotebooks` (a cada 2 h) colhe sozinha; para forçar:
  `python D:\projeto-navegador-sem-navegador\tools\colher_notebooks.py <maq>`.
- Google/Flow: `python D:\postador-de-videos\bin\maquina_remota.py colher-flow <perfil> <maq>`; também acontece sozinho
  a cada vídeo do Veo gerado por HTTP lá.
- Qualquer post pelo Chrome da máquina também colhe no fim (`nsn_colher`).

Conferir, sem abrir Chrome:
```bash
python D:\postador-de-videos\bin\maquina_remota.py saude-flow <maq>   # Flow + Instagram logados lá (HTTP)
```
A aba **Sem navegador (HTTP)** do painel (:8790) mostra o mesmo por máquina (`<conta>@<maq>`), de hora em hora.

## 6. Provas (uma de cada, antes de dar por implantado)

| O quê | Comando no PC1 | Esperado |
|---|---|---|
| Leitura do Instagram lá | `python -m services.instagram.web <conta> --maquina <maq>` (em `D:\projeto-navegador-sem-navegador`, python do `D:\veo\venv`) | JSON com perfil/reels |
| Robô QUERO a seco | `python tools\quero.py <conta> --seco --maquina <maq>` | `N atendido(s)` |
| Google Fotos | `python -m services.google_photos.fotos_http <perfil> "termo" 3 --maquina <maq>` | `N itens` (sem "pediu login") |
| Reel real | rodada normal do Instagram Auto (`postar_insta_auto.py`) | `instagram_auto.log`: `<conta>: HTTP no <maq>: ok` e em `maquina_remota.log` `Reel por HTTP (<conta>) -> https://www.instagram.com/reel/...` |
| Veo por HTTP | próxima geração do cron, ou `python tools\teste_flow_2fases.py <maq> <perfil> saida.mp4` (gasta 20 créditos) | `maquina_remota.log`: `Flow por HTTP video-pedir … chrome=~40 s` e `… 2ª fase … ok`; `VEZ SOLTA em ~60 s` |

Uma prova que **não** precisa do ssh ficar estável (caso desktop): copie
`prova_desktop_local.py` + `prova_prompt.txt` para `C:\postador-worker\nsn\saida\` e rode **na máquina**
`C:\postador-worker\nsn\venv\Scripts\python.exe C:\postador-worker\nsn\saida\prova_desktop_local.py`
(abre o Chrome do perfil, gera 1 imagem do Flow por HTTP, fecha, grava `prova_desktop.log` ao lado).

## 7. Desktop: onde parou em 29/10 e o que falta

Feito: chrome_conta (passo 2), venv + Pillow (3a), worker completo (3b, "nsn ok 0 cookies"), contas logadas pela dona
(`netbooks_logins.json` lista o desktop em ~50 perfis). Script de prova já copiado para `C:\postador-worker\nsn\saida\`.

Falta, nesta ordem:
1. **ssh estável.** O `sshd` do desktop derruba quase toda conexão (`Read from remote host: Connection reset by peer`),
   mesmo depois de `Restart-Service sshd`. Ping e porta 22 respondem. Olhar **na máquina**: Visualizador de Eventos
   → Aplicativos e Serviços → OpenSSH → Operational; `C:\ProgramData\ssh\sshd_config` (MaxStartups/MaxSessions estão
   no padrão); antivírus/firewall matando a sessão; Tailscale reiniciando. Teste: 20 vezes
   `ssh -o BatchMode=yes desktop "echo OK"` seguidas têm de passar todas.
2. Rodar a prova local (passo 6, último parágrafo) e ler `prova_desktop.log`: `FIM: png=... chrome_aberto≈40 s`.
3. `python bin\maquina_remota.py colher-flow <perfil> desktop` para 1 conta e `saude-flow desktop` para ver vivo.
4. Colheita do Instagram: `tools\colher_notebooks.py desktop` (o script padrão não inclui o desktop na lista fixa;
   passar o nome).
5. A partir daí o desktop entra sozinho: ele é a 1ª máquina da ordem (`ORDEM_NAVEGADOR`), fora dos horários da câmera.

## 8. Pega-ratão (o que já deu errado e como se vê)

| Sintoma | Causa | Como resolver |
|---|---|---|
| `nsn <maq>: … ModuleNotFoundError: PIL` | venv sem Pillow | `venv\Scripts\python.exe -m pip install pillow` e `instalar-nsn` |
| Saída vazia de comando no Windows | shell é PowerShell e o comando era `cd /d … &&` | usar `powershell -NoProfile -Command` ou caminho completo do script (`Remoto._nsn_script`) |
| "postado" sem postar (29/10 18:38–18:53) | o leitor aceitava a frase `reel ok:` vinda de um traceback | corrigido: só URL real conta; se voltar, ver `maquina_remota.log` |
| `Connection reset by peer` | sshd da máquina (desktop) | passo 7.1; nunca insistir em loop curto (piora) |
| `nsn_tem_cookie` False mesmo logada | cookie ainda não colhido lá | passo 5 |
| Flow `UNUSUAL_ACTIVITY` / recusa | token do reCAPTCHA reaproveitado ou conta marcada | 1 token por pedido (já é assim); conta em `contas.SEM_HTTP` se repetir |
| `Flow pediu login` | perfil Google deslogado na máquina | `logar <perfil> <maq>` (dona) |
| Instagram `1357031 conteúdo não disponível` na leitura | conta restrita/checkpoint (jornalcomia 29/10) | abrir o Instagram na conta e resolver o aviso; postar ainda funciona |

## 9. Interruptores

- Veo/Flow por HTTP nas máquinas: `D:\veo\beta\config.py` `FLOW_HTTP_REMOTO` (env `FLOW_HTTP_REMOTO=0` desliga);
  por conta `contas.SEM_HTTP`; `FLOW_HTTP_FECHAR_CHROME=0` mantém o Chrome aberto (diagnóstico).
- Reel por HTTP: `instagram.postar_http` em `config\reuso_plataformas.json` (reuso); por conta `"sem_http": true`.
- Ordem das máquinas: `ORDEM_NAVEGADOR` em `maquina_remota.py` (desktop → x200ma → acer → pc2 → PC1).
