# CLAUDE.md — Hermes Call

> **LEIA ISTO PRIMEIRO.** Este arquivo orienta qualquer agente (Claude ou outro modelo) que abra este
> projeto: o que ele é, onde estão as coisas, como trabalhar e como publicar. Mantenha-o atualizado.

> ## 🟢 ESTADO ATUAL (04/10/2026) — vale acima de tudo abaixo
>
> 1. **Leia, nesta ordem:** `CONTINUAR_DAQUI.md` (onde paramos + regras da dona),
>    `docs/PLANO_MES_OUTUBRO_2026.md` (o que fazer agora, em que ordem e quem faz cada item) e, se for
>    mexer na ligação/voz, `docs/REGRESSOES_LIGACAO.md` (obrigatório).
> 2. **A versão certa é a que está NO AR** em hermescall.opus-sem-limites.com.br (veja `bash ops/status.sh`
>    e `docs/VERSOES.md`). Roda via **systemd** (`/opt/hermes-call/hermes-call`), **não** via Docker.
> 3. **Publicar só com `bash ops/publicar.sh`** (bloqueia retrocesso, compila com mlow, faz backup do banco
>    e volta sozinho se falhar). Para voltar: **`bash ops/reverter.sh`**. Os scripts de `deploy/` são
>    obsoletos para a produção.
> 4. Acesso às VPS só por chave: `ssh hermes-prod` / `ssh hermes-staging`. Nunca digite senha.
> 5. **Segredos da produção** ficam em `/etc/systemd/system/hermes-call.service.d/10-segredos.conf`
>    (ex.: `HERMES_JWT_SECRET`). O servidor **recusa iniciar** sem ele. Não mexa nesse arquivo nem o copie
>    para o repositório.
> 6. A porta **8080 está fechada** na internet de propósito (só o Traefik, em 127.0.0.1, fala com o
>    servidor). Não reabra.
> 7. Pendências e estado de cada bug: **`docs/PENDENCIAS_BUGS.md`**.
> 8. **Onde se trabalha no PC (06/10):** o código novo fica no ramo `pc/v0.8.0`, aberto na pasta
>    **`D:\hermes\pc-base`**. **`D:\hermes\hermes-call` é o `main` = cópia do que está NO AR: não mude código
>    aqui.** Abra `D:\hermes\pc-base` e leia o `CONTINUAR_DAQUI.md` de lá (é o mais novo). Desde 12/10 tudo
>    do Hermes no PC fica em `D:\hermes\` (mapa em `D:\hermes\LEIA-ME.md`). Em 06/10 um
>    agente corrigiu 9 arquivos soltos no `main` sem saber que as mesmas correções já estavam prontas e
>    testadas no `pc/v0.8.0`; o trabalho dele teve de ser desfeito.
> 9. **Documento antigo não é lista de pendência.** Antes de corrigir um "achado" (auditoria F01–F34,
>    `docs/QA_PAINEL_E_METRICAS.md`, `docs/BACKLOG_DX.md`, tudo em `docs/archive/`), confira o estado em
>    `docs/mes2-online/README.md` e `docs/PENDENCIAS_BUGS.md` **e no código do `pc/v0.8.0`**. Quase tudo
>    o que esses documentos listam já foi corrigido.
>
> ### Onde você está rodando muda o que você pode fazer
>
> | Ambiente | Pode | Não pode |
> |---|---|---|
> | **Nuvem** (Claude Code online, repositório do GitHub) | ler e mudar o código, `go build/vet/test`, `vite build`, enviar ao GitHub | entrar nas VPS (sem chave e a porta 22 é bloqueada), publicar, ligar |
> | **PC** (Claude Code em `D:\hermes\pc-base`, com a chave SSH) | tudo da nuvem + publicar, ver o registro da produção, usar a bancada, ligação de teste | trocar senhas e segurança do servidor sem a dona |
>
> Os avisos de julho (produção em Docker, `_GOLDEN_v0.2.1`) foram para
> `docs/archive/CLAUDE_md_avisos_julho_2026.md`. São históricos: não siga.


## 0. Identidade do projeto e regra de TROCA entre projetos

**Este `CLAUDE.md` vale para o projeto Hermes Call, cuja raiz é `D:\hermes\hermes-call`.**

Cada projeto tem o SEU próprio `CLAUDE.md` na raiz. A regra de orientação é:

1. **Confirme onde você está.** Se a pasta aberta é `D:\hermes\hermes-call` ou `D:\hermes\pc-base` (ou o
   repositório `fabricadeautomacoesia/hermes-call` ou `Emersonjosielmrx/hermes-call`), **este** arquivo é o
   guia — siga-o.
2. **Se a tarefa é sobre OUTRO projeto** (não o Hermes Call), **não trabalhe aqui.**
   Abra a pasta do projeto correto e leia o `CLAUDE.md` da raiz dele. O mapa de
   projetos conhecidos está na seção **"Registro de projetos"** abaixo — troque para
   o que casar com a tarefa.
3. **Se você abriu outra pasta e a tarefa é sobre o Hermes Call**, volte para
   `D:\hermes\pc-base` e use este arquivo.
4. Regra geral: **o `CLAUDE.md` que manda é sempre o da raiz do projeto da tarefa.**
   Fique trocando conforme o projeto — nunca misture procedimentos de projetos diferentes.

> Existe também um `CLAUDE.md` GLOBAL do usuário (regras que valem para TODAS as
> sessões/projetos) em `C:\Users\Haylla\.claude-vscode\CLAUDE.md`. Ele complementa
> este; em conflito, o global (comportamento/idioma) e este (técnico do projeto)
> se somam — este detalha o específico do Hermes Call.

### Registro de projetos (atualize quando surgir um novo)

| Projeto | Raiz | Guia | Do que trata |
|---|---|---|---|
| **Hermes Call** | `D:\hermes\hermes-call` (GitHub: `fabricadeautomacoesia/hermes-call`, cópia em `Emersonjosielmrx/hermes-call`) | este `CLAUDE.md` | ligações WhatsApp + agente IA, CRM, painel (ESTE) |
| **Campanha Hermes** | `D:\hermes\campanha` | `README.md` de lá | campanha de ligações pra vender o Hermes (plano do mês, item P5) |
| **Veo** | `D:\veo` (a versão que roda é `D:\veo\beta`) | `docs\LEVANTAMENTO_2026-10-15.md` e `docs\PLANO_MELHORIAS_VEO.md` de lá | Shorts gerados no Google Flow/Veo 3.1 com a foto da dona + comercial dos produtos (Hermes Call, Avatar IA, Follow-up IA, SuperChat IA) |
| **ManhwaReact** | `D:\manhwa-react` | `CLAUDE.md` de lá | Shorts de react + a **rede de 19 canais do YouTube** (`mr\rede.py`), hoje o único caminho de postagem saudável |
| **Hipercool** | `D:\hipercool-videos` | `CLAUDE.md` de lá e `docs\MELHORIAS_PARA_TODOS_OS_PROJETOS.md` (fonte oficial das melhorias de vídeo) | recap de manhwa em várias línguas |
| **Postador de vídeos** | `D:\postador-de-videos` | `LEIA.txt` de lá | postagem compartilhada (YouTube/TikTok/Instagram), política de uploads, relatórios do banimento de 04/09/2026 |

> Ao criar/descobrir um novo projeto: adicione a linha aqui **e** crie um `CLAUDE.md`
> na raiz dele. Assim qualquer agente abre a pasta certa e se orienta sozinho.

---

## 1. O que é o Hermes Call

Sistema de **ligações WhatsApp com agente de IA**. Faz/recebe chamadas de voz nativas
(whatsmeow + codec MLow), tem painel web, bot Telegram, CRM, campanhas em massa e
agente LLM que opera o sistema. Multi-tenant (cada usuário vê só os próprios dados).

- **Backend:** Go 1.26, pacote `main` em `cmd/server/` (~108 arquivos), libs em `internal/`.
- **Frontend:** React + TypeScript + Vite + Tailwind em `client/`.
- **Banco:** PostgreSQL — `wacalls_main` + um `wacalls_<sessionid>` por número WhatsApp.
- **Áudio da ligação:** codec MLow (`libopus_mlow.so`), compilado no `Dockerfile` (cgo).
- **Produção:** binário Go rodando via **systemd** (`hermes-call.service`,
  `/opt/hermes-call/hermes-call`) na VPS `62.171.128.241`, atrás do Traefik, domínio
  `hermescall.opus-sem-limites.com.br`. Publicação só por `ops/` (seção 6).

### ⚠️ VPS de produção (COMPARTILHADA — não confundir)

**O Hermes Call roda na VPS `62.171.128.241`, mas ela NÃO é exclusiva:** a mesma máquina
também roda o **Atlas** e o **Lucrativa** (projetos do trader). **Não mexa neles**
(serviços, bancos, crons, pastas, portas) — ao operar na VPS, toque só no que é do
Hermes (`hermes-call.service`, `/opt/hermes-call*`, bancos `wacalls_*`, units
`hermes-*`). Limites globais (ex.: journal, disco) afetam todos: pense nisso antes.

> O CLAUDE.md **global** menciona a VPS `209.145.60.53` (Swarm) como padrão dos
> "projetos web" — **isso NÃO vale para a produção do Hermes.** A `209...` é só a VPS
> de TESTE do Hermes (`ops/publicar-teste.sh`) e de outros projetos. Nunca publicar a
> produção do Hermes na `209...`.

| Item | Valor (VPS 62.171.128.241) |
|---|---|
| Acesso | `ssh hermes-prod` (**só por chave**; nunca digite/teste senha) |
| Serviço | `hermes-call.service` (systemd); segredos em `/etc/systemd/system/hermes-call.service.d/10-segredos.conf` |
| Versões | `/opt/hermes-call/releases/` (ver `bash ops/status.sh`) |
| Porta interna | `127.0.0.1:8080` (Traefik faz o proxy/TLS; 8080 fechada na internet) |
| Banco | PostgreSQL local, `wacalls_main` + `wacalls_<sessionid>` por número |
| Domínio | `hermescall.opus-sem-limites.com.br` |
| Operação | backup diário, alertas e journal: `ops/vps/` (instalar com `ops/vps/instalar-operacao.sh`) |
| Login painel | admin definido por `HERMES_ADMIN_EMAIL`/`HERMES_ADMIN_PASSWORD` (sem senha padrão) |

## 2. Mapa da pasta (onde procurar)

| Caminho | O que é |
|---|---|
| `cmd/server/` | **todo o backend** (HTTP, agente IA, WhatsApp, CRM, voz, telegram…) |
| `internal/` | libs: `settings/`, `billing/`, `voice/`, `voip/`, `auth/`… |
| `client/src/` | frontend (pages/, components/, services/, stores/, types/) |
| `ops/` | **publicação da produção** (`publicar.sh`, `reverter.sh`, `status.sh`) e `ops/vps/` (backup/alertas) |
| `deploy/` | scripts antigos de deploy Docker + credenciais (⚠️ gitignored; **histórico**) |
| `docs/` | `ARCHITECTURE.md`, `DEPLOY.md` (infra VPS), `COMO_*`, `archive/` (histórico) |
| `native/` | `libopus_mlow.so` (gerado no build) |
| raiz | `README.md`, `CHANGELOG.md`, `VERSIONING.md`, `CONTRIBUTING.md`, `VERSION`, `Dockerfile`, `Makefile` |

Documentos-chave para se orientar:
- **Arquitetura:** `docs/ARCHITECTURE.md`
- **Versionamento (regras):** `VERSIONING.md`
- **Deploy/build (procedimento + infra):** `deploy/DEPLOY.md` e `docs/DEPLOY.md`
- **Histórico de mudanças:** `CHANGELOG.md`
- **Anotações antigas (podem estar desatualizadas):** `docs/archive/`

## 3. Ambiente (importante)

- **Backend:** valide com `export CGO_ENABLED=0; go build ./... && go vet ./... && go test ./...`
  (o mesmo que o CI roda). O CI também roda `CGO_ENABLED=1 go test -race ./...` (detector de corrida;
  precisa de `gcc`). O build com o codec MLow (`-tags mlow`, cgo) só acontece na VPS, feito pelo
  `ops/publicar.sh`.
- **Simulador de ligação:** `go test ./internal/voice/ -run Simulador -v` (~18 s). Roda o agente de voz
  inteiro com uma linha telefônica falsa. Se falhar depois da sua mudança, você trouxe de volta um problema
  que a dona já viu (`docs/REGRESSOES_LIGACAO.md`).
- **Frontend dá pra buildar local:** `cd client && npm ci && npm run build`.
- Atalhos: `make help` (ver `Makefile`).
- **Configurações do servidor (variáveis de ambiente):** todas estão em `.env.example` (raiz), com o que fazem e o
  padrão. Criou uma nova? Documente lá e rode `go test ./cmd/server -run TestEnvCatalog -atualizar-catalogo`
  (o teste falha se faltar). A dona vê o que está em uso em Configurações › "Configuração do servidor".

## 4. Como trabalhar (fluxo)

1. Mudança pequena e focada; siga o estilo do arquivo vizinho.
2. Valide o que der localmente: **sempre** `cd client && npx vite build` após mexer no
   front; no backend, `go build/vet/test` (seção 3). O **CI** (`.github/workflows/ci.yml`)
   roda o mesmo no push/PR.
3. Toda mudança relevante entra no `CHANGELOG.md`.
4. Publicação só pelo `ops/` (ver seção 6): teste em `ops/publicar-teste.sh`, produção em
   `ops/publicar.sh`, volta com `ops/reverter.sh`.

## 5. Versionamento (REGRA FIXA)

- **Cada melhoria sobe +1 ponto (o MINOR) e o projeto fica SEMPRE abaixo de v1.0**
  (série `v0.x`): `v0.1.0` → `v0.2.0` → `v0.3.0` → … Nunca chega em v1.0.0.
- Fonte da versão: arquivo `VERSION` na raiz. O binário expõe em `GET /api/version`.
- Canal: o binário publicado por `ops/publicar.sh` sai com `channel":"producao"` em
  `/api/version` (os canais Docker `:latest`/`:next` são históricos).
- Migrações de banco **devem ser aditivas** (`ADD COLUMN IF NOT EXISTS`,
  `CREATE TABLE IF NOT EXISTS`) — é o que garante o rollback. Detalhes: `VERSIONING.md`.

## 6. Publicação (procedimento ATUAL: systemd via `ops/`)

```bash
bash ops/publicar-teste.sh          # ensaio na VPS de teste (209.145.60.53)
bash ops/publicar.sh --so-compilar  # compila e prepara na produção SEM colocar no ar
bash ops/publicar.sh                # publica o HEAD (commit limpo) na produção
bash ops/status.sh                  # o que está no ar + versões guardadas
bash ops/reverter.sh                # volta para a versão anterior
```

- `ops/publicar.sh` recusa git sujo e retrocesso, roda `go vet` e compila na VPS com
  `-tags mlow` e canal `producao`, faz backup do banco, troca a versão e volta sozinho se
  não subir em 90 s; depois envia a tag `PRODUCAO-<ID>` ao GitHub.
- Operação da VPS (backup diário, alertas de queda/disco, limite do journal): `ops/vps/`.

### Histórico (NÃO usar na produção): Docker / `deploy/*.js`

Até ago/2026 a produção rodava em container Docker publicado por `node deploy/release.js`,
`deploy/deploy-beta.js`, `deploy/promote-stable.js` e `deploy/rollback.js` (canais
`:next`/`:latest`). Esses scripts não estão no git e **não valem mais para a produção**.
O `.github/workflows/release.yml` (imagem no Docker Hub ao dar push de tag `v*`) e o
`Dockerfile` seguem servindo só para a VPS de teste.

### ⚠️ ARMADILHA DO SSH (fail2ban)

- **Acesso só por chave** (`ssh hermes-prod` / `ssh hermes-staging`). **Nunca** tente senha
  — e nunca escreva senha em arquivo versionado (as que existiam foram removidas em out/2026;
  se precisar, estão no cofre da dona).
- **NUNCA teste senha SSH em loop.** A VPS tem **fail2ban**: tentativa errada repetida →
  seu IP é **banido na porta 22** (dá `ETIMEDOUT`), enquanto 80/443 seguem abertas.
  Foi a causa do deploy travado em 2026-07-21. Detalhes e como sair do ban: `deploy/DEPLOY.md`.
- Diagnóstico rápido: se o site responde mas a porta 22 dá timeout → **é ban do seu IP**,
  não é a VPS. Use outra máquina/IP ou espere o ban expirar.

## 7. Segurança (não negociável)

- **Nunca** commite segredos. `deploy/` é gitignored; só `.env.deploy.example` e
  `DEPLOY.md` são versionados. Não cole tokens em PR/issue/chat. Em doc, troque o valor
  por `<removido — ver cofre/VPS>`.
- O servidor mascara segredos nos logs (`cmd/server/redact.go`); não desligue isso e não
  logue texto de mensagens de clientes fora do nível Debug (LGPD).
- Rotacione PATs (Docker Hub) periodicamente.
- Ações destrutivas (apagar dados, force-push, mexer em produção) → confirme antes.

## 8. Regras rápidas para o agente

- **Mexeu na voz/ligação? Leia antes `docs/REGRESSOES_LIGACAO.md`.** Problemas como "a IA não para quando o
  cliente fala" já foram corrigidos e voltaram quando alguém mexeu no código. Os testes listados lá não podem ser
  apagados nem afrouxados; e mudança de voz só é "pronta" depois de uma ligação de verdade.
- Responda em **português brasileiro**, direto.
- Não crie arquivos `.md` de scratch na raiz — anotações vão em `docs/archive/` ou não
  existem. A raiz é só documentação de produto.
- Não reintroduza os arquivos que foram arquivados/removidos (snapshots, scripts de
  debug soltos). O código de verdade vive em `cmd/` e `internal/`.
- Ao terminar uma leva: atualize `CHANGELOG.md`, bump do `VERSION`, e siga o fluxo de release.
- Terminou um item do plano do mês? Marque `[x]` com data e commit em `docs/PLANO_MES_OUTUBRO_2026.md` e
  acrescente uma linha na seção "Registro do mês" dele. É assim que o próximo agente sabe onde parou.
- Antes de afirmar algo sobre o código num documento, confira no código (ex.: 04/10 um agente escreveu que o
  pré-aceite não era enviado; era).
- Mantenha **este `CLAUDE.md`** atualizado quando o procedimento mudar.

## 9. Herdado do global (vale aqui também)

Estas regras vêm do `CLAUDE.md` global do usuário e se aplicam a este projeto:

- **Modo ativo** (usuário presente): implemente, teste, mostre o resultado; chame o
  usuário só na validação final. **Modo autônomo** (usuário ausente): continue a lista
  sozinho, resolva travas antes de escalar, e registre o progresso em
  `logs/night-shift.md`.
- **Validar de verdade antes de dizer "pronto".** Aqui isso significa: `vite build`
  passou (frontend) e, pro backend, `go build/vet/test` (na nuvem roda direto; no PC da dona pode não
  haver Go: aí vale o CI verde). Não afirme que algo funciona sem prova.
- **Ações autônomas trabalham LOCAL.** Commit/push e deploy só com confirmação do
  usuário (deploy é produção — VPS `62.171.128.241`).
- **Gateway LLM** (ambiente do usuário): `ANTHROPIC_BASE_URL=http://157.173.207.22:20128`
  (sub-proxy com filas de fallback). Não confundir com o **gateway de IA do produto**
  (omniroute) que o app usa em runtime — este exige `stream:true`/SSE (ver `chatOpenAIH`
  em `cmd/server/aiagent.go`; a porta `:20129` era contorno, resolvido na v0.1.0).
- Responder em **pt-BR**, direto; nunca escrever "(empty)".

## 10. Ideias para facilitar o trabalho futuro (backlog de DX)

Coisas que dá pra adicionar depois pra deixar o dev/deploy ainda mais fácil (nada
disso é obrigatório agora — anotado pra não esquecer):

- **`make doctor`** — script que checa o ambiente ao abrir a pasta: se tem Node/Go/Docker,
  se `deploy/.env.deploy` existe, se o `git remote` é o certo, e imprime a versão atual
  (`VERSION`) + o que está no ar (`curl /api/version` na VPS). Ajuda o agente a se localizar.
- **`deploy/status.js`** — SSH na VPS e imprime: container up?, `/api/version`, últimas
  linhas do log, imagens `hermes-call:*` presentes. Diagnóstico rápido sem abrir SSH.
- **Smoke test pós-deploy** — script que, após subir, valida login, `/api/version` e um
  endpoint autenticado, e falha o deploy se algo quebrar.
- **Seed de dados de dev** — um `docker compose` + seed pra subir um ambiente local
  completo (Postgres + app + usuário de teste) sem depender da VPS.
- **Dependabot/renovate** — atualizar deps Go/npm com PR automático (o CI valida).
- **CODEOWNERS + template de PR** — padroniza revisão.
- Registrar aqui, conforme surgirem, os "pega-ratão" recorrentes (o equivalente ao
  `SINTOMA_CAUSA_FIX.md` que o projeto hipercool usa).
