# Hermes Call — Experimento de Desbloqueio (REACH-OUT TIMELOCK)

Pasta **isolada** em `D:\hermes-call-bloqueio\` — totalmente separada do código de produção.

## POR QUE ESTA PASTA EXISTE

O Hermes Call em produção (D:\hipercool-refactor\), após certo volume de chamadas,
começa a ter TODAS as chamadas rejeitadas pelo servidor do WhatsApp com erro
`offer ack error=439` ou `error=463`. Mensagens funcionam; chamadas não.

Investigação inicial (workers de pesquisa 2026-07-25) identificou a **causa provável**:
o WhatsApp Server aplica **Reachout Timelock** (anti-spam) em contas que fazem
muitos reachouts (chamadas/mensagens) sem o token `<tctoken>` correspondentes.
O whatsmeow v0.0.0-20260630 só anexa `<tctoken>` em `RejectCall()`, **NÃO** no
offer de saída da chamada. Por isso chamada cai 463.

## SEPARAÇÃO DURA COM PRODUÇÃO

| Pasta | Função | Pode mexer? |
|---|---|---|
| `D:\hipercool-refactor\` | **PRODUÇÃO** real (rodando em 62.171.128.241) | ❌ NÃO, sob nenhuma hipótese |
| `D:\hermes-call-anexo\` | Anexo local com fixes do 439 | ⚠️ Só pra APLICAR fix já validado |
| `D:\hermes-call-bloqueio\` | **ESTE DIRETÓRIO** — investigação de desbloqueio | ✅ Pode (e deve) experimentar |

A **única coisa compartilhada** com a produção é a lib `go.mau.fi/whatsmeow` (que vem
do Go mod cache, é código upstream, não nosso).

## AMBIENTE DE TESTE (VPS 2)

Toda experimentação acontece em **VPS 2** (`157.173.207.22`, sem wildcard DNS),
exposta via SSH tunnel (`ssh -L 8081:localhost:8081 root@157.173.207.22` → porta 8081
local). Acessível SÓ da minha máquina. **Produção continua intocada**.

Não estou modificando nada em `D:\hipercool-refactor\` nem deployando nada em
`hermescall.opus-sem-limites.com.br` (prod) — só vou subir uma stack
`hermes-call-anexo` na VPS 2.

## LINHA USADA NO TESTE

`559192438288` (não é linha de campanha, não toca em cliente real).
