# Hermes Call v0.10.0 — aba "Por código" na tela de conexão

Mudança de frontend, pronta e validada, **não commitada e não publicada**. Leia o
`..\LEIA-PRIMEIRO.md` antes, se ainda não leu.

## O que a mudança faz

A tela de conectar uma linha (`SessionPairing`) passa a ter duas abas:

- **QR Code** — exatamente como era antes, nada mudou no comportamento.
- **Por código** — campo para o número com DDI e DDD; o painel chama o servidor e mostra um código
  de 8 dígitos, com o passo a passo de onde digitar (WhatsApp › Aparelhos conectados › Conectar
  aparelho › Conectar com número de telefone). Tem botão para gerar outro se expirar.

O caso da passkey (`session.state === "passkey_request"`) não foi tocado: continua tomando a tela
inteira, sem as abas.

**Isto não cria conta no WhatsApp.** Conecta o Hermes como aparelho secundário de uma conta que já
existe. Não há SMS nesse fluxo.

## Base

Feito em cima do `main`, commit `b2f7e8a`, VERSION `0.9.0` (= o que estava no ar em 08/10/2026).
Se o `main` tiver andado desde então, aplique pelo diff (abaixo), não pelos arquivos inteiros.

## Arquivos

| Arquivo | O que mudou |
|---|---|
| `client/src/services/sessions.ts` | **+4 linhas.** Novo `pairCodeSession(id, phone)` chamando `POST /api/sessions/{id}/pair-code`. Nada mais no arquivo foi tocado. |
| `client/src/components/domain/session/SessionPairing.tsx` | Imports (`Input`, ícones `QrCode`/`Hash`, `pairCodeSession`); novo helper `mensagemDoErro`; novo componente `CodigoStep`; estado `modo` e o seletor de abas dentro do `CardContent`. |
| `CHANGELOG.md` | Entrada nova no topo, acima da v0.9.0. |
| `VERSION` | `0.9.0` → `0.10.0`. |

**Backend: nenhuma mudança.** O endpoint já existia (`httpapi.go:822`, `handleSessionPairCode` →
`sessionmanager.go:310`, `PairPhone`). **Banco: nenhuma migração.**

## Como aplicar

Preferido — o diff, que não sobrescreve trabalho novo:

```bash
cd <raiz do hermes-call>
git apply --check "<esta pasta>/mudancas.diff"   # confere antes
git apply "<esta pasta>/mudancas.diff"
```

Se o `git apply` reclamar (o `main` andou), use `alterados\` como referência e refaça as edições à
mão. **Não copie `CHANGELOG.md` e `VERSION` por cima sem olhar**: se outras versões entraram depois,
você apaga o histórico delas. Nesses dois a edição certa é: acrescentar a entrada no topo do
CHANGELOG e subir o MINOR a partir do que estiver lá.

## Como validar

```bash
cd client
npx tsc --noEmit     # passou aqui
npx vite build       # passou aqui, 56 s
```

Backend não precisa recompilar para esta mudança, mas se for publicar vale o
`go build/vet/test` de praxe.

## O que falta

Ninguém viu a tela renderizada com o painel logado. O código tipa e compila; o visual não foi
conferido. Antes de publicar, convém abrir o painel, criar uma linha nova e olhar as duas abas.

## Publicação

Pelas regras do projeto (`CLAUDE.md`, seção 6): só `bash ops/publicar.sh`, que compila na própria
VPS com `-tags mlow`, faz backup do banco e volta sozinho se não subir em 90 s. Volta manual:
`bash ops/reverter.sh`. **Publicar é ação em produção: só com o OK da dona.**

Observação sobre a máquina onde isto foi feito (PC do Emerson): ela tem `node`/`npm` e tem `git`
(embutido no GitHub Desktop, em
`C:\Users\Emerson\AppData\Local\GitHubDesktop\app-3.6.3\resources\app\git\cmd\git.exe`), mas
**não tem `go`, `gcc` nem `bash`**. Sem `bash` não dá para rodar os scripts de `ops/` por lá. Como o
`publicar.sh` compila na VPS, faltaria só um `bash` (Git for Windows ou WSL) para publicar daquela
máquina.
