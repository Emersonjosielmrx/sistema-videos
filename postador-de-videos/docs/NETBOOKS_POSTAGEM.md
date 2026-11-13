# Notebooks postando: passo a passo (logar as contas uma por uma)

> Para qualquer agente, inclusive um modelo mais simples, fazer **junto com a dona**. Escrito em 22/10/2026.
> Rode os comandos no PC1, na pasta `D:\postador-de-videos`.

## O que é

Os dois notebooks da dona também postam:

| Nome | Acesso | Máquina | Chrome |
|---|---|---|---|
| `x200ma` | `ssh emerson@100.87.195.108` | Celeron, 1,8 GB | já tem |
| `acer` | `ssh emerson-ia@100.98.55.125` | Atom, 2 GB (é o telão principal) | **falta instalar** (passo 0) |

- Nos notebooks roda **só o Chrome** da conta, **uma conta por vez em cada um**.
- Quem decide o que postar, o horário e os limites continua sendo o PC1. O PC1 manda o vídeo e comanda o Chrome de lá.
- Uma conta logada **nos dois** notebooks usa o que estiver **livre**. Se os dois estiverem ocupados ou desligados,
  o PC1 posta sozinho, como antes. Nada fica sem postar.
- **Perfil** = a parte do e-mail antes do `@` (ex.: `emersonjosiel2032`). Um login Google serve para tudo daquele
  e-mail: **YouTube** (postar e as conferências do Studio), **TikTok** ("Continuar com Google") e **Flow/Veo**.
- Perfis que começam com `ig_` são do **Instagram** (login do próprio Instagram, não do Google).
- O que passa a usar os notebooks depois do `ativar`: postagem do YouTube (rede e recap de parceiros), conferências do
  Studio (`youtube_studio_extras.py`), TikTok automático, Instagram automático e geração no Flow (`D:\veo\beta\flow_bot.py`).

## Regras (não quebre)

1. **Nunca digite senha** e nunca peça a senha à dona: quem entra na conta é ela, **na tela do notebook**.
2. **Nunca copie cookies ou pastas de perfil** de um PC para outro. Chega deslogado e o Google pode bloquear a conta.
3. O passo 0 (instalar o Chrome no Acer) **só com a dona autorizando** naquela conversa.
4. Um e-mail por vez: só passe para o próximo depois do `ativar` dizer `ATIVADO`.
5. Não apague nada em `~/postador-worker/perfis/` nos notebooks: ali estão os logins.

## Passo 0 (uma vez só): Chrome no Acer

Peça à dona: *"Posso baixar o Chrome oficial do Google (~110 MB) no Acer?"*. Só com um **sim**:

```
python bin\maquina_remota.py preparar-chrome acer --dona-autorizou
python bin\maquina_remota.py estado
```

Deu certo se no `estado` o `acer` mostrar `"chrome": "...chrome"` (e não `null`). Sem o Acer, tudo funciona só com o
X200MA.

## Login em lote — O PADRÃO (desde 26/10): várias janelas, fecha e abre sozinho

Dona 26/10: "deixe documentado pra sempre usarmos esse tipo de login sequencial, é muito mais rápido". No PC2 foram
~50 contas em ~1 h (uma por uma levava ~5 min cada). Vale para PC2 e notebooks:
```
python bin\netbooks\login_em_lote.py pc2 10      # mantém 10 janelas de login na tela até acabar a fila
python bin\netbooks\login_em_lote.py x200ma      # notebook (1,8 GB): 2 janelas + a conferência (padrão)
python bin\netbooks\login_em_lote.py pc2 estado  # feitas, na tela, puladas, não logaram
```
Antes e durante (dona 26/10, "sempre"):
- **Fecha o que não precisa e limpa a RAM** antes de cada janela (`chrome_conta.py liberar`): notebooks = bandeja/
  atualização + cache do disco; Windows = apps de bandeja (OneDrive, Teams, Phone Link, Widgets...) + enxuga a memória
  de todos os processos. Nunca toca em python/pythonw. Notebook sem RAM pra mais uma: espera uma fechar.
- **Telão/painel de métricas fora da tela** enquanto loga: notebooks pela vez da máquina (o player fecha); PC2 pelo
  `C:\vitrine\login.txt` (o `telao_win.py` fecha e volta sozinho quando o arquivo sai).
- **Som mudo** durante os logins; no fim volta como estava.
- CCleaner do PC2 desativado de vez (26/10: serviço CCleaner7 desabilitado + 7 tarefas desabilitadas, não desinstalado).
- Cada janela abre **sem porta de controle**, no perfil da conta, com o **e-mail já no campo**; depois do login vai pro
  YouTube. A dona só faz captcha/senha/código, em qualquer ordem, em quantas janelas quiser.
- Um vigia na sessão da tela lê o título das janelas: chegou no **YouTube** = logada → fecha pela janela (grava os
  cookies), **abre a próxima na hora** e confere a conta pela própria rede (Google + canal) no meio do caminho.
- Conta com erro: a dona **fecha a janela**; ela é conferida uma vez e, sem login, fica em "não logaram" (não reabre).
  Para pular de vez: pôr o perfil em `puladas` no `config\login_em_lote_<maquina>.json`.
- Enquanto roda, segura a vez da máquina ("login google lote (dona)"): o login do TikTok e o telão esperam.
- O painel/telão cobre a tela do PC2: o script traz as janelas pra frente sozinho (tarefa `PostadorFrente`).
- Coisas do PC2 que o script já contorna: cmdlets de tarefa do PowerShell quebrados ("Classe inválida") → `schtasks
  /it` + `.bat`; janela aberta pelo ssh não aparece na tela → tudo que mexe em janela roda por tarefa na sessão da tela.
- Notebooks Linux: os títulos das janelas são lidos com `xprop` (`chrome_conta.py janelas`), abertura/fechamento com
  `login_janela`/`fechar_janela` (SIGTERM grava os cookies). Testado no Acer 26/10 (abriu → "YouTube" → fechou).

### Script que roda NA PRÓPRIA máquina — o padrão quando dá (dona 26/10)
"Mandando o script de uma vez fica muito mais rápido, isso deve ser padrão." Uma conexão ssh manda o script e cria a
tarefa na sessão da tela (`schtasks /it`); dali em diante ele roda lá sozinho, mesmo que o ssh caia (o desktop vivia
derrubando a sessão). Prontos em `bin\netbooks\`:
- `login_desktop_local.ps1` — Google, 5 janelas; título "YouTube" = logada (fecha e abre a próxima).
- `tiktok_desktop_local.ps1` — TikTok, 5 janelas na página de login (a dona faz "Continuar com Google"); porta CDP local
  em cada uma, a página saiu do `/login` sem popup do Google aberto = logada.
Resultado em `C:\postador-worker\login_feitas.txt` / `tiktok_feitas.txt` (e `*_falhas.txt`); rodar de novo continua.
Depois, a conferência pela própria rede vem do PC1 (`conferir_logins`), quando o ssh estiver firme.

## Jeito antigo (23/10): a fila da dona, uma por vez

`bin\netbooks\logar_lista.py` tem a lista da dona na ordem dela. Um comando por conta:
```
python bin\netbooks\logar_lista.py seguinte   # confere+ativa a conta da vez e abre a PRÓXIMA com o e-mail já digitado
python bin\netbooks\logar_lista.py estado     # quantas foram, qual é a da vez
python bin\netbooks\logar_lista.py abrir      # reabre a da vez (janela fechou/travou)
python bin\netbooks\logar_lista.py pular      # deixa a da vez pra depois
```
O e-mail é digitado pela porta de controle (`email_login.py`) e o Google aceitou assim. A dona faz a verificação "não sou
um robô", a senha e o código. Desktop: fora da fila até o OpenSSH dele ser atualizado (o 7.7 derruba o ssh); a dona
loga lá à mão (`desktop_login.py` só funciona com o ssh estável).

## O ciclo (repita para cada e-mail)

**1. Qual é o próximo?**
```
python bin\maquina_remota.py proxima
```
Mostra o perfil, o e-mail e os canais. Os canais do recap de parceiros, prioridade da dona, vêm primeiro.

**2. Abrir o Chrome nos dois notebooks ao mesmo tempo**
```
python bin\maquina_remota.py logar <perfil>
```
Diga à dona: *"Abri o Chrome nos notebooks. Em cada um: entre na conta `<e-mail>`. Depois abra tiktok.com, clique em
Entrar e em 'Continuar com Google'. Feche a janela quando terminar."*
Se ela só quiser um notebook: `python bin\maquina_remota.py logar <perfil> x200ma`.

**3. Esperar a dona dizer que terminou e fechou as janelas.** Então:
```
python bin\maquina_remota.py ativar <perfil>
```
O `ativar` abre a conta em cada notebook, só **olha** se o YouTube Studio e o TikTok abrem logados e liga o que estiver
logado. Respostas:
- `ATIVADO:` e a lista dos canais e notebooks: pronto, volte ao passo 1.
- `NÃO ATIVOU`: o login não pegou. Volte ao passo 2 com o mesmo perfil.

**4. Para ver como está tudo:**
```
python bin\maquina_remota.py contas
```
A coluna LOGADO mostra `x200ma:S/S` (YouTube sim / TikTok sim); `-` é não. A coluna ATIVO mostra onde já posta.

## Se algo der errado

| Mensagem | O que fazer |
|---|---|
| `não respondeu` | notebook desligado ou fora da Tailscale: peça à dona para ligar. O PC1 segue postando. |
| `OCUPADO por <perfil>` | aquele notebook está postando agora. Espere uns minutos e repita. |
| `POUCA_RAM` | notebook sem memória livre: peça à dona para fechar programas abertos nele. |
| `SEM_CHROME` | é o Acer sem o passo 0. |
| a conta caiu depois de dias | `logar <perfil>` de novo, a dona entra, `ativar <perfil>`. |
| tirar uma conta dos notebooks | `python bin\maquina_remota.py desativar <perfil>` (volta a postar só pelo PC1). |
| mudou o `bin\netbooks\chrome_conta.py` | `python bin\maquina_remota.py instalar` (copia para os dois). |

## Ordem de tentativa (desde 23/10)

Regra da dona: conta logada nos notebooks usa eles; **deu erro num, tenta no outro; deu erro de novo (ou a conta não
existe lá), faz no PC1**. Vale para postagem no YouTube (`youtube_web_poster.py`), TikTok (`postar_tiktok_auto.py`),
Instagram (`postar_insta_auto.py`) e Flow/Veo imagem e vídeo (`D:\veo\beta\flow_bot.py`). Peça central:
`maquina_remota.tentativas()`. Notebook ocupado com outra conta = pula para o próximo na hora (não espera).
**Nunca reenvia depois do clique final** (YouTube: botão Agendar/Publicar; TikTok: "Post clicked"; Instagram:
"Compartilhar clicado"): aí o vídeo pode já estar no canal, e mandar de novo seria o mesmo vídeo duas vezes.
Limite diário e canal bloqueado também não trocam de máquina (são da conta). O Chrome da postagem abre FORA da tela
dos notebooks (o painel do telão continua); só a janela de login aparece.

## TikTok nos notebooks (sozinho, desde 23/10)

`bin\netbooks\tiktok_notebooks.py` (sub-vigia `tiktok_notebooks`, a cada 20 min a partir das 7h): pega 1 conta por vez
que já tem o Google logado no notebook e ainda não o TikTok, só com o notebook LIVRE. Abre na tela, zoom 0,7, rola até
"Continuar com Google", clica e escolhe a conta. Logou = liga o TikTok da conta naquele notebook. Pediu o **código do
e-mail** = deixa a janela na tela com o Gmail ao lado e avisa no Telegram (**o código é a dona quem digita**). O Google
abriria cadastro novo = para sem criar nada. Contas só de TikTok vão primeiro. O TikTok às vezes mostra "Abrir
xdg-open?" (quer abrir um app): clicar **Cancelar**. Estado: `config\tiktok_notebooks.json`; fila: `--fila`.

## Like da dona no telão (desde 23/10)

Regra da dona: like **só de UMA conta, a pessoal dela**, no **Acer**, nos vídeos que o telão já toca. O Acer toca no
Chrome (perfil `~/vitrine/perfil_chrome`, porta de controle 9470 só local); quando um vídeo do YouTube começa, o player
anota em `~/vitrine/curtir.txt` e o PC1 (`vitrine.py curtir_no_telao`) clica "Gostei" pelo túnel, 1 vez por vídeo
(`D:\video-fila\estado\vitrine_curtidos.json`). Conta não logada = não faz nada. Para a dona entrar com a conta pessoal
(1 vez): `python D:\video-fila\vitrine.py --logar-telao` e depois `--retomar-telao`. O antigo "curtir" do
`extras_rede.py` (curtia com o próprio canal em TODOS os canais da rede) foi DESLIGADO.

## Vigia mútuo (Telegram)

PC1, Acer e X200MA conferem a cada 2 min, pela Tailscale, quem está online: PC1, PC2, Acer e X200MA (o desktop fica de
fora: ele desliga normalmente). Caiu por 6 min = "🔴 <máquina> SEM SINAL" no Telegram; voltou = "✅ VOLTOU". Só avisa a
primeira viva na ordem PC1 → X200MA → Acer (sem mensagem repetida). Os notebooks também avisam "PC1 (sistema de vídeos)"
quando o PC1 está ligado mas parou de mandar o painel há 15 min. Código: `D:\video-fila\vitrine\vigia_mutuo.py`
(nos notebooks em `~/vitrine/`, bot em `~/vitrine/telegram.json`, só do usuário).

## Login: a janela abre SEM a porta de controle

Com a porta de controle (CDP) ligada o Google recusa entrar ("este navegador pode não ser seguro"). Por isso o
`logar` abre o Chrome normal; o controle só liga depois, para postar, com o perfil já logado. Se a janela de login
ficar aberta, ela segura o notebook (marca "ocupado"): feche quando terminar.

## O telão (quando não está postando)

Os dois notebooks mostram um **painel girando**, no visual da Central de Vídeos, com quadros diferentes em cada um
(`TELAS` em `D:\video-fila\vitrine_painel.py`):
- **Acer:** saíram agora, próximos a abrir (horário grande), mil visualizações, novos inscritos, esperando você, Telegram.
- **X200MA:** hoje em números, bloqueios do Studio, Opus/Flow, mil visualizações, Telegram, próximos.
- **Pop-up** grande na hora de cada novo inscrito e de cada vídeo que passa de mil views.
- Botão **Abrir** toca o vídeo ali mesmo; botão **Ver** (em "Esperando você") traz o vídeo do PC1 e toca. Aprovar continua
  pelo Telegram.
- **PC1 SEM SINAL** em vermelho = o PC1 parou de mandar dados há 12 min (travou, desligou ou ficou sem internet).
- **Vídeo só toca no Acer** (dono 22/10 23:50). O X200MA só mostra o painel; os botões dele mandam o vídeo pro Acer.
- No Acer, quando sai vídeo novo, o painel fecha, o vídeo toca e o painel volta. Postando, o painel fecha para sobrar memória.
- Existia também um `~/visualizador` (serviço `visualizador.service` + tarefa `VisualizadorX200` no PC1), de outra
  sessão, que abria cada vídeo no X200MA e não fechava: **desligado em 22/10 23:48** (pausado, serviço e tarefa
  desativados, nada apagado). Não religar sem a dona pedir.
- Arquivos: página `D:\video-fila\vitrine\painel.html`, player `D:\video-fila\vitrine\player.py`, dados
  `D:\video-fila\vitrine_painel.py`, envio `D:\video-fila\vitrine.py` (mudou algum? `python D:\video-fila\vitrine.py --instalar`).

## Onde fica cada coisa (para quem for mexer no código)

- PC1: `bin\maquina_remota.py` (comandos acima e a classe `Remoto`, que abre o túnel ssh e manda o arquivo).
- Notebooks: `~/postador-worker/chrome_conta.py` (fonte em `bin\netbooks\chrome_conta.py`), perfis em
  `~/postador-worker/perfis/`, vídeo de passagem em `~/postador-worker/entrada/` (apagado no fim), trava em
  `~/postador-worker/ocupado`, registro em `~/postador-worker/chrome.log`.
- Ativação: o campo `"maquina": ["x200ma", "acer"]` + `"perfil_remoto"` em `config\youtube_navegador.json`
  (canal) e `config\reuso_plataformas.json` (conta do TikTok). Quem conferiu e quando: `config\netbooks_logins.json`.
- Quem usa: `bin\youtube_web_poster.py` (rede e recap de parceiros) e `bin\postar_tiktok_auto.py`. O
  `D:\recapd-ambientes\producao\bin\parceiro_diario.py` não espera a fila do PC1 quando o canal está nos notebooks.
- O telão (`D:\video-fila\vitrine`) não exibe vídeo no notebook que estiver postando.
- Registro dos envios: `logs\maquina_remota.log`.

## Login do TikTok nos notebooks (atualizado 23/10/2026)
**Como funciona:** o TikTok entra pelo **"Continuar com Google"**, usando o Google que JÁ está logado no Chrome daquela conta, no próprio notebook. **Nunca** copiar cookies de uma máquina para outra (regra da dona; o TikTok pode derrubar as duas sessões).

**Quem faz:** `bin\netbooks\tiktok_notebooks.py`, chamado pelo vigia geral a cada 20 min, das 7h em diante.
- A cada rodada, passa conta por conta enquanto houver notebook livre, até 17 min. Notebook com 2 erros seguidos sai da rodada.
- **Fila:** perfis com Google logado no notebook e TikTok ainda não (`netbooks_logins.json`). As contas só de TikTok vão primeiro. Ver a fila: `python bin\netbooks\tiktok_notebooks.py --fila`.
- **Resultados** (`config\tiktok_notebooks.json` e `logs\maquina_remota.log`):
  - `logado`: liga o TikTok da conta naquele notebook (`reuso_plataformas.json`, campo "maquina").
  - `codigo`: o TikTok pediu código por e-mail. A janela fica NA TELA com o Gmail ao lado e chega aviso no Telegram; a dona digita o código. Tenta de novo em 1 h.
  - `captcha`: "não sou um robô" do Google. Janela na tela e aviso no Telegram; quem resolve é a dona. Tenta de novo em 1 h.
  - `nao_logou`: grava print em `logs\tiktok_nb_<perfil>_<notebook>.png`. Tenta de novo em 6 h.
  - `sem_conta`: o Google abriria conta NOVA no TikTok. Não cria nada e avisa.
  - `erro ...`: Chrome fechou no meio, conexão etc. Tenta de novo em 1 h.
- **Truques que já resolveram:**
  - O TikTok cria um iframe `bytedance://`, que trava a página com "Abrir xdg-open?". O script injeta `SEM_APP_JS` antes de carregar.
  - Tela pequena esconde o botão: zoom 0,7 e, se não achar, 0,5.
- **Conferir quem está logado de verdade:** `python bin\maquina_remota.py checar <perfil> [notebook]`. Ela exige o cookie `sessionid` do tiktok.com (desde 23/10; antes dava falso "logado").
- **Notebook ocupado** (login à mão, postagem, telão) gera os `TargetClosedError` e `connect_over_cdp` de 180 s: é só esperar a próxima rodada.
- **Senha nunca. Código, só a dona.**

### Fila única por notebook (23/10, dona: "o TikTok tem que ser como as outras coisas: entra na fila")
- O login do TikTok só usa um notebook livre, isto é:
  - sem a vez de outro (`maquina_remota.py vez`: Veo, login…);
  - sem Chrome aberto do chrome_conta;
  - sem vídeo tocando no telão (`~/vitrine/TOCANDO`, que o player marca enquanto toca).
- Enquanto roda, ele pega a vez ("login tiktok <perfil>", 15 min): o telão para (motivo "login") e o Veo e as postagens vão para outro lugar. Se pediu código ou captcha, segura a vez 45 min com a janela na tela para a dona; senão, solta na hora.
- Login à mão: `python bin\maquina_remota.py ocupar <notebook> "login manual" 30` e depois `liberar <notebook>`.

## Máquina nova (PC2, desktop...): sequência padrão (25/10/2026)
Foi o que se fez no x200ma e no Acer. Em outra máquina, seguir a mesma ordem, trocando o nome:
1. **Google/YouTube:** a dona loga o Google de cada conta (só a senha, uma vez): `python bin\netbooks\logar_lista.py` (fila em "Jeito rápido", acima).
2. **TikTok** ("Continuar com Google", sozinho): `python bin\netbooks\tiktok_notebooks.py --agora <maquina>`.
3. **Instagram** (usuário, senha `IG_SENHA` e código do e-mail, sozinho): `python bin\netbooks\instagram_notebooks.py <maquina>`. Se der captcha ("não sou um robô"), quem resolve é a dona.
4. **Conferência (obrigatória depois de toda rodada de login):** `python bin\netbooks\conferir_logins.py <maquina> [google|youtube|tiktok|instagram]`.
   - Abre cada conta marcada como logada naquela máquina e pede a prova à própria rede: Google = myaccount abre sem tela de login; YouTube = o Studio abre um `/channel/UC...`; TikTok e Instagram = a rede devolve o `@`.
   - A conta deslogada é desmarcada e volta para a fila de login. Se a rede não respondeu, a marca fica como está.
   - Espera a máquina ficar livre e pega a vez ("conferir logins <perfil>").
   - Resultado: resumo no fim (logadas, DESLOGADAS, sem resposta, por rede), `logs\conferencia_<maquina>.json`, uma linha por conta no `logs\maquina_remota.log` e prints em `logs\tiktok_tela\<maquina>_<perfil>_<hora>_conferir_<rede>.png`.
   - **Não conferir a mesma máquina com dois scripts ao mesmo tempo:** um rouba a vez do outro.
5. Login conferido prova a sessão, não a postagem. A prova de que posta é um post de verdade (`logs\tiktok_auto.log`, linha "pelo Chrome do <maquina>" seguida de "OK #").

## 29/10 — Instagram por HTTP nos notebooks (sem Chrome)

Cada notebook tem em `~/postador-worker/nsn` o worker do projeto-navegador-sem-navegador, com os cookies DELE em
`nsn/cookies/` (colhidos do Chrome dele; nunca copiados). O PC1 manda o vídeo e o comando por ssh; o Reel sai por HTTP
sem abrir Chrome e sem ocupar a vez da máquina. Atualizar o código: `python bin\maquina_remota.py instalar-nsn`.
Conferir cookies: `ssh x200ma "ls ~/postador-worker/nsn/cookies"`. Cookie vencido = o Chrome de lá posta e recolhe.
