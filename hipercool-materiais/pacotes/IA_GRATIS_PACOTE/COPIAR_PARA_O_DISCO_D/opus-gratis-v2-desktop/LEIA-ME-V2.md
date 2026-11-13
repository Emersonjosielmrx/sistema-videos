# opus-gratis v2 — merge do desktop + pc1 (31/10/2026)

Esta pasta junta as duas linhas que divergiram do ancestral comum (30/10):

- **do pc1** (`D:\opus-gratis` no pc1, que virou a base aqui): núcleo evoluído da UI — leitura de **créditos reais**
  (`_menu_conta`, `marcar_creditos`), detecção de **conta sem Opus** (`marcar_opus`/`opus`), **páginas quentes de UI**
  (`_abrir_quente`/`_faxina_quentes`), `_forcar_modelo`; **reuso de conversa** no front (`genspark_http.py`), `_flatten`
  com enquadramento de tool-call; e as ferramentas de operação: `login_fila.py` (login em fila à mão), `zelador_genspark.py`
  (teste diário de Opus/saldo), `og_manter.py` (mantém o front + túnel SSH pra VPS do Claude Code).
- **do desktop** (minha linha): o **sem-navegador** — `genspark_api.py`, `genspark_pagina.py`, `genspark_http_puro.py`,
  `proxy_cc/` (proxy local p/ o VS Code), `captura/`, `cookies/` (sessões), `SEM_NAVEGADOR.md`, e o `_sessao` (is_login).

## O que a v2 tem de novo em relação a cada lado

- O `genspark.py` da v2 = o do pc1 **+ `_sessao`** (necessário aos modos sem-navegador).
- O `genspark_http.py` da v2 = o do pc1 (reuso de conversa, tool-call) **+ backends `puro` e `pagina`**; o `auto` agora é
  **puro → pagina → 1min**. Detecta "conta sem Opus" (mensagem de upgrade) e pula a conta.
- Caminhos **relativos à própria pasta** (`BASE = Path(__file__).parent`, `sys.path` na pasta do script): a v2 usa a
  própria `contas_genspark.json`, `cookies/`, `segredos/` — não mexe no `D:\opus-gratis` do desktop.

## Modos (do melhor pro backup)

1. **PURO** (`genspark_http_puro.py`) — HTTP puro, **ZERO navegador** (curl_cffi + cookies). ~5-7 s. Principal.
   `python genspark_http_puro.py capturar` (1x por conta) · `... --conta X "pergunta"`.
2. **PÁGINA** (`genspark_pagina.py`) — fetch de dentro da página quente (navegador hospedeiro). Backup.
3. **genspark** (UI antiga, `genspark.py`) — automação de tela com reuso de conversa. Fallback profundo.
4. **1min** (`umin/`) — API paga do 1min.ai (reserva).

Veja `SEM_NAVEGADOR.md` para a história completa (o Genspark responde sem navegador: Cloudflare cai com curl_cffi e o
ask_proxy não exige o g_recaptcha_token para sessão logada).

## Rodar

```bash
python genspark_http.py              # front OpenAI em 127.0.0.1:20165 (auto = puro,pagina,1min)
python genspark_http_puro.py capturar          # captura cookies das contas logadas (1x)
python zelador_genspark.py                     # testa Opus/saldo das contas (pc1)
python login_fila.py 3 --todas                 # login em fila à mão (pc1)
```

**Estado (31/10, noite): a v2 É A PRODUÇÃO.** Ponte :20165 e proxy :20166 rodam desta pasta (proxy_cc\manter.ps1 da v2; a tarefa GensparkProxyManter e o trocar.ps1 apontam para cá; o manter.ps1 da v1 só repassa). Seletor do Antigravity: linhas Genspark PURO/PAGINA/CAPTCHA v2. Chave do captcha (se comprar) vai em D:\opus-gratis-v2\segredos\captcha.key. Voltar à v1: restaurar D:\opus-gratis\proxy_cc\manter.ps1.bak-20261031-antes-v2, reapontar a tarefa para ele e reiniciar 20165/20166.

