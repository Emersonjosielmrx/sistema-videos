# ⭐ ÚLTIMA IMAGEM FUNCIONAL — NÃO PERDER

> Documento de segurança criado em 2026-07-26. Esta é a versão CORRETA e
> FUNCIONAL do Hermes Call. Se algo quebrar de vez na reconstrução, VOLTE PRA CÁ.

## A imagem boa (padrão-ouro)

```
fabricadeautomacoesia/hermes-call:v0.2.1
```

- **Também disponível como:** `:stable`, `:latest`, `:GOLDEN-ultima-funcional-20260723` e `:backup-pre-asaas-20260726-0857` (todas mesmo digest)
- **Tag redundante à prova de sobrescrita:** `fabricadeautomacoesia/hermes-call:GOLDEN-ultima-funcional-20260723` (criada 2026-07-26, mesmo digest)
- **Tag de backup pré-operação Asaas:** `fabricadeautomacoesia/hermes-call:backup-pre-asaas-20260726-0857` (Docker Hub, mesmo digest). Detalhes em [`_BACKUP_OPERACAO_ASAAS.md`](_BACKUP_OPERACAO_ASAAS.md).
- **Snapshot local do container (pré-Asaas):** `hermes-call:snapshot-pre-asaas-20260726-0857` na VPS `.241` (ID `56173657fa2e`).
- **Digest imutável:** `sha256:e9076d201c63fce053d5ff9bead7275ed590f58815bc6516e765bcc177042c13`
- **Versão da API:** `{"build":"20260723-2224","channel":"beta","version":"v0.2.1"}`
- **Bundle front:** `index-BYgTiieN.js`
- **Tamanho:** ~297 MB
- **Registry:** Docker Hub, conta `fabricadeautomacoesia`

## Como ela está preservada (3 cópias independentes)

1. **Docker Hub** — `fabricadeautomacoesia/hermes-call:v0.2.1` (nuvem, imutável por digest).
2. **Rodando na VPS** — container `hermes-call` em `62.171.128.241` (opus-sem-limites),
   servindo `https://hermescall.opus-sem-limites.com.br`.
3. **Cópia local** — `D:\hermes-call\_GOLDEN_v0.2.1\` (binário `wacalls` + `dist` + `MANIFEST.txt`).
   - md5 do bundle golden: `a717f71250d9b34a003f09969051bf6b`

## Login Docker Hub (pra puxar a imagem)

```bash
echo "<removido — ver cofre/VPS>" | docker login -u fabricadeautomacoesia --password-stdin
docker pull fabricadeautomacoesia/hermes-call:v0.2.1
```

## COMO RESTAURAR (rollback total) — se a reconstrução quebrar

Na VPS `62.171.128.241` (senha SSH em `deploy/.env.deploy`):

```bash
# 1. parar o que estiver rodando
docker stop hermes-call && docker rm hermes-call

# 2. subir a imagem boa de novo (mesmas envs)
docker run -d --name hermes-call --restart=always --network host \
  -e "WACALLS_PG_URL=postgres://hermes_call_v3test:<removido — ver cofre/VPS>@localhost:5432/wacalls_main?sslmode=disable" \
  -e "PORT=8080" \
  -e "HERMES_TELEGRAM_TOKEN=<removido — ver cofre/VPS>" \
  fabricadeautomacoesia/hermes-call:v0.2.1

# 3. validar
sleep 8 && curl -s http://127.0.0.1:8080/api/version
# esperado: {"build":"20260723-2224","channel":"beta","version":"v0.2.1"}
```

O container contaminado anterior foi preservado como `hermes-call-backup-<stamp>`
e a imagem como `hermes-call:backup-contaminada-<stamp>` (rollback local também possível).

## Bugs conhecidos NESTA versão (corrigir na reconstrução, não são regressão)

Ver `_BUGS_v0.2.1_A_CORRIGIR.md` — 7 bugs confirmados (voz/nome incompatível mal
exibido, estimativas simuladas, chat de teste não puxa agentes reais, wizard não
responde após finalizar, wizard não pede Whisper/voz em ligação, tema preto ao
abrir Config, motor de ligação pede API key com credencial já vinculada).

## Por que o fonte exato não existe

A v0.2.1 foi buildada de um working-tree NÃO commitado e o fonte se perdeu.
Confirmado ausente em: git local (todas branches/tags/stashes/reflog), GitHub
(2 contas, todas branches/tags + busca de código), Docker Hub (só binário
compilado), e disco inteiro. Ver memória `project_hermes_versao_limpa_v021` e
seção anti-contaminação no `CLAUDE.md`.

A reconstrução acontece na branch git `reconstrucao-v0.2.1`, usando esta imagem
como molde. **Esta imagem NUNCA deve ser sobrescrita** até a reconstrução estar
validada e a dona aprovar.
