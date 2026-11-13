# 1min.ai pela API — Opus 5.5 / Fable 5.1 sem navegador (30/10/2026)

Conta: **sua_conta@gmail.com** (a mesma de teste do `RESULTADO.md`). Chave em `..\segredos\1min.key`.

## Por que API e não a tela

- Na tela (Multi AI Chat) a pergunta vai para **vários modelos juntos** e o Qwen vem marcado: gasta crédito à toa.
  Pela API o modelo vai fixo no pedido e não tem isso.
- **Custo medido, pergunta curta:**

  | Modelo | Créditos | Tempo |
  |---|---|---|
  | Opus 5.5 | **3.973** (pela tela era ~21.600) | 8 s |
  | Opus 5 | 14.124 | 5 s |
  | Fable 5.1 | 60.357 | 9 s |
  | Haiku 5.5 | 87 | 3 s |

- O endpoint compatível com OpenAI do 1min (`/openai/v1`) **não tem Claude**. O Claude só sai pelo `/api/chat-with-ai`,
  que é o que o `umin.py` usa.
- Das 13h40 às 14h20 o Opus 5.5 deu `503 Bedrock is unable to process your request` (a AWS deles sem capacidade).
  Falha **não é cobrada**. Por isso o `umin.py` tenta de novo 3 vezes e aceita `--reserva`.

## Uso

```bash
python umin.py "pergunta"                    # Opus 5.5
python umin.py -m fable "pergunta"           # fable, fable5, opus5, opus48, opus47, opus46, sonnet, haiku
python umin.py --reserva opus5 "pergunta"    # se o Opus 5.5 não responder, usa o Opus 5 (e avisa)
python umin.py --conversa nova "pergunta"    # conversa com contexto; depois: --conversa ultima "e agora?"
python umin.py saldo                         # saldo calculado e gasto médio por modelo
python umin.py calibrar 145429               # acerta o saldo com o número que a tela mostra
```

Como módulo: `from umin import perguntar; texto, info = perguntar("oi", reservas=("opus5",))`.
O `info` traz o modelo que respondeu de fato, os segundos, o gasto e o saldo. Cada pergunta vira uma linha no
`umin_uso.jsonl`, com as falhas também.

## Sem cadastro?

Não. A página "free-ai-chat-with-claude-opus-5-5" diz "No registration is needed", mas, testado sem login em 30/10,
o envio da mensagem abre o quadro "Log In". Tudo aqui depende da conta já existente (conta_exemplo, login Google).

## Saldo e créditos grátis

- A chave **não lê o saldo**; só a sessão do site lê. A conta fecha assim: **265.000** (bônus de cadastro) +
  bônus resgatados − "usado" (que o 1min devolve em cada resposta). Conferido duas vezes com a tela, bateu exato.
- **Visita diária: 15.000 créditos/dia** só por abrir o site logado. O dia vira à meia-noite de Los Angeles
  (4h no horário de Brasília até 31/10, 5h depois). Dá umas 3 a 4 mensagens curtas de Opus 5.5 por dia.
- **Pesquisa "AI Agent"** em app.1min.ai/free-credits: **1.000.000 de créditos, uma vez**. São respostas suas
  (a dona responde, não a automação).
- Também existem curtir/comentar 10 posts/dia (15 mil) e avaliação em sites de review. Ficaram de fora de propósito:
  é engajamento e avaliação fabricados.

## Visita diária automática (`visita_diaria.py`)

## Proxy Webshare para o IP_LOCKED (31/10 ~18h20, a dona autorizou)

O 1min bloqueia o IP de casa (`IP_REMOVIDO`) por 24 h depois de ~3 cadastros seguidos. A dona pediu para usar o
proxy da Webshare que já temos (mesmas credenciais do TikTok, `D:\postador-de-videos\secrets\proxies.txt`).

`umin/proxy_umin.py` é um repassador local (PAC em 127.0.0.1:18250, um por IP em 18251..18259) **gêmeo** do
`proxy_tiktok.py`, mas com portas próprias (não encosta na produção do TikTok) e um PAC que manda **só `*.1min.ai`**
pelo IP da Webshare — o login do Google e todo o resto continuam saindo de casa (IP confiável; não dispara o
"verifique que é você" do Google). Cada conta ganha um IP fixo (1..9) espalhado pelos nós (`proxy_umin_mapa.json`).

```bash
python umin\proxy_umin.py --teste     # sobe o repassador e testa túnel até api.1min.ai por cada IP (9/9 OK em 31/10)
python umin\login_fila.py 1 --proxy   # fila à mão COM o proxy (a dona escolhe a conta no Google)
python umin\criar_contas.py --proxy   # login automático COM o proxy
```

Provado em 31/10 18h20: casa = `IP_REMOVIDO`; nós Webshare dão `IP_REMOVIDO`, `IP_REMOVIDO`, `IP_REMOVIDO`…
(IPs de datacenter EUA, fixos por nó). Se o Chrome da conta já estiver aberto SEM o proxy, o script PULA (sairia pelo
IP bloqueado). Mesmo com proxy: no máximo 1–2 cadastros por lote e horas de intervalo — o IP novo também pode travar.

A tarefa agendada **"1min visita diaria"** roda todo dia às 06:10 (prioridade 6, até 15 min; se o PC estava
desligado, roda quando ligar). Ela:

1. abre o Chrome da conta pelo cofre;
2. entra em app.1min.ai/free-credits por uma janela própria;
3. reloga com o Google se a sessão do site caiu;
4. lê o saldo da tela e acerta a base do `umin.py`, para o `umin.py saldo` contar os bônus;
5. fecha só o que ela mesma abriu.

Cada execução vira uma linha em `visitas.jsonl`. O teste de 30/10 às 14h25 abriu, achou o site logado, leu 145.429
(igual ao calculado) e fechou.

```bash
python visita_diaria.py              # visita agora
python visita_diaria.py --agendar    # recria a tarefa
schtasks /Delete /TN "1min visita diaria" /F   # tira a tarefa
```

A visita de 30/10 já tinha sido contada antes do script: a página Free Credits mostrava "Daily Visit Credits 15,000".
A prova de que os +15.000 entram sozinhos vai ser o saldo de 31/10 no `visitas.jsonl`, que precisa ficar acima do
de 30/10 se ninguém usar o 1min no meio.

## Navegador (só para o que a chave não faz)

`node cdp.mjs ...` controla **uma janela própria** no Chrome do cofre, por CDP direto. O Playwright travou 3 minutos
para conectar quando outra sessão usava o mesmo Chrome; o CDP direto fala só com a própria janela e não tira a aba
de ninguém da frente.

- O login do site **cai de vez em quando**: o token vale 7 dias, mas tem `tokenVersion`, e o servidor pode invalidá-lo.
  Relogar = `Log In` → `Log in with Google` → `node cdp.mjs usar accounts.google.com` → clicar a conta.
- `js\login.js` diz se está logado e o saldo da tela. `js\token_validade.js` mostra emissão e validade do token
  (nunca o token).
- `node cdp.mjs segredo` e `node cdp.mjs rede ... regex arquivo` gravam segredos direto no arquivo, sem mostrar na tela.
