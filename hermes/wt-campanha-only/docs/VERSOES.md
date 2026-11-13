# Versões do Hermes Call: qual é a certa

> Fonte única da verdade sobre versões. Se algum outro documento contradisser este, **vale este**.
> Atualizado em 05/10/2026.

## A versão certa

**A versão certa é a que está no ar** em https://hermescall.opus-sem-limites.com.br.

- Para ver qual é: `bash ops/status.sh`, ou abra `/api/version` e olhe o campo `build`.
- No git ela é o branch `main` (e a tag `PRODUCAO-...` mais recente).
- Toda correção começa do `main` atualizado. O `ops/publicar.sh` **recusa** publicar um commit que não contenha a versão que está no ar.

| Data | Versão | Commit | Como chegou lá |
|---|---|---|---|
| 26/08/2026 | TOC-fix (v0.3.9) | `6c5794b`, tag `PRODUCAO-2026-08-26-tocfix` | compilada à mão na VPS; capturada no git em 24/09 e conferida arquivo por arquivo |
| **24/09/2026** | **v0.5.0** | `ee98b85`, tag `PRODUCAO-20260924-2331_ee98b85` | primeira publicação pelo `ops/publicar.sh` (com backup do banco e volta automática) |
| 25/09/2026 | v0.5.0 (correções) | `29e4e85`, build `20260925-0158_29e4e85` | `ops/publicar.sh`; **ESTÁVEL (volta segura)** desde 03/10 |
| 03/10/2026 | v0.6.0 | `f021966`, tag `PRODUCAO-20261003-0857_f021966` | `ops/publicar.sh` com OK da dona |
| 03/10/2026 | v0.6.1 | `dbcfd55`, tag `PRODUCAO-20261003-0919_dbcfd55` | ajustes da ligação de teste (interrupção, preço, voz) |
| 03/10/2026 | v0.7.0 | `af7413e`, build `20261003-2306_af7413e` (antes `7d82f24`) | `ops/publicar.sh` com OK da dona; ficou no ar até 05/10 (a dona achou aceitável) |
| 05/10/2026 | v0.8.0 | `b9bf587` (= `main` = ramo `pc/v0.8.0`), build `20261005-1058_b9bf587`, tag `PRODUCAO-20261005-1058_b9bf587` | v0.8.0 da nuvem + correções/revisão do PC + ensaios na bancada; `ops/publicar.sh` com OK da dona; ficou no ar das 11:05 às 11:53; é a volta do `ops/reverter.sh` |
| **05/10/2026** | **v0.8.1** | `f28526a` (= `main` = ramo `pc/v0.8.0`), build `20261005-1148_f28526a`, tag `PRODUCAO-20261005-1148_f28526a` | F31, planilhas CSV e token do Telegram mascarado; `ops/publicar.sh` com OK da dona; ficou no ar até 07/10 14:33 |
| **07/10/2026** | **v0.9.0** | `cdad439` (ramo `pc/v0.8.0`), build `20261007-1425_cdad439`, tag `PRODUCAO-20261007-1425_cdad439` | voz tolerante ao engasgo do servidor, gravação em sequência, achados de julho, painel; duas ligações de verdade pela bancada antes; `ops/publicar.sh` a pedido da dona ("mantenha dois Hermes atualizados com a correção"); ficou no ar até 08/10 15:48; é a volta do `ops/reverter.sh` |
| **08/10/2026** | **v0.10.0** | `b0605a3` (= `main` = ramo `pc/v0.8.0`), build `20261008-1541_b0605a3`, tag `PRODUCAO-20261008-1541_b0605a3` | aba "Por código" na tela de conectar (parear sem ler o QR Code; só painel), mais a caixa `telefone,Nome` do Disparo em Massa e o ajuste do roteiro de vendas; `ops/publicar.sh` com OK da dona; **no ar**. As bancadas (produção e 209) e a reserva da 209 estão na mesma versão (`ops/atualizar-copias.sh`) |
| a partir de agora | publicações feitas pelo `ops/publicar.sh` | tag `PRODUCAO-<data>_<commit>` | registradas em `/opt/hermes-call/releases/HISTORICO` na VPS |

## Onde existe código (24/09/2026)

| Lugar | Até | Situação |
|---|---|---|
| **`D:\hermes-call`, branch `main`** | 24/09 (v0.5.0, no ar) | **fonte da verdade** |
| GitHub `fabricadeautomacoesia/hermes-call` (remote `origin`) | 24/09 | igual ao `main` |
| GitHub `Emersonjosielmrx/hermes-call` (remote `emerson`) | 24/09 | igual ao `main` |
| Branch `backup-versao-final-bd24` | 02/08 | já incorporado no `main` (v0.5.0) |
| **`/opt/hermes-call-fonte`** nas 2 VPS | = `main` | **cópia de referência** (git completo) pra outros agentes/projetos consultarem. Atualizada pelo `ops/enviar-fonte.sh` (o `publicar.sh` já chama). Não compilar/publicar a partir dela |
| Cópias antigas do código (produção) | jul/ago | movidas em 25/09 para `/opt/_arquivo_hermes_antigo_20260925/codigo/`. Não usar |
| `_GOLDEN_v0.2.1/`, `_VERSAO_BOA_SOURCE/`, `version_corrente_vps/` | jul/ago | **históricos, obsoletos**. Não usar |

Em 24/09 o `main` foi enviado para os dois GitHubs (sem sobrescrever nada: os dois só estavam para trás).

## Regras de build

1. **Sempre `-tags mlow` e `CGO_ENABLED=1`**, compilando na VPS (liga na `/usr/local/lib/libopus_mlow.so`). Todo binário marcado "QUEBRADA / só conectando" em agosto foi compilado **sem** mlow. Para conferir um binário: `go version -m <binário> | grep tags`.
   O painel (`client/`) é compilado **no PC** (a VPS tem Node 18 e o Vite 7 exige 20+).
2. Compilar só a partir de um **commit** (o `git archive` do `ops/publicar.sh` garante isso), nunca de pasta suja.
3. O `buildStamp` recebe o ID da versão, então `/api/version` mostra exatamente qual versão está no ar.

## Como publicar e reverter

```bash
bash ops/status.sh                 # o que está no ar + versões guardadas
bash ops/publicar.sh --so-compilar # compila e prepara na VPS sem colocar no ar
bash ops/publicar.sh               # publica o HEAD (com backup do banco e volta automática)
bash ops/voltar-estavel.sh         # VOLTA SEGURA: põe no ar a versão ESTÁVEL (pode rodar de novo, não alterna)
                                   #   = dois cliques em ops\VOLTAR-VERSAO-ESTAVEL.bat (pede "SIM")
bash ops/marcar-estavel.sh         # depois de validar: a versão no ar vira a nova ESTÁVEL
bash ops/reverter.sh               # volta para a versão de onde veio a última troca (cuidado: rodar 2x alterna)
bash ops/reverter.sh <ID>          # volta para uma versão específica
bash ops/publicar-teste.sh         # ensaio: publica o HEAD na VPS de teste (Docker)
bash ops/publicar-teste.sh --voltar
```

Na VPS, cada versão fica em `/opt/hermes-call/releases/<ID>/` (binário, painel, INFO e `banco.dump`). O sistema guarda as últimas 8 versões e os 3 últimos backups do banco — e **nunca apaga a versão ESTÁVEL nem as marcadas PROTEGIDA** (nem o backup do banco delas). `releases/ESTAVEL` diz qual é a estável; o `publicar.sh` marca a versão no ar como estável antes da primeira troca. O serviço continua sendo o systemd `hermes-call`, com os mesmos caminhos de antes.

**O banco não é revertido automaticamente.** Reverter só troca o programa e o painel. Se uma versão estragar dados, o `banco.dump` da versão anterior tem o backup feito logo antes da troca. Restaurar o banco só com o OK da dona, porque os dados novos se perdem.

## Backups antigos soltos na VPS

Em 25/09 os binários de backup soltos (`hermes-call.bak*`, `*.GOLDEN-v3-*`, `*-tocfix-20260821` etc.), as
cópias antigas do painel (`dist.bak`, `dist.new`), as cópias antigas do código (`/opt/hipercool-refactor`,
`/opt/build-bd24aef`, `/opt/hermes-qa`, `/opt/hermes-teste-src`) e o cron morto da campanha das 9h
(`/etc/cron.d/hermes_disparo_9h`) foram MOVIDOS para `/opt/_arquivo_hermes_antigo_20260925/`
(lista em `MANIFESTO.txt` lá dentro). Nada disso estava em uso. A dona pode apagar a pasta para
liberar 1,9 GB. As versões para reverter ficam em `/opt/hermes-call/releases/`.

## Ambientes

| Ambiente | Endereço | Situação em 24/09 |
|---|---|---|
| **Produção** | 62.171.128.241, `ssh hermes-prod`, hermescall.opus-sem-limites.com.br | v0.5.0 no ar (systemd) |
| Teste | 209.145.60.53, `ssh hermes-staging` | de volta ao ar em 24/09 (banco apontado pelo nome `pg_v3` em vez de IP fixo). Serviço Docker `hermes_call_refactor_hermes-call-refactor` |
| Teste de bloqueio | 157.173.207.22:8090 | fora do ar |
