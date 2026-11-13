# Hermes e bancada nas duas VPS

Decisão da dona em 07/10/2026: **manter Hermes e bancada instalados nas duas VPS, usar um em cada, e inverter para
comparar.** Motivo: a VPS da produção engasga (`docs/ensaios/2026-10-06_1246_ligacao-picotada.md`) e a de teste não.

## Como está (07/10 14:35)

| | Produção (62.171.128.241, `hermes-prod`) | Teste (209.145.60.53, `hermes-staging`) |
|---|---|---|
| **Hermes** | **NO AR**, v0.9.0 `20261007-1425_cdad439`, linhas 8653 e 8288 | reserva em `/opt/hermes-call-reserva`: só o programa e o painel, **desligado** |
| **Bancada** | instalada, mesma versão, **parada e desabilitada**, bancos guardados | **LIGADA**, linha 8288, banco próprio (`hermes-bancada-pg`, `127.0.0.1:5440`) |

Todas as cópias estão no mesmo programa. Depois de cada publicação: `bash ops/atualizar-copias.sh`.

## Inverter a BANCADA (pronto, um comando no PC)

```
bash ops/bancada/trocar-bancada-de-vps.sh estado
bash ops/bancada/trocar-bancada-de-vps.sh para-producao    # 209 -> produção
bash ops/bancada/trocar-bancada-de-vps.sh para-209         # produção -> 209
```

Ele para a de origem, copia os dois bancos e as gravações, e liga a de destino. **Nunca ligue a bancada só com
`systemctl start`**: a linha 8288 é a mesma nas duas, e ligar com o banco velho da outra (ou as duas juntas) estraga a
sessão do WhatsApp. O caminho produção → 209 foi feito à mão em 07/10 e funcionou; o caminho 209 → produção **ainda
não foi exercitado** (o script confere o número de tabelas e para se algo não bater).

## Inverter o HERMES (não está pronto: é uma mudança de máquina)

Hoje a reserva da 209 não liga: não tem banco, linha, nem segredo. Para o Hermes atender pela 209 é preciso levar:

1. **Os bancos**: `wacalls_main` (446 MB) e um por linha. Enquanto copia, o Hermes fica fora do ar (minutos).
2. **As gravações e os envios** (`/var/lib/hermes-call`, pasta de uploads).
3. **As linhas do WhatsApp** vão dentro dos bancos. Vale a mesma regra da bancada: uma máquina por vez.
4. **Os segredos da produção** (assinatura dos logins, bot do Telegram). Hoje existem só na produção, de propósito.
   **Decisão da dona:** a 209 já foi invadida uma vez (conta `duc`). Em 07/10, vista de fora, a porta de banco 5433
   estava aberta (aberta nesse dia por um agente; `ops\DESFAZER-SENHA-DO-BANCO-209.bat` fecha) e as 5432, 5436 e 6379
   estavam filtradas. Antes de pôr segredo de produção lá: 5433 fechada e a senha do banco compartilhado desfeita.
5. **O domínio** `hermescall.opus-sem-limites.com.br` aponta para a produção. Ou a dona muda o apontamento no painel
   do domínio, ou o Traefik da produção repassa para a 209 (exige abrir uma porta só entre as duas).
6. **O que roda junto na produção**: backup diário, avisos de queda, bot do Telegram (só uma máquina pode usar o
   mesmo bot), webhook do Asaas quando existir.
7. **A volta**: o caminho inverso, com os dados novos.

Nada disto foi feito. Quando a dona decidir os itens 4 e 5, o agente escreve `ops/trocar-hermes-de-vps.sh` nos mesmos
moldes do da bancada e ensaia primeiro com a bancada.

## O que já dá para comparar sem mudar o Hermes de máquina

O programa é o mesmo nas duas bancadas e na produção. Então:

| Medida | Onde | Como |
|---|---|---|
| máquina boa | bancada na 209 | chamada direta da bancada (o agente dispara) |
| máquina que engasga, mesmo programa | Hermes de produção | a dona pede a ligação pelo Telegram |
| máquina que engasga, bancada | bancada na produção | `trocar-bancada-de-vps.sh para-producao` e chamada direta |

No registro de cada ligação: `qualidade do áudio da ligação` (`resultado`, `tx_buracos`, `rx_jitter_ms`) e
`gravação: frames fora do ritmo…` (`ia_maior_ajuste_ms`). Resultados até agora:

| Ligação | Máquina | Programa | `tx_buracos` | Abertura gravada | Ajuste na fala da IA |
|---|---|---|---|---|---|
| 06/10 12:46 | produção | sem a correção | 14 | 7,3 s | (não media) |
| 06/10 17:46 | produção (bancada) | com a correção | 3 | 6,1 s | 307 ms |
| 07/10 14:15 | **209 (bancada)** | com a correção | **0** | **5,8 s** | **29 ms** |
