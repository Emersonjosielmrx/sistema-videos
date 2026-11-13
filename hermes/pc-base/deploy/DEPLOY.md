# Deploy & Versionamento — Hermes Call

Guia curto de build, release versionada (GitHub + Docker Hub), deploy na VPS e rollback.
**Sem segredos aqui.** As credenciais ficam em `deploy/.env.deploy` (ignorado pelo Git).

## Pré-requisitos

- Credenciais: copie o modelo e preencha:
  ```bash
  cp deploy/.env.deploy.example deploy/.env.deploy
  # edite deploy/.env.deploy com os tokens reais
  ```
- Node instalado (para os scripts `deploy/*.js`).
- Docker: **não roda no PC de dev**. O build de imagem acontece na VPS
  (`golang:1.26-bookworm` + Dockerfile). Rode os scripts que fazem `docker build`
  a partir da VPS, ou deixe o `deploy-beta.js` buildar remotamente via SSH.

## Versionamento

- Fonte da versão: arquivo **`VERSION`** na raiz (semântico, começa em `0.1.0`).
- O binário expõe em `GET /api/version`: `{ version, channel, build }`.
  - `channel = beta` enquanto a leva nova está em teste; `stable` após promover.
- Tags Git: `vX.Y.Z` (ex.: `v0.1.0`).
- Tags Docker Hub: `fabricadeautomacoesia/hermes-call:vX.Y.Z` + `:latest`.

### Cortar uma release (GitHub + Docker Hub)
```bash
# pré-lançamento pra validar (canal beta → tags :next + :beta; NÃO mexe em :latest)
node deploy/release.js --version 0.2.0-beta.1

# release estável (canal stable → tags :stable + :latest)
node deploy/release.js --version 0.2.0

# variações
node deploy/release.js --no-docker              # só tag Git
node deploy/release.js --no-git                 # só imagem Docker
node deploy/release.js --version 0.2.0 --channel beta   # força o canal
```
O `release.js` faz: `git tag vX.Y.Z[-beta.N]` + push pro GitHub, depois
`docker login` (via token do `.env.deploy`), `docker build` e `docker push` da
**stack de tags do canal**.

### Stack de tags no Docker Hub (o que cada uma significa)

| Tag | Move? | Aponta pra | Puxe quando quer… |
|---|---|---|---|
| `:vX.Y.Z` | ❌ | versão estável exata | fixar/rollback determinístico |
| `:vX.Y.Z-beta.N` | ❌ | pré-lançamento exato | fixar um beta específico |
| `:stable` | ✅ | última estável | produção |
| `:latest` | ✅ | **última estável** (nunca beta) | produção (default do pull) |
| `:next` / `:beta` | ✅ | próxima em validação | testar antes de promover |

- Release **estável** move `:stable` + `:latest`. Release **beta** move `:next` +
  `:beta` e **não toca em `:latest`** — produção fica intocada.
- Canal inferido do sufixo (`-beta`/`-rc`/`-alpha`) ou forçado com `--channel`.

```bash
docker pull fabricadeautomacoesia/hermes-call:latest   # produção estável
docker pull fabricadeautomacoesia/hermes-call:next     # próxima (beta), pra testar
docker pull fabricadeautomacoesia/hermes-call:v0.2.0   # versão exata (pin)
```

## Deploy na VPS (com rollback seguro)

O deploy roda como container Docker `hermes-call` (`--network host`, com áudio MLow).

```bash
# 1. Sobe a leva nova como BETA. Na PRIMEIRA vez, congela a imagem que já está
#    rodando como hermes-call:stable (ponto de restauração).
node deploy/deploy-beta.js

# 2. Valide em https://hermescall.opus-sem-limites.com.br
#    (o /api/version deve mostrar channel=beta).

# 3a. Se estiver bom: promove o beta a novo ponto estável.
node deploy/promote-stable.js

# 3b. Se der errado: volta pra imagem estável anterior (1 comando).
node deploy/rollback.js
```

### Como o rollback funciona
- `deploy-beta.js` builda `hermes-call:beta` e, antes disso, garante que exista
  `hermes-call:stable` (a última versão comprovadamente boa).
- `rollback.js` recria o container a partir de `hermes-call:stable`.
- `promote-stable.js` retagueia `:beta` → `:stable` (e guarda a anterior como
  `:stable-prev`), fixando o novo ponto de restauração.
- Migrations do banco são **aditivas** (`ADD COLUMN IF NOT EXISTS` /
  `CREATE TABLE IF NOT EXISTS`), então a versão estável continua lendo o banco
  normalmente após um rollback.

## Deploy legado (systemd, SEM áudio)

`deploy/deploy.js` compila via container Go e instala por systemd — **não** carrega
o codec MLow, então a ligação conecta mas não passa voz. Prefira `deploy-beta.js`.

## Como o deploy realmente funciona (leia antes de mexer)

`deploy-beta.js` **NÃO usa `git pull`** na VPS. Ele:
1. Conecta por **SSH (porta 22, senha)** usando a lib `ssh2` do Node.
2. Sobe as fontes por **SFTP** (dirs `cmd/ internal/ client/src client/public native/ passkey-extension/`
   + arquivos raiz) pra `/opt/hipercool-refactor` no servidor.
3. Roda `docker build` **na VPS** (compila MLow + client + Go) gerando `hermes-call:beta`.
4. Sobe o container a partir da `:beta`.

Ou seja: **o que sobe é o seu working tree local**, não o que está no GitHub. Fazer
`git push` é bom pra versionar/backup, mas **não alimenta o deploy** — quem alimenta é
o SFTP do `deploy-beta.js`. E como o build é `docker build` na VPS, **não precisa de Go
nem gcc no PC** (o PC só precisa de Node + acesso SSH).

## ⚠️ Como NÃO fazer (causa raiz de deploy travado — 2026-07-21)

**NUNCA fique testando senha de SSH em loop contra a VPS.** A VPS tem **fail2ban**: após
poucas tentativas de login SSH com senha errada, o **seu IP é BANIDO na porta 22** (via
DROP → conexão dá **timeout**, não "connection refused"). As portas do app (80/443/8080)
continuam abertas, então o site parece no ar, mas **o `deploy-beta.js` passa a dar
`ETIMEDOUT` na hora de conectar** — e parece que "o deploy quebrou".

Foi exatamente isso que travou o deploy nesta data (e provavelmente na véspera): um agente
tentou adivinhar a senha (senhas de outra VPS, `changeme`, etc.) em vez de ler a senha correta
em `deploy/.env.deploy` (`HERMES_VPS_PASS=<removido — ver cofre/VPS>`). Resultado: IP banido.

Regras pra não cair nisso:
- **A senha correta está em `deploy/.env.deploy`** (`HERMES_VPS_PASS`). Leia de lá. Não
  invente, não reaproveite a senha de OUTRA VPS (a `209.145.60.53` usa outra senha — é outra máquina, ver abaixo).
- **Não faça brute-force / retry de auth.** Se a 1ª conexão autenticar, ótimo. Se der
  `Authentication failed`, PARE e confira a senha no `.env.deploy` — não tente de novo
  às cegas.
- **Diagnóstico de "deploy dá ETIMEDOUT na porta 22":**
  ```bash
  # app está vivo? (se responder, o problema é SÓ o SSH, não a VPS)
  curl -s --max-time 8 http://62.171.128.241:8080/api/version
  # porta 22 abre por TCP? (1 teste só, NÃO em loop)
  timeout 8 bash -c 'echo > /dev/tcp/62.171.128.241/22' && echo ABERTA || echo "banido/timeout"
  ```
  Se o app responde mas a 22 dá timeout → **é ban de fail2ban no seu IP**, não é a VPS.
- **Como sair do ban:** (a) esperar o fail2ban expirar (tipicamente 10–60 min); (b) deployar
  de OUTRA máquina/IP que não esteja banido (ex.: o Mac ou o outro PC da rede); ou (c) pedir
  pra alguém com acesso ao servidor rodar `fail2ban-client set sshd unbanip <SEU_IP>` (o IP
  público sai de `curl -s https://api.ipify.org`). **Não** fique reconectando durante o ban —
  cada tentativa pode renovar/estender o bloqueio.

## VPS: prod vs staging (NÃO confundir — mesma senha-base, sufixos diferentes)

| | **Produção (Hermes Call)** | **Staging (outros projetos)** |
|---|---|---|
| IP | `62.171.128.241` | `209.145.60.53` |
| Senha root | <removido — ver cofre/VPS> (acesso só por chave: `ssh hermes-prod`) | <removido — ver cofre/VPS> |
| Deploy | `node deploy/deploy-beta.js` (Docker `--network host`) | Docker Swarm (`_deploy.py`) |
| Domínio | `hermescall.opus-sem-limites.com.br` | `hermescall.inovareinteligenciaartificial.com` |
| Fontes no servidor | `/opt/hipercool-refactor` | `/root/hermes-call` (Swarm) |

O Hermes Call **só** roda na `62.171.128.241`. A `209.145.60.53` é de outros projetos e
NÃO deve receber deploy do Hermes.

## Padrão de nomenclatura (OBRIGATÓRIO — leia antes de criar tag/imagem)

### Git tags

**Formato:** `vMAJOR.MINOR.PATCH` (semver estrito). Exemplos: `v0.3.7`, `v1.0.0`.

| Situação | Formato | Exemplo |
|---|---|---|
| Release estável | `vX.Y.Z` | `v0.3.7` |
| Pré-release / beta | `vX.Y.Z-beta.N` | `v0.4.0-beta.1` |
| Release candidate | `vX.Y.Z-rc.N` | `v1.0.0-rc.1` |
| Marco histórico (raro) | `vX.Y.Z-descricao` | `v0.2.0-ui-base` |

**PROIBIDO** — nunca crie tags assim:
- `VERSAO-BOA`, `versao-funciona`, `golden-source` (subjetivo, vira lixo)
- `backup-AAAA-MM-DD`, `checkpoint-XXX` (use branch ou snapshot, não tag)
- `pre-fix-algo`, `post-fix-algo` (efêmero, polui a lista)
- Qualquer tag sem o prefixo `v` e sem formato semver

**Quando criar tag:** só após `promote-stable.js` confirmar que a versão está rodando
em produção. Não crie tag em código não-deployado.

**Comando:**
```bash
# Atualize VERSION, depois:
git tag -a v0.4.0 -m "v0.4.0: resumo curto do que mudou"
git push origin v0.4.0
```

### Docker images (VPS)

Na VPS existem **apenas 3 tags em uso** — não crie outras:

| Tag | Propósito | Quem cria |
|---|---|---|
| `hermes-call:beta` | Build mais recente em validação | `deploy-beta.js` |
| `hermes-call:stable` | Versão comprovadamente boa (rollback target) | `promote-stable.js` |
| `hermes-call:stable-prev` | Penúltima estável (rede de segurança) | `promote-stable.js` |

**PROIBIDO** criar tags Docker manuais como:
- `hermes-call:latest` (ambíguo — era do deploy legado)
- `hermes-call:qa`, `hermes-call:test` (use `:beta` pra isso)
- `hermes-call:BASE-UNICA-AAAMMDD` (não existe mais)
- `hermes-call:stable-backup-AAAMMDD` (`:stable-prev` já cobre)
- Qualquer tag ad-hoc com nome descritivo

Se precisar de mais de 3 imagens ao mesmo tempo, algo está errado no fluxo.

**Limpeza periódica:** `node deploy/cleanup-docker.js` remove tudo exceto
`:beta`, `:stable` e `:stable-prev`.

### Docker Hub (releases publicadas)

Tags gerenciadas por `release.js` — nunca crie manualmente no Hub:

| Tag | Move? | Significado |
|---|---|---|
| `:vX.Y.Z` | Não | Versão exata (pin/rollback determinístico) |
| `:vX.Y.Z-beta.N` | Não | Pré-release exato |
| `:stable` / `:latest` | Sim | Última release estável |
| `:next` / `:beta` | Sim | Próxima em validação |

### Arquivo VERSION

Fonte única da versão. Fica na raiz do repo, formato `X.Y.Z` (sem `v`).

**Quando bumpar:**
- **PATCH** (0.3.5 → 0.3.6): correções, ajustes de UI, fixes de bug
- **MINOR** (0.3.x → 0.4.0): feature nova visível pro usuário
- **MAJOR** (0.x → 1.0.0): breaking change ou lançamento público

Bump o VERSION **antes** de rodar `deploy-beta.js` — o build injeta a versão no binário.

## Checklist de segurança

- `deploy/.env.deploy` **nunca** vai pro Git (conferido em `.gitignore`).
- Rotacione os PATs do Docker Hub periodicamente (Account Settings › Security).
- Não cole tokens em chat/PR/issue.
- **Nunca** faça brute-force de senha SSH (banimento fail2ban — ver seção acima).
