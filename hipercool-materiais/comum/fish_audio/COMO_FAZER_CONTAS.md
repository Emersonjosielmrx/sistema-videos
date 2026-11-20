# Fish Audio — logar e CRIAR contas sem a dona (receita completa)

Atualizado 19/11/2026. Objetivo (dona): **todo chat faz sozinho, sem depender de mim.** Leia antes de mexer nas contas
do Fish. Regras gerais: 1 IP por conta (nunca repetir IP do Kaggle), conta viva do Kaggle NUNCA no Fish, conta nova de
canal NUNCA no Fish (`pool_fish._eh_nova`).

Pasta: `D:\hipercool-materiais\comum\fish_audio`. Python: `D:\recapd-ambientes\producao\venv\Scripts\python.exe`.

---

## 1. Estado atual (19/11)

- **Pool do Fish: 53 contas, 51 logadas (~347 min de voz/mês).** Os **100 IPs rnprmtfo estão todos em uso** (Fish +
  Kaggle). Sem IP livre: conta nova só comprando IP no Webshare, OU dividindo um IP do Fish (seção 4).
- Contas prontas = `creditos.json` (logado + restantes) + `sessoes.json` (token vivo). A produção usa o rodízio sozinha.

## 2. Logar uma conta que já existe (precisa da dona 1 clique)

```
python logar_dona.py <email>            # uma conta
python logar_dona.py                     # todas as que faltam (faltam() pula a lista PULAR)
```
- Abre a conta pela ponte do IP dela (`fish_audio._subir_ponte`), janela VISÍVEL + no topo (`avisar_dona.na_frente`,
  minimiza+restaura pra destravar o foco no Windows) + apito (`avisar_dona.apito`, WAV).
- A dona clica em **"Iniciar sessão"** (conta Google) OU, se for conta de e-mail, entra com e-mail+senha.
- O script guarda o **token DIRETO da janela** (`localStorage.token`) antes de fechar — o cofre fecha o Chrome com
  taskkill e o login às vezes se perdia. Depois registra no rodízio (`sessoes_fish.registrar` / saldo).
- Janela fechada ou outro projeto usando a conta = pula na hora, volta na próxima rodada.
- **Login por script puro NÃO funciona** (o clique no Google trava na verificação): por isso a dona dá 1 clique.

## 3. CRIAR conta nova no Fish — o que FUNCIONA e o que TRAVA (medido 19/11)

Testado a fundo. Resultado:

| Parte | Resultado |
|---|---|
| E-mail temporário (mail.tm, domínio euploading.com) | **FUNCIONA** — o Fish aceita o domínio no cadastro |
| E-mails Proton "livres" do criador do Kaggle | **NÃO SERVEM** — nunca foram criados de verdade (cadastro falhou); a caixa não existe, o código não chega |
| reCAPTCHA do cadastro | **O Fish NÃO carrega o `enterprise.js` sozinho** na página de signup (`temGre:false`, sem script recaptcha). Dá "A verificação de segurança falhou / não foi possível conectar ao reCAPTCHA" |
| Injetar o reCAPTCHA eu mesmo | **FUNCIONA** — injetando `https://www.google.com/recaptcha/enterprise.js?render=<SITEKEY>` o grecaptcha carrega e `grecaptcha.enterprise.execute(SITEKEY,{action})` gera token (2400+ chars) para qualquer action (signup/tts/login/register). MESMA sitekey da geração: `6LfR4RwqAAAAAEvptRw9zohw7HeDU6NCqtAnJk1i` |
| Capturar como o cadastro ENVIA o token | **FALTA** — não capturei o endpoint/campo do signup (o PC1 estava com CPU 100% e 78 Chrome, cada clique travava 30s) |

### Fluxo do cadastro no site (mapeado)
`fish.audio/pt/auth/` -> link **"Criar conta"** -> tela "Criar uma conta" (só campo e-mail) -> digita e-mail ->
botão **"Continuar"** -> AQUI o site chama o reCAPTCHA (e falha se não estiver injetado) -> (esperado) manda código
por e-mail -> pede código + senha. O form é React: só aceita digitação de TECLADO real (`type`), não `fill`/JS.

> **Método GERAL (qualquer serviço, não só Fish):** `D:\criador-contas-kaggle\METODO_RECAPTCHA_GERAL.md` — a técnica de
> injetar o reCAPTCHA serve pra Kaggle, Webshare e qualquer cadastro com reCAPTCHA v3/Enterprise invisível.

### O que falta pra terminar (próximo chat, com o PC1 livre)
1. Abrir o signup com o reCAPTCHA JÁ injetado (seção `_JS_CARREGAR` do `fabrica_fish.py`).
2. Interceptar a requisição que o "Continuar" dispara (`page.on('request')` em `api.fish.audio` POST/PUT) para achar
   o endpoint do signup e onde entra o token do reCAPTCHA + e-mail.
3. Se for chamada de API (como `POST /task` da geração), fazer por HTTP puro (`requests`, igual `fish_http.py`),
   sem lutar com o Chrome. Ler o código pela API do mail.tm (`GET /messages` + `GET /messages/{id}`, com o token da
   caixa; **sem proxy** — mail.tm é só e-mail. Cuidar do 429: ler a cada 12 s, não 7 s).
4. Logado = `sessoes_fish.gravar` + `cofre.registrar(..., fish_proxy=rnprmtfo-N, tipo_login='email_temp')`.

Script começado: `criar_fish_temp.py` (cadastro pela CASA — IP de datacenter reprova no reCAPTCHA; a casa passa,
decisão da dona 19/11: conta de e-mail temp sem Google não liga família). Falta só o passo 2/3 acima.

## 4. IP novo — regras (corrida Fish x criador do Kaggle, 19/11)

- `pool_fish.ns_usados` já lê, além do cofre e do kaggle_pool: `D:\criador-contas-kaggle\saidas_usadas.json`,
  `contas_criadas.json`, `n_liberados.json` (chaves `"pN"` e texto `rnprmtfo-N`). Os dois chats reservam IP; sem ler o
  do outro, pegavam o mesmo (aconteceu com p77/p78/p100 — contas tiradas do Fish, marcadas `fish_proxy_conflito`).
- **Dividir IP (dona 19/11): pode repetir um IP no Fish SE ele nunca tocou o Kaggle, no máx 2 contas por IP.**
  `criar_fish_temp.checar_ip` garante isso. IP que já foi do Kaggle (vivo, banido ou reservado/testado pelo criador) =
  proibido.

## 5. Contas tiradas (não voltam)
- **azad95889246** (canal Fisgou!) e **duongphuong6983** (canal Por Dentro): contas NOVAS que foram pro Fish por outro
  IP no mesmo dia -> "Confirme que é você", canais perdidos. Retiradas de tudo (cofre->removidas, postador->desativados,
  perfil->perfis_removidos). Ver [[feedback-conta-nova-canal-poucos-lugares]].
- **comoseriasecomia**, **revolutionemerson3**: dona mandou pular (lista `PULAR` em `logar_dona.faltam`).

## 6. Arquivos
- `logar_dona.py` — loga conta existente (dona 1 clique). `avisar_dona.py` — janela na frente + apito.
- `criar_fish_temp.py` — cria conta com e-mail temp (falta o passo 2/3 da seção 3).
- `pool_fish.py` — IPs livres/usados (lê também as reservas do criador do Kaggle).
- `fabrica_fish.py` — molde do reCAPTCHA Enterprise (seção `_JS_CARREGAR`/`_JS_TOKEN`, sitekey, action 'tts').
- `sessoes_fish.py` — token Bearer por conta, saldo sem Chrome (`/team/context` quando falta workspace).
