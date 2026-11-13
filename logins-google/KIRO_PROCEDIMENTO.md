# Kiro: conferir quais contas têm crédito, quais faltam criar e quais faltam conectar no OmniRoute

Procedimento usado em 23/10/2026 no PC1. Serve para repetir aqui e para fazer no **desktop** e no **PC2**.

## 0. Regras (sempre)
- **Senha nunca** é digitada pelo agente. Login de conta Google é a dona quem faz.
- **Conta nova no Kiro só a dona cria.** Quando o Google mostra "Fazer login no serviço kiro… / Continuar" (em inglês:
  "Google will allow kiro… to access"), é a 1ª vez daquela conta no Kiro: clicar em Continuar CRIA a conta. O script
  nunca clica: deixa a janela aberta para a dona.
- Na página da conta do Kiro existe **"Delete account"**: o script não clica em nada lá, só abre pelo endereço e lê.
- Cookies do site do Kiro: sempre **Decline**.
- Não entrar no Kiro com conta que não seja da dona.

## 1. Quantas contas Kiro estão no OmniRoute (VPS final 22, `ssh hermes-bloqueio`)
Só leitura:
```
ssh hermes-bloqueio "python3 /opt/omniroute/kiro_renovacao.py --simular"
```
Mostra `sem credito no mes=N ligadas com credito=M`. Total e as conectadas hoje:
```
ssh hermes-bloqueio "python3 -c \"import sqlite3; db=sqlite3.connect('file:/opt/omniroute/data/storage.sqlite?mode=ro', uri=True); print(db.execute(\\\"select count(*), sum(is_active) from provider_connections where provider='kiro'\\\").fetchone())\""
```
Limites conhecidos:
- O OmniRoute **não guarda o e-mail** das contas Kiro, e os tokens ficam criptografados (`enc:v1`). Não dá para saber
  pelo banco qual conta é qual.
- Dá só para comparar NÚMEROS: (contas novas conectadas hoje) × (contas que precisavam conectar).
- Dica: ao conectar uma conta no painel do OmniRoute, colocar o e-mail no nome/apelido da conexão (se houver campo).
  Assim dá para cruzar depois.
- Pelo gasto também não fecha na hora: o OmniRoute usa UMA conta por vez até acabar. Conta conectada pode ficar dias em
  "0 used / 50".

## 2. Conferir conta por conta (script `kiro_creditos.py`)
Funciona com as contas do **cofre** (`D:\logins-google\cofre\contas.json`, perfis de Chrome com porta de controle).
```
python D:\logins-google\kiro_creditos.py                 # todas as contas com Google vivo (≈1 min por conta)
python D:\logins-google\kiro_creditos.py conta1 conta2   # só essas
python D:\logins-google\kiro_creditos.py --fechar-todas  # confere sem deixar nenhuma janela aberta
python D:\logins-google\kiro_creditos.py --relatorio     # refaz a tabela KIRO_CREDITOS.md
```
Para cada conta, ele abre app.kiro.dev, clica em Decline (cookies), depois em "Google", escolhe a conta e lê em
`/settings/account` o plano, os créditos usados/limite e a data de renovação. Resultados possíveis:
- `usa_kiro`: lê os créditos. **Com saldo:** a janela fica aberta na tela. **Sem saldo:** fecha.
- `sem_kiro`: o Google pediu o "Continuar". A janela fica aberta parada ali, para a dona criar.
- `nao_entrou` e outros: a janela fica aberta.
- Se a RAM livre ficar abaixo de 3 GB, ele para de deixar janelas abertas e marca "abrir depois".

Saídas:
- `kiro_creditos.json`: última leitura por conta.
- `KIRO_CREDITOS.md`: tabela para ler.
- `kiro_prints\`: prints da página do plano.

## 3. Abrir as que precisam da dona
```
python D:\logins-google\kiro_creditos.py --abrir conta1 conta2    # janela NA TELA (sem Kiro: no "Continuar")
python D:\logins-google\kiro_creditos.py --fila                   # no máx. 5 por vez; a dona fecha uma, abre a próxima
python D:\logins-google\kiro_creditos.py --fila --so-sem-kiro     # a fila só com as que faltam CRIAR
```
Depois que a dona cria/conecta, rodar o passo 2 de novo nas mesmas contas. Quem passar a `usa_kiro` foi criada.

## 4. Contas que estão só no Chrome normal (fora do cofre)
- O script **não funciona** no Chrome normal: o Chrome bloqueia a porta de controle na pasta padrão `User Data`.
- Testado em 23/10: **copiar o perfil para o cofre não leva o login** (o Chrome prende os cookies à pasta de origem).
- Ver quais perfis do Chrome normal têm conta fora do cofre (só leitura do `Local State`):
  ```
  python -c "import json,os; ls=json.load(open(os.path.expandvars(r'%LOCALAPPDATA%\Google\Chrome\User Data\Local State'),encoding='utf-8')); c=set(json.load(open(r'D:\logins-google\cofre\contas.json',encoding='utf-8'))['contas']); [print(p,i.get('user_name')) for p,i in ls['profile']['info_cache'].items() if i.get('user_name') and i['user_name'].lower() not in c]"
  ```
- Abrir cada um no Chrome normal já na página de créditos, para a dona olhar (ela fecha as sem saldo e cria as que
  pedirem "Continuar"):
  ```
  "C:\Program Files\Google\Chrome\Application\chrome.exe" --profile-directory="Profile 39" --new-window https://app.kiro.dev/settings/account
  ```
- Para essas contas entrarem na conferência automática: a dona entra uma vez no cofre com
  `python D:\logins-google\cofre.py logar <email>`.

## 5. No desktop e no PC2 (a fazer)
- **PC2** (`ssh pc2`, Windows, shell cmd, Python 3.13): não tem o cofre. Opções:
  1. Usar só o passo 4 (perfis do Chrome normal de lá, abrindo a página de créditos).
  2. Copiar `cofre.py` e `kiro_creditos.py` para lá, e a dona logar as contas no cofre de lá.

  Lembrar que os cmdlets de tarefa agendada estão quebrados no PC2 (usar schtasks) e que o ssh pede
  `-o LogLevel=ERROR`.
- **Desktop** (`ssh desktop`): desde 24/10 o Windows de lá está SEM SENHA e o acesso é só por chave
  (`ssh -o BatchMode=yes desktop`, shell PowerShell; nunca usar senha). Testado 24/10: 30 perfis do Chrome lidos. Mesmas opções do PC2. Lá
  NÃO rodar nada com OBS aberto ou câmera/microfone em uso (regra da dona).
- Em cada máquina: listar as contas (passo 4), conferir, abrir as que faltam e, no fim, comparar o total do
  OmniRoute (passo 1).

## Registro de 23/10/2026 (PC1)
- **Cofre:** 58 contas com Google vivo; todas passaram a ter Kiro (as 8 últimas criadas pela dona às ~20h). Só a
  emersonjosiel1995 estava sem saldo.
- **OmniRoute:** de 91 contas Kiro (todas esgotadas) para 126; 35 conectadas no dia; 31 com saldo à noite. As
  esgotadas renovam em 31/10 / 1/11 (o `kiro_renovacao.py` religa sozinho).
- **Chrome normal:** 14 contas fora do cofre, abertas para a dona na página do Kiro:
  - emersonjosielmrx, volupecenografiaintegrada, daniel.automacaoia, hayllamikeycesouza, pauladvasconcelos3
  - chatscentralz, hootztech, evoogabriel, ulissesluciolaveriano, travelbds25
  - ameliablack.uk, leechardes.ia.1, felipeaguiar.ia.2, brunagesteira.ia

## Lista única (kiro_contas_unica.json)
Uma entrada por conta Google: em que máquina e perfil ela está (pc1_cofre, pc1_chrome, desktop_chrome, …) e a última situação no Kiro. O OmniRoute não mostra e-mail, então ESTA é a referência. Em 23/10 ela tinha 108 contas; as 22 do desktop ainda não vistas foram abertas no Chrome normal de lá (tarefa KiroAbrir, kiro_abrir.bat em C:\postador-worker).
