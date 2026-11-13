# Backup de todas as VPS no Google Drive

Pedido da dona em 05/10/2026: guardar fora das máquinas não só o Hermes, mas **tudo o que roda nas três VPS**,
incluindo os fluxos do n8n. Arquivos em `ops/vps/backup-todas/`.

## O que existe

| Backup | Quem faz | Quando | Onde fica no Drive |
|---|---|---|---|
| **Hermes Call** (bancos `wacalls_*`, gravações, uploads) | `hermes-backup.sh` (já existia) | todo dia 03:30 | `hermes-call-backup/` |
| **Todas as VPS** (o resto da produção, a de teste 209 e a 157) | `backup-vps.sh` (novo) | todo dia 04:30 | `backup-vps/<vps>/` |

Dentro de `backup-vps/<vps>/` (`producao`, `teste`, `vps157`):

- `diario/<AAAA-MM-DD>/` — todo dia:
  - `pg.<contêiner>.sql.gz`: **todos os bancos** de cada Postgres (pg_dumpall). Na 157 é onde está o Chatwoot.
  - `n8n.<contêiner>.tgz`: `fluxos.jsonl` (**um fluxo por linha**: nome, nós, ligações), `credenciais.jsonl`
    (cifradas), `CHAVE_DE_CRIPTOGRAFIA.txt` (sem ela as credenciais não abrem em outra instalação) e um `LEIA-ME.txt`.
    Sai **direto do banco do n8n, só leitura**: nada roda dentro do n8n (ver "O que deu errado na 1ª cópia").
  - `sistema.tgz`: crons, a definição de cada serviço e stack do docker (com as variáveis), traefik, firewall, portas.
  - `MANIFESTO.txt`: o que foi guardado, tamanho, tempo e o que falhou.
- `semanal/<AAAA-MM-DD>/` — no domingo (e na primeira vez): `vol.<volume>.tgz` (volumes do docker, menos bancos
  e caches) e `dir.<pasta>.tgz` (pastas de projeto em `/opt`, `/root`, `/home`, `/srv`, `/var/www`).

Ficam **7 diários e 4 semanais** por VPS. Falhou algum item: aviso no Telegram e o resto continua.

Em 05/10 isso dava, por semana: teste 209 ~25 GB (93 itens; MinIO sozinho 6,6 GB), 157 ~12 GB, produção ~8 GB.
**Fica de fora** o que passa de 8 GB num item só (hoje: `/opt/omniroute` da 157, 10 GB) — aparece como `FORA` no
manifesto. Também não entram caches, `node_modules`, `.git`, logs e o que o backup do Hermes já guarda.

## Como é seguro

A autorização do Google Drive existe **só na produção**. A VPS de teste já foi invadida uma vez (conta `duc`): se a
autorização morasse lá, quem entrasse leria e apagaria todos os backups. Por isso as outras VPS não mandam nada:
a produção entra nelas por SSH com uma chave que **só roda o exportador** (`command=` no `authorized_keys`, sem
terminal, sem túnel, e só aceita vinda do endereço da produção). O exportador só entrega itens da própria lista.
Cada item é gravado num arquivo temporário na produção (`/var/tmp/backup-vps`, um por vez, apagado em seguida) e
enviado com novas tentativas; se não houver espaço para o item mais 3 GB de folga, ele falha em vez de encher o disco.

Os pacotes vão **sem criptografia própria** para o Drive: têm dados de clientes e senhas de serviços (as variáveis do
docker em `sistema.tgz`, a chave do n8n). A proteção é a conta do Google: verificação em duas etapas ligada.

## Ligar (a dona roda, no PowerShell do PC; é chave SSH e agendamento)

```
ssh hermes-prod "/opt/hermes-call/ops/backup-vps.sh chave-publica" | ssh hermes-staging "bash /root/vps-backup-instalar.sh"
ssh hermes-prod "/opt/hermes-call/ops/backup-vps.sh chave-publica" | ssh hermes-bloqueio "bash /root/vps-backup-instalar.sh"
ssh -t hermes-prod /opt/hermes-call/ops/backup-vps.sh instalar
```

O terceiro confere o acesso, agenda as 04:30 e dispara na hora uma primeira cópia **só do diário e devagar** (para
não disputar rede com as ligações). Os volumes e pastas vão sozinhos na madrugada seguinte.

Acompanhar: `ssh hermes-prod /opt/hermes-call/ops/backup-vps.sh estado`.
Desfazer numa VPS de origem: `bash /root/vps-backup-instalar.sh remover`. Na produção:
`systemctl disable --now hermes-backup-vps.timer`.

## Recuperar

Tudo a partir da produção (é onde o `rclone` está). Troque `<vps>`, a data e os nomes.

- **Ver o que há:** `rclone lsf -R hermes-drive:backup-vps/<vps>/diario/2026-10-06/`
- **Um fluxo do n8n:** `rclone copy hermes-drive:backup-vps/vps157/diario/<data>/n8n.n8n_editor2_n8n_editor2.tgz /tmp/`
  → `tar -xzf` → `grep -m1 '"name":"NOME DO FLUXO"' fluxos.jsonl > fluxo.json` → no n8n: *Import from file*.
- **O n8n inteiro noutra máquina:** recuperar o `pg.*.sql.gz` do Postgres do n8n (banco `n8n_queue`: tem fluxos,
  credenciais e histórico de execuções) e subir o n8n com `N8N_ENCRYPTION_KEY` igual ao `CHAVE_DE_CRIPTOGRAFIA.txt`.
- **Um Postgres:** `rclone cat hermes-drive:backup-vps/<vps>/diario/<data>/pg.<contêiner>.sql.gz | gunzip | docker exec -i <contêiner novo> psql -U postgres`
  (é um pg_dumpall: recria usuários e todos os bancos; use num Postgres vazio).
- **Um volume:** criar o volume, e `rclone cat …/semanal/<data>/vol.<nome>.tgz | tar -xz -C /var/lib/docker/volumes/<nome>/_data`.
- **Uma pasta:** `rclone cat …/semanal/<data>/dir.opt__cas.tgz | tar -xz -C /opt` (o `__` do nome é a barra do caminho).
- **Como estava montado:** `sistema.tgz` → `docker/servicos/<serviço>.json` tem imagem, variáveis, volumes e portas.

## O que deu errado na 1ª cópia (05/10 21:35) e o que mudou

1. **O editor do n8n da 157 caiu e reiniciou sozinho** (~21:45, saída 134). A cópia exportava os fluxos rodando
   `n8n export:workflow` dentro do contêiner do editor, um segundo processo pesado na mesma memória. **Agora nada
   roda dentro do n8n:** os fluxos são lidos do Postgres dele. Regra para qualquer item novo: backup só lê; não
   executa nada dentro do serviço que está guardando.
2. **Quase todo envio falhou com `rateLimitExceeded` do Google.** O envio era em fluxo (`rclone rcat`), que não dá
   para repetir. Agora é arquivo temporário + `rclone copyto` com poucas requisições por segundo e muitas tentativas.
   Se voltar a acontecer com frequência: criar um "client ID" próprio do Google para o rclone (hoje usa o
   compartilhado do rclone, que é disputado).
3. **Pastas e volumes permitidos eram recusados** (`pasta não permitida`): `lista | grep -q` com `pipefail` dá erro
   mesmo achando. Corrigido em todos os scripts que o agente escreveu. O ensaio de 05/10 não tinha exportado
   nenhuma pasta nem volume de verdade; em 06/10 foi exportado um item de cada tipo em cada VPS.
4. O aviso de falha **não chegou no Telegram**: falta `/etc/hermes-call/alertas.env` na produção (token e chat do
   bot de avisos). Sem isso, backup que falha só aparece no registro.

## Como está em 06/10

O agendamento das 04:30 **ainda não está ligado**: depende de a dona rodar `ops\LIGAR-BACKUP-TODAS-VPS.bat` (cria a
chave de backup e o agendamento; o agente não faz alteração de segurança em servidor). Enquanto isso o agente fez
**cópias avulsas** em 06/10 de manhã, com o acesso que o PC já tem: os itens diários da 209 e da 157 passaram pelo
PC (`backup-vps.sh receber`) e os da produção rodaram lá mesmo. Volumes e pastas da 209 e da 157 (~37 GB) **não**
foram copiados: pela internet do PC levaria muitas horas; ficam para o agendamento.

## O que foi testado e o que não foi

Testado: a lista nas três VPS; em 06/10, a exportação de verdade de um item de cada tipo em cada VPS (sistema,
pasta, volume, Postgres, n8n), com o pacote aberto na própria máquina; o envio (`receber`) com conferência de
tamanho e recusa de entrada vazia; os itens diários da 209 (6 de 6) e da 157 (3 de 3) no Drive.
**Recuperação a partir do Drive (06/10 12:05):** o pacote do n8n da 209 foi baixado e aberto: 909 fluxos em JSON
válido (163 ativos, 28.008 nós), 335 credenciais, chave de 32 caracteres; o dump `pg.hermes_call_v3_pg_v3` termina
com "PostgreSQL database cluster dump complete".
**Não testado:** a entrada por SSH com a chave nova (só existe depois de a dona ligar); os dois dumps de 1 GB não
foram abertos nem restaurados num Postgres; importar um fluxo de volta num n8n; volumes e pastas da 209 e da 157
nunca foram enviados.
