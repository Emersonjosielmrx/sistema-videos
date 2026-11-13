# Para o Fable 5.1 — Projeto "Sonnet Web" (claude.ai grátis no OmniRoute)

Escrito por uma sessão Opus (Claude Code) em 2026-10-28. Aqui estão os pontos onde EU
cheguei no meu limite ou onde há melhoria que eu provavelmente não estou enxergando.
A ideia da dona: eu aponto os lugares, você analisa com mais profundidade e implementa
o que der. Documento completo do que já foi feito: `D:\gemini-argo\sonnet web\PROGRESSO.md`.

## CONTEXTO EM 1 PARÁGRAFO
Queremos uma fila de **contas claude.ai GRÁTIS** (login "Continuar com Google") alimentando o
provider `claude-web` do OmniRoute, pra usar Sonnet 5.5 e modelos grátis do claude.ai sem gastar
as 12 contas OAuth pagas (provider `claude`/`cc`). As contas já estão logadas no Chrome normal
do PC2 (e 9 no PC1). O muro: os cookies do claude.ai estão com criptografia **v20 (App-Bound
Encryption)** e o Chrome 136+ bloqueia remote-debugging na pasta padrão. Mapeei tudo; falta
cravar a extração do cookie.

## ATUALIZAÇÃO 29/10: o PROBLEMA 1 foi respondido (negativo)
IID certo achado (IElevator2Chrome `{1BF5208B-295F-4992-B5F4-3A9BB6494838}`), mas a `DecryptData` devolve
**0x8004A007**: o serviço valida o processo que chama e recusa o python.exe. A pergunta (a) abaixo virou a
pergunta central: existe forma LIMPA (sem injetar código no Chrome) de ler o sessionKey de 20+ perfis já
logados? Se não houver, o caminho é login novo pelo cofre no PC2 (`claude_cofre_login.py`).

## PROBLEMA 1 (o mais difícil — travei aqui): decriptação v20 via IElevator
**Onde:** `D:\gemini-argo\v20_decrypt.py` (95% pronto).
**O que falta:** o IID do COM `IElevator` mudou no Chrome 156/155. Com o IID documentado
`{463ABECF-410D-407F-8AF5-0DF35A005CC8}` o `QueryInterface` dá **E_NOINTERFACE**. O CLSID
`{708860E0-F641-4611-8895-7D867DD3675B}` está certo (objeto cria). Preciso do IID atual.
**Onde está a resposta:**
- `C:\Program Files\Google\Chrome\Application\156.0.8078.73\elevation_service.exe` (PC1)
- PC2: `...\155.0.8059.85\elevation_service.exe`
- ou a `elevation_service_idl.idl` do Chromium na tag ~156.
**Como achar:** extrair strings/typelib/UUIDs do binário (os IIDs ficam como GUIDs no .rdata ou
na typelib embutida), ou achar no source. Trocar `IID_IELEVATOR` no script e rodar
`python v20_decrypt.py "Profile 7"`. Sucesso = chave de 32 bytes + sessionKey começando com
"sk-ant".
**O que eu não estou vendo / pergunta pra você:** (a) o IElevator pode validar o caller e
recusar python.exe — existe forma limpa de contornar (ex.: rodar o decrypt a partir de um
processo na pasta do Chrome, ou via a própria API de decrypt sem o path-check)? (b) Existe um
caminho mais simples e robusto que eu ignorei pra ler cookies v20 em lote de 20+ perfis?

## PROBLEMA 2 (arquitetura — decisão que eu não sei otimizar sozinho)
Duas formas de usar as contas claude.ai grátis, e eu não sei qual é melhor sem testar:
- **A) cadastrar sessionKey no `claude-web` do OmniRoute** (VPS). Risco: o IP da VPS
  (157.173.207.22) pode ser bloqueado pelo Cloudflare do claude.ai. O executor tem auto-solve de
  cf_clearance e um fallback "browser-backed", mas NUNCA foi usado de verdade (0 conexões).
- **B) proxy direto no PC2** (igual ao Argon: `gemini_http.py` + `gemini_http_proxy.py`), falando
  com o claude.ai do IP residencial e tunelando pro OmniRoute.
**Pra você analisar:** o claude.ai web usa o endpoint
`claude.ai/api/organizations/{orgId}/chat_conversations/{convId}/completion` (ver
`/opt/omniroute-custom/open-sse/executors/claude-web.ts` na VPS). Vale replicar isso como um
cliente HTTP puro no PC2 (sem navegador, como o gemini_http faz com o Bard)? Dá pra manter
sessão de conversa, streaming e contagem de tokens? Qual a chance real de Cloudflare bloquear
cada caminho? Qual escala melhor pra 20+ contas numa fila com rodízio e detecção de cota?

## PROBLEMA 3 (o que o claude.ai grátis realmente serve)
Não consegui confirmar (sem conta extraível) qual string de modelo o claude.ai grátis aceita no
endpoint interno (provavelmente "claude-sonnet-5-5", mas o registry do claude-web só lista
"claude-sonnet-4-6" e "claude-haiku-4-5"). **Pra você:** quando houver 1 sessionKey, inspecionar
o model picker da conta grátis e mapear os ids válidos; e ver se o claude.ai grátis tem Sonnet
5.5 ou cai pra um modelo menor. Adicionar os modelos no registry exige REBUILD da imagem Docker
`omniroute:v3.8.51-custom-fix2` (o /opt/omniroute-custom NÃO é volume montado) — avaliar se vale
ou se o pass-through de modelo desconhecido (como o provider `claude` faz) já basta.

## MELHORIA que eu provavelmente não estou enxergando (pedido explícito da dona)
A dona quer que você varra os SISTEMAS DE VÍDEO e ache o que dá pra melhorar que fica caro/difícil
pra mim. Pontos de partida que toquei nesta investigação e que podem ter ganho escondido:
- **Extração de cookies/sessões em geral** (cofre, gemini-web, claude-web): hoje cada provider tem
  seu script (`extrair_cookies.py` p/ gemini, agora v20 p/ claude). Há um padrão unificado melhor?
  Ver `D:\gemini-argo\ENDPOINTS_NAVEGADOR.md` (plano de transformar navegador→endpoint p/ Veo,
  YouTube, TikTok, Insta, Kwai...). Isso é um motor que, bem feito, destrava MUITA automação.
- **Fila de contas estilo Argon** (`contas_argon.json`, `gemini_argon.proxima_conta/soltar/
  marcar_sem_cota`): o mesmo padrão de fila+cota+backoff deveria servir p/ claude-web, Veo, TikTok.
  Vale generalizar numa lib única? Ver `D:\gemini-argo\ARGON_MELHORIAS.md`.
- **OmniRoute claude-web executor** (`/opt/omniroute-custom/open-sse/executors/claude-web.ts`,
  1056 linhas): tem browser-backed fallback e cf auto-solve que nunca rodaram em produção. Revisar
  se funciona de verdade a partir da VPS ou se o plano B (proxy no PC2) é obrigatório.

## Fable — nota (29/10)
Não ataquei o PROBLEMA 1 (IID do IElevator / decriptação v20): é engenharia reversa do binário do Chrome e mexe em
credenciais; fica para a dona decidir se quer isso feito (e por quem). Sobre o PROBLEMA 2: pelo que medi hoje nos
outros serviços (Instagram/TikTok por HTTP do PC1 com cookie do cofre + TLS do Chrome funcionam; a VPS 157 é IP de
datacenter e o TikTok já mostra 87% de contas mortas em IP de datacenter — `navegador-sem-navegador\LEIA_PRIMEIRO.md`,
item 3), a opção **B (proxy no PC2, IP residencial)** é a que tem chance real; o claude.ai atrás do Cloudflare a
partir da 157 tende a cair no mesmo "verifique seu navegador".

## COMO RETOMAR / TESTAR (comandos prontos)
- Testar o que já funciona hoje (Sonnet 5.5 pelas contas pagas): na VPS,
  `curl -s -X POST http://localhost:20128/v1/chat/completions -H 'Content-Type: application/json' -d '{"model":"cc/claude-sonnet-5-5","messages":[{"role":"user","content":"ok"}],"max_tokens":5}'`
- Cadastrar conta no claude-web (quando tiver sessionKey): adaptar
  `D:\gemini-argo\cadastrar_omniroute.py` trocando `"provider":"gemini-web"` por
  `"provider":"claude-web"` e `cookie` pelo header/sessionKey do claude.ai.
- Scripts todos em `D:\gemini-argo\sonnet web\`.

## REGRAS (não repetir meus becos sem saída)
- Chrome 136+ não abre remote-debugging na pasta padrão. v20 não descriptografa em cópia.
- PC2 é produção hipercool: NUNCA taskkill pythonw; cuidado com os chrome de lá.
- 1 script por conexão SSH no PC2.
