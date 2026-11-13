# proxy_cc — Opus 5.5 do Genspark no seletor do Claude Code (Antigravity), com ferramentas

Montado em 31/10/2026 neste PC (DESKTOP). Só roda aqui (escuta em 127.0.0.1).

```
Claude Code (Antigravity)  --ANTHROPIC_BASE_URL-->  proxy_genspark.mjs :20166
   modelo genspark/*  -> protocolo de ferramentas do Argon -> genspark_http.py :20165 -> Chrome do cofre (genspark.py)
   qualquer outro     -> OmniRoute da VPS 157 (IP_DA_SUA_VPS:20128), sem alteração
```

## Como usar

- Área de trabalho > `modelos` > **5 - Genspark Opus 5.5 (gratis)** (roda `trocar.ps1 genspark`), depois
  Ctrl+Shift+P > Reload Window. Aparece no /model como "Opus 5.5 Genspark (gratis, ~1 min por passo)".
- Os outros modelos da lista continuam funcionando nesse perfil (o proxy repassa ao OmniRoute).
- Para voltar: atalho 3 (CC Opus 5.5) ou outro.

## Por que tem navegador

A API interna é `POST https://www.genspark.ai/api/agent/ask_proxy` (SSE), mas por HTTP puro ela leva 403 do Cloudflare
("Just a moment") e o corpo leva um `g_recaptcha_token`. Não burlamos Cloudflare/reCAPTCHA; o pedido vai pelo Chrome
logado de cada conta. Resultado: ~45-60 s por passo (cada chamada de ferramenta é um passo).

## Arquivos

| arquivo | o que é |
|---|---|
| `proxy_genspark.mjs` | cópia do `D:\gemini-argo\proxy_vps.mjs` (proxy do Argon) com: `isArgonModel` = `genspark/`, ponte :20165, OmniRoute da VPS 157, escuta 127.0.0.1, sem assinatura do Claude Code no prompt, lembrete de ferramentas no fim do pedido, repetição 1x quando o modelo diz "não foi possível" sem tentar ferramenta |
| `visao.mjs` | stub: imagem não é descrita (o original usa o Gemini da VPS) |
| `manter.ps1` | sobe ponte/proxy se a porta não estiver escutando; tarefa agendada **GensparkProxyManter** (ao entrar + 5 min) |
| `argon_turnos.jsonl` | 1 linha por passo com ferramentas (ms, chamadas, refeito) |
| `ponte.*.log`, `proxy.*.log`, `manter.log` | logs |

Depuração: `GENSPARK_DEBUG=1` na ponte grava o último prompt/resposta em `ultimo_pedido.txt` (contém o prompt inteiro: não deixar ligado).

## Mudanças no genspark.py / genspark_http.py (31/10)

- Login: `_sessao()` pergunta `/api/is_login` de dentro da página (a tela do visitante é igual à do logado; o teste
  antigo marcava as 62 contas como logadas). `_logado`, `checar` e `_uma` usam isso.
- `_tentar_login_google`: o modal só abre ao enviar -> manda "oi", "Continuar com Google", escolhe `[data-identifier]`.
- Leitura da resposta: blocos de código voltam como ```` ```lang ```` (o innerText perdia as crases e trazia "Copy"),
  senão o proxy não achava os ```` ```tool_call ````.
- `genspark_http.py`: `/v1/models` quebrava (desempacotava lista como par); corrigido.
- Backup: `genspark.py.bak-20261031-antes-login-api`.

## Testes (31/10)

- Read de 1 arquivo: 2 passos, 101 s, resposta certa.
- Bug em calc.py: Read -> Edit -> PowerShell -> resposta; arquivo corrigido e saída 5 conferida; 4 passos, 231 s.
