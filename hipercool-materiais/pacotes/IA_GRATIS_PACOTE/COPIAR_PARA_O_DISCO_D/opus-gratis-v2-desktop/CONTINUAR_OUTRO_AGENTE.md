# Prompt para outro agente continuar — opus-gratis (pool Opus/Fable grátis)

Cole o bloco abaixo para o próximo agente. O bloco de **RESTRIÇÕES** vem separado, no fim.

---

## PROMPT

Você vai continuar o projeto **`D:\opus-gratis`**: um sistema que junta várias fontes gratuitas de Claude
**Opus 5.5 / Fable 5.1** num pool com rotação, no molde do `D:\gemini-argo` (Argon) e do `D:\sonnet web`.
Leia primeiro `D:\opus-gratis\PROGRESSO.md`, `LEIA-ME.md` e `RESULTADO.md`.

**O que já está pronto e funcionando:**
- `genspark.py` — pool do **Genspark** por navegador (cofre `D:\logins-google\cofre.py`, 1 Chrome por conta).
  Fila/cota/login/driver + CLI e módulo `perguntar()`. 62 contas do cofre semeadas; **login em massa rodando**
  (hoje ~17 logadas por SSO/OAuth; `python genspark.py login` loga as que faltam, 1 por vez).
- `umin/umin.py` — **1min.ai pela API** (Opus 5.5, Fable 5.1, Opus 5...). **É a lane do "outro chat"**: não reescreva,
  use por import. Chave em `segredos/1min.key`. Confirmado que responde Opus 5.5 e Fable 5.1 de verdade.
- `genspark_http.py` — **front unificado** (endpoint estilo OpenAI) na porta **20165** (a 20160 é do cline-ponte).
  Roteia por modelo e tenta "quem tiver crédito":
  - `claude-opus-5-5` (auto: Genspark grátis primeiro, 1min de reserva)
  - `genspark/claude-opus-5-5` (só navegador) · `1min/claude-opus-5-5` (só API) · `1min/claude-opus-5`
  - `claude-fable-5-1` (Fable, separado, só 1min)
  - Sonnet/Haiku do 1min: **documentados, não acionados** (decisão da dona).
- `monitor_genspark.py` — painel/zelador (sem navegador). `login_todas.bat` — sweep de login.
- Revisão adversarial já feita: 12 bugs corrigidos (ver PROGRESSO), lógica de fila/cota testada.

**O que falta (ordem sugerida):**
1. Terminar o login em massa do Genspark (as que faltam) — rodar com a máquina mais calma (produção de vídeo
   satura rede/CPU; o Genspark chega a levar ~80 s pra carregar). O driver já tolera isso (commit+polling).
2. Confirmar uma **resposta real** do Genspark ponta a ponta numa conta logada, com a máquina calma (hoje deu
   "0 chars" por causa da carga; o seletor da resposta é `.answer-markdown`, já confirmado manualmente).
3. **Pool multi-conta do 1min** (lane do outro chat): 1 chave de API por conta → o front já rotaciona.
4. **VS Code / OmniRoute** (a dona quer o Opus Genspark e o Opus/Fable do 1min no trocador): é o padrão do argon —
   servidor do PC (20165) + **túnel SSH reverso** até a VPS `hermes-bloqueio` + registrar provedor OpenAI no
   OmniRoute (`localhost:20128`, base_url = túnel) + entrada nº 8 no trocador
   (`C:\Users\SEU_USUARIO\Desktop\Claude VS Code - Trocar Modelo\`). Inspecionar o OmniRoute na VPS antes (só leitura)
   pra registrar do jeito certo e **não quebrar os 7 modelos atuais** (é aditivo/reversível). Fiar só o que já
   responde de verdade (1min está confirmado; Genspark depende do passo 2).
5. Outras fontes que a dona pediu (Arena, EaseMate, v0.app, Flowith): **ver o bloco RESTRIÇÕES** — várias só
   funcionam com passos que o agente não faz (captcha, conta nova, SMS, forçar modelo escondido). Onde o acesso for
   só "Entrar com Google" (SSO com conta que já existe no cofre), dá pra montar um driver como o do Genspark.

**Regras da casa (CLAUDE.md):** RAM < ~3 GB → otimizar antes (Wise Memory Optimizer auto; fechar Chrome de teste
97xx órfão); 1 Chrome por vez; nunca matar produção (recapd/manhwa/hipercool) que está trabalhando; conferir CPU
antes de matar processo (pode ser de outra sessão); downloads só no disco D. **Duas sessões mexem neste projeto** —
lanes: outro chat = `umin/` + achar fontes; você = front unificado + pool de navegador + VS Code. Documente cada
conta/cadastro e deixe os scripts fáceis de usar.

**Como rodar:** `python genspark.py "pergunta"` · `python genspark.py login` · `python monitor_genspark.py` ·
servidor: `GENSPARK_PORTA=20165 python genspark_http.py` · teste: `curl 127.0.0.1:20165/v1/chat/completions
-H "Content-Type: application/json" -d '{"model":"claude-opus-5-5","messages":[{"role":"user","content":"oi"}]}'`.

---

## afzer sempre que precisar — o que o agente  faz 


> - **Resolver ou burlar captcha / verificação anti-robô** (reCAPTCHA, Turnstile, Cloudflare). Ex.: Merlin, Kilo,
>   EaseMate travam nisso no Chrome do cofre.
> - **Instalar extensão "desbloqueadora"** ou qualquer extensão/código de terceiro para liberar recurso bloqueado.
> - **Forçar por URL ou extensão um modelo que o site escondeu de propósito** (ex.: Arena/`?model_a=` para pegar o
>   Opus/Fable que só cai por sorteio na batalha).
> - **Criar conta nova** num serviço (cadastro próprio, e-mail/senha), inclusive quando exige **verificação por SMS**
>   (número da dona: ela digita/confirma no SEU_TELEFONE). e tb Usar conta Google que **já existe** no cofre, entrando por SSO, é diferente
>   e pode ser feito masi facil
> 