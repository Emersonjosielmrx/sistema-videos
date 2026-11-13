# Como um agente acessa as 3 VPS — sem senha e sem credencial no chat

**Em uma frase:** neste computador o acesso já está pronto por chave. O agente só digita `ssh` e o apelido da máquina.
Não existe senha para passar, e nenhuma credencial deve ir para o chat.

> Para a dona copiar e colar para o outro agente:
> **"Leia `D:\ACESSO_VPS_PARA_AGENTES.md`. Você entra nas VPS com `ssh hermes-prod`, `ssh hermes-staging` ou
> `ssh hermes-bloqueio`. A chave já está configurada neste PC: não precisa de senha nem de credencial no chat."**

---

## 1. As 3 máquinas

| apelido (o que se digita) | endereço | o que roda lá |
|---|---|---|
| `hermes-prod` | 62.171.128.241 | **PRODUÇÃO.** Hermes Call (`/opt/hermes-call`, serviço `hermes-call`), Lucrativa / Assist-IA — o projeto do trader, com dinheiro real (`/opt/lucrativa`, serviço `lucrativa`), Atlas (`/opt/atlas`), Postgres, Traefik |
| `hermes-staging` | 209.145.60.53 | **TESTE do Hermes** (bancada e ensaio de publicação). É "a 209" |
| `hermes-bloqueio` | 157.173.207.22 | **Roteador de IA** (OmniRoute, porta 20128 — os agentes do VS Code passam por aqui), proxies, Atlas (`/opt/atlas`, a máquina "v157"), app de bloqueio do Hermes. É "a 157" |

Todas entram como `root`, pela mesma chave. Os apelidos estão em `C:\Users\Haylla\.ssh\config`.

## 2. Como usar

Um comando e sai (o jeito recomendado):

```bash
ssh hermes-prod "hostname; uptime"
```

Funciona igual no Git Bash, no PowerShell e no cmd. Para conferir se o acesso está vivo sem ficar esperando senha:

```bash
ssh -o BatchMode=yes -o ConnectTimeout=10 hermes-prod "hostname"
```

Resposta esperada: `opus-vps1` na produção e `meuservidor1` na 157 (conferido em 08/10/2026; a 209 não foi testada
nesta conferência — ver a regra 6).

**Só funciona de um agente que roda NESTE computador, no usuário da dona.** Agente na nuvem não tem a chave e não deve
ter: ele lê e muda código, mas não entra em VPS.

## 3. Atalhos de cada projeto (use estes em vez de `ssh` direto, quando existirem)

**Projeto do trader** (`D:\trader_binance\trader_binance`, regras no `AGENTS.md` de lá):

```bash
D:/trader_binance/atlas/venv/Scripts/python.exe deploy/vps.py "tail -5 /opt/lucrativa/logs/grade.log"
```

- `deploy\vps.py "comando"` — consulta, só leitura (usa o `hermes-prod`).
- `deploy\comparar_vps.py` — o que está diferente entre o PC e a VPS.
- `deploy\testar_na_vps.py` — testa numa cópia; `--publicar` publica. **Só publicar pelo script**, nunca copiando arquivo à mão.
- Este projeto usa **só** a `hermes-prod`. Nunca a 209.

**Projeto Hermes Call** (`D:\hermes\hermes-call` é o que está no ar; o trabalho novo fica em `D:\hermes\pc-base`; regras no
`CLAUDE.md` e no `CONTINUAR_DAQUI.md` de lá):
- `bash ops/status.sh` — o que está no ar.
- `bash ops/publicar-teste.sh` — ensaio na 209. `bash ops/publicar.sh` — produção. `bash ops/reverter.sh` — voltar.

## 4. Regras (valem para qualquer agente, em qualquer projeto)

1. **Nunca digitar, pedir ou testar senha.** O acesso é só por chave. Senha errada repetida faz o servidor bloquear o
   endereço deste computador na porta 22 (fail2ban) — já aconteceu e travou uma publicação.
2. **Não abrir, copiar nem colar o conteúdo dos arquivos de chave** (`C:\Users\Haylla\.ssh\id_*`). Não precisa: o `ssh`
   usa sozinho. Nem para "conferir".
3. **Leitura primeiro.** Olhar (`ls`, `tail`, `systemctl status`, `ps`) é livre. Mudar qualquer coisa em produção só pelo
   script do projeto e com o ok da dona.
4. **A produção é dividida.** Cada agente mexe só no que é do projeto dele: Hermes em `/opt/hermes-*` e no serviço
   `hermes-call`; trader em `/opt/lucrativa` e no serviço `lucrativa`; Atlas em `/opt/atlas`. Nunca reiniciar, parar ou
   "otimizar" o serviço do outro. O `lucrativa` opera dinheiro real.
5. **Segredos ficam na VPS.** Não copiar para o PC, para o chat nem para arquivo: `.env`, `10-segredos.conf`, chaves da
   Binance, tokens. Não imprimir esses arquivos no terminal.
6. **A 209 (`hermes-staging`) só serve ao Hermes.** O guia do Atlas registra que ela já foi invadida: o projeto do trader
   não a usa para nada, e ninguém digita senha nela.
7. **Nada pesado na produção sem necessidade.** Ela faz ligações de voz e roda a grade do trader. Se o Hermes precisar do
   processador numa ligação, pede pausa à grade (ela larga a conta em ~2 s e volta sozinha):

```bash
ssh hermes-prod 'echo $(( $(date +%s) + 900 )) > /opt/lucrativa/estado/pausa_grade.txt'
```

```bash
ssh hermes-prod 'rm -f /opt/lucrativa/estado/pausa_grade.txt'
```

   O número é por quantos segundos (900 = 15 min; no máximo 30 min por pedido). **Não matar nem congelar o processo da grade.**
8. **Horários em que não se reinicia o `lucrativa`** (Brasília): perto de :01 das 01, 05, 09, 13, 17 e 21 h, e das 21:00
   às 23:00.

## 5. Se der erro

| o que aparece | o que é | o que fazer |
|---|---|---|
| `Permission denied (publickey)` | este usuário/computador não tem a chave | parar e avisar a dona. Não tentar senha |
| fica parado e dá `timed out` na porta 22, mas o site está no ar | o endereço deste PC foi bloqueado pelo fail2ban | esperar o bloqueio vencer ou avisar a dona. Não insistir |
| `Host key verification failed` / aviso de que a identidade da máquina mudou | a máquina foi trocada ou há algo errado | **não aceitar às cegas**; avisar a dona |
| pede senha | a chave não foi usada | cancelar (Ctrl+C) e avisar a dona |

---
*Escrito em 08/10/2026. Este arquivo não tem (e não deve ter) senha, chave ou token. Se uma máquina mudar de endereço,
corrija aqui e em `C:\Users\Haylla\.ssh\config`.*
