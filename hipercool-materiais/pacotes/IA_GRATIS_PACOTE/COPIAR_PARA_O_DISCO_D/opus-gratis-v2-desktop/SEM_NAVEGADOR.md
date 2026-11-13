# Genspark sem robotizar a tela — dois modos (31/10/2026)

Pedido da dona: *"faça o opus-gratis responder sem navegador como o argo gemini; o Genspark pede reCAPTCHA, faça funcionar."*
Resultado: **funciona por HTTP puro, zero navegador** (modo PURO) — e tem um **backup** que usa o navegador só como
hospedeiro da sessão (modo PÁGINA). O antigo (robotizar a tela) vira fallback profundo.

## O que travava, e o que descobrimos

O chat do Genspark é `POST https://www.genspark.ai/api/agent/ask_proxy` (resposta **SSE**). A fama era de duas paredes:

1. **Cloudflare** — com `requests` puro dá 403 "Just a moment". **Causa real: fingerprint TLS errado.** Com
   **`curl_cffi` impersonando o Chrome** (mesmo JA3) + os cookies da sessão, passa liso (nem precisou do `cf_clearance`).
2. **`g_recaptcha_token`** no corpo — a fama era que exigia um token novo por mensagem (reCAPTCHA Enterprise).
   **Testado: o ask_proxy NÃO exige o token para sessão já logada** — POST com token **vazio** respondeu 200 e
   devolveu a resposta completa ("391" em 4,5 s). Igual ao gemini_http: só cookies + TLS do Chrome.

(A site key do reCAPTCHA, caso um dia passem a exigir, é `6LfYyWcsAAAAAK8DUr6Oo1wHl2CJ5kKbO0AK3LIM`, descoberta ao
vivo — ela só carrega quando se foca o campo. Guardada em `segredos/genspark_recaptcha.json`.)

## Modo PURO — `genspark_http_puro.py` (principal, ZERO navegador)

`curl_cffi` + cookies capturados 1x do cofre. Sem token, sem serviço pago. ~5-7 s por mensagem.

```bash
python genspark_http_puro.py capturar --conta conta_exemplo     # 1x por conta (como o login): salva cookies da sessão
python genspark_http_puro.py capturar                       # todas as logadas (1 Chrome por vez)
python genspark_http_puro.py testar-cloudflare --conta conta_exemplo   # só confere o Cloudflare (GET is_login)
python genspark_http_puro.py --conta conta_exemplo "Quanto e 17 x 23?" # pergunta (HTTP puro)
```

- Cookies ficam em `cookies/<conta>.json`; o módulo persiste os que o Genspark renova (Set-Cookie) p/ manter a sessão fresca.
- Quando a sessão expirar (resposta parar de vir), **recapturar**: `python genspark_http_puro.py capturar --conta X`.
- **Backup de captcha** (se um dia exigirem o token): `GENSPARK_PURO_TOKEN=auto` (padrão: vazio; cai pro serviço se
  preciso **e** houver chave) / `none` / `servico`. Chave em `segredos/captcha.key` (`capsolver:CAP-...` ou
  `2captcha:...`). A dona autorizou o serviço pago em 31/10 (por padrão o projeto não usaria — regra da casa).

## Modo PÁGINA — `genspark_pagina.py` (backup, navegador como hospedeiro)

Manda o mesmo `fetch` de **dentro da página logada** (CDP), gerando o token pelo reCAPTCHA da própria página
(injeta o `enterprise.js` com a site key — sem solver, sem burla). Serve se o Genspark um dia endurecer Cloudflare/token.

```bash
python genspark_pagina.py --conta conta_exemplo "pergunta"               # FRIO: abre e fecha o Chrome (~17 s)
python genspark_pagina.py --conta conta_exemplo --quente "a || b || c"   # QUENTE: página persistente (~16 s a 1ª, ~5 s as seguintes)
python genspark_pagina.py --descobrir --conta conta_exemplo              # investiga o reCAPTCHA da página
```

- `perguntar_quente()` mantém um worker (thread dona do Playwright) por conta; evicta por ócio (`GENSPARK_QUENTE_OCIO_MIN`,
  padrão 20) e por limite (`GENSPARK_QUENTES`, padrão 2) — a API sync do Playwright não é thread-safe, as threads do
  servidor só enfileiram.

## Front unificado — `genspark_http.py` (OpenAI-compatível, porta 20165)

Novos ids de modelo (escolhem o backend); o `auto` agora põe o PURO na frente:

| id | backend | navegador? | velocidade |
|---|---|---|---|
| `claude-opus-5-5` | **puro** → 1min (reserva) | não | ~5-7 s |
| `puro/claude-opus-5-5` | HTTP puro | **não** | ~5-7 s |
| `pagina/claude-opus-5-5` | página quente | sim (hospedeiro) | ~5 s pós-aquecimento |
| `genspark/claude-opus-5-5` | automação de tela (antigo) | sim | ~45-60 s |
| `1min/...`, `claude-fable-5-1` | 1min.ai (API) | não | — |

`GENSPARK_AUTO` muda a ordem do `auto` (ex.: `"puro,pagina,1min"`). Teste:
```bash
curl 127.0.0.1:20165/v1/chat/completions -H "Content-Type: application/json" \
     -d '{"model":"puro/claude-opus-5-5","messages":[{"role":"user","content":"oi"}]}'
```

**Para ativar em produção:** o servidor 20165 (e o proxy_cc 20166 do VS Code) precisam **reiniciar** para pegar o
código novo — aí o `auto` passa a responder pelo PURO (sem navegador, ~5 s) em vez da automação de tela. Não reiniciei
sozinho porque o 20166 está ligado ao trocador de modelo do VS Code.

## Comparação (qual ficou melhor)

- **PURO vence**: sem navegador, ~5-7 s, imune à carga da máquina (era o que derrubava a automação de tela: `0 chars`),
  sem RAM de Chrome, sem serviço pago. É o principal.
- **PÁGINA é o backup**: só vale se o Genspark passar a exigir Cloudflare/token de verdade; aí a página real resolve
  nativamente. Custa um Chrome por conta quente (RAM).
- **Serviço de captcha**: backup do backup. Só se exigirem o token E não der pra usar a página. Custa dinheiro.

Arquivos novos: `genspark_api.py` (corpo + parser SSE + config reCAPTCHA), `genspark_http_puro.py`, `genspark_pagina.py`,
`cookies/` (sessões do modo PURO), `segredos/genspark_recaptcha.json`.
